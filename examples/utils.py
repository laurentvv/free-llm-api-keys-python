"""Utilitaires partagés pour les exemples."""

from __future__ import annotations

import sys
from pathlib import Path

# Permet d'exécuter le script sans installer le paquet (depuis la racine du dépôt).
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

def _c(text: str, color: str) -> str:
    return f"{color}{text}{RESET}" if sys.stdout.isatty() else str(text)
