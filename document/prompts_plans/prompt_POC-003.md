Tu travailles dans le repo ProspectionLinkedIn avec Claude Code dans VS Code.

Je viens de faire un /clear pour réduire le contexte. Tu dois reprendre proprement à partir de la documentation projet, mais sans relire tout le repository.

## Ticket à traiter

Ticket : POC-003
Titre : Scoring et catégorisation des profils (Phase 2)
Objectif : Catégoriser chaque profil déjà extrait et lui attribuer un score de
pertinence, à partir du CSV existant — **sans aucune nouvelle extraction LinkedIn**.

**Ce ticket n'est plus BLOCKED** (requalifié le 25/08/2026, statut `TODO` / P1 dans
`task_list.md`). Une version antérieure de ce prompt indiquait le contraire : elle est
caduque, ne pas en tenir compte si elle traîne dans un contexte. Le déblocage vient de la
relecture des mails client des 08 et 13/07/2026, reportés dans `Backlog.md` :

* la calibration bon/mauvais est couverte (validation en bloc du CSV de démo par le
  client, plus une exclusion explicite) ;
* le vocabulaire de la catégorie outdoor a été fourni ;
* le client a explicitement priorisé ce ticket le 13/07/2026.

**Périmètre volontairement réduit** : la distinction *débutant / expérimenté* est
**hors scope** — elle n'est pas décidable depuis le titre LinkedIn (seul signal textuel
disponible), elle demanderait d'extraire la durée d'expérience de la page profil, et
elle attend une réponse d'Henri-Pierre Michaud. Ces profils sortent en
`indifférencié`, ce qui est le repli explicitement annoncé par le client le 04/07/2026.

Critère d'acceptation (mesurable sur le lot de 25 profils réels de `profils_extraits.csv`,
que le client a lui-même étiqueté dans son mail du 08/07/2026) :

1. Cécile Pollin ("HR Senior Manager - Responsable RH Senior - Transformation") est
   **exclue** (pas un coach — faux positif de la recherche booléenne).
2. Anne-Laure F. ("Coach en développement personnel, professionnel et scolaire...") est
   **conservée mais classée sous la médiane** des scores (acceptable, moins intéressante).
3. Les 23 autres profils sont **conservés** (le client les a validés en bloc comme de
   "bons" coach business).
4. Chaque profil sort avec : `categorie`, `score`, `justification` (les règles ayant
   matché — le client a demandé cette colonne le 04/07/2026).
5. Tests unitaires passants, sans navigateur ni appel réseau.

La branche attendue est `master` (**35 tests passants**, 0 échec, 0 skipped à l'issue de
POC-004).

## Décision d'architecture déjà prise (ne pas la rouvrir sans raison)

**Scoring 100 % déterministe, zéro appel LLM** — cohérent avec le précédent POC-004
(pipeline v1 déterministe, paliers LLM conditionnels et non activés), et justifié
spécifiquement ici : le client demande une colonne `justification` à côté du score. Un
moteur de règles la produit par construction et elle est vérifiable ; un LLM la génère,
et elle ne l'est pas.

Signaux disponibles dans le CSV d'entrée : `nom`, `url`, `localisation`, `titre`. Le
`titre` est le seul signal textuel exploitable.

Éléments de calibration à utiliser (source : `Backlog.md`, section POC-003) :

* **Catégorie outdoor**, mots-clés fournis par le client : *coach nature*, *coach qui
  marche*, *coach outdoor*, *coach hors-les-murs*, *coaching en itinérance*.
* **Exclusion** : absence de marqueur "coach" dans le titre (cas Cécile Pollin).
* **Malus sans exclusion** : "développement personnel", "scolaire" (cas Anne-Laure F.).

## Risque principal à garder en tête

Calibrer les règles sur les 25 profils qui servent aussi de jeu de référence, c'est du
sur-mesure sur un échantillon minuscule. Ça ne se corrige pas par de la technique :
garder les règles **simples, peu nombreuses et lisibles**, ne pas empiler des cas
particuliers pour faire passer le critère d'acceptation, et documenter que la
revalidation devra se faire sur un lot fraîchement extrait.

## Périmètre autorisé

* `source/backend/core/` — nouveau module de scoring/catégorisation, logique pure, **zéro
  import Streamlit** (voir CLAUDE.md), zéro import Playwright, zéro appel réseau
* `source/backend/adapters/storage/csv_export.py` — ajout des colonnes `categorie`,
  `score`, `justification` (même pattern `restval=""` que `email` en POC-002 et
  `email_web`/`site_web` en POC-004)
* un script d'assemblage dédié dans le même esprit que `run_poc001.py` / `run_poc004.py`
  (lecture du CSV existant → scoring → export), à nommer selon la convention en place
* `tests/unit/` — tests de la logique de scoring (pure, sans navigateur)

Hors périmètre :
* **aucune nouvelle extraction / scraping LinkedIn** — on réutilise `profils_extraits.csv` ;
* pas d'appel LLM, pas de nouvelle dépendance ;
* pas de distinction débutant/expérimenté (voir plus haut) ;
* pas de refactoring global, pas de changement d'architecture, pas de renommage de module ;
* pas de suppression de fichier ;
* pas de modification de secrets ou fichiers sensibles.

## Point d'architecture à intégrer au cadrage (sans le coder maintenant)

Décision client du 13/07/2026 : l'enrichissement web (POC-004) **cesse d'être une étape
systématique** du pipeline et devient une étape **conditionnelle appliquée après le
scoring**, aux seuls profils jugés intéressants. Le code POC-004 reste en place et
fonctionnel ; c'est sa position dans la chaîne qui change. À prendre en compte dans la
façon dont le module de scoring expose son résultat (il doit permettre de sélectionner
un sous-ensemble "intéressant" en aval), **sans modifier POC-004 dans ce ticket**.

## Documents à lire en premier

Lis uniquement ces fichiers au démarrage :

1. `CLAUDE.md`
2. `document/claude_code/AGENTS.md`
3. `document/Backlog.md` — sections `## POC-003` (calibration client, décisions) et les
   décisions du 13/07/2026 de la section `## POC-004`
4. `document/claude_code/task_list.md` — ligne POC-003
5. `document/claude_code/handoff.md` — dernière section uniquement
6. `source/backend/adapters/storage/csv_export.py` — pattern d'export existant à suivre

Ne lis pas tout le repo.

Note : `profils_extraits.csv` (25 profils, entrée de ce ticket) est présent localement
mais **gitignoré** (données personnelles) — il n'est pas dans l'historique Git.

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
* vérifie la présence et le format de `profils_extraits.csv` (25 lignes + en-tête,
  colonnes `nom,url,localisation,titre`) ;
* ne modifie aucun fichier.

Étape 2 — Plan court :
Réponds d'abord avec :
1. résumé du ticket en 5 lignes maximum ;
2. fichiers à créer ou modifier ;
3. règles de scoring proposées (liste explicite, avec les poids/seuils envisagés) ;
4. tests prévus, dont les 3 cas du critère d'acceptation (Cécile Pollin exclue,
   Anne-Laure F. sous la médiane, 23 profils conservés) ;
5. plan en 3 à 5 étapes ;
6. questions bloquantes éventuelles (ex : seuil d'exclusion, échelle du score,
   comportement sur un titre vide).

Sauvegarde le plan validé dans `document/prompts_plans/plan_POC-003.md` et commit
(`docs: POC-003 plan — description courte`).

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
uv run --extra test pytest tests/unit/ -v
```

```powershell
uv run --extra test pytest tests/ --collect-only -q
```

Puis exécuter le scoring sur le CSV réel et **relire le classement avec moi** : le
critère d'acceptation porte sur des profils réels nommés, pas seulement sur des tests
synthétiques.

Étape 5 — Fin de session (OBLIGATOIRE) :
* `document/Backlog.md` — section POC-003 : specs et critères d'acceptation définitifs,
  décisions prises, résultat de la relecture du classement ;
* `document/claude_code/task_list.md` : POC-003 → DONE avec métriques (nb tests) ;
* `document/claude_code/handoff.md` : nouvelle section (ce qui a été fait, fichiers
  modifiés, prochain ticket) ;
* sauvegarder le prompt du prochain ticket dans
  `document/prompts_plans/prompt_[NEXT_TICKET].md` ;
* commit : `git commit -m "docs: POC-003 DONE — description courte"`.

Indiquer explicitement si le lancement de l'application est nécessaire (a priori **non** :
aucun fichier `frontend_streamlit/` touché).

## Suite attendue après ce ticket (contexte, à ne pas traiter ici)

Une fois le CSV scoré disponible, il servira de support à la reprise de contact client
(silence depuis le 13/07/2026), avec deux questions ouvertes à poser : la nuance
débutant/expérimenté (adressée à Henri-Pierre Michaud) et l'arbitrage sur l'extraction de
la durée d'expérience depuis la page profil.

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
3. vérifier le CSV d'entrée ;
4. proposer un plan court et attendre ma validation.
