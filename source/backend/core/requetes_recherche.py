"""Search queries described in configuration (POC-008).

The queries run by the LinkedIn search live in config/requetes_recherche.json,
like the scoring rules: adding one must not require touching the code. The
file is validated on load - a missing or malformed file raises an explicit
ConfigRequetesInvalide instead of failing later, mid-run, with a browser open.

No Streamlit import, no Playwright import: pure loading and validation.
"""

import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_REQUETES_PATH = (
    Path(__file__).resolve().parents[3] / "config" / "requetes_recherche.json"
)


class ConfigRequetesInvalide(ValueError):
    """The query configuration file is missing or malformed."""


@dataclass(frozen=True)
class Lieu:
    """A native LinkedIn location facet: a slicing device, not a selection criterion."""

    libelle: str
    geo_urn: str


@dataclass(frozen=True)
class Requete:
    """One configured search query."""

    id: str
    libelle: str
    mots_cles: str
    lieu: Lieu | None = None
    max_pages: int | None = None
    provisoire: bool = False
    active: bool = True

    @property
    def geo_urns(self) -> tuple[str, ...]:
        return (self.lieu.geo_urn,) if self.lieu else ()


@dataclass(frozen=True)
class ConfigRequetes:
    """The whole query file: the queries plus the run-level profile ceiling."""

    requetes: tuple[Requete, ...]
    max_profils_par_run: int
    version: int = 1
    commentaire: str = ""

    def actives(self) -> tuple[Requete, ...]:
        return tuple(r for r in self.requetes if r.active)


def _texte_obligatoire(brut: dict, champ: str, contexte: str) -> str:
    valeur = brut.get(champ)
    if not isinstance(valeur, str) or not valeur.strip():
        raise ConfigRequetesInvalide(f"{contexte} : champ '{champ}' absent ou vide.")
    return valeur.strip()


def _entier_positif(valeur: object, champ: str, contexte: str) -> int:
    # bool is a subclass of int: reject it explicitly, "true" is not a ceiling.
    if isinstance(valeur, bool) or not isinstance(valeur, int) or valeur <= 0:
        raise ConfigRequetesInvalide(
            f"{contexte} : '{champ}' doit etre un entier strictement positif "
            f"(recu : {valeur!r})."
        )
    return valeur


def _booleen(brut: dict, champ: str, defaut: bool, contexte: str) -> bool:
    valeur = brut.get(champ, defaut)
    if not isinstance(valeur, bool):
        raise ConfigRequetesInvalide(
            f"{contexte} : '{champ}' doit valoir true ou false (recu : {valeur!r})."
        )
    return valeur


def _lire_lieu(brut: object, contexte: str) -> Lieu | None:
    if brut is None:
        return None
    if not isinstance(brut, dict):
        raise ConfigRequetesInvalide(f"{contexte} : 'lieu' doit etre un objet.")
    libelle = _texte_obligatoire(brut, "libelle", f"{contexte}, lieu")
    geo_urn = _texte_obligatoire(brut, "geo_urn", f"{contexte}, lieu")
    if not geo_urn.isdigit():
        raise ConfigRequetesInvalide(
            f"{contexte}, lieu : 'geo_urn' doit etre l'identifiant numerique de la "
            f"facette LinkedIn (recu : {geo_urn!r})."
        )
    return Lieu(libelle=libelle, geo_urn=geo_urn)


def _lire_requete(brut: object, rang: int) -> Requete:
    contexte = f"Requete n°{rang}"
    if not isinstance(brut, dict):
        raise ConfigRequetesInvalide(f"{contexte} : un objet est attendu.")
    identifiant = _texte_obligatoire(brut, "id", contexte)
    contexte = f"Requete '{identifiant}'"
    max_pages = brut.get("max_pages")
    return Requete(
        id=identifiant,
        libelle=_texte_obligatoire(brut, "libelle", contexte),
        mots_cles=_texte_obligatoire(brut, "mots_cles", contexte),
        lieu=_lire_lieu(brut.get("lieu"), contexte),
        max_pages=(
            None if max_pages is None else _entier_positif(max_pages, "max_pages", contexte)
        ),
        provisoire=_booleen(brut, "provisoire", False, contexte),
        active=_booleen(brut, "active", True, contexte),
    )


def charger_requetes(chemin: Path | None = None) -> ConfigRequetes:
    """Load and validate the query file, raising ConfigRequetesInvalide on any defect."""
    chemin = chemin or DEFAULT_REQUETES_PATH
    try:
        with open(chemin, encoding="utf-8") as f:
            brut = json.load(f)
    except FileNotFoundError as erreur:
        raise ConfigRequetesInvalide(
            f"Fichier de requetes introuvable : {chemin}"
        ) from erreur
    except json.JSONDecodeError as erreur:
        raise ConfigRequetesInvalide(
            f"Fichier de requetes malforme ({chemin}) : {erreur}"
        ) from erreur

    if not isinstance(brut, dict):
        raise ConfigRequetesInvalide(f"{chemin} : un objet JSON est attendu a la racine.")

    brutes = brut.get("requetes")
    if not isinstance(brutes, list) or not brutes:
        raise ConfigRequetesInvalide(f"{chemin} : 'requetes' doit etre une liste non vide.")

    requetes = tuple(_lire_requete(r, rang) for rang, r in enumerate(brutes, start=1))

    vus: set[str] = set()
    for requete in requetes:
        if requete.id in vus:
            raise ConfigRequetesInvalide(
                f"Identifiant de requete en double : '{requete.id}'. Il sert a tracer "
                f"l'origine d'un profil, il doit etre unique."
            )
        vus.add(requete.id)

    if not any(r.active for r in requetes):
        raise ConfigRequetesInvalide(f"{chemin} : aucune requete active.")

    return ConfigRequetes(
        requetes=requetes,
        max_profils_par_run=_entier_positif(
            brut.get("max_profils_par_run"), "max_profils_par_run", str(chemin)
        ),
        version=int(brut.get("version", 1)),
        commentaire=str(brut.get("commentaire", "")),
    )
