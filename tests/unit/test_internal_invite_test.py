from source.backend.adapters.scraping.internal_invite_test import (
    MAX_NOTE_LENGTH,
    is_url_whitelisted,
    validate_note_length,
)


def test_is_url_whitelisted_accepts_the_three_whitelisted_urls():
    assert is_url_whitelisted("linkedin.com/in/henri-pierre-michaud-19a0a6b0") is True
    assert is_url_whitelisted("linkedin.com/in/choffstetter") is True
    assert is_url_whitelisted("linkedin.com/in/wanda-kleck-76ba342b8") is True


def test_is_url_whitelisted_accepts_url_format_variants():
    assert is_url_whitelisted("https://www.linkedin.com/in/choffstetter") is True
    assert is_url_whitelisted("https://www.linkedin.com/in/choffstetter/") is True
    assert (
        is_url_whitelisted("https://www.linkedin.com/in/choffstetter?trk=public")
        is True
    )


def test_is_url_whitelisted_rejects_any_other_url():
    assert is_url_whitelisted("linkedin.com/in/some-random-prospect") is False
    assert is_url_whitelisted("linkedin.com/in/choffstetter-fake") is False
    assert is_url_whitelisted("linkedin.com/in/choffstette") is False
    assert is_url_whitelisted("linkedin.com") is False
    assert is_url_whitelisted("") is False


def test_validate_note_length_accepts_note_within_limit():
    assert validate_note_length("hello ici beau temps et mer calme") is True


def test_validate_note_length_accepts_note_at_max_length():
    assert validate_note_length("a" * MAX_NOTE_LENGTH) is True


def test_validate_note_length_rejects_note_over_max_length():
    assert validate_note_length("a" * (MAX_NOTE_LENGTH + 1)) is False


def test_validate_note_length_rejects_empty_note():
    assert validate_note_length("") is False
