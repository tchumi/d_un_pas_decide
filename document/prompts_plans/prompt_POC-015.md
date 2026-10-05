Tu travailles dans le repo ProspectionLinkedIn avec Claude Code dans VS Code.

Je viens de faire un /clear pour réduire le contexte. Tu dois reprendre proprement à partir de la
documentation projet, mais sans relire tout le repository.

> Contexte de rédaction : prompt écrit le 05/10/2026 sur le **poste principal**, à la clôture de
> POC-014. L'itinérance est terminée ; les sauvegardes vont dans
> `D:\Documents\Dev\_backup_prospection\`.

## Ticket à traiter

Ticket : POC-015
Titre : Colonne département dans l'export
Objectif : Répondre à la suggestion du client du 11/09/2026 — « une nouvelle colonne numéro de
département ou nom du département serait la bienvenue » — pour lui permettre de **trier** le
classeur. La géographie reste un critère accessoire : on n'en fait ni un filtre ni un score. Cette
colonne est promise dans le prochain fichier envoyé (mail du 19/09/2026).

Critère d'acceptation :

- L'export (CSV et classeur xlsx) porte une colonne département, **dérivée de `localisation`** par
  une fonction pure et une table de correspondance statique versionnée.
- **Une localisation non rattachable donne une cellule vide, jamais une valeur devinée** (« France »,
  « Paris et périphérie »…). Le nombre de profils rattachés et non rattachés sur les 81 est publié.
- **La boucle de retour de POC-013 tient toujours** : un classeur exporté avec la nouvelle colonne,
  annoté puis ré-importé, ne modifie que `commentaire_client` et `statut_coordonnees`. Le sort d'un
  **ancien classeur** (sans la colonne) qui reviendrait est décidé et testé : refus explicite ou
  acceptation, mais pas d'échec silencieux.
- Les 81 `commentaire_client` sont intacts — vérifié contre une sauvegarde si le magasin est écrit.
- Tests : partir de **172 passed** et ne rien casser.

La branche attendue est `master` (172+ tests).

## Périmètre autorisé

* `source/backend/core/` — une fonction pure de dérivation du département (nouveau module) et sa
  table de correspondance (dans `config/` si elle est éditable, à l'image de `scoring_rules.json`).
* `source/backend/adapters/storage/csv_export.py` — `PROFILE_CSV_FIELDS` et l'export.
* `source/backend/adapters/storage/xlsx_export.py` — **seulement** ce qu'exige le contrôle d'en-tête.
* Tests unitaires de la dérivation, de l'export et de l'aller-retour xlsx.

Hors périmètre :
* tout filtrage ou découpage géographique de la collecte (POC-008) ;
* toute modification des règles de scoring (POC-014 est clos ; la v2 attend le prochain lot annoté) ;
* **toute migration de schéma sans plan validé et sauvegarde explicite** — la question « colonne
  dérivée à l'export ou stockée » est à trancher au plan, la dérivation à l'export étant l'option
  sans migration ;
* toute écriture dans `commentaire_client` ;
* pas de refactoring global, pas de renommage de module, pas de suppression de fichier, pas de
  modification de secrets ou fichiers sensibles.

## Documents à lire en premier

Lis uniquement ces fichiers au démarrage :

1. `CLAUDE.md`
2. `document/claude_code/AGENTS.md`
3. `document/claude_code/handoff.md` — la **dernière section** (n°15) et, dans la section 11
   (POC-013), ce qui concerne le contrôle d'en-tête et l'aller-retour Excel
4. `document/Backlog.md` — uniquement la section `## POC-015`
5. `document/claude_code/task_list.md` — lignes POC-015 et POC-013

Puis (OBLIGATOIRE avant d'écrire une ligne) :

* `source/backend/adapters/storage/csv_export.py` — `PROFILE_CSV_FIELDS`, `export_profiles_to_csv`
* `source/backend/adapters/storage/xlsx_export.py` — `_valider_entete`, `lire_xlsx`,
  `convertir_csv_en_xlsx`, `xlsx_vers_csv`
* `source/backend/adapters/storage/run_poc013.py` et `run_poc006.py` — le chemin d'export et de
  ré-import
* `source/backend/adapters/storage/profile_store.py` — **uniquement** `PROFILE_COLUMNS`,
  `lister_profils` et `importer_commentaires_csv`

Ne lis pas tout le repo.

## Faits vérifiés

* **[Documentation, mesuré le 16/09/2026]** `localisation` n'est pas homogène : 52 profils au format
  « Ville, Région, France », 28 en libellé unique (« Paris et périphérie », « Lille et périphérie »,
  « France ») dont une partie non rattachable, 1 en deux parties. À remesurer en lecture seule.
* **[Code]** `xlsx_export._valider_entete` **refuse** tout classeur dont l'en-tête n'est pas
  exactement `PROFILE_CSV_FIELDS`, dans l'ordre. Ajouter une colonne rend inimportables les
  classeurs déjà envoyés. Le retour du 11/09/2026 a été ré-importé avant ce ticket, pour cette raison.
* **[Code]** `source/backend/adapters/storage/run_poc014_evaluation.py` montre comment lire le
  magasin **en lecture seule** (`lire_profils_lecture_seule`, SQLite `mode=ro`).
* **État du magasin au 05/10/2026** : 81 profils, 81 commentaires client, `user_version` 2,
  empreinte MD5 `7bf1cbb0fa4d015ade51ab9a942e4f41` (après le re-scoring de POC-014).
* **`profils_magasin.xlsx` porte encore les scores v1** : il doit être régénéré par ce ticket, avec
  les scores v2 et la nouvelle colonne.

## Risque principal

Casser la boucle de retour client de POC-013 : une colonne ajoutée, mal placée ou réécrite par Excel
peut faire refuser le prochain classeur annoté — ou pire, faire entrer en base une colonne dérivée
comme si elle venait du client. Second risque : deviner un département (une ville homonyme, une
« périphérie ») au lieu de laisser la cellule vide.

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
* lis ensuite uniquement les fichiers de code nécessaires au ticket ;
* identifie les appels entrants/sortants des fonctions concernées ;
* vérifie le magasin **en lecture seule** (comptages, empreinte) et mesure la répartition des
  formats de `localisation` ;
* ne modifie aucun fichier.

Étape 2 — Plan court :
Réponds d'abord avec :
1. résumé du ticket en 5 lignes maximum ;
2. fichiers à lire ou modifier ;
3. risque principal ;
4. tests prévus ;
5. plan en 3 à 5 étapes ;
6. questions bloquantes éventuelles, dont : numéro, nom ou les deux ; colonne dérivée à l'export ou
   stockée ; position de la colonne ; sort d'un ancien classeur sans la colonne ; origine de la
   table commune → département (aucun appel réseau à l'exécution).

Attends ma validation avant toute modification. Puis sauvegarde le plan dans
`document/prompts_plans/plan_POC-015.md` et committe
(`git commit -m "docs: POC-015 plan — description courte"`).

Étape 3 — Implémentation contrôlée :
Après validation :
* applique uniquement l'étape validée ;
* fais un petit diff ;
* évite toute modification opportuniste ;
* explique le diff ;
* lance uniquement les tests ciblés.

Étape 4 — Vérification :
```powershell
uv run --extra test pytest tests/unit/test_csv_export.py tests/unit/test_xlsx_export.py -v
uv run --extra test pytest tests/ -q
```

```powershell
uv run --extra test pytest tests/ --collect-only -q
```

Puis, sur les données réelles : régénération du CSV et du classeur, comptage des départements
rattachés et vides, contrôle de l'aller-retour xlsx. Sauvegarde datée avant toute écriture dans le
magasin.

Étape 5 — Fin de session (OBLIGATOIRE) :
* `document/Backlog.md` — section POC-015 : décisions, couverture mesurée, limites ;
* `document/claude_code/task_list.md` : POC-015 → DONE avec métriques ;
* `document/claude_code/handoff.md` : nouvelle section (ce qui a été fait, fichiers modifiés, prochain ticket) ;
* `CLAUDE.md` — section « État actuel » : dernière session (ID + date) et prochain ticket actif,
  **deux lignes, aucune métrique** (elles vivent dans `task_list.md`) ; compléter aussi « Structure
  du repository » si un dossier a été créé ;
* sauvegarder le prompt du prochain ticket (POC-008) dans `document/prompts_plans/prompt_POC-008.md` ;
* commit : `git commit -m "docs: POC-015 DONE — description courte"`.

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
