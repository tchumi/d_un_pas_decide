"""POC-001 entry script: search LinkedIn profiles and export them to CSV.

Read-only, manual login, no email extraction, no scoring (all out of scope
for this ticket - see document/Backlog.md POC-001).

POC-006: the run no longer starts from a blank slate. Profiles already in the
store are excluded from the search, and the CSV is rewritten from the whole
store - so a new run adds to the batch instead of replacing it.

POC-008: the queries are no longer hard-coded here. They are read from
config/requetes_recherche.json and run in sequence, each one excluding what
the previous ones brought back; the query that brought each new profile is
written to the collection journal.

Usage:
    python -m source.backend.adapters.scraping.run_poc001

Run standalone (never via `streamlit run`, see CLAUDE.md rule 6).
"""

from datetime import date
from pathlib import Path

from source.backend.adapters.scraping.browser_session import (
    ensure_logged_in,
    open_browser_session,
)
from source.backend.adapters.scraping.profile_search import (
    MAX_PAGES,
    ResultatRecherche,
    ResultatRequete,
    clean_profile_url,
    message_arret,
    parcourir_requetes,
    pause_humaine,
    search_and_extract,
)
from source.backend.adapters.storage.csv_export import EXPORT_CSV, export_profiles_to_csv
from source.backend.adapters.storage.journal_collecte import (
    JOURNAL_COLLECTE,
    journaliser_collecte,
)
from source.backend.adapters.storage.profile_store import (
    DEFAULT_DB_PATH,
    enregistrer_profils,
    lister_profils,
    ouvrir_magasin,
    urls_connues,
)
from source.backend.core.requetes_recherche import Requete, charger_requetes

PROFILE_DIR = Path("./browser_profile")


def lignes_journal(
    bilans: list[ResultatRequete], urls_ajoutees: list[str], jour: str
) -> list[dict[str, str]]:
    """One journal line per profile actually added to the store, with its query."""
    ajoutees = set(urls_ajoutees)
    lignes = []
    for bilan in bilans:
        for profil in bilan.resultat.profils:
            url = clean_profile_url(profil.get("url"))
            if url in ajoutees:
                lignes.append(
                    {
                        "date_collecte": jour,
                        "url": url,
                        "requete_id": bilan.requete.id,
                        "requete_libelle": bilan.requete.libelle,
                    }
                )
    return lignes


def afficher_bilan(bilans: list[ResultatRequete], requetes: tuple[Requete, ...]) -> None:
    """Say, per query, how many new profiles it brought back and why it stopped."""
    for bilan in bilans:
        print(f"[{bilan.requete.id}] {bilan.requete.libelle}")
        print(f"    {message_arret(bilan.resultat, bilan.profils_demandes)}")
        annoncees = bilan.resultat.pages_annoncees
        print(
            f"    Pagination annoncee : {annoncees} page(s)."
            if annoncees
            else "    Pagination annoncee : aucune barre (une seule page de resultats ?)."
        )
    for requete in requetes[len(bilans) :]:
        print(f"[{requete.id}] {requete.libelle}")
        print("    Non lancee : plafond de profils du run deja atteint.")


def main() -> None:
    # Loaded before opening anything: a malformed file must fail here, not
    # mid-run with a browser session open.
    configuration = charger_requetes()
    requetes = configuration.actives()
    max_profiles = configuration.max_profils_par_run
    print(f"{len(requetes)} requete(s) active(s), plafond du run : {max_profiles} profils")

    conn = ouvrir_magasin(DEFAULT_DB_PATH)
    try:
        deja_vus = urls_connues(conn)
        print(f"{len(deja_vus)} profils deja connus du magasin — ils seront ignores")

        with open_browser_session(PROFILE_DIR) as (context, page):
            ensure_logged_in(page, context)
            premiere = True

            def rechercher(
                requete: Requete, quota: int, exclues: frozenset[str]
            ) -> ResultatRecherche:
                nonlocal premiere
                if not premiere:
                    # Longer pause between two searches than between two pages.
                    pause_humaine(8, 15)
                premiere = False
                return search_and_extract(
                    page,
                    requete.mots_cles,
                    quota,
                    exclues,
                    requete.max_pages or MAX_PAGES,
                    requete.geo_urns,
                )

            bilans = parcourir_requetes(requetes, rechercher, max_profiles, deja_vus)

        afficher_bilan(bilans, requetes)
        profils = [p for bilan in bilans for p in bilan.resultat.profils]
        enregistrement = enregistrer_profils(conn, profils)
        print(f"{len(enregistrement.nouveaux)} profils ajoutes au magasin {DEFAULT_DB_PATH}")

        journalisees = journaliser_collecte(
            lignes_journal(bilans, enregistrement.nouveaux, date.today().isoformat())
        )
        print(f"{journalisees} ligne(s) ajoutee(s) au journal {JOURNAL_COLLECTE}")

        # The CSV is now a view of the whole store, not just of this run:
        # nothing collected earlier is lost by rewriting it.
        profils_magasin = lister_profils(conn)
        export_profiles_to_csv(profils_magasin, EXPORT_CSV)
        print(f"{len(profils_magasin)} profils exportes -> {EXPORT_CSV.resolve()}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
