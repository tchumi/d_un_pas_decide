from source.backend.adapters.scraping.profile_email import (
    clean_email,
    extract_rubriques_from_profile_page,
    extract_section_text,
)
from source.backend.adapters.scraping.selectors import LinkedInProfileSelectors


class _FakeLocator:
    def __init__(self, count=0, text="", error=None):
        self._count, self._text, self._error = count, text, error

    def count(self):
        if self._error:
            raise self._error
        return self._count

    @property
    def first(self):
        return self

    def inner_text(self, timeout=None):
        return self._text


class _FakePage:
    """Minimal stand-in for a Playwright Page: no browser in the test suite."""

    def __init__(self, sections):
        self._sections = sections

    def locator(self, selector):
        return self._sections.get(selector.removeprefix("xpath="), _FakeLocator())


def test_section_absente_donne_une_valeur_vide():
    assert extract_section_text(_FakePage({}), "//section") == ""


def test_section_illisible_donne_une_valeur_vide_jamais_une_erreur():
    page = _FakePage({"//section": _FakeLocator(error=TimeoutError("DOM changed"))})

    assert extract_section_text(page, "//section") == ""


def test_rubriques_lues_chacune_par_son_selecteur():
    page = _FakePage(
        {
            LinkedInProfileSelectors.EXPERIENCE_SECTION_XPATH: _FakeLocator(1, " Expérience\nCoach "),
        }
    )

    assert extract_rubriques_from_profile_page(page) == {
        "experience": "Expérience\nCoach",
        "infos": "",
    }


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
