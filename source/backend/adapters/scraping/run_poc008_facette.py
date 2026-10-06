"""POC-008 verification run: read the native location facet off a real search.

Diagnostic only - writes neither the store nor the collection journal. It
answers three questions that must be measured, not assumed:

1. Which URL parameter carries the "Locations" facet, and with which id for
   a given region? The filter is applied by hand in the browser window; the
   script only watches the address bar.
2. Does a URL built by build_search_url with that id really filter? The
   locations of the profiles brought back are printed for a human check.
3. What does the numbered pagination bar look like, and how many results
   does LinkedIn announce? Dumped to tests/temp/ (gitignored).

Ceiling (validated before launch): one region, 2 pages, 10 profiles.

Usage:
    python -m source.backend.adapters.scraping.run_poc008_facette
"""

import json
import sys
import time
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Page

from source.backend.adapters.scraping.browser_session import (
    ensure_logged_in,
    open_browser_session,
)
from source.backend.adapters.scraping.profile_search import (
    GEO_FACET_PARAM,
    build_search_url,
    message_arret,
    pause_humaine,
    search_and_extract,
)
from source.backend.adapters.scraping.selectors import LinkedInSearchSelectors

# Current vocabulary without the textual "AND (France)": the facet replaces it.
MOTS_CLES = (
    '("coach business" OR "coach professionnel" OR "coach entreprise") '
    'NOT ("life coach" OR "sportif")'
)

MAX_PROFILES = 10
MAX_PAGES = 2

PROFILE_DIR = Path("./browser_profile")
DUMP_DIR = Path("./tests/temp")

ATTENTE_FILTRE_S = 480
INTERVALLE_S = 2


def parametres_geo(url: str) -> dict[str, list[str]]:
    """Query parameters whose name mentions "geo", decoded."""
    parametres = parse_qs(urlparse(url).query)
    return {nom: valeurs for nom, valeurs in parametres.items() if "geo" in nom.lower()}


def attendre_filtre_lieu(page: Page) -> str | None:
    """Wait until the address bar carries a geo parameter, printing every URL change."""
    derniere = page.url
    echeance = time.monotonic() + ATTENTE_FILTRE_S
    while time.monotonic() < echeance:
        page.wait_for_timeout(INTERVALLE_S * 1000)
        if page.url != derniere:
            derniere = page.url
            print(f"URL -> {derniere}", flush=True)
        if parametres_geo(derniere):
            return derniere
    return None


def relever_pagination(page: Page) -> None:
    """Dump the markup around the "next" button and any announced result count."""
    DUMP_DIR.mkdir(parents=True, exist_ok=True)
    suivant = page.locator(LinkedInSearchSelectors.NEXT_BUTTON)
    if suivant.count() == 0:
        print("Pagination : bouton 'suivant' absent, rien a relever.")
    else:
        html = suivant.first.evaluate(
            "el => { let n = el; for (let i = 0; i < 4 && n.parentElement; i++) "
            "n = n.parentElement; return n.outerHTML; }"
        )
        sortie = DUMP_DIR / "poc008_pagination.html"
        sortie.write_text(html, encoding="utf-8")
        print(f"Pagination : {len(html)} caracteres ecrits dans {sortie}")

    # Diagnostic text probe, not a selector the pipeline relies on.
    annonces = page.get_by_text("résultat", exact=False)
    for i in range(min(annonces.count(), 5)):
        try:
            print(f"Annonce de resultats : {annonces.nth(i).inner_text(timeout=2000)!r}")
        except Exception:
            continue


def main() -> None:
    sys.stdout.reconfigure(errors="replace")

    with open_browser_session(PROFILE_DIR) as (context, page):
        ensure_logged_in(page, context)

        page.goto(build_search_url(MOTS_CLES), timeout=60000)
        print(
            "\n>>> Dans la fenetre Chrome : filtre 'Lieux' -> choisir UNE region "
            f"-> 'Afficher les resultats'. Attente maximale : {ATTENTE_FILTRE_S} s.\n",
            flush=True,
        )
        url_filtree = attendre_filtre_lieu(page)
        if url_filtree is None:
            print("Aucun parametre de lieu apparu dans l'URL : run arrete, rien n'est lu.")
            return

        trouves = parametres_geo(url_filtree)
        print(f"Parametres de lieu lus dans l'URL : {trouves}")
        if GEO_FACET_PARAM not in trouves:
            print(
                f"ATTENTION : le parametre attendu '{GEO_FACET_PARAM}' est absent. "
                f"build_search_url est a corriger avant tout run : arret."
            )
            return

        geo_urns = [str(i) for i in json.loads(trouves[GEO_FACET_PARAM][0])]
        url_construite = build_search_url(MOTS_CLES, geo_urns)
        print(f"Identifiant(s) de lieu : {geo_urns}")
        print(f"URL construite par build_search_url : {url_construite}")

        pause_humaine(4, 8)
        resultat = search_and_extract(
            page, MOTS_CLES, MAX_PROFILES, frozenset(), MAX_PAGES, geo_urns
        )
        print(f"URL apres navigation : {page.url}")
        print(message_arret(resultat, MAX_PROFILES))

        localisations = Counter(p.get("localisation", "") or "(vide)" for p in resultat.profils)
        print("Localisations des profils lus (controle de la facette) :")
        for localisation, nombre in localisations.most_common():
            print(f"  {nombre} x {localisation}")

        relever_pagination(page)


if __name__ == "__main__":
    main()
