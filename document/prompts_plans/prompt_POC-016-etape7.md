Tu travailles dans le repo ProspectionLinkedIn avec Claude Code dans VS Code.

Je viens de faire un /clear. Tu reprends **POC-016 à l'étape 7 : run de lecture**. Ne relis pas tout
le repository.

## Ticket à traiter

Ticket : POC-016
Titre : Extraction des rubriques « Expérience » et « Infos » — étape 7, run de lecture
Objectif : lire « Expérience » et « Infos » des 131 profils non opposés (lot 1 de 81 d'abord, puis
les 50 du 07/10), en une seule visite par profil, sans fenêtre « Coordonnées », et stocker texte et
date dans les colonnes v3.

Critère d'acceptation (étape 7) :
- `run_poc002` (mode normal) visite les profils **non lus** (`date_lecture_parcours` vide) et non
  opposés, lot 1 d'abord (`date_collecte` < 2026-10-07), sans filtre de seuil ;
- il lit les deux rubriques (`scroll_profile_page`, `extract_rubriques_from_profile_page`) et
  n'appelle plus la fenêtre « Coordonnées » (le code de l'email reste en place, non appelé) ;
- une fonction de `profile_store` écrit `texte_experience`, `texte_infos`, `date_lecture_parcours` ;
  **la date est posée même si les deux rubriques sont vides** ; aucune autre colonne touchée ;
- arrêt immédiat sur page de blocage (`page_bloquee`) : les profils déjà lus sont écrits, le reste
  non marqué ;
- `MAX_PROFILES` à 5 pour le premier run ; paliers 5, 10, 20 ; 2 lancements par jour au plus ;
- le texte n'entre dans aucun export (`PARCOURS_COLUMNS` hors `PROFILE_COLUMNS`, déjà testé).

La branche attendue est `master` (312 tests).

## Périmètre autorisé

* `source/backend/adapters/storage/profile_store.py` (écriture et sélection du parcours)
* `source/backend/adapters/scraping/run_poc002.py`
* `source/backend/adapters/scraping/profile_email.py` (lecture seule sauf nécessité argumentée)
* `tests/unit/test_profile_store.py`, `tests/unit/test_run_poc002.py`

Hors périmètre : signaux et verdict (étape 8), évaluateur (étape 9), `config/scoring_rules.json`,
exports, toute écriture de `commentaire_client`.

## Documents à lire en premier

1. `CLAUDE.md`
2. `document/prompts_plans/plan_POC-016.md` — section « Actualisation du 05/11/2026 » et
   « Étape 6 — Migration v3 »
3. `document/claude_code/handoff.md` — sections 21 et 22

Puis le code : `profile_store.py` (`PARCOURS_COLUMNS`, `_ecrire_coordonnees`, `profils_a_visiter`,
`lister_profils`), `run_poc002.py` en entier, `profile_email.py` (`scroll_profile_page`,
`extract_rubriques_from_profile_page`, `enrich_profiles_with_email`), et leurs tests.

## État vérifié au 09/11/2026

* Tests : **312 passed**.
* Magasin migré en v3 : 131 profils, 131 commentaires, colonnes v3 vides, `user_version` 3,
  empreinte MD5 `54179a0bd97e5f269b31e44fb5c79b1d`.
* Sauvegarde v2 : `D:\Documents\Dev\_backup_prospection\profils_v2_avant_migration_v3_2026-11-09.db`.

## Interdit

* lancer soi-même un run LinkedIn réel ;
* lancer un run qui écrit le magasin sans sauvegarde datée du magasin et de `journal_collecte.csv`
  juste avant ;
* écrire dans `commentaire_client` ; modifier `config/scoring_rules.json` ;
* contourner une page de blocage.

## Rappels

* Les runs réels sont lancés par l'utilisateur : préparer, montrer le lot nominatif, donner la
  commande, attendre la sortie collée ; contrôle des `commentaire_client` contre la sauvegarde après
  chaque run.
* Les sauvegardes contiendront désormais le texte brut : les lister, la suppression (étape 11) devra
  les couvrir.
* Réponses en français, commentaires de code en anglais, affirmations taguées
  [Code] / [Documentation] / [Inférence].

## Première réponse attendue

Ne modifie aucun fichier. Vérifie la branche, l'état Git, la suite de tests (312) et l'empreinte du
magasin. Propose le plan détaillé de l'étape 7 (fonction d'écriture, sélection, changements de
`run_poc002`, tests, procédure du premier run de 5), et attends la validation.
