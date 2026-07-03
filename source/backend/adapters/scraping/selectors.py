"""Centralized CSS/ARIA selectors for LinkedIn people-search scraping.

LinkedIn's DOM changes frequently. Every selector used to drive Playwright
lives here so a broken selector can be fixed in one place instead of being
hunted down across the codebase.
"""


class LinkedInSearchSelectors:
    """Selectors for the LinkedIn "people" search results page.

    LinkedIn's CSS class names are hashed/atomic (e.g. "_3ff84621") and
    regenerated on every deploy - unusable as stable selectors. These
    selectors rely instead on structural ARIA roles and data-testid
    attributes, verified against a live DOM dump on 03/07/2026.
    """

    # One search result card. Scoped under the page's single ARIA list to
    # avoid matching unrelated "listitem" roles elsewhere (right rail,
    # filter pills, etc.).
    RESULT_CARD = '[role="list"] [role="listitem"]'

    # Card-wrapping anchor, relative to a RESULT_CARD - first match gives
    # the profile URL (it wraps the whole card content).
    PROFILE_LINK = 'a[href*="/in/"]'

    # Name link, relative to a RESULT_CARD: the first anchor nested inside
    # a <p> pointing to a profile - distinguishes it from the outer
    # card-wrapping anchor (not inside a <p>) and from "mutual connections"
    # anchors appearing later in the card (pointing to other profiles).
    NAME = 'p a[href*="/in/"]'

    # Headline and location, relative to a RESULT_CARD: each is the sole
    # <p> inside the 1st / 2nd <div> sibling following the name's <p>,
    # within their shared info block. XPath needed for sibling traversal.
    HEADLINE_XPATH = ".//p[.//a[contains(@href,'/in/')]][1]/following-sibling::div[1]//p"
    LOCATION_XPATH = ".//p[.//a[contains(@href,'/in/')]][1]/following-sibling::div[2]//p"

    # Pagination "next page" button. Uses a stable data-testid instead of
    # the old aria-label text, which depended on the account's display
    # language (e.g. "Suivant" in French, "Next" in English).
    NEXT_BUTTON = '[data-testid="pagination-controls-next-button-visible"]'


class LinkedInAuthSelectors:
    """Selectors/markers used to detect whether a manual login is needed."""

    # URL fragment seen once logged in and on the main feed. Its absence is
    # treated as "not logged in" - a logged-out session doesn't reliably
    # expose a "login"/"authwall" marker on the plain homepage URL.
    FEED_URL_MARKER = "feed"
