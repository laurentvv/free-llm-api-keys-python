"""Catalogue de clés : orchestration fetch + parse + cache.

Au premier accès, le catalogue décide de la source des données :

  - cache local **valide** (non stale) → chargé depuis le disque, pas de réseau ;
  - cache **stale** ou **absent** → téléchargement + parsing + écriture du cache ;
  - échec réseau → repli sur le cache (même stale) si disponible, sinon
    :class:`FetchError`.

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
from .parser import KeyEntry, dedupe, parse_readme

logger = logging.getLogger("free_llm_api_keys")


class Catalog:
    """Catalogue de clés, mis à jour automatiquement depuis GitHub.

    Usage typique ::

        catalog = Catalog.load()
        print(catalog.list_models())
        keys = catalog.get_keys("gpt-5.5")
    """

    def __init__(
        self,
        keys: Iterable[KeyEntry],
        *,
        cache_path: str | None = None,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        self._keys: list[KeyEntry] = dedupe(keys)
        self._ttl_seconds = ttl_seconds
        self._cache = CatalogCache(cache_path)
        self._lock = threading.Lock()
        self._initialized = False  # chargé/rafraîchi une fois

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
            catalog._initialized = True
        return catalog

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
                    self._initialized = True
                    return
                raise

            if content:
                keys = parse_readme(content)
                logger.info("README parsé : %d clés trouvées.", len(keys))
            else:
                # 304 Not Modified : on conserve le cache précédent.
                keys = list(fallback.keys) if fallback else []
                logger.info("README inchangé : %d clés conservées.", len(keys))

            self._keys = dedupe(keys)
            self._cache.save(self._keys, etag=etag)
            self._initialized = True

    # ------------------------------------------------------------------ #
    # Accès aux données
    # ------------------------------------------------------------------ #
    def all_keys(self) -> list[KeyEntry]:
        """Toutes les clés du catalogue (dédupliquées)."""
        return list(self._keys)

    def list_models(self, category: ModelCategory | None = None) -> list[str]:
        """Liste les noms de modèles disponibles, triés et uniques.

        Args:
            category: Filtrer par catégorie (ex. :attr:`ModelCategory.TEXTE`).
        """
        models: list[str] = []
        seen: set[str] = set()
        for entry in self._keys:
            if category is not None and entry.category != category:
                continue
            if entry.model in seen:
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
