"""POC-003 entry script: score and categorize already-extracted profiles.

Reads the CSV produced by an earlier ticket, applies the deterministic rule
engine of source/backend/core/profile_scoring.py, and exports the same rows
with the categorie/score/justification/commentaire_client columns filled in.

No new LinkedIn extraction, no browser, no network call, no LLM: the input is
the existing CSV (see document/Backlog.md POC-003).

Usage:
    python -m source.backend.adapters.storage.run_poc003

Run standalone (never via `streamlit run`, see CLAUDE.md rule 6).
"""

import csv
from pathlib import Path

from source.backend.adapters.storage.csv_export import export_profiles_to_csv
from source.backend.core.profile_scoring import (
    charger_regles,
    scorer_profils,
    selectionner_profils_interessants,
)

INPUT_CSV = Path("./profils_extraits.csv")
OUTPUT_CSV = Path("./profils_extraits_scores.csv")


def load_profiles(csv_path: Path) -> list[dict[str, str]]:
    """Read profiles from a CSV file produced by an earlier ticket."""
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    regles = charger_regles()
    profils = load_profiles(INPUT_CSV)
    print(f"{len(profils)} profils lus depuis {INPUT_CSV}")

    scores = scorer_profils(profils, regles)
    # Sorted by descending score so the ranking can be reviewed with the
    # client; excluded profiles stay in the file (score 0, categorie "exclu")
    # rather than being silently dropped.
    scores.sort(key=lambda p: int(p["score"]), reverse=True)

    export_profiles_to_csv(scores, OUTPUT_CSV)

    exclus = [p for p in scores if p["categorie"] == regles.categorie_exclusion]
    interessants = selectionner_profils_interessants(scores, regles=regles)
    print(f"{len(scores) - len(exclus)} profils conserves, {len(exclus)} exclus")
    print(
        f"{len(interessants)} profils 'interessants' "
        f"(score >= {regles.seuil_profil_interessant}) — candidats a "
        f"l'enrichissement web conditionnel de POC-004"
    )
    print(f"Export ecrit dans {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
