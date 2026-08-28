"""POC-003 entry script: score and categorize already-extracted profiles.

Reads the profiles from the store, applies the deterministic rule engine of
source/backend/core/profile_scoring.py, writes the scoring columns back and
exports the whole store to CSV.

No new LinkedIn extraction, no browser, no network call, no LLM.

POC-006: the input is the store, no longer profils_extraits.csv. That is what
makes the client's feedback survive a re-run - scorer_profils already refused
to overwrite a commentaire_client, but reading the raw extraction CSV meant it
never saw one (see document/Backlog.md POC-006). Seed or re-import an
annotated CSV with run_poc006.

Usage:
    python -m source.backend.adapters.storage.run_poc003

Run standalone (never via `streamlit run`, see CLAUDE.md rule 6).
"""

import sqlite3

from source.backend.adapters.storage.csv_export import EXPORT_CSV, export_profiles_to_csv
from source.backend.adapters.storage.profile_store import (
    DEFAULT_DB_PATH,
    lister_profils,
    mettre_a_jour_scoring,
    ouvrir_magasin,
)
from source.backend.core.profile_scoring import (
    ReglesScoring,
    charger_regles,
    scorer_profils,
    selectionner_profils_interessants,
)

def main() -> None:
    regles = charger_regles()
    conn = ouvrir_magasin(DEFAULT_DB_PATH)
    try:
        _scorer_et_exporter(conn, regles)
    finally:
        conn.close()


def _scorer_et_exporter(conn: sqlite3.Connection, regles: ReglesScoring) -> None:
    """Score every stored profile, write the scores back, export the view."""
    profils = lister_profils(conn)
    print(f"{len(profils)} profils lus depuis le magasin {DEFAULT_DB_PATH}")
    if not profils:
        print(
            "Magasin vide : alimenter le magasin avec run_poc001 (extraction) "
            "ou run_poc006 (import d'un CSV existant) avant de scorer."
        )
        return

    scores = scorer_profils(profils, regles)
    # Sorted by descending score so the ranking can be reviewed with the
    # client; excluded profiles stay in the file (score 0, categorie "exclu")
    # rather than being silently dropped.
    scores.sort(key=lambda p: int(p["score"]), reverse=True)

    mettre_a_jour_scoring(conn, scores)
    export_profiles_to_csv(scores, EXPORT_CSV)

    exclus = [p for p in scores if p["categorie"] == regles.categorie_exclusion]
    interessants = selectionner_profils_interessants(scores, regles=regles)
    print(f"{len(scores) - len(exclus)} profils conserves, {len(exclus)} exclus")
    print(
        f"{len(interessants)} profils 'interessants' "
        f"(score >= {regles.seuil_profil_interessant}) — candidats a "
        f"l'enrichissement web conditionnel de POC-004"
    )
    print(f"Export ecrit dans {EXPORT_CSV}")


if __name__ == "__main__":
    main()
