"""POC-002 entry script: search LinkedIn profiles, then visit each profile
page to extract its public email, and export everything to CSV.

Read-only, manual login, no invitation/message sent (out of scope for this
ticket - see document/Backlog.md POC-002).

Usage:
    python -m source.backend.adapters.scraping.run_poc002

Run standalone (never via `streamlit run`, see CLAUDE.md rule 6).
"""

from pathlib import Path

from source.backend.adapters.scraping.browser_session import (
    ensure_logged_in,
    open_browser_session,
)
from source.backend.adapters.scraping.profile_email import enrich_profiles_with_email
from source.backend.adapters.scraping.profile_search import search_and_extract
from source.backend.adapters.storage.csv_export import export_profiles_to_csv

# Boolean query from document/spec/spec_onboarding_prospection_linkedin.md
SEARCH_QUERY = (
    '("coach business" OR "coach professionnel" OR "coach entreprise") '
    'AND (France) NOT ("life coach" OR "sportif")'
)

# Raised to 25 (user decision, 07/07/2026) after the first 5-profile run
# confirmed the contact-info flow works with no LinkedIn account restriction.
MAX_PROFILES = 25

PROFILE_DIR = Path("./browser_profile")
OUTPUT_CSV = Path("./profils_extraits_email.csv")


def main() -> None:
    with open_browser_session(PROFILE_DIR) as (context, page):
        ensure_logged_in(page, context)
        profiles = search_and_extract(page, SEARCH_QUERY, MAX_PROFILES)
        profiles = enrich_profiles_with_email(page, profiles)

    export_profiles_to_csv(profiles, OUTPUT_CSV)
    print(f"{len(profiles)} profils extraits (avec email) -> {OUTPUT_CSV.resolve()}")


if __name__ == "__main__":
    main()
