Tu travailles dans le repo ProspectionLinkedIn avec Claude Code dans VS Code.

Je viens de faire un /clear pour réduire le contexte. Tu dois reprendre proprement à partir de
la documentation projet, mais sans relire tout le repository.

## Ticket à traiter

Ticket : POC-007
Titre : Revalidation des règles de scoring POC-003 sur le lot frais
Objectif : Statuer sur le **sur-apprentissage** des 6 règles de `config/scoring_rules.json`,
calibrées sur les 25 profils qui servaient aussi de jeu de référence, en les confrontant aux
**50 profils frais** extraits le 26/08/2026 par POC-006.

Statut : `TODO` / **P1** dans `task_list.md`. Ticket créé le 26/08/2026 à la clôture de
POC-006 : le cadrage détaillé est à faire dans ce ticket.

**Pourquoi maintenant** : c'est la réserve n°1 de POC-003, et la raison d'être explicite de
l'enchaînement POC-003 → POC-006. Le jeu de contrôle qui manquait existe désormais.

## État de départ (vérifié le 26/08/2026, ne pas le refaire de zéro)

1. [Code] Le magasin `profils.db` contient **75 profils, tous scorés** : 25 datés du
   03/07/2026 (lot POC-001, jeu de calibration des règles) et **50 datés du 26/08/2026, le
   lot frais** jamais vu par les règles au moment de leur écriture.
2. [Code] `run_poc003` a été lancé le 26/08/2026 à la clôture de POC-006 : le lot à analyser
   **existe déjà**, dans le magasin et dans `profils_extraits_scores.csv` (75 lignes).
   Le scoring est donc *calculé* — ce ticket porte sur son **analyse**, pas sur son
   exécution. Ne pas confondre : un moteur qui note bien les données sur lesquelles il a
   été réglé ne prouve rien.
3. [Code] Premier signal déjà mesuré : **1 exclu sur 25 en juillet, 2 exclus sur 50 en
   août** — taux d'exclusion quasi identique. Indicateur trop grossier pour conclure : il
   ne dit rien de la dispersion des scores conservés, où le sur-apprentissage se voit.
4. [Documentation] Distribution de référence, lot de juillet : 24 conservés, 1 exclu, médiane
   des conservés = 75, 21 profils au-dessus du seuil « intéressant » (60).

## Périmètre autorisé

* `config/scoring_rules.json` — ajustement des poids, des mots-clés ou ajout d'une règle, **si
  et seulement si** l'analyse du lot frais le justifie ;
* `tests/unit/test_profile_scoring.py` — tout ajustement de règle doit être couvert ;
* `document/` — Backlog, task_list, handoff.

Hors périmètre :
* pas de modification du magasin ni du scraping (POC-006 est clos) ;
* pas de nouvelle extraction LinkedIn (le lot frais est déjà en base) ;
* la diversification des requêtes, qui est POC-008 ;
* pas de refactoring de `core/profile_scoring.py` : le moteur n'est pas en cause, seules ses
  **règles** sont à revalider.

## Méthode attendue

Étape 1 — **Déjà faite** (26/08/2026) : le lot scoré existe. La relancer n'est utile que si
`config/scoring_rules.json` est modifié en cours de ticket — `run_poc003` réécrit alors les
colonnes de scoring en base et l'export.

Étape 2 — **Comparer les deux distributions** (25 de juillet vs 50 d'août) : nombre de
conservés/exclus, médiane, répartition par catégorie, nombre au-dessus du seuil. [Inférence]
Une distribution nettement plus basse sur le lot frais signerait le sur-apprentissage ; une
distribution comparable validerait les règles.

Étape 3 — **Relecture humaine d'un échantillon** avec moi, en particulier les profils exclus et
ceux qui sont juste sous le seuil. Distinguer ce qui relève d'un poids mal réglé de ce qui
relève d'une règle manquante. Ne rien ajuster sans validation.

Étape 4 — Ajustements éventuels dans `config/scoring_rules.json` + tests, puis relancer le
scoring et vérifier que le lot de juillet ne se dégrade pas (non-régression sur les 3 critères
d'acceptation client de POC-003 : Cécile Pollin exclue, Anne-Laure F. conservée sous la médiane,
les 23 autres conservés).

## Points d'attention

* [Inférence] La catégorie `coach_outdoor` sera **probablement encore absente** du lot frais :
  la requête utilisée ne contient aucun mot-clé outdoor. Son absence ne devra donc **pas** être
  interprétée comme une validation de la règle, seulement comme une non-observation. C'est
  POC-008 qui la rendra observable.
* **Deux `commentaire_client` fictifs** sont peut-être encore en base (Alain MASSON, Cécile
  Pollin), écrits par l'agent pendant la vérification de l'aller-retour POC-006. Vérifier et
  demander avant de les effacer — ce ne sont pas des retours du client.
* `profils.db` est **local et gitignoré**, sans sauvegarde. Ne rien y faire de destructif.
* Le seuil « intéressant » est à 60, avec deux profils pile dessus (arbitrage POC-003 accepté) —
  le lot frais est l'occasion de revalider ce seuil, pas seulement les règles.

## Documents à lire en premier

Lis uniquement ces fichiers au démarrage :

1. `CLAUDE.md`
2. `document/claude_code/AGENTS.md`
3. `document/Backlog.md` — sections `## POC-007` et `## POC-003` (réserves et critères client)
4. `document/claude_code/task_list.md` — lignes POC-003 et POC-007
5. `document/claude_code/handoff.md` — dernière section uniquement (POC-006)
6. `config/scoring_rules.json`
7. `source/backend/core/profile_scoring.py`

Ne lis pas tout le repo.

## Branche et sécurité Git

```powershell
git status --short
git branch --show-current
```

La branche attendue est `master`. Ne change pas de branche sans validation humaine. Ne fais
jamais : `git reset --hard` ; checkout destructif ; suppression de fichiers ; amend de commit ;
modification de fichiers non liés au ticket.

## Contraintes de style

* Réponses en français.
* Commentaires de code en anglais.
* Toute affirmation importante taguée [Code] / [Documentation] / [Inférence].
* Ne corrige jamais silencieusement une donnée métier sensible.

## Première réponse attendue

Ne modifie aucun fichier. Commence par : (1) vérifier la branche et l'état Git ; (2) lire les
fichiers listés → résumer le ticket ; (3) produire le lot scoré et présenter la **comparaison
des deux distributions** ; (4) proposer un plan court et attendre ma validation avant tout
ajustement de règle.
