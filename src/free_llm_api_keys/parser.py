"""Parsing du README de ``alistaitsacle/free-llm-api-keys``.

Le README contient une section ``## 📋 Available Keys`` qui liste les clés
sous forme de tableaux markdown, un tableau par modèle. On parse uniquement
cette section (et on ignore l'énorme changelog en dessous de ``## 🚀 How to Use``).

Structure attendue par modèle :

    ### Nom du modèle `2026-06-25T12:00Z`

    | Key | Model | Status | Budget | Rate Limit | Expires | Description |
    |-----|-------|--------|--------|------------|---------|-------------|
    | sk-xxxx | gpt-5.5 | Active | $X | Y req/min | 48h | ... |

Le nombre/ordre des colonnes peut varier légèrement : on se cale sur l'en-tête
du tableau pour être robuste.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Iterable

from .classifier import ModelCategory, classify
from .exceptions import ParseError

# Marqueurs de section (le séparateur d'en-tête de colonnes dans un tableau md).
_TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{3,}.*$")

# En-tête de modèle : ``### Nom `timestamp``` ou simplement ``### Nom``.
_MODEL_HEADER_RE = re.compile(r"^###\s+(.+?)(?:\s+`([^`]+)`)?\s*$")

# Ligne de date globale du README : ``> ⏰ Last updated: 2026-06-25 19:22 (UTC+8)``.
_LAST_UPDATED_RE = re.compile(
    r"Last updated:\s*([0-9]{4}-[0-9]{2}-[0-9]{2}\s+[0-9]{2}:[0-9]{2})", re.IGNORECASE
)

# Bornes de la section à parser. On normalise les espaces pour repérer
# ces titres indépendamment des variations d'emoji/spacing.
_AVAILABLE_KEYS_RE = re.compile(r"^##\s+.*Available Keys", re.IGNORECASE)
_HOW_TO_USE_RE = re.compile(r"^##\s+.*How to Use", re.IGNORECASE)

# Colonnes reconnues -> nom de champ normalisé. On matche sur des substrings
# insensibles à la casse pour tolérer les variations d'en-tête.
_COLUMN_ALIASES: dict[str, str] = {
    "key": "key",
    "model": "model",
    "status": "status",
    "budget": "budget",
    "rate": "rate_limit",
    "rate limit": "rate_limit",
    "expires": "expires",
    "expiry": "expires",
    "description": "description",
    "notes": "description",
}


@dataclass
class KeyEntry:
    """Une clé API associée à un modèle, telle qu'extraite du README."""

    key: str
    model: str
    status: str = ""
    budget: str = ""
    rate_limit: str = ""
    expires: str = ""
    description: str = ""
    display_name: str = ""
    category: ModelCategory = ModelCategory.TEXTE
    # Horodatage lu dans le titre ``### Nom `MM-DD HH:MM``` (heure d'ajout
    # de la section dans le README source). Sert au suivi / nettoyage.
    source_timestamp: str = ""

    def to_dict(self) -> dict[str, object]:
        d = asdict(self)
        # Les enums ne sont pas sérialisables en JSON tels quels.
        d["category"] = self.category.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "KeyEntry":
        category = data.get("category", ModelCategory.TEXTE)
        if isinstance(category, str):
            category = ModelCategory(category)
        return cls(
            key=str(data.get("key", "")),
            model=str(data.get("model", "")),
            status=str(data.get("status", "")),
            budget=str(data.get("budget", "")),
            rate_limit=str(data.get("rate_limit", "")),
            expires=str(data.get("expires", "")),
            description=str(data.get("description", "")),
            display_name=str(data.get("display_name", "")),
            category=category,  # type: ignore[arg-type]
            source_timestamp=str(data.get("source_timestamp", "")),
        )


# Champs qui ne sont jamais sensibles au statut "expiré" pour le parsing :
# on garde tout, c'est le client qui décide quoi faire.


def _slice_section(lines: list[str]) -> list[str]:
    """Extrait les lignes comprises entre ``Available Keys`` et ``How to Use``."""
    start: int | None = None
    end: int | None = None
    for i, line in enumerate(lines):
        if start is None:
            if _AVAILABLE_KEYS_RE.match(line):
                start = i + 1
        else:
            if _HOW_TO_USE_RE.match(line):
                end = i
                break
    if start is None:
        raise ParseError(
            "Section 'Available Keys' introuvable dans le README ; "
            "la structure du document a peut-être changé."
        )
    # Si on ne trouve pas la fin, on va jusqu'au bout du document.
    return lines[start : end if end is not None else len(lines)]


def _parse_header(header_line: str) -> list[str] | None:
    """Lit l'en-tête d'un tableau markdown -> liste de noms de champs normalisés.

    Retourne ``None`` si la ligne n'est pas un en-tête de tableau valide.
    """
    if "|" not in header_line:
        return None
    cells = [c.strip() for c in header_line.strip().strip("|").split("|")]
    if not cells or all(not c for c in cells):
        return None
    fields_: list[str] = []
    for cell in cells:
        key = cell.lower()
        fields_.append(_COLUMN_ALIASES.get(key, key.replace(" ", "_")))
    return fields_


def _parse_row(row_line: str) -> list[str]:
    cells = [c.strip() for c in row_line.strip().strip("|").split("|")]
    return cells


def _is_row(line: str) -> bool:
    return line.lstrip().startswith("|") and "|" in line.lstrip()[1:]


def _build_entry(
    fields_: list[str], cells: list[str], display_name: str, timestamp: str = ""
) -> KeyEntry | None:
    """Construit une :class:`KeyEntry` à partir d'une ligne de tableau.

    Retourne ``None`` si la ligne n'a pas de clé exploitable.
    """
    row = dict(zip(fields_, cells))
    key = (row.get("key") or "").strip()
    if not key:
        return None
    # Nettoyage : retirer les backticks/espaces autour de la clé.
    key = key.strip("`").strip()
    if not key:
        return None
    model = (row.get("model") or display_name or "").strip().strip("`")
    if not model:
        # Si le tableau n'a pas de colonne "model" lisible, on retombe
        # sur le nom affiché dans le titre de la sous-section.
        model = display_name
    return KeyEntry(
        key=key,
        model=model,
        status=(row.get("status") or "").strip(),
        budget=(row.get("budget") or "").strip(),
        rate_limit=(row.get("rate_limit") or "").strip(),
        expires=(row.get("expires") or "").strip(),
        description=(row.get("description") or "").strip(),
        display_name=display_name,
        category=classify(model),
        source_timestamp=timestamp,
    )


def extract_readme_updated_at(markdown: str) -> str:
    """Extrait la date globale ``Last updated: ...`` du README.

    Retourne la chaîne brute (ex. ``"2026-06-25 19:22"``) ou ``""`` si
    introuvable. C'est l'identifiant de version du catalogue : quand il
    change, l'état de santé (ce qui marche / ne marche pas) est réinitialisé.
    """
    for line in markdown.splitlines():
        m = _LAST_UPDATED_RE.search(line)
        if m:
            return m.group(1).strip()
    return ""


@dataclass
class ParsedCatalog:
    """Résultat complet du parsing : clés + date de version du README."""

    keys: list[KeyEntry]
    readme_updated_at: str = ""


def parse_readme_full(markdown: str) -> ParsedCatalog:
    """Parse le README -> :class:`ParsedCatalog` (clés + date de version).

    Variante enrichie de :func:`parse_readme` qui renvoie aussi la date
    ``Last updated`` du README (identifiant de version pour le suivi).
    """
    if not markdown or not markdown.strip():
        raise ParseError("README vide.")

    readme_updated_at = extract_readme_updated_at(markdown)

    lines = markdown.splitlines()
    section = _slice_section(lines)

    entries: list[KeyEntry] = []
    current_display_name = ""
    current_timestamp = ""

    i = 0
    n = len(section)
    while i < n:
        line = section[i]

        # Titre de modèle ?
        header_match = _MODEL_HEADER_RE.match(line)
        if header_match:
            current_display_name = (header_match.group(1) or "").strip()
            # Le 2e groupe de capture est le timestamp ``MM-DD HH:MM``.
            current_timestamp = (header_match.group(2) or "").strip()
            i += 1
            continue

        # Début d'un tableau ? On cherche l'en-tête puis la ligne de séparation.
        if _is_row(line):
            fields_ = _parse_header(line)
            if fields_ is not None:
                # La ligne suivante doit être le séparateur |---|---|.
                if i + 1 < n and _TABLE_SEP_RE.match(section[i + 1]):
                    i += 2  # skip header + separator
                    # Lignes de données jusqu'à sortir du tableau.
                    while i < n and _is_row(section[i]):
                        cells = _parse_row(section[i])
                        entry = _build_entry(
                            fields_, cells, current_display_name, current_timestamp
                        )
                        if entry is not None:
                            entries.append(entry)
                        i += 1
                    continue
                # Sinon, c'est peut-être un tableau sans séparateur clair :
                # on tente quand même les lignes suivantes.
                i += 1
                while i < n and _is_row(section[i]):
                    cells = _parse_row(section[i])
                    entry = _build_entry(
                        fields_, cells, current_display_name, current_timestamp
                    )
                    if entry is not None:
                        entries.append(entry)
                    i += 1
                continue

        i += 1

    return ParsedCatalog(keys=entries, readme_updated_at=readme_updated_at)


def parse_readme(markdown: str) -> list[KeyEntry]:
    """Parse le contenu markdown du README -> liste de :class:`KeyEntry`.

    Robuste aux variations de format : se cale sur l'en-tête de chaque
    tableau pour nommer les colonnes, ignore les tableaux sans clé,
    ignore les statuts (on garde toutes les clés, le filtrage se fait
    côté client).

    Pour obtenir aussi la date de version du README, préférer
    :func:`parse_readme_full`.

    Args:
        markdown: Contenu brut du fichier ``README.md``.

    Returns:
        Liste des clés trouvées (potentiellement vide si la section
        ne contient aucune clé).

    Raises:
        ParseError: Si la section ``Available Keys`` est absente.
    """
    return parse_readme_full(markdown).keys


def dedupe(entries: Iterable[KeyEntry]) -> list[KeyEntry]:
    """Supprime les doublons (même clé) en conservant l'ordre de première occurrence."""
    seen: set[str] = set()
    out: list[KeyEntry] = []
    for e in entries:
        if e.key in seen:
            continue
        seen.add(e.key)
        out.append(e)
    return out
