"""POC-004 entry script: web enrichment pipeline (deterministic, no LLM).

For each profile worth the cost, search the web via the Brave Search API for
an alternative contact, filter out irrelevant domains, then visit the
remaining candidate page via a simple HTTP request and extract an email/site
with regex. See document/Backlog.md POC-004 for the full pipeline description
and RGPD safeguards.

POC-009: input and output are the store, no longer two CSV files. Two rules
the CSV could not carry:

- the enrichment is conditional on the scoring (client decision, 13/07/2026),
  so the input is selectionner_profils_interessants applied to the store;
- what the pipeline finds is stored as a *candidate*, never as a fact. The
  measured relevance rate is 1 confirmed true positive out of 25 (10/07/2026),
  so only a human review turns a candidate into valide or rejete - and a later
  run never downgrades that ruling.

date_enrichissement_web is stamped even when nothing is found, so a profile
already processed leaves the backlog instead of costing a Brave Search call at
every run.

Usage:
    python -m source.backend.adapters.enrichment.run_poc004

Run standalone (never via `streamlit run`, see CLAUDE.md rule 6). No browser
involved here: candidate pages are fetched via plain HTTP requests, not
Playwright.
"""

import requests

from source.backend.adapters.enrichment.email_site_extractor import (
    extract_email_from_html,
    extract_site_root,
    filter_candidate_urls,
)
from source.backend.adapters.enrichment.web_search import (
    build_search_query,
    get_brave_api_key,
    search_candidate_urls,
)
from source.backend.adapters.storage.csv_export import EXPORT_CSV, export_profiles_to_csv
from source.backend.adapters.storage.profile_store import (
    DEFAULT_DB_PATH,
    RapportCoordonnees,
    enregistrer_coordonnees_web,
    lister_profils,
    ouvrir_magasin,
    profils_a_enrichir,
)
from source.backend.core.profile_scoring import (
    charger_regles,
    selectionner_profils_interessants,
)

# Kept at 5 for the first run on the store (POC-009): 60 of the 75 stored
# profiles are above the threshold, so an unbounded run would be 60 Brave
# Search calls. Raise it only once a run has been reviewed.
MAX_PROFILES = 5


def fetch_candidate_html(url: str) -> str:
    """Fetch a candidate page's HTML via a simple HTTP request.

    Never raises: an unreachable page or failed request is treated as "no
    conclusive content" rather than a blocking error, same pattern as
    POC-002's email extraction.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return ""


def enrich_profile(profile: dict[str, str], api_key: str) -> dict[str, str]:
    """Search, filter and visit candidate pages for one profile, returning it
    with email_web/site_web added (blank if nothing conclusive was found).
    """
    query = build_search_query(profile["nom"], profile["titre"], profile["localisation"])
    candidate_urls = filter_candidate_urls(search_candidate_urls(query, api_key))

    email_web = ""
    site_web = ""
    for url in candidate_urls:
        html = fetch_candidate_html(url)
        if not html:
            continue
        email_web = extract_email_from_html(html)
        site_web = extract_site_root(url)
        if email_web or site_web:
            break

    return {**profile, "email_web": email_web, "site_web": site_web}


def main() -> None:
    regles = charger_regles()
    conn = ouvrir_magasin(DEFAULT_DB_PATH)
    try:
        interessants = selectionner_profils_interessants(lister_profils(conn), regles=regles)
        reliquat = profils_a_enrichir(interessants)
        print(
            f"{len(interessants)} profils interessants "
            f"(score >= {regles.seuil_profil_interessant}), "
            f"dont {len(reliquat)} jamais enrichis"
        )
        if not reliquat:
            print("Rien a traiter : tous les profils interessants ont deja ete enrichis.")
            return

        lot = reliquat[:MAX_PROFILES]
        print(
            f"Lot traite : {len(lot)} profils, soit autant d'appels Brave Search "
            f"(plafond MAX_PROFILES={MAX_PROFILES})"
        )
        for profil in lot:
            print(f"  - {profil['nom']} — {profil['url']}")

        api_key = get_brave_api_key()
        enrichis = [enrich_profile(profil, api_key) for profil in lot]

        rapport = enregistrer_coordonnees_web(conn, enrichis)
        _afficher_rapport(rapport)

        profils_magasin = lister_profils(conn)
        export_profiles_to_csv(profils_magasin, EXPORT_CSV)
        print(f"{len(profils_magasin)} profils exportes -> {EXPORT_CSV.resolve()}")
    finally:
        conn.close()


def _afficher_rapport(rapport: RapportCoordonnees) -> None:
    """Print what the run wrote, contradictions and frozen rulings included.

    A stored value replaced by a fresh one is never silent (AGENTS.md).
    """
    print(
        f"{len(rapport.profils_traites)} profils marques comme enrichis, "
        f"{len(rapport.coordonnees_trouvees)} candidat(s) trouve(s) — "
        f"a relire avant tout contact, aucun n'est un fait etabli"
    )
    for url, colonne, ancienne, nouvelle in rapport.valeurs_remplacees:
        print(f"  ATTENTION valeur remplacee — {url} : {colonne} '{ancienne}' -> '{nouvelle}'")
    if rapport.figes_par_statut:
        print(
            f"  {len(rapport.figes_par_statut)} profil(s) deja tranche(s) par un humain, "
            f"coordonnees inchangees"
        )
    if rapport.urls_inconnues:
        print(f"  {len(rapport.urls_inconnues)} URL(s) absente(s) du magasin, ignoree(s)")


if __name__ == "__main__":
    main()
