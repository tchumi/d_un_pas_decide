"""POC-002 entry script, POC-016 reading run: visit the stored profiles' pages,
read their "Experience" and "About" sections, and write the text back to the store.

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

POC-016 reading run (default mode since 09/11/2026): every non-objecting
profile never read yet (date_lecture_parcours empty) is visited once, batch 1
first, with no score threshold (client decision D1, 03/11/2026). The
"Contact info" overlay is no longer opened (0 email out of 30 - decision D2,
05/11/2026): the email code stays in profile_email.py, uncalled. Each profile
is written as soon as it is read, so a run stopped on a block page keeps
every profile already read and leaves the rest unmarked.

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
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from source.backend.adapters.scraping.browser_session import (
    ensure_logged_in,
    open_browser_session,
)
from source.backend.adapters.scraping.profile_email import (
    extract_rubriques_from_profile_page,
    scroll_profile_page,
)
from source.backend.adapters.scraping.profile_search import clean_profile_url, pause_humaine
from source.backend.adapters.scraping.selectors import LinkedInProfileSelectors
from source.backend.adapters.storage.profile_store import (
    DEFAULT_DB_PATH,
    LECTURE_ECRITE,
    enregistrer_lecture_parcours,
    ouvrir_magasin,
    profils_a_lire,
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
# POC-016 reading run: steps of 5, 10, then 20, one commit per step, and at
# most 2 launches a day (decision D6, 05/11/2026 - a procedure rule, not coded).
MAX_PROFILES = 5

# Reading run guard: this many profiles in a row with both sections empty
# stops the run. One empty profile is plausible (no About section); several in
# a row more likely mean a LinkedIn markup change breaking the selectors, and
# going on would stamp the whole backlog "read, nothing found". The profiles
# already stamped are reported so they can be reset deliberately.
MAX_VIDES_CONSECUTIFS = 2

# Outcomes of one profile visit, as returned by a lire_profil callable.
VISITE_LUE = "lu"
VISITE_ECHEC = "echec"
VISITE_BLOQUEE = "bloque"

ARRET_BLOCAGE = "blocage"
ARRET_VIDES = "vides_consecutifs"

PROFILE_DIR = Path("./browser_profile")

# Survey dumps (personal data): tests/temp/ is gitignored, same place as the
# POC-008 diagnostic dumps. Written for every surveyed profile, so selectors and
# parsing can be corrected from the real markup. To delete after use.
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


@dataclass
class BilanLecture:
    """Outcome of a reading run - POC-016.

    lus lists (url, length of Experience, length of About) for every profile
    written; vides is the subset with both sections empty. echecs were not
    loaded and stay unmarked; refus were read but not written (the store's
    answer is given). arret says why the run stopped early, if it did.
    """

    lus: list[tuple[str, int, int]] = field(default_factory=list)
    vides: list[str] = field(default_factory=list)
    echecs: list[str] = field(default_factory=list)
    refus: list[tuple[str, str]] = field(default_factory=list)
    arret: str = ""
    detail_arret: str = ""
    non_traites: int = 0


def lire_lot(
    lot: list[dict[str, str]],
    lire_profil: Callable[[dict[str, str]], tuple[str, object]],
    ecrire: Callable[[str, str, str], str],
) -> BilanLecture:
    """Visit each profile, writing it as soon as it is read - POC-016.

    lire_profil returns (VISITE_LUE, {"experience", "infos"}),
    (VISITE_ECHEC, None) or (VISITE_BLOQUEE, page title). Kept free of
    Playwright so the stopping rules are unit-tested:
    - block page: immediate stop, nothing written for it nor after it
      (decision D5 - never work around a block page);
    - page not loaded: not marked - stamping it would claim "read, nothing
      found" - and the run goes on;
    - read: written at once, date stamped even when both sections are empty;
      MAX_VIDES_CONSECUTIFS empty ones in a row stop the run.
    """
    bilan = BilanLecture()
    vides_consecutifs = 0
    for rang, profil in enumerate(lot):
        url = profil["url"]
        etat, contenu = lire_profil(profil)
        if etat == VISITE_BLOQUEE:
            bilan.arret = ARRET_BLOCAGE
            bilan.detail_arret = str(contenu or "")
            bilan.non_traites = len(lot) - rang
            return bilan
        if etat != VISITE_LUE or not isinstance(contenu, dict):
            bilan.echecs.append(url)
            continue

        experience = str(contenu.get("experience", "") or "").strip()
        infos = str(contenu.get("infos", "") or "").strip()
        statut = ecrire(url, experience, infos)
        if statut != LECTURE_ECRITE:
            bilan.refus.append((url, statut))
            continue
        bilan.lus.append((url, len(experience), len(infos)))

        if experience or infos:
            vides_consecutifs = 0
            continue
        bilan.vides.append(url)
        vides_consecutifs += 1
        if vides_consecutifs >= MAX_VIDES_CONSECUTIFS:
            bilan.arret = ARRET_VIDES
            bilan.non_traites = len(lot) - rang - 1
            return bilan
    return bilan


def _lot_du_profil(profil: dict[str, str]) -> str:
    # Batch 2 is the 07/10/2026 collection; everything before is batch 1.
    return "lot 1" if profil.get("date_collecte", "") < "2026-10-07" else "lot 2"


def _lecteur_playwright(page) -> Callable[[dict[str, str]], tuple[str, object]]:
    """lire_profil over a live page: one visit, no "Contact info" overlay."""

    def lire_profil(profil: dict[str, str]) -> tuple[str, object]:
        print(f"  -> {profil['nom']}")
        try:
            page.goto(profil["url"], timeout=60000)
        except Exception as erreur:
            print(f"     page non chargee ({type(erreur).__name__})")
            return VISITE_ECHEC, None
        titre = page.title()
        if page_bloquee(page.url, titre):
            return VISITE_BLOQUEE, titre
        pause_humaine(2, 4)
        scroll_profile_page(page)
        rubriques = extract_rubriques_from_profile_page(page)
        pause_humaine(2, 5)
        return VISITE_LUE, rubriques

    return lire_profil


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

    conn = ouvrir_magasin(DEFAULT_DB_PATH)
    try:
        a_lire = profils_a_lire(conn)
        print(f"{len(a_lire)} profils non opposes dont le parcours n'a jamais ete lu")
        if not a_lire:
            print("Rien a traiter : tous les parcours ont deja ete lus.")
            return

        lot = a_lire[:MAX_PROFILES]
        print(f"Lot traite : {len(lot)} profils (plafond MAX_PROFILES={MAX_PROFILES})")
        for profil in lot:
            print(
                f"  - {profil['nom']} — {_lot_du_profil(profil)}, collecte "
                f"{profil['date_collecte']}, score {profil['score']} — {profil['url']}"
            )

        def ecrire(url: str, experience: str, infos: str) -> str:
            return enregistrer_lecture_parcours(conn, url, experience, infos)

        with open_browser_session(PROFILE_DIR) as (context, page):
            ensure_logged_in(page, context)
            bilan = lire_lot(lot, _lecteur_playwright(page), ecrire)

        _afficher_bilan(bilan)
    finally:
        conn.close()


def _afficher_bilan(bilan: BilanLecture) -> None:
    """Print what the reading run wrote - lengths only, never the text itself."""
    print(f"\n{len(bilan.lus)} profil(s) lu(s) et ecrit(s), dont {len(bilan.vides)} vide(s)")
    for url, longueur_experience, longueur_infos in bilan.lus:
        marque = "  VIDE" if url in bilan.vides else ""
        print(f"  {url} : Experience {longueur_experience} car., Infos {longueur_infos} car.{marque}")
    for url in bilan.echecs:
        print(f"  NON CHARGE (non marque) : {url}")
    for url, statut in bilan.refus:
        print(f"  NON ECRIT ({statut}) : {url}")
    if bilan.arret == ARRET_BLOCAGE:
        print(
            f"PAGE DE BLOCAGE ({bilan.detail_arret}) : run arrete, "
            f"{bilan.non_traites} profil(s) non traite(s). Ne pas relancer sans en decider."
        )
    elif bilan.arret == ARRET_VIDES:
        print(
            f"ARRET : {MAX_VIDES_CONSECUTIFS} profils consecutifs sans aucune rubrique lue "
            f"(selecteurs a verifier), {bilan.non_traites} profil(s) non traite(s). "
            "Les profils VIDE ci-dessus sont dates."
        )


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


def page_bloquee(url: str, titre: str) -> bool:
    """Whether the page reached is a block or security page, not a profile."""
    return LinkedInProfileSelectors.BLOCKED_TITLE_MARKER in titre or any(
        marqueur in url for marqueur in LinkedInProfileSelectors.BLOCKED_URL_MARKERS
    )


def _afficher_signaux(signaux: SignauxParcours) -> None:
    tronque = f" sur {signaux.total_annonce} annonces" if signaux.total_annonce else ""
    print(
        f"    postes lus : {signaux.nb_postes}{tronque}, en cours : {signaux.nb_postes_en_cours}"
        f" | coach en cours : {'oui' if signaux.coach_en_cours else 'non'}"
        f" ({signaux.anciennete_coach_mois} mois)"
        f" | autre poste en cours : {'oui' if signaux.autre_poste_en_cours else 'non'}"
        f" | ancien dirigeant : {'oui' if signaux.ancien_dirigeant else 'non'}"
        f" | fonction publique : {'oui' if signaux.fonction_publique else 'non'}"
        f" | Infos : {signaux.longueur_infos} car."
    )
    for poste in signaux.postes:
        etat = "en cours" if poste.en_cours else "termine "
        marques = (
            ("coach " if poste.coach else "")
            + ("direction " if poste.direction else "")
            + ("fonctionnaire" if poste.fonctionnaire else "")
        )
        print(f"      [{etat}] {poste.duree_mois:>3} mois  {poste.libelle[:60]}  {marques}")


def _diagnostiquer_page(page, rang: int) -> None:
    """Print the section headings found and dump the page for selector and parser repair."""
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
            if page_bloquee(page.url, page.title()):
                # Going on would only add requests to a session already refused.
                print(f"    PAGE DE BLOCAGE ({page.title()}) : releve arrete, ne pas relancer.")
                break
            pause_humaine(2, 4)
            scroll_profile_page(page)
            rubriques = extract_rubriques_from_profile_page(page)
            print(
                f"    sections trouvees : Experience {'oui' if rubriques['experience'] else 'NON'}"
                f", Infos {'oui' if rubriques['infos'] else 'NON'}"
            )
            # Always dumped: a section found can still be misread, and the first
            # survey had no page to check for the two profiles it read wrongly.
            _diagnostiquer_page(page, rang)
            _afficher_signaux(deriver_signaux(rubriques["experience"], rubriques["infos"]))
            pause_humaine(2, 5)


if __name__ == "__main__":
    main()
