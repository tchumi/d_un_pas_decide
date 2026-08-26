Tu travailles dans le repo ProspectionLinkedIn avec Claude Code dans VS Code.

Je viens de faire un /clear pour réduire le contexte. Tu dois reprendre proprement à partir de
la documentation projet, mais sans relire tout le repository.

## Ticket à traiter

Ticket : POC-006
Titre : Renouvellement du gisement de profils (mémoire des profils déjà vus)
Objectif : Faire en sorte que deux exécutions successives du pipeline ramènent des profils
**nouveaux** plutôt que le même lot, et rendre atteignable la cible client de **50
profils/semaine** (mail Christophe Hoffstetter du 04/07/2026).

Statut : `TODO` / **P1** dans `task_list.md` (passé P1 le 26/08/2026 à la clôture de POC-003).
Ticket créé en stub le 26/08/2026 : **le cadrage détaillé est à faire dans ce ticket**, le
constat technique est en revanche déjà établi et vérifié dans le code (voir `Backlog.md`).

**Pourquoi maintenant** : POC-003 vient de livrer un moteur de scoring dont les règles sont
calibrées sur les 25 profils qui servent **aussi** de jeu de référence. La réserve est
explicitement documentée : ces règles doivent être revalidées sur un **lot fraîchement
extrait**. Tant que le pipeline ramène toujours le même lot, cette revalidation est
impossible. POC-006 est donc le prérequis de la consolidation de POC-003.

## Constat à l'origine du ticket (déjà vérifié, ne pas le refaire de zéro)

1. [Code] `search_and_extract` repart systématiquement de la page 1 et retient les
   `max_profiles` **premières** cartes du DOM. La pagination ne sert qu'à compléter le lot,
   jamais à dépasser ce qui a déjà été vu.
2. [Code] `export_profiles_to_csv` ouvre le fichier en mode `"w"` : chaque run **écrase** le
   précédent. Aucune persistance, aucune déduplication, aucune notion de « profil déjà
   traité » dans le code.
3. [Inférence] Les deux défauts se composent, et l'écrasement du CSV empêche même de
   constater le recouvrement.

## Périmètre autorisé

* `source/backend/adapters/storage/` — magasin persistant des profils déjà extraits
  (**SQLite**, annoncé dans la stack `CLAUDE.md` mais jamais introduit : `storage/` ne
  contient à ce jour que l'export CSV et `run_poc003.py`).
  *Note : la présence de `run_poc003.py` — un script de scoring — dans `storage/` est
  délibérée et non une erreur à corriger. Convention du repo : chaque `run_pocNNN.py` vit
  auprès de l'adaptateur qui porte ses entrées/sorties (`run_poc001`/`run_poc002` dans
  `scraping/`, `run_poc004` dans `enrichment/`, `run_poc003` dans `storage/` car son unique
  I/O est le CSV). Ne pas le déplacer dans ce ticket.*
* `source/backend/adapters/scraping/profile_search.py` — passer de « les N premières cartes »
  à « les N cartes **inconnues** », en paginant tant que le quota de nouveaux profils n'est
  pas atteint
* `source/backend/adapters/storage/csv_export.py` — l'export cesse d'être la source de vérité
  pour devenir une **vue exportée** du magasin. **Attention** : ce fichier vient d'être étendu
  par POC-003 (colonnes `categorie`, `score`, `justification`, `commentaire_client`) — les
  conserver toutes
* **Ré-import du retour client** (voir le constat dédié ci-dessous) — le magasin doit pouvoir
  relire un CSV annoté par le client et en conserver la colonne `commentaire_client`
* `tests/unit/` — logique de déduplication, de pagination et de ré-import testable **sans
  navigateur ni réseau**

Hors périmètre :
* pas de refactoring global, pas de changement d'architecture, pas de renommage de module ;
* pas de modification du moteur de scoring POC-003 (`source/backend/core/profile_scoring.py`,
  `config/scoring_rules.json`) ;
* pas de suppression de fichier ; pas de modification de secrets ou fichiers sensibles ;
* **pas de migration de schéma sans plan validé et backup explicite** (règle CLAUDE.md n°5) —
  ce ticket *crée* un schéma, il n'en migre aucun : si une migration devient nécessaire en
  cours de route, s'arrêter et demander.

## Clé de déduplication

L'URL de profil, déjà normalisée par `clean_profile_url` (suppression des query params et du
fragment) — clé naturelle stable. À vérifier dans le code avant de s'appuyer dessus.

## Constat complémentaire — la préservation du retour client est aujourd'hui inatteignable

Vérifié dans le code le 26/08/2026, à intégrer au cadrage :

1. [Code] POC-003 a bien implémenté la préservation côté moteur : `scorer_profils`
   (`core/profile_scoring.py`) ne remplace jamais un `commentaire_client` existant
   (`setdefault`), et un test unitaire dédié le couvre
   (`test_scorer_profils_ne_perd_pas_un_commentaire_client_existant`).
2. [Code] Mais son unique appelant réel, `run_poc003.py`, lit `profils_extraits.csv` (le CSV
   brut d'extraction, **sans** colonne `commentaire_client`) et écrit
   `profils_extraits_scores.csv` en mode `"w"`. Le fichier que le client annote n'est donc
   **jamais relu** : relancer le scoring écrase silencieusement ses commentaires.
3. [Inférence] La protection est donc du code correct et testé, mais **mort en pratique** — le
   test la valide sur un dictionnaire construit à la main, jamais sur un véritable
   aller-retour. La colonne `commentaire_client` est décorative tant qu'aucun chemin de
   ré-import n'existe.

**Décision prise (26/08/2026) : le ré-import entre dans le périmètre de POC-006.** Le magasin
persistant est précisément l'endroit où le retour client doit vivre, au même titre que
`date_collecte` et le marquage « à ne plus traiter » — trois données qui, chacune, ne
survivent pas à un CSV écrasé. Les traiter séparément reviendrait à construire deux fois le
même mécanisme de persistance.

À cadrer explicitement à l'étape 2 : par quelle clé un CSV annoté est réconcilié avec le
magasin (a priori l'URL de profil, même clé que la déduplication), et ce qui se passe en cas
de conflit (commentaire présent des deux côtés et différent — [Inférence] le retour client
doit primer sur une valeur générée, mais ça doit être décidé, pas subi).

## Critères d'acceptation (à confirmer et affiner au cadrage)

1. Deux exécutions successives de la même requête booléenne produisent deux lots **disjoints**
   (aucune URL commune), tant que le gisement de la requête n'est pas épuisé.
2. Gisement épuisé → comportement **explicite** (lot plus petit que demandé + message clair),
   jamais une boucle infinie ni un lot silencieusement incomplet.
3. Aucun profil déjà collecté n'est perdu par un nouveau run (fin de l'écrasement).
4. **Aller-retour du retour client vérifié de bout en bout** : un CSV dont la colonne
   `commentaire_client` a été remplie est ré-importé, puis un nouveau run de scoring conserve
   ces commentaires. Le test doit porter sur l'aller-retour réel (export → annotation →
   ré-import → run), pas sur un dictionnaire construit à la main — c'est exactement ce qui
   manquait à POC-003.
5. Logique de déduplication, de pagination et de ré-import testable sans navigateur ni appel
   réseau.
6. Tests unitaires passants (**67 passants** à l'issue de POC-003, 0 échec, 0 skipped).

## Garde-fous RGPD — ce ticket solde une dette déjà inscrite au Backlog

La section POC-004 engage deux garde-fous **structurellement intenables** avec un CSV écrasé,
que le magasin persistant rend réalisables pour la première fois :

* **Conservation limitée** : champ `date_collecte` par profil, pour permettre une purge future.
* **Droit d'opposition** : pouvoir marquer un profil « à ne plus traiter » — ce marquage doit
  **exclure le profil des collectes futures**, sans quoi il serait réextrait indéfiniment.
* **Minimisation** : le magasin ne stocke que les champs déjà justifiés par les tickets
  précédents. Ce ticket **n'introduit aucune nouvelle catégorie de donnée personnelle**.

## Point à trancher au cadrage (piste complémentaire)

La déduplication seule se heurte au plafond de la recherche LinkedIn pour un compte gratuit
([Inférence] ~100 résultats / 10 pages par requête, plus le quota « commercial use limit »).
Elle donne quelques runs d'avance, pas un gisement infini. **Décider explicitement** si la
diversification des requêtes entre dans ce ticket ou dans un ticket suivant :

* **Filtre géographique réel** : [Code] `build_search_url` place toute la requête — y compris
  `AND (France)` — dans le seul paramètre `keywords`. Ce n'est donc **pas** un filtre
  géographique mais une correspondance textuelle. Les facettes natives de LinkedIn seraient
  plus précises *et* un axe de variation (par ville/région).
* **Vocabulaire outdoor non couvert** : les 5 mots-clés fournis par le client le 08/07/2026
  (*coach nature*, *coach qui marche*, *coach outdoor*, *coach hors-les-murs*, *coaching en
  itinérance*) n'apparaissent dans **aucune** requête actuelle — la catégorie `coach_outdoor`
  de POC-003 est donc testée unitairement mais n'a **jamais** été observée sur données réelles.
  Une requête dédiée la rendrait enfin observable.

## Documents à lire en premier

Lis uniquement ces fichiers au démarrage :

1. `CLAUDE.md`
2. `document/claude_code/AGENTS.md`
3. `document/Backlog.md` — section `## POC-006` (constat, périmètre, garde-fous RGPD) et les
   garde-fous RGPD de la section `## POC-004`
4. `document/claude_code/task_list.md` — ligne POC-006
5. `document/claude_code/handoff.md` — dernière section uniquement (POC-003)
6. `source/backend/adapters/scraping/profile_search.py` — `search_and_extract`,
   `go_to_next_page`, `clean_profile_url`
7. `source/backend/adapters/storage/csv_export.py` — export existant, colonnes POC-003 incluses

Ne lis pas tout le repo.

Note : les CSV de données (`profils_extraits.csv`, `profils_extraits_email.csv`,
`profils_extraits_enrichis.csv`, `profils_extraits_scores.csv`) sont présents localement mais
**gitignorés** (données personnelles) — ils ne sont pas dans l'historique Git. Le `.gitignore`
couvre **déjà** `*.db`, `*.sqlite` et `*.sqlite3` (lignes 16-18) : le magasin créé par ce
ticket est donc protégé sans rien ajouter — vérifier, ne pas dupliquer l'entrée.

## Branche et sécurité Git

```powershell
git status --short
git branch --show-current
```

La branche attendue est `master`. Ne change pas de branche sans validation humaine.

Ne fais jamais : `git reset --hard` ; checkout destructif ; suppression de fichiers ; amend de
commit ; modification de fichiers non liés au ticket.

## Méthode obligatoire

Étape 1 — Lecture et diagnostic :
* lis les fichiers de documentation listés ;
* vérifie dans le code les points 1 et 2 du constat (mode `"w"`, retour à la page 1) ;
* ne modifie aucun fichier.

Étape 2 — Plan court. Réponds d'abord avec :
1. résumé du ticket en 5 lignes maximum ;
2. fichiers à créer ou modifier ;
3. schéma SQLite proposé (tables, colonnes, clé de déduplication, `date_collecte`, marquage
   « à ne plus traiter ») ;
4. stratégie de pagination « jusqu'à N profils inconnus » et condition d'arrêt sur gisement
   épuisé ;
5. tests prévus, dont les 4 critères d'acceptation ;
6. arbitrage proposé sur la diversification des requêtes (dans ce ticket ou le suivant) ;
7. questions bloquantes éventuelles.

Sauvegarde le plan validé dans `document/prompts_plans/plan_POC-006.md` et commit
(`docs: POC-006 plan — description courte`). **Attends ma validation avant toute
modification.**

Étape 3 — Implémentation contrôlée : applique uniquement l'étape validée, petit diff, pas de
modification opportuniste, explique le diff, lance uniquement les tests ciblés.

Étape 4 — Vérification :

```powershell
uv run --extra test pytest tests/unit/ -v
uv run --extra test pytest tests/ --collect-only -q
```

Puis **run réel de deux exécutions successives** et relecture avec moi : le critère
d'acceptation porte sur des lots réellement disjoints, pas seulement sur des tests
synthétiques. Attention au quota LinkedIn et au risque de restriction de compte : proposer un
volume prudent pour le premier run.

Étape 5 — Fin de session (OBLIGATOIRE) :
* `document/Backlog.md` — section POC-006 : specs et critères d'acceptation définitifs,
  décisions prises, résultat des deux runs ;
* `document/claude_code/task_list.md` : POC-006 → DONE avec métriques (nb tests) ;
* `document/claude_code/handoff.md` : nouvelle section ;
* `CLAUDE.md` — section « État actuel » : dernière session (ID + date) et prochain ticket
  actif, **deux lignes, aucune métrique** (elles vivent dans `task_list.md`) ; compléter aussi
  « Structure du repository » — ce ticket crée un magasin SQLite dans `adapters/storage/` ;
* sauvegarder le prompt du prochain ticket dans `document/prompts_plans/prompt_[NEXT].md` ;
* commit : `git commit -m "docs: POC-006 DONE — description courte"`.

Indiquer explicitement si le lancement de l'application est nécessaire.

## Suite attendue après ce ticket (contexte, à ne pas traiter ici)

1. **Revalidation des règles de scoring POC-003 sur le lot frais** produit par ce ticket —
   c'est la raison d'être de l'enchaînement.
2. **Branchement de POC-004 en étape conditionnelle** après le scoring (décision client du
   13/07/2026) : `selectionner_profils_interessants()` existe déjà côté `core/`, le câblage
   reste à faire.
3. **Menu configuration Streamlit** (à prévoir) : réglage du seuil « profil intéressant » et
   édition/sauvegarde des règles de scoring — `charger_regles`/`sauvegarder_regles` sont déjà
   livrées et testées.
4. **Reprise de contact client** (silence depuis le 13/07/2026), avec les trois questions
   ouvertes listées dans `Backlog.md` section POC-003.

## Contraintes de style

* Réponses en français.
* Commentaires de code en anglais.
* Toute affirmation importante taguée [Code] / [Documentation] / [Inférence].
* Ne corrige jamais silencieusement une donnée métier sensible.

## Première réponse attendue

Ne modifie aucun fichier. Commence par : (1) vérifier la branche et l'état Git ; (2) lire les
fichiers listés → résumer le ticket ; (3) vérifier dans le code les deux points du constat ;
(4) proposer un plan court et attendre ma validation.
