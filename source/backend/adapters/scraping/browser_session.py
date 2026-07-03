"""Playwright browser session handling: persistent context + manual login.

No Streamlit import here (see CLAUDE.md / ARCHITECTURE.md): this module must
stay usable standalone, independently of the UI.
"""

from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import BrowserContext, Page, sync_playwright

from source.backend.adapters.scraping.selectors import LinkedInAuthSelectors

LINKEDIN_HOME_URL = "https://www.linkedin.com/"


@contextmanager
def open_browser_session(profile_dir: Path, headless: bool = False):
    """Open a Playwright persistent context tied to profile_dir.

    The persistent context keeps the LinkedIn session (cookies, storage)
    across runs, so a valid login only needs to happen once.
    """
    profile_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=headless,
        )
        try:
            page = context.new_page()
            yield context, page
        finally:
            context.close()


def is_logged_in(page: Page) -> bool:
    """Check whether the current page indicates an authenticated session.

    A logged-in session redirects https://www.linkedin.com/ to /feed/. A
    logged-out session stays on the plain homepage (no "login"/"authwall"
    marker in the URL in that case), so absence of those markers cannot be
    used as a positive signal - only the feed redirect can.
    """
    return LinkedInAuthSelectors.FEED_URL_MARKER in page.url


def ensure_logged_in(page: Page, context: BrowserContext) -> None:
    """Navigate to LinkedIn and block on manual login if not authenticated.

    The script never fills the login form itself: the user logs in by hand
    in the visible browser window, then confirms in the console.
    """
    page.goto(LINKEDIN_HOME_URL, timeout=60000)

    if not is_logged_in(page):
        input(
            "\n>>> Connecte-toi manuellement dans la fenetre Chrome qui "
            "s'est ouverte, puis reviens ici et appuie sur Entree...\n"
        )
