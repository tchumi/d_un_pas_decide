# ARCHITECTURE.md — ProspectionLinkedIn

> Dernière mise à jour : 02/07/2026

## Stack technique

| Composant | Technologie | Version |
|---|---|---|
| UI | Streamlit | — |
| Scraping | Playwright | — |
| Base de données | SQLite | — |
| Traitement données / export | pandas | — |
| ORM | N/A (sqlite3 stdlib, pas d'ORM en POC) | — |
| Migration schéma | N/A (pas de migration prévue en POC) | — |
| API interne | N/A (pas d'API en Phase 1) | — |
| Gestionnaire de paquets | uv | — |

## Arborescence réelle

```
source/
  main.py                    # point d'entrée Streamlit (streamlit run)
  frontend_streamlit/        # pages/composants Streamlit — présentation uniquement
  backend/
    core/                    # scoring, catégorisation, modèles métier — zéro import Streamlit/Playwright
    adapters/
      scraping/               # Playwright, sélecteurs CSS LinkedIn centralisés, session
      storage/                # SQLite / export CSV
tests/
  unit/
  integration/
  e2e/
document/
  claude_code/
  prompts_plans/
```

## Modules actifs

| Module | Chemin | Rôle |
|---|---|---|
| — | — | Aucun module implémenté à ce stade (POC-001 en cours) |

## Contraintes d'architecture

- Zéro import Streamlit dans `backend/core/` et `backend/adapters/` — permet de remplacer l'UI (ex: desktop) sans toucher au backend.
- Les services `core/` sont testables sans Streamlit ni Playwright.
- Sélecteurs CSS LinkedIn centralisés et isolés (le DOM LinkedIn change régulièrement) — jamais dispersés dans le code.
- Pas d'envoi de message ni d'invitation automatisée (lecture seule uniquement) à ce stade.
- Volume cible faible : ~50 profils qualifiés/semaine en sortie, quelques centaines de profils scrapés/semaine maximum — ne pas optimiser pour un volume supérieur sans validation explicite du client.
- Identifiants LinkedIn (`LINKEDIN_EMAIL`/`LINKEDIN_PASSWORD`) dans `.env.local` (non commité), jamais en dur dans le code ; session persistée localement.

## Décisions d'architecture

| Date | Décision | Alternatives rejetées |
|---|---|---|
| 02/07/2026 | Streamlit retenu pour l'UI, avec isolation stricte frontend/backend (zéro import Streamlit dans `core/`/`adapters/`) pour permettre une UI desktop en remplacement futur | CLI pur (moins ergonomique pour piloter/visualiser les résultats) ; PyQt6 desktop d'emblée (proposé par le template, pas nécessaire en Phase 1 POC) |
