"""LinkedIn people-search: URL building, result-page extraction, pagination.

No Streamlit import here (see CLAUDE.md / ARCHITECTURE.md): this module must
stay usable standalone, independently of the UI.
"""

import random
import time
from urllib.parse import quote

from playwright.sync_api import Locator, Page

from source.backend.adapters.scraping.selectors import LinkedInSearchSelectors

LINKEDIN_PEOPLE_SEARCH_URL = "https://www.linkedin.com/search/results/people/"

PROFILE_FIELDS = ["nom", "url", "localisation", "titre"]


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


def extract_profile_from_card(card: Locator) -> dict[str, str] | None:
    """Extract one profile's fields from a single result card.

    Returns None if the card doesn't match the expected structure (LinkedIn
    DOM changed, or a non-profile card slipped into the results).
    """
    try:
        name = card.locator(LinkedInSearchSelectors.NAME).first.inner_text(timeout=3000)
        title = card.locator(LinkedInSearchSelectors.TITLE).first.inner_text(timeout=3000)
        location = card.locator(LinkedInSearchSelectors.LOCATION).first.inner_text(timeout=3000)
        raw_url = card.locator(LinkedInSearchSelectors.PROFILE_LINK).first.get_attribute("href")
    except Exception:
        return None

    return {
        "nom": name.strip(),
        "titre": title.strip(),
        "localisation": location.strip(),
        "url": clean_profile_url(raw_url),
    }


def extract_profiles_from_page(
    page: Page, max_profiles: int, existing: list[dict[str, str]]
) -> list[dict[str, str]]:
    """Extract profiles from the currently loaded results page.

    Appends to existing until max_profiles is reached, then stops.
    """
    results = list(existing)
    cards = page.locator(LinkedInSearchSelectors.RESULT_CARD)

    for i in range(cards.count()):
        if len(results) >= max_profiles:
            break
        profile = extract_profile_from_card(cards.nth(i))
        if profile is not None:
            results.append(profile)

    return results


def go_to_next_page(page: Page) -> bool:
    """Click the "next page" button if present and enabled.

    Returns True if pagination happened, False if there is no next page.
    """
    next_button = page.locator(LinkedInSearchSelectors.NEXT_BUTTON)
    if next_button.count() == 0 or not next_button.is_enabled():
        return False
    next_button.click()
    return True


def search_and_extract(page: Page, boolean_query: str, max_profiles: int) -> list[dict[str, str]]:
    """Run the full search + paginated extraction flow for a boolean query."""
    page.goto(build_search_url(boolean_query), timeout=60000)
    pause_humaine(2, 4)

    results: list[dict[str, str]] = []
    while len(results) < max_profiles:
        results = extract_profiles_from_page(page, max_profiles, results)
        pause_humaine(1, 2.5)

        if len(results) >= max_profiles:
            break
        if not go_to_next_page(page):
            break
        pause_humaine(3, 6)

    return results
