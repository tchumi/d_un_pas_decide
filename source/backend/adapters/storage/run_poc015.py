"""POC-015 entry script: regenerate the export and the client workbook, read-only.

READ-ONLY on the store, opened with SQLite's `mode=ro` (same guarantee as
run_poc014_evaluation): the departement column is derived at export time, so
nothing has to be written back. This is also why the script exists next to
run_poc003, which produces the same CSV but rewrites the scoring columns on
its way.

It writes profils_magasin.csv then profils_magasin.xlsx, and publishes how many
profiles could be tied to a departement and how many were left blank, with the
blank locations listed - a blank is an assumed outcome, never a guess, and the
list is how a new unresolved spelling gets noticed.

No LinkedIn run, no browser, no network call.

Usage:
    python -m source.backend.adapters.storage.run_poc015

Run standalone (never via `streamlit run`, see CLAUDE.md rule 6).
"""

import sqlite3
import sys
from collections import Counter
from pathlib import Path

from source.backend.adapters.storage.csv_export import EXPORT_CSV, export_profiles_to_csv
from source.backend.adapters.storage.profile_store import DEFAULT_DB_PATH, lister_profils
from source.backend.adapters.storage.xlsx_export import EXPORT_XLSX, convertir_csv_en_xlsx
from source.backend.core.departement import deriver_departement


def lister_profils_lecture_seule(db_path: Path | str = DEFAULT_DB_PATH) -> list[dict[str, str]]:
    """Return the exported view of the store through a read-only connection."""
    uri = f"file:{Path(db_path).resolve().as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        conn.row_factory = sqlite3.Row
        return lister_profils(conn)
    finally:
        conn.close()


def compter_rattachements(profils: list[dict[str, str]]) -> tuple[Counter, Counter]:
    """Count the profiles per departement, and per location left without one."""
    rattaches: Counter = Counter()
    non_rattaches: Counter = Counter()
    for profil in profils:
        localisation = profil.get("localisation", "")
        departement = deriver_departement(localisation)
        if departement:
            rattaches[departement] += 1
        else:
            non_rattaches[localisation] += 1
    return rattaches, non_rattaches


def main(
    db_path: Path = DEFAULT_DB_PATH, csv_path: Path = EXPORT_CSV, xlsx_path: Path = EXPORT_XLSX
) -> None:
    # Locations carry accents: a cp1252 console must not kill the report (POC-009).
    sys.stdout.reconfigure(errors="replace")
    if not db_path.exists():
        print(f"Magasin introuvable : {db_path.resolve()}")
        return

    profils = lister_profils_lecture_seule(db_path)
    print(f"{len(profils)} profils lus (lecture seule) depuis le magasin {db_path}")
    # Same row order as run_poc003, so the client keeps reviewing a ranking: by
    # descending score, a profile not scored yet going last.
    profils.sort(key=lambda p: int(p["score"] or 0), reverse=True)

    export_profiles_to_csv(profils, csv_path)
    lignes = convertir_csv_en_xlsx(csv_path, xlsx_path)
    print(f"Export CSV ecrit dans {csv_path.resolve()}")
    print(f"Livrable client ecrit dans {xlsx_path.resolve()} ({lignes} lignes)")

    rattaches, non_rattaches = compter_rattachements(profils)
    print(
        f"\nDepartement : {sum(rattaches.values())} profils rattaches "
        f"({len(rattaches)} departements), {sum(non_rattaches.values())} laisses vides"
    )
    for departement, nombre in sorted(rattaches.items()):
        print(f"  {nombre:>3}  {departement}")
    print("\nLocalisations laissees vides (jamais devinees) :")
    for localisation, nombre in sorted(non_rattaches.items()):
        print(f"  {nombre:>3}  {localisation!r}")


if __name__ == "__main__":
    main()
