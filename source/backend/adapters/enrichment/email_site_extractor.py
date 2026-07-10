"""Domain blacklist filtering and regex-based email/site extraction (POC-004).

Pure logic, no network calls here: no LLM, no interpretation, only a domain
blacklist and regex patterns, matching the deterministic v1 pipeline described
in document/Backlog.md (POC-004). A missing or unparsable value degrades to
"" rather than raising, same pattern as profile_email.py (POC-002).
"""

import re
from urllib.parse import unquote, urlparse

# Domains considered irrelevant for a personal/professional contact page:
# social networks, directories, encyclopedic sites. Adjust based on false
# positives observed during real runs (see document/Backlog.md POC-004).
BLACKLISTED_DOMAINS = frozenset(
    {
        "linkedin.com",
        "facebook.com",
        "instagram.com",
        "twitter.com",
        "x.com",
        "pagesjaunes.fr",
        "societe.com",
        "wikipedia.org",
        "viadeo.com",
        "indeed.com",
        "glassdoor.com",
        "glassdoor.fr",
        "malt.fr",
        "annuaire-entreprises.data.gouv.fr",
        # Added after the 25-profile real run (10/07/2026, see Backlog.md
        # POC-004): confirmed false positives, all directories/platforms
        # rather than personal sites.
        "noomii.com",  # coach directory
        "journaldunet.com",  # hosts defunct Viadeo profiles (viadeo.journaldunet.com)
        "spotify.com",
        "amazon.co.uk",
    }
)

# TLD restricted to letters only (not just "not @/whitespace"): real-world
# HTML/JS often embeds mailto: links with escaped quotes (e.g. `mailto:x@y.com\"`
# inside a JSON string), and a too-permissive TLD group let a trailing
# backslash through (observed on a real page during the POC-004 run).
EMAIL_VALIDATION_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
MAILTO_PATTERN = re.compile(r'mailto:([^"\'\s?]+)', re.IGNORECASE)
EMAIL_TEXT_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def is_domain_blacklisted(url: str) -> bool:
    """Return True if the URL's domain (or a subdomain of it) is blacklisted."""
    netloc = urlparse(url).netloc.lower().removeprefix("www.")
    return any(netloc == domain or netloc.endswith(f".{domain}") for domain in BLACKLISTED_DOMAINS)


def filter_candidate_urls(urls: list[str]) -> list[str]:
    """Keep only URLs whose domain is not blacklisted."""
    return [url for url in urls if not is_domain_blacklisted(url)]


def clean_email(raw_email: str | None) -> str:
    """Return a stripped, validated email, or "" if missing/malformed."""
    if not raw_email:
        return ""
    candidate = raw_email.strip()
    if not EMAIL_VALIDATION_PATTERN.match(candidate):
        return ""
    return candidate


def extract_email_from_html(html: str) -> str:
    """Extract an email from a page's HTML: a mailto: link first, otherwise a
    plain email pattern in the text. Returns "" if nothing conclusive.
    """
    mailto_match = MAILTO_PATTERN.search(html)
    if mailto_match:
        cleaned = clean_email(unquote(mailto_match.group(1)))
        if cleaned:
            return cleaned

    text_match = EMAIL_TEXT_PATTERN.search(html)
    if text_match:
        return clean_email(text_match.group(0))

    return ""


def extract_site_root(url: str) -> str:
    """Return the root URL (scheme + netloc) of a candidate page, or "" if
    the URL is not absolute.
    """
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}"
