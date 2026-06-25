"""État de santé des modèles : ce qui marche / ne marche pas.

Stocké dans un fichier ``health.json`` **séparé** du cache du catalogue :
le catalogue reste fidèle au README source, l'état de santé est lui
éphémère et re-vérifiable.

Mécanisme clé : l'état est **rattaché à une version du README** (champ
``readme_updated_at``). Quand cette date change (le README source a été
mis à jour), tout l'état est **réinitialisé** : un modèle qui était marqué
« défaillant » revient à « inconnu », car il a pu être réparé côté serveur.

Deux sources alimentent l'état :
  1. le **nettoyage** (:mod:`examples.cleanup`) qui « probe » chaque modèle ;
  2. le **runtime** (:class:`~free_llm_api_keys.client.FreeLLMClient`) qui
     marque un modèle défaillant quand toutes ses clés échouent.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

logger = logging.getLogger("free_llm_api_keys")


class HealthStatus(str, Enum):
    """État de santé d'un modèle."""

    UNKNOWN = "unknown"  # pas encore testé
    OK = "ok"  # fonctionne
    FAILED = "failed"  # défaillant (endpoint inactif / clés épuisées)


def _default_health_path() -> Path:
    """Chemin de health.json, respectant ``FREE_LLM_CACHE_DIR`` si défini."""
    env_dir = os.environ.get("FREE_LLM_CACHE_DIR")
    if env_dir:
        return Path(env_dir) / "health.json"
    return Path.home() / ".cache" / "free-llm-api-keys" / "health.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ModelHealth:
    """État de santé d'un seul modèle."""

    status: HealthStatus = HealthStatus.UNKNOWN
    last_checked: str = ""  # ISO 8601
    last_error: str = ""  # message d'erreur si FAILED

    def to_dict(self) -> dict[str, str]:
        return {
            "status": self.status.value,
            "last_checked": self.last_checked,
            "last_error": self.last_error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ModelHealth":
        status = data.get("status", HealthStatus.UNKNOWN)
        if isinstance(status, str):
            try:
                status = HealthStatus(status)
            except ValueError:
                status = HealthStatus.UNKNOWN
        return cls(
            status=status,  # type: ignore[arg-type]
            last_checked=str(data.get("last_checked", "")),
            last_error=str(data.get("last_error", "")),
        )


@dataclass
class HealthState:
    """État de santé complet du catalogue, rattaché à une version du README."""

    readme_updated_at: str = ""
    models: dict[str, ModelHealth] = field(default_factory=dict)

    def status_of(self, model: str) -> HealthStatus:
        return self.models.get(model, ModelHealth()).status

    def set(
        self, model: str, status: HealthStatus, last_error: str = ""
    ) -> None:
        self.models[model] = ModelHealth(
            status=status, last_checked=_now_iso(), last_error=last_error
        )

    def to_json(self) -> str:
        return json.dumps(
            {
                "readme_updated_at": self.readme_updated_at,
                "models": {m: h.to_dict() for m, h in self.models.items()},
            },
            ensure_ascii=False,
            indent=2,
        )

    @classmethod
    def from_json(cls, raw: str) -> "HealthState":
        data = json.loads(raw)
        models = {
            name: ModelHealth.from_dict(h)
            for name, h in (data.get("models") or {}).items()
        }
        return cls(
            readme_updated_at=str(data.get("readme_updated_at", "")),
            models=models,
        )


class HealthStore:
    """Persistance de l'état de santé sur disque, avec reset sur changement de version."""

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path is not None else _default_health_path()

    def load(self, readme_updated_at: str = "") -> HealthState:
        """Charge l'état ; réinitialise si la version du README a changé.

        Args:
            readme_updated_at: Version courante du README (date ``Last updated``).
                Si elle diffère de celle stockée, l'état est remis à zéro
                (mais ``readme_updated_at`` est mis à jour).
        """
        state = self._read()
        if readme_updated_at and state.readme_updated_at != readme_updated_at:
            logger.info(
                "README mis à jour ('%s' -> '%s') : réinitialisation de l'état de santé.",
                state.readme_updated_at or "(vide)",
                readme_updated_at,
            )
            state = HealthState(readme_updated_at=readme_updated_at)
            self._write(state)
        return state

    def save(self, state: HealthState) -> None:
        self._write(state)

    def mark(
        self,
        model: str,
        status: HealthStatus,
        *,
        readme_updated_at: str = "",
        last_error: str = "",
    ) -> HealthState:
        """Marque un modèle et persiste. Charge/initialise au besoin."""
        state = self.load(readme_updated_at=readme_updated_at)
        state.set(model, status, last_error=last_error)
        self._write(state)
        return state

    def clear(self) -> None:
        try:
            self.path.unlink(missing_ok=True)
        except OSError as exc:
            logger.warning("Impossible de supprimer %s : %s", self.path, exc)

    # ------------------------------------------------------------------ #
    def _read(self) -> HealthState:
        if not self.path.is_file():
            return HealthState()
        try:
            return HealthState.from_json(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("health.json illisible (%s), ignoré.", exc)
            return HealthState()

    def _write(self, state: HealthState) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(state.to_json(), encoding="utf-8")
        except OSError as exc:
            logger.warning("Impossible d'écrire %s : %s", self.path, exc)
