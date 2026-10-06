"""Collection journal: which query brought each profile into the store (POC-008).

The store has no column for the originating query, and adding one would be a
schema migration. Since a profile is only ever collected once (deduplication
on the URL), a side journal is enough to trace it: one line per profile
actually added to the store, appended run after run.

The journal holds profile URLs - personal data, gitignored like the exports -
and lives outside the store: it must be backed up along with it.
"""

import csv
from pathlib import Path

JOURNAL_COLLECTE = Path("./journal_collecte.csv")

JOURNAL_FIELDS = ["date_collecte", "url", "requete_id", "requete_libelle"]


def journaliser_collecte(lignes: list[dict[str, str]], chemin: Path = JOURNAL_COLLECTE) -> int:
    """Append the given lines to the journal, returning how many were written.

    Append-only: an existing journal is never rewritten, and the header is
    written only when the file is created.
    """
    if not lignes:
        return 0

    nouveau = not chemin.exists() or chemin.stat().st_size == 0
    with open(chemin, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=JOURNAL_FIELDS, restval="", extrasaction="ignore")
        if nouveau:
            writer.writeheader()
        writer.writerows(lignes)
    return len(lignes)


def lire_journal(chemin: Path = JOURNAL_COLLECTE) -> list[dict[str, str]]:
    """Read the whole journal, or [] if no run has written it yet."""
    if not chemin.exists():
        return []
    with open(chemin, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
