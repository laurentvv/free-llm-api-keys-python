"""Tests du cache du catalogue (cycle save/load + staleness)."""

from __future__ import annotations

from datetime import timedelta

from free_llm_api_keys.cache import CacheEntry
from free_llm_api_keys.cache import _now as now_utc
from free_llm_api_keys.classifier import ModelCategory
from free_llm_api_keys.parser import KeyEntry


def test_round_trip_preserves_keys(tmp_path) -> None:
    from free_llm_api_keys.cache import CatalogCache

    cache = CatalogCache(tmp_path / "catalog.json")
    keys = [
        KeyEntry(key="sk-1", model="gpt-5.5", category=ModelCategory.TEXTE),
        KeyEntry(key="sk-2", model="dall-e-3", category=ModelCategory.IMAGE),
    ]
    cache.save(keys, etag="W/\"abc\"")

    loaded = cache.load()
    assert loaded is not None
    assert loaded.etag == "W/\"abc\""
    assert [k.key for k in loaded.keys] == ["sk-1", "sk-2"]
    assert loaded.keys[1].category == ModelCategory.IMAGE


def test_load_missing_returns_none(tmp_path) -> None:
    from free_llm_api_keys.cache import CatalogCache

    cache = CatalogCache(tmp_path / "absent.json")
    assert cache.load() is None


def test_entry_fresh_then_stale() -> None:
    fresh = CacheEntry(fetched_at=now_utc(), etag=None, keys=[])
    assert fresh.is_stale(ttl_seconds=3600) is False

    old = CacheEntry(fetched_at=now_utc() - timedelta(hours=2), etag=None, keys=[])
    assert old.is_stale(ttl_seconds=3600) is True
