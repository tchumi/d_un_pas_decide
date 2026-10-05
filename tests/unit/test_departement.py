"""Tests for the derivation of the departement from a LinkedIn location (POC-015).

The rule under test is a refusal as much as a lookup: whatever cannot be tied
to exactly one departement must give an empty string, never a guess. Most
cases below are locations actually present in the store on 05/10/2026.
"""

import pytest

from source.backend.core.departement import (
    DEFAULT_COMMUNES_PATH,
    DEFAULT_DEPARTEMENTS_PATH,
    TableDepartements,
    charger_table,
    deriver_departement,
)


@pytest.mark.parametrize(
    ("localisation", "attendu"),
    [
        ("Strasbourg, Grand Est, France", "67 - Bas-Rhin"),
        ("Paris, Île-de-France, France", "75 - Paris"),
        ("Bordeaux, Nouvelle-Aquitaine, France", "33 - Gironde"),
        ("Orléans, Centre-Val de Loire, France", "45 - Loiret"),
        ("Château-Gontier-sur-Mayenne, Pays de la Loire, France", "53 - Mayenne"),
        # A leading zero must survive: the column is sorted as text.
        ("Bourg-en-Bresse, Auvergne-Rhône-Alpes, France", "01 - Ain"),
        ("Ajaccio, Corse, France", "2A - Corse-du-Sud"),
    ],
)
def test_commune_region_france_donne_numero_et_nom(localisation, attendu):
    assert deriver_departement(localisation) == attendu


@pytest.mark.parametrize(
    "localisation",
    [
        "STRASBOURG, grand est, france",
        "Strasbourg ,  Grand Est ,France",
        "Orleans, Centre Val de Loire, France",
    ],
)
def test_casse_accents_et_espaces_sont_indifferents(localisation):
    assert deriver_departement(localisation) != ""


def test_apostrophe_et_trema_absents_du_libelle_linkedin():
    # LinkedIn writes "L'Hay-les-Roses"; the official name is "L'Haÿ-les-Roses".
    assert deriver_departement("L'Hay-les-Roses, Île-de-France, France") == "94 - Val-de-Marne"
    assert deriver_departement("L’Haÿ-les-Roses, Île-de-France, France") == "94 - Val-de-Marne"


def test_ville_de_paris_est_paris():
    assert deriver_departement("Ville de Paris, Île-de-France, France") == "75 - Paris"


@pytest.mark.parametrize(
    "localisation",
    [
        # Floirac exists in Gironde and in Charente-Maritime, Vougy in Loire and
        # in Haute-Savoie: same region each time, nothing tells them apart.
        "Floirac, Nouvelle-Aquitaine, France",
        "Vougy, Auvergne-Rhône-Alpes, France",
    ],
)
def test_commune_homonyme_dans_la_meme_region_reste_vide(localisation):
    assert deriver_departement(localisation) == ""


def test_la_region_departage_un_homonyme_d_une_autre_region():
    # The third Floirac is in the Lot, alone of its name in Occitanie.
    assert deriver_departement("Floirac, Occitanie, France") == "46 - Lot"


@pytest.mark.parametrize(
    "localisation",
    [
        "Paris et périphérie",
        "Lille et périphérie",
        "Nice et périphérie",
        "France",
        "Espagne",
        "Suisse",
        "Pays de la Loire, France",
        "Paris, Île-de-France",
        "Paris",
        "",
        None,
    ],
)
def test_localisation_non_rattachable_reste_vide(localisation):
    assert deriver_departement(localisation) == ""


@pytest.mark.parametrize(
    "localisation",
    [
        "Trifouillis-les-Oies, Grand Est, France",  # unknown commune
        "Strasbourg, Bretagne, France",  # commune of another region
        "Strasbourg, Alsace, France",  # region the table does not know
        "Barcelona, Catalonia, Spain",
        "Strasbourg, Grand Est, France, Europe",
    ],
)
def test_commune_ou_region_inconnue_reste_vide(localisation):
    assert deriver_departement(localisation) == ""


def test_la_table_est_injectable():
    table = TableDepartements(
        libelles={"99": "99 - Essai"},
        communes={("ville test", "region test"): frozenset({"99"})},
    )

    assert deriver_departement("Ville-Test, Région Test, France", table) == "99 - Essai"
    assert deriver_departement("Strasbourg, Grand Est, France", table) == ""


def test_la_table_versionnee_couvre_les_101_departements():
    table = charger_table(DEFAULT_DEPARTEMENTS_PATH, DEFAULT_COMMUNES_PATH)

    assert len(table.libelles) == 101
    presents = {code for codes in table.communes.values() for code in codes}
    assert presents == set(table.libelles)
