from source.backend.adapters.scraping.profile_email import clean_email


def test_clean_email_accepts_valid_address():
    assert clean_email("marie.dupont@example.com") == "marie.dupont@example.com"


def test_clean_email_strips_whitespace():
    assert clean_email("  marie.dupont@example.com  ") == "marie.dupont@example.com"


def test_clean_email_rejects_missing_value():
    assert clean_email(None) == ""
    assert clean_email("") == ""


def test_clean_email_rejects_malformed_value():
    assert clean_email("pas-un-email") == ""
    assert clean_email("marie.dupont@") == ""
    assert clean_email("@example.com") == ""
