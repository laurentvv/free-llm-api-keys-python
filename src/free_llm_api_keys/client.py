"""Client OpenAI-compatible avec auto-rotation des clés et retry.

Les clés du catalogue sont publiques et partagées : elles peuvent être
épuisées (budget) ou expirées. :class:`FreeLLMClient` essaie donc toutes
les clés d'un modèle l'une après l'autre, et bascule automatiquement sur
la suivante quand une clé est refusée. Les erreurs réseau transitoires
sont retentées avec un backoff exponentiel.

Une seule classe, 4 méthodes par type de modèle :

  - :meth:`FreeLLMClient.chat`            (TEXTE)
  - :meth:`FreeLLMClient.generate_image`  (IMAGE)
  - :meth:`FreeLLMClient.tts`             (TTS)
  - :meth:`FreeLLMClient.embeddings`      (EMBEDDINGS)
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any, Callable, TypeVar

import openai
from openai import OpenAI

from .catalog import Catalog
from .classifier import ModelCategory
from .exceptions import AllKeysExhaustedError, NoKeysAvailableError
from .parser import KeyEntry

if TYPE_CHECKING:  # pragma: no cover
    from typing import Iterable

logger = logging.getLogger("free_llm_api_keys")

DEFAULT_BASE_URL = "https://aiapiv2.pekpik.com/v1"
DEFAULT_TIMEOUT = 60.0
MAX_RETRIES = 3  # retries pour erreurs transitoires (réseau / 5xx)
BACKOFF_BASE = 0.5  # secondes, multiplié par 2 à chaque essai

# Codes/statuts indiquant qu'une clé est inutilisable : on passe à la suivante.
# 401/403 = clé invalide/non autorisée, 402 = budget épuisé, 429 = rate limit,
# 404 = endpoint/modèle non trouvé pour cette clé (la suivante peut pointer ailleurs).
_ROTATABLE_STATUS_CODES = {401, 402, 403, 404, 429}

T = TypeVar("T")


def _is_rotatable(exc: Exception) -> bool:
    """Une clé doit-elle être abandonnée pour cette erreur ?

    Oui pour : clé invalide/non autorisée, budget épuisé, rate limit.
    Non pour : erreur réseau transitoire ou 5xx (à retenter sur la même clé).
    """
    if isinstance(exc, openai.AuthenticationError):
        return True
    if isinstance(exc, openai.PermissionDeniedError):
        return True
    if isinstance(exc, openai.NotFoundError):
        return True
    if isinstance(exc, openai.RateLimitError):
        return True
    status = getattr(exc, "status_code", None)
    return status in _ROTATABLE_STATUS_CODES


def _is_transient(exc: Exception) -> bool:
    """Erreur transitoire à retenter (réseau / 5xx) ?"""
    if isinstance(exc, openai.APIConnectionError):
        return True
    if isinstance(exc, openai.APITimeoutError):
        return True
    if isinstance(exc, openai.InternalServerError):
        return True
    status = getattr(exc, "status_code", None)
    return status is not None and 500 <= int(status) < 600


class FreeLLMClient:
    """Client LLM avec rotation automatique des clés du catalogue.

    Args:
        model: Nom du modèle cible (ex. ``"gpt-5.5"``).
        base_url: Base URL OpenAI-compatible (défaut : le serveur pekpip).
        catalog: Catalogue de clés. Si ``None``, chargé via :meth:`Catalog.load`.
        max_retries: Nombre maximal de retries pour erreurs transitoires
            par clé.
        timeout: Délai d'attente par requête (secondes).
    """

    def __init__(
        self,
        model: str | None = None,
        *,
        type: str | ModelCategory | None = None,
        base_url: str = DEFAULT_BASE_URL,
        catalog: Catalog | None = None,
        max_retries: int = MAX_RETRIES,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        if model is None and type is None:
            type = ModelCategory.TEXTE

        self.model = model
        self.type = type
        self.base_url = base_url
        self._catalog = catalog if catalog is not None else Catalog.load()
        self.max_retries = max_retries
        self.timeout = timeout
        self._keys: list[KeyEntry] = self._resolve_keys(model, type)
        # Index de rotation courant (tourne en rond si tout échoue).
        self._cursor = 0

    # ------------------------------------------------------------------ #
    # Résolution des clés
    # ------------------------------------------------------------------ #
    def _resolve_keys(self, model: str | None, type_: str | ModelCategory | None) -> list[KeyEntry]:
        if model:
            keys = self._catalog.get_keys(model)
            if not keys:
                # Recherche insensible à la casse / espaces en fallback.
                norm = model.strip().lower()
                keys = [
                    e for e in self._catalog.all_keys() if e.model.strip().lower() == norm
                ]
            if not keys:
                raise NoKeysAvailableError(
                    f"Aucune clé trouvée pour le modèle '{model}'. "
                    f"Modèles disponibles : {self._catalog.list_models()}"
                )
            return keys

        if isinstance(type_, str):
            try:
                type_ = ModelCategory(type_.lower())
            except ValueError:
                pass

        models = self._catalog.list_models(category=type_, only_healthy=True)
        if not models:
            models = self._catalog.list_models(category=type_)

        if not models:
            raise NoKeysAvailableError(
                f"Aucune clé trouvée pour le type '{type_}'."
            )

        keys = []
        for m in models:
            keys.extend(self._catalog.get_keys(m))
        return keys

    def _client_for(self, key: str) -> OpenAI:
        return OpenAI(base_url=self.base_url, api_key=key, timeout=self.timeout)

    # ------------------------------------------------------------------ #
    # Cœur : exécution avec rotation + retry
    # ------------------------------------------------------------------ #
    def _run(self, fn: Callable[[OpenAI, str], T]) -> T:
        """Exécute ``fn(client)`` sur les clés en rotation, avec retry transitoire.

        - Sur erreur *rotatable* (clé refusée) → passe à la clé suivante.
        - Sur erreur *transitoire* (réseau/5xx) → retry sur la même clé
          avec backoff, jusqu'à ``max_retries``.
        - Si toutes les clés sont épuisées → :class:`AllKeysExhaustedError`.
        """
        attempts = 0
        tried_keys: set[str] = set()
        n = len(self._keys)

        while attempts < n:
            entry = self._keys[(self._cursor + attempts) % n]
            if entry.key in tried_keys:
                attempts += 1
                continue
            tried_keys.add(entry.key)
            client = self._client_for(entry.key)
            last_exc: Exception | None = None

            for retry in range(self.max_retries + 1):
                try:
                    result = fn(client, entry.model)
                    # Succès : on marque le modèle sain et on avance le
                    # curseur sur la clé gagnante.
                    self._catalog.mark_ok(entry.model)
                    self._cursor = (self._cursor + attempts) % n
                    return result
                except Exception as exc:  # noqa: BLE001 - OpenAI lève des exceptions variées
                    last_exc = exc
                    if _is_rotatable(exc):
                        logger.info(
                            "Clé refusée pour '%s' (%s). Rotation vers la suivante.",
                            entry.model,
                            type(exc).__name__,
                        )
                        self._catalog.mark_failed(entry.model, reason=f"{type(exc).__name__}: {exc}")
                        break  # sortir des retries, passer à la clé suivante
                    if _is_transient(exc) and retry < self.max_retries:
                        delay = BACKOFF_BASE * (2**retry)
                        logger.warning(
                            "Erreur transitoire (%s) sur '%s' : retry dans %.1fs.",
                            type(exc).__name__,
                            entry.model,
                            delay,
                        )
                        time.sleep(delay)
                        continue
                    # Erreur non récupérable (4xx hors rotation) : on la propage.
                    raise

            attempts += 1

        # Toutes les clés ont échoué : on marque le modèle défaillant pour
        # que le catalogue puisse le skip au prochain appel, puis on lève.
        target = self.model if self.model else str(self.type)
        raise AllKeysExhaustedError(target, n) from last_exc

    # ------------------------------------------------------------------ #
    # API publique : 4 types de modèles
    # ------------------------------------------------------------------ #
    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        """Chat completion (TEXTE). Retourne le contenu du message.

        Args:
            messages: Liste de messages au format OpenAI
                (``{"role": "user", "content": "..."}``).
            **kwargs: Options additionnelles passées à l'API (temperature,
                max_tokens, etc.). ``model`` est forcé à ``self.model``.
        """
        category = self._category()
        if category is not ModelCategory.TEXTE:
            logger.warning(
                "chat() appelé avec un modèle '%s' de catégorie %s "
                "(texte attendu).", self.model, category.value
            )

        def _do(c: OpenAI, m: str) -> str:
            resp = c.chat.completions.create(model=m, messages=messages, **kwargs)
            return resp.choices[0].message.content or ""

        return self._run(_do)

    def generate_image(self, prompt: str, *, n: int = 1, **kwargs: Any) -> list[str]:
        """Génération d'images (IMAGE). Retourne la liste des URLs/data.

        Args:
            prompt: Description textuelle de l'image.
            n: Nombre d'images à générer.
            **kwargs: Options (size, quality, response_format...).
        """
        def _do(c: OpenAI, m: str) -> list[str]:
            resp = c.images.generate(model=m, prompt=prompt, n=n, **kwargs)
            return [img.url or getattr(img, "b64_json", "") for img in resp.data]

        return self._run(_do)

    def tts(self, text: str, **kwargs: Any) -> bytes:
        """Synthèse vocale (TTS). Retourne le contenu audio en bytes.

        Args:
            text: Texte à synthétiser.
            **kwargs: Options (voice, response_format, speed...).
        """
        def _do(c: OpenAI, m: str) -> bytes:
            resp = c.audio.speech.create(model=m, input=text, **kwargs)
            return resp.content

        return self._run(_do)

    def embeddings(self, input: "str | Iterable[str]", **kwargs: Any) -> list[list[float]]:
        """Embeddings (EMBEDDINGS). Retourne une liste de vecteurs.

        Args:
            input: Un texte ou une liste de textes.
            **kwargs: Options (encoding_format, dimensions...).
        """
        def _do(c: OpenAI, m: str) -> list[list[float]]:
            resp = c.embeddings.create(model=m, input=input, **kwargs)
            return [d.embedding for d in resp.data]

        return self._run(_do)

    # ------------------------------------------------------------------ #
    def _category(self) -> ModelCategory:
        return self._keys[0].category if self._keys else ModelCategory.TEXTE

    def __repr__(self) -> str:
        return f"<FreeLLMClient model='{self.model}' type='{self.type}' keys={len(self._keys)}>"
