"""Persistent store (SQLite) of the profiles already collected — POC-006.

Before this module, every run overwrote profils_extraits.csv: no memory of what
had already been seen, so two runs of the same boolean query brought back the
same batch. The store is now the source of truth; the CSV is an exported view
of it (see document/Backlog.md POC-006).

Deduplication key: the profile URL, normalised by clean_profile_url (same key
as the search, on purpose — a second normalisation rule here would be the real
bug). Also carries the two RGPD guardrails written down in POC-004 and
unattainable with an overwritten CSV: date_collecte (limited retention) and
ne_plus_traiter (right to object).

No Streamlit import here (see CLAUDE.md / ARCHITECTURE.md).
"""

import csv
import sqlite3
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from source.backend.adapters.scraping.profile_search import clean_profile_url

DEFAULT_DB_PATH = Path("./profils.db")

SCHEMA_VERSION = 1

# Columns carried by a profile dict, in CSV order. Must stay aligned with
# PROFILE_CSV_FIELDS (csv_export.py) - a unit test guards the alignment.
PROFILE_COLUMNS = [
    "nom",
    "url",
    "localisation",
    "titre",
    "email",
    "email_web",
    "site_web",
    "categorie",
    "score",
    "justification",
    "commentaire_client",
    "date_collecte",
    "ne_plus_traiter",
]

# Fields a collection run may complete on an already-known profile. Neither
# commentaire_client (client feedback, only importer_commentaires_csv writes
# it) nor date_collecte (frozen at first insert) nor ne_plus_traiter (only
# lifted deliberately) belong here.
_CHAMPS_COMPLETABLES = [
    "nom",
    "localisation",
    "titre",
    "email",
    "email_web",
    "site_web",
    "categorie",
    "score",
    "justification",
]

_CHAMPS_SCORING = ["categorie", "score", "justification"]

# Values accepted as "the client asked not to be contacted again" in a
# re-imported CSV. A blank or a 0 never lifts an existing marking.
_VALEURS_OPPOSITION = {"1", "true", "vrai", "oui", "yes", "x"}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS profils (
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


@dataclass
class ResultatEnregistrement:
    """What a collection run actually added to the store."""

    nouveaux: list[str] = field(default_factory=list)
    deja_connus: list[str] = field(default_factory=list)
    sans_url: int = 0

    def __len__(self) -> int:
        return len(self.nouveaux)


@dataclass
class RapportReimport:
    """Outcome of re-importing a CSV annotated by the client.

    commentaires_remplaces lists (url, ancien, nouveau): a client comment
    always wins over a stored one, but the substitution is reported rather
    than applied silently (AGENTS.md - no silent correction of business data).
    """

    commentaires_ajoutes: list[str] = field(default_factory=list)
    commentaires_remplaces: list[tuple[str, str, str]] = field(default_factory=list)
    commentaires_inchanges: int = 0
    oppositions_ajoutees: list[str] = field(default_factory=list)
    urls_inconnues: list[str] = field(default_factory=list)
    lignes_sans_url: int = 0


def ouvrir_magasin(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open (creating it if needed) the profile store and return its connection.

    Creating the schema is idempotent; no migration is ever performed here
    (CLAUDE.md rule 5 - a schema change requires a validated plan and a backup).
    """
    if str(db_path) != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    conn.commit()
    return conn


def urls_connues(conn: sqlite3.Connection) -> set[str]:
    """Every URL the store has ever seen — the set to exclude from a new run.

    Profiles marked ne_plus_traiter are deliberately included: the right to
    object is enforced by the very mechanism that deduplicates, so an opposed
    profile is never re-extracted.
    """
    return {row["url"] for row in conn.execute("SELECT url FROM profils")}


def enregistrer_profils(
    conn: sqlite3.Connection,
    profils: list[dict[str, str]],
    date_collecte: str | None = None,
) -> ResultatEnregistrement:
    """Store freshly extracted profiles without ever losing what is already there.

    A new URL is inserted with its collection date. A known URL is completed
    field by field: a non-empty incoming value refreshes the column, an empty
    one leaves the stored value untouched. date_collecte is never rewritten.
    """
    jour = date_collecte or date.today().isoformat()
    connues = urls_connues(conn)
    resultat = ResultatEnregistrement()

    for profil in profils:
        url = clean_profile_url(profil.get("url"))
        if not url:
            resultat.sans_url += 1
            continue

        valeurs = {champ: str(profil.get(champ, "") or "") for champ in _CHAMPS_COMPLETABLES}
        valeurs["url"] = url

        if url in connues:
            # COALESCE(NULLIF(...)) keeps the stored value when the incoming
            # one is empty: a new run never blanks an existing field.
            affectations = ", ".join(
                f"{champ} = COALESCE(NULLIF(:{champ}, ''), {champ})"
                for champ in _CHAMPS_COMPLETABLES
            )
            conn.execute(f"UPDATE profils SET {affectations} WHERE url = :url", valeurs)
            resultat.deja_connus.append(url)
        else:
            valeurs["commentaire_client"] = str(profil.get("commentaire_client", "") or "")
            valeurs["date_collecte"] = str(profil.get("date_collecte", "") or jour)
            colonnes = list(valeurs)
            conn.execute(
                f"INSERT INTO profils ({', '.join(colonnes)}) "
                f"VALUES ({', '.join(':' + c for c in colonnes)})",
                valeurs,
            )
            connues.add(url)
            resultat.nouveaux.append(url)

    conn.commit()
    return resultat


def mettre_a_jour_scoring(conn: sqlite3.Connection, profils: list[dict[str, str]]) -> int:
    """Write the scoring columns back to the store, returning the row count.

    commentaire_client is untouched on purpose: the scoring engine never owns
    the client's feedback (see scorer_profils, POC-003).
    """
    mises_a_jour = 0
    affectations = ", ".join(f"{champ} = :{champ}" for champ in _CHAMPS_SCORING)

    for profil in profils:
        url = clean_profile_url(profil.get("url"))
        if not url:
            continue
        valeurs = {champ: str(profil.get(champ, "") or "") for champ in _CHAMPS_SCORING}
        valeurs["url"] = url
        curseur = conn.execute(f"UPDATE profils SET {affectations} WHERE url = :url", valeurs)
        mises_a_jour += curseur.rowcount

    conn.commit()
    return mises_a_jour


def lister_profils(
    conn: sqlite3.Connection, inclure_ne_plus_traiter: bool = False
) -> list[dict[str, str]]:
    """Return the stored profiles as CSV-shaped dicts (every value a string).

    Profiles the client asked us to drop are excluded by default: they stay in
    the store so they keep being excluded from future collections, but they
    leave the exported view.
    """
    requete = f"SELECT {', '.join(PROFILE_COLUMNS)} FROM profils"
    if not inclure_ne_plus_traiter:
        requete += " WHERE ne_plus_traiter = 0"
    requete += " ORDER BY date_collecte, nom"

    return [
        {colonne: str(row[colonne]) for colonne in PROFILE_COLUMNS}
        for row in conn.execute(requete)
    ]


def marquer_ne_plus_traiter(conn: sqlite3.Connection, url: str) -> bool:
    """Mark a profile as "do not process again" (RGPD right to object).

    Returns False when the URL is unknown, so the caller can report it instead
    of believing the objection was recorded.
    """
    url_propre = clean_profile_url(url)
    if not url_propre:
        return False

    curseur = conn.execute(
        "UPDATE profils SET ne_plus_traiter = 1 WHERE url = :url", {"url": url_propre}
    )
    conn.commit()
    return curseur.rowcount > 0


def importer_commentaires_csv(conn: sqlite3.Connection, csv_path: Path) -> RapportReimport:
    """Re-import a CSV the client annotated, reconciled on the profile URL.

    Conflict rule (user decision, 26/08/2026): a filled client comment wins
    over the stored one and the substitution is reported; an empty CSV cell
    never erases stored feedback; an unknown URL is not created. The
    ne_plus_traiter column is read too, but only ever to add an objection -
    a blank or a 0 never lifts an existing marking.
    """
    rapport = RapportReimport()

    with open(csv_path, newline="", encoding="utf-8") as f:
        lignes = list(csv.DictReader(f))

    for ligne in lignes:
        url = clean_profile_url(ligne.get("url"))
        if not url:
            rapport.lignes_sans_url += 1
            continue

        row = conn.execute(
            "SELECT commentaire_client, ne_plus_traiter FROM profils WHERE url = :url",
            {"url": url},
        ).fetchone()
        if row is None:
            rapport.urls_inconnues.append(url)
            continue

        commentaire = str(ligne.get("commentaire_client", "") or "").strip()
        stocke = str(row["commentaire_client"] or "")
        if commentaire and commentaire != stocke:
            conn.execute(
                "UPDATE profils SET commentaire_client = :commentaire WHERE url = :url",
                {"commentaire": commentaire, "url": url},
            )
            if stocke:
                rapport.commentaires_remplaces.append((url, stocke, commentaire))
            else:
                rapport.commentaires_ajoutes.append(url)
        elif commentaire:
            rapport.commentaires_inchanges += 1

        opposition = str(ligne.get("ne_plus_traiter", "") or "").strip().lower()
        if opposition in _VALEURS_OPPOSITION and not row["ne_plus_traiter"]:
            conn.execute(
                "UPDATE profils SET ne_plus_traiter = 1 WHERE url = :url", {"url": url}
            )
            rapport.oppositions_ajoutees.append(url)

    conn.commit()
    return rapport
