from source.backend.adapters.enrichment.email_site_extractor import (
    extract_email_from_html,
    extract_site_root,
    filter_candidate_urls,
    is_domain_blacklisted,
)


def test_is_domain_blacklisted_exact_domain():
    assert is_domain_blacklisted("https://www.linkedin.com/in/someone") is True


def test_is_domain_blacklisted_subdomain():
    assert is_domain_blacklisted("https://fr.wikipedia.org/wiki/Someone") is True


def test_is_domain_blacklisted_false_for_personal_site():
    assert is_domain_blacklisted("https://jeanne-dupont-coaching.fr") is False


def test_is_domain_blacklisted_platforms_added_after_poc004_real_run():
    assert is_domain_blacklisted("https://www.noomii.com") is True
    assert is_domain_blacklisted("https://viadeo.journaldunet.com") is True
    assert is_domain_blacklisted("https://creators.spotify.com") is True
    assert is_domain_blacklisted("https://music.amazon.co.uk") is True


def test_filter_candidate_urls_removes_blacklisted_only():
    urls = [
        "https://www.linkedin.com/in/someone",
        "https://jeanne-dupont-coaching.fr",
        "https://www.pagesjaunes.fr/annuaire/someone",
    ]
    assert filter_candidate_urls(urls) == ["https://jeanne-dupont-coaching.fr"]


def test_extract_email_from_html_mailto_link():
    html = '<a href="mailto:contact@example.fr">Me contacter</a>'
    assert extract_email_from_html(html) == "contact@example.fr"


def test_extract_email_from_html_plain_text_pattern():
    html = "<p>Ecrivez-moi a jeanne.dupont@example.fr pour toute question.</p>"
    assert extract_email_from_html(html) == "jeanne.dupont@example.fr"


def test_extract_email_from_html_no_email_returns_empty():
    html = "<p>Aucune adresse ici.</p>"
    assert extract_email_from_html(html) == ""


def test_extract_email_from_html_rejects_mailto_with_escaped_quote_artifact():
    # Real case observed on a page during the POC-004 run: a JSON string with
    # an escaped quote leaves a trailing backslash in the mailto: capture.
    # The plain-text pattern elsewhere on the page should still find the
    # clean email.
    html = (
        '<script>var x = "mailto:avecsens@gmail.com\\"; '
        "var contact = \"avecsens@gmail.com\";</script>"
    )
    assert extract_email_from_html(html) == "avecsens@gmail.com"


def test_extract_site_root_strips_path_and_query():
    assert extract_site_root("https://jeanne-dupont-coaching.fr/a-propos?x=1") == "https://jeanne-dupont-coaching.fr"


def test_extract_site_root_invalid_url_returns_empty():
    assert extract_site_root("not-a-url") == ""
