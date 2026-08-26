"""LinkedIn people-search: URL building, result-page extraction, pagination.

No Streamlit import here (see CLAUDE.md / ARCHITECTURE.md): this module must
stay usable standalone, independently of the UI.
"""

import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import quote

from playwright.sync_api import Locator, Page

from source.backend.adapters.scraping.selectors import LinkedInSearchSelectors

LINKEDIN_PEOPLE_SEARCH_URL = "https://www.linkedin.com/search/results/people/"

PROFILE_FIELDS = ["nom", "url", "localisation", "titre"]

# [Inference] A LinkedIn people search on a free account caps out around 10
# result pages; the ceiling is also what guarantees the collection loop always
# terminates, even if "next page" kept answering yes.
MAX_PAGES = 10

RAISON_QUOTA_ATTEINT = "quota_atteint"
RAISON_GISEMENT_EPUISE = "gisement_epuise"
RAISON_PLAFOND_PAGES = "plafond_pages"


@dataclass(frozen=True)
class ResultatRecherche:
    """A collected batch plus why the collection stopped.

    POC-006: a run that returns fewer profiles than asked must say so
    explicitly, never hand back a silently incomplete batch.
    """

    profils: list[dict[str, str]]
    raison_arret: str
    pages_visitees: int

    def __len__(self) -> int:
        return len(self.profils)


def build_search_url(boolean_query: str) -> str:
    """Build a LinkedIn people-search URL from a boolean query string.

    Pure function, no browser needed: the boolean query text (including any
    geographic terms, e.g. "AND (France)") is passed as-is in the
    "keywords" parameter.
    """
    return f"{LINKEDIN_PEOPLE_SEARCH_URL}?keywords={quote(boolean_query)}"


def clean_profile_url(raw_url: str | None) -> str:
    """Strip query params/fragment from a profile URL, return "" if absent."""
    if not raw_url:
        return ""
    return raw_url.split("?")[0].split("#")[0]


def pause_humaine(min_s: float = 1.5, max_s: float = 4.0) -> None:
    """Random pause to avoid a too-regular, bot-like request rhythm."""
    time.sleep(random.uniform(min_s, max_s))


def _extract_optional_text(locator: Locator) -> str:
    """Return the locator's inner text, or "" if absent/unreadable.

    Used for fields (headline, location) that some profiles legitimately
    omit - their absence should not reject the whole card.
    """
    if locator.count() == 0:
        return ""
    try:
        return locator.first.inner_text(timeout=3000).strip()
    except Exception:
        return ""


def extract_profile_from_card(card: Locator) -> dict[str, str] | None:
    """Extract one profile's fields from a single result card.

    Returns None if the card doesn't match the expected structure (LinkedIn
    DOM changed, or a non-profile card slipped into the results). Name and
    URL are required; headline/location degrade to "" if missing, since not
    every profile shows them.
    """
    try:
        name = card.locator(LinkedInSearchSelectors.NAME).first.inner_text(timeout=3000).strip()
        raw_url = card.locator(LinkedInSearchSelectors.PROFILE_LINK).first.get_attribute("href")
    except Exception:
        return None

    if not name or not raw_url:
        return None

    headline = _extract_optional_text(
        card.locator(f"xpath={LinkedInSearchSelectors.HEADLINE_XPATH}")
    )
    location = _extract_optional_text(
        card.locator(f"xpath={LinkedInSearchSelectors.LOCATION_XPATH}")
    )

    return {
        "nom": name,
        "titre": headline,
        "localisation": location,
        "url": clean_profile_url(raw_url),
    }


def extract_profiles_from_page(page: Page) -> list[dict[str, str]]:
    """Extract every readable profile card of the currently loaded results page.

    No quota applied here (POC-006): the caller decides which of those cards
    are new, so a page whose first cards are all already known must still be
    read in full.
    """
    results: list[dict[str, str]] = []
    cards = page.locator(LinkedInSearchSelectors.RESULT_CARD)

    for i in range(cards.count()):
        profile = extract_profile_from_card(cards.nth(i))
        if profile is not None:
            results.append(profile)

    return results


def filtrer_profils_inconnus(
    profils: list[dict[str, str]], urls_exclues: set[str] | frozenset[str]
) -> list[dict[str, str]]:
    """Keep the profiles whose URL is neither already known nor a duplicate.

    Pure function - the deduplication key is the URL normalised by
    clean_profile_url, the same key the store uses. A card without a usable
    URL is dropped: it could not be deduplicated on a later run.
    """
    retenus: list[dict[str, str]] = []
    vues = set(urls_exclues)

    for profil in profils:
        url = clean_profile_url(profil.get("url"))
        if not url or url in vues:
            continue
        vues.add(url)
        retenus.append(profil)

    return retenus


def collecter_profils_inconnus(
    extraire_page: Callable[[], list[dict[str, str]]],
    page_suivante: Callable[[], bool],
    max_profiles: int,
    urls_connues: set[str] | frozenset[str] = frozenset(),
    max_pages: int = MAX_PAGES,
) -> ResultatRecherche:
    """Paginate until max_profiles *unknown* profiles are collected.

    Pure orchestration: the two callables are injected, so the whole stop
    logic is testable without a browser. Two guards make an endless loop
    impossible - "no next page" and the max_pages ceiling.
    """
    if max_profiles <= 0:
        return ResultatRecherche([], RAISON_QUOTA_ATTEINT, 0)

    retenus: list[dict[str, str]] = []
    exclues = set(urls_connues)
    pages_visitees = 0

    while True:
        pages_visitees += 1
        for profil in filtrer_profils_inconnus(extraire_page(), exclues):
            if len(retenus) >= max_profiles:
                break
            retenus.append(profil)
            exclues.add(clean_profile_url(profil.get("url")))

        if len(retenus) >= max_profiles:
            return ResultatRecherche(retenus, RAISON_QUOTA_ATTEINT, pages_visitees)
        if pages_visitees >= max_pages:
            return ResultatRecherche(retenus, RAISON_PLAFOND_PAGES, pages_visitees)
        if not page_suivante():
            return ResultatRecherche(retenus, RAISON_GISEMENT_EPUISE, pages_visitees)


def message_arret(resultat: ResultatRecherche, max_profiles: int) -> str:
    """Human-readable explanation of why a collection stopped."""
    if resultat.raison_arret == RAISON_QUOTA_ATTEINT:
        return (
            f"{len(resultat.profils)} nouveaux profils collectes "
            f"({resultat.pages_visitees} page(s) parcourue(s))."
        )
    if resultat.raison_arret == RAISON_GISEMENT_EPUISE:
        return (
            f"Gisement epuise : {len(resultat.profils)} nouveaux profils sur "
            f"{max_profiles} demandes apres {resultat.pages_visitees} page(s). "
            f"Cette requete n'a plus de profil inconnu a fournir - varier la "
            f"requete pour renouveler le gisement."
        )
    return (
        f"Plafond de {resultat.pages_visitees} pages atteint : "
        f"{len(resultat.profils)} nouveaux profils sur {max_profiles} demandes. "
        f"Le reste du gisement est hors de portee de la recherche LinkedIn."
    )


def go_to_next_page(page: Page) -> bool:
    """Click the "next page" button if present and enabled.

    Returns True if pagination happened, False if there is no next page.
    """
    next_button = page.locator(LinkedInSearchSelectors.NEXT_BUTTON)
    if next_button.count() == 0 or not next_button.is_enabled():
        return False
    next_button.click()
    return True


def search_and_extract(
    page: Page,
    boolean_query: str,
    max_profiles: int,
    urls_connues: set[str] | frozenset[str] = frozenset(),
    max_pages: int = MAX_PAGES,
) -> ResultatRecherche:
    """Run the full search + paginated extraction flow for a boolean query.

    Browser shell around collecter_profils_inconnus: it only wires the real
    Playwright page to the pure collection loop. urls_connues defaults to an
    empty set, so a caller with no store behaves as before POC-006.
    """
    page.goto(build_search_url(boolean_query), timeout=60000)
    pause_humaine(2, 4)

    def extraire_page() -> list[dict[str, str]]:
        profils = extract_profiles_from_page(page)
        pause_humaine(1, 2.5)
        return profils

    def page_suivante() -> bool:
        if not go_to_next_page(page):
            return False
        pause_humaine(3, 6)
        return True

    return collecter_profils_inconnus(
        extraire_page, page_suivante, max_profiles, urls_connues, max_pages
    )
