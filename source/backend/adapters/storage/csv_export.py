"""CSV export for extracted LinkedIn profiles.

No Streamlit import here (see CLAUDE.md / ARCHITECTURE.md): this module must
stay usable standalone, independently of the UI.
"""

import csv
from pathlib import Path

from source.backend.core.departement import deriver_departement

# Email added in POC-002 (visited from the individual profile page); blank
# when the profile doesn't display it publicly.
# email_web/site_web added in POC-004 (deterministic web enrichment pipeline,
# no LLM): alternative contact found via Brave Search + regex extraction,
# blank when nothing conclusive was found.
# categorie/score/justification added in POC-003 (deterministic rule engine):
# blank when the profile hasn't been scored yet. commentaire_client is the
# column the client fills in to tell us whether the criterion/score is
# relevant - blank on a fresh export, re-imported into the store afterwards.
# date_collecte/ne_plus_traiter added in POC-006: they come from the profile
# store (the CSV is now a view of it) and carry the two RGPD guardrails,
# limited retention and right to object. Both are visible to the client
# (user decision, 26/08/2026) so an objection can be expressed in the CSV.
# date_visite_email/date_enrichissement_web/statut_coordonnees added in
# POC-009: the two dates tell "attempted, nothing found" apart from "not
# attempted yet", and statut_coordonnees carries the human ruling on the web
# contact details. The status is exported because that is how the review comes
# back into the store, exactly like commentaire_client.
# departement added in POC-015 (client suggestion of 11/09/2026, to sort the
# workbook): unlike every other column it is not read from the store, it is
# derived from localisation at export time - blank when the location cannot be
# tied to exactly one departement. No re-import path reads it back.
DERIVED_CSV_FIELDS = ["departement"]

PROFILE_CSV_FIELDS = [
    "nom",
    "url",
    "localisation",
    "departement",
    "titre",
    "email",
    "email_web",
    "site_web",
    "categorie",
    "score",
    "justification",
    "commentaire_client",
    "date_collecte",
    "ne_plus_traiter",
    "date_visite_email",
    "date_enrichissement_web",
    "statut_coordonnees",
]

# Single export file shared by every run script (POC-009, user decision of
# 28/08/2026). Before it, run_poc001 wrote profils_extraits.csv and run_poc003
# profils_extraits_scores.csv - two names for two views of the same store,
# carrying identical content once the scoring had run, and the first no longer
# holding the raw extraction its name suggested. The older files are left on
# disk untouched (CLAUDE.md rule 3), they simply stop being written.
EXPORT_CSV = Path("./profils_magasin.csv")


def export_profiles_to_csv(profiles: list[dict[str, str]], output_path: Path) -> None:
    """Write extracted profiles to a CSV file with the expected field set.

    departement is always recomputed from localisation, whatever the incoming
    dict carries: a value edited in a returned workbook must not survive a
    re-export as if it were derived.
    """
    lignes = [
        {**profil, "departement": deriver_departement(profil.get("localisation"))}
        for profil in profiles
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PROFILE_CSV_FIELDS, restval="")
        writer.writeheader()
        writer.writerows(lignes)
