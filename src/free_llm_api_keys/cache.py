"""Cache local du catalogue de clés (JSON) avec TTL.

Le cache permet :
  - d'éviter de télécharger le README à chaque import (TTL d'une heure),
  - de fonctionner hors-ligne (fallback sur un cache même stale).

Emplacement : ``~/.cache/free-llm-api-keys/catalog.json``.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .parser import KeyEntry

logger = logging.getLogger("free_llm_api_keys")

# TTL par défaut : 1 heure.
DEFAULT_TTL_SECONDS = 3600


def _default_cache_path() -> Path:
    """Chemin du cache, respectant ``FREE_LLM_CACHE_DIR`` si défini."""
    env_dir = os.environ.get("FREE_LLM_CACHE_DIR")
    if env_dir:
        return Path(env_dir) / "catalog.json"
    return Path.home() / ".cache" / "free-llm-api-keys" / "catalog.json"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(value: str) -> datetime | None:
    if not value:
        return None
    try:
        # ``fromisoformat`` gère le suffixe 'Z' depuis Python 3.11.
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


@dataclass
class CacheEntry:
    """Contenu sérialisé du catalogue de clés."""

    fetched_at: datetime
    etag: str | None = None
    keys: list[KeyEntry] = field(default_factory=list)
    # Version du README source (date ``Last updated``). Sert à réinitialiser
    # l'état de santé quand le catalogue change.
    readme_updated_at: str = ""
    base_url: str = ""

    @property
    def fetched_at_iso(self) -> str:
        return self.fetched_at.isoformat()

    def is_stale(self, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> bool:
        age = (_now() - self.fetched_at).total_seconds()
        return age > ttl_seconds

    def to_json(self) -> str:
        return json.dumps(
            {
                "fetched_at": self.fetched_at_iso,
                "etag": self.etag,
                "readme_updated_at": self.readme_updated_at,
                "base_url": self.base_url,
                "keys": [k.to_dict() for k in self.keys],
            },
            ensure_ascii=False,
            indent=2,
        )

    @classmethod
    def from_json(cls, raw: str) -> "CacheEntry":
        d = json.loads(raw)
        fetched_at_str = d.get("fetched_at") or ""
        fetched_at = _parse_iso(fetched_at_str)
        if fetched_at is None:
            # Cache corrompu / trop ancien : on le considère comme stale.
            fetched_at = datetime(1970, 1, 1, tzinfo=timezone.utc)
        return cls(
            fetched_at=fetched_at,
            etag=d.get("etag"),
            keys=[KeyEntry.from_dict(k) for k in d.get("keys", [])],
            readme_updated_at=d.get("readme_updated_at", ""),
            base_url=d.get("base_url", ""),
        )


class CatalogCache:
    """Gestion du cache du catalogue sur disque."""

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path is not None else _default_cache_path()

    def exists(self) -> bool:
        return self.path.is_file()

    def load(self) -> CacheEntry | None:
        """Charge le cache, ou ``None`` s'il n'existe pas / est illisible."""
        if not self.exists():
            return None
        try:
            raw = self.path.read_text(encoding="utf-8")
            entry = CacheEntry.from_json(raw)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Cache illisible (%s), ignoré.", exc)
            return None
        if entry.is_stale():
            logger.info("Cache présent mais stale (âgé de plus de %ds).", DEFAULT_TTL_SECONDS)
        return entry

    def save(
        self,
        keys: Iterable[KeyEntry],
        etag: str | None = None,
        readme_updated_at: str = "",
    ) -> CacheEntry:
        entry = CacheEntry(
            fetched_at=_now(),
            etag=etag,
            keys=list(keys),
            readme_updated_at=readme_updated_at,
        )
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(entry.to_json(), encoding="utf-8")
        except OSError as exc:
            # Le cache n'est pas vital : on prévient mais on ne plante pas.
            logger.warning("Impossible d'écrire le cache dans %s : %s", self.path, exc)
        return entry

    def clear(self) -> None:
        try:
            self.path.unlink(missing_ok=True)
        except OSError as exc:
            logger.warning("Impossible de supprimer le cache %s : %s", self.path, exc)
