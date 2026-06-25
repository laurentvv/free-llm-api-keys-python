"""Tests du classifieur de modèles."""

from __future__ import annotations

import pytest

from free_llm_api_keys.classifier import ModelCategory, classify


@pytest.mark.parametrize(
    "model, expected",
    [
        # Texte (défaut)
        ("gpt-5.5", ModelCategory.TEXTE),
        ("gpt-4o", ModelCategory.TEXTE),
        ("claude-opus-4-7", ModelCategory.TEXTE),
        ("deepseek-v3", ModelCategory.TEXTE),
        ("gemini-2.5-pro", ModelCategory.TEXTE),
        ("kimi-k2", ModelCategory.TEXTE),
        ("qwen3-235b", ModelCategory.TEXTE),
        ("grok-4", ModelCategory.TEXTE),
        ("mistral-large", ModelCategory.TEXTE),
        # Image
        ("dall-e-3", ModelCategory.IMAGE),
        ("dall-e-2", ModelCategory.IMAGE),
        ("sdxl", ModelCategory.IMAGE),
        ("flux-pro", ModelCategory.IMAGE),
        ("stable-diffusion-3", ModelCategory.IMAGE),
        # TTS
        ("tts-1", ModelCategory.TTS),
        ("tts-1-hd", ModelCategory.TTS),
        ("elevenlabs-v2", ModelCategory.TTS),
        # Embeddings
        ("text-embedding-3-small", ModelCategory.EMBEDDINGS),
        ("text-embedding-3-large", ModelCategory.EMBEDDINGS),
        ("embed-english-v3.0", ModelCategory.EMBEDDINGS),
        ("embed-multilingual-v3.0", ModelCategory.EMBEDDINGS),
        ("bge-large-en", ModelCategory.EMBEDDINGS),
    ],
)
def test_classify_known_models(model: str, expected: ModelCategory) -> None:
    assert classify(model) == expected


def test_classify_is_case_insensitive() -> None:
    assert classify("DALL-E-3") == ModelCategory.IMAGE
    assert classify("TTS-1-HD") == ModelCategory.TTS


def test_classify_unknown_defaults_to_text() -> None:
    assert classify("some-future-model-xyz") == ModelCategory.TEXTE


def test_classify_empty_defaults_to_text() -> None:
    assert classify("") == ModelCategory.TEXTE
    assert classify("   ") == ModelCategory.TEXTE
