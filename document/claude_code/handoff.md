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
- **Bugs corrigés en cours de test live** (voir commits `fix: POC-001 ...`) :
  1. `is_logged_in` traitait la page d'accueil non connectée comme déjà authentifiée (absence de marqueur "login"/"authwall" dans l'URL) → fenêtre fermée avant la saisie du login. Corrigé : seule la redirection vers `/feed/` compte comme connecté.
  2. Course entre la confirmation du login (`input()`) et la navigation suivante, qui interrompait la navigation vers la recherche (`interrupted by another navigation to /login/fr`). Corrigé : attente explicite de `/feed/` avec plusieurs tentatives avant d'abandonner avec un message clair.
  3. Sélecteurs CSS obsolètes (`reusable-search__*`, `entity-result__*`) : LinkedIn utilise désormais des classes hashées régénérées à chaque déploiement → 0 profils extraits malgré des résultats visibles. Diagnostiqué via un dump HTML d'une vraie page de résultats (session utilisateur, une seule requête ponctuelle). Corrigé avec des attributs structurels stables : `role="listitem"`/`role="list"` pour les cartes, ancre imbriquée dans un `<p>` pour le nom, traversal XPath pour titre/localisation, `data-testid="pagination-controls-next-button-visible"` pour la pagination (remplace l'ancien `aria-label` dépendant de la langue).
- **Run réel validé** (03/07/2026, `MAX_PROFILES=5`) : 5 profils cohérents extraits (noms, URLs, localisations, titres de coachs conformes à la requête), aucun blocage/restriction de compte constaté.
- `MAX_PROFILES` remonté à **25** dans `run_poc001.py` pour le test final du critère d'acceptation.
- Points de vigilance restants : les sélecteurs XPath pour titre/localisation supposent une structure à 3 `<p>` fixe (nom, titre, localisation) dans le bloc info de la carte — un profil qui n'affiche pas l'un de ces champs peut décaler l'extraction des champs suivants (dégrade vers `""`, ne fait pas planter le run).
- Lancement de l'app **non nécessaire** : aucun fichier `frontend_streamlit/` touché.
- **Run final validé (04/07/2026, `MAX_PROFILES=25`)** : 25 profils cohérents extraits (noms, URLs, localisations, titres tous liés au coaching professionnel), export CSV vérifié par script (4 colonnes attendues, aucun nom/URL vide, aucune URL avec résidu de query string, aucune colonne email). Aucun blocage/restriction de compte constaté ; l'utilisateur a enregistré ce run (OBS) comme démo pour Henri-Pierre Michaud et Christophe Hoffsteter (client D'un Pas Décidé).
- **POC-001 → DONE.** Tous les critères d'acceptation sont remplis.
- Prochain ticket : **POC-002** — Extraction de l'email depuis la page profil individuelle (hors scope POC-001, décision du 02/07/2026 dans Backlog.md). Prompt préparé dans `document/prompts_plans/prompt_POC-002.md`.
