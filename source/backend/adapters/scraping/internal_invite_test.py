"""POC-005: internal-only "invite with note" feasibility test.

Deliberate, narrow exception to the read-only rule for this repo (see
document/Backlog.md POC-005) - restricted to a hardcoded whitelist of
internal, consenting profiles. This is not wired to the scraping pipeline
and must never be: WHITELISTED_PROFILE_URLS is the only source of truth for
which URLs this module will act on.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from source.backend.adapters.scraping.selectors import LinkedInInviteSelectors

DEBUG_SCREENSHOT_DIR = Path("./debug_poc005")

MAX_NOTE_LENGTH = 300

# Hardcoded whitelist - the only URLs send_invitation_with_note() will ever
# act on. Validated by the user, see document/Backlog.md POC-005.
WHITELISTED_PROFILE_URLS = frozenset(
    {
        "linkedin.com/in/henri-pierre-michaud-19a0a6b0",
        "linkedin.com/in/choffstetter",
        "linkedin.com/in/wanda-kleck-76ba342b8",
    }
)


class InviteOutcome(str, Enum):
    SENT = "sent"
    ALREADY_CONNECTED = "already_connected"
    FAILED = "failed"


@dataclass
class InviteResult:
    url: str
    outcome: InviteOutcome
    detail: str = ""


def _normalize_url(url: str) -> str:
    """Strip scheme/query/trailing slash for a robust whitelist comparison,
    independent of how the caller formats the URL."""
    stripped = url.strip()
    for prefix in ("https://www.", "http://www.", "https://", "http://"):
        if stripped.startswith(prefix):
            stripped = stripped[len(prefix) :]
            break
    return stripped.split("?")[0].rstrip("/")


def is_url_whitelisted(url: str) -> bool:
    """Pure check: True only for the exact whitelisted profile URLs."""
    return _normalize_url(url) in WHITELISTED_PROFILE_URLS


def validate_note_length(note: str) -> bool:
    """Pure check: LinkedIn's invitation note limit (~300 characters)."""
    return 0 < len(note) <= MAX_NOTE_LENGTH


def _click_first_actionable(locator, attempts: int, per_attempt_timeout: int) -> bool:
    """Try clicking each matching element in turn and stop at the first
    that succeeds.

    LinkedIn renders several copies of some header buttons (likely for
    different responsive breakpoints); Playwright's ":visible" selector
    filter proved unreliable live against this duplicated markup - it
    timed out even though the button was plainly visible on screen (see
    document/Backlog.md POC-005). Trying each match individually sidesteps
    that instead of depending on that filter.
    """
    for i in range(attempts):
        try:
            locator.nth(i).click(timeout=per_attempt_timeout)
            return True
        except PlaywrightTimeoutError:
            continue
    return False


def _screenshot_detail(page: Page, url: str, step_label: str, match_count: int) -> str:
    """Best-effort diagnostics for a failed step: a screenshot plus a full
    HTML dump to inspect the actual page state at that step without a new
    live run (a screenshot alone isn't enough to tell a wrong selector from
    an actionability issue - see document/Backlog.md POC-005)."""
    DEBUG_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    safe_step = step_label.lower().replace(" ", "_").replace("'", "")
    base_name = f"{_normalize_url(url).replace('/', '_')}_{safe_step}"
    screenshot_path = DEBUG_SCREENSHOT_DIR / f"{base_name}.png"
    html_dump_path = DEBUG_SCREENSHOT_DIR / f"{base_name}.html"
    page.screenshot(path=str(screenshot_path))
    html_dump_path.write_text(page.content(), encoding="utf-8")
    return (
        f"{step_label} introuvable (matches bruts: {match_count}, "
        f"capture: {screenshot_path})"
    )


def _deep_diagnose_add_note_failure(page: Page, url: str) -> str:
    """One-shot, multi-strategy diagnostics for the "Ajouter une note"
    button specifically: several candidate locators tried at once (instead
    of one guess per live run) plus a frame inventory, to settle whether
    this is a shadow-DOM issue, an iframe, or a wrong text/tag assumption.
    """
    detail = _screenshot_detail(page, url, "bouton 'Ajouter une note'", 0)

    frame_urls = [f.url for f in page.frames]

    candidates = {
        "get_by_text_exact": lambda: page.get_by_text(
            "Ajouter une note", exact=True
        ).count(),
        "get_by_text_substring": lambda: page.get_by_text("Ajouter une note").count(),
        "css_text_is_any_tag": lambda: page.locator(
            ':text-is("Ajouter une note")'
        ).count(),
        "css_has_text_button": lambda: page.locator(
            "button", has_text="Ajouter une note"
        ).count(),
        "role_dialog": lambda: page.locator('[role="dialog"]').count(),
        "tag_dialog": lambda: page.locator("dialog").count(),
    }
    results = {}
    for name, probe in candidates.items():
        try:
            results[name] = probe()
        except Exception as exc:  # pylint: disable=broad-except
            results[name] = f"erreur: {exc}"

    return (
        f"{detail} | frames: {frame_urls} | candidats: {results}"
    )


def send_invitation_with_note(page: Page, url: str, note: str) -> InviteResult:
    """Send a LinkedIn connection invitation with a personalized note.

    Refuses structurally (raises, before any navigation) if url is not
    whitelisted - this check cannot be bypassed by a caller. Beyond that,
    never raises for expected LinkedIn states: always returns an
    InviteResult so a caller can process multiple profiles without one
    profile's outcome aborting the run. In particular, a profile already
    connected in 1st degree has no "Se connecter" option to act on - that is
    reported as ALREADY_CONNECTED, not as a failure.
    """
    if not is_url_whitelisted(url):
        raise ValueError(f"URL non autorisee (hors liste blanche) : {url}")

    full_url = f"https://www.{_normalize_url(url)}/"
    page.goto(full_url, timeout=60000)
    # LinkedIn's profile header (incl. the "..." button) is hydrated by JS
    # after the "load" event page.goto() already waits for - give it a
    # fixed extra margin before relying on it being present.
    page.wait_for_timeout(3000)

    overflow_buttons = page.locator(LinkedInInviteSelectors.OVERFLOW_MENU_BUTTON)
    match_count = overflow_buttons.count()
    if not _click_first_actionable(overflow_buttons, match_count, per_attempt_timeout=5000):
        detail = _screenshot_detail(page, url, "bouton '...'", match_count)
        return InviteResult(url, InviteOutcome.FAILED, detail)

    connect_item = page.locator(LinkedInInviteSelectors.CONNECT_MENU_ITEM_XPATH)
    try:
        connect_item.first.wait_for(state="visible", timeout=5000)
    except PlaywrightTimeoutError:
        return InviteResult(
            url,
            InviteOutcome.ALREADY_CONNECTED,
            "option 'Se connecter' absente du menu (deja connecte en 1er degre)",
        )

    if not validate_note_length(note):
        return InviteResult(
            url, InviteOutcome.FAILED, f"note invalide (1-{MAX_NOTE_LENGTH} caracteres)"
        )

    # Dropdown menus commonly ignore clicks landing right after they open
    # (guard against the same click that opened them also selecting an
    # item by bounce). An automated click can land well inside that guard
    # window - give it a human-scale pause first (see document/Backlog.md
    # POC-005: this item's click was otherwise silently swallowed live).
    page.wait_for_timeout(800)

    connect_item_count = connect_item.count()
    if not _click_first_actionable(connect_item, connect_item_count, per_attempt_timeout=5000):
        detail = _screenshot_detail(page, url, "item 'Se connecter'", connect_item_count)
        return InviteResult(url, InviteOutcome.FAILED, detail)

    add_note_buttons = page.locator(LinkedInInviteSelectors.ADD_NOTE_BUTTON)
    # .count() queries the DOM synchronously, unlike .click()/.wait_for()
    # which auto-retry - it can read 0 if this modal (opened by the click
    # just above) hasn't finished rendering yet. Wait for it explicitly
    # first (see document/Backlog.md POC-005: this caused a false failure
    # live even though the button reliably appears moments later).
    try:
        add_note_buttons.first.wait_for(state="visible", timeout=5000)
    except PlaywrightTimeoutError:
        pass  # fall through - count() below will be 0 and reported as such
    add_note_count = add_note_buttons.count()
    if not _click_first_actionable(add_note_buttons, add_note_count, per_attempt_timeout=5000):
        detail = _deep_diagnose_add_note_failure(page, url)
        return InviteResult(url, InviteOutcome.FAILED, detail)

    try:
        page.locator(LinkedInInviteSelectors.NOTE_TEXTAREA).fill(note, timeout=10000)
    except PlaywrightTimeoutError:
        detail = _screenshot_detail(page, url, "zone de texte de la note", 0)
        return InviteResult(url, InviteOutcome.FAILED, detail)

    send_buttons = page.locator(LinkedInInviteSelectors.SEND_INVITATION_BUTTON)
    send_count = send_buttons.count()
    if not _click_first_actionable(send_buttons, send_count, per_attempt_timeout=5000):
        detail = _screenshot_detail(page, url, "bouton 'Envoyer'", send_count)
        return InviteResult(url, InviteOutcome.FAILED, detail)

    # KNOWN LIMITATION (confirmed live, 08/07/2026, see document/Backlog.md
    # POC-005): SENT here only means the click on the send button did not
    # raise - it is not a confirmation that LinkedIn actually registered
    # the invitation server-side. A live run reported SENT for a profile
    # whose "Se connecter" button was still active minutes later (the
    # invitation was never actually received), while another profile in
    # the same run was correctly confirmed pending both in "Envoyees" and
    # on their own profile page. The caller should independently verify
    # (LinkedIn's "Envoyees" list or the target's own profile) before
    # trusting SENT for anything beyond a feasibility signal.
    return InviteResult(url, InviteOutcome.SENT)
