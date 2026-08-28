"""POC-001 entry script: search LinkedIn profiles and export them to CSV.

Read-only, manual login, no email extraction, no scoring (all out of scope
for this ticket - see document/Backlog.md POC-001).

POC-006: the run no longer starts from a blank slate. Profiles already in the
store are excluded from the search, and the CSV is rewritten from the whole
store - so a new run adds to the batch instead of replacing it.

Usage:
    python -m source.backend.adapters.scraping.run_poc001

Run standalone (never via `streamlit run`, see CLAUDE.md rule 6).
"""

from pathlib import Path

from source.backend.adapters.scraping.browser_session import (
    ensure_logged_in,
    open_browser_session,
)
from source.backend.adapters.scraping.profile_search import (
    message_arret,
    search_and_extract,
)
from source.backend.adapters.storage.csv_export import EXPORT_CSV, export_profiles_to_csv
from source.backend.adapters.storage.profile_store import (
    DEFAULT_DB_PATH,
    enregistrer_profils,
    lister_profils,
    ouvrir_magasin,
    urls_connues,
)

# Boolean query from document/spec/spec_onboarding_prospection_linkedin.md
SEARCH_QUERY = (
    '("coach business" OR "coach professionnel" OR "coach entreprise") '
    'AND (France) NOT ("life coach" OR "sportif")'
)

# Raised to 25 (user decision, 03/07/2026) after a first 5-profile run
# confirmed clean extraction with no LinkedIn account restriction.
MAX_PROFILES = 25

PROFILE_DIR = Path("./browser_profile")


def main() -> None:
    conn = ouvrir_magasin(DEFAULT_DB_PATH)
    try:
        deja_vus = urls_connues(conn)
        print(f"{len(deja_vus)} profils deja connus du magasin — ils seront ignores")

        with open_browser_session(PROFILE_DIR) as (context, page):
            ensure_logged_in(page, context)
            resultat = search_and_extract(page, SEARCH_QUERY, MAX_PROFILES, deja_vus)

        print(message_arret(resultat, MAX_PROFILES))
        enregistrement = enregistrer_profils(conn, resultat.profils)
        print(f"{len(enregistrement.nouveaux)} profils ajoutes au magasin {DEFAULT_DB_PATH}")

        # The CSV is now a view of the whole store, not just of this run:
        # nothing collected earlier is lost by rewriting it.
        profils_magasin = lister_profils(conn)
        export_profiles_to_csv(profils_magasin, EXPORT_CSV)
        print(f"{len(profils_magasin)} profils exportes -> {EXPORT_CSV.resolve()}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
