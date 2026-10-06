from source.backend.adapters.scraping.profile_search import (
    RAISON_GISEMENT_EPUISE,
    RAISON_PLAFOND_PAGES,
    RAISON_QUOTA_ATTEINT,
    build_search_url,
    clean_profile_url,
    collecter_profils_inconnus,
    compter_pages_annoncees,
    filtrer_profils_inconnus,
    message_arret,
    parcourir_requetes,
)
from source.backend.core.requetes_recherche import Lieu, Requete


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


def requete(identifiant, **champs):
    return Requete(id=identifiant, libelle=f"Requete {identifiant}", mots_cles="coach", **champs)


def recherche_simulee(gisements, appels=None):
    """Fake search: each query id has its own paginated result set."""

    def rechercher(requete, quota, exclues):
        if appels is not None:
            appels.append((requete.id, quota, exclues))
        extraire_page, page_suivante = gisement(gisements[requete.id])
        return collecter_profils_inconnus(
            extraire_page, page_suivante, quota, exclues, requete.max_pages or 10
        )

    return rechercher


def test_build_search_url_encodes_boolean_query():
    query = '("coach business") AND (France)'

    url = build_search_url(query)

    assert url.startswith("https://www.linkedin.com/search/results/people/?keywords=")
    assert "coach" in url
    assert " " not in url


def test_build_search_url_sans_facette_est_inchangee():
    """POC-008 : la requete historique doit produire exactement l'URL d'avant."""
    url = build_search_url('("coach business") AND (France)')

    assert url == (
        "https://www.linkedin.com/search/results/people/"
        "?keywords=%28%22coach%20business%22%29%20AND%20%28France%29"
    )
    assert "geoUrn" not in url


def test_build_search_url_ajoute_la_facette_de_lieu_encodee():
    url = build_search_url('"coach business"', ["123456"])

    assert url == (
        "https://www.linkedin.com/search/results/people/"
        "?keywords=%22coach%20business%22&geoUrn=%5B%22123456%22%5D"
    )


def test_la_facette_de_lieu_d_une_requete_arrive_dans_l_url():
    regionale = requete("grand_est", lieu=Lieu(libelle="Grand Est", geo_urn="123456"))

    url = build_search_url(regionale.mots_cles, regionale.geo_urns)

    assert url.endswith("?keywords=coach&geoUrn=%5B%22123456%22%5D")


class PageSimulee:
    """Stands for a Playwright page whose pagination bar has n numbered buttons."""

    def __init__(self, indicateurs):
        self.indicateurs = indicateurs
        self.selecteur = None

    def locator(self, selecteur):
        self.selecteur = selecteur
        return self

    def count(self):
        return self.indicateurs


def test_compter_pages_annoncees_compte_les_boutons_numerotes():
    page = PageSimulee(10)

    assert compter_pages_annoncees(page) == 10
    assert page.selecteur == '[data-testid^="pagination-indicator-"]'


def test_compter_pages_annoncees_sans_barre_ne_devine_rien():
    assert compter_pages_annoncees(PageSimulee(0)) is None


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


def test_parcours_lance_les_requetes_dans_l_ordre_avec_un_bilan_par_requete():
    gisements = {"a": [[profil("marie")]], "b": [[profil("jean"), profil("lea")]]}

    bilans = parcourir_requetes(
        [requete("a"), requete("b")], recherche_simulee(gisements), max_profiles=10
    )

    assert [b.requete.id for b in bilans] == ["a", "b"]
    assert [len(b.resultat) for b in bilans] == [1, 2]
    assert [b.resultat.raison_arret for b in bilans] == [RAISON_GISEMENT_EPUISE] * 2


def test_parcours_deduplique_entre_deux_requetes_qui_se_recouvrent():
    """Critere d'acceptation : urls_connues est enrichi d'une requete a la suivante."""
    gisements = {
        "a": [[profil("marie"), profil("jean")]],
        "b": [[profil("jean"), profil("lea")]],
    }
    appels = []

    bilans = parcourir_requetes(
        [requete("a"), requete("b")], recherche_simulee(gisements, appels), max_profiles=10
    )

    assert [p["nom"] for p in bilans[0].resultat.profils] == ["marie", "jean"]
    assert [p["nom"] for p in bilans[1].resultat.profils] == ["lea"]
    assert appels[0][2] == frozenset()
    assert appels[1][2] == {profil("marie")["url"], profil("jean")["url"]}


def test_parcours_exclut_les_profils_du_magasin_pour_toutes_les_requetes():
    gisements = {"a": [[profil("marie")]], "b": [[profil("marie"), profil("jean")]]}

    bilans = parcourir_requetes(
        [requete("a"), requete("b")],
        recherche_simulee(gisements),
        max_profiles=10,
        urls_connues={profil("marie")["url"]},
    )

    assert bilans[0].resultat.profils == []
    assert [p["nom"] for p in bilans[1].resultat.profils] == ["jean"]


def test_parcours_partage_le_plafond_du_run_entre_les_requetes():
    gisements = {
        "a": [[profil("marie"), profil("jean")]],
        "b": [[profil("lea"), profil("paul"), profil("zoe")]],
        "c": [[profil("noe")]],
    }
    appels = []

    bilans = parcourir_requetes(
        [requete("a"), requete("b"), requete("c")],
        recherche_simulee(gisements, appels),
        max_profiles=3,
    )

    assert [(b.requete.id, b.profils_demandes, len(b.resultat)) for b in bilans] == [
        ("a", 3, 2),
        ("b", 1, 1),
    ]
    assert bilans[1].resultat.raison_arret == RAISON_QUOTA_ATTEINT
    # The third query is never run once the run ceiling is reached.
    assert [identifiant for identifiant, _, _ in appels] == ["a", "b"]


def test_parcours_respecte_le_plafond_de_pages_propre_a_une_requete():
    gisements = {"a": [[profil("marie")], [profil("jean")], [profil("lea")]]}

    (bilan,) = parcourir_requetes(
        [requete("a", max_pages=2)], recherche_simulee(gisements), max_profiles=10
    )

    assert bilan.resultat.raison_arret == RAISON_PLAFOND_PAGES
    assert bilan.resultat.pages_visitees == 2


def test_parcours_sans_plafond_ne_lance_aucune_recherche():
    appels = []

    bilans = parcourir_requetes(
        [requete("a")], recherche_simulee({"a": [[profil("marie")]]}, appels), max_profiles=0
    )

    assert bilans == []
    assert appels == []


def test_message_arret_par_requete_utilise_le_quota_qui_lui_restait():
    gisements = {"a": [[profil("marie"), profil("jean")]], "b": [[profil("lea")]]}

    bilans = parcourir_requetes(
        [requete("a"), requete("b")], recherche_simulee(gisements), max_profiles=5
    )

    message = message_arret(bilans[1].resultat, bilans[1].profils_demandes)
    assert "1 nouveaux profils sur 3" in message
