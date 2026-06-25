"""free_llm_api_keys — accès simple aux clés IA gratuites (format OpenAI).

Ce module télécharge, parse et met en cache les clés publiques du dépôt
``alistaitsacle/free-llm-api-keys``, puis expose des clients prêts à l'emploi
qui tournent automatiquement sur les clés disponibles.

Exemple rapide ::

    from free_llm_api_keys import FreeLLMClient

    client = FreeLLMClient(model="gpt-5.5")
    reponse = client.chat([{"role": "user", "content": "Bonjour !"}])
    print(reponse)
"""

from __future__ import annotations

from .cache import DEFAULT_TTL_SECONDS
from .catalog import Catalog
from .classifier import ModelCategory
from .client import DEFAULT_BASE_URL, FreeLLMClient
from .exceptions import (
    AllKeysExhaustedError,
    FetchError,
    FreeLLMError,
    NoKeysAvailableError,
    ParseError,
)
from .parser import KeyEntry

__version__ = "0.1.0"

__all__ = [
    "__version__",
    # Client & catalogue
    "FreeLLMClient",
    "Catalog",
    "ModelCategory",
    "KeyEntry",
    # Constantes
    "DEFAULT_BASE_URL",
    "DEFAULT_TTL_SECONDS",
    # Exceptions
    "FreeLLMError",
    "FetchError",
    "ParseError",
    "NoKeysAvailableError",
    "AllKeysExhaustedError",
]
