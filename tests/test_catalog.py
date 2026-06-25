"""Tests du catalogue : fetch+parse via httpx simulé, et fallback hors-ligne.

Aucune requête réseau réelle : on utilise ``httpx.MockTransport`` pour
servir un README de test, et un transport en erreur pour simuler le
hors-ligne.
"""

from __future__ import annotations

import httpx
import pytest

from free_llm_api_keys.catalog import Catalog
from free_llm_api_keys.classifier import ModelCategory
from free_llm_api_keys.exceptions import FetchError

SAMPLE_README = """\
# Free LLM API Keys

## 📋 Available Keys

### GPT-5.5 `2026-06-25T12:00Z`

| Key | Model | Status | Budget | Rate Limit | Expires | Description |
|-----|-------|--------|--------|------------|---------|-------------|
| sk-text-aaa | gpt-5.5 | Active | $50 | 30 req/min | 48h | Texte |

### DALL-E 3 `2026-06-25T12:00Z`

| Key | Model | Status | Budget | Rate Limit | Expires | Description |
|-----|-------|--------|--------|------------|---------|-------------|
| sk-img-aaa | dall-e-3 | Active | $10 | 5 req/min | 48h | Image |

## 🚀 How to Use

...
"""


def _ok_client(body: str = SAMPLE_README) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=body, headers={"ETag": "W/\"v1\""})
    return httpx.Client(transport=httpx.MockTransport(handler))


def _error_client() -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_catalog_fetch_and_parse(tmp_path) -> None:
    cache_file = str(tmp_path / "catalog.json")
    catalog = Catalog.load(
        force_refresh=True,
        cache_path=cache_file,
        http_client=_ok_client(),
    )
    assert len(catalog) == 2
    assert "dall-e-3" in catalog.list_models()
    assert "gpt-5.5" in catalog.list_models()
    assert catalog.list_models(ModelCategory.IMAGE) == ["dall-e-3"]
    assert catalog.list_models(ModelCategory.TTS) == []


def test_catalog_uses_cache_when_fresh(tmp_path) -> None:
    # 1er chargement : fetch + écrit cache.
    cache_file = str(tmp_path / "catalog.json")
    catalog = Catalog.load(
        force_refresh=True, cache_path=cache_file, http_client=_ok_client()
    )
    assert len(catalog) == 2

    # 2e chargement sans force_refresh : on NE doit PAS faire de réseau.
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, text=SAMPLE_README)

    catalog2 = Catalog.load(
        cache_path=cache_file, http_client=httpx.Client(transport=httpx.MockTransport(handler))
    )
    assert calls["n"] == 0  # cache frais, pas de réseau
    assert len(catalog2) == 2


def test_catalog_offline_falls_back_to_stale_cache(tmp_path) -> None:
    cache_file = str(tmp_path / "catalog.json")
    # Pré-remplir un cache, puis le rendre stale via force_refresh hors-ligne.
    Catalog.load(force_refresh=True, cache_path=cache_file, http_client=_ok_client())

    # Hors-ligne + force_refresh : on doit retomber sur le cache.
    catalog = Catalog.load(
        force_refresh=True, cache_path=cache_file, http_client=_error_client()
    )
    assert len(catalog) == 2  # données du cache


def test_catalog_offline_without_cache_raises(tmp_path) -> None:
    cache_file = str(tmp_path / "catalog.json")
    with pytest.raises(FetchError):
        Catalog.load(force_refresh=True, cache_path=cache_file, http_client=_error_client())


def test_catalog_get_keys(tmp_path) -> None:
    cache_file = str(tmp_path / "catalog.json")
    catalog = Catalog.load(
        force_refresh=True, cache_path=cache_file, http_client=_ok_client()
    )
    keys = catalog.get_keys("gpt-5.5")
    assert len(keys) == 1
    assert keys[0].key == "sk-text-aaa"
    assert catalog.get_keys("inexistant") == []
