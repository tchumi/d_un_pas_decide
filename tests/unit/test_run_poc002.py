from source.backend.adapters.scraping.run_poc002 import (
    ARRET_BLOCAGE,
    ARRET_VIDES,
    VISITE_BLOQUEE,
    VISITE_ECHEC,
    VISITE_LUE,
    lire_lot,
    page_bloquee,
    profils_du_releve,
    selectionner_reliquat,
)
from source.backend.adapters.storage.profile_store import LECTURE_DEJA_LUE, LECTURE_ECRITE
from source.backend.core.profile_scoring import charger_regles


def _profil(url, score, categorie="coach_business_indifferencie", date_visite_email=""):
    return {
        "url": url,
        "score": str(score),
        "categorie": categorie,
        "date_visite_email": date_visite_email,
    }


def test_reliquat_ecarte_les_profils_sous_le_seuil():
    regles = charger_regles()
    seuil = regles.seuil_profil_interessant
    profils = [_profil("a", seuil), _profil("b", seuil - 1)]

    assert [p["url"] for p in selectionner_reliquat(profils, regles)] == ["a"]


def test_reliquat_ecarte_les_profils_exclus_meme_bien_notes():
    regles = charger_regles()
    profils = [_profil("a", 100, categorie=regles.categorie_exclusion)]

    assert selectionner_reliquat(profils, regles) == []


def test_reliquat_ecarte_les_profils_deja_visites():
    regles = charger_regles()
    profils = [_profil("a", 100, date_visite_email="2026-08-28"), _profil("b", 100)]

    assert [p["url"] for p in selectionner_reliquat(profils, regles)] == ["b"]


def test_releve_ne_retient_que_des_profils_du_magasin():
    magasin = [_profil("https://www.linkedin.com/in/a", 60)]
    urls = ["https://www.linkedin.com/in/a?miniProfile=x", "https://www.linkedin.com/in/z"]

    trouves, inconnues = profils_du_releve(urls, magasin)

    assert [p["url"] for p in trouves] == ["https://www.linkedin.com/in/a"]
    assert inconnues == ["https://www.linkedin.com/in/z"]


def test_page_bloquee_reconnait_cloudflare_et_les_redirections_de_securite():
    profil = "https://www.linkedin.com/in/a/"

    assert page_bloquee(profil, "Attention Required! | Cloudflare")
    assert page_bloquee("https://www.linkedin.com/checkpoint/challenge/x", "LinkedIn")
    assert page_bloquee("https://www.linkedin.com/authwall?x=1", "LinkedIn")
    assert not page_bloquee(profil, "Prénom Nom | LinkedIn")


# --- POC-016 step 7: reading run loop ----------------------------------------


def _lot(*urls):
    return [{"url": u, "nom": u} for u in urls]


def _lecteur(resultats):
    """lire_profil stub: url -> (etat, contenu), recording the visits."""
    visites = []

    def lire_profil(profil):
        visites.append(profil["url"])
        return resultats[profil["url"]]

    return lire_profil, visites


def _ecrivain(statut=LECTURE_ECRITE):
    ecrits = []

    def ecrire(url, experience, infos):
        ecrits.append((url, experience, infos))
        return statut

    return ecrire, ecrits


def _lu(experience="Coach depuis 2015", infos=""):
    return VISITE_LUE, {"experience": experience, "infos": infos}


def test_lecture_ecrit_chaque_profil_lu():
    lire, _ = _lecteur({"a": _lu("Exp a", "Infos a"), "b": _lu("Exp b")})
    ecrire, ecrits = _ecrivain()

    bilan = lire_lot(_lot("a", "b"), lire, ecrire)

    assert ecrits == [("a", "Exp a", "Infos a"), ("b", "Exp b", "")]
    assert bilan.lus == [("a", 5, 7), ("b", 5, 0)]
    assert bilan.arret == ""


def test_blocage_arrete_le_run_et_garde_les_profils_deja_lus():
    lire, visites = _lecteur(
        {"a": _lu(), "b": _lu(), "c": (VISITE_BLOQUEE, "Cloudflare"), "d": _lu()}
    )
    ecrire, ecrits = _ecrivain()

    bilan = lire_lot(_lot("a", "b", "c", "d"), lire, ecrire)

    assert [e[0] for e in ecrits] == ["a", "b"]
    assert visites == ["a", "b", "c"]
    assert (bilan.arret, bilan.detail_arret, bilan.non_traites) == (ARRET_BLOCAGE, "Cloudflare", 2)


def test_page_non_chargee_n_est_pas_marquee_et_le_run_continue():
    lire, _ = _lecteur({"a": (VISITE_ECHEC, None), "b": _lu()})
    ecrire, ecrits = _ecrivain()

    bilan = lire_lot(_lot("a", "b"), lire, ecrire)

    assert [e[0] for e in ecrits] == ["b"]
    assert bilan.echecs == ["a"]


def test_profil_vide_est_ecrit_pour_poser_la_date():
    lire, _ = _lecteur({"a": _lu("", ""), "b": _lu()})
    ecrire, ecrits = _ecrivain()

    bilan = lire_lot(_lot("a", "b"), lire, ecrire)

    assert ecrits[0] == ("a", "", "")
    assert bilan.vides == ["a"]
    assert bilan.arret == ""


def test_profils_vides_consecutifs_arretent_le_run():
    # Several empty profiles in a row more likely mean broken selectors.
    lire, visites = _lecteur({"a": _lu(), "b": _lu("", ""), "c": _lu("  ", ""), "d": _lu()})
    ecrire, ecrits = _ecrivain()

    bilan = lire_lot(_lot("a", "b", "c", "d"), lire, ecrire)

    assert [e[0] for e in ecrits] == ["a", "b", "c"]
    assert visites == ["a", "b", "c"]
    assert (bilan.arret, bilan.vides, bilan.non_traites) == (ARRET_VIDES, ["b", "c"], 1)


def test_un_profil_lu_remet_le_compteur_de_vides_a_zero():
    lire, _ = _lecteur({"a": _lu("", ""), "b": _lu(), "c": _lu("", ""), "d": _lu()})
    ecrire, _ = _ecrivain()

    bilan = lire_lot(_lot("a", "b", "c", "d"), lire, ecrire)

    assert bilan.arret == ""
    assert len(bilan.lus) == 4


def test_un_refus_du_magasin_est_signale_et_non_compte_comme_lu():
    lire, _ = _lecteur({"a": _lu()})
    ecrire, _ = _ecrivain(statut=LECTURE_DEJA_LUE)

    bilan = lire_lot(_lot("a"), lire, ecrire)

    assert bilan.lus == []
    assert bilan.refus == [("a", LECTURE_DEJA_LUE)]
