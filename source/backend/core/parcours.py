"""Career signals derived from a profile's "Experience" and "About" text — POC-016.

The client judges a profile on its career path (former executive, actually
practising coach or merely certified, several jobs at once), which the title
alone cannot tell (measured 29/10/2026: "multi fonction" is unreadable in the
title). These signals are read from the *structure* of the Experience text -
its date-range lines - rather than from free-text keywords, which fire far too
easily on long text (POC-007 substring trap, "marche" / "marché").

Pure functions over plain text: no Playwright, no Streamlit, testable without
a browser. Whether the raw text or only these signals get stored is decided by
the client (plan_POC-016.md, question 2); nothing here writes anything.
"""

import re
from dataclasses import dataclass, field
from datetime import date

from source.backend.core.profile_scoring import normaliser

# A position's date line: "janv. 2019 - aujourd'hui · 5 ans 10 mois",
# "2015 - 2019 · 4 ans", "Mar 2020 - Present · 4 yrs 7 mos". The start must
# carry a year, the end a year or an "ongoing" word.
_LIGNE_DATES = re.compile(
    r"^(?:[^\d\s]+\.?\s+)?(?P<debut>(?:19|20)\d{2})\s*[-–—]\s*"
    r"(?P<fin>(?:[^\d\s]+\.?\s+)?(?:19|20)\d{2}|aujourd\S*hui|present|now)"
    r"(?:\s*·\s*(?P<duree>.+))?$",
    re.IGNORECASE,
)
_FIN_EN_COURS = re.compile(r"aujourd|present|now", re.IGNORECASE)
_ANNEE = re.compile(r"(?:19|20)\d{2}")

# A position shown with one date and no range ("nov. 2024", survey of
# 30/10/2026). Months are spelled out so that "Promo 2017" is not read as a date.
_LIGNE_DATE_SEULE = re.compile(
    r"^(?:(?:janv|févr|fevr|mars|avr|mai|juin|juil|août|aout|sept?|oct|nov|déc|dec"
    r"|jan|feb|mar|apr|may|jun|jul|aug)\.?\s+)?(?:19|20)\d{2}"
    r"(?:\s*·\s*(?P<duree>.+))?$",
    re.IGNORECASE,
)

# The skills line under a position: "Coaching de vie et 4 compétences de plus".
# Matched on normaliser() output.
_LIGNE_COMPETENCES = re.compile(r"\d+ competences? de plus$|\d+ more skills?$")

# A title that only states a legal status says nothing about the activity:
# whether it is a second job or the coaching itself is in its skills line.
_TITRE_STATUT_SEUL = re.compile(
    r"^(?:auto ?entrepreneure?|micro ?entrepreneure?|freelance|independante?)$"
)

# LinkedIn's "Fonctionnaire" contract type: a fact shown on the page, not a guess
# from a list of public employers.
_MOT_FONCTIONNAIRE = re.compile(r"\bfonctionnaire\b")

_DUREE_ANS = re.compile(r"(\d+)\s*(?:ans?|yrs?|years?)\b", re.IGNORECASE)
_DUREE_MOIS = re.compile(r"(\d+)\s*(?:mois|mos?|months?)\b", re.IGNORECASE)

# "Afficher les 8 expériences" / "Show all 8 experiences": the profile page
# only lists the first positions, the rest sit behind a second page that this
# ticket does not visit (plan_POC-016.md, question 5).
_TOTAL_ANNONCE = re.compile(r"(?:afficher les|show all)\s+(\d+)\s+exp", re.IGNORECASE)

# Matched on normaliser() output, at word starts only: "coach" also catches
# "coaching" and "coachs", never a word merely containing the letters.
_MOT_COACH = re.compile(r"\bcoach")
_MOTS_DIRECTION = re.compile(
    r"\b(?:directeur|directrice|dirigeant|dirigeante|ceo|coo|cfo|dg|pdg|gerant|gerante"
    r"|president|presidente|fondateur|fondatrice|managing director|general manager)\b"
)

# How many lines before a date line may describe its position: the title and
# the "Company · contract type" line.
_FENETRE_POSTE = 2


@dataclass(frozen=True)
class Poste:
    """One position read off the Experience text."""

    libelle: str
    en_cours: bool
    duree_mois: int
    coach: bool
    direction: bool
    fonctionnaire: bool = False


@dataclass(frozen=True)
class SignauxParcours:
    """What the Experience and About text says about a career, as signals.

    nb_postes counts the positions read on the page; total_annonce is the
    count LinkedIn announces when the list is truncated (0 when it is not, or
    when the Experience section was not read at all).
    """

    nb_postes: int = 0
    nb_postes_en_cours: int = 0
    coach_en_cours: bool = False
    anciennete_coach_mois: int = 0
    autre_poste_en_cours: bool = False
    ancien_dirigeant: bool = False
    fonction_publique: bool = False
    total_annonce: int = 0
    longueur_infos: int = 0
    postes: tuple[Poste, ...] = field(default=(), repr=False)


def lignes_utiles(texte: str) -> list[str]:
    """Non-empty stripped lines, consecutive duplicates removed.

    LinkedIn renders most texts twice (a visible copy and a screen-reader
    copy), which inner_text returns as two identical lines in a row.
    """
    lignes: list[str] = []
    for brute in (texte or "").splitlines():
        ligne = brute.strip()
        if ligne and (not lignes or lignes[-1] != ligne):
            lignes.append(ligne)
    return lignes


def duree_en_mois(duree: str) -> int:
    """'5 ans 10 mois' -> 70, '1 yr' -> 12, '' -> 0."""
    ans = _DUREE_ANS.search(duree or "")
    mois = _DUREE_MOIS.search(duree or "")
    return (int(ans.group(1)) * 12 if ans else 0) + (int(mois.group(1)) if mois else 0)


def _est_ligne_de_dates(ligne: str) -> bool:
    return bool(_LIGNE_DATES.match(ligne) or _LIGNE_DATE_SEULE.match(ligne))


def _duree_du_poste(dates: re.Match[str], annee_courante: int) -> int:
    """Stated duration, or one worked out from the years when none is shown.

    LinkedIn shows no duration on year-only dates ("1995 – 2012", survey of
    30/10/2026): reading those as 0 months would call a long career brand new.
    """
    if dates.group("duree"):
        return duree_en_mois(dates.group("duree"))
    fin = _ANNEE.search(dates.group("fin"))
    annee_fin = int(fin.group()) if fin else annee_courante
    return max(0, annee_fin - int(dates.group("debut"))) * 12


def lire_postes(texte_experience: str, annee_courante: int | None = None) -> list[Poste]:
    """Positions found in the Experience text, one per date line."""
    annee_courante = annee_courante or date.today().year
    lignes = lignes_utiles(texte_experience)
    rangs_dates = [i for i, ligne in enumerate(lignes) if _est_ligne_de_dates(ligne)]
    postes: list[Poste] = []
    for rang, i in enumerate(rangs_dates):
        dates = _LIGNE_DATES.match(lignes[i])
        fenetre = lignes[max(0, i - _FENETRE_POSTE) : i]
        # Never reach back past the previous position's date line, nor take the
        # previous position's skills for this one's description.
        while fenetre and _est_ligne_de_dates(fenetre[0]):
            fenetre = fenetre[1:]
        fenetre = [l for l in fenetre if not _LIGNE_COMPETENCES.search(normaliser(l))]
        description = normaliser(" ".join(fenetre))
        # The title is the line without "·": the other one is
        # "Company · contract type", or "Full-time · 6 yrs" in a grouped entry.
        libelle = next((l for l in fenetre if "·" not in l), fenetre[-1] if fenetre else "")
        coach = bool(_MOT_COACH.search(description))
        if not coach and _TITRE_STATUT_SEUL.match(normaliser(libelle)):
            # Only for a status title: on "DRH" a coaching skill must not hide
            # the second job, which is what this signal is there to show.
            fin_du_poste = rangs_dates[rang + 1] if rang + 1 < len(rangs_dates) else len(lignes)
            coach = any(
                _LIGNE_COMPETENCES.search(normaliser(l)) and _MOT_COACH.search(normaliser(l))
                for l in lignes[i + 1 : fin_du_poste]
            )
        if dates:
            en_cours = bool(_FIN_EN_COURS.search(dates.group("fin")))
            duree_mois = _duree_du_poste(dates, annee_courante)
        else:
            en_cours = False
            duree_mois = duree_en_mois(_LIGNE_DATE_SEULE.match(lignes[i]).group("duree") or "")
        postes.append(
            Poste(
                libelle=libelle,
                en_cours=en_cours,
                duree_mois=duree_mois,
                coach=coach,
                direction=bool(_MOTS_DIRECTION.search(description)),
                fonctionnaire=bool(_MOT_FONCTIONNAIRE.search(description)),
            )
        )
    return postes


def deriver_signaux(texte_experience: str, texte_infos: str = "") -> SignauxParcours:
    """Career signals of one profile; empty text gives empty signals, never an error."""
    postes = lire_postes(texte_experience)
    en_cours = [p for p in postes if p.en_cours]
    coachs_en_cours = [p for p in en_cours if p.coach]
    total = _TOTAL_ANNONCE.search(texte_experience or "")
    return SignauxParcours(
        nb_postes=len(postes),
        nb_postes_en_cours=len(en_cours),
        coach_en_cours=bool(coachs_en_cours),
        anciennete_coach_mois=max((p.duree_mois for p in coachs_en_cours), default=0),
        autre_poste_en_cours=any(not p.coach for p in en_cours),
        ancien_dirigeant=any(p.direction and not p.en_cours for p in postes),
        fonction_publique=any(p.fonctionnaire for p in postes),
        total_annonce=int(total.group(1)) if total else 0,
        longueur_infos=len(" ".join(lignes_utiles(texte_infos))),
        postes=tuple(postes),
    )
