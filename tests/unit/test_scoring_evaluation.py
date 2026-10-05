import hashlib
import sqlite3

import pytest

from source.backend.adapters.storage.run_poc014_evaluation import (
    VERDICT_BON,
    VERDICT_EXCELLENT,
    VERDICT_MAUVAIS,
    VERDICT_RIEN_A_VOIR,
    evaluer,
    lire_profils_lecture_seule,
    parser_verdict,
)
from source.backend.core.profile_scoring import charger_regles


@pytest.fixture
def regles():
    """The real rule set shipped in config/scoring_rules.json."""
    return charger_regles()


# --- parsing du verdict ------------------------------------------------------


@pytest.mark.parametrize(
    ("commentaire", "attendu"),
    [
        ("excellent profil", VERDICT_EXCELLENT),
        ("bon profil", VERDICT_BON),
        ("mauvais profil", VERDICT_MAUVAIS),
        ("rien à voir", VERDICT_RIEN_A_VOIR),
        ("Bon profil ", VERDICT_BON),
        ("mauvais profil, consultant", VERDICT_MAUVAIS),
        ("rien à voir, service aux coachs", VERDICT_RIEN_A_VOIR),
    ],
)
def test_verdict_reconnu_par_son_prefixe(commentaire, attendu):
    assert parser_verdict(commentaire) == attendu


@pytest.mark.parametrize("commentaire", ["", None, "OK", "à recontacter", "bon profilage", "profil bon"])
def test_commentaire_hors_grille_n_est_jamais_devine(commentaire):
    assert parser_verdict(commentaire) is None


# --- métriques ---------------------------------------------------------------

# Fictitious titles. With the shipped rules: the first two are kept (>= 60),
# the third is under the threshold, the fourth is excluded (no "coach").
PROFILS = [
    {"url": "u1", "titre": "Coach professionnel certifié", "commentaire_client": "bon profil"},
    {"url": "u2", "titre": "Coach professionnel certifié", "commentaire_client": "mauvais profil"},
    {"url": "u3", "titre": "Coach", "commentaire_client": "excellent profil"},
    {"url": "u4", "titre": "Responsable RH", "commentaire_client": "rien à voir"},
    {"url": "u5", "titre": "Coach professionnel certifié", "commentaire_client": "à revoir"},
]


def test_precision_et_rappel_au_seuil(regles):
    evaluation = evaluer(PROFILS, regles)

    assert evaluation.juges == 4
    assert evaluation.positifs == 2
    assert evaluation.retenus == 2
    assert evaluation.retenus_positifs == 1
    assert evaluation.precision == 0.5
    assert evaluation.rappel == 0.5
    assert evaluation.taux_de_base == 0.5


def test_bon_profil_sous_le_seuil_est_liste(regles):
    evaluation = evaluer(PROFILS, regles)

    assert [p["url"] for p in evaluation.positifs_ecartes] == ["u3"]


def test_commentaire_non_reconnu_est_signale_et_sorti_des_chiffres(regles):
    evaluation = evaluer(PROFILS, regles)

    assert [p["url"] for p in evaluation.non_reconnus] == ["u5"]
    assert sum(sum(ligne.values()) for ligne in evaluation.matrice.values()) == 4


def test_matrice_croise_score_et_verdict(regles):
    evaluation = evaluer(PROFILS, regles)

    score_retenu = max(evaluation.matrice)
    assert evaluation.matrice[score_retenu][VERDICT_BON] == 1
    assert evaluation.matrice[score_retenu][VERDICT_MAUVAIS] == 1
    assert evaluation.matrice[0][VERDICT_RIEN_A_VOIR] == 1


def test_pouvoir_discriminant_par_regle(regles):
    evaluation = evaluer(PROFILS, regles)

    # base_coach fires on the three judged coach titles, two of them good.
    assert evaluation.par_regle["base_coach"].declenchee == 3
    assert evaluation.par_regle["base_coach"].positifs == 2
    assert evaluation.par_regle["exclusion_non_coach"].declenchee == 1
    assert evaluation.par_regle["exclusion_non_coach"].part_positifs == 0.0
    assert evaluation.par_regle["hors_cible"].declenchee == 0


def test_evaluer_ne_modifie_pas_les_profils_recus(regles):
    avant = [dict(p) for p in PROFILS]

    evaluer(PROFILS, regles)

    assert PROFILS == avant


# --- lecture seule -----------------------------------------------------------


@pytest.fixture
def magasin(tmp_path):
    chemin = tmp_path / "profils.db"
    conn = sqlite3.connect(chemin)
    conn.execute("CREATE TABLE profils (url TEXT, titre TEXT, commentaire_client TEXT)")
    conn.execute("INSERT INTO profils VALUES ('u1', 'Coach', 'bon profil')")
    conn.commit()
    conn.close()
    return chemin


def test_lecture_du_magasin_ne_modifie_pas_le_fichier(magasin):
    empreinte = hashlib.md5(magasin.read_bytes()).hexdigest()

    profils = lire_profils_lecture_seule(magasin)

    assert profils == [{"url": "u1", "titre": "Coach", "commentaire_client": "bon profil"}]
    assert hashlib.md5(magasin.read_bytes()).hexdigest() == empreinte


def test_connexion_en_lecture_seule_ne_cree_pas_de_magasin(tmp_path):
    absent = tmp_path / "absent.db"

    with pytest.raises(sqlite3.OperationalError):
        lire_profils_lecture_seule(absent)

    assert not absent.exists()
