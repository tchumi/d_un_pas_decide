"""Brave Search API client for the POC-004 enrichment pipeline.

No LinkedIn/Google scraping here (see document/Backlog.md POC-004): only the
Brave Search API is called, never the search engine's result pages directly.
"""

import os

import requests
from dotenv import load_dotenv

BRAVE_SEARCH_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
DEFAULT_RESULT_COUNT = 5

# Brave Search API rejects queries over 50 words (HTTP 422). LinkedIn "titre"
# fields can be a full bio (observed: 69 words for a real profile), so it is
# truncated first to stay under the limit; name and location are short and
# matter more for identifying the right person.
MAX_QUERY_WORDS = 50


def build_search_query(nom: str, titre: str, localisation: str) -> str:
    """Build the search query for a profile: quoted name + title + location,
    truncating the title first if the total exceeds Brave's 50-word limit.
    """
    fixed_parts = [f'"{nom}"', localisation]
    fixed_word_count = sum(len(part.split()) for part in fixed_parts if part)
    title_budget = max(0, MAX_QUERY_WORDS - fixed_word_count)

    title_words = titre.split()
    truncated_titre = " ".join(title_words[:title_budget])

    parts = [f'"{nom}"', truncated_titre, localisation]
    return " ".join(part for part in parts if part)


def get_brave_api_key() -> str:
    """Load BRAVE_SEARCH_API_KEY from .env.local (never hardcoded)."""
    load_dotenv(".env.local")
    api_key = os.getenv("BRAVE_SEARCH_API_KEY")
    if not api_key:
        raise RuntimeError("BRAVE_SEARCH_API_KEY manquante : verifier .env.local")
    return api_key


def search_candidate_urls(query: str, api_key: str, count: int = DEFAULT_RESULT_COUNT) -> list[str]:
    """Call the Brave Search API and return the top result URLs for the query.

    Returns an empty list on any request/parsing failure rather than raising:
    a missing search result is not a blocking error for the enrichment
    pipeline (same pattern as POC-002's email extraction).
    """
    headers = {"Accept": "application/json", "X-Subscription-Token": api_key}
    params = {"q": query, "count": count}
    try:
        response = requests.get(BRAVE_SEARCH_ENDPOINT, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return []

    results = data.get("web", {}).get("results", [])
    return [result["url"] for result in results if result.get("url")]
