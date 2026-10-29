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

POC-016 survey mode (--releve URL...): visits a few chosen profiles, reads
their Experience and About sections and prints the derived career signals next
to the client's verdict. Diagnostic only - the store is opened read-only,
nothing is written, no visit marker is stamped. Its purpose is to check the
section selectors on a live DOM and whether the signals separate profiles that
share the same title but not the same verdict.

Usage:
    python -m source.backend.adapters.scraping.run_poc002
    python -m source.backend.adapters.scraping.run_poc002 --releve URL [URL ...]

Run standalone (never via `streamlit run`, see CLAUDE.md rule 6).
"""

import sys
from pathlib import Path

from source.backend.adapters.scraping.browser_session import (
    ensure_logged_in,
    open_browser_session,
)
from source.backend.adapters.scraping.profile_email import (
    enrich_profiles_with_email,
    extract_rubriques_from_profile_page,
    scroll_profile_page,
)
from source.backend.adapters.scraping.profile_search import clean_profile_url, pause_humaine
from source.backend.adapters.scraping.selectors import LinkedInProfileSelectors
from source.backend.adapters.storage.csv_export import EXPORT_CSV, export_profiles_to_csv
from source.backend.adapters.storage.profile_store import (
    DEFAULT_DB_PATH,
    RapportCoordonnees,
    enregistrer_email_linkedin,
    lister_profils,
    ouvrir_magasin,
    profils_a_visiter,
)
from source.backend.adapters.storage.run_poc014_evaluation import lire_profils_lecture_seule
from source.backend.core.parcours import SignauxParcours, deriver_signaux
from source.backend.core.profile_scoring import (
    ReglesScoring,
    charger_regles,
    selectionner_profils_interessants,
)

# Back down to 5 for the first run on the store (POC-009): the backlog is the
# whole store, and one profile page visit is one extra LinkedIn request. Same
# prudence as POC-001/POC-002 took on their own first runs; raise it only once
# a run has been validated with no account restriction.
MAX_PROFILES = 5

PROFILE_DIR = Path("./browser_profile")

# Survey dumps (personal data): tests/temp/ is gitignored, same place as the
# POC-008 diagnostic dumps. Written only when a section is not found, so the
# selector can be corrected from the real markup.
DUMP_DIR = Path("./tests/temp")


def selectionner_reliquat(
    profils: list[dict[str, str]], regles: ReglesScoring
) -> list[dict[str, str]]:
    """Profiles worth a profile-page visit: interesting and never visited.

    POC-016: until 29/10/2026 every never-visited profile was visited, whatever
    its score - one of the five visited on 28/08/2026 was under the threshold.
    A page visit is the riskiest step of the pipeline for the LinkedIn account,
    so it now follows the same conditional selection as run_poc004 (client
    decision, 13/07/2026). Feeding it lister_profils() output means
    ne_plus_traiter profiles are already excluded.
    """
    return profils_a_visiter(selectionner_profils_interessants(profils, regles=regles))


def main() -> None:
    # LinkedIn names carry emoji (observed 28/08/2026: two real profiles in
    # the store). Printing one raw on a cp1252 Windows console raises
    # UnicodeEncodeError and kills the run before a single profile is
    # processed - the store data itself is UTF-8 and unaffected.
    sys.stdout.reconfigure(errors="replace")
    arguments = sys.argv[1:]
    if arguments[:1] == ["--releve"]:
        main_releve(arguments[1:])
        return

    regles = charger_regles()
    conn = ouvrir_magasin(DEFAULT_DB_PATH)
    try:
        reliquat = selectionner_reliquat(lister_profils(conn), regles)
        print(
            f"{len(reliquat)} profils interessants "
            f"(score >= {regles.seuil_profil_interessant}) jamais visites"
        )
        if not reliquat:
            print("Rien a traiter : tous les profils interessants ont deja ete visites.")
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


def profils_du_releve(
    urls: list[str], profils: list[dict[str, str]]
) -> tuple[list[dict[str, str]], list[str]]:
    """Stored profiles matching the survey URLs, and the URLs the store lacks.

    A survey profile must be in the store: the point is to confront what the
    page says with the client's verdict, which only the store holds.
    """
    par_url = {clean_profile_url(p.get("url")): p for p in profils}
    trouves: list[dict[str, str]] = []
    inconnues: list[str] = []
    for url in urls:
        profil = par_url.get(clean_profile_url(url))
        if profil is None:
            inconnues.append(url)
        else:
            trouves.append(profil)
    return trouves, inconnues


def _afficher_signaux(signaux: SignauxParcours) -> None:
    tronque = f" sur {signaux.total_annonce} annonces" if signaux.total_annonce else ""
    print(
        f"    postes lus : {signaux.nb_postes}{tronque}, en cours : {signaux.nb_postes_en_cours}"
        f" | coach en cours : {'oui' if signaux.coach_en_cours else 'non'}"
        f" ({signaux.anciennete_coach_mois} mois)"
        f" | autre poste en cours : {'oui' if signaux.autre_poste_en_cours else 'non'}"
        f" | ancien dirigeant : {'oui' if signaux.ancien_dirigeant else 'non'}"
        f" | Infos : {signaux.longueur_infos} car."
    )
    for poste in signaux.postes:
        etat = "en cours" if poste.en_cours else "termine "
        marques = ("coach " if poste.coach else "") + ("direction" if poste.direction else "")
        print(f"      [{etat}] {poste.duree_mois:>3} mois  {poste.libelle[:60]}  {marques}")


def _diagnostiquer_page(page, rang: int) -> None:
    """Print the section headings found and dump the page for selector repair."""
    try:
        titres = page.locator(LinkedInProfileSelectors.SECTION_HEADINGS).all_inner_texts()
        print(f"    titres de section sur la page : {[t.strip() for t in titres]}")
        DUMP_DIR.mkdir(parents=True, exist_ok=True)
        sortie = DUMP_DIR / f"poc016_releve_{rang}.html"
        sortie.write_text(page.content(), encoding="utf-8")
        print(f"    page ecrite dans {sortie} (gitignore, donnees personnelles)")
    except Exception as erreur:
        print(f"    diagnostic impossible ({type(erreur).__name__})")


def main_releve(urls: list[str]) -> None:
    """Survey mode: read and print career signals, write nothing (POC-016)."""
    if len(urls) > MAX_PROFILES:
        print(f"Releve refuse : {len(urls)} URL, plafond MAX_PROFILES={MAX_PROFILES}.")
        return
    lot, inconnues = profils_du_releve(urls, lire_profils_lecture_seule(DEFAULT_DB_PATH))
    if inconnues:
        print(f"Releve refuse : URL absente(s) du magasin : {inconnues}")
        return

    print(f"Releve POC-016 : {len(lot)} profils, rien n'est ecrit dans le magasin")
    with open_browser_session(PROFILE_DIR) as (context, page):
        ensure_logged_in(page, context)
        for rang, profil in enumerate(lot, start=1):
            print(f"\n[{rang}] {profil['nom']} — score {profil['score']}")
            print(f"    titre   : {profil['titre'][:90]}")
            print(f"    verdict : {profil['commentaire_client'][:90]}")
            try:
                page.goto(profil["url"], timeout=60000)
            except Exception as erreur:
                print(f"    page non chargee ({type(erreur).__name__})")
                continue
            pause_humaine(2, 4)
            scroll_profile_page(page)
            rubriques = extract_rubriques_from_profile_page(page)
            print(
                f"    sections trouvees : Experience {'oui' if rubriques['experience'] else 'NON'}"
                f", Infos {'oui' if rubriques['infos'] else 'NON'}"
            )
            if not rubriques["experience"] or not rubriques["infos"]:
                _diagnostiquer_page(page, rang)
            _afficher_signaux(deriver_signaux(rubriques["experience"], rubriques["infos"]))
            pause_humaine(2, 5)


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
