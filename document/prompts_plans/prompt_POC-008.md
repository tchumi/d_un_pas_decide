Tu travailles dans le repo ProspectionLinkedIn avec Claude Code dans VS Code.

Je viens de faire un /clear pour réduire le contexte. Tu dois reprendre proprement à partir de
la documentation projet, mais sans relire tout le repository.

## Ticket à traiter

Ticket : POC-008
Titre : Diversification des requêtes (vocabulaire outdoor + filtre géographique réel)
Objectif : Sortir de la requête booléenne unique qui alimente le gisement depuis POC-001, sur
deux axes — un **vrai filtre géographique** (facettes natives LinkedIn plutôt que `AND (France)`
noyé dans les mots-clés) et le **vocabulaire outdoor fourni par le client le 08/07/2026**, qui
n'a jamais été interrogé.

Statut : `TODO` / **P1** dans `task_list.md` (passé P2 → P1 le 27/08/2026 à la clôture de
POC-007). Le cadrage détaillé est à faire dans ce ticket.

**Pourquoi maintenant — trois arguments convergents** :

1. [Code] **Le gisement est presque épuisé** : mesuré le 26/08/2026, la requête actuelle est à
   la page 8 sur un plafond estimé à ~10, soit [Inférence] environ **un run d'avance restant**.
   La cible client de 50 profils/semaine n'est pas tenable sans nouvelles requêtes.
2. [Documentation] **La catégorie `coach_outdoor` de POC-003 n'a jamais été observée** :
   0 profil sur 75, parce qu'aucune requête ne contient de mot-clé outdoor. Ses 5 mots-clés
   sont couverts par des tests unitaires et par rien d'autre.
3. [Code] **POC-007 a montré que l'homogénéité de la requête écrase le pouvoir discriminant du
   scoring** : 48 % du lot frais (24 profils sur 50) sont à **75 pile**, tous des « Coach
   professionnel certifié par Coaching Ways France Level 2 ICF ». Le score trie le pertinent du
   non-pertinent, mais ne hiérarchise plus à l'intérieur. Diversifier la requête est le levier
   identifié.

## État de départ (vérifié, ne pas le refaire de zéro)

1. [Code] `build_search_url` place **toute** la requête — `AND (France)` compris — dans le seul
   paramètre `keywords` de l'URL de recherche. Ce n'est donc **pas un filtre géographique** mais
   une correspondance textuelle : un profil basé à Genève dont le titre mentionne « France »
   passe, un profil lyonnais dont le titre ne la mentionne pas est écarté.
2. [Code] Le magasin `profils.db` contient **81 profils** dédupliqués sur l'URL normalisée
   (`clean_profile_url`). La déduplication est persistante : une nouvelle requête qui recroise
   d'anciens profils ne les réextraira pas, et `collecter_profils_inconnus` sait s'arrêter sur
   `quota_atteint` / `gisement_epuise` / `plafond_pages` (plafond 10 pages).
3. [Code] `search_and_extract` n'est plus que le câblage Playwright autour d'une **boucle pure
   injectable** — la logique d'arrêt est déjà testable sans navigateur. C'est le point d'entrée
   à étendre, pas à réécrire.
4. [Code] **Piège mesuré par POC-007** : le mot-clé outdoor « coach qui marche » se réduit à la
   sous-chaîne `marche` après normalisation, **déjà présente dans 3 titres du lot frais** via
   « Analyste **Marché** en ophtalmologie » et « expert du **marché** allemand ». À traiter
   avant d'écrire les mots-clés, sous peine de faux positifs dès le premier run.

5. [Code] **Ce que POC-009 a changé le 28/08/2026 et qui te concerne directement** :
   - `SEARCH_QUERY` n'est **plus dupliquée**. Elle était présente à l'identique dans
     `run_poc001.py` **et** `run_poc002.py` ; `run_poc002` ne cherche plus, il part du magasin.
     Tu n'as donc **qu'un seul endroit** à modifier pour varier les requêtes ;
   - l'export est unifié : constante partagée `EXPORT_CSV` (`profils_magasin.csv`) dans
     `csv_export.py`, importée par les quatre scripts. `profils_extraits.csv` et
     `profils_extraits_scores.csv` existent encore sur disque mais **ne sont plus écrits** ;
   - le magasin est en `PRAGMA user_version = 2` et porte **16 colonnes** : trois ajoutées par
     POC-009 (`date_visite_email`, `date_enrichissement_web`, `statut_coordonnees`). Les
     profils que tu collecteras entreront avec ces trois colonnes vides, donc dans le reliquat
     des deux étapes de coordonnées — c'est le comportement voulu ;
   - **6 profils de juillet ont été ajoutés au magasin** (datés du 07/07/2026) : ils venaient du
     lot POC-002, jamais entré en base parce que `run_poc002` faisait alors sa propre recherche.
     Deux recherches sur la même requête booléenne à deux moments différents n'avaient pas
     ramené le même lot (recouvrement 19/25) — à garder en tête quand tu jugeras la stabilité
     du gisement d'une requête.

## Périmètre autorisé

* `source/backend/adapters/scraping/profile_search.py` — construction de l'URL de recherche,
  facettes, et la ou les requêtes à jouer ;
* `source/backend/adapters/scraping/selectors.py` — sélecteurs des facettes (règle AGENTS.md
  §4 : les sélecteurs CSS LinkedIn restent centralisés ici, jamais dispersés) ;
* `source/backend/adapters/scraping/run_poc001.py` — pilotage d'un run multi-requêtes ;
* `config/` — si les requêtes deviennent de la configuration éditable (à proposer, pas à
  décider seul) ;
* `tests/unit/test_profile_search.py` — toute construction d'URL et toute logique de requête
  doit être couverte hors-ligne ;
* `document/` — Backlog, task_list, handoff.

Hors périmètre :

* **pas de modification du scoring ni de `config/scoring_rules.json`** — POC-007 a clos le
  sujet en décidant de ne rien ajuster avant retour client ;
* pas de modification du schéma du magasin (règle CLAUDE.md n°5) ;
* le raccordement de POC-002/POC-004 au magasin, qui est POC-009 ;
* pas de refactoring de `profile_search.py` au-delà de ce que la diversification exige.

## Méthode attendue

Étape 1 — **Diagnostic sur DOM réel, avant tout code** : ouvrir une recherche LinkedIn et
relever les sélecteurs des facettes (lieu en particulier) ainsi que la forme réelle des
paramètres d'URL qu'elles produisent. [Documentation] **Contrairement à POC-006, ce ticket
n'est pas développable entièrement hors-ligne** — les sélecteurs de facettes doivent être
vérifiés sur un DOM réel, comme l'ont été ceux de POC-001/002/005.

Étape 2 — **Plan court**, puis validation avant toute modification. Deux questions à trancher
avec moi et non seul : (a) les requêtes deviennent-elles de la configuration éditable ou
restent-elles en dur ; (b) un run joue-t-il plusieurs requêtes à la suite, ou une seule choisie
à l'appel.

Étape 3 — **Implémentation avec tests hors-ligne** : la construction d'URL et la sélection des
requêtes doivent être testables sans navigateur, comme l'est déjà la boucle de pagination.

Étape 4 — **Run réel** sur la requête outdoor, en surveillant le quota et sans jamais dépasser
les volumes des runs précédents (`MAX_PROFILES = 25`). Objectif de vérification : la catégorie
`coach_outdoor` devient-elle enfin observable, et avec quel taux de faux positifs compte tenu
du piège `marche` ci-dessus.

Étape 5 — **Mesurer au lieu d'estimer** : profiter du run pour relever le sélecteur de la barre
de pagination numérotée et journaliser la taille réelle du gisement par requête. Le « ~10 pages »
actuel est une estimation, pas une mesure.

## Points d'attention

* **Quota et ToS LinkedIn** : chaque requête supplémentaire consomme du quota réel sur un compte
  personnel. Ne jamais enchaîner les runs sans me demander.
* `profils.db` est **local et gitignoré**, sans sauvegarde. Ne rien y faire de destructif ;
  `run_poc006.py` sait le reconstruire depuis un CSV si nécessaire.
* [Inférence] Un profil outdoor authentique pourrait très bien ne pas contenir le mot `coach`
  dans son titre et se faire **exclure** par `exclusion_non_coach`. Si le cas se présente, le
  **signaler** — c'est une donnée pour la reprise de contact client, pas une règle à corriger
  en douce (le scoring est hors périmètre).
* La liste des questions ouvertes au client compte **7 entrées** (`Backlog.md`, section
  POC-003) ; ce ticket peut en produire une huitième, il ne doit en trancher aucune.

## Documents à lire en premier

Lis uniquement ces fichiers au démarrage :

1. `CLAUDE.md`
2. `document/claude_code/AGENTS.md`
3. `document/Backlog.md` — sections `## POC-008` et `## POC-006` (gisement, pagination)
4. `document/claude_code/task_list.md` — lignes POC-006, POC-007 et POC-008
5. `document/claude_code/handoff.md` — sections 7 (POC-006) et 8 (POC-007) uniquement
6. `source/backend/adapters/scraping/profile_search.py`
7. `source/backend/adapters/scraping/selectors.py`

Ne lis pas tout le repo.

## Branche et sécurité Git

```powershell
git status --short
git branch --show-current
```

La branche attendue est `master` (123 tests). Ne change pas de branche sans validation humaine.
Ne fais jamais : `git reset --hard` ; checkout destructif ; suppression de fichiers ; amend de
commit ; modification de fichiers non liés au ticket.

## Vérification

```powershell
pytest tests/unit/test_profile_search.py -v
pytest tests/ -q
pytest tests/ --collect-only -q
```

## Fin de session (OBLIGATOIRE)

* `document/Backlog.md` — section POC-008 : specs définitives, décisions, résultats du run réel ;
* `document/claude_code/task_list.md` — POC-008 → DONE avec métriques (nb tests) ;
* `document/claude_code/handoff.md` — nouvelle section ;
* `CLAUDE.md` — « État actuel », **deux lignes, aucune métrique** ;
* prompt du ticket suivant dans `document/prompts_plans/prompt_[NEXT_TICKET].md` ;
* commit : `git commit -m "docs: POC-008 DONE — description courte"`.

## Contraintes de style

* Réponses en français.
* Commentaires de code en anglais.
* Toute affirmation importante taguée [Code] / [Documentation] / [Inférence].
* Ne corrige jamais silencieusement une donnée métier sensible.

## Première réponse attendue

Ne modifie aucun fichier. Commence par : (1) vérifier la branche et l'état Git ; (2) lire les
fichiers listés → résumer le ticket ; (3) exposer ce que tu as compris de la construction
actuelle de l'URL de recherche et ce qui devra changer ; (4) proposer un plan court et attendre
ma validation.
