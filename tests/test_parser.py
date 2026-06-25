"""Tests du parser de README.

On utilise une fixture markdown qui imite la structure réelle du README
(section Available Keys + How to Use), avec plusieurs types de modèles
et une clé expirée, pour valider la robustesse du parsing.
"""

from __future__ import annotations

import textwrap

import pytest

from free_llm_api_keys.classifier import ModelCategory
from free_llm_api_keys.exceptions import ParseError
from free_llm_api_keys.parser import parse_readme

# README minimal mais fidèle à la structure réelle.
SAMPLE_README = textwrap.dedent(
    """\
    # Free LLM API Keys

    ![banner](https://example.com/banner.jpg)

    Quelques clés gratuites.

    ## 📋 Available Keys

    ### GPT-5.5 `2026-06-25T12:00Z`

    | Key | Model | Status | Budget | Rate Limit | Expires | Description |
    |-----|-------|--------|--------|------------|---------|-------------|
    | sk-text-aaa | gpt-5.5 | Active | $50 | 30 req/min | 48h | Modèle texte principal |
    | sk-text-bbb | gpt-5.5 | Active | $20 | 30 req/min | 48h | Clé de secours |

    ### DALL-E 3 `2026-06-25T12:00Z`

    | Key | Model | Status | Budget | Rate Limit | Expires | Description |
    |-----|-------|--------|--------|------------|---------|-------------|
    | sk-img-aaa | dall-e-3 | Active | $10 | 5 req/min | 48h | Génération d'images |

    ### TTS HD `2026-06-25T12:00Z`

    | Key | Model | Status | Budget | Rate Limit | Expires | Description |
    |-----|-------|--------|--------|------------|---------|-------------|
    | sk-tts-aaa | tts-1-hd | Expired | $0 | 0 req/min | expired | Clé expirée |
    | sk-tts-bbb | tts-1-hd | Active | $5 | 10 req/min | 24h | Synthèse vocale |

    ### Embeddings `2026-06-25T12:00Z`

    | Key | Model | Status | Budget | Rate Limit | Expires | Description |
    |-----|-------|--------|--------|------------|---------|-------------|
    | sk-emb-aaa | text-embedding-3-small | Active | $2 | 100 req/min | 48h | Embeddings OpenAI |

    ## 🚀 How to Use

    All keys work with the OpenAI API format...

    ```python
    client = OpenAI(base_url="https://aiapiv2.pekpik.com/v1", api_key="...")
    ```

    ## 📅 Changelog

    - Added 5 keys
    - Added 10 keys
    """
)


def test_parse_extracts_all_keys() -> None:
    entries = parse_readme(SAMPLE_README)
    # 2 (gpt) + 1 (dall-e) + 2 (tts) + 1 (emb) = 6
    assert len(entries) == 6
    keys = {e.key for e in entries}
    assert keys == {
        "sk-text-aaa",
        "sk-text-bbb",
        "sk-img-aaa",
        "sk-tts-aaa",
        "sk-tts-bbb",
        "sk-emb-aaa",
    }


def test_parse_populates_fields() -> None:
    entries = parse_readme(SAMPLE_README)
    gpt = next(e for e in entries if e.key == "sk-text-aaa")
    assert gpt.model == "gpt-5.5"
    assert gpt.status == "Active"
    assert gpt.budget == "$50"
    assert gpt.rate_limit == "30 req/min"
    assert gpt.expires == "48h"
    assert gpt.description == "Modèle texte principal"
    assert gpt.display_name == "GPT-5.5"


def test_parse_assigns_categories() -> None:
    entries = parse_readme(SAMPLE_README)
    by_key = {e.key: e for e in entries}
    assert by_key["sk-text-aaa"].category == ModelCategory.TEXTE
    assert by_key["sk-img-aaa"].category == ModelCategory.IMAGE
    assert by_key["sk-tts-aaa"].category == ModelCategory.TTS
    assert by_key["sk-emb-aaa"].category == ModelCategory.EMBEDDINGS


def test_parse_keeps_expired_key() -> None:
    # Le parser garde toutes les clés ; le filtrage se fait côté client.
    entries = parse_readme(SAMPLE_README)
    expired = [e for e in entries if e.status == "Expired"]
    assert len(expired) == 1
    assert expired[0].key == "sk-tts-aaa"


def test_parse_ignores_changelog_section() -> None:
    entries = parse_readme(SAMPLE_README)
    # Aucune clé ne doit provenir du changelog.
    assert all(e.key.startswith("sk-") for e in entries)


def test_parse_missing_available_keys_raises() -> None:
    with pytest.raises(ParseError):
        parse_readme("# Un README sans la bonne section\n\nRien ici.")


def test_parse_empty_raises() -> None:
    with pytest.raises(ParseError):
        parse_readme("")


def test_parse_empty_available_section_returns_empty() -> None:
    readme = "## 📋 Available Keys\n\nRien pour l'instant.\n\n## 🚀 How to Use\n\n..."
    entries = parse_readme(readme)
    assert entries == []


def test_parse_table_without_model_column_uses_display_name() -> None:
    # Tableau sans colonne "Model" : le nom vient du titre de section.
    readme = textwrap.dedent(
        """\
        ## 📋 Available Keys

        ### Claude Opus `2026-06-25T12:00Z`

        | Key | Status | Budget |
        |-----|--------|--------|
        | sk-claude-aaa | Active | $30 |

        ## 🚀 How to Use
        """
    )
    entries = parse_readme(readme)
    assert len(entries) == 1
    assert entries[0].model == "Claude Opus"
    assert entries[0].category == ModelCategory.TEXTE
