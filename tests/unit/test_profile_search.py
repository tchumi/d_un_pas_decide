from source.backend.adapters.scraping.profile_search import (
    build_search_url,
    clean_profile_url,
)


def test_build_search_url_encodes_boolean_query():
    query = '("coach business") AND (France)'

    url = build_search_url(query)

    assert url.startswith("https://www.linkedin.com/search/results/people/?keywords=")
    assert "coach" in url
    assert " " not in url


def test_clean_profile_url_strips_query_params():
    raw_url = "https://www.linkedin.com/in/marie-dupont?miniProfileUrn=abc&trk=xyz"

    cleaned = clean_profile_url(raw_url)

    assert cleaned == "https://www.linkedin.com/in/marie-dupont"


def test_clean_profile_url_strips_fragment():
    raw_url = "https://www.linkedin.com/in/marie-dupont#experience"

    cleaned = clean_profile_url(raw_url)

    assert cleaned == "https://www.linkedin.com/in/marie-dupont"


def test_clean_profile_url_handles_missing_url():
    assert clean_profile_url(None) == ""
    assert clean_profile_url("") == ""
