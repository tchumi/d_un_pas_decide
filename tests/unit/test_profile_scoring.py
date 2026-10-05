import json
import statistics

import pytest

from source.backend.core.profile_scoring import (
    charger_regles,
    normaliser,
    sauvegarder_regles,
    scorer_profils,
    scorer_titre,
    selectionner_profils_interessants,
)


@pytest.fixture
def regles():
    """The real rule set shipped in config/scoring_rules.json."""
    return charger_regles()


# --- normalisation ---------------------------------------------------------


def test_normaliser_lowercases_and_strips_accents():
    assert normaliser("Coach Professionnel Certifié") == "coach professionnel certifie"


def test_normaliser_turns_punctuation_into_spaces():
    # Typographic apostrophe, hyphen and multiple spaces all collapse the same way.
    assert normaliser("Coach-Professionnel") == "coach professionnel"
    assert normaliser("Coach d’entreprise") == "coach d entreprise"
    assert normaliser("Coach   business  ·  ICF") == "coach business icf"


# --- exclusions ------------------------------------------------------------


def test_titre_sans_marqueur_coach_est_exclu(regles):
    resultat = scorer_titre("HR Senior Manager - Responsable RH Senior - Transformation", regles)

    assert resultat.categorie == "exclu"
    assert resultat.score == 0
    assert "exclusion_non_coach" in resultat.justification


def test_titre_vide_est_exclu(regles):
    resultat = scorer_titre("", regles)

    assert resultat.categorie == "exclu"
    assert resultat.score == 0


def test_life_coach_est_exclu(regles):
    # User decision of 26/08/2026: life coaching is an exclusion, not a malus.
    assert scorer_titre("Life Coach certifié ICF", regles).categorie == "exclu"
    assert scorer_titre("Coach de vie et bien-être", regles).categorie == "exclu"


def test_titre_mixte_life_et_business_est_exclu(regles):
    # POC-014, anomaly A: the ampersand used to split "life" from "coach".
    # Client grid of 11/09/2026: a life coach is a bad profile.
    assert scorer_titre("Certified Life & Business Coach", regles).categorie == "exclu"
    assert scorer_titre("Business and life coach", regles).categorie == "exclu"


def test_coach_en_formation_est_exclu(regles):
    # POC-014: not a practising coach yet.
    resultat = scorer_titre("Chef de projet / Coach professionnel en formation", regles)

    assert resultat.categorie == "exclu"
    assert "exclusion_en_formation" in resultat.justification


def test_formateur_n_est_pas_un_coach_en_formation(regles):
    # "en formation" alone must not exclude: trainers and training consultants
    # are legitimate business coach profiles.
    assert scorer_titre("Coach professionnel, consultant en formation", regles).categorie != "exclu"
    assert scorer_titre("Coach professionnel & Formateur", regles).categorie != "exclu"


# --- règles de score -------------------------------------------------------


def test_marqueur_coach_seul_donne_le_score_de_base(regles):
    resultat = scorer_titre("Coach", regles)

    assert resultat.score == 20
    assert "base_coach +20" in resultat.justification


def test_focus_business_ajoute_quarante_points(regles):
    # base_coach (+20) + focus_business (+40), aucune certification ni cible.
    assert scorer_titre("Coach professionnel", regles).score == 60


def test_coach_professionnel_sans_autre_signal_atteint_le_seuil(regles):
    # POC-014 invariant: base_coach + focus_business alone reach the threshold.
    # That is what keeps every good profile of the 11/09/2026 batch selected.
    assert scorer_titre("Coach professionnel", regles).score >= regles.seuil_profil_interessant


def test_certification_ajoute_cinq_points(regles):
    # base_coach (+20) + certification (+5) : la grille client n'en parle pas.
    assert scorer_titre("Coach certifié", regles).score == 25


def test_cible_business_ajoute_quinze_points(regles):
    # base_coach (+20) + cible_business (+15) via "entrepreneur", sans
    # déclencher focus_business (aucune formule "coach professionnel/business").
    assert scorer_titre("Coach pour entrepreneurs", regles).score == 35


def test_nom_d_ecole_executive_ne_declenche_pas_la_cible_business(regles):
    # "executive" used to match the name of a coaching school by substring.
    resultat = scorer_titre("Coach professionnel certifié par Ecole Executive", regles)

    assert "cible_business" not in resultat.justification


def test_profil_dirigeant_ajoute_vingt_points(regles):
    # Client grid: "ancien dirigeant" defines the excellent profile.
    resultat = scorer_titre("Coach professionnel, ancien directeur d'usine", regles)

    assert resultat.score == 80  # 20 + 40 + 20
    assert "profil_dirigeant +20" in resultat.justification


def test_autre_pratique_est_un_malus_leger_sans_exclusion(regles):
    # Client grid: "multicarte" is a bad profile, but the title alone cannot
    # tell, so the profile is ranked lower rather than dropped.
    resultat = scorer_titre("Coach professionnel et hypnothérapeute", regles)

    assert resultat.categorie != "exclu"
    assert resultat.score == 50  # 20 + 40 - 10
    assert "autre_pratique -10" in resultat.justification


def test_malus_hors_cible_sans_exclusion(regles):
    resultat = scorer_titre("Coach en développement personnel et scolaire", regles)

    assert resultat.categorie != "exclu"
    assert resultat.score == 0  # 20 - 25, borné à score_min
    assert "hors_cible -25" in resultat.justification


def test_regle_appliquee_une_seule_fois_malgre_plusieurs_mots_cles(regles):
    # "dirigeant" et "entreprise" appartiennent tous deux à cible_business :
    # la règle ne doit compter qu'une fois (+15, pas +30).
    resultat = scorer_titre("Coach de dirigeants en entreprise", regles)

    assert resultat.score == 95  # 20 + 40 (coach de dirigeant) + 15 + 20 (profil_dirigeant)
    assert resultat.justification.count("cible_business") == 1


def test_score_borne_entre_min_et_max(regles):
    titre_charge = (
        "Coach business, coach professionnel certifié ICF RNCP Level 2 PCC, "
        "coach de dirigeants et d'équipe en entreprise, leadership et management"
    )
    resultat = scorer_titre(titre_charge, regles)

    assert regles.score_min <= resultat.score <= regles.score_max


def test_justification_liste_les_regles_ayant_matche(regles):
    resultat = scorer_titre("Coach professionnel certifié ICF pour dirigeants", regles)

    assert "base_coach" in resultat.justification
    assert "focus_business" in resultat.justification
    assert "certification" in resultat.justification
    assert "cible_business" in resultat.justification


# --- catégories ------------------------------------------------------------


@pytest.mark.parametrize(
    "titre",
    [
        "Coach nature en Bretagne",
        "Le coach qui marche",
        "Coach outdoor certifié",
        "Coach hors-les-murs",
        "Coaching en itinérance",
    ],
)
def test_mots_cles_outdoor_donnent_la_categorie_outdoor(titre, regles):
    assert scorer_titre(titre, regles).categorie == "coach_outdoor"


def test_categorie_par_defaut_est_indifferenciee(regles):
    # Beginner/experienced is out of scope: everything else falls back here.
    assert scorer_titre("Coach professionnel certifié", regles).categorie == (
        "coach_business_indifferencie"
    )


# --- scorer_profils / sélection --------------------------------------------


def test_scorer_profils_ajoute_les_quatre_colonnes(regles):
    profils = [{"nom": "Marie Dupont", "titre": "Coach business certifiée ICF"}]

    resultat = scorer_profils(profils, regles)[0]

    assert resultat["nom"] == "Marie Dupont"
    assert resultat["categorie"] == "coach_business_indifferencie"
    assert int(resultat["score"]) > 0
    assert resultat["justification"] != ""
    assert resultat["commentaire_client"] == ""


def test_scorer_profils_ne_perd_pas_un_commentaire_client_existant(regles):
    profils = [{"nom": "Marie Dupont", "titre": "Coach business", "commentaire_client": "OK"}]

    assert scorer_profils(profils, regles)[0]["commentaire_client"] == "OK"


def test_selection_filtre_sur_le_seuil_et_ecarte_les_exclus(regles):
    profils_scores = [
        {"nom": "A", "categorie": "coach_business_indifferencie", "score": "85"},
        {"nom": "B", "categorie": "coach_business_indifferencie", "score": "60"},
        {"nom": "C", "categorie": "coach_business_indifferencie", "score": "20"},
        {"nom": "D", "categorie": "exclu", "score": "0"},
    ]

    par_defaut = selectionner_profils_interessants(profils_scores, regles=regles)
    seuil_haut = selectionner_profils_interessants(profils_scores, seuil=80, regles=regles)

    assert [p["nom"] for p in par_defaut] == ["A", "B"]  # seuil par défaut = 60
    assert [p["nom"] for p in seuil_haut] == ["A"]


# --- chargement / sauvegarde des règles ------------------------------------


def test_regles_chargees_depuis_le_json_par_defaut(regles):
    assert regles.seuil_profil_interessant == 60
    assert {r.id for r in regles.regles} == {
        "exclusion_non_coach",
        "exclusion_hors_metier",
        "exclusion_en_formation",
        "base_coach",
        "focus_business",
        "certification",
        "cible_business",
        "profil_dirigeant",
        "hors_cible",
        "autre_pratique",
    }


def test_agregation_declaree_dans_le_json(regles):
    assert regles.agregation.mode == "somme"
    assert regles.agregation.regle_appliquee_une_seule_fois is True
    assert regles.agregation.commentaire != ""


def test_mode_agregation_inconnu_est_refuse_au_chargement(regles, tmp_path):
    chemin = tmp_path / "regles.json"
    sauvegarder_regles(regles, chemin)
    contenu = json.loads(chemin.read_text(encoding="utf-8"))
    contenu["agregation"]["mode"] = "moyenne"
    chemin.write_text(json.dumps(contenu, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ValueError, match="agregation"):
        charger_regles(chemin)


def test_poids_compte_par_mot_cle_si_regle_non_limitee_a_une_fois(regles, tmp_path):
    # Bascule documentée dans le JSON : le poids est alors compté une fois par
    # mot-clé trouvé au lieu d'une fois par règle.
    chemin = tmp_path / "regles.json"
    sauvegarder_regles(regles, chemin)
    contenu = json.loads(chemin.read_text(encoding="utf-8"))
    contenu["agregation"]["regle_appliquee_une_seule_fois"] = False
    chemin.write_text(json.dumps(contenu, ensure_ascii=False), encoding="utf-8")
    regles_cumulatives = charger_regles(chemin)

    titre = "Coach pour entrepreneurs et managers"

    assert scorer_titre(titre, regles).score == 35  # 20 + 15 (règle une fois)
    assert scorer_titre(titre, regles_cumulatives).score == 50  # 20 + 15 + 15


def test_sauvegarder_puis_recharger_conserve_les_regles(regles, tmp_path):
    # Round-trip needed by the future configuration menu (edit then save).
    chemin = tmp_path / "regles.json"

    sauvegarder_regles(regles, chemin)

    assert charger_regles(chemin) == regles


# --- critère d'acceptation sur les titres réels du lot de 25 ---------------
# Titres réels du CSV client (mail du 08/07/2026). Le nom est conservé ici
# parce que le critère d'acceptation porte nommément sur ces deux profils.

TITRE_CECILE_POLLIN = "HR Senior Manager - Responsable RH Senior - Transformation"
TITRE_ANNE_LAURE = (
    "Coach en développement personnel, professionnel et scolaire  certifiée par "
    "Coaching Ways France Level 2 ICF  (RNCP niveau 6)"
)
TITRES_VALIDES_PAR_LE_CLIENT = [
    "Coach Professionnel certifié par Coaching Ways (France) · Accrédité Level 2 par ICF",
    "Coach Professionnel certifié RNCP  (Coaching Ways) // Coach d'équipe",
    "Coach Business Certifiée Level 2 ICF Fondatrice | POINT.ZERO France · International",
    "Coach Professionnel & Manager. Coach professionnel certifié ICF & RNCP Niveau 6",
    "Coach professionnel certifié par Coaching Ways France accrédité Level 2 ICF",
    "Coach professionnel certifiée & Accréditée EIA - Formatrice Accréditée PSSM France",
    "Coach professionnel certifié Coaching Ways France",
    "Coach d’intégration professionnelle en France | Français professionnel & communication",
    "Coach d’entreprise - AUTODOC PRO FRANCE",
    "Directeur dans le monde industriel | Coach professionnel certifié ICF Level 2",
    "Co-Dirigeant de TREMPLIN France & Coach Professionnel ICF   Engagée par nature",
    "Senior Business Advisor |, Business Unit Management, Coach professionnel",
    "Coach professionnel certifié | ex-Dir. marketing CoachingWays France",
    "Formateur Coach Commercial Réseau France chez Stellantis | Coaching Professionnel",
    "Coach Professionnel Level 2 accrédité ICF par Coaching Ways France-Certifiée CCTI®",
    "International Business Coach, Trainer & Consultant ICF PCC",
    "Directeur associé de Coachingways France - formation de coach-professionnel",
    "Executive Coach (HEC) | Transformation & performance | Fondateur HPES France",
    "Coach Professionnelle, Equicoach - Consultante & Formatrice - ex DRH",
    "Personnel Navigant Commercial (PNC) - 25 ans Air France | Coach certifié RNCP 7",
    "Coach professionnelle certifié par COACHING WAYS FRANCE / COACHING WAYS EXECUTIVE",
]
# Validated in bulk on 08/07/2026, then judged "mauvais profil" one by one by
# the client on 11/09/2026: the later, individual verdict prevails (POC-014).
TITRES_EN_FORMATION_REJUGES_LE_11_09 = [
    "Product Data & Certification Manager / Coach professionnel en formation / MERSEN",
    "Coach professionnel en formation chez Coaching Ways France",
]


def test_acceptation_cecile_pollin_est_exclue(regles):
    """Faux positif de la recherche booléenne : pas un coach (client, 04/07/2026)."""
    assert scorer_titre(TITRE_CECILE_POLLIN, regles).categorie == "exclu"


def test_acceptation_les_21_profils_valides_sont_conserves(regles):
    """Le client a validé ces profils en bloc comme de bons coachs business (08/07/2026)."""
    assert len(TITRES_VALIDES_PAR_LE_CLIENT) == 21
    categories = [scorer_titre(t, regles).categorie for t in TITRES_VALIDES_PAR_LE_CLIENT]

    assert "exclu" not in categories


def test_acceptation_les_2_coachs_en_formation_sont_exclus(regles):
    """Jugés « mauvais profil » par le client le 11/09/2026 : ils sortent de la sélection."""
    categories = [scorer_titre(t, regles).categorie for t in TITRES_EN_FORMATION_REJUGES_LE_11_09]

    assert categories == ["exclu", "exclu"]


def test_acceptation_anne_laure_conservee_mais_sous_la_mediane(regles):
    """Acceptable mais moins intéressante (client, 04/07/2026) : conservée, sous la médiane."""
    resultat_anne_laure = scorer_titre(TITRE_ANNE_LAURE, regles)
    scores_conserves = [resultat_anne_laure.score] + [
        scorer_titre(t, regles).score for t in TITRES_VALIDES_PAR_LE_CLIENT
    ]

    assert resultat_anne_laure.categorie != "exclu"
    assert resultat_anne_laure.score < statistics.median(scores_conserves)
