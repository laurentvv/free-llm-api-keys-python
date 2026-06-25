"""Exceptions du module free_llm_api_keys."""

from __future__ import annotations


class FreeLLMError(Exception):
    """Classe de base de toutes les exceptions du module."""


class FetchError(FreeLLMError):
    """Échec du téléchargement du README depuis GitHub."""


class ParseError(FreeLLMError):
    """Le README téléchargé n'a pas pu être parsé (structure inattendue)."""


class NoKeysAvailableError(FreeLLMError):
    """Aucune clé disponible pour le modèle demandé."""


class AllKeysExhaustedError(FreeLLMError):
    """Toutes les clés d'un modèle ont été essayées et ont échoué."""

    def __init__(self, model: str, attempts: int) -> None:
        self.model = model
        self.attempts = attempts
        super().__init__(
            f"Toutes les {attempts} clé(s) du modèle '{model}' ont échoué "
            "(budget épuisé, expirée ou non autorisée)."
        )
