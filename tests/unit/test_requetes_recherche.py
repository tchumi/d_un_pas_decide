import json

import pytest

from source.backend.core.requetes_recherche import (
    ConfigRequetesInvalide,
    Lieu,
    charger_requetes,
)

# The query run_poc001 carried in code before POC-008, character for character.
REQUETE_HISTORIQUE = (
    '("coach business" OR "coach professionnel" OR "coach entreprise") '
    'AND (France) NOT ("life coach" OR "sportif")'
)


def requete(**surcharges):
    base = {"id": "r1", "libelle": "Requete 1", "mots_cles": '"coach business"'}
    base.update(surcharges)
    return base


def ecrire(tmp_path, contenu):
    chemin = tmp_path / "requetes.json"
    texte = contenu if isinstance(contenu, str) else json.dumps(contenu)
    chemin.write_text(texte, encoding="utf-8")
    return chemin


def config(*requetes, **surcharges):
    base = {"version": 1, "max_profils_par_run": 25, "requetes": list(requetes)}
    base.update(surcharges)
    return base


def test_le_fichier_reel_reprend_la_requete_historique_a_l_identique():
    """Critere d'acceptation : un run sans nouvelle requete se comporte comme avant."""
    configuration = charger_requetes()

    premiere = configuration.requetes[0]
    assert premiere.mots_cles == REQUETE_HISTORIQUE
    assert premiere.lieu is None
    assert premiere.max_pages is None
    assert premiere.active is True
    assert configuration.max_profils_par_run == 25


def test_charge_une_requete_minimale_avec_les_valeurs_par_defaut(tmp_path):
    configuration = charger_requetes(ecrire(tmp_path, config(requete())))

    (seule,) = configuration.requetes
    assert (seule.id, seule.libelle, seule.mots_cles) == ("r1", "Requete 1", '"coach business"')
    assert seule.lieu is None
    assert seule.geo_urns == ()
    assert seule.provisoire is False
    assert seule.active is True


def test_charge_une_requete_avec_facette_de_lieu_et_plafond_de_pages(tmp_path):
    brute = requete(
        lieu={"libelle": "Grand Est", "geo_urn": "123456"}, max_pages=3, provisoire=True
    )

    (seule,) = charger_requetes(ecrire(tmp_path, config(brute))).requetes

    assert seule.lieu == Lieu(libelle="Grand Est", geo_urn="123456")
    assert seule.geo_urns == ("123456",)
    assert seule.max_pages == 3
    assert seule.provisoire is True


def test_actives_ecarte_les_requetes_desactivees_en_gardant_l_ordre(tmp_path):
    chemin = ecrire(
        tmp_path,
        config(requete(id="a"), requete(id="b", active=False), requete(id="c")),
    )

    configuration = charger_requetes(chemin)

    assert [r.id for r in configuration.requetes] == ["a", "b", "c"]
    assert [r.id for r in configuration.actives()] == ["a", "c"]


def test_fichier_absent_leve_une_erreur_explicite(tmp_path):
    with pytest.raises(ConfigRequetesInvalide, match="introuvable"):
        charger_requetes(tmp_path / "absent.json")


def test_json_malforme_leve_une_erreur_explicite(tmp_path):
    with pytest.raises(ConfigRequetesInvalide, match="malforme"):
        charger_requetes(ecrire(tmp_path, "{ pas du json"))


@pytest.mark.parametrize("requetes", [[], None, "coach"])
def test_liste_de_requetes_vide_ou_absente_refusee(tmp_path, requetes):
    with pytest.raises(ConfigRequetesInvalide, match="liste non vide"):
        charger_requetes(ecrire(tmp_path, {"max_profils_par_run": 25, "requetes": requetes}))


def test_identifiant_en_double_refuse(tmp_path):
    with pytest.raises(ConfigRequetesInvalide, match="en double"):
        charger_requetes(ecrire(tmp_path, config(requete(), requete())))


@pytest.mark.parametrize("champ", ["id", "libelle", "mots_cles"])
@pytest.mark.parametrize("valeur", ["", "   ", None])
def test_champ_obligatoire_vide_refuse(tmp_path, champ, valeur):
    with pytest.raises(ConfigRequetesInvalide, match=champ):
        charger_requetes(ecrire(tmp_path, config(requete(**{champ: valeur}))))


@pytest.mark.parametrize(
    "lieu",
    [
        {"libelle": "Grand Est"},
        {"libelle": "Grand Est", "geo_urn": ""},
        {"libelle": "Grand Est", "geo_urn": "Grand Est"},
        {"geo_urn": "123456"},
        "Grand Est",
    ],
)
def test_lieu_incomplet_ou_non_numerique_refuse(tmp_path, lieu):
    with pytest.raises(ConfigRequetesInvalide, match="lieu"):
        charger_requetes(ecrire(tmp_path, config(requete(lieu=lieu))))


@pytest.mark.parametrize("max_pages", [0, -1, "3", True, 2.5])
def test_plafond_de_pages_invalide_refuse(tmp_path, max_pages):
    with pytest.raises(ConfigRequetesInvalide, match="max_pages"):
        charger_requetes(ecrire(tmp_path, config(requete(max_pages=max_pages))))


@pytest.mark.parametrize("plafond", [0, -5, "25", None, True])
def test_plafond_de_profils_du_run_invalide_refuse(tmp_path, plafond):
    with pytest.raises(ConfigRequetesInvalide, match="max_profils_par_run"):
        charger_requetes(ecrire(tmp_path, config(requete(), max_profils_par_run=plafond)))


def test_drapeau_non_booleen_refuse(tmp_path):
    with pytest.raises(ConfigRequetesInvalide, match="active"):
        charger_requetes(ecrire(tmp_path, config(requete(active="oui"))))


def test_aucune_requete_active_refuse(tmp_path):
    with pytest.raises(ConfigRequetesInvalide, match="aucune requete active"):
        charger_requetes(ecrire(tmp_path, config(requete(active=False))))
