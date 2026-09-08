"""POC-013 entry script: turn the CSV export into the client's xlsx deliverable.

Converts profils_magasin.csv into profils_magasin.xlsx, value for value. It
does not read the store, does not score and does not filter: the deliverable
is the CSV export in full - the 81 profiles minus the ne_plus_traiter ones -
because the client said at the call of 04/09/2026 that he wants to sort and
filter himself, notably by location. Whether to deliver only the profiles
above the threshold is therefore his arbitration, not ours (user decision,
08/09/2026).

Kept as a separate script on purpose: the four existing run_pocNNN.py are left
untouched, which is the smallest possible blast radius for a ticket that has a
firm deadline.

Run run_poc003 first if the CSV export is not up to date with the store.

No browser, no network call.

Usage:
    python -m source.backend.adapters.storage.run_poc013 [chemin_csv] [chemin_xlsx]

Run standalone (never via `streamlit run`, see CLAUDE.md rule 6).
"""

import sys
from pathlib import Path

from source.backend.adapters.storage.csv_export import EXPORT_CSV
from source.backend.adapters.storage.xlsx_export import (
    EXPORT_XLSX,
    EnteteXlsxInvalide,
    convertir_csv_en_xlsx,
)


def main(csv_path: Path = EXPORT_CSV, xlsx_path: Path = EXPORT_XLSX) -> None:
    if not csv_path.exists():
        print(f"Export CSV introuvable : {csv_path.resolve()}")
        print("Lancer d'abord run_poc003 pour produire l'export depuis le magasin.")
        return

    try:
        lignes = convertir_csv_en_xlsx(csv_path, xlsx_path)
    except EnteteXlsxInvalide as erreur:
        print(f"Conversion refusee.\n{erreur}")
        return

    print(f"{lignes} profils convertis depuis {csv_path}")
    print(f"Livrable client ecrit dans {xlsx_path.resolve()}")
    print(
        "En-tete fige et filtre automatique poses ; aucune valeur reformatee. "
        "Le retour annote se reinjecte avec :\n"
        f"  python -m source.backend.adapters.storage.run_poc006 {xlsx_path}"
    )


if __name__ == "__main__":
    main(
        Path(sys.argv[1]) if len(sys.argv) > 1 else EXPORT_CSV,
        Path(sys.argv[2]) if len(sys.argv) > 2 else EXPORT_XLSX,
    )
