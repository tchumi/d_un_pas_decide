"""CSV export for extracted LinkedIn profiles.

No Streamlit import here (see CLAUDE.md / ARCHITECTURE.md): this module must
stay usable standalone, independently of the UI.
"""

import csv
from pathlib import Path

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
PROFILE_CSV_FIELDS = [
    "nom",
    "url",
    "localisation",
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
]


def export_profiles_to_csv(profiles: list[dict[str, str]], output_path: Path) -> None:
    """Write extracted profiles to a CSV file with the expected field set."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PROFILE_CSV_FIELDS, restval="")
        writer.writeheader()
        writer.writerows(profiles)
