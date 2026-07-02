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
