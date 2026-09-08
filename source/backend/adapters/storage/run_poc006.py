"""POC-006 entry script: import a CSV into the profile store.

Two uses, one code path:

* seeding - load an existing CSV (e.g. profils_extraits.csv from POC-001) into
  a fresh store, so past collections are not lost;
* re-importing the client's feedback - reload a CSV whose commentaire_client
  column has been filled in, so a later scoring run keeps it.

Reconciliation key: the profile URL, normalised exactly like the search
deduplication key. Conflict rule (user decision, 26/08/2026): a filled client
comment wins over the stored one and the substitution is listed below, never
applied silently; an empty cell never erases stored feedback.

POC-013: the input may also be the .xlsx the client annotated. It is converted
to a sibling CSV first, then this script runs its usual path on that CSV - the
store keeps reading exactly what it has always read.

No browser, no network call.

Usage:
    python -m source.backend.adapters.storage.run_poc006 [chemin_csv_ou_xlsx] [date_collecte]

date_collecte (ISO, ex. 2026-07-04) is only used to seed rows that carry no
date of their own - the CSVs written before POC-006 have no such column, and
dating them "today" would understate their age for the RGPD retention rule.

Run standalone (never via `streamlit run`, see CLAUDE.md rule 6).
"""

import csv
import sys
from pathlib import Path

from source.backend.adapters.storage.profile_store import (
    DEFAULT_DB_PATH,
    RapportReimport,
    enregistrer_profils,
    importer_commentaires_csv,
    ouvrir_magasin,
)
from source.backend.adapters.storage.xlsx_export import EnteteXlsxInvalide, xlsx_vers_csv

# The file the client annotates: the scored export of POC-003.
DEFAULT_INPUT_CSV = Path("./profils_extraits_scores.csv")

# Suffix of the workbook the client sends back since POC-013.
SUFFIXE_XLSX = ".xlsx"


def _afficher_rapport(rapport: RapportReimport) -> None:
    """Print the re-import outcome, substitutions spelled out one by one."""
    print(f"{len(rapport.commentaires_ajoutes)} commentaires client ajoutes")
    print(f"{rapport.commentaires_inchanges} commentaires client inchanges")

    if rapport.commentaires_remplaces:
        print(
            f"{len(rapport.commentaires_remplaces)} commentaires client REMPLACES "
            f"(le retour client prime, substitution detaillee ci-dessous) :"
        )
        for url, ancien, nouveau in rapport.commentaires_remplaces:
            print(f"  - {url}\n      ancien : {ancien}\n      nouveau : {nouveau}")

    if rapport.oppositions_ajoutees:
        print(
            f"{len(rapport.oppositions_ajoutees)} profils marques 'ne plus traiter' "
            f"(RGPD, exclus des collectes futures) :"
        )
        for url in rapport.oppositions_ajoutees:
            print(f"  - {url}")

    # POC-013: these two blocks were missing. RapportReimport has carried both
    # fields since POC-009 and _importer_statut_coordonnees fills them, but no
    # script ever printed them - so a ruling entered the store with no trace,
    # and an unrecognised one ("Valide" accented, "OK") was dropped in silence,
    # which is exactly what the POC-009 rule forbids.
    if rapport.statuts_tranches:
        print(
            f"{len(rapport.statuts_tranches)} statuts de coordonnees tranches "
            f"par le client :"
        )
        for url, statut in rapport.statuts_tranches:
            print(f"  - {url} -> {statut}")

    if rapport.statuts_refuses:
        print(
            f"{len(rapport.statuts_refuses)} statuts de coordonnees REFUSES "
            f"(valeur non reconnue, rien ecrit en base — a arbitrer a la main) :"
        )
        for url, statut in rapport.statuts_refuses:
            print(f"  - {url} -> {statut!r}")

    if rapport.urls_inconnues:
        print(
            f"{len(rapport.urls_inconnues)} URLs du CSV absentes du magasin, "
            f"ignorees (aucun profil cree par un re-import)"
        )
    if rapport.lignes_sans_url:
        print(f"{rapport.lignes_sans_url} lignes sans URL exploitable, ignorees")


def _resoudre_source(chemin: Path) -> Path | None:
    """Return the CSV to re-import, converting a workbook first if need be.

    POC-013: the client sends the annotated file back as .xlsx. Rather than
    teaching the store to read a workbook, the workbook is converted here into
    a sibling CSV, and everything downstream runs the exact path it has run
    since POC-006 - profile_store.py, which carries the conflict rules of
    POC-006 and POC-009, is not touched (user arbitration, 08/09/2026).

    The intermediate CSV is deliberately left on disk: it is the inspectable
    trace of what Excel gave back, and on a file nobody annotated it is
    identical to the exported CSV. Returns None when the workbook is refused.
    """
    if chemin.suffix.lower() != SUFFIXE_XLSX:
        return chemin

    # with_name rather than with_suffix: a name like "retour.v2.xlsx" would
    # lose its ".v2" to with_suffix.
    trace = chemin.with_name(f"{chemin.stem}.reimport.csv")
    try:
        lignes = xlsx_vers_csv(chemin, trace)
    except EnteteXlsxInvalide as erreur:
        print(f"Re-import refuse.\n{erreur}")
        return None

    print(f"{lignes} lignes converties depuis le classeur {chemin}")
    print(f"Trace de la conversion ecrite dans {trace} (relue ci-dessous)")
    return trace


def main(csv_path: Path = DEFAULT_INPUT_CSV, date_collecte: str | None = None) -> None:
    if not csv_path.exists():
        print(f"Fichier introuvable : {csv_path.resolve()}")
        return

    csv_path = _resoudre_source(csv_path)
    if csv_path is None:
        return

    with open(csv_path, newline="", encoding="utf-8") as f:
        lignes = list(csv.DictReader(f))
    print(f"{len(lignes)} lignes lues depuis {csv_path}")

    conn = ouvrir_magasin(DEFAULT_DB_PATH)
    try:
        # First pass: create the profiles the store doesn't know yet and
        # complete the known ones. Second pass: apply the client's feedback
        # with the conflict rule above.
        enregistrement = enregistrer_profils(conn, lignes, date_collecte=date_collecte)
        print(
            f"{len(enregistrement.nouveaux)} profils ajoutes au magasin, "
            f"{len(enregistrement.deja_connus)} deja connus completes"
        )
        if enregistrement.sans_url:
            print(f"{enregistrement.sans_url} lignes sans URL exploitable, ignorees")

        _afficher_rapport(importer_commentaires_csv(conn, csv_path))
        print(f"Magasin a jour : {DEFAULT_DB_PATH.resolve()}")
    finally:
        conn.close()


if __name__ == "__main__":
    main(
        Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT_CSV,
        sys.argv[2] if len(sys.argv) > 2 else None,
    )
