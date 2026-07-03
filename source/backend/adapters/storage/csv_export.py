"""CSV export for extracted LinkedIn profiles.

No Streamlit import here (see CLAUDE.md / ARCHITECTURE.md): this module must
stay usable standalone, independently of the UI.
"""

import csv
from pathlib import Path

# Email is intentionally excluded: out of scope for POC-001.
PROFILE_CSV_FIELDS = ["nom", "url", "localisation", "titre"]


def export_profiles_to_csv(profiles: list[dict[str, str]], output_path: Path) -> None:
    """Write extracted profiles to a CSV file with the expected field set."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PROFILE_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(profiles)
