"""Derivation of the French departement from a LinkedIn location (POC-015).

Pure business logic: no Streamlit, no Playwright, no network call, no LLM. The
client asked on 11/09/2026 for a departement column to *sort* the deliverable;
geography stays an accessory criterion, so this is neither a filter nor a score.

The single rule of this module: a location that cannot be tied to exactly one
departement gives an empty string, never a guess. Only the
"Commune, Region, France" form is derivable. "Paris et peripherie" is a LinkedIn
urban area and not a departement, a region or a country alone says nothing, and
a commune name carried by two departements of the same region (Floirac in
Gironde and in Charente-Maritime) stays empty.

The reference tables live in config/ and are static: they were reduced once
from INSEE's Code officiel geographique (edition 2025, Licence Ouverte), no
network call is ever made at run time.
"""

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from source.backend.core.profile_scoring import normaliser

# config/ sits at the repository root, three levels above this module.
_CONFIG = Path(__file__).resolve().parents[3] / "config"
DEFAULT_DEPARTEMENTS_PATH = _CONFIG / "departements.csv"
DEFAULT_COMMUNES_PATH = _CONFIG / "communes_departements.csv"

_PAYS = "france"
# LinkedIn names the capital "Ville de Paris" on some profiles; the prefix is
# dropped only when the name as written is not a commune.
_PREFIXE_VILLE = "ville de "


@dataclass(frozen=True)
class TableDepartements:
    """Lookup tables, keyed on normalised names (see profile_scoring.normaliser)."""

    # departement code -> exported label, e.g. "67" -> "67 - Bas-Rhin"
    libelles: dict[str, str]
    # (commune, region) -> codes of every departement holding a commune of that name
    communes: dict[tuple[str, str], frozenset[str]]


def charger_table(
    chemin_departements: Path | None = None, chemin_communes: Path | None = None
) -> TableDepartements:
    """Load the departement and commune tables from their CSV files."""
    with open(chemin_departements or DEFAULT_DEPARTEMENTS_PATH, newline="", encoding="utf-8") as f:
        departements = list(csv.DictReader(f))

    libelles = {d["code"]: f"{d['code']} - {d['nom']}" for d in departements}
    regions = {d["code"]: normaliser(d["region"]) for d in departements}

    communes: dict[tuple[str, str], set[str]] = {}
    with open(chemin_communes or DEFAULT_COMMUNES_PATH, newline="", encoding="utf-8") as f:
        for ligne in csv.DictReader(f):
            code = ligne["departement"]
            cle = (normaliser(ligne["commune"]), regions[code])
            communes.setdefault(cle, set()).add(code)

    return TableDepartements(
        libelles=libelles,
        communes={cle: frozenset(codes) for cle, codes in communes.items()},
    )


@lru_cache(maxsize=1)
def _table_par_defaut() -> TableDepartements:
    return charger_table()


def deriver_departement(localisation: str | None, table: TableDepartements | None = None) -> str:
    """Return "NN - Nom" for a "Commune, Region, France" location, else "".

    Empty whenever the location is not in that form, the commune is unknown in
    that region, or several departements of the region hold a commune of that
    name.
    """
    parties = [p.strip() for p in (localisation or "").split(",") if p.strip()]
    if len(parties) != 3 or normaliser(parties[2]) != _PAYS:
        return ""

    table = table or _table_par_defaut()
    commune, region = normaliser(parties[0]), normaliser(parties[1])
    codes = table.communes.get((commune, region))
    if codes is None and commune.startswith(_PREFIXE_VILLE):
        codes = table.communes.get((commune.removeprefix(_PREFIXE_VILLE), region))

    if codes is None or len(codes) != 1:
        return ""
    return table.libelles[next(iter(codes))]
