import csv

import pytest

from source.backend.adapters.storage.csv_export import (
    PROFILE_CSV_FIELDS,
    export_profiles_to_csv,
)
from source.backend.adapters.storage.profile_store import (
    PROFILE_COLUMNS,
    enregistrer_profils,
    importer_commentaires_csv,
    lister_profils,
    marquer_ne_plus_traiter,
    mettre_a_jour_scoring,
    ouvrir_magasin,
    urls_connues,
)
from source.backend.core.profile_scoring import charger_regles, scorer_profils

URL_MARIE = "https://www.linkedin.com/in/marie-dupont"
URL_JEAN = "https://www.linkedin.com/in/jean-martin"


@pytest.fixture
def conn(tmp_path):
    connexion = ouvrir_magasin(tmp_path / "profils.db")
    yield connexion
    connexion.close()


def profil(nom="Marie Dupont", url=URL_MARIE, **extra):
    base = {
        "nom": nom,
        "url": url,
        "localisation": "Paris",
        "titre": "Coach business certifiee ICF",
    }
    base.update(extra)
    return base


def lire_csv(chemin):
    with open(chemin, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_colonnes_du_magasin_alignees_sur_l_export_csv():
    # The CSV is a view of the store: a column added on one side without the
    # other would silently drop data at export time.
    assert PROFILE_COLUMNS == PROFILE_CSV_FIELDS


def test_ouvrir_magasin_est_idempotent(tmp_path):
    chemin = tmp_path / "profils.db"

    premiere = ouvrir_magasin(chemin)
    enregistrer_profils(premiere, [profil()])
    premiere.close()

    seconde = ouvrir_magasin(chemin)
    try:
        assert urls_connues(seconde) == {URL_MARIE}
    finally:
        seconde.close()


def test_enregistrer_profils_insere_les_nouveaux(conn):
    resultat = enregistrer_profils(conn, [profil(), profil(nom="Jean Martin", url=URL_JEAN)])

    assert resultat.nouveaux == [URL_MARIE, URL_JEAN]
    assert urls_connues(conn) == {URL_MARIE, URL_JEAN}


def test_enregistrer_profils_ne_duplique_pas_une_url_deja_connue(conn):
    enregistrer_profils(conn, [profil()])

    resultat = enregistrer_profils(conn, [profil()])

    assert resultat.nouveaux == []
    assert resultat.deja_connus == [URL_MARIE]
    assert len(lister_profils(conn)) == 1


def test_enregistrer_profils_normalise_l_url_comme_cle(conn):
    enregistrer_profils(conn, [profil()])

    resultat = enregistrer_profils(conn, [profil(url=f"{URL_MARIE}?miniProfileUrn=abc&trk=x")])

    assert resultat.nouveaux == []
    assert len(lister_profils(conn)) == 1


def test_enregistrer_profils_ignore_une_ligne_sans_url(conn):
    resultat = enregistrer_profils(conn, [profil(url="")])

    assert resultat.sans_url == 1
    assert lister_profils(conn) == []


def test_enregistrer_profils_ne_remplace_jamais_un_champ_rempli_par_du_vide(conn):
    enregistrer_profils(conn, [profil(email="marie@example.com")])

    enregistrer_profils(conn, [profil(email="")])

    assert lister_profils(conn)[0]["email"] == "marie@example.com"


def test_enregistrer_profils_complete_un_champ_reste_vide(conn):
    enregistrer_profils(conn, [profil()])

    enregistrer_profils(conn, [profil(email="marie@example.com")])

    assert lister_profils(conn)[0]["email"] == "marie@example.com"


def test_enregistrer_profils_fige_la_date_de_collecte(conn):
    enregistrer_profils(conn, [profil()], date_collecte="2026-08-01")

    enregistrer_profils(conn, [profil()], date_collecte="2026-08-26")

    assert lister_profils(conn)[0]["date_collecte"] == "2026-08-01"


def test_un_nouveau_run_ne_perd_aucun_profil_deja_collecte(conn):
    enregistrer_profils(conn, [profil()])

    enregistrer_profils(conn, [profil(nom="Jean Martin", url=URL_JEAN)])

    assert {p["url"] for p in lister_profils(conn)} == {URL_MARIE, URL_JEAN}


def test_marquer_ne_plus_traiter_garde_l_url_dans_les_urls_connues(conn):
    # RGPD right to object: the profile stays known so it is never re-extracted.
    enregistrer_profils(conn, [profil()])

    assert marquer_ne_plus_traiter(conn, URL_MARIE) is True
    assert URL_MARIE in urls_connues(conn)


def test_marquer_ne_plus_traiter_exclut_le_profil_de_l_export(conn):
    enregistrer_profils(conn, [profil(), profil(nom="Jean Martin", url=URL_JEAN)])

    marquer_ne_plus_traiter(conn, URL_MARIE)

    assert [p["url"] for p in lister_profils(conn)] == [URL_JEAN]
    assert len(lister_profils(conn, inclure_ne_plus_traiter=True)) == 2


def test_marquer_ne_plus_traiter_signale_une_url_inconnue(conn):
    assert marquer_ne_plus_traiter(conn, URL_MARIE) is False


def test_mettre_a_jour_scoring_ecrit_les_colonnes_de_score(conn):
    enregistrer_profils(conn, [profil()])

    mis_a_jour = mettre_a_jour_scoring(
        conn,
        [{"url": URL_MARIE, "categorie": "coach_business", "score": "85", "justification": "ok"}],
    )

    stocke = lister_profils(conn)[0]
    assert mis_a_jour == 1
    assert (stocke["categorie"], stocke["score"], stocke["justification"]) == (
        "coach_business",
        "85",
        "ok",
    )


def test_mettre_a_jour_scoring_ne_touche_pas_au_commentaire_client(conn):
    enregistrer_profils(conn, [profil(commentaire_client="profil pertinent")])

    mettre_a_jour_scoring(conn, [{"url": URL_MARIE, "categorie": "x", "score": "0"}])

    assert lister_profils(conn)[0]["commentaire_client"] == "profil pertinent"


def ecrire_csv_annote(chemin, lignes):
    """Write a CSV the way the client hands it back to us."""
    export_profiles_to_csv(lignes, chemin)
    return chemin


def test_importer_commentaires_ajoute_le_retour_client(conn, tmp_path):
    enregistrer_profils(conn, [profil()])
    chemin = ecrire_csv_annote(
        tmp_path / "annote.csv", [profil(commentaire_client="tres pertinent")]
    )

    rapport = importer_commentaires_csv(conn, chemin)

    assert rapport.commentaires_ajoutes == [URL_MARIE]
    assert lister_profils(conn)[0]["commentaire_client"] == "tres pertinent"


def test_importer_commentaires_ne_vide_jamais_un_commentaire_stocke(conn, tmp_path):
    enregistrer_profils(conn, [profil(commentaire_client="tres pertinent")])
    chemin = ecrire_csv_annote(tmp_path / "annote.csv", [profil(commentaire_client="")])

    importer_commentaires_csv(conn, chemin)

    assert lister_profils(conn)[0]["commentaire_client"] == "tres pertinent"


def test_importer_commentaires_le_retour_client_prime_et_la_substitution_est_signalee(
    conn, tmp_path
):
    enregistrer_profils(conn, [profil(commentaire_client="ancien avis")])
    chemin = ecrire_csv_annote(tmp_path / "annote.csv", [profil(commentaire_client="nouvel avis")])

    rapport = importer_commentaires_csv(conn, chemin)

    assert rapport.commentaires_remplaces == [(URL_MARIE, "ancien avis", "nouvel avis")]
    assert lister_profils(conn)[0]["commentaire_client"] == "nouvel avis"


def test_importer_commentaires_ne_cree_pas_un_profil_inconnu(conn, tmp_path):
    chemin = ecrire_csv_annote(tmp_path / "annote.csv", [profil(commentaire_client="avis")])

    rapport = importer_commentaires_csv(conn, chemin)

    assert rapport.urls_inconnues == [URL_MARIE]
    assert lister_profils(conn) == []


def test_importer_enregistre_une_opposition_exprimee_dans_le_csv(conn, tmp_path):
    enregistrer_profils(conn, [profil()])
    chemin = ecrire_csv_annote(tmp_path / "annote.csv", [profil(ne_plus_traiter="1")])

    rapport = importer_commentaires_csv(conn, chemin)

    assert rapport.oppositions_ajoutees == [URL_MARIE]
    assert lister_profils(conn) == []
    assert URL_MARIE in urls_connues(conn)


def test_importer_ne_leve_jamais_une_opposition_existante(conn, tmp_path):
    enregistrer_profils(conn, [profil()])
    marquer_ne_plus_traiter(conn, URL_MARIE)
    chemin = ecrire_csv_annote(tmp_path / "annote.csv", [profil(ne_plus_traiter="0")])

    importer_commentaires_csv(conn, chemin)

    assert lister_profils(conn) == []


def test_aller_retour_complet_du_retour_client(conn, tmp_path):
    """Critere d'acceptation 4 : export -> annotation -> re-import -> nouveau scoring.

    C'est exactement ce que POC-003 ne pouvait pas verifier : la protection de
    scorer_profils y etait testee sur un dictionnaire construit a la main, sur
    un chemin de donnees qui n'existait pas.
    """
    regles = charger_regles()
    enregistrer_profils(conn, [profil(), profil(nom="Jean Martin", url=URL_JEAN)])
    export = tmp_path / "profils_scores.csv"

    # 1. Premier run de scoring, exporte pour le client.
    premier = scorer_profils(lister_profils(conn), regles)
    mettre_a_jour_scoring(conn, premier)
    export_profiles_to_csv(premier, export)
    assert all(ligne["commentaire_client"] == "" for ligne in lire_csv(export))

    # 2. Le client annote le CSV et nous le renvoie.
    annote = lire_csv(export)
    for ligne in annote:
        if ligne["url"] == URL_MARIE:
            ligne["commentaire_client"] = "exactement le profil recherche"
    export_profiles_to_csv(annote, export)

    # 3. Re-import du retour client dans le magasin.
    importer_commentaires_csv(conn, export)

    # 4. Nouveau run de scoring complet, puis re-export.
    second = scorer_profils(lister_profils(conn), regles)
    mettre_a_jour_scoring(conn, second)
    export_profiles_to_csv(second, export)

    final = {ligne["url"]: ligne for ligne in lire_csv(export)}
    assert final[URL_MARIE]["commentaire_client"] == "exactement le profil recherche"
    assert final[URL_JEAN]["commentaire_client"] == ""
    assert final[URL_MARIE]["score"] != ""
