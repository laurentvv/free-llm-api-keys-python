"""Tests du système de santé (health.json) et du filtrage du catalogue."""

from __future__ import annotations

from free_llm_api_keys.catalog import Catalog
from free_llm_api_keys.classifier import ModelCategory
from free_llm_api_keys.health import HealthStatus, HealthStore
from free_llm_api_keys.parser import KeyEntry


def _keys() -> list[KeyEntry]:
    return [
        KeyEntry(key="sk-1", model="good-model", category=ModelCategory.TEXTE),
        KeyEntry(key="sk-2", model="good-model", category=ModelCategory.TEXTE),
        KeyEntry(key="sk-3", model="bad-model", category=ModelCategory.TEXTE),
        KeyEntry(key="sk-4", model="text-embedding-3-small",
                 category=ModelCategory.EMBEDDINGS),
    ]


# ────────────────────────────────────────────────────────────────── #
#  HealthStore : persistance + reset
# ────────────────────────────────────────────────────────────────── #
def test_health_store_round_trip(tmp_path) -> None:
    store = HealthStore(tmp_path / "health.json")
    state = store.load(readme_updated_at="v1")
    state.set("good-model", HealthStatus.OK)
    state.set("bad-model", HealthStatus.FAILED, last_error="404")
    store.save(state)

    # Recharger sans reset conserve l'état.
    reloaded = HealthStore(tmp_path / "health.json").load(readme_updated_at="v1")
    assert reloaded.status_of("good-model") == HealthStatus.OK
    assert reloaded.status_of("bad-model") == HealthStatus.FAILED
    assert reloaded.models["bad-model"].last_error == "404"


def test_health_resets_when_readme_version_changes(tmp_path) -> None:
    store = HealthStore(tmp_path / "health.json")
    state = store.load(readme_updated_at="v1")
    state.set("bad-model", HealthStatus.FAILED)
    store.save(state)
    assert store.load("v1").status_of("bad-model") == HealthStatus.FAILED

    # Le README change de version → reset automatique.
    new_state = store.load(readme_updated_at="v2")
    assert new_state.status_of("bad-model") == HealthStatus.UNKNOWN
    assert new_state.readme_updated_at == "v2"


def test_health_mark_persists(tmp_path) -> None:
    store = HealthStore(tmp_path / "health.json")
    store.mark("m1", HealthStatus.FAILED, readme_updated_at="v1", last_error="boom")
    assert store.load("v1").status_of("m1") == HealthStatus.FAILED


# ────────────────────────────────────────────────────────────────── #
#  Catalogue : filtrage par santé
# ────────────────────────────────────────────────────────────────── #
def test_catalog_mark_failed_filters_list_models(tmp_path) -> None:
    cache = str(tmp_path / "catalog.json")
    catalog = Catalog(_keys(), cache_path=cache, readme_updated_at="v1")

    # Avant : tous les modèles texte sont listés.
    assert "good-model" in catalog.list_models(ModelCategory.TEXTE)
    assert "bad-model" in catalog.list_models(ModelCategory.TEXTE)

    catalog.mark_failed("bad-model", reason="404 No endpoints")

    # only_healthy=True exclut le modèle FAILED.
    healthy = catalog.list_models(ModelCategory.TEXTE, only_healthy=True)
    assert "good-model" in healthy
    assert "bad-model" not in healthy

    # Sans filtre, on garde tout (le catalogue reste complet).
    all_models = catalog.list_models(ModelCategory.TEXTE)
    assert "bad-model" in all_models


def test_catalog_health_status_unknown_by_default(tmp_path) -> None:
    cache = str(tmp_path / "catalog.json")
    catalog = Catalog(_keys(), cache_path=cache, readme_updated_at="v1")
    assert catalog.health_status("good-model") == HealthStatus.UNKNOWN


def test_catalog_health_report(tmp_path) -> None:
    cache = str(tmp_path / "catalog.json")
    catalog = Catalog(_keys(), cache_path=cache, readme_updated_at="v1")
    catalog.mark_ok("good-model")
    catalog.mark_failed("bad-model", reason="x")

    report = catalog.health_report()
    assert report["good-model"] == "ok"
    assert report["bad-model"] == "failed"
    assert report["text-embedding-3-small"] == "unknown"
