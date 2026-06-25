"""Catalogue de clés : orchestration fetch + parse + cache + santé.

Au premier accès, le catalogue décide de la source des données :

  - cache local **valide** (non stale) → chargé depuis le disque, pas de réseau ;
  - cache **stale** ou **absent** → téléchargement + parsing + écriture du cache ;
  - échec réseau → repli sur le cache (même stale) si disponible, sinon
    :class:`FetchError`.

Le catalogue porte aussi l'**état de santé** des modèles (ce qui marche /
ne marche pas), stocké séparément dans ``health.json``. Cet état se
réinitialise automatiquement quand la version du README change. Voir
:mod:`free_llm_api_keys.health`.

Thread-safe via un verrou, afin que des imports concurrents ne déclenchent
pas plusieurs téléchargements.
"""

from __future__ import annotations

import logging
import threading
from typing import Iterable

import httpx

from .cache import CatalogCache, CacheEntry, DEFAULT_TTL_SECONDS
from .classifier import ModelCategory
from .exceptions import FetchError
from .fetcher import README_URL, fetch_readme
from .health import HealthState, HealthStatus, HealthStore
from .parser import KeyEntry, dedupe, parse_readme_full

logger = logging.getLogger("free_llm_api_keys")


class Catalog:
    """Catalogue de clés, mis à jour automatiquement depuis GitHub.

    Usage typique ::

        catalog = Catalog.load()
        print(catalog.list_models())
        keys = catalog.get_keys("deepseek-chat")
        # Marquer un modèle défaillant découvert au runtime
        catalog.mark_failed("baidu/cobuddy:free", reason="404 No endpoints")
    """

    def __init__(
        self,
        keys: Iterable[KeyEntry],
        *,
        cache_path: str | None = None,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        readme_updated_at: str = "",
    ) -> None:
        self._keys: list[KeyEntry] = dedupe(keys)
        self._ttl_seconds = ttl_seconds
        self._cache = CatalogCache(cache_path)
        # Le health store vit dans le même dossier que le cache.
        if cache_path:
            import os
            self._health = HealthStore(os.path.join(os.path.dirname(cache_path), "health.json"))
        else:
            self._health = HealthStore(None)
        self._lock = threading.Lock()
        self._initialized = False  # chargé/rafraîchi une fois
        self._readme_updated_at = readme_updated_at

    # ------------------------------------------------------------------ #
    # Construction / chargement
    # ------------------------------------------------------------------ #
    @classmethod
    def load(
        cls,
        *,
        force_refresh: bool = False,
        cache_path: str | None = None,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        http_client: httpx.Client | None = None,
    ) -> "Catalog":
        """Charge un catalogue, en rafraîchissant depuis GitHub si nécessaire.

        Args:
            force_refresh: Si ``True``, force un téléchargement même si le
                cache est frais.
            cache_path: Chemin personnalisé du cache (pratique pour les tests).
            ttl_seconds: TTL du cache en secondes (défaut 1 h).
            http_client: Client httpx injecté (pour tests). Si ``None``, un
                client éphémère est créé lors du téléchargement.
        """
        cache = CatalogCache(cache_path)
        cached = cache.load()

        catalog = cls([], cache_path=cache_path, ttl_seconds=ttl_seconds)
        catalog._cache = cache
        catalog._sync_health_store(cache_path)

        need_refresh = force_refresh or cached is None or cached.is_stale(ttl_seconds)
        if need_refresh:
            catalog.refresh(http_client=http_client, fallback=cached)
        else:
            logger.info(
                "Cache utilisé (%d clés, dernière màj %s).",
                len(cached.keys),  # type: ignore[union-attr]
                cached.fetched_at_iso,  # type: ignore[union-attr]
            )
            catalog._keys = cached.keys  # type: ignore[union-attr]
            catalog._readme_updated_at = cached.readme_updated_at  # type: ignore[union-attr]
            catalog._initialized = True
        return catalog

    def _sync_health_store(self, cache_path: str | None) -> None:
        """Place health.json à côté de catalog.json (dossier commun)."""
        if cache_path is None:
            self._health = HealthStore(None)
            return
        from pathlib import Path

        base = Path(cache_path).resolve().parent
        self._health = HealthStore(base / "health.json")

    def refresh(
        self,
        *,
        http_client: httpx.Client | None = None,
        fallback: CacheEntry | None = None,
    ) -> None:
        """Télécharge et parse le README, puis met à jour le cache.

        En cas d'échec réseau, bascule sur ``fallback`` (cache précédent)
        s'il contient des clés ; sinon lève :class:`FetchError`.
        """
        with self._lock:
            previous_etag = fallback.etag if fallback else None
            try:
                content, etag = fetch_readme(
                    etag=previous_etag,
                    url=README_URL,
                    client=http_client,
                )
            except FetchError as exc:
                if fallback is not None and fallback.keys:
                    logger.warning(
                        "Réseau indisponible (%s) : utilisation du cache "
                        "(potentiellement stale, %d clés).",
                        exc,
                        len(fallback.keys),
                    )
                    self._keys = list(fallback.keys)
                    self._readme_updated_at = fallback.readme_updated_at
                    self._initialized = True
                    return
                raise

            if content:
                parsed = parse_readme_full(content)
                keys = parsed.keys
                readme_updated_at = parsed.readme_updated_at
                logger.info("README parsé : %d clés trouvées (version %s).",
                            len(keys), readme_updated_at or "?")
            else:
                # 304 Not Modified : on conserve le cache précédent.
                keys = list(fallback.keys) if fallback else []
                readme_updated_at = fallback.readme_updated_at if fallback else ""
                logger.info("README inchangé : %d clés conservées.", len(keys))

            self._keys = dedupe(keys)
            self._readme_updated_at = readme_updated_at
            self._cache.save(self._keys, etag=etag, readme_updated_at=readme_updated_at)
            self._initialized = True

    @property
    def readme_updated_at(self) -> str:
        """Version du README source (date ``Last updated``)."""
        return self._readme_updated_at

    # ------------------------------------------------------------------ #
    # Accès aux données
    # ------------------------------------------------------------------ #
    def all_keys(self) -> list[KeyEntry]:
        """Toutes les clés du catalogue (dédupliquées)."""
        return list(self._keys)

    def list_models(
        self,
        category: ModelCategory | None = None,
        *,
        only_healthy: bool = False,
    ) -> list[str]:
        """Liste les noms de modèles disponibles, triés et uniques.

        Args:
            category: Filtrer par catégorie (ex. :attr:`ModelCategory.TEXTE`).
            only_healthy: Si ``True``, exclut les modèles marqués
                ``FAILED`` dans l'état de santé (les ``UNKNOWN`` sont gardés).
        """
        failed = self._health_state().models if only_healthy else {}
        models: list[str] = []
        seen: set[str] = set()
        for entry in self._keys:
            if category is not None and entry.category != category:
                continue
            if entry.model in seen:
                continue
            if only_healthy and failed.get(entry.model) is not None:
                if failed[entry.model].status == HealthStatus.FAILED:
                    continue
            seen.add(entry.model)
            models.append(entry.model)
        return sorted(models)

    def get_keys(self, model: str) -> list[KeyEntry]:
        """Toutes les clés disponibles pour un modèle donné."""
        return [e for e in self._keys if e.model == model]

    def __len__(self) -> int:
        return len(self._keys)

    def __repr__(self) -> str:
        return f"<Catalog models={len(self.list_models())} keys={len(self)}>"

    # ------------------------------------------------------------------ #
    # État de santé
    # ------------------------------------------------------------------ #
    def _health_state(self) -> HealthState:
        return self._health.load(readme_updated_at=self._readme_updated_at)

    def health_status(self, model: str) -> HealthStatus:
        """Statut de santé d'un modèle (``UNKNOWN`` si non testé)."""
        return self._health_state().status_of(model)

    def mark_failed(self, model: str, *, reason: str = "") -> None:
        """Marque un modèle comme défaillant (découvert au runtime).

        Le client appelle cette méthode quand toutes les clés d'un modèle
        échouent. L'état est persisté et réutilisé pour skip le modèle
        lors des prochains :meth:`list_models` (avec ``only_healthy=True``).
        """
        self._health.mark(
            model,
            HealthStatus.FAILED,
            readme_updated_at=self._readme_updated_at,
            last_error=reason,
        )
        logger.info("Modèle '%s' marqué FAILED (%s).", model, reason or "sans détail")

    def mark_ok(self, model: str) -> None:
        """Marque un modèle comme fonctionnel (après un probe réussi)."""
        self._health.mark(
            model,
            HealthStatus.OK,
            readme_updated_at=self._readme_updated_at,
        )

    def health_report(self) -> dict[str, str]:
        """Retourne ``{modèle: statut}`` pour tous les modèles connus."""
        state = self._health_state()
        report: dict[str, str] = {}
        for model in self.list_models():
            mh = state.models.get(model)
            report[model] = mh.status.value if mh else HealthStatus.UNKNOWN.value
        return report
