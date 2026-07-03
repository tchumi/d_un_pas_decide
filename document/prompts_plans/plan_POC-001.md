# Plan — POC-001 : Script de recherche + extraction basique de profils LinkedIn

Validé le 03/07/2026.

## Décisions issues des échanges de cadrage

- `MAX_PROFILES` par défaut = **5** pour la première phase de test/debug (au lieu de 20-25) — décision explicite de l'utilisateur pour ne prendre aucun risque de blocage de compte lors des premiers runs. Le paramètre reste configurable ; passer à 20-25 se fait sans changement de code une fois le comportement validé sans risque.
- Requête booléenne de test = celle de la spec : `("coach business" OR "coach professionnel" OR "coach entreprise") AND (France) NOT ("life coach" OR "sportif")`.
- Compte LinkedIn de test = compte personnel de l'utilisateur (connexion manuelle dans la fenêtre Playwright).
- `.env.local` créé avec placeholders `LINKEDIN_EMAIL` / `LINKEDIN_PASSWORD` à remplir manuellement par l'utilisateur (non lu par le code dans ce ticket — login manuel uniquement, session persistée localement).
- Ajout de `browser_profile/` au `.gitignore` (hors périmètre listé initialement, ajouté sur validation explicite) : ce dossier contient le profil navigateur complet (cookies de session LinkedIn incluse) créé par `launch_persistent_context`, aucun pattern existant du `.gitignore` ne le couvrait.

## Fichiers créés

```
pyproject.toml
source/backend/__init__.py
source/backend/adapters/__init__.py
source/backend/adapters/scraping/__init__.py
source/backend/adapters/scraping/selectors.py
source/backend/adapters/scraping/browser_session.py
source/backend/adapters/scraping/profile_search.py
source/backend/adapters/scraping/run_poc001.py         # script exécutable, assemble les modules ci-dessus
source/backend/adapters/storage/__init__.py
source/backend/adapters/storage/csv_export.py
tests/unit/__init__.py
tests/unit/test_csv_export.py
tests/unit/test_profile_search.py
.env.local                                              # placeholders, non commité
.gitignore                                              # ajout de browser_profile/
```

## Risque principal

Fragilité des sélecteurs CSS LinkedIn (nom, pagination dépendante de la langue du compte) — le DOM change régulièrement, rien ne garantit leur validité au moment du test réel. Risque secondaire : blocage/restriction de compte si le rythme n'est pas assez "humain" — mitigé par `MAX_PROFILES=5` et les pauses aléatoires conservées du script d'inspiration.

## Tests

- Unitaires (CI-safe, sans navigateur) : `build_search_url`, `clean_profile_url` (logique pure de `profile_search.py`), export CSV (`csv_export.py`) — 4 champs attendus, absence d'email, gestion des accents.
- Non testable en CI : extraction réelle depuis une page LinkedIn live (nécessite navigateur + session + compte réel) — vérification manuelle par l'utilisateur avec son compte personnel.

## Ce qui reste hors de ce ticket / à valider manuellement

- Lancer réellement `run_poc001.py`, se connecter manuellement, vérifier l'extraction sur ≥ 20-25 profils sans blocage de compte (critère d'acceptation non vérifiable par l'agent).
- Extraction d'email : hors scope (ticket séparé).
- Scoring/catégorisation : hors scope (Phase 2).
