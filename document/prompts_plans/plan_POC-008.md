# Plan POC-008 — Diversification des requêtes (découpage géographique)

Plan validé par l'utilisateur le 06/10/2026 (réponses A à E « selon les recommandations »).

## État vérifié au démarrage

- Branche `master`, arbre propre, HEAD `124280f`.
- Magasin, en lecture seule : 81 profils, 81 `commentaire_client`, `user_version` 2, MD5
  `7bf1cbb0fa4d015ade51ab9a942e4f41`.
- [Code] `search_and_extract` n'a qu'un appelant (`run_poc001.main`) ; `build_search_url` n'est
  appelé que par `search_and_extract` et un test ; `SEARCH_QUERY` n'existe que dans `run_poc001.py`.
- [Code] La table `profils` (16 colonnes) ne porte pas la requête d'origine.

## Résumé

Sortir la requête de `run_poc001.py` vers un fichier de `config/` validé au chargement, parcourir
plusieurs requêtes en séquence avec déduplication entre elles, et découper la recherche par région
avec la facette native LinkedIn (paramètre d'URL à vérifier sur un run réel). Produire ensuite un
lot de profils nouveaux, scoré en v2 inchangée, exporté avec le département, sans toucher aux 81
commentaires client.

## Décisions validées

- **A — Requêtes** : la requête actuelle reprise à l'identique en première entrée, puis son
  vocabulaire découpé par région, entrées étiquetées `provisoire`. Pas de requête outdoor dans ce
  lot. La requête « executive coach / coach de dirigeants » (mots de la grille client du
  11/09/2026) reste une **option à confirmer** avant le run de production : elle n'est pas ajoutée
  d'office.
- **B — Découpage** : région seule (13 régions métropolitaines, DROM exclus). Le texte
  `AND (France)` est retiré des requêtes régionales, la facette le remplace ; il reste dans la
  requête historique, inchangée.
- **C — Plafonds** : premier run réel 1 région, 2 pages, 10 profils au plus. Runs suivants : au
  plus 5 requêtes par session, 3 pages par requête, 50 profils nouveaux, sur 2 à 3 sessions à des
  jours différents. Chaque run réel est validé séparément.
- **D — Traçage** : journal à part, CSV gitignoré (date, URL, identifiant et libellé de requête),
  écrit pour les seuls profils réellement ajoutés au magasin. **Aucune migration**, export
  inchangé à 17 colonnes.
- **E — Taille du lot** : 50 profils nouveaux.

## Fichiers

| Fichier | Action |
|---|---|
| `config/requetes_recherche.json` | créer : plafond du run, requêtes (`id`, `libelle`, `mots_cles`, `lieu` optionnel, `max_pages` optionnel, `provisoire`, `active`) |
| `source/backend/core/requetes_recherche.py` | créer : chargement et validation, erreur explicite |
| `source/backend/adapters/scraping/profile_search.py` | facette optionnelle dans `build_search_url` et `search_and_extract` ; boucle pure `parcourir_requetes` |
| `source/backend/adapters/scraping/run_poc001.py` | charge la configuration, parcourt les requêtes, bilan par requête, journal |
| `source/backend/adapters/scraping/selectors.py` | après le run réel seulement : barre de pagination numérotée |
| `source/backend/adapters/storage/journal_collecte.py` | créer (**écart au périmètre du prompt, validé**) |
| `.gitignore` | une ligne pour le journal (**écart validé** : il contient des URL de profils) |
| `tests/unit/test_requetes_recherche.py`, `tests/unit/test_journal_collecte.py` | créer |
| `tests/unit/test_profile_search.py` | compléter |

## Risques

- **Compte LinkedIn** : 13 régions, c'est 13 recherches là où il y en avait une. Plafonds en
  configuration, validation distincte avant chaque run réel, premier run petit.
- **Facette ignorée** : [Inférence] le paramètre serait `geoUrn=["<id>"]`. Les identifiants de
  région ne sont pas supposés : ils sont lus dans l'URL après application du filtre « Lieux » dans
  le navigateur, puis contrôlés sur la localisation des profils ramenés.
- **Homogénéité** : [Inférence] le découpage par région règle le volume, pas la variété du
  vocabulaire.

## Tests prévus

- Chargement : fichier valide, absent, JSON malformé, liste vide, `id` en double, `mots_cles`
  vide, libellé manquant, lieu sans identifiant, plafond invalide.
- La première entrée du vrai fichier est égale, caractère pour caractère, à la chaîne historique.
- `build_search_url` : sans facette, URL strictement inchangée ; avec facette, paramètre encodé.
- `parcourir_requetes` (recherche injectée) : ordre, `urls_connues` enrichi d'une requête à la
  suivante, pas de doublon entre requêtes qui se recouvrent, bilan et raison d'arrêt par requête,
  arrêt au plafond global.
- Journal : en-tête écrit une fois, ajout sans écrasement.
- Suite complète : partir de 214 passed, ne rien casser.

## Étapes

**Volet hors-ligne**

1. Fichier de requêtes et chargeur validé dans `core/`, requête actuelle en première entrée, tests.
2. Facette optionnelle, boucle `parcourir_requetes`, câblage de `run_poc001`, journal d'origine,
   tests. Avec une configuration à une seule entrée, le run se comporte comme avant.

**Volet à run réel, chacun validé séparément**

3. Run de vérification après sauvegarde datée du magasin : une région, plafond minimal. Lecture du
   paramètre de facette dans l'URL, contrôle des localisations ramenées, relevé de la barre de
   pagination et de la taille du gisement.
4. Runs de production plafonnés sur les régions, puis `run_poc003` (règles v2 inchangées),
   `run_poc015`, comptages par requête, région et tranche de score, contrôle des 81 commentaires
   contre la sauvegarde.
5. Fin de session : les quatre fichiers, le prompt POC-016, le commit.
