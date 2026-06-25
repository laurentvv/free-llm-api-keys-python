#!/usr/bin/env python3
"""Script de « nettoyage » : probe chaque modèle et enregistre l'état de santé.

Pour chaque modèle du catalogue, on fait un appel léger (1 token) pour
vérifier qu'il répond. Le résultat est persisté dans ``health.json`` :

  - ``OK``      → le modèle fonctionne,
  - ``FAILED``  → défaillant (endpoint inactif / clés épuisées).

L'état est rattaché à la version du README : si le README source est mis
à jour (date ``Last updated`` qui change), l'état est réinitialisé
automatiquement et le prochain nettoyage re-testera tout.

Par défaut, seules les catégories **bon marché** (Texte, Embeddings) sont
probe : générer une vraie image / audio consomme du budget des clés
partagées. On peut forcer l'image/TTS avec ``--full``.

Utilisation::

    uv run python examples/cleanup.py             # texte + embeddings
    uv run python examples/cleanup.py --full      # + image + tts (coûteux)
    uv run python examples/cleanup.py --refresh   # forcer la màj GitHub avant
    uv run python examples/cleanup.py --report    # seulement afficher health.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from free_llm_api_keys import (  # noqa: E402
    AllKeysExhaustedError,
    Catalog,
    FreeLLMClient,
    ModelCategory,
    NoKeysAvailableError,
)

# ────────────────────────────────────────────────────────────────────── #
#  Couleurs
# ────────────────────────────────────────────────────────────────────── #
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def _c(text: str, color: str) -> str:
    return f"{color}{text}{RESET}" if sys.stdout.isatty() else text


# ────────────────────────────────────────────────────────────────────── #
#  Probes par catégorie
# ────────────────────────────────────────────────────────────────────── #
def probe_text(catalog: Catalog, model: str) -> tuple[bool, str]:
    """Probe un modèle texte (chat) : 1 appel court à 1 token."""
    try:
        client = FreeLLMClient(model=model, catalog=catalog)
        client.chat(
            [{"role": "user", "content": "ping"}], max_tokens=1
        )
        return True, ""
    except (AllKeysExhaustedError, NoKeysAvailableError) as exc:
        return False, str(exc)
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


def probe_embeddings(catalog: Catalog, model: str) -> tuple[bool, str]:
    """Probe un modèle d'embeddings : 1 mot."""
    try:
        client = FreeLLMClient(model=model, catalog=catalog)
        client.embeddings(["ping"])
        return True, ""
    except (AllKeysExhaustedError, NoKeysAvailableError) as exc:
        return False, str(exc)
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


def probe_image(catalog: Catalog, model: str) -> tuple[bool, str]:
    """Probe un modèle d'image : 1 image 256×256 (coûteux)."""
    try:
        client = FreeLLMClient(model=model, catalog=catalog)
        client.generate_image("a dot", n=1, size="256x256")
        return True, ""
    except (AllKeysExhaustedError, NoKeysAvailableError) as exc:
        return False, str(exc)
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


def probe_tts(catalog: Catalog, model: str) -> tuple[bool, str]:
    """Probe un modèle TTS : 1 mot (coûteux)."""
    try:
        client = FreeLLMClient(model=model, catalog=catalog)
        client.tts("hi")
        return True, ""
    except (AllKeysExhaustedError, NoKeysAvailableError) as exc:
        return False, str(exc)
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


# ────────────────────────────────────────────────────────────────────── #
#  Orchestration du nettoyage
# ────────────────────────────────────────────────────────────────────── #
# (catégorie, fonction de probe, libellé, coûteux ?)
PROBES = [
    (ModelCategory.TEXTE, probe_text, "Texte", False),
    (ModelCategory.EMBEDDINGS, probe_embeddings, "Embeddings", False),
    (ModelCategory.IMAGE, probe_image, "Image", True),
    (ModelCategory.TTS, probe_tts, "TTS", True),
]


def run_cleanup(catalog: Catalog, *, full: bool) -> dict[str, dict[str, object]]:
    """Probe toutes les catégories pertinentes ; retourne le rapport."""
    total_ok = 0
    total_fail = 0
    report: dict[str, dict[str, object]] = {}

    for category, probe, label, costly in PROBES:
        if costly and not full:
            continue
        models = catalog.list_models(category)
        if not models:
            print(_c(f"\n{label} : aucun modèle — ignoré.", YELLOW))
            continue

        print(_c(f"\n{'─' * 60}", DIM))
        print(_c(f" {label}  ({len(models)} modèle(s))", BOLD + CYAN))
        print(_c("─" * 60, DIM))

        for model in models:
            ok, err = probe(catalog, model)
            report[model] = {
                "category": category.value,
                "ok": ok,
                "error": err,
            }
            if ok:
                total_ok += 1
                print(f"  {_c('OK  ', GREEN)} {model}")
            else:
                total_fail += 1
                reason = err[:80].replace("\n", " ")
                print(f"  {_c('FAIL', RED)} {model}  {_c(reason, DIM)}")

    print(_c("\n" + "═" * 60, CYAN))
    print(
        _c(f"  Bilan : ", BOLD)
        + _c(f"{total_ok} OK", GREEN)
        + ", "
        + _c(f"{total_fail} défaillants", RED if total_fail else DIM)
    )
    print(_c("═" * 60, CYAN))
    return report


# ────────────────────────────────────────────────────────────────────── #
#  Affichage seul du rapport existant
# ────────────────────────────────────────────────────────────────────── #
def show_report(catalog: Catalog) -> None:
    report = catalog.health_report()
    if not report:
        print(_c("Aucun état de santé enregistré. Lancez le nettoyage.", YELLOW))
        return

    print(_c(f"\nVersion du README : {catalog.readme_updated_at or '?'}\n", CYAN))
    # Regroupé par statut.
    by_status: dict[str, list[str]] = {}
    for model, status in report.items():
        by_status.setdefault(status, []).append(model)

    for status in ("ok", "failed", "unknown"):
        models = sorted(by_status.get(status, []))
        if not models:
            continue
        color = {"ok": GREEN, "failed": RED, "unknown": YELLOW}[status]
        print(_c(f"  {status.upper()} ({len(models)})", BOLD + color))
        for m in models:
            print(f"    {m}")
    print()


# ────────────────────────────────────────────────────────────────────── #
#  Point d'entrée
# ────────────────────────────────────────────────────────────────────── #
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Nettoie le catalogue : probe chaque modèle et enregistre l'état de santé.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--refresh", action="store_true", help="Forcer la màj GitHub avant le nettoyage.")
    p.add_argument("--full", action="store_true", help="Probe aussi image + tts (coûteux en budget).")
    p.add_argument("--report", action="store_true", help="Afficher seulement l'état de santé existant.")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    catalog = Catalog.load(force_refresh=args.refresh)

    print(_c("═" * 60, CYAN))
    print(_c("  Nettoyage du catalogue", BOLD + CYAN))
    print(_c(f"  Version README : {catalog.readme_updated_at or '?'}", DIM))
    print(_c(f"  Total : {len(catalog)} clés, {len(catalog.list_models())} modèles", DIM))
    print(_c("═" * 60, CYAN))

    if args.report:
        show_report(catalog)
        return 0

    run_cleanup(catalog, full=args.full)
    print(_c("\nÉtat de santé enregistré dans health.json.", DIM))
    print(_c("Astuce : `Catalog.list_models(only_healthy=True)` skip les modèles FAILED.", DIM))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
