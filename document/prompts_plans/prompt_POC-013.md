Tu travailles dans le repo ProspectionLinkedIn avec Claude Code dans VS Code.

Je viens de faire un /clear pour réduire le contexte. Tu dois reprendre proprement à partir de
la documentation projet, mais sans relire tout le repository.

> Contexte de rédaction : prompt écrit le 08/09/2026 depuis le **laptop en itinérance**, après
> réception du CR du call client du 04/09/2026. Le poste principal est **éteint** pour toute la
> durée du déplacement : la base du laptop est la seule copie qui vit. Voir
> `document/claude_code/prompt_reconciliation_retour.md` pour le retour.

## Ticket à traiter

Ticket : POC-013
Titre : Livrable Excel client et boucle de retour au format xlsx
Objectif : Honorer le point d'action n°1 du call du 04/09/2026 — livrer à Christophe et
Henri-Pierre un **tableau Excel** exploitable (tri, filtres) portant les colonnes de scoring et
la colonne `commentaire_client`, et **accepter en retour le fichier `.xlsx` annoté**, sans leur
demander de le reconvertir en CSV.

**Périmètre volontairement minimal (décision utilisateur du 08/09/2026 : « on reste simple »)** :

1. **Export** — *convertir le CSV existant, sans le modifier*. Le contenu, les 16 colonnes de
   `PROFILE_CSV_FIELDS` et leur ordre restent **strictement identiques**. Ce ticket ajoute une
   conversion en `.xlsx` ; il ne retouche ni le contenu de l'export, ni le scoring, ni les
   colonnes.
2. **Import** — la boucle de retour doit lire un `.xlsx`. C'est le pendant obligatoire : livrer
   de l'Excel et exiger du CSV au retour déplacerait la corvée de conversion chez le client,
   sur un Excel français où « enregistrer en CSV » produit précisément le fichier cassé que ce
   ticket vient d'éliminer.

Critère d'acceptation :

- **Aller-retour vérifié sur le magasin réel** (81 profils) : export CSV → conversion `.xlsx` →
  ouverture dans Excel → annotation de quelques `commentaire_client` → ré-import du `.xlsx` →
  commentaires en base, **et aucune autre colonne modifiée**, vérifié ligne à ligne contre une
  sauvegarde prise avant. C'est la vérification qui a fait la valeur de POC-006 et de POC-009 ;
  elle est ici **le** critère, parce que le risque du ticket n'est pas le code mais ce qu'Excel
  fait aux données en chemin.
- **Fidélité de la conversion** : le `.xlsx` produit contient exactement les mêmes lignes et les
  mêmes valeurs que le CSV source, en-tête compris et dans le même ordre. Un test d'aller-retour
  (CSV → xlsx → lignes relues) rend des dictionnaires **égaux** à ceux qu'aurait produits
  `csv.DictReader` sur le CSV d'origine.
- **Tout est relu en texte.** `csv.DictReader` rend des `str` ; openpyxl rend des `int`, des
  `float`, des `datetime` et des `None`. Le module de lecture doit ramener tout cela à des
  chaînes, et une cellule vide à `""`, sinon les comparaisons de `importer_commentaires_csv` et
  de `_importer_statut_coordonnees` ne se comportent plus comme avec un CSV. **C'est le risque
  principal du ticket.**
- **Un en-tête non conforme est signalé, jamais deviné.** Si le client insère, supprime ou
  réordonne une colonne, le ré-import doit le dire et s'arrêter plutôt que de mal apparier les
  valeurs — même exigence que les `statuts_refuses` de POC-009 : la donnée métier est chère, on
  ne la corrige pas en silence.
- Tests : partir de **123 passed** et ne rien casser.

La branche attendue est `master` (123 tests).

## Périmètre autorisé

* `source/backend/adapters/storage/xlsx_export.py` — **nouveau** : conversion CSV → xlsx, et
  lecture xlsx → `list[dict[str, str]]`.
* `source/backend/adapters/storage/run_poc006.py` — accepter un `.xlsx` en entrée, en plus du
  CSV, en s'appuyant sur l'extension du fichier.
* `source/backend/adapters/storage/run_poc013.py` — **nouveau**, si c'est le chemin retenu :
  petit script qui produit le `.xlsx` à partir de l'export CSV. Cette option laisse les quatre
  `run_pocNNN.py` existants **intacts**, ce qui est le plus petit rayon d'action possible.
* `pyproject.toml` — dépendance de lecture/écriture xlsx.
* `tests/unit/test_xlsx_export.py` — **nouveau** ; compléments éventuels dans
  `tests/unit/test_profile_store.py`.

Hors périmètre :
* **toute modification du contenu de l'export** : pas de colonne ajoutée, retirée, renommée ni
  réordonnée, pas de valeur reformatée — c'est le sens de « convertir sans modifier » ;
* mise en forme Excel (largeurs de colonnes, filtre automatique, figeage de l'en-tête, styles) :
  **hors périmètre par défaut**. À proposer comme arbitrage explicite, pas à faire d'office ;
* le scoring, les règles, le seuil ;
* les règles de conflit du ré-import (POC-006 / POC-009) : elles sont acquises et ne bougent pas ;
* toute migration de schéma ;
* pas de refactoring global, pas de renommage de module, pas de suppression de fichier.

## Documents à lire en premier

Lis uniquement ces fichiers au démarrage :

1. `CLAUDE.md`
2. `document/claude_code/AGENTS.md`
3. `document/claude_code/handoff.md` — les **deux dernières sections** seulement
4. `document/Backlog.md` — uniquement les sections `## POC-013` et `## POC-006` (règles de
   conflit du ré-import), plus la sous-section « Call client du 04/09/2026 » de POC-003
5. `document/claude_code/task_list.md` — ligne POC-013

Puis (OBLIGATOIRE avant d'écrire une ligne) :

* `source/backend/adapters/storage/csv_export.py` — les 16 colonnes et leur ordre font foi
* `source/backend/adapters/storage/run_poc006.py` — le point d'entrée du ré-import
* `source/backend/adapters/storage/profile_store.py` — **uniquement** `importer_commentaires_csv`,
  `_importer_statut_coordonnees`, `enregistrer_profils` et `_CHAMPS_COMPLETABLES`

Ne lis pas tout le repo.

## Pièges connus, vérifiés dans le code le 08/09/2026

* **[Code] `run_poc006.main` appelle `enregistrer_profils` AVANT `importer_commentaires_csv`.**
  La première passe complète les champs des profils connus depuis le fichier relu. Si Excel a
  reformaté une valeur au passage — une date `2026-08-26` rendue `26/08/2026` ou en numéro de
  série, un `score` en flottant, un `ne_plus_traiter` en entier — c'est cette passe qui écrira
  la valeur abîmée en base. Le projet a déjà un précédent de titre divergent entre CSV et
  magasin (Erwan Jorand, point de vigilance de POC-009) et personne ne sait lequel est le bon.
  **Ne pas laisser ce ticket en créer un deuxième.**
* **[Code] `importer_commentaires_csv` ouvre le fichier elle-même** (`open(csv_path, ...)` puis
  `csv.DictReader`). Elle ne sait pas lire un classeur. Il faut décider proprement où se fait la
  bascule : lui passer des lignes déjà lues, ou lire en amont dans `run_poc006`. Regarder les
  appelants avant de trancher.
* **[Code] `_STATUTS_IMPORTABLES` n'accepte que `valide` et `rejete`**, en comparant des chaînes
  minuscules. Une cellule Excel vide arrivant en `None` au lieu de `""` casse `.strip().lower()`.
* **Deux profils du magasin portent un emoji dans leur nom** — c'est ce qui a fait planter un run
  de POC-009 sur console cp1252. Les inclure dans les tests.
* **`justification` est longue et contient des séparateurs** ; `url` est un candidat à la
  conversion automatique en lien hypertexte par Excel.

## Branche et sécurité Git

```powershell
git status --short
git branch --show-current
```

La branche attendue est `master`. Ne change pas de branche sans validation humaine.

Ne fais jamais : `git reset --hard` ; checkout destructif ; suppression de fichiers ; amend de
commit ; modification de fichiers non liés au ticket.

## Précautions propres à la session en itinérance

* **`profils.db` est la seule copie qui existe** — le poste principal est éteint depuis le
  départ. Il n'y a pas de `D:\Documents\Dev\_backup_prospection\` sur cette machine ; les
  sauvegardes du déplacement sont dans `C:\Users\HP\Documents\_backup_prospection\`.
* **Faire une copie datée de `profils.db` avant le premier ré-import**, et une autre avant chaque
  écriture structurante. C'est la règle du poste principal ; elle vaut d'autant plus ici qu'il
  n'y a pas de second filet.
* Vérifier avant de commencer, **en lecture seule** (sans passer par `ouvrir_magasin`, qui
  créerait un magasin vide si le fichier manquait) : 81 profils, dernière collecte 2026-08-26,
  20 statuts relus.
* Aucun run LinkedIn dans ce ticket : pas de réseau, pas de navigateur, pas de session.

## Méthode obligatoire

Étape 1 — Lecture et diagnostic : lis les documents listés, puis seulement les fichiers de code
nécessaires ; identifie les appelants de `importer_commentaires_csv` ; ne modifie aucun fichier.

Étape 2 — Plan court. Réponds d'abord avec :
1. résumé du ticket en 5 lignes maximum ;
2. fichiers à lire ou modifier ;
3. risque principal ;
4. tests prévus ;
5. plan en 3 à 5 étapes ;
6. questions bloquantes éventuelles.

Attends ma validation avant toute modification. Une fois validé, sauvegarder le plan dans
`document/prompts_plans/plan_POC-013.md` et committer
(`git commit -m "docs: POC-013 plan — description courte"`).

Étape 3 — Implémentation contrôlée : applique uniquement l'étape validée, petit diff, pas de
modification opportuniste, explique le diff, lance les tests ciblés.

Étape 4 — Vérification :

```powershell
uv run --extra test pytest tests/unit/test_xlsx_export.py -v
uv run --extra test pytest tests/ -q
uv run --extra test pytest tests/ --collect-only -q
```

Puis l'aller-retour réel : sauvegarde de `profils.db`, export, conversion, annotation dans
Excel, ré-import, et **comparaison ligne à ligne contre la sauvegarde**.

Étape 5 — Fin de session (OBLIGATOIRE) :
* `document/Backlog.md` — section POC-013 : compléter les specs et les décisions ;
* `document/claude_code/task_list.md` : POC-013 → DONE avec métriques (nb tests) ;
* `document/claude_code/handoff.md` : nouvelle section ;
* `CLAUDE.md` — « État actuel » : deux lignes, aucune métrique ;
* `document/claude_code/prompt_reconciliation_retour.md` : **compléter la liste de ce qui a été
  écrit sur le laptop** — c'est ce fichier qui pilotera la réconciliation au retour ;
* commit : `git commit -m "docs: POC-013 DONE — description courte"`.

## Contraintes de style

* Réponses en français, commentaires de code en anglais.
* Toute affirmation importante taguée [Code] / [Documentation] / [Inférence].
* Ne corrige jamais silencieusement une donnée métier sensible.

## Première réponse attendue

Ne modifie aucun fichier. Commence par : vérifier la branche et l'état Git, vérifier le magasin
en lecture seule, lire les fichiers listés, résumer le ticket, proposer un plan court, et
attendre ma validation.
