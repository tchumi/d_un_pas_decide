Tu travailles dans le repo ProspectionLinkedIn avec Claude Code dans VS Code.

Je viens de faire un /clear pour réduire le contexte. Tu dois reprendre proprement à partir de la documentation projet, mais sans relire tout le repository.

## Ticket à traiter

Ticket : POC-001
Titre : Script de recherche + extraction basique de profils LinkedIn
Objectif : Valider que le scraping LinkedIn via Playwright permet de rechercher des profils
selon une requête booléenne définie manuellement, et d'extraire de façon fiable nom, URL
LinkedIn, localisation et titre/résumé — sur un petit lot de test (20-25 profils), sans
déclencher de blocage ou restriction du compte. L'email est explicitement hors scope
(reporté à un ticket séparé).

Critère d'acceptation :
- Script fonctionnel qui extrait au moins 20-25 profils cohérents sur une requête booléenne donnée
- Aucun blocage/restriction du compte LinkedIn constaté pendant les tests
- Sélecteurs CSS LinkedIn documentés et isolés dans un module dédié (facilite la maintenance si le DOM change)
- Export CSV propre avec les champs : nom, URL, localisation, titre/résumé (sans email)
- Session LinkedIn persistée localement ; identifiants (`LINKEDIN_EMAIL`/`LINKEDIN_PASSWORD`) dans `.env.local`, jamais en dur dans le code ; connexion initiale manuelle (pas de remplissage automatique du login)

La branche attendue est `master` (0 tests actuellement — aucun code source n'existe encore, ce ticket crée le squelette initial).

## Périmètre autorisé

* `pyproject.toml` — création (dépendances : playwright, pandas, streamlit, pytest)
* `source/backend/adapters/scraping/` — nouveau module : recherche + extraction Playwright, sélecteurs CSS centralisés dans un fichier dédié (ex. `selectors.py`), login manuel + session persistée
* `source/backend/adapters/storage/` — nouveau module : export CSV
* `.env.local` — nouveau (non commité, déjà couvert par `.gitignore`)
* `tests/unit/` — tests ciblés sur les modules ci-dessus (logique pure testable sans navigateur réel ; le scraping live reste vérifié manuellement, pas en CI)

Hors périmètre :
* pas de refactoring global ;
* pas de changement d'architecture ;
* pas de renommage de module ;
* pas de suppression de fichier ;
* pas de modification de secrets ou fichiers sensibles ;
* pas d'extraction d'email (ticket séparé) ;
* pas de scoring/catégorisation (Phase 2) ;
* pas d'UI Streamlit dans ce ticket (le module scraping/storage doit rester utilisable en standalone, sans dépendre de `frontend_streamlit/`).

## Documents à lire en premier

Lis uniquement ces fichiers au démarrage :

1. `CLAUDE.md`
2. `document/claude_code/AGENTS.md`
3. `document/claude_code/handoff.md` — section 1 (initialisation projet)
4. `document/Backlog.md` — uniquement la section `## POC-001`
5. `document/claude_code/task_list.md` — ligne POC-001

Puis (OBLIGATOIRE avant d'écrire une ligne) :
* `document/spec/spec_onboarding_prospection_linkedin.md` — spec complète du POC
* `document/spec/linkedin_search_poc.py` — script d'inspiration (diagnostic déjà fait, voir décisions `## POC-001` dans `Backlog.md` : sélecteurs non isolés, login `input()` incompatible Streamlit, pagination dépendante de la langue du compte, sélecteur de nom fragile)
* `document/ARCHITECTURE.md` — arborescence cible et contraintes (zéro import Streamlit dans `core/`/`adapters/`)

Ne lis pas tout le repo.

## Branche et sécurité Git

```powershell
git status --short
git branch --show-current
```

La branche attendue est `master`. Ne change pas de branche sans validation humaine.

Ne fais jamais :
* git reset --hard ;
* checkout destructif ;
* suppression de fichiers ;
* amend de commit ;
* modification de fichiers non liés au ticket.

## Méthode obligatoire

Étape 1 — Lecture et diagnostic :
* lis les fichiers de documentation listés ;
* lis ensuite `document/spec/linkedin_search_poc.py` en détail (base de départ) ;
* identifie ce qui doit être repris tel quel vs refactoré (sélecteurs, login, pagination) ;
* ne modifie aucun fichier.

Étape 2 — Plan court :
Réponds d'abord avec :
1. résumé du ticket en 5 lignes maximum ;
2. fichiers à créer ou modifier ;
3. risque principal (ex : fragilité des sélecteurs LinkedIn, blocage de compte) ;
4. tests prévus (unitaires sur la logique pure ; note sur ce qui ne peut être testé qu'en conditions réelles) ;
5. plan en 3 à 5 étapes ;
6. questions bloquantes éventuelles (ex : requête booléenne exacte à utiliser, compte LinkedIn de test à connecter).

Attends ma validation avant toute modification.

Étape 3 — Implémentation contrôlée :
Après validation :
* applique uniquement l'étape validée ;
* fais un petit diff ;
* évite toute modification opportuniste ;
* explique le diff ;
* lance uniquement les tests ciblés.

Étape 4 — Vérification :
```powershell
pytest tests/unit/ -v
```

```powershell
pytest tests/ --collect-only -q
```

## Contraintes de style

* Réponses en français.
* Commentaires de code en anglais.
* Toute affirmation importante taguée [Code] / [Documentation] / [Inférence].
* Ne corrige jamais silencieusement une donnée métier sensible.

## Première réponse attendue

Ne modifie aucun fichier.

Commence par :
1. vérifier la branche et l'état Git ;
2. lire les fichiers listés → résumer le ticket ;
3. proposer un plan court ;
4. attendre ma validation.
