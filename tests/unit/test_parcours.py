from source.backend.core.parcours import (
    deriver_signaux,
    duree_en_mois,
    lignes_utiles,
    lire_postes,
)

# Synthetic Experience text shaped like LinkedIn's inner_text (every line
# rendered twice, a grouped entry, a truncated list). No real profile.
EXPERIENCE_MULTI_FONCTION = """Expérience
Expérience
Coach professionnelle
Coach professionnelle
Indépendant · Freelance
janv. 2021 - aujourd’hui · 3 ans 10 mois
janv. 2021 - aujourd’hui · 3 ans 10 mois
Strasbourg, Grand Est, France
Société Exemple
Temps plein · 12 ans
Responsable RH
sept. 2016 - aujourd’hui · 8 ans 2 mois
Chargée de recrutement
2012 - 2016 · 4 ans
Afficher les 7 expériences
"""

EXPERIENCE_ANCIEN_DIRIGEANT = """Expérience
Coach de dirigeants
Cabinet Exemple · Indépendant
2018 - aujourd'hui · 6 ans 10 mois
Directeur général
Industrie Exemple · CDI
2005 - 2018 · 13 ans
"""


def test_lignes_utiles_retire_les_doublons_consecutifs_et_les_blancs():
    assert lignes_utiles("A\nA\n\n  B \nA\n") == ["A", "B", "A"]


def test_duree_en_mois_en_francais_et_en_anglais():
    assert duree_en_mois("5 ans 10 mois") == 70
    assert duree_en_mois("1 an") == 12
    assert duree_en_mois("3 mois") == 3
    assert duree_en_mois("4 yrs 7 mos") == 55
    assert duree_en_mois("") == 0


def test_un_poste_par_ligne_de_dates_meme_rendue_deux_fois():
    postes = lire_postes(EXPERIENCE_MULTI_FONCTION)

    assert [p.libelle for p in postes] == [
        "Coach professionnelle",
        "Responsable RH",
        "Chargée de recrutement",
    ]
    assert [p.en_cours for p in postes] == [True, True, False]


def test_multi_fonction_lu_dans_la_structure_du_parcours():
    signaux = deriver_signaux(EXPERIENCE_MULTI_FONCTION)

    assert signaux.nb_postes_en_cours == 2
    assert signaux.coach_en_cours
    assert signaux.anciennete_coach_mois == 46
    assert signaux.autre_poste_en_cours
    assert not signaux.ancien_dirigeant
    assert signaux.total_annonce == 7


def test_ancien_dirigeant_seulement_sur_un_poste_termine():
    signaux = deriver_signaux(EXPERIENCE_ANCIEN_DIRIGEANT)

    assert signaux.ancien_dirigeant
    assert signaux.coach_en_cours
    assert not signaux.autre_poste_en_cours
    assert signaux.total_annonce == 0


def test_un_dirigeant_en_poste_n_est_pas_un_ancien_dirigeant():
    texte = "Fondatrice et dirigeante\nCabinet · Indépendant\n2019 - aujourd’hui · 5 ans"

    assert not deriver_signaux(texte).ancien_dirigeant


def test_poste_en_cours_en_anglais():
    texte = "Executive Coach\nSelf-employed\nMar 2020 - Present · 4 yrs 7 mos"

    signaux = deriver_signaux(texte)
    assert signaux.coach_en_cours
    assert signaux.anciennete_coach_mois == 55


def test_rubriques_absentes_donnent_des_signaux_vides_sans_erreur():
    signaux = deriver_signaux("", "")

    assert signaux.nb_postes == 0
    assert not signaux.coach_en_cours
    assert not signaux.autre_poste_en_cours
    assert signaux.longueur_infos == 0


def test_texte_sans_ligne_de_dates_ne_devine_aucun_poste():
    assert deriver_signaux("Expérience\nCoach certifié depuis longtemps\n").nb_postes == 0


def test_un_mot_qui_contient_coach_sans_le_commencer_ne_compte_pas():
    texte = "Autocoaching produit\nSociété · CDI\n2020 - aujourd’hui · 4 ans"

    assert not deriver_signaux(texte).coach_en_cours


def test_longueur_infos_sans_doublons_de_rendu():
    assert deriver_signaux("", "Bonjour\nBonjour\nJe coache.").longueur_infos == len(
        "Bonjour Je coache."
    )
