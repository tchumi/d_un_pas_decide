# Plan POC-006 — Renouvellement du gisement de profils (mémoire des profils déjà vus)

Plan validé par l'utilisateur le 26/08/2026. Branche `master`, arbre propre au démarrage.

## 0. Constat vérifié dans le code au démarrage (26/08/2026)

1. [Code] `search_and_extract` (`profile_search.py`) fait `page.goto(build_search_url(...))` —
   toujours la page 1 — puis boucle `while len(results) < max_profiles`.
   `extract_profiles_from_page` retient les cartes dans l'ordre du DOM jusqu'au quota. Aucun
   paramètre d'exclusion : la pagination ne fait que compléter le lot.
2. [Code] `export_profiles_to_csv` (`csv_export.py`) : `open(output_path, "w", ...)`.
   Écrasement total, aucune lecture préalable.
3. [Code] Complément : `run_poc003.py` lit `profils_extraits.csv` (brut, sans
   `commentaire_client`) et écrit `profils_extraits_scores.csv` — le `setdefault` de
   `scorer_profils` ne protège donc jamais rien en pratique.
4. [Code] `.gitignore` lignes 16-18 couvrent déjà `*.db` / `*.sqlite` / `*.sqlite3` — le
   magasin est protégé sans rien ajouter.

## 1. Résumé

Introduire un magasin SQLite persistant des profils déjà vus, dédupliqué sur l'URL normalisée.
La recherche pagine jusqu'à obtenir N profils **inconnus** au lieu des N premières cartes, avec
raison d'arrêt explicite. Le CSV devient une vue exportée du magasin, plus la source de vérité.
Le magasin porte `date_collecte` et `ne_plus_traiter` (garde-fous RGPD de POC-004, jusqu'ici
intenables) et accueille le `commentaire_client` ré-importé d'un CSV annoté. Tout est
développable et testable hors-ligne ; seule la validation finale demande deux runs réels.

## 2. Fichiers

| Fichier | Action |
|---|---|
| `source/backend/adapters/storage/profile_store.py` | **créer** — magasin SQLite |
| `source/backend/adapters/storage/run_poc006.py` | **créer** — ré-import d'un CSV annoté + rapport |
| `source/backend/adapters/scraping/profile_search.py` | modifier — pagination « N inconnus » |
| `source/backend/adapters/scraping/run_poc001.py` | modifier — câblage magasin (avant/après recherche) |
| `source/backend/adapters/storage/run_poc003.py` | modifier — lit/écrit le magasin (requis par le critère 4) |
| `source/backend/adapters/storage/csv_export.py` | modifier — 2 colonnes ajoutées |
| `tests/unit/test_profile_store.py` | **créer** |
| `tests/unit/test_profile_search.py` | étendre |
| `tests/unit/test_csv_export.py` | étendre (2 nouvelles colonnes) |

## 3. Schéma SQLite

`PRAGMA user_version = 1` — création seule, aucune migration (règle CLAUDE.md n°5).

```sql
CREATE TABLE IF NOT EXISTS profils (
    url                TEXT PRIMARY KEY,   -- cle de dedup, normalisee par clean_profile_url
    nom                TEXT NOT NULL DEFAULT '',
    localisation       TEXT NOT NULL DEFAULT '',
    titre              TEXT NOT NULL DEFAULT '',
    email              TEXT NOT NULL DEFAULT '',   -- POC-002
    email_web          TEXT NOT NULL DEFAULT '',   -- POC-004
    site_web           TEXT NOT NULL DEFAULT '',   -- POC-004
    categorie          TEXT NOT NULL DEFAULT '',   -- POC-003
    score              TEXT NOT NULL DEFAULT '',   -- POC-003
    justification      TEXT NOT NULL DEFAULT '',   -- POC-003
    commentaire_client TEXT NOT NULL DEFAULT '',   -- retour client, re-importable
    date_collecte      TEXT NOT NULL,              -- ISO 8601, RGPD conservation limitee
    ne_plus_traiter    INTEGER NOT NULL DEFAULT 0  -- RGPD droit d'opposition
);
```

- **Minimisation** : aucune nouvelle catégorie de donnée personnelle — les 11 colonnes sont
  celles déjà justifiées par POC-001/002/003/004, `date_collecte` et `ne_plus_traiter` sont des
  métadonnées de gouvernance.
- `score` en `TEXT` : le pipeline CSV manipule des chaînes de bout en bout
  (`enrichi["score"] = str(...)`) ; un `INTEGER` introduirait des conversions et un cas
  « non scoré » ambigu.
- `date_collecte` est **figée à la première insertion**, jamais réécrite — c'est ce qui rend une
  purge future possible.
- API : `ouvrir_magasin`, `urls_connues`, `enregistrer_profils`, `mettre_a_jour_scoring`,
  `lister_profils`, `marquer_ne_plus_traiter`, `importer_commentaires_csv`.
- **Règle d'écriture** : `enregistrer_profils` n'écrase jamais un champ rempli par une valeur
  vide (critère 3).
- `urls_connues` **inclut** les profils `ne_plus_traiter=1` → le droit d'opposition exclut des
  collectes futures par le même mécanisme que la déduplication ; `lister_profils` les exclut de
  l'export par défaut.

## 4. Pagination « jusqu'à N inconnus »

Découpage cœur pur / coquille, testable sans navigateur :

```python
def filtrer_profils_inconnus(profils, urls_exclues) -> list[dict]                  # pur
def collecter_profils_inconnus(extraire_page, page_suivante, max_profiles,
                               urls_connues, max_pages=10) -> ResultatRecherche    # pur, injecte
def search_and_extract(page, boolean_query, max_profiles,
                       urls_connues=frozenset(), max_pages=10) -> ResultatRecherche # coquille
```

`ResultatRecherche(profils, raison_arret, pages_visitees)` avec
`raison_arret ∈ {quota_atteint, gisement_epuise, plafond_pages}` — critère 2 : lot plus petit +
message clair, jamais de boucle infinie (double garde : `go_to_next_page() is False` **et**
`max_pages=10`, [Inférence] plafond du compte gratuit). `urls_connues` par défaut vide → aucun
appelant existant cassé.

## 5. Tests prévus (unitaires, zéro navigateur, zéro réseau, `tmp_path`)

**Magasin** : création idempotente ; insertion des nouveaux / doublons ignorés ; pas
d'écrasement d'un champ rempli par du vide (**critère 3**) ; `date_collecte` figée ;
`marquer_ne_plus_traiter` → profil **inclus** dans `urls_connues` (donc jamais réextrait) et
exclu de l'export.

**Recherche** : `filtrer_profils_inconnus` (URL connue, doublon intra-lot, URL vide) ; deux
collectes successives sur le même gisement simulé → **lots disjoints (critère 1)** ; gisement
épuisé → lot partiel + `raison_arret="gisement_epuise"` (**critère 2**) ; plafond de pages.

**Ré-import (critère 4)** : aller-retour **réel** — magasin → export CSV → annotation du CSV →
`importer_commentaires_csv` → `scorer_profils` → ré-export, commentaire intact. Plus : conflit,
CSV vide, URL absente du magasin.

Base de départ : 67 passants (**critère 6**).

## 6. Décisions validées par l'utilisateur le 26/08/2026

1. **Règle de conflit sur `commentaire_client`** :

   | Magasin | CSV client | Comportement |
   |---|---|---|
   | vide | rempli | écrit |
   | rempli | vide | **conservé** (un blanc n'efface jamais un retour) |
   | rempli | rempli, différent | **le CSV client prime**, substitution **listée dans le rapport** — jamais silencieuse |
   | — | URL absente du magasin | non créée, comptée en « ignorées » |

   Clé de réconciliation : l'URL passée par `clean_profile_url`, **même clé que la
   déduplication**, importée depuis `profile_search` (dupliquer la normalisation dans
   `storage/` serait la vraie erreur ; déplacer la fonction serait un refactoring hors
   périmètre).

2. **`run_poc003.py` lit désormais le magasin** au lieu de `profils_extraits.csv` — nécessaire
   au critère 4.

3. **`date_collecte` et `ne_plus_traiter` sont des colonnes exportées** (décision utilisateur :
   visibles pour le client). Conséquence : le ré-import lit aussi `ne_plus_traiter` (le client
   peut exprimer une opposition directement dans le CSV) ; un `0`/vide **ne lève jamais** un
   marquage existant — seule une action délibérée le fait.

4. **Volume des deux runs réels de validation : `max_profiles=25`** (inchangé par rapport à
   POC-001).

5. **Diversification des requêtes → ticket suivant (POC-007)**, pas dans POC-006. Le Backlog a
   déjà tranché l'ordre le 26/08 ; la diversification (facettes géographiques natives,
   vocabulaire outdoor) exige des runs LinkedIn réels pour valider les sélecteurs de facettes,
   ce qui ferait perdre à POC-006 sa propriété d'être entièrement testable hors-ligne et
   mélangerait deux causes d'échec dans un même run.
