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

SCHEMA_VERSION = 2

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
    "date_visite_email",
    "date_enrichissement_web",
    "statut_coordonnees",
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

# Validation status of the *web* contact details only (email_web/site_web),
# POC-009. The LinkedIn email of POC-002 is deliberately out of its scope: the
# person published it on their own profile, it is a fact rather than a
# candidate. The doubt - 1 confirmed true positive out of 25, measured on
# 10/07/2026 - is entirely on the web pipeline.
STATUT_CANDIDAT = "candidat"
STATUT_VALIDE = "valide"
STATUT_REJETE = "rejete"

# Statuses a human has ruled on. A run never overwrites them, neither the
# status itself nor the coordinates it qualifies: re-running the pipeline must
# not cost the human review a second time (POC-009 decision, 28/08/2026).
_STATUTS_HUMAINS = frozenset({STATUT_VALIDE, STATUT_REJETE})

@dataclass(frozen=True)
class _EtapeCoordonnees:
    """One contact-gathering step: what it fills, what it stamps, what it claims.

    statut_si_trouve is empty for a step whose result needs no human ruling.
    """

    champs: tuple[str, ...]
    colonne_marqueur: str
    statut_si_trouve: str = ""


_ETAPE_EMAIL_LINKEDIN = _EtapeCoordonnees(("email",), "date_visite_email")

_ETAPE_COORDONNEES_WEB = _EtapeCoordonnees(
    ("email_web", "site_web"), "date_enrichissement_web", STATUT_CANDIDAT
)

# Rulings a human may express in the re-imported CSV. candidat is deliberately
# absent: it is the machine's own word, only run_poc004 writes it.
_STATUTS_IMPORTABLES = frozenset({STATUT_VALIDE, STATUT_REJETE})

_SCHEMA = """
CREATE TABLE IF NOT EXISTS profils (
    url                     TEXT PRIMARY KEY,
    nom                     TEXT NOT NULL DEFAULT '',
    localisation            TEXT NOT NULL DEFAULT '',
    titre                   TEXT NOT NULL DEFAULT '',
    email                   TEXT NOT NULL DEFAULT '',
    email_web               TEXT NOT NULL DEFAULT '',
    site_web                TEXT NOT NULL DEFAULT '',
    categorie               TEXT NOT NULL DEFAULT '',
    score                   TEXT NOT NULL DEFAULT '',
    justification           TEXT NOT NULL DEFAULT '',
    commentaire_client      TEXT NOT NULL DEFAULT '',
    date_collecte           TEXT NOT NULL,
    ne_plus_traiter         INTEGER NOT NULL DEFAULT 0,
    date_visite_email       TEXT NOT NULL DEFAULT '',
    date_enrichissement_web TEXT NOT NULL DEFAULT '',
    statut_coordonnees      TEXT NOT NULL DEFAULT ''
);
"""

# Columns added by each schema version, applied to a store created under an
# earlier one. Purely additive with an empty default: on the rows already
# there, "empty" reads as "never attempted", which is exactly true.
_MIGRATIONS: dict[int, list[str]] = {
    2: [
        "date_visite_email       TEXT NOT NULL DEFAULT ''",
        "date_enrichissement_web TEXT NOT NULL DEFAULT ''",
        "statut_coordonnees      TEXT NOT NULL DEFAULT ''",
    ],
}


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
    statuts_tranches: list[tuple[str, str]] = field(default_factory=list)
    statuts_refuses: list[tuple[str, str]] = field(default_factory=list)
    urls_inconnues: list[str] = field(default_factory=list)
    lignes_sans_url: int = 0


@dataclass
class RapportCoordonnees:
    """Outcome of writing contact details back to the store — POC-009.

    valeurs_remplacees lists (url, colonne, ancienne, nouvelle): a fresh run
    observes a live source, so its non-empty value wins over a stored one, but
    the substitution is reported rather than applied silently (AGENTS.md - no
    silent correction of business data).

    figes_par_statut lists the profiles a human already ruled on (valide or
    rejete): their web coordinates and their status are left untouched, so a
    re-run never costs the review a second time.
    """

    profils_traites: list[str] = field(default_factory=list)
    coordonnees_trouvees: list[str] = field(default_factory=list)
    valeurs_remplacees: list[tuple[str, str, str, str]] = field(default_factory=list)
    figes_par_statut: list[str] = field(default_factory=list)
    urls_inconnues: list[str] = field(default_factory=list)
    sans_url: int = 0


def ouvrir_magasin(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open (creating it if needed) the profile store and return its connection.

    Creating the schema is idempotent, and a store created under an earlier
    schema version is migrated by migrer_schema (POC-009 plan, validated on
    28/08/2026 with an explicit backup - CLAUDE.md rule 5).
    """
    if str(db_path) != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    migrer_schema(conn)
    return conn


def migrer_schema(conn: sqlite3.Connection) -> list[str]:
    """Bring an existing store up to SCHEMA_VERSION, returning the columns added.

    Idempotent and additive only: every step is an ALTER TABLE ADD COLUMN with
    an empty default, guarded by what PRAGMA table_info actually reports, so a
    store already migrated by hand is left alone rather than failing. No column
    is ever dropped, renamed or rewritten.

    Before POC-009 this function did not exist and ouvrir_magasin stamped
    user_version unconditionally - which would have marked a v1 store as v2
    without adding a single column.
    """
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version >= SCHEMA_VERSION:
        return []

    colonnes_presentes = {row["name"] for row in conn.execute("PRAGMA table_info(profils)")}
    ajoutees: list[str] = []

    for cible in range(version + 1, SCHEMA_VERSION + 1):
        for declaration in _MIGRATIONS.get(cible, []):
            nom = declaration.split()[0]
            if nom in colonnes_presentes:
                continue
            conn.execute(f"ALTER TABLE profils ADD COLUMN {declaration}")
            ajoutees.append(nom)

    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    conn.commit()
    return ajoutees


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


def _ecrire_coordonnees(
    conn: sqlite3.Connection,
    profils: list[dict[str, str]],
    etape: _EtapeCoordonnees,
    jour: str,
) -> RapportCoordonnees:
    """Shared body of the two targeted contact-detail writes.

    The marker column is stamped for every processed profile, including the
    ones where nothing was found: that is the whole point of POC-009 - an
    empty coordinate column used to mean "not attempted", "attempted, nothing
    found" and "found but unreviewed" all at once.
    """
    rapport = RapportCoordonnees()
    champs = etape.champs

    for profil in profils:
        url = clean_profile_url(profil.get("url"))
        if not url:
            rapport.sans_url += 1
            continue

        row = conn.execute(
            f"SELECT {', '.join(champs)}, statut_coordonnees FROM profils WHERE url = :url",
            {"url": url},
        ).fetchone()
        if row is None:
            rapport.urls_inconnues.append(url)
            continue

        # A human already ruled on this one: stamp the marker so it leaves the
        # backlog, but touch neither the coordinates nor the status.
        if etape.statut_si_trouve and str(row["statut_coordonnees"] or "") in _STATUTS_HUMAINS:
            conn.execute(
                f"UPDATE profils SET {etape.colonne_marqueur} = :jour WHERE url = :url",
                {"jour": jour, "url": url},
            )
            rapport.figes_par_statut.append(url)
            rapport.profils_traites.append(url)
            continue

        valeurs = {champ: str(profil.get(champ, "") or "").strip() for champ in champs}
        trouve = any(valeurs.values())

        for champ, entrante in valeurs.items():
            stockee = str(row[champ] or "")
            if entrante and stockee and entrante != stockee:
                rapport.valeurs_remplacees.append((url, champ, stockee, entrante))

        # COALESCE(NULLIF(...)): an empty incoming value never blanks a filled
        # column, same rule as enregistrer_profils.
        affectations = [f"{champ} = COALESCE(NULLIF(:{champ}, ''), {champ})" for champ in champs]
        affectations.append(f"{etape.colonne_marqueur} = :jour")
        parametres = {**valeurs, "jour": jour, "url": url}

        if etape.statut_si_trouve and trouve:
            affectations.append("statut_coordonnees = :statut")
            parametres["statut"] = etape.statut_si_trouve

        conn.execute(
            f"UPDATE profils SET {', '.join(affectations)} WHERE url = :url", parametres
        )
        rapport.profils_traites.append(url)
        if trouve:
            rapport.coordonnees_trouvees.append(url)

    conn.commit()
    return rapport


def enregistrer_email_linkedin(
    conn: sqlite3.Connection,
    profils: list[dict[str, str]],
    date_visite: str | None = None,
) -> RapportCoordonnees:
    """Write back the public email read on the LinkedIn profile page (POC-002).

    No validation status is involved: the person published that address on
    their own profile. date_visite_email is stamped even when the profile
    showed no public email, so the profile leaves the backlog instead of being
    visited again at every run.
    """
    return _ecrire_coordonnees(
        conn, profils, _ETAPE_EMAIL_LINKEDIN, date_visite or date.today().isoformat()
    )


def enregistrer_coordonnees_web(
    conn: sqlite3.Connection,
    profils: list[dict[str, str]],
    date_enrichissement: str | None = None,
) -> RapportCoordonnees:
    """Write back the web enrichment results (POC-004), as candidates only.

    Anything found is stored as STATUT_CANDIDAT and never as validated: the
    measured relevance rate is 1 confirmed true positive out of 25, so a
    candidate is not a fact. Only a human turns it into valide or rejete, and
    a later run never downgrades that ruling.
    """
    return _ecrire_coordonnees(
        conn,
        profils,
        _ETAPE_COORDONNEES_WEB,
        date_enrichissement or date.today().isoformat(),
    )


def profils_a_visiter(profils: list[dict[str, str]]) -> list[dict[str, str]]:
    """Profiles whose LinkedIn page has never been visited for an email.

    Pure function over already-listed rows, so the backlog logic is testable
    without a database, a browser or a network (same split as POC-006's
    collecter_profils_inconnus). Feeding it lister_profils() output means
    ne_plus_traiter profiles are already excluded.
    """
    return [p for p in profils if not str(p.get("date_visite_email", "") or "").strip()]


def profils_a_enrichir(profils: list[dict[str, str]]) -> list[dict[str, str]]:
    """Profiles the web enrichment has never been attempted on.

    Deliberately unaware of the score: the caller applies
    selectionner_profils_interessants first (client decision, 13/07/2026), so
    that the conditional selection and the backlog stay two separate rules.
    """
    return [p for p in profils if not str(p.get("date_enrichissement_web", "") or "").strip()]


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

        _importer_statut_coordonnees(conn, url, ligne, rapport)

    conn.commit()
    return rapport


def _importer_statut_coordonnees(
    conn: sqlite3.Connection, url: str, ligne: dict[str, str], rapport: RapportReimport
) -> None:
    """Apply the human ruling on a profile's web contact details (POC-009).

    Only valide and rejete are accepted: candidat is the machine's own word,
    written by run_poc004 alone. A blank cell never clears an existing ruling,
    and an unrecognised value is reported rather than silently dropped - it is
    business data, and the review it stands for is expensive (1 confirmed true
    positive out of 25).
    """
    statut = str(ligne.get("statut_coordonnees", "") or "").strip().lower()
    if not statut or statut == STATUT_CANDIDAT:
        return

    if statut not in _STATUTS_IMPORTABLES:
        rapport.statuts_refuses.append((url, statut))
        return

    conn.execute(
        "UPDATE profils SET statut_coordonnees = :statut WHERE url = :url",
        {"statut": statut, "url": url},
    )
    rapport.statuts_tranches.append((url, statut))
