import csv
import sqlite3

import pytest

from source.backend.adapters.storage.csv_export import (
    PROFILE_CSV_FIELDS,
    export_profiles_to_csv,
)
from source.backend.adapters.storage.profile_store import (
    PROFILE_COLUMNS,
    SCHEMA_VERSION,
    STATUT_CANDIDAT,
    STATUT_REJETE,
    STATUT_VALIDE,
    enregistrer_coordonnees_web,
    enregistrer_email_linkedin,
    enregistrer_profils,
    importer_commentaires_csv,
    lister_profils,
    marquer_ne_plus_traiter,
    mettre_a_jour_scoring,
    migrer_schema,
    ouvrir_magasin,
    profils_a_enrichir,
    profils_a_visiter,
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


# --- POC-009 : migration de schema, marqueurs de reliquat, statut de validation ---

# The store exactly as POC-006 left it: 13 columns, PRAGMA user_version = 1.
# Written out in full on purpose - a migration test that builds its "before"
# state from the current code tests nothing.
_SCHEMA_V1 = """
CREATE TABLE profils (
    url                TEXT PRIMARY KEY,
    nom                TEXT NOT NULL DEFAULT '',
    localisation       TEXT NOT NULL DEFAULT '',
    titre              TEXT NOT NULL DEFAULT '',
    email              TEXT NOT NULL DEFAULT '',
    email_web          TEXT NOT NULL DEFAULT '',
    site_web           TEXT NOT NULL DEFAULT '',
    categorie          TEXT NOT NULL DEFAULT '',
    score              TEXT NOT NULL DEFAULT '',
    justification      TEXT NOT NULL DEFAULT '',
    commentaire_client TEXT NOT NULL DEFAULT '',
    date_collecte      TEXT NOT NULL,
    ne_plus_traiter    INTEGER NOT NULL DEFAULT 0
);
"""


def creer_magasin_v1(chemin):
    """Build a pre-POC-009 store holding one fully filled profile."""
    connexion = sqlite3.connect(chemin)
    connexion.executescript(_SCHEMA_V1)
    connexion.execute("PRAGMA user_version = 1")
    connexion.execute(
        "INSERT INTO profils (url, nom, titre, score, commentaire_client, date_collecte) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (URL_MARIE, "Marie Dupont", "Coach business", "75", "retour client", "2026-07-03"),
    )
    connexion.commit()
    connexion.close()
    return chemin


def test_migration_ajoute_les_colonnes_poc009_a_un_magasin_v1(tmp_path):
    chemin = creer_magasin_v1(tmp_path / "profils.db")

    connexion = ouvrir_magasin(chemin)
    try:
        colonnes = {row["name"] for row in connexion.execute("PRAGMA table_info(profils)")}
        assert {
            "date_visite_email",
            "date_enrichissement_web",
            "statut_coordonnees",
        } <= colonnes
        assert connexion.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    finally:
        connexion.close()


def test_migration_ne_touche_a_aucune_donnee_existante(tmp_path):
    chemin = creer_magasin_v1(tmp_path / "profils.db")

    connexion = ouvrir_magasin(chemin)
    try:
        stocke = lister_profils(connexion)[0]
    finally:
        connexion.close()

    assert stocke["nom"] == "Marie Dupont"
    assert stocke["score"] == "75"
    assert stocke["commentaire_client"] == "retour client"
    assert stocke["date_collecte"] == "2026-07-03"
    # On the rows already there, "empty" reads as "never attempted" - which is
    # exactly true, and is the whole point of the new columns.
    assert stocke["date_visite_email"] == ""
    assert stocke["date_enrichissement_web"] == ""
    assert stocke["statut_coordonnees"] == ""


def test_migration_signale_les_colonnes_ajoutees_puis_est_idempotente(tmp_path):
    chemin = creer_magasin_v1(tmp_path / "profils.db")
    connexion = sqlite3.connect(chemin)
    connexion.row_factory = sqlite3.Row

    try:
        assert migrer_schema(connexion) == [
            "date_visite_email",
            "date_enrichissement_web",
            "statut_coordonnees",
        ]
        # Re-running must be a no-op, not a duplicate-column error.
        assert migrer_schema(connexion) == []
    finally:
        connexion.close()


def test_magasin_neuf_est_deja_en_derniere_version(conn):
    assert conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    assert migrer_schema(conn) == []


def test_visite_sans_email_marque_quand_meme_le_profil(conn):
    enregistrer_profils(conn, [profil()])

    rapport = enregistrer_email_linkedin(
        conn, [{"url": URL_MARIE, "email": ""}], date_visite="2026-08-28"
    )

    stocke = lister_profils(conn)[0]
    assert stocke["email"] == ""
    assert stocke["date_visite_email"] == "2026-08-28"
    assert rapport.profils_traites == [URL_MARIE]
    assert rapport.coordonnees_trouvees == []
    # Marking a fruitless visit is what makes the backlog shrink: before
    # POC-009 an empty email meant "not visited" and "no public email" alike.
    assert profils_a_visiter(lister_profils(conn)) == []


def test_visite_avec_email_ecrit_l_email_sans_statut_de_validation(conn):
    enregistrer_profils(conn, [profil()])

    enregistrer_email_linkedin(
        conn, [{"url": URL_MARIE, "email": "marie@example.com"}], date_visite="2026-08-28"
    )

    stocke = lister_profils(conn)[0]
    assert stocke["email"] == "marie@example.com"
    assert stocke["date_visite_email"] == "2026-08-28"
    # The person published that address on their own profile: it is a fact,
    # not a candidate awaiting review.
    assert stocke["statut_coordonnees"] == ""


def test_enrichissement_web_enregistre_une_trouvaille_comme_candidate(conn):
    enregistrer_profils(conn, [profil()])

    rapport = enregistrer_coordonnees_web(
        conn,
        [{"url": URL_MARIE, "email_web": "marie@mycoach.fr", "site_web": "mycoach.fr"}],
        date_enrichissement="2026-08-28",
    )

    stocke = lister_profils(conn)[0]
    assert stocke["email_web"] == "marie@mycoach.fr"
    assert stocke["site_web"] == "mycoach.fr"
    # Never valide: the measured relevance rate is 1 true positive out of 25.
    assert stocke["statut_coordonnees"] == STATUT_CANDIDAT
    assert stocke["date_enrichissement_web"] == "2026-08-28"
    assert rapport.coordonnees_trouvees == [URL_MARIE]


def test_enrichissement_sans_resultat_marque_sans_donner_de_statut(conn):
    enregistrer_profils(conn, [profil()])

    enregistrer_coordonnees_web(
        conn,
        [{"url": URL_MARIE, "email_web": "", "site_web": ""}],
        date_enrichissement="2026-08-28",
    )

    stocke = lister_profils(conn)[0]
    assert stocke["statut_coordonnees"] == ""
    assert stocke["date_enrichissement_web"] == "2026-08-28"
    # One Brave Search call already spent on this profile: never spend a
    # second one on the same result.
    assert profils_a_enrichir(lister_profils(conn)) == []


def test_un_run_ne_retrograde_jamais_un_statut_tranche_par_un_humain(conn, tmp_path):
    enregistrer_profils(conn, [profil()])
    enregistrer_coordonnees_web(
        conn,
        [{"url": URL_MARIE, "email_web": "vrai@mycoach.fr", "site_web": "mycoach.fr"}],
        date_enrichissement="2026-07-10",
    )
    chemin = ecrire_csv_annote(
        tmp_path / "relu.csv", [{"url": URL_MARIE, "statut_coordonnees": "valide"}]
    )
    importer_commentaires_csv(conn, chemin)

    rapport = enregistrer_coordonnees_web(
        conn,
        [{"url": URL_MARIE, "email_web": "faux@agence.fr", "site_web": "agence.fr"}],
        date_enrichissement="2026-08-28",
    )

    stocke = lister_profils(conn)[0]
    assert stocke["statut_coordonnees"] == STATUT_VALIDE
    assert stocke["email_web"] == "vrai@mycoach.fr"
    assert stocke["site_web"] == "mycoach.fr"
    assert rapport.figes_par_statut == [URL_MARIE]
    # Still stamped, so a reviewed profile leaves the backlog for good.
    assert stocke["date_enrichissement_web"] == "2026-08-28"


def test_un_profil_rejete_n_est_jamais_repropose_par_un_run(conn, tmp_path):
    enregistrer_profils(conn, [profil()])
    enregistrer_coordonnees_web(
        conn, [{"url": URL_MARIE, "email_web": "urgent@lafrenchcom.fr", "site_web": ""}]
    )
    chemin = ecrire_csv_annote(
        tmp_path / "relu.csv", [{"url": URL_MARIE, "statut_coordonnees": "rejete"}]
    )
    importer_commentaires_csv(conn, chemin)

    enregistrer_coordonnees_web(
        conn, [{"url": URL_MARIE, "email_web": "urgent@lafrenchcom.fr", "site_web": ""}]
    )

    assert lister_profils(conn)[0]["statut_coordonnees"] == STATUT_REJETE


def test_valeur_entrante_vide_ne_blanchit_pas_une_coordonnee_stockee(conn):
    enregistrer_profils(conn, [profil()])
    enregistrer_coordonnees_web(
        conn, [{"url": URL_MARIE, "email_web": "marie@mycoach.fr", "site_web": "mycoach.fr"}]
    )

    enregistrer_coordonnees_web(conn, [{"url": URL_MARIE, "email_web": "", "site_web": ""}])

    stocke = lister_profils(conn)[0]
    assert stocke["email_web"] == "marie@mycoach.fr"
    assert stocke["site_web"] == "mycoach.fr"


def test_une_valeur_remplacee_est_signalee_et_jamais_silencieuse(conn):
    enregistrer_profils(conn, [profil()])
    enregistrer_email_linkedin(conn, [{"url": URL_MARIE, "email": "ancien@example.com"}])

    rapport = enregistrer_email_linkedin(
        conn, [{"url": URL_MARIE, "email": "nouveau@example.com"}]
    )

    assert rapport.valeurs_remplacees == [
        (URL_MARIE, "email", "ancien@example.com", "nouveau@example.com")
    ]
    assert lister_profils(conn)[0]["email"] == "nouveau@example.com"


def test_une_url_inconnue_n_est_pas_creee_par_une_ecriture_de_coordonnees(conn):
    rapport = enregistrer_email_linkedin(conn, [{"url": URL_JEAN, "email": "jean@example.com"}])

    assert rapport.urls_inconnues == [URL_JEAN]
    assert lister_profils(conn) == []


def test_profils_a_visiter_ne_garde_que_les_profils_jamais_visites():
    # Pure function over listed rows: no database, no browser, no network.
    profils = [
        {"url": URL_MARIE, "date_visite_email": ""},
        {"url": URL_JEAN, "date_visite_email": "2026-08-28"},
    ]

    assert [p["url"] for p in profils_a_visiter(profils)] == [URL_MARIE]


def test_profils_a_enrichir_ne_garde_que_les_profils_jamais_enrichis():
    profils = [
        {"url": URL_MARIE, "date_enrichissement_web": ""},
        {"url": URL_JEAN, "date_enrichissement_web": "2026-08-28"},
    ]

    assert [p["url"] for p in profils_a_enrichir(profils)] == [URL_MARIE]


def test_un_statut_non_reconnu_est_refuse_et_signale(conn, tmp_path):
    enregistrer_profils(conn, [profil()])
    chemin = ecrire_csv_annote(
        tmp_path / "relu.csv", [{"url": URL_MARIE, "statut_coordonnees": "peut-etre"}]
    )

    rapport = importer_commentaires_csv(conn, chemin)

    assert rapport.statuts_refuses == [(URL_MARIE, "peut-etre")]
    assert lister_profils(conn)[0]["statut_coordonnees"] == ""


def test_un_statut_vide_dans_le_csv_ne_leve_pas_une_decision_existante(conn, tmp_path):
    enregistrer_profils(conn, [profil()])
    valide = ecrire_csv_annote(
        tmp_path / "valide.csv", [{"url": URL_MARIE, "statut_coordonnees": "valide"}]
    )
    importer_commentaires_csv(conn, valide)

    vide = ecrire_csv_annote(tmp_path / "vide.csv", [{"url": URL_MARIE}])
    rapport = importer_commentaires_csv(conn, vide)

    assert lister_profils(conn)[0]["statut_coordonnees"] == STATUT_VALIDE
    assert rapport.statuts_tranches == []
