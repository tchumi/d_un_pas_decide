from source.backend.adapters.scraping.run_poc002 import selectionner_reliquat
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
