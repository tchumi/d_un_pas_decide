from source.backend.adapters.scraping.profile_search import (
    RAISON_GISEMENT_EPUISE,
    ResultatRecherche,
    ResultatRequete,
)
from source.backend.adapters.scraping.run_poc001 import lignes_journal
from source.backend.adapters.storage.journal_collecte import (
    JOURNAL_FIELDS,
    journaliser_collecte,
    lire_journal,
)
from source.backend.core.requetes_recherche import Requete


def ligne(slug, requete_id="r1"):
    return {
        "date_collecte": "2026-10-06",
        "url": f"https://www.linkedin.com/in/{slug}",
        "requete_id": requete_id,
        "requete_libelle": f"Requete {requete_id}",
    }


def test_journal_absent_se_lit_comme_vide(tmp_path):
    assert lire_journal(tmp_path / "journal.csv") == []


def test_premier_ajout_ecrit_l_en_tete_et_les_lignes(tmp_path):
    chemin = tmp_path / "journal.csv"

    ecrites = journaliser_collecte([ligne("marie"), ligne("jean")], chemin)

    assert ecrites == 2
    assert chemin.read_text(encoding="utf-8").splitlines()[0] == ",".join(JOURNAL_FIELDS)
    assert lire_journal(chemin) == [ligne("marie"), ligne("jean")]


def test_un_second_run_ajoute_sans_ecraser_ni_repeter_l_en_tete(tmp_path):
    chemin = tmp_path / "journal.csv"
    journaliser_collecte([ligne("marie")], chemin)

    journaliser_collecte([ligne("lea", "r2")], chemin)

    assert lire_journal(chemin) == [ligne("marie"), ligne("lea", "r2")]
    assert len(chemin.read_text(encoding="utf-8").splitlines()) == 3


def test_aucune_ligne_ne_cree_pas_de_fichier(tmp_path):
    chemin = tmp_path / "journal.csv"

    assert journaliser_collecte([], chemin) == 0
    assert not chemin.exists()


def bilan(identifiant, *slugs):
    requete = Requete(id=identifiant, libelle=f"Requete {identifiant}", mots_cles="coach")
    profils = [{"nom": s, "url": f"https://www.linkedin.com/in/{s}?trk=x"} for s in slugs]
    return ResultatRequete(requete, ResultatRecherche(profils, RAISON_GISEMENT_EPUISE, 1), 10)


def test_lignes_journal_rattache_chaque_profil_ajoute_a_sa_requete():
    bilans = [bilan("r1", "marie"), bilan("r2", "lea")]
    ajoutees = ["https://www.linkedin.com/in/marie", "https://www.linkedin.com/in/lea"]

    assert lignes_journal(bilans, ajoutees, "2026-10-06") == [ligne("marie"), ligne("lea", "r2")]


def test_lignes_journal_ignore_un_profil_que_le_magasin_n_a_pas_ajoute():
    bilans = [bilan("r1", "marie", "jean")]

    lignes = lignes_journal(bilans, ["https://www.linkedin.com/in/jean"], "2026-10-06")

    assert [ligne["url"] for ligne in lignes] == ["https://www.linkedin.com/in/jean"]
