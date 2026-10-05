# Plan POC-015 — Colonne département dans l'export

Plan validé par l'utilisateur le 05/10/2026 (« ok pour les recommandations »).

## État vérifié au départ

- Branche `master`, arbre propre, **172 passed**.
- [Code, lecture seule `mode=ro`] Magasin : 81 profils, 81 commentaires client, `user_version` 2,
  MD5 `7bf1cbb0fa4d015ade51ab9a942e4f41`.
- [Code] Formats de `localisation` remesurés, identiques au 16/09/2026 :

| Format | Profils | Détail |
|---|---|---|
| « Ville, Région, France » | 52 | 41 libellés distincts |
| « Région, France » | 1 | Pays de la Loire |
| « X et périphérie » | 20 | Paris 12, Lille 2, Lyon 2, Angers, Clermont-Ferrand, Nice, Toulon |
| Pays seul | 8 | France 6, Espagne 1, Suisse 1 |

## Décisions

1. **Une seule colonne `departement`**, au format « 67 - Bas-Rhin » : triable en texte, numéro et
   nom ensemble, une seule colonne ajoutée à l'en-tête.
2. **Colonne dérivée à l'export**, jamais stockée : pas de migration, aucune écriture en base.
3. **Position** : juste après `localisation`.
4. **Ancien classeur à 16 colonnes : accepté au ré-import**, avec un message explicite « ancien
   format reconnu ». La colonne manquante n'est jamais importée, donc rien n'est perdu. Tout autre
   écart d'en-tête reste refusé ; l'export (CSV → xlsx) reste strict.
5. **Table** : Code officiel géographique de l'INSEE, téléchargé une fois pendant le développement
   puis versionné dans `config/`. Aucun appel réseau à l'exécution. Clé (commune normalisée,
   région) ; la fonction ne répond que si un seul département correspond.
6. **Régénération** par un nouveau script `run_poc015.py` **en lecture seule** : il exporte le CSV,
   produit le classeur et affiche le nombre de rattachés et de vides. Le magasin n'est pas écrit.
7. **« X et périphérie » reste vide dans tous les cas** : une aire urbaine LinkedIn n'est pas un
   département.

## Fichiers

- À créer : `source/backend/core/departement.py`, la table dans `config/`,
  `source/backend/adapters/storage/run_poc015.py`, `tests/unit/test_departement.py`.
- À modifier : `source/backend/adapters/storage/csv_export.py` (colonne et dérivation dans
  `export_profiles_to_csv`, aucun des 4 scripts appelants ne change),
  `source/backend/adapters/storage/xlsx_export.py` (`_valider_entete`, docstrings),
  `tests/unit/test_csv_export.py`, `tests/unit/test_xlsx_export.py`,
  `tests/unit/test_profile_store.py` (le garde-fou `PROFILE_COLUMNS == PROFILE_CSV_FIELDS` devient
  « égal hors colonnes dérivées »).
- Non touché : `profile_store.py`, `run_poc006.py` sauf si le message « ancien format » l'exige.

## Risque principal

[Code] La colonne dérivée ne peut pas entrer en base par le chemin actuel : `enregistrer_profils`
ne lit que `_CHAMPS_COMPLETABLES`, `importer_commentaires_csv` ne lit que `url`,
`commentaire_client`, `ne_plus_traiter` et `statut_coordonnees`. Un test le verrouille.

Le risque réel est de deviner un département. Deux homonymes attendus dans les 81 [Inférence, à
confirmer par la table] : Floirac (Gironde et Charente-Maritime, même région) et Vougy (Loire et
Haute-Savoie, même région). Ces cellules restent vides.

## Tests prévus

- Dérivation : cas nominal, accents, casse, apostrophes, « Ville de Paris », homonyme dans la même
  région, commune inconnue, « et périphérie », région seule, pays seul, étranger, chaîne vide.
- Export CSV : colonne à la bonne position, toujours recalculée même si le dict entrant porte une
  valeur.
- Aller-retour xlsx : le classeur à 17 colonnes, annoté puis ré-importé, ne modifie que
  `commentaire_client` et `statut_coordonnees` ; une cellule département modifiée par le client
  n'entre pas en base ; l'ancien classeur à 16 colonnes est accepté et signalé.

## Étapes

1. Table et fonction pure, avec leurs tests.
2. Colonne dans `csv_export.py`, garde-fou d'alignement adapté, tests.
3. `_valider_entete` : ancien format accepté au ré-import, tests d'aller-retour.
4. Données réelles : `run_poc015`, comptage rattachés / vides, contrôle de l'aller-retour, MD5 du
   magasin inchangé.
5. Fin de session : les quatre fichiers, prompt POC-008, commit.

Couverture attendue : 50 rattachés, 31 vides (20 « périphérie », 8 pays seuls, 1 région seule,
2 homonymes) [Inférence, à confirmer à l'étape 4].
