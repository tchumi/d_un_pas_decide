# handoff.md — État du sprint en cours

<!--
Format de chaque section :
## [N]. [ID_TICKET] — [Titre court] ([date JJ/MM/AAAA])
- Ce qui a été fait
- Fichiers modifiés
- Tests lancés / résultats
- Points de vigilance
- Prochain ticket recommandé
-->

## 1. Initialisation projet (02/07/2026)

- Squelette de gouvernance Claude créé depuis `claude-project-template`, adapté au projet ProspectionLinkedIn (POC prospection coachs business sur LinkedIn pour D'un Pas Décidé).
- Fichiers initiaux : `CLAUDE.md`, `AGENTS.md`, `task_list.md`, `handoff.md`, `prompt_générique.md`, `Backlog.md`, `ARCHITECTURE.md`.
- Stack retenue : Streamlit (UI) + Playwright (scraping) + SQLite + pandas, avec isolation stricte frontend/backend (zéro import Streamlit dans `core/`/`adapters/`) pour permettre une UI desktop en remplacement futur.
- Identifiants LinkedIn (`LINKEDIN_EMAIL`/`LINKEDIN_PASSWORD`) prévus dans `.env.local` (non commité).
- Prochain ticket : POC-001 — Script de recherche + extraction basique de profils LinkedIn

## 2. POC-001 — Script de recherche + extraction basique de profils LinkedIn (03/07/2026)

- Squelette du module scraping/storage créé : `pyproject.toml` (deps playwright, pandas, streamlit, pytest) + arborescence `source/backend/adapters/{scraping,storage}/`.
- Sélecteurs CSS LinkedIn centralisés dans `source/backend/adapters/scraping/selectors.py` (repris et isolés depuis `document/spec/linkedin_search_poc.py`, avec commentaires sur les points fragiles : sélecteur du nom, bouton de pagination dépendant de la langue du compte).
- Login manuel (bloquant via `input()`, pas d'auto-remplissage) isolé dans `browser_session.py` (`ensure_logged_in`) pour faciliter un futur remplacement non bloquant sans toucher au reste.
- Recherche + extraction + pagination dans `profile_search.py`, logique pure (`build_search_url`, `clean_profile_url`) séparée de la partie Playwright pour rester testable sans navigateur.
- Export CSV (nom, url, localisation, titre — sans email) dans `storage/csv_export.py`.
- Script exécutable d'assemblage : `source/backend/adapters/scraping/run_poc001.py` (requête booléenne de la spec, `MAX_PROFILES=5` pour la première phase de debug — décision explicite utilisateur, à remonter à 20-25 une fois un run validé sans blocage de compte).
- `.env.local` créé avec placeholders `LINKEDIN_EMAIL`/`LINKEDIN_PASSWORD` (non lus par le code, non commité).
- `.gitignore` : ajout de `browser_profile/` (dossier de session Playwright, cookies LinkedIn) et `profils_extraits.csv` (validé explicitement par l'utilisateur, hors périmètre initial du ticket).
- Zéro import Streamlit dans les modules créés (vérifié).
- Fichiers créés : `pyproject.toml`, `source/backend/**/__init__.py`, `source/backend/adapters/scraping/{selectors,browser_session,profile_search,run_poc001}.py`, `source/backend/adapters/storage/csv_export.py`, `tests/unit/{__init__,test_csv_export,test_profile_search}.py`, `.env.local` (non commité).
- Fichiers modifiés : `.gitignore`, `document/claude_code/task_list.md`, `document/claude_code/handoff.md`.
- Tests lancés : `pytest tests/unit/ -v` → 7 passed ; `pytest tests/ --collect-only -q` → 7 tests collectés. Import de tous les modules (y compris Playwright) vérifié sans erreur.
- **Non vérifié par l'agent** : exécution réelle de `run_poc001.py` avec un compte LinkedIn (login manuel, extraction live, absence de blocage de compte) — critère d'acceptation du ticket, à valider manuellement par l'utilisateur. Lancement : `uv run python -m source.backend.adapters.scraping.run_poc001`.
- Points de vigilance : sélecteur du nom (`span[aria-hidden='true']`) et bouton de pagination (`aria-label='Suivant'`, dépend de la langue du compte) restent les points les plus fragiles du DOM LinkedIn — à corriger dans `selectors.py` si l'extraction échoue en conditions réelles.
- Lancement de l'app **non nécessaire** avant le prochain ticket : aucun fichier `frontend_streamlit/` touché, uniquement des modules nouveaux sans appelant Streamlit.
- Prochain ticket recommandé : valider manuellement `run_poc001.py` (MAX_PROFILES=5) avec le compte LinkedIn personnel ; si concluant, remonter à 20-25 et clore POC-001 (DONE) ; sinon, ticket de correction des sélecteurs.
