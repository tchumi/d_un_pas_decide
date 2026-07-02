# AGENTS.md — Règles de travail IA pour [PROJECT_NAME]

## 1. Cadre de travail

- [Documentation] Objectif du repo : [PROJECT_DESCRIPTION]
- [Code] Le code applicatif est dans `source/` ; les tests dans `tests/` ; la documentation dans `document/`.
- [Code] Le point d'entrée desktop est `source/main.py`.
- [Règle] Vérifier la branche active au démarrage : `git branch --show-current`. Si la branche n'est pas `[BRANCHE_BASE]`, le signaler et attendre validation.
- [Documentation] Le backlog produit est dans `document/Backlog.md`. À lire avant tout développement pour ne pas réimplémenter l'existant ni ignorer les contraintes en cours.
- [Inférence] Toute reprise par agent doit considérer la documentation existante comme potentiellement partielle et vérifier dans le code avant d'agir.

## 2. Discipline agent IA

- [Règle] Plan d'abord, diff ensuite : proposer un plan court avant toute modification de code.
- [Règle] Pour une modification non triviale, indiquer les fichiers cibles, le risque, les tests prévus et les points ouverts.
- [Règle] Ne modifier un fichier qu'après avoir lu son contexte local et les appels entrants/sortants.
- [Règle] Chaque affirmation structurante doit être rattachée au code [Code], à la documentation [Documentation] ou à une inférence [Inférence].
- [Règle] Ne jamais exposer de secret, clé API, fichier `.env` ou mot de passe.
- [Règle] Ne pas modifier `.env`, fichiers de secrets, bases de données de production sans demande explicite.

## 3. Interdictions

- [Règle] Pas de refactoring global.
- [Règle] Pas de renommage de module.
- [Règle] Pas de changement d'architecture sans validation humaine.
- [Règle] Pas de suppression de fichiers.
- [Règle] Pas de migration schéma/base de données sans plan validé et backup explicite.
- [Règle] Pas de correction silencieuse de données métier sensibles : signaler les anomalies et demander validation.

## 4. Conventions de code

- [Code] Architecture visée : séparation `frontend_qt/`, `backend/core/`, `backend/adapters/`.
- [Règle] Respecter les imports `source.` existants.
- [Règle] Garder les commentaires de code en anglais.
- [Règle] Éviter les chemins hardcodés ; passer par le gestionnaire de workspace ou les helpers existants.
- [Règle] PyQt6 uniquement dans `frontend_qt/` — zéro import PyQt6 dans les modules `core/` ou `adapters/`.

## 5. Règles Git

- [Règle] Lire `git status --short` avant toute modification.
- [Règle] Ne jamais revenir sur des changements non faits par l'agent.
- [Règle] Pas de `git reset --hard` ni de checkout destructif.
- [Règle] Commits conventionnels : `docs:`, `fix:`, `feat:`, `test:`, `refactor:`, `chore:`.
- [Règle] Ne pas amender un commit sans demande explicite.

## 6. Commandes essentielles

### Installation

```powershell
uv sync --extra gui --extra test
```

### Lancement desktop

```powershell
python source\main.py
```

### Lancement API (si applicable)

```powershell
python -m uvicorn source.backend.api.main:app --reload --host 127.0.0.1 --port 8000
```

### Tests

```powershell
pytest tests/ -v
pytest tests/unit/ -v
pytest tests/ --collect-only -q
pytest tests/ --cov=source --cov-report=html
```

## 7. Variables d'environnement

<!-- Lister ici les variables spécifiques au projet -->
- [Code] `[VAR_ENV_1]` : [description]
- [Code] `[VAR_ENV_2]` : [description]
- [Règle] Ne pas renseigner de valeur secrète dans la documentation ou dans Git.
