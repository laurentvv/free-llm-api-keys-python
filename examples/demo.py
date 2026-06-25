#!/usr/bin/env python3
"""Script de démonstration / test en direct contre l'API.

Teste chaque type de modèle (Texte, Image, TTS, Embeddings) avec de vrais
appels via le module ``free_llm_api_keys``. Les clés viennent automatiquement
du catalogue (mis à jour depuis GitHub si le cache est stale).

Utilisation::

    uv run python examples/demo.py                  # tout tester
    uv run python examples/demo.py --text smart-chat
    uv run python examples/demo.py --only text,embeddings
    uv run python examples/demo.py --refresh        # forcer la màj GitHub

Le script n'échoue pas si une catégorie n'a aucune clé disponible :
il l'indique et passe à la suivante.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

# Permet d'exécuter le script sans installer le paquet (depuis la racine du dépôt).
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from free_llm_api_keys import (  # noqa: E402
    Catalog,
    FreeLLMClient,
    ModelCategory,
    NoKeysAvailableError,
    AllKeysExhaustedError,
)

# ────────────────────────────────────────────────────────────────────── #
#  Utilitaires d'affichage
# ────────────────────────────────────────────────────────────────────── #
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _supports_color() -> bool:
    return sys.stdout.isatty()


def c(text: str, color: str) -> str:
    if not _supports_color():
        return text
    return f"{color}{text}{RESET}"


def header(title: str) -> None:
    line = "═" * 64
    print(f"\n{c(line, CYAN)}")
    print(c(f"  {title}", BOLD + CYAN))
    print(c(line, CYAN))


def ok(msg: str) -> None:
    print(f"{c('✓ OK', GREEN)}  {msg}")


def warn(msg: str) -> None:
    print(f"{c('! ATTENTION', YELLOW)}  {msg}")


def fail(msg: str) -> None:
    print(f"{c('✗ ÉCHEC', RED)}  {msg}")


# ────────────────────────────────────────────────────────────────────── #
#  Affichage du catalogue
# ────────────────────────────────────────────────────────────────────── #
def show_catalog(catalog: Catalog) -> None:
    header("Catalogue des clés")
    print(f"Total : {c(str(len(catalog)), BOLD)} clés")
    for cat in ModelCategory:
        models = catalog.list_models(cat)
        label = cat.value.upper()
        if models:
            sample = ", ".join(models[:6]) + ("..." if len(models) > 6 else "")
            print(f"  {label:11s} : {len(models):2d} modèle(s) → {sample}")
        else:
            print(f"  {label:11s} : {c('0 (aucune clé disponible)', YELLOW)}")


# ────────────────────────────────────────────────────────────────────── #
#  Tests par catégorie
# ────────────────────────────────────────────────────────────────────── #
def _run(name: str, fn: Callable[[], object]) -> None:
    try:
        result = fn()
    except NoKeysAvailableError as exc:
        warn(f"{name} : aucune clé disponible ({exc}).")
    except AllKeysExhaustedError as exc:
        fail(f"{name} : toutes les clés ont échoué — {exc}.")
    except Exception as exc:  # noqa: BLE001
        fail(f"{name} : erreur inattendue — {type(exc).__name__}: {exc}")
    else:
        ok(f"{name} réussi.")
        if isinstance(result, str) and result:
            preview = result.strip().replace("\n", " ")
            if len(preview) > 280:
                preview = preview[:280] + "…"
            print(f"           Réponse : {c(preview, CYAN)}")
        elif isinstance(result, list) and result and isinstance(result[0], list):
            print(f"           {len(result)} vecteur(s) de dim {len(result[0])}")
        elif isinstance(result, list) and result:
            print(f"           {len(result)} résultat(s) : {c(str(result[0])[:120], CYAN)}")
        elif isinstance(result, (bytes, bytearray)) and result:
            print(f"           Audio : {len(result)} octets")


def test_text(model: str | None) -> None:
    header("Test — Texte (chat)")
    if model is None:
        models = Catalog.load().list_models(ModelCategory.TEXTE)
        if not models:
            warn("Aucun modèle texte dans le catalogue.")
            return
        print(f"Essai successif parmi {len(models)} modèles candidats.")
    else:
        models = [model]
        print(f"Modèle demandé : {c(model, BOLD)}")

    # Certains modèles du catalogue n'ont pas d'endpoint actif (404) ou leurs
    # clés sont épuisées. On en essaie plusieurs jusqu'à obtenir une réponse.
    for candidate in models:
        print(f"\n→ Essai : {c(candidate, BOLD)}")
        try:
            client = FreeLLMClient(model=candidate)
            response = client.chat(
                [{"role": "user", "content": "Réponds uniquement par 'pong'."}],
                max_tokens=20,
            )
        except NoKeysAvailableError as exc:
            warn(f"aucune clé ({exc}).")
            continue
        except AllKeysExhaustedError as exc:
            warn(f"toutes les clés ont échoué. On essaie le suivant.")
            continue
        except Exception as exc:  # noqa: BLE001
            warn(f"{type(exc).__name__}: {exc}")
            continue
        else:
            preview = response.strip().replace("\n", " ")[:120]
            ok(f"chat({candidate}) réussi. Réponse : {c(preview, CYAN)}")
            return
    fail("Aucun modèle texte n'a répondu.")


def test_image() -> None:
    header("Test — Génération d'images")
    models = Catalog.load().list_models(ModelCategory.IMAGE)
    if not models:
        warn("Aucun modèle d'image disponible pour le moment (liste mise à jour 3-5x/jour).")
        return
    model = models[0]
    print(f"Modèle : {c(model, BOLD)}")

    def _do() -> list[str]:
        client = FreeLLMClient(model=model)
        return client.generate_image("A minimal red cube on white background", n=1)

    _run(f"generate_image({model})", _do)


def test_tts() -> None:
    header("Test — Synthèse vocale (TTS)")
    models = Catalog.load().list_models(ModelCategory.TTS)
    if not models:
        warn("Aucun modèle TTS disponible pour le moment.")
        return
    model = models[0]
    print(f"Modèle : {c(model, BOLD)}")

    def _do() -> bytes:
        client = FreeLLMClient(model=model)
        return client.tts("Ceci est un test de synthèse vocale.")

    _run(f"tts({model})", _do)


def test_embeddings(model: str | None) -> None:
    header("Test — Embeddings")
    if model is None:
        models = Catalog.load().list_models(ModelCategory.EMBEDDINGS)
        if not models:
            warn("Aucun modèle d'embeddings dans le catalogue.")
            return
        model = models[0]
        print(f"Modèle auto-sélectionné : {c(model, BOLD)}")
    else:
        print(f"Modèle demandé : {c(model, BOLD)}")

    def _do() -> list[list[float]]:
        client = FreeLLMClient(model=model)
        return client.embeddings(["bonjour le monde", "hello world"])

    _run(f"embeddings({model})", _do)


# ────────────────────────────────────────────────────────────────────── #
#  Point d'entrée
# ────────────────────────────────────────────────────────────────────── #
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Test en direct du module free_llm_api_keys.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--text", metavar="MODÈLE", help="Modèle texte à tester (défaut : 1er dispo).")
    p.add_argument("--embeddings", metavar="MODÈLE", help="Modèle embeddings à tester.")
    p.add_argument(
        "--only",
        metavar="LISTE",
        help="Catégories à tester, séparées par virgule (text,image,tts,embeddings).",
    )
    p.add_argument("--refresh", action="store_true", help="Forcer la mise à jour depuis GitHub.")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    # Chargement / mise à jour du catalogue (1 fois, partagé par tous les tests).
    catalog = Catalog.load(force_refresh=args.refresh)
    show_catalog(catalog)

    if args.only:
        wanted = {part.strip().lower() for part in args.only.split(",")}
    else:
        wanted = {"text", "image", "tts", "embeddings"}

    if "text" in wanted:
        test_text(args.text)
    if "image" in wanted:
        test_image()
    if "tts" in wanted:
        test_tts()
    if "embeddings" in wanted:
        test_embeddings(args.embeddings)

    header("Terminé")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
