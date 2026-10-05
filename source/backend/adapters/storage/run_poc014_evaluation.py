"""POC-014 entry script: measure a scoring rule set against the client's verdicts.

READ-ONLY. The store is opened with SQLite's `mode=ro`, never through
ouvrir_magasin (which may create or migrate the schema). The titles are
re-scored in memory with the rule file(s) given on the command line, so a
candidate rule set can be measured before run_poc003 writes anything.

The ground truth is the client's verdict of 11/09/2026, stored as free text in
`commentaire_client` and starting with one of four prefixes (see
document/Backlog.md POC-003, "Retour client du 11/09/2026"). A comment that
matches none of them is reported, never guessed.

No LinkedIn run, no browser, no network call, no LLM.

Usage:
    python -m source.backend.adapters.storage.run_poc014_evaluation
    python -m source.backend.adapters.storage.run_poc014_evaluation old.json new.json

Run standalone (never via `streamlit run`, see CLAUDE.md rule 6).
"""

import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from source.backend.adapters.storage.profile_store import DEFAULT_DB_PATH
from source.backend.core.profile_scoring import (
    DEFAULT_RULES_PATH,
    ReglesScoring,
    charger_regles,
    normaliser,
    scorer_profils,
    selectionner_profils_interessants,
)

VERDICT_EXCELLENT = "excellent"
VERDICT_BON = "bon"
VERDICT_MAUVAIS = "mauvais"
VERDICT_RIEN_A_VOIR = "rien a voir"
VERDICTS = (VERDICT_EXCELLENT, VERDICT_BON, VERDICT_MAUVAIS, VERDICT_RIEN_A_VOIR)
# The profiles the client wants to keep: precision and recall are computed
# on this group.
VERDICTS_POSITIFS = frozenset({VERDICT_EXCELLENT, VERDICT_BON})

# Normalized comment prefix -> verdict (the client's own wording, mail of 11/09/2026).
_PREFIXES_VERDICT = {
    "excellent profil": VERDICT_EXCELLENT,
    "bon profil": VERDICT_BON,
    "mauvais profil": VERDICT_MAUVAIS,
    "rien a voir": VERDICT_RIEN_A_VOIR,
}


def parser_verdict(commentaire: str | None) -> str | None:
    """Verdict carried by a client comment, or None when it matches no prefix.

    The prefix must be the whole comment or be followed by a separator
    ("mauvais profil, consultant"): "bon profilage" is not a verdict.
    """
    normalise = normaliser(commentaire or "")
    for prefixe, verdict in _PREFIXES_VERDICT.items():
        if normalise == prefixe or normalise.startswith(prefixe + " "):
            return verdict
    return None


def lire_profils_lecture_seule(db_path: Path | str = DEFAULT_DB_PATH) -> list[dict[str, str]]:
    """Read every stored profile through a read-only SQLite connection."""
    uri = f"file:{Path(db_path).resolve().as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        conn.row_factory = sqlite3.Row
        return [dict(ligne) for ligne in conn.execute("SELECT * FROM profils")]
    finally:
        conn.close()


@dataclass(frozen=True)
class MesureRegle:
    """How often a rule fired, and on how many good or excellent profiles."""

    declenchee: int
    positifs: int

    @property
    def part_positifs(self) -> float:
        return self.positifs / self.declenchee if self.declenchee else 0.0


@dataclass(frozen=True)
class Evaluation:
    """Scores of one rule set confronted with the client's verdicts."""

    seuil: int
    juges: int
    positifs: int
    retenus: int
    retenus_positifs: int
    # score -> verdict -> number of profiles
    matrice: dict[int, Counter] = field(default_factory=dict)
    par_regle: dict[str, MesureRegle] = field(default_factory=dict)
    # Good or excellent profiles left under the threshold (recall losses).
    positifs_ecartes: tuple[dict[str, str], ...] = ()
    # Profiles whose comment carries no recognizable verdict: left out of
    # every figure above, listed so that nothing is silently dropped.
    non_reconnus: tuple[dict[str, str], ...] = ()

    @property
    def precision(self) -> float:
        return self.retenus_positifs / self.retenus if self.retenus else 0.0

    @property
    def rappel(self) -> float:
        return self.retenus_positifs / self.positifs if self.positifs else 0.0

    @property
    def taux_de_base(self) -> float:
        return self.positifs / self.juges if self.juges else 0.0


def _regles_declenchees(justification: str) -> set[str]:
    # scorer_titre writes "id +40 (...)" per bonus/malus, joined by " | ", and
    # "id : libelle" for an exclusion: the rule id is always the first token.
    return {partie.split(" ", 1)[0] for partie in justification.split(" | ") if partie}


def evaluer(profils: list[dict[str, str]], regles: ReglesScoring) -> Evaluation:
    """Re-score the profiles in memory and compare with the client's verdicts."""
    scores = scorer_profils(profils, regles)
    juges = []
    non_reconnus = []
    for profil in scores:
        verdict = parser_verdict(profil.get("commentaire_client"))
        if verdict is None:
            non_reconnus.append(profil)
        else:
            juges.append((profil, verdict))

    interessants = selectionner_profils_interessants([p for p, _ in juges], regles=regles)
    retenus = {id(p) for p in interessants}

    matrice: dict[int, Counter] = {}
    declenchements: Counter = Counter()
    declenchements_positifs: Counter = Counter()
    positifs_ecartes = []
    retenus_positifs = 0
    for profil, verdict in juges:
        positif = verdict in VERDICTS_POSITIFS
        matrice.setdefault(int(profil["score"]), Counter())[verdict] += 1
        for regle_id in _regles_declenchees(profil["justification"]):
            declenchements[regle_id] += 1
            declenchements_positifs[regle_id] += positif
        if positif and id(profil) in retenus:
            retenus_positifs += 1
        elif positif:
            positifs_ecartes.append(profil)

    return Evaluation(
        seuil=regles.seuil_profil_interessant,
        juges=len(juges),
        positifs=sum(1 for _, v in juges if v in VERDICTS_POSITIFS),
        retenus=len(retenus),
        retenus_positifs=retenus_positifs,
        matrice=matrice,
        par_regle={
            regle.id: MesureRegle(declenchements[regle.id], declenchements_positifs[regle.id])
            for regle in regles.regles
        },
        positifs_ecartes=tuple(positifs_ecartes),
        non_reconnus=tuple(non_reconnus),
    )


def _afficher(evaluation: Evaluation, regles: ReglesScoring, chemin_regles: Path) -> None:
    print(f"=== Regles : {chemin_regles} (version {regles.version}) ===")
    print(
        f"{evaluation.juges} profils juges, {evaluation.positifs} bons ou excellents "
        f"(taux de base {evaluation.taux_de_base:.0%})"
    )
    print(
        f"Seuil {evaluation.seuil} : {evaluation.retenus} retenus dont "
        f"{evaluation.retenus_positifs} bons ou excellents -> "
        f"precision {evaluation.precision:.0%}, rappel {evaluation.rappel:.0%}"
    )

    print("\nMatrice score x verdict (cumul = profils a ce score ou au-dessus)")
    print(
        f"{'score':>5} {'exc':>4} {'bon':>4} {'mauv':>5} {'rien':>5} | "
        f"{'cumul':>5} {'precision':>9}"
    )
    cumul = cumul_positifs = 0
    for score in sorted(evaluation.matrice, reverse=True):
        ligne = evaluation.matrice[score]
        cumul += sum(ligne.values())
        cumul_positifs += ligne[VERDICT_EXCELLENT] + ligne[VERDICT_BON]
        print(
            f"{score:>5} {ligne[VERDICT_EXCELLENT]:>4} {ligne[VERDICT_BON]:>4} "
            f"{ligne[VERDICT_MAUVAIS]:>5} {ligne[VERDICT_RIEN_A_VOIR]:>5} | "
            f"{cumul:>5} {cumul_positifs / cumul:>9.0%}"
        )

    print("\nPouvoir discriminant par regle (part de bons ou excellents quand elle se declenche)")
    for regle in regles.regles:
        mesure = evaluation.par_regle[regle.id]
        print(
            f"  {regle.id:<24} {regle.type:<19} poids {regle.poids:>+4} : "
            f"{mesure.positifs:>2}/{mesure.declenchee:<2} ({mesure.part_positifs:.0%})"
        )

    if evaluation.positifs_ecartes:
        nombre = len(evaluation.positifs_ecartes)
        print(f"\nATTENTION - {nombre} bon(s) ou excellent(s) sous le seuil :")
        for profil in evaluation.positifs_ecartes:
            print(f"  score {profil['score']} | {profil.get('titre', '')}")
    if evaluation.non_reconnus:
        print(f"\nATTENTION - {len(evaluation.non_reconnus)} commentaire(s) sans verdict reconnu :")
        for profil in evaluation.non_reconnus:
            print(f"  {profil.get('url', '')} | {profil.get('commentaire_client', '')!r}")
    print()


def main(arguments: list[str] | None = None) -> None:
    # Titles carry emoji: a cp1252 console must not kill the report (POC-009).
    sys.stdout.reconfigure(errors="replace")
    arguments = sys.argv[1:] if arguments is None else arguments
    chemins = [Path(a) for a in arguments] or [DEFAULT_RULES_PATH]

    profils = lire_profils_lecture_seule(DEFAULT_DB_PATH)
    print(f"{len(profils)} profils lus (lecture seule) depuis le magasin {DEFAULT_DB_PATH}\n")
    for chemin in chemins:
        regles = charger_regles(chemin)
        _afficher(evaluer(profils, regles), regles, chemin)


if __name__ == "__main__":
    main()
