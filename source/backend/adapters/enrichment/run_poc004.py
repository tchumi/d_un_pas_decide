"""POC-004 entry script: web enrichment pipeline (deterministic, no LLM).

For each profile already extracted (input CSV from POC-001/POC-002), search
the web via the Brave Search API for an alternative contact, filter out
irrelevant domains, then visit the remaining candidate page via a simple HTTP
request and extract an email/site with regex. See document/Backlog.md
POC-004 for the full pipeline description and RGPD safeguards.

Usage:
    python -m source.backend.adapters.enrichment.run_poc004

Run standalone (never via `streamlit run`, see CLAUDE.md rule 6). No browser
involved here: candidate pages are fetched via plain HTTP requests, not
Playwright.
"""

import csv
from pathlib import Path

import requests

from source.backend.adapters.enrichment.email_site_extractor import (
    extract_email_from_html,
    extract_site_root,
    filter_candidate_urls,
)
from source.backend.adapters.enrichment.web_search import (
    build_search_query,
    get_brave_api_key,
    search_candidate_urls,
)
from source.backend.adapters.storage.csv_export import export_profiles_to_csv

INPUT_CSV = Path("./profils_extraits_email.csv")
OUTPUT_CSV = Path("./profils_extraits_enrichis.csv")

# Raised to 25 (user decision, 10/07/2026) after the first 5-profile batch
# confirmed the pipeline mechanism works end-to-end (bug found and fixed on
# Brave's 50-word query limit) but showed 0/5 relevant candidates on that
# small sample - a larger batch is needed to judge the real relevance rate.
MAX_PROFILES = 25


def load_profiles(csv_path: Path) -> list[dict[str, str]]:
    """Read profiles from a CSV file produced by an earlier ticket."""
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fetch_candidate_html(url: str) -> str:
    """Fetch a candidate page's HTML via a simple HTTP request.

    Never raises: an unreachable page or failed request is treated as "no
    conclusive content" rather than a blocking error, same pattern as
    POC-002's email extraction.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return ""


def enrich_profile(profile: dict[str, str], api_key: str) -> dict[str, str]:
    """Search, filter and visit candidate pages for one profile, returning it
    with email_web/site_web added (blank if nothing conclusive was found).
    """
    query = build_search_query(profile["nom"], profile["titre"], profile["localisation"])
    candidate_urls = filter_candidate_urls(search_candidate_urls(query, api_key))

    email_web = ""
    site_web = ""
    for url in candidate_urls:
        html = fetch_candidate_html(url)
        if not html:
            continue
        email_web = extract_email_from_html(html)
        site_web = extract_site_root(url)
        if email_web or site_web:
            break

    return {**profile, "email_web": email_web, "site_web": site_web}


def main() -> None:
    api_key = get_brave_api_key()
    profiles = load_profiles(INPUT_CSV)[:MAX_PROFILES]
    enriched = [enrich_profile(profile, api_key) for profile in profiles]

    export_profiles_to_csv(enriched, OUTPUT_CSV)
    print(f"{len(enriched)} profils enrichis -> {OUTPUT_CSV.resolve()}")


if __name__ == "__main__":
    main()
