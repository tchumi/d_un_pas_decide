# Plan POC-009 — Raccordement de POC-002 et POC-004 au magasin

Plan proposé le 28/08/2026, **validé par l'utilisateur le 28/08/2026** (« ok recommandations,
oublier a-bis »).

## Diagnostic de départ (vérifié dans le code et en base le 28/08/2026)

1. [Code] `run_poc002.main()` : `search_and_extract(page, SEARCH_QUERY, MAX_PROFILES).profils`
   → `enrich_profiles_with_email` → CSV. Aggravant, non documenté jusqu'ici : **il ne passe pas
   `urls_connues` à `search_and_extract`** (4ᵉ paramètre, `frozenset()` par défaut, que
   `run_poc001` renseigne). Le run repart donc de la page 1 et ramène des profils **déjà en
   base** avant de les visiter.
2. [Code] `enrich_profiles_with_email(page, profils)` ne lit que `profil["url"]` et renvoie les
   mêmes dicts + une clé `email`. Elle est indifférente à la provenance de la liste — c'est ce
   qui rend la suppression de la recherche sans effet de bord.
3. [Code] `enrich_profile(profil, api_key)` (POC-004) lit `nom`, `titre`, `localisation` et
   renvoie le dict + `email_web` / `site_web`. Même indifférence à la provenance.
4. [Base, lecture seule] 75 profils, `PRAGMA user_version = 1`, **0 `email`, 0 `email_web`,
   0 `site_web`, 0 `commentaire_client`, 0 `ne_plus_traiter`**.
5. [Code] `scorer_titre` ne lit que le `titre` — noté ici parce que c'est le constat qui a
   ouvert POC-010, pas parce que ce ticket l'utilise.
6. [Code] `SEARCH_QUERY` est **dupliquée à l'identique** dans `run_poc001.py` et
   `run_poc002.py`. Ce ticket supprime la seconde.

## Décisions validées

### (a) Marqueur de reliquat — option A1

Deux colonnes datées, `TEXT NOT NULL DEFAULT ''` :

- `date_visite_email` — écrite par `run_poc002` à chaque visite, **même infructueuse** ;
- `date_enrichissement_web` — écrite par `run_poc004` à chaque tentative, **même infructueuse**.

C'est l'écriture systématique du marqueur, y compris quand rien n'est trouvé, qui distingue
enfin « pas encore traité » de « traité, rien trouvé ». Reliquat = colonne vide. Sur les 75
lignes existantes, vide signifie « jamais tenté », ce qui est factuellement exact.

**Pas de ré-essai automatique** dans ce ticket : le reliquat est uniquement « colonne vide ». La
date est stockée pour rendre un ré-essai possible plus tard sans nouvelle migration.

**(a-bis) abandonné sur décision utilisateur** : `run_poc002` **ne devient pas** conditionnel au
score. Son reliquat reste l'ensemble des profils du magasin non encore visités (75 aujourd'hui),
`ne_plus_traiter` exclus par `lister_profils`. Seul `run_poc004` est conditionnel, conformément
à la décision client du 13/07/2026.

### (b) Statut de validation — option B1

Une colonne `statut_coordonnees`, `TEXT NOT NULL DEFAULT ''`, valeurs `''` / `candidat` /
`valide` / `rejete`, **portant sur les coordonnées web uniquement** (`email_web`, `site_web`).

L'email LinkedIn de POC-002 n'en relève pas : il est publié par la personne sur son propre
profil, c'est un fait et non un candidat. Le doute — taux mesuré 1/25 le 10/07/2026 — porte
exclusivement sur le web.

Qui écrit quoi :

- `run_poc004` écrit `candidat` dès qu'un `email_web` ou un `site_web` non vide sort du
  pipeline. Il n'écrit **jamais** `valide` ;
- l'humain écrit `valide` / `rejete` dans le CSV, ré-importé par le chemin de POC-006.

**Règle de non-régression** : un run ultérieur ne rétrograde jamais un `valide` / `rejete` en
`candidat`, et ne réécrit pas les coordonnées d'un profil dans cet état. Même esprit que le
`COALESCE(NULLIF(...))` existant.

**Règle de contradiction** : hors statut figé, une valeur entrante non vide et différente de la
valeur stockée est appliquée **et listée dans un rapport**, jamais appliquée en silence — patron
`RapportReimport` de POC-006. Une valeur entrante vide ne blanchit jamais une colonne remplie.

**Question client n°8 produite par ce ticket, non tranchée** : qui valide, nous ou le client ?

### (c) Rapatriement de `profils_extraits_enrichis.csv` — option C2

Rapatriement **nominatif**, ligne à ligne, après relecture avec l'utilisateur, et **jamais** en
bloc via `run_poc006` :

- Manuel BOSSU → `valide` ;
- Sylvie WEILER → `candidat` (le Backlog dit « positif partiel » : site pertinent, email de
  cabinet non personnel — ce n'est pas `valide`) ;
- les 7 faux positifs confirmés → `rejete` ;
- les 2 candidats non vérifiés → `candidat`.

Argument décisif : [Documentation, handoff §6] **Manuel BOSSU est scoré 20, donc sous le seuil
de 60**. L'enrichissement devenant conditionnel au score, il ne sera plus jamais candidat — ne
rien rapatrier reviendrait à perdre définitivement le seul vrai positif jamais obtenu. Les 7
`rejete` ont une valeur propre : ils évitent de re-proposer les mêmes erreurs.

### (§5) Les trois colonnes apparaissent dans le CSV

[Code] Un test unitaire garde l'alignement `PROFILE_COLUMNS` ↔ `PROFILE_CSV_FIELDS`. Les trois
colonnes sont ajoutées des deux côtés, en fin de liste — même patron que `date_collecte` /
`ne_plus_traiter` en POC-006. C'est de toute façon nécessaire pour `statut_coordonnees` :
c'est par le CSV que la relecture humaine revient en base.

### (§6) Hygiène d'export — option H2

Une constante partagée `EXPORT_CSV = Path("./profils_magasin.csv")` dans `csv_export.py`,
importée par les quatre scripts. Les anciens fichiers (`profils_extraits.csv`,
`profils_extraits_scores.csv`, `profils_extraits_email.csv`,
`profils_extraits_enrichis.csv`) **restent sur disque et ne sont pas supprimés** (règle
CLAUDE.md n°3) ; ils cessent simplement d'être écrits.

**Élargissement de périmètre assumé** : H2 impose de toucher `run_poc001.py` et `run_poc003.py`
(une ligne chacun, la constante de sortie), qui ne figuraient pas au périmètre initial du
prompt. Explicitement couvert par la décision utilisateur du 28/08/2026, qui portait sur une
constante « importée par les 4 scripts ».

**`.gitignore`** : `profils_magasin.csv` doit y être ajouté — il contient des données
personnelles, même précédent que les CSV de POC-001/003/004.

## Migration de schéma

`SCHEMA_VERSION` 1 → 2, trois colonnes :

```sql
ALTER TABLE profils ADD COLUMN date_visite_email       TEXT NOT NULL DEFAULT '';
ALTER TABLE profils ADD COLUMN date_enrichissement_web TEXT NOT NULL DEFAULT '';
ALTER TABLE profils ADD COLUMN statut_coordonnees      TEXT NOT NULL DEFAULT '';
```

- **Effet sur les 75 lignes existantes** : les trois colonnes à `''` — « jamais tenté, rien à
  valider ». Aucune donnée existante réécrite, aucune colonne supprimée ni renommée.
- [Code] `ouvrir_magasin` pose aujourd'hui `PRAGMA user_version` **inconditionnellement** et ne
  migre jamais : sur une base v1, il l'aurait marquée v2 sans rien migrer. Remplacé par une
  fonction de migration idempotente (lecture de `user_version`, colonnes ajoutées seulement si
  absentes de `PRAGMA table_info`), testée sur une base v1 synthétique.
- **Backup obligatoire avant tout `ALTER`** (règle CLAUDE.md n°5) : copie de `profils.db` hors
  du dépôt, emplacement confirmé à l'utilisateur et validé par lui. Aucun `ALTER` sur la base
  réelle avant ce feu vert ; tout le développement et les tests se font sur des bases
  temporaires.

## Étapes

1. `profile_store.py` — `SCHEMA_VERSION = 2`, migration idempotente, 3 colonnes dans `_SCHEMA`
   et `PROFILE_COLUMNS`. Les nouvelles colonnes **n'entrent pas** dans `_CHAMPS_COMPLETABLES` :
   comme `commentaire_client` / `date_collecte` / `ne_plus_traiter`, elles ne sont pas des
   champs qu'un run de collecte complète, mais des colonnes à écriture ciblée.
2. `profile_store.py` — écritures ciblées sur le modèle de `mettre_a_jour_scoring` :
   `enregistrer_email_linkedin` et `enregistrer_coordonnees_web`, renvoyant un
   `RapportCoordonnees` (patron `RapportReimport`) portant les contradictions et les statuts
   préservés.
3. `profile_store.py` — sélection du reliquat en **fonctions pures** sur une liste de dicts,
   testables sans base : `profils_a_visiter`, `profils_a_enrichir`.
4. `csv_export.py` — 3 colonnes en fin de `PROFILE_CSV_FIELDS` + constante `EXPORT_CSV`.
5. `run_poc002.py` — suppression de l'import et de l'appel `search_and_extract` et de la
   constante `SEARCH_QUERY` ; entrée = reliquat du magasin, sortie = magasin. `MAX_PROFILES`
   ramené à **5** par prudence pour le premier run, comme POC-001/002 l'ont fait.
6. `run_poc004.py` — entrée = `profils_a_enrichir(selectionner_profils_interessants(...))`,
   sortie = magasin. `load_profiles` et l'import `csv` deviennent morts et sont retirés.
7. `run_poc001.py`, `run_poc003.py` — une ligne chacun pour `EXPORT_CSV` (H2). `.gitignore`.
8. Tests hors-ligne, sans navigateur ni réseau : migration (v1 → v2, idempotence, données
   préservées), marqueur écrit même sans résultat, non-régression du statut, contradiction
   rapportée, reliquats, alignement store/CSV.
9. Runs réels **un par un, jamais enchaînés**, reliquat nominatif montré avant chaque
   lancement : `run_poc002` d'abord (5 profils), `run_poc004` ensuite (5 profils, donc 5 appels
   Brave Search et non 60).
10. Relecture humaine des coordonnées trouvées avant tout passage en `valide`, puis
    rapatriement C2.

## Risque principal

L'écriture de schéma sur une base locale, gitignorée, **sans aucune sauvegarde**, contenant des
données personnelles. Mitigé par : backup hors dépôt validé avant tout `ALTER`, migration
idempotente et purement additive, aucune réécriture de donnée existante, et une suite de tests
verte sur bases temporaires avant de pointer la base réelle.

## Hors périmètre

Scoring et `config/scoring_rules.json` (POC-007 a décidé de ne rien ajuster avant retour
client) ; diversification des requêtes (POC-008) ; toute nouvelle recherche LinkedIn ; Palier 1
LLM de POC-004 ; fusion collecte/scoring/email (POC-010). Aucune des 7 questions client n'est
tranchée — ce ticket en produit une 8ᵉ.
