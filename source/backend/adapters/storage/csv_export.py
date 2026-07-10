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
PROFILE_CSV_FIELDS = ["nom", "url", "localisation", "titre", "email", "email_web", "site_web"]


def export_profiles_to_csv(profiles: list[dict[str, str]], output_path: Path) -> None:
    """Write extracted profiles to a CSV file with the expected field set."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PROFILE_CSV_FIELDS, restval="")
        writer.writeheader()
        writer.writerows(profiles)
