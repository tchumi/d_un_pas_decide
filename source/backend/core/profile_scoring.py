"""Deterministic scoring and categorization of extracted LinkedIn profiles (POC-003).

Pure business logic: no Streamlit, no Playwright, no network call, no LLM (see
CLAUDE.md and document/Backlog.md POC-003). The client asked for a
`justification` column next to the score, which a rule engine produces by
construction and which stays verifiable - that is the reason a deterministic
engine was chosen over an LLM.

The only textual signal available for a profile at this stage is its LinkedIn
`titre`. The beginner/experienced distinction is deliberately out of scope
(not decidable from the title alone): those profiles fall back to the default
"indifferencie" category, which is the fallback the client announced on
04/07/2026.

The rules themselves live in a JSON file (config/scoring_rules.json) so they
can be read, edited and saved from the future configuration menu without
touching this module.

WARNING - calibration: the rules were calibrated on the same batch of 25 real
profiles that serves as the reference set. They are kept few and simple on
purpose; they must be revalidated on a freshly extracted batch.
"""

import json
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from re import sub

# config/ sits at the repository root, three levels above this module
# (source/backend/core/). Resolved from __file__ rather than the current
# working directory so the module works whatever the caller's cwd.
DEFAULT_RULES_PATH = Path(__file__).resolve().parents[3] / "config" / "scoring_rules.json"

# Rule types understood by the engine. Exclusion rules are always evaluated
# first and short-circuit the scoring (score forced to 0).
TYPE_EXCLUSION_ABSENCE = "exclusion_absence"  # excluded when NO keyword matches
TYPE_EXCLUSION_PRESENCE = "exclusion_presence"  # excluded when ANY keyword matches
TYPE_BONUS = "bonus"
TYPE_MALUS = "malus"
TYPES_EXCLUSION = (TYPE_EXCLUSION_ABSENCE, TYPE_EXCLUSION_PRESENCE)

# How the weights of the triggered rules are combined. Declared explicitly in
# the JSON ("agregation") so the arithmetic isn't an implicit property of this
# module. Only the algebraic sum is implemented so far; any other mode is
# rejected at load time rather than silently ignored.
MODE_AGREGATION_SOMME = "somme"
MODES_AGREGATION_SUPPORTES = (MODE_AGREGATION_SOMME,)


def normaliser(texte: str) -> str:
    """Lowercase, strip accents and turn punctuation into spaces.

    Applied to both the profile title and the rule keywords, so that a keyword
    can be written naturally in the JSON ("coach d'entreprise") and still match
    real-world title spellings ("Coach-Professionnel", "COACH D’ENTREPRISE").
    """
    decompose = unicodedata.normalize("NFD", texte.lower())
    sans_accents = "".join(c for c in decompose if unicodedata.category(c) != "Mn")
    return sub(r"\s+", " ", sub(r"[^a-z0-9]+", " ", sans_accents)).strip()


@dataclass(frozen=True)
class Regle:
    """One scoring rule, applied at most once whatever the number of matches."""

    id: str
    type: str
    poids: int
    mots_cles: tuple[str, ...]
    libelle: str = ""

    def mots_cles_trouves(self, titre_normalise: str) -> tuple[str, ...]:
        """Keywords of this rule present in the normalized title (original spelling)."""
        return tuple(m for m in self.mots_cles if normaliser(m) in titre_normalise)


@dataclass(frozen=True)
class Categorie:
    """A named category detected by keywords; carries no score of its own."""

    id: str
    mots_cles: tuple[str, ...]
    libelle: str = ""

    def correspond(self, titre_normalise: str) -> bool:
        return any(normaliser(m) in titre_normalise for m in self.mots_cles)


@dataclass(frozen=True)
class Agregation:
    """How triggered weights combine into the final score.

    Made explicit in the configuration rather than hardcoded here: a bonus
    carries a positive weight (added), a malus a negative one (subtracted).
    """

    mode: str = MODE_AGREGATION_SOMME
    regle_appliquee_une_seule_fois: bool = True
    commentaire: str = ""


@dataclass(frozen=True)
class ReglesScoring:
    """Full rule set, as loaded from the JSON configuration file."""

    regles: tuple[Regle, ...]
    categories: tuple[Categorie, ...]
    agregation: Agregation = Agregation()
    score_min: int = 0
    score_max: int = 100
    seuil_profil_interessant: int = 60
    categorie_exclusion: str = "exclu"
    categorie_par_defaut: str = "coach_business_indifferencie"
    version: int = 1
    commentaire: str = ""


@dataclass(frozen=True)
class ResultatScoring:
    """Outcome for one profile: what the CSV columns are filled with."""

    categorie: str
    score: int
    justification: str


def charger_regles(chemin: Path | None = None) -> ReglesScoring:
    """Load the rule set from its JSON file."""
    chemin = chemin or DEFAULT_RULES_PATH
    with open(chemin, encoding="utf-8") as f:
        brut = json.load(f)
    agregation_brute = brut.get("agregation", {})
    agregation = Agregation(
        mode=agregation_brute.get("mode", MODE_AGREGATION_SOMME),
        regle_appliquee_une_seule_fois=bool(
            agregation_brute.get("regle_appliquee_une_seule_fois", True)
        ),
        commentaire=agregation_brute.get("commentaire", ""),
    )
    if agregation.mode not in MODES_AGREGATION_SUPPORTES:
        raise ValueError(
            f"Mode d'agregation inconnu : {agregation.mode!r}. "
            f"Modes supportes : {MODES_AGREGATION_SUPPORTES}."
        )
    return ReglesScoring(
        regles=tuple(
            Regle(
                id=r["id"],
                type=r["type"],
                poids=int(r.get("poids", 0)),
                mots_cles=tuple(r.get("mots_cles", [])),
                libelle=r.get("libelle", ""),
            )
            for r in brut.get("regles", [])
        ),
        categories=tuple(
            Categorie(
                id=c["id"],
                mots_cles=tuple(c.get("mots_cles", [])),
                libelle=c.get("libelle", ""),
            )
            for c in brut.get("categories", [])
        ),
        agregation=agregation,
        score_min=int(brut.get("score_min", 0)),
        score_max=int(brut.get("score_max", 100)),
        seuil_profil_interessant=int(brut.get("seuil_profil_interessant", 60)),
        categorie_exclusion=brut.get("categorie_exclusion", "exclu"),
        categorie_par_defaut=brut.get("categorie_par_defaut", "coach_business_indifferencie"),
        version=int(brut.get("version", 1)),
        commentaire=brut.get("commentaire", ""),
    )


def sauvegarder_regles(regles: ReglesScoring, chemin: Path | None = None) -> None:
    """Write a rule set back to JSON, in the format charger_regles() reads.

    Provided for the future configuration menu (edit then save). Keyword
    spellings are preserved as-is: normalization happens at match time only.
    """
    chemin = chemin or DEFAULT_RULES_PATH
    contenu = {
        "version": regles.version,
        "commentaire": regles.commentaire,
        "score_min": regles.score_min,
        "score_max": regles.score_max,
        "seuil_profil_interessant": regles.seuil_profil_interessant,
        "agregation": {
            "mode": regles.agregation.mode,
            "regle_appliquee_une_seule_fois": regles.agregation.regle_appliquee_une_seule_fois,
            "commentaire": regles.agregation.commentaire,
        },
        "categorie_exclusion": regles.categorie_exclusion,
        "categorie_par_defaut": regles.categorie_par_defaut,
        "regles": [
            {
                "id": r.id,
                "type": r.type,
                "poids": r.poids,
                "mots_cles": list(r.mots_cles),
                "libelle": r.libelle,
            }
            for r in regles.regles
        ],
        "categories": [
            {"id": c.id, "mots_cles": list(c.mots_cles), "libelle": c.libelle}
            for c in regles.categories
        ],
    }
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(contenu, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _exclusion_declenchee(regle: Regle, titre_normalise: str) -> bool:
    trouves = regle.mots_cles_trouves(titre_normalise)
    if regle.type == TYPE_EXCLUSION_ABSENCE:
        return not trouves
    return bool(trouves)


def _categoriser(titre_normalise: str, regles: ReglesScoring) -> str:
    for categorie in regles.categories:
        if categorie.correspond(titre_normalise):
            return categorie.id
    return regles.categorie_par_defaut


def scorer_titre(titre: str, regles: ReglesScoring) -> ResultatScoring:
    """Score and categorize a single LinkedIn title.

    Exclusion rules are evaluated first and win over everything else: an
    excluded profile scores 0 and gets the exclusion category. It is still
    returned (never silently dropped) so the exclusion stays auditable.
    """
    titre_normalise = normaliser(titre or "")

    for regle in regles.regles:
        if regle.type in TYPES_EXCLUSION and _exclusion_declenchee(regle, titre_normalise):
            return ResultatScoring(
                categorie=regles.categorie_exclusion,
                score=regles.score_min,
                justification=f"{regle.id} : {regle.libelle}",
            )

    # Aggregation is the algebraic sum of the triggered weights (bonus > 0
    # added, malus < 0 subtracted), as declared in the JSON "agregation"
    # block, then clamped to [score_min, score_max].
    score = 0
    justifications: list[str] = []
    for regle in regles.regles:
        if regle.type not in (TYPE_BONUS, TYPE_MALUS):
            continue
        trouves = regle.mots_cles_trouves(titre_normalise)
        if not trouves:
            continue
        occurrences = 1 if regles.agregation.regle_appliquee_une_seule_fois else len(trouves)
        apport = regle.poids * occurrences
        score += apport
        justifications.append(f"{regle.id} {apport:+d} ({', '.join(trouves)})")

    score = max(regles.score_min, min(regles.score_max, score))
    return ResultatScoring(
        categorie=_categoriser(titre_normalise, regles),
        score=score,
        justification=" | ".join(justifications),
    )


def scorer_profils(
    profils: list[dict[str, str]], regles: ReglesScoring | None = None
) -> list[dict[str, str]]:
    """Score a list of profile rows, returning copies enriched with the new columns.

    An existing `commentaire_client` value is never overwritten: re-running the
    scoring on a CSV the client has already annotated keeps their feedback.
    """
    regles = regles or charger_regles()
    resultats = []
    for profil in profils:
        resultat = scorer_titre(profil.get("titre", ""), regles)
        enrichi = dict(profil)
        enrichi["categorie"] = resultat.categorie
        enrichi["score"] = str(resultat.score)
        enrichi["justification"] = resultat.justification
        enrichi.setdefault("commentaire_client", "")
        resultats.append(enrichi)
    return resultats


def selectionner_profils_interessants(
    profils_scores: list[dict[str, str]],
    seuil: int | None = None,
    regles: ReglesScoring | None = None,
) -> list[dict[str, str]]:
    """Keep only the profiles worth a downstream, costly step.

    Client decision of 13/07/2026: web enrichment (POC-004) is no longer a
    systematic pipeline stage, it becomes a conditional one applied after the
    scoring to the interesting profiles only. This function is that selection
    point; POC-004 itself is untouched.

    The threshold is a starting value, meant to be tunable from the future
    configuration menu - hence its presence in the JSON rules file.
    """
    regles = regles or charger_regles()
    seuil = regles.seuil_profil_interessant if seuil is None else seuil
    return [
        p
        for p in profils_scores
        if p.get("categorie") != regles.categorie_exclusion and int(p.get("score", 0)) >= seuil
    ]
