Tu travailles dans le repo ProspectionLinkedIn avec Claude Code dans VS Code.

Je viens de faire un /clear pour réduire le contexte. Tu dois reprendre proprement à partir de
la documentation projet, mais sans relire tout le repository.

## Ticket à traiter

Ticket : POC-009
Titre : Raccordement de POC-002 et POC-004 au magasin (sans refaire le scraping)
Objectif : Faire vivre dans le magasin les résultats de l'extraction d'email (POC-002) et de
l'enrichissement web (POC-004), comme POC-006 l'a fait pour les profils — **sans que
`run_poc002` refasse la recherche déjà effectuée par `run_poc001`**.

Statut : `TODO` / **P2** dans `task_list.md`. Ticket ouvert le 26/08/2026 à la clôture de
POC-006, à ma demande. Le cadrage détaillé est à faire dans ce ticket.

**Ce ticket est développable entièrement hors-ligne côté LinkedIn** (contrairement à POC-008) :
la liste des profils à traiter vient du magasin. Seul l'enrichissement web appelle un réseau
externe (API Brave Search).

## État de départ (revérifié dans le code et en base le 27/08/2026, ne pas le refaire de zéro)

1. [Code] **Le magasin est vide de toute coordonnée** : sur les 75 profils de `profils.db`,
   **0 `email`, 0 `email_web`, 0 `site_web`**. Les trois colonnes existent depuis
   POC-002/POC-004, rien ne les alimente.
2. [Code] POC-006 a câblé `run_poc001` (extraction) et `run_poc003` (scoring) au magasin, parce
   que c'est ce que son périmètre couvrait. `run_poc002` et `run_poc004` sont restés sur le
   schéma CSV → CSV d'avant.
3. [Code] `run_poc002.main()` appelle `search_and_extract(...)` **puis**
   `enrich_profiles_with_email(...)` : il refait donc intégralement la recherche de
   `run_poc001` avant de visiter les pages profil. Quota LinkedIn et exposition ToS dépensés
   pour un résultat que le magasin détient déjà. **Contrainte que j'ai posée à l'ouverture du
   ticket : cette recherche doit disparaître.**
4. [Code] `run_poc004.main()` lit `profils_extraits_email.csv` (`INPUT_CSV`) et écrit
   `profils_extraits_enrichis.csv` (`OUTPUT_CSV`) via `load_profiles`/`export_profiles_to_csv` :
   le magasin n'est jamais ouvert.
5. [Code] Le patron de raccordement existe déjà et est à réutiliser, pas à réinventer —
   `run_poc003` en est le modèle : `ouvrir_magasin` → `lister_profils(conn)` → traitement →
   fonction d'écriture ciblée → `export_profiles_to_csv`. `profile_store` expose
   `enregistrer_profils` (complète champ par champ, `COALESCE(NULLIF(...))` : **une valeur
   entrante vide ne blanchit jamais une colonne remplie**) et `mettre_a_jour_scoring` (écriture
   ciblée d'un sous-ensemble de colonnes). Une écriture ciblée des colonnes de coordonnées
   suivrait le même patron.
6. [Code] **Volume d'entrée de l'enrichissement conditionnel : 60 profils sur 75** sont
   au-dessus du seuil de 60 et non exclus. C'est autant d'appels à l'API Brave Search si
   `run_poc004` est branché sans marqueur de reliquat — d'où le point suivant.

## La vraie question à trancher au cadrage

Le magasin ne sait pas distinguer **« pas encore enrichi »**, **« enrichi, rien trouvé »** et
**« candidat trouvé, non validé par un humain »** : une colonne vide veut dire les trois. C'est
exactement la classe de problème que POC-006 a réglée pour les profils. Deux conséquences
concrètes : sans marqueur, **chaque run refait tout le travail** ; sans statut de validation,
**un faux positif devient une donnée de contact**.

Pistes ouvertes, **aucune n'est décidée** — c'est à toi de les instruire et à moi de trancher :

- un marqueur « déjà visité pour email » et « déjà enrichi », **datés**, pour ne traiter que le
  reliquat à chaque run. [Inférence] C'est ce qui remplace la recherche supprimée de
  `run_poc002` : la liste des profils à visiter vient du magasin ;
- un **statut de validation** sur les coordonnées trouvées (candidat / validé / rejeté), pour
  que la relecture humaine — indispensable au vu du taux de pertinence de **1/25** mesuré le
  10/07/2026 — soit conservée au lieu d'être refaite à chaque run ;
- `run_poc004` devient **conditionnel après le scoring** (décision client du 13/07/2026) : sa
  liste d'entrée est `selectionner_profils_interessants()` appliqué au magasin, et non plus un
  CSV.

## Le piège à ne pas contourner naïvement

On pourrait croire qu'un `run_poc006 profils_extraits_enrichis.csv` suffirait à rapatrier
l'existant. **Ne pas le faire tel quel.** [Code] Revérifié le 27/08/2026 : ce fichier contient
25 lignes, **5 `email_web` et 11 `site_web`** — et d'après la relecture humaine déjà consignée
en section POC-004 du Backlog, il s'y trouve **1 seul vrai positif confirmé** (Manuel BOSSU →
`mycoachonline.fr`), 1 positif partiel (Sylvie WEILER → `memepascap.fr`, adresse de cabinet non
personnelle) et **7 faux positifs confirmés** (`intercariforef.org`, `spotify.com`,
`noomii.com`, `amazon.co.uk`, `journaldunet.com`, `je-change-de-metier.com`, `lafrenchcom.fr`
avec son `urgent@` typique d'une agence). Les importer en l'état inscrirait des faux positifs
dans le magasin **comme s'ils étaient des faits établis**. Si l'existant doit être récupéré, ce
doit être après relecture, ou accompagné d'un statut de validation.

## Périmètre autorisé

* `source/backend/adapters/scraping/run_poc002.py` — suppression de la recherche, entrée = le
  magasin, sortie = le magasin ;
* `source/backend/adapters/enrichment/run_poc004.py` — entrée = le magasin (liste conditionnelle
  après scoring), sortie = le magasin ;
* `source/backend/adapters/storage/profile_store.py` — écriture ciblée des coordonnées et, si le
  plan le retient, colonnes de marqueur/statut ;
* `source/backend/adapters/storage/csv_export.py` — si de nouvelles colonnes doivent apparaître
  dans l'export (même patron `restval=""` que les colonnes précédentes) ;
* `tests/unit/test_profile_store.py`, `tests/unit/test_csv_export.py` et les tests des scripts
  concernés — toute nouvelle logique doit être couverte **hors-ligne, sans navigateur ni
  réseau**, comme l'est déjà la boucle de pagination de POC-006 ;
* `document/` — Backlog, task_list, handoff.

Hors périmètre :

* **pas de modification du scoring ni de `config/scoring_rules.json`** — POC-007 a décidé le
  27/08/2026 de ne rien ajuster avant retour client. Ce ticket **consomme**
  `selectionner_profils_interessants()`, il ne touche pas aux règles ni au seuil ;
* pas de diversification des requêtes, qui est POC-008 ;
* **pas de nouvelle recherche LinkedIn** — c'est l'objet même du ticket ;
* pas d'activation du Palier 1 (vérification LLM) de POC-004 : le pipeline reste déterministe
  tant que le client n'a pas tranché sur le taux de pertinence de 1/25.

## Attention — évolution de schéma

[Code] `profils.db` est en `PRAGMA user_version = 1` (`SCHEMA_VERSION = 1` dans
`profile_store.py`), **créé et jamais migré**. Ce ticket ajoute très probablement des colonnes.
Règle CLAUDE.md n°5 : **pas de migration sans plan validé et backup explicite**.

Concrètement, avant toute écriture de schéma :
1. me faire valider le plan de migration (colonnes, valeurs par défaut, comportement sur les
   75 lignes existantes) ;
2. prendre une **copie de `profils.db` hors du dépôt** et me confirmer son emplacement ;
3. seulement ensuite, migrer.

[Documentation] `profils.db` est **local, gitignoré et sans sauvegarde** — il n'existe que sur
ma machine et contient des données personnelles. `run_poc006.py` sait le reconstruire depuis un
CSV, mais uniquement pour ce qu'un CSV contient.

## Point d'hygiène à traiter au passage

[Code] Depuis POC-006, `profils_extraits.csv` ne contient plus l'extraction brute que son nom
suggère, mais une vue complète du magasin. Et deux scripts exportent deux vues du même magasin
dans deux fichiers différents (`run_poc001` → `profils_extraits.csv`, `run_poc003` →
`profils_extraits_scores.csv`), qui portent le même contenu une fois le scoring passé. Un seul
fichier d'export suffirait, avec un nom qui dise ce qu'il est. **À proposer dans le plan, pas à
décider seul** — et sans supprimer de fichier (règle CLAUDE.md n°3).

## Méthode attendue

Étape 1 — **Lecture et diagnostic, sans modifier un fichier** : relire `run_poc002`,
`run_poc004`, `profile_store` et le patron de `run_poc003`. Identifier précisément ce que
`enrich_profiles_with_email` attend en entrée et rend en sortie, et ce que `enrich_profile`
(POC-004) attend, avant de proposer quoi que ce soit.

Étape 2 — **Plan court**, puis validation avant toute modification. Trois décisions à
m'apporter argumentées, pas tranchées : (a) marqueur de reliquat — quelles colonnes, datées
comment ; (b) statut de validation des coordonnées — quelles valeurs, qui les écrit ; (c) le
rapatriement éventuel de `profils_extraits_enrichis.csv`, sachant le piège ci-dessus.

Étape 3 — **Migration de schéma** selon la procédure de backup ci-dessus, si le plan la retient.

Étape 4 — **Implémentation et tests hors-ligne**, puis vérification que la suite reste verte
(102 tests avant ce ticket).

Étape 5 — **Runs réels, un par un et jamais enchaînés sans me demander** : d'abord
`run_poc002` sur un petit reliquat pour vérifier que la recherche a bien disparu et que le
magasin se remplit, ensuite `run_poc004`. Surveiller le volume : 60 profils au-dessus du seuil,
c'est 60 appels Brave Search si aucun marqueur ne limite le reliquat.

Étape 6 — **Relecture humaine avec moi** des coordonnées trouvées avant de leur donner un
statut « validé ». Le taux de 1/25 mesuré en POC-004 interdit de considérer un candidat comme
un fait.

## Points d'attention

* **RGPD et données personnelles** : ce ticket manipule des emails et des sites personnels. Les
  garde-fous de POC-004 (liste noire de domaines, relecture humaine avant tout contact) restent
  en vigueur et ne doivent pas être affaiblis pour simplifier le raccordement.
* **Quota et ToS LinkedIn** : `run_poc002` visite une page profil par candidat. Ne jamais lancer
  un run sur les 75 profils sans m'avoir montré le reliquat qui serait traité.
* [Documentation] `BRAVE_SEARCH_API_KEY` est lue depuis `.env.local`. Ne jamais l'exposer, ni
  dans un log, ni dans la documentation, ni dans un commit.
* **Ne corrige jamais silencieusement une donnée métier** : si un enrichissement écrase ou
  contredit une valeur en base, le signaler dans un rapport, comme POC-006 l'a fait pour la
  substitution des `commentaire_client`.
* La liste des questions ouvertes au client compte **7 entrées** (`Backlog.md`, section
  POC-003) ; ce ticket peut en produire une huitième — par exemple sur le statut de validation
  des coordonnées — il ne doit en trancher aucune.

## Documents à lire en premier

Lis uniquement ces fichiers au démarrage :

1. `CLAUDE.md`
2. `document/claude_code/AGENTS.md`
3. `document/Backlog.md` — sections `## POC-009` et `## POC-004` (garde-fous RGPD, faux positifs)
4. `document/claude_code/task_list.md` — lignes POC-004, POC-006 et POC-009
5. `document/claude_code/handoff.md` — sections 5 (POC-004) et 7 (POC-006) uniquement
6. `source/backend/adapters/storage/profile_store.py`
7. `source/backend/adapters/storage/run_poc003.py` — le patron de raccordement à réutiliser
8. `source/backend/adapters/scraping/run_poc002.py`
9. `source/backend/adapters/enrichment/run_poc004.py`

Ne lis pas tout le repo.

## Branche et sécurité Git

```powershell
git status --short
git branch --show-current
```

La branche attendue est `master` (102 tests). Ne change pas de branche sans validation humaine.
Ne fais jamais : `git reset --hard` ; checkout destructif ; suppression de fichiers ; amend de
commit ; modification de fichiers non liés au ticket.

## Vérification

```powershell
pytest tests/unit/test_profile_store.py -v
pytest tests/ -q
pytest tests/ --collect-only -q
```

## Fin de session (OBLIGATOIRE)

* `document/Backlog.md` — section POC-009 : specs définitives, décisions, résultats des runs ;
* `document/claude_code/task_list.md` — POC-009 → DONE avec métriques (nb tests) ;
* `document/claude_code/handoff.md` — nouvelle section ;
* `CLAUDE.md` — « État actuel », **deux lignes, aucune métrique** ;
* prompt du ticket suivant dans `document/prompts_plans/prompt_[NEXT_TICKET].md` ;
* commit : `git commit -m "docs: POC-009 DONE — description courte"`.

## Contraintes de style

* Réponses en français.
* Commentaires de code en anglais.
* Toute affirmation importante taguée [Code] / [Documentation] / [Inférence].
* Ne corrige jamais silencieusement une donnée métier sensible.

## Première réponse attendue

Ne modifie aucun fichier. Commence par : (1) vérifier la branche et l'état Git ; (2) lire les
fichiers listés → résumer le ticket ; (3) exposer ce que font aujourd'hui `run_poc002` et
`run_poc004` et ce qui doit changer pour qu'ils lisent et écrivent le magasin ; (4) proposer un
plan court, avec les trois décisions de l'étape 2 argumentées mais non tranchées, et attendre ma
validation.
