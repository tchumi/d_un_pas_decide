"""LinkedIn individual profile page: contact-info visit and email extraction.

No Streamlit import here (see CLAUDE.md / ARCHITECTURE.md): this module must
stay usable standalone, independently of the UI.
"""

import re

from playwright.sync_api import Page

from source.backend.adapters.scraping.profile_search import pause_humaine
from source.backend.adapters.scraping.selectors import LinkedInProfileSelectors

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Centre of Playwright's default 1280x720 viewport.
SCROLL_POINTER_POSITION = (640, 360)


def clean_email(raw_email: str | None) -> str:
    """Return a stripped, validated email, or "" if missing/malformed."""
    if not raw_email:
        return ""
    candidate = raw_email.strip()
    if not EMAIL_PATTERN.match(candidate):
        return ""
    return candidate


def extract_email_from_profile_page(page: Page) -> str:
    """Open the contact-info overlay on an already-loaded profile page and
    return the email if publicly displayed, "" otherwise.

    Never raises: a missing contact-info link, a missing email inside the
    overlay, or a timeout are all treated as "no public email" rather than a
    failure, since visibility depends on the visited profile's own privacy
    settings, not on a scraping error.
    """
    contact_link = page.locator(f"xpath={LinkedInProfileSelectors.CONTACT_INFO_LINK_XPATH}")
    if contact_link.count() == 0:
        return ""

    try:
        contact_link.first.click(timeout=5000)
        page.wait_for_selector(LinkedInProfileSelectors.CONTACT_INFO_DIALOG, timeout=5000)
    except Exception:
        return ""

    email_link = page.locator(LinkedInProfileSelectors.EMAIL_LINK)
    if email_link.count() == 0:
        return ""

    try:
        href = email_link.first.get_attribute("href", timeout=3000)
    except Exception:
        return ""

    if not href or not href.startswith("mailto:"):
        return ""

    return clean_email(href.removeprefix("mailto:"))


def visit_profile_and_extract_email(page: Page, profile_url: str) -> str:
    """Navigate to a profile URL and extract its public email, if any."""
    try:
        page.goto(profile_url, timeout=60000)
    except Exception:
        return ""
    pause_humaine(2, 4)
    return extract_email_from_profile_page(page)


def scroll_profile_page(page: Page, steps: int = 9) -> None:
    """Scroll down the profile page step by step so lazy sections render.

    Experience and About are only rendered once scrolled into view; a reader
    called right after goto() would find them missing. The pointer is moved
    over the page first: wheel events go to what lies under it, and at its
    initial (0, 0) that may be a header that does not scroll. Each step stays
    shorter than the viewport, or a lazy section's trigger could be jumped over
    without ever being in view.
    """
    try:
        page.mouse.move(*SCROLL_POINTER_POSITION)
    except Exception:
        return
    for _ in range(steps):
        try:
            page.mouse.wheel(0, 600)
        except Exception:
            return
        pause_humaine(0.6, 1.4)


def extract_section_text(page: Page, section_xpath: str) -> str:
    """Visible text of the first section matching section_xpath, or "".

    Never raises: a missing or unreadable section reads as empty, never as a
    run failure nor as a guessed value (POC-016 acceptance criterion).
    """
    try:
        section = page.locator(f"xpath={section_xpath}")
        if section.count() == 0:
            return ""
        return section.first.inner_text(timeout=3000).strip()
    except Exception:
        return ""


def extract_rubriques_from_profile_page(page: Page) -> dict[str, str]:
    """Experience and About text of an already-loaded, already-scrolled profile page."""
    return {
        "experience": extract_section_text(
            page, LinkedInProfileSelectors.EXPERIENCE_SECTION_XPATH
        ),
        "infos": extract_section_text(page, LinkedInProfileSelectors.ABOUT_SECTION_XPATH),
    }


def enrich_profiles_with_email(
    page: Page, profiles: list[dict[str, str]]
) -> list[dict[str, str]]:
    """Visit each profile's page and add its email field, one at a time.

    Sequential with a human-like pause between visits: this adds one request
    per profile on top of POC-001's search, raising the account-restriction
    risk (see document/Backlog.md POC-002).
    """
    enriched = []
    for profile in profiles:
        email = visit_profile_and_extract_email(page, profile["url"])
        enriched.append({**profile, "email": email})
        pause_humaine(2, 5)
    return enriched
