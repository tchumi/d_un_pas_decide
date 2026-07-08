"""POC-005 entry script: send a LinkedIn connection invitation with a
personalized note to exactly 3 hardcoded, internal, consenting profiles.
Single manual execution - no loop, no scheduling (see document/Backlog.md
POC-005 for the read-only exception this ticket introduces).

Structural safety: send_invitation_with_note() itself refuses any URL not
in WHITELISTED_PROFILE_URLS - editing INVITES below to add another profile
would still be rejected at runtime.

Henri-Pierre is already a 1st-degree connection with the test account
(confirmed by the user on 08/07/2026): included to confirm and document the
ALREADY_CONNECTED outcome, not to actually send a note - "" is passed since
the note step is never reached for him.

Usage:
    python -m source.backend.adapters.scraping.run_poc005

Run standalone (never via `streamlit run`, see CLAUDE.md rule 6).
"""

from pathlib import Path

from source.backend.adapters.scraping.browser_session import (
    ensure_logged_in,
    open_browser_session,
)
from source.backend.adapters.scraping.internal_invite_test import (
    send_invitation_with_note,
)

PROFILE_DIR = Path("./browser_profile")

# Notes validated by the user on 08/07/2026, see document/Backlog.md POC-005.
INVITES = [
    ("linkedin.com/in/henri-pierre-michaud-19a0a6b0", ""),
    ("linkedin.com/in/choffstetter", "hello ici beau temps et mer calme"),
    ("linkedin.com/in/wanda-kleck-76ba342b8", "hello Wanda, on arrive..."),
]


def main() -> None:
    with open_browser_session(PROFILE_DIR) as (context, page):
        ensure_logged_in(page, context)
        for url, note in INVITES:
            result = send_invitation_with_note(page, url, note)
            print(f"{url} -> {result.outcome.value} ({result.detail})")


if __name__ == "__main__":
    main()
