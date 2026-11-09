Tu travailles dans le repo ProspectionLinkedIn avec Claude Code dans VS Code.

Je viens de faire un /clear. Tu reprends **POC-016 à l'étape 7, runs de lecture suivants**. Ne relis
pas tout le repository.

## Ticket à traiter

Ticket : POC-016
Titre : Extraction des rubriques « Expérience » et « Infos » — étape 7, runs suivants
Objectif : poursuivre la lecture des profils non lus (5/131 lus le 09/11), palier 10 puis 20, lot 1
(81) d'abord puis les 50 du 07/10, avec sauvegarde et contrôle à chaque run.

Critères (étape 7) : inchangés, voir `plan_POC-016.md`, « Étape 7 ». Le code est fait et a tourné en
réel une fois (5 lus, 0 vide).

La branche attendue est `master` (329 tests).

## Périmètre autorisé

* `source/backend/adapters/scraping/run_poc002.py` (constante `MAX_PROFILES` seulement, sauf
  anomalie argumentée)
* lecture seule du magasin pour le lot nominatif et le contrôle

Hors périmètre : signaux et verdict (étape 8), évaluateur (étape 9), `config/scoring_rules.json`,
exports, toute écriture de `commentaire_client`.

## Documents à lire en premier

1. `CLAUDE.md`
2. `document/prompts_plans/plan_POC-016.md` — « Étape 7 »
3. `document/claude_code/handoff.md` — section 23

## État vérifié au 09/11/2026

* Tests : **329 passed**.
* Magasin : 131 profils, 5 lus, 131 commentaires, `user_version` 3, empreinte
  `0c7d96bbcd130f9c01d83d33b81b504c`.
* Lancements du 09/11 : 2 sur 2.

## Interdit

* lancer soi-même un run LinkedIn réel ;
* lancer un run qui écrit le magasin sans sauvegarde datée du magasin et de `journal_collecte.csv`
  juste avant ;
* écrire dans `commentaire_client` ; modifier `config/scoring_rules.json` ;
* contourner une page de blocage ; plus de 2 lancements par jour.

## Rappels

* Runs lancés par l'utilisateur : sauvegarde, lot nominatif, commande, sortie collée, contrôle
  ligne à ligne contre la sauvegarde (`mode=ro`), `commentaire_client` compris.
* Lister les sauvegardes contenant du texte brut (étape 11).
* Réponses en français, commentaires de code en anglais, affirmations taguées
  [Code] / [Documentation] / [Inférence].

## Première réponse attendue

Ne modifie aucun fichier. Vérifie la branche, l'état Git, la suite de tests (329) et l'empreinte du
magasin. Propose le passage au palier 10 (commit), la sauvegarde et le lot nominatif, et attends la
validation.
