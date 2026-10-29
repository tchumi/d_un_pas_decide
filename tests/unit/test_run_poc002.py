from source.backend.adapters.scraping.run_poc002 import profils_du_releve, selectionner_reliquat
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
