Tu travailles dans le repo ProspectionLinkedIn avec Claude Code dans VS Code.

Je viens de faire un /clear pour réduire le contexte. Tu dois reprendre proprement à partir de
la documentation projet, mais sans relire tout le repository.

## Ticket à traiter

Ticket : POC-010
Titre : Collecte, scoring et extraction d'email en une seule session LinkedIn
Objectif : Faire de `run_poc001` un run complet — collecte des cartes de résultats, scoring en
mémoire, puis visite des pages profil **des seuls profils intéressants** — au lieu d'une
collecte nue suivie d'une seconde session qui refait le travail. Une session LinkedIn, une
seule passe, aucune recherche refaite.

**Origine** : ticket ouvert le 28/08/2026 à ma demande, pendant le cadrage de POC-009. J'avais
posé la question « il faudrait une version enrichie de `run_poc001` qui en profite pour
récupérer l'email ». La proposition brute a été instruite et **amendée** : la fusionner telle
quelle rendait systématique l'étape la plus risquée du pipeline. La variante retenue est
décrite ci-dessous.

Statut attendu : `TODO` / **P2** dans `task_list.md`.

## État de départ (vérifié dans le code le 28/08/2026 — ne pas le refaire de zéro)

1. [Code] `run_poc001.main()` fait aujourd'hui : `ouvrir_magasin` → `urls_connues` →
   `search_and_extract(page, SEARCH_QUERY, MAX_PROFILES, deja_vus)` → `enregistrer_profils` →
   `lister_profils` → `export_profiles_to_csv`. **Aucune visite de page profil, aucun email**
   (`extract_profile_from_card` renvoie exactement `nom`, `titre`, `localisation`, `url`).
2. [Code] `scorer_titre(titre, regles)` ne lit **que le `titre`** — champ disponible dès la
   carte de résultat. **Le score est donc calculable pendant le run de collecte, sans visiter
   une seule page profil.** C'est le fait qui rend ce ticket possible.
3. [Code] `enrich_profiles_with_email(page, profils)` ne lit que `profil["url"]` et renvoie les
   mêmes dicts + une clé `email`. Elle est indifférente à la provenance de la liste.
4. [Code] `_CHAMPS_COMPLETABLES` dans `profile_store.py` contient déjà `email`, `email_web` et
   `site_web` : **`enregistrer_profils` sait déjà écrire l'email**. Aucune migration de schéma
   n'est nécessaire pour ce ticket au titre de l'email.
5. [Code] Un adapter a le droit d'importer `core/` — `run_poc003` importe déjà
   `source.backend.core.profile_scoring` (AGENTS.md §4 interdit l'inverse, pas ce sens).

## Le design retenu au cadrage (à confirmer, pas à réinventer)

```
search_and_extract (pagination complète, aucune visite de page profil)
  → scorer_profils en mémoire              ← ne demande que le titre, déjà présent
  → selectionner_profils_interessants
  → enrich_profiles_with_email SUR CETTE SÉLECTION SEULEMENT
  → enregistrer_profils (tout : les profils, leurs scores, les emails trouvés)
  → export
```

Pas d'entrelacement risqué : la pagination est entièrement terminée avant la première visite de
page profil.

**Pourquoi la sélection par le score, et pas la visite de tous les profils collectés** — les
trois raisons instruites au cadrage de POC-009, à ne pas perdre :

1. [Documentation, Backlog POC-002] la visite d'une page profil « ajoute une requête par profil
   au-dessus de la recherche, ce qui élève le risque de restriction du compte ». Fusionner sans
   filtre rendrait **systématique** l'étape la plus risquée du pipeline.
2. [Documentation, Backlog POC-004] le run réel de POC-002 a donné **0 email public sur 30
   profils**. Payer 25 visites par run pour une espérance de 0 email est le pire ratio
   risque/rendement de la chaîne.
3. [Documentation, Backlog POC-004, décision client du 13/07/2026] les coordonnées ne sont
   cherchées que pour les profils intéressants. Dans une fusion naïve, **le score n'existe pas
   encore au moment de la visite** — la décision client serait contournée par construction.

## Ce que ce ticket ne remplace pas

[Code] Les profils déjà en base sont dans `urls_connues`, donc `run_poc001` ne les reverra
**jamais**. Ce ticket ne fait donc rien pour le stock existant : la passe de rattrapage
alimentée par le magasin (`run_poc002` version POC-009) reste nécessaire, et elle reste le seul
chemin pour un profil dont le statut change après coup — passé sous ou au-dessus du seuil par un
ajustement de règles ou par POC-008. **Ne pas proposer de la supprimer.**

## Les décisions à m'apporter argumentées, non tranchées

* **(a) Couplage collecte ↔ règles de scoring.** Le run de collecte se met à dépendre de
  `config/scoring_rules.json` : changer une règle change ce qui est visité. Est-ce acceptable,
  ou faut-il un garde-fou (seuil de visite distinct du seuil « intéressant », plafond de visites
  par run, mode « collecte seule ») ?
* **(b) Que faire des profils non visités.** Ils entrent en base avec `email` vide — donc, si
  POC-009 a retenu un marqueur daté, **sans** `date_visite_email`, ce qui est correct : ils
  n'ont pas été visités. Vérifier que le reliquat de `run_poc002` les reprend bien et ne les
  considère pas comme traités.
* **(c) Un script ou deux.** Enrichir `run_poc001` en place, ou livrer un `run_poc010` distinct
  en laissant `run_poc001` intact comme collecte nue ? Argument pour deux scripts : garder une
  collecte bon marché et sans risque disponible. Argument pour un seul : deux scripts qui
  paginent la même requête, c'est exactement le doublon que POC-009 vient de supprimer.

## Périmètre autorisé

* `source/backend/adapters/scraping/run_poc001.py` — le cœur du ticket ;
* `source/backend/adapters/scraping/profile_search.py` — **uniquement si** la structuration
  cœur pur / coquille l'exige ; ne pas y toucher autrement ;
* `tests/unit/test_profile_search.py` et le ou les fichiers de tests des scripts concernés — la
  nouvelle logique d'orchestration doit être couverte **hors-ligne, sans navigateur ni réseau**,
  comme l'est déjà `collecter_profils_inconnus` depuis POC-006 ;
* `document/` — Backlog, task_list, handoff.

Hors périmètre :

* **pas de modification du scoring ni de `config/scoring_rules.json`** — ce ticket **consomme**
  `scorer_profils` et `selectionner_profils_interessants`, il ne touche ni aux règles ni au
  seuil ;
* pas de modification de `profile_store.py` ni de `csv_export.py` — [Code] l'email y est déjà
  géré, aucune migration n'est requise. Si l'implémentation semble en exiger une, **c'est un
  signal d'alarme : s'arrêter et m'en parler** ;
* pas de suppression de `run_poc002` ni de sa passe de rattrapage (voir ci-dessus) ;
* pas de diversification des requêtes — c'est POC-008 ;
* pas d'activation du Palier 1 (vérification LLM) de POC-004.

## Ordre des tickets et fichiers partagés

[Code] **Trois tickets convergent sur `run_poc001.py` et `profile_search.py`** : POC-008
(plusieurs requêtes + facettes géographiques natives dans `build_search_url`) et ce ticket.
Ordre recommandé et raison :

* **POC-009 d'abord** — il supprime la recherche de `run_poc002`, et donc la duplication de la
  constante `SEARCH_QUERY`, aujourd'hui présente à l'identique dans `run_poc001.py` **et**
  `run_poc002.py` ;
* **POC-008 ensuite** — P1, le gisement de la requête actuelle est mesuré à ~1 run restant ; et
  c'est POC-008 qui produira les profils frais sur lesquels ce ticket a un intérêt ;
* **POC-010 en dernier**. **Au démarrage, vérifier l'état réel de `run_poc001.main()`** : si
  POC-008 est passé, la fonction boucle probablement sur plusieurs requêtes, et le point
  d'insertion du scoring et de la visite n'est plus celui décrit ci-dessus. Lire avant d'écrire.

## Attention — run LinkedIn réel obligatoire

Contrairement à POC-009, ce ticket **n'est pas validable hors-ligne** : seule une session réelle
montre que la pagination se termine proprement avant les visites, et qu'aucune restriction de
compte n'apparaît. Comme pour POC-001/002/006 :

* **premier run plafonné à 5 profils**, jamais 25 d'emblée ;
* me montrer la sélection qui serait visitée **avant** de lancer la visite ;
* runs jamais enchaînés sans me demander.

Chaque profil collecté entre définitivement dans `urls_connues` : un run de test consomme du
gisement pour de bon.

## Points d'attention

* **Quota et ToS LinkedIn** : c'est le ticket qui augmente le nombre de requêtes par run. Le
  plafond de visites doit être explicite dans le code, pas implicite.
* **RGPD** : les garde-fous de POC-004/POC-006 (`date_collecte`, `ne_plus_traiter`, relecture
  humaine avant tout contact) restent en vigueur. [Code] `lister_profils` exclut déjà les
  profils opposés ; vérifier qu'un profil `ne_plus_traiter` ne peut en aucun cas être visité.
* **Ne corrige jamais silencieusement une donnée métier** : si un run écrase ou contredit une
  valeur en base, le signaler dans un rapport, comme POC-006 l'a fait pour les
  `commentaire_client`.
* [Documentation] `BRAVE_SEARCH_API_KEY`, `LINKEDIN_EMAIL`, `LINKEDIN_PASSWORD` sont lues depuis
  `.env.local`. Ne jamais les exposer, ni dans un log, ni dans la documentation, ni dans un
  commit.
* [Documentation] `profils.db` est local, gitignoré et sans sauvegarde. Aucune écriture de
  schéma n'est prévue par ce ticket ; s'il en faut une, règle CLAUDE.md n°5 (plan validé +
  backup hors du dépôt).
* La liste des questions ouvertes au client (`Backlog.md`, section POC-003) ne doit être
  tranchée par aucun ticket.

## Documents à lire en premier

Lis uniquement ces fichiers au démarrage :

1. `CLAUDE.md`
2. `document/claude_code/AGENTS.md`
3. `document/Backlog.md` — sections `## POC-010`, `## POC-002` (risque de restriction de compte)
   et `## POC-004` (décision client du 13/07/2026, taux de pertinence)
4. `document/claude_code/task_list.md` — lignes POC-002, POC-008, POC-009 et POC-010
5. `document/claude_code/handoff.md` — la section POC-009 et celle de POC-008 si elle existe
6. `source/backend/adapters/scraping/run_poc001.py`
7. `source/backend/adapters/scraping/profile_search.py`
8. `source/backend/adapters/scraping/profile_email.py`
9. `source/backend/core/profile_scoring.py` — `scorer_profils` et
   `selectionner_profils_interessants` uniquement

Ne lis pas tout le repo.

## Branche et sécurité Git

```powershell
git status --short
git branch --show-current
```

La branche attendue est `master`. Le nombre de tests de référence est celui consigné dans
`document/claude_code/task_list.md` à la clôture du ticket précédent (102 avant POC-009).
Ne change pas de branche sans validation humaine. Ne fais jamais : `git reset --hard` ; checkout
destructif ; suppression de fichiers ; amend de commit ; modification de fichiers non liés au
ticket.

## Méthode attendue

Étape 1 — **Lecture et diagnostic, sans modifier un fichier** : relire `run_poc001.main()` dans
son état réel du jour (voir « Ordre des tickets » ci-dessus), et les signatures exactes de
`enrich_profiles_with_email`, `scorer_profils`, `selectionner_profils_interessants`.

Étape 2 — **Plan court**, puis validation avant toute modification, avec les trois décisions
(a) (b) (c) argumentées et non tranchées.

Étape 3 — **Implémentation et tests hors-ligne** : l'orchestration doit être extraite en
fonction pure injectable (patron `collecter_profils_inconnus` de POC-006) pour être testable
sans navigateur. Suite verte avant tout run réel.

Étape 4 — **Run réel plafonné à 5 profils**, sélection montrée avant visite.

Étape 5 — **Vérification en base** : les profils collectés portent bien score et catégorie ; les
seuls à porter un `email` non vide (ou un marqueur de visite, selon ce que POC-009 a retenu)
sont ceux de la sélection.

## Vérification

```powershell
pytest tests/unit/test_profile_search.py -v
pytest tests/ -q
pytest tests/ --collect-only -q
```

## Fin de session (OBLIGATOIRE)

* `document/Backlog.md` — section POC-010 : specs définitives, décisions, résultat du run réel ;
* `document/claude_code/task_list.md` — POC-010 → DONE avec métriques (nb tests) ;
* `document/claude_code/handoff.md` — nouvelle section ;
* `CLAUDE.md` — « État actuel », **deux lignes, aucune métrique** ;
* prompt du ticket suivant dans `document/prompts_plans/prompt_[NEXT_TICKET].md` ;
* commit : `git commit -m "docs: POC-010 DONE — description courte"`.

## Contraintes de style

* Réponses en français.
* Commentaires de code en anglais.
* Toute affirmation importante taguée [Code] / [Documentation] / [Inférence].
* Ne corrige jamais silencieusement une donnée métier sensible.

## Première réponse attendue

Ne modifie aucun fichier. Commence par : (1) vérifier la branche et l'état Git ; (2) lire les
fichiers listés → résumer le ticket ; (3) exposer l'état **réel** de `run_poc001.main()` au jour
du démarrage et le point d'insertion exact du scoring et de la visite conditionnelle ; (4)
proposer un plan court, avec les trois décisions (a) (b) (c) argumentées mais non tranchées, et
attendre ma validation.
