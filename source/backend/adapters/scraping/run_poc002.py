"""POC-002 entry script: visit the stored profiles' pages to extract their
public email, and write the result back to the store.

Read-only, manual login, no invitation/message sent (out of scope for this
ticket - see document/Backlog.md POC-002).

POC-009: this script no longer searches LinkedIn. It used to call
search_and_extract before visiting the profile pages - and without passing
urls_connues, so it paginated from page 1 and brought back profiles the store
already held, spending LinkedIn quota and ToS exposure on a result already in
hand. The list of profiles to visit now comes from the store, and only the
ones never visited yet (date_visite_email empty) are processed.

The marker is stamped even when a profile shows no public email: that is what
makes the backlog shrink instead of the run redoing the same work every time.

Usage:
    python -m source.backend.adapters.scraping.run_poc002

Run standalone (never via `streamlit run`, see CLAUDE.md rule 6).
"""

import sys
from pathlib import Path

from source.backend.adapters.scraping.browser_session import (
    ensure_logged_in,
    open_browser_session,
)
from source.backend.adapters.scraping.profile_email import enrich_profiles_with_email
from source.backend.adapters.storage.csv_export import EXPORT_CSV, export_profiles_to_csv
from source.backend.adapters.storage.profile_store import (
    DEFAULT_DB_PATH,
    RapportCoordonnees,
    enregistrer_email_linkedin,
    lister_profils,
    ouvrir_magasin,
    profils_a_visiter,
)

# Back down to 5 for the first run on the store (POC-009): the backlog is the
# whole store, and one profile page visit is one extra LinkedIn request. Same
# prudence as POC-001/POC-002 took on their own first runs; raise it only once
# a run has been validated with no account restriction.
MAX_PROFILES = 5

PROFILE_DIR = Path("./browser_profile")


def main() -> None:
    # LinkedIn names carry emoji (observed 28/08/2026: two real profiles in
    # the store). Printing one raw on a cp1252 Windows console raises
    # UnicodeEncodeError and kills the run before a single profile is
    # processed - the store data itself is UTF-8 and unaffected.
    sys.stdout.reconfigure(errors="replace")
    conn = ouvrir_magasin(DEFAULT_DB_PATH)
    try:
        reliquat = profils_a_visiter(lister_profils(conn))
        print(f"{len(reliquat)} profils jamais visites pour leur email")
        if not reliquat:
            print("Rien a traiter : tous les profils du magasin ont deja ete visites.")
            return

        lot = reliquat[:MAX_PROFILES]
        print(f"Lot traite : {len(lot)} profils (plafond MAX_PROFILES={MAX_PROFILES})")
        for profil in lot:
            print(f"  - {profil['nom']} — {profil['url']}")

        with open_browser_session(PROFILE_DIR) as (context, page):
            ensure_logged_in(page, context)
            visites = enrich_profiles_with_email(page, lot)

        rapport = enregistrer_email_linkedin(conn, visites)
        _afficher_rapport(rapport)

        profils_magasin = lister_profils(conn)
        export_profiles_to_csv(profils_magasin, EXPORT_CSV)
        print(f"{len(profils_magasin)} profils exportes -> {EXPORT_CSV.resolve()}")
    finally:
        conn.close()


def _afficher_rapport(rapport: RapportCoordonnees) -> None:
    """Print what the run wrote, contradictions included.

    A stored value replaced by a fresh one is never silent (AGENTS.md).
    """
    print(
        f"{len(rapport.profils_traites)} profils marques comme visites, "
        f"{len(rapport.coordonnees_trouvees)} email(s) trouve(s)"
    )
    for url, colonne, ancienne, nouvelle in rapport.valeurs_remplacees:
        print(f"  ATTENTION valeur remplacee — {url} : {colonne} '{ancienne}' -> '{nouvelle}'")
    if rapport.urls_inconnues:
        print(f"  {len(rapport.urls_inconnues)} URL(s) absente(s) du magasin, ignoree(s)")


if __name__ == "__main__":
    main()
