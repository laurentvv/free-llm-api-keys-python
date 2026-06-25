"""Classification des modèles par catégorie (texte, image, tts, embeddings).

La détection se fait par motifs sur le nom du modèle (insensible à la casse),
ce qui permet de router chaque clé vers la bonne méthode du client OpenAI.
"""

from __future__ import annotations

import re
from enum import Enum


class ModelCategory(str, Enum):
    """Catégories de modèles supportées par l'API OpenAI-compatible."""

    TEXTE = "texte"
    IMAGE = "image"
    TTS = "tts"
    EMBEDDINGS = "embeddings"


# Motifs (regex) par catégorie. L'ordre compte : on teste dans l'ordre
# et la première correspondance gagne. Les catégories spécialisées sont
# testées avant TEXTE (qui est le fallback par défaut).
_IMAGE_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"^dall-?e-?[23]",
        r"sdxl",
        r"flux",
        r"stable-?diffusion",
        r"imagen",
        r"midjourney",
    )
]

_TTS_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"^tts-?1",
        r"-tts",
        r"elevenlabs",
        r"-audio$",
        r"^audio/",
    )
]

_EMBEDDING_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"text-?embedding",
        r"-embedding",
        r"^embed-",
        r"^embeddings",
        r"^bge-",
        r"-e5-",
        r"^e5-",
    )
]


def _matches_any(name: str, patterns: list[re.Pattern[str]]) -> bool:
    return any(p.search(name) for p in patterns)


def classify(model_name: str) -> ModelCategory:
    """Détermine la catégorie d'un modèle à partir de son nom.

    Args:
        model_name: Nom du modèle (ex. ``gpt-5.5``, ``dall-e-3``,
            ``tts-1-hd``, ``text-embedding-3-small``).

    Returns:
        La :class:`ModelCategory` correspondante. Par défaut
        :attr:`ModelCategory.TEXTE` pour tout ce qui n'est pas reconnu
        comme image / tts / embeddings.
    """
    if not model_name:
        return ModelCategory.TEXTE
    name = model_name.strip()
    if _matches_any(name, _IMAGE_PATTERNS):
        return ModelCategory.IMAGE
    if _matches_any(name, _TTS_PATTERNS):
        return ModelCategory.TTS
    if _matches_any(name, _EMBEDDING_PATTERNS):
        return ModelCategory.EMBEDDINGS
    return ModelCategory.TEXTE
