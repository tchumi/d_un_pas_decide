from source.backend.adapters.enrichment.web_search import build_search_query


def test_build_search_query_combines_all_fields():
    query = build_search_query("Jeanne Dupont", "Coach professionnel", "Lyon, France")
    assert query == '"Jeanne Dupont" Coach professionnel Lyon, France'


def test_build_search_query_quotes_the_name_only():
    query = build_search_query("Jean Martin", "Coach", "Paris")
    assert query.startswith('"Jean Martin"')


def test_build_search_query_skips_empty_fields():
    query = build_search_query("Jeanne Dupont", "", "Lyon")
    assert query == '"Jeanne Dupont" Lyon'


def test_build_search_query_truncates_long_title_to_stay_under_brave_limit():
    long_titre = " ".join(f"mot{i}" for i in range(69))
    query = build_search_query("Magali Balhadere", long_titre, "Mimizan, France")

    assert len(query.split()) <= 50
    assert query.startswith('"Magali Balhadere"')
    assert query.endswith("Mimizan, France")
