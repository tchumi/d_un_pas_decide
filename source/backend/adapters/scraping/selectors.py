"""Centralized CSS/ARIA selectors for LinkedIn people-search scraping.

LinkedIn's DOM changes frequently. Every selector used to drive Playwright
lives here so a broken selector can be fixed in one place instead of being
hunted down across the codebase.
"""


class LinkedInSearchSelectors:
    """Selectors for the LinkedIn "people" search results page."""

    # One search result card in the results list.
    RESULT_CARD = "li.reusable-search__result-container"

    # Profile display name, relative to a RESULT_CARD.
    # Fragile: LinkedIn reuses aria-hidden spans for other purposes too,
    # this targets the first one found in the card.
    NAME = "span[aria-hidden='true']"

    # Headline / title shown under the name, relative to a RESULT_CARD.
    TITLE = ".entity-result__primary-subtitle"

    # Location shown under the title, relative to a RESULT_CARD.
    LOCATION = ".entity-result__secondary-subtitle"

    # Link to the profile page, relative to a RESULT_CARD.
    PROFILE_LINK = "a.app-aware-link"

    # Pagination "next page" button.
    # Fragile: aria-label text depends on the LinkedIn account's display
    # language (e.g. "Suivant" in French, "Next" in English).
    NEXT_BUTTON = "button[aria-label='Suivant']"


class LinkedInAuthSelectors:
    """Selectors/markers used to detect whether a manual login is needed."""

    # URL fragments seen when the account is not authenticated.
    LOGIN_URL_MARKERS = ("login", "authwall")

    # URL fragment seen once logged in and on the main feed.
    FEED_URL_MARKER = "feed"
