from source.backend.adapters.scraping.profile_search import (
    RAISON_GISEMENT_EPUISE,
    RAISON_PLAFOND_PAGES,
    RAISON_QUOTA_ATTEINT,
    build_search_url,
    clean_profile_url,
    collecter_profils_inconnus,
    filtrer_profils_inconnus,
    message_arret,
)


def profil(slug):
    return {
        "nom": slug,
        "url": f"https://www.linkedin.com/in/{slug}",
        "localisation": "Paris",
        "titre": "Coach business",
    }


def gisement(pages):
    """Fake a paginated result set: no browser, no network."""
    etat = {"page": 0}

    def extraire_page():
        return list(pages[etat["page"]])

    def page_suivante():
        if etat["page"] + 1 >= len(pages):
            return False
        etat["page"] += 1
        return True

    return extraire_page, page_suivante


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


def test_filtrer_profils_inconnus_exclut_les_urls_deja_connues():
    profils = [profil("marie"), profil("jean")]

    retenus = filtrer_profils_inconnus(profils, {"https://www.linkedin.com/in/marie"})

    assert [p["nom"] for p in retenus] == ["jean"]


def test_filtrer_profils_inconnus_dedoublonne_a_l_interieur_du_lot():
    retenus = filtrer_profils_inconnus([profil("marie"), profil("marie")], set())

    assert len(retenus) == 1


def test_filtrer_profils_inconnus_normalise_l_url():
    connue = profil("marie")
    avec_parametres = dict(connue, url=f"{connue['url']}?miniProfileUrn=abc")

    retenus = filtrer_profils_inconnus([avec_parametres], {connue["url"]})

    assert retenus == []


def test_filtrer_profils_inconnus_ecarte_une_carte_sans_url():
    retenus = filtrer_profils_inconnus([dict(profil("marie"), url="")], set())

    assert retenus == []


def test_collecte_pagine_jusqu_a_obtenir_le_quota_de_profils_inconnus():
    pages = [[profil("marie"), profil("jean")], [profil("lea"), profil("paul")]]
    extraire_page, page_suivante = gisement(pages)

    resultat = collecter_profils_inconnus(
        extraire_page, page_suivante, max_profiles=2, urls_connues={profil("marie")["url"]}
    )

    assert [p["nom"] for p in resultat.profils] == ["jean", "lea"]
    assert resultat.raison_arret == RAISON_QUOTA_ATTEINT
    assert resultat.pages_visitees == 2


def test_deux_collectes_successives_produisent_des_lots_disjoints():
    """Critere d'acceptation 1 : aucune URL commune entre deux runs."""
    pages = [[profil("marie"), profil("jean")], [profil("lea"), profil("paul")]]

    extraire_page, page_suivante = gisement(pages)
    premier = collecter_profils_inconnus(extraire_page, page_suivante, max_profiles=2)

    deja_vus = {p["url"] for p in premier.profils}
    extraire_page, page_suivante = gisement(pages)
    second = collecter_profils_inconnus(
        extraire_page, page_suivante, max_profiles=2, urls_connues=deja_vus
    )

    urls_second = {p["url"] for p in second.profils}
    assert deja_vus == {profil("marie")["url"], profil("jean")["url"]}
    assert urls_second == {profil("lea")["url"], profil("paul")["url"]}
    assert deja_vus & urls_second == set()


def test_collecte_signale_un_gisement_epuise_sans_boucler():
    """Critere d'acceptation 2 : lot plus petit que demande, raison explicite."""
    extraire_page, page_suivante = gisement([[profil("marie")], [profil("jean")]])

    resultat = collecter_profils_inconnus(extraire_page, page_suivante, max_profiles=10)

    assert len(resultat.profils) == 2
    assert resultat.raison_arret == RAISON_GISEMENT_EPUISE
    assert resultat.pages_visitees == 2


def test_collecte_s_arrete_au_plafond_de_pages():
    pages_infinies = [[profil("marie")]] * 50
    extraire_page, page_suivante = gisement(pages_infinies)

    resultat = collecter_profils_inconnus(
        extraire_page, page_suivante, max_profiles=10, max_pages=3
    )

    assert resultat.raison_arret == RAISON_PLAFOND_PAGES
    assert resultat.pages_visitees == 3


def test_collecte_d_un_gisement_entierement_connu_ne_ramene_rien():
    pages = [[profil("marie")], [profil("jean")]]
    extraire_page, page_suivante = gisement(pages)
    connues = {profil("marie")["url"], profil("jean")["url"]}

    resultat = collecter_profils_inconnus(
        extraire_page, page_suivante, max_profiles=5, urls_connues=connues
    )

    assert resultat.profils == []
    assert resultat.raison_arret == RAISON_GISEMENT_EPUISE


def test_message_arret_explicite_le_gisement_epuise():
    extraire_page, page_suivante = gisement([[profil("marie")]])
    resultat = collecter_profils_inconnus(extraire_page, page_suivante, max_profiles=25)

    message = message_arret(resultat, 25)

    assert "Gisement epuise" in message
    assert "1 nouveaux profils sur 25" in message


def test_message_arret_du_quota_atteint_reste_neutre():
    extraire_page, page_suivante = gisement([[profil("marie")]])
    resultat = collecter_profils_inconnus(extraire_page, page_suivante, max_profiles=1)

    assert message_arret(resultat, 1).startswith("1 nouveaux profils collectes")
