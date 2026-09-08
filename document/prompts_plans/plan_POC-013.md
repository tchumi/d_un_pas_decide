# Plan POC-013 — Livrable Excel client et boucle de retour au format xlsx

> Plan validé par l'utilisateur le 08/09/2026, depuis le **laptop en itinérance**.
> Prompt source : `document/prompts_plans/prompt_POC-013.md`.

## Résumé

Livrer à Christophe et Henri-Pierre un `.xlsx` exploitable (tri, filtres) et savoir relire le
fichier annoté qu'ils renverront. L'export CSV n'est **pas** retouché : on ajoute une conversion
CSV → xlsx, et un chemin de lecture xlsx → `list[dict[str, str]]`. Le risque n'est pas le code
mais ce qu'Excel fait aux données en chemin. Échéance ferme : fin de la semaine du 08/09/2026.

## Arbitrages tranchés par l'utilisateur au cadrage (08/09/2026)

1. **Bascule xlsx → lignes : option A.** `run_poc006` convertit le `.xlsx` en CSV normalisé
   voisin, puis le pipeline actuel tourne dessus **sans une ligne modifiée dans
   `profile_store.py`** — le module qui porte les règles de conflit acquises de POC-006 et
   POC-009 n'est pas touché, et il est hors du périmètre autorisé du prompt. L'option B (ajouter
   un paramètre `lignes` à `importer_commentaires_csv`) est écartée pour cette raison.
   Bénéfice secondaire retenu : le CSV intermédiaire est une **trace inspectable** de ce qu'Excel
   a rendu, et sur un fichier non annoté il doit être identique au CSV d'origine — c'est un
   levier de vérification direct pour le critère d'acceptation.
2. **Mise en forme Excel : minimum strict accepté** — figeage de la ligne d'en-tête et filtre
   automatique, **rien d'autre** (pas de largeurs, pas de styles, pas de couleurs). Aucune valeur
   n'est touchée, donc « convertir sans modifier » est préservé.
3. **Lignes livrées : le CSV intégral**, soit les 81 profils moins les `ne_plus_traiter`, sans
   filtre de seuil. Cohérent avec un client qui a dit vouloir trier et filtrer lui-même. La
   question ouverte du Backlog (81 vs 65 au-dessus du seuil) est donc tranchée : **81, intégral**.

## Risque principal

La normalisation en texte à la relecture. [Code] `csv.DictReader` rend des `str` ; openpyxl rend
des `int`, `float`, `datetime` et `None`. [Code] `_importer_statut_coordonnees` fait
`.strip().lower()` sur la cellule : un `None` lève, un `4.0` au lieu de `4` fausse la comparaison
de `_STATUTS_IMPORTABLES`.

**Piège aggravant vérifié le 08/09/2026** : [Code] `run_poc006.main` appelle `enregistrer_profils`
**avant** `importer_commentaires_csv` — c'est cette première passe qui écrirait en base une valeur
reformatée par Excel. `titre`, `categorie`, `score`, `justification` sont dans
`_CHAMPS_COMPLETABLES` et donc exposés ; `date_collecte` et `ne_plus_traiter` n'y sont pas et sont
protégés sur un profil connu.

**Parade en deux temps** :
* à l'écriture, toutes les cellules sont écrites **en texte** (openpyxl ne retype pas les `str`
  depuis la 2.4) ;
* à la lecture, tout est ramené en `str` : `None` → `""`, `datetime` → ISO, `float` entier sans
  le `.0`.

## Étapes

1. **Dépendance** : `openpyxl` dans `pyproject.toml`, `uv sync --extra test`. Vérifier que les
   123 tests passent toujours.
2. **`source/backend/adapters/storage/xlsx_export.py`** (nouveau) :
   `convertir_csv_en_xlsx`, `lire_xlsx -> list[dict[str, str]]` avec la normalisation texte,
   `xlsx_vers_csv`, et la validation d'en-tête **bloquante**.
3. **`source/backend/adapters/storage/run_poc013.py`** (nouveau) : produit
   `profils_magasin.xlsx` depuis `profils_magasin.csv`. Aucun autre `run_pocNNN.py` touché.
4. **`source/backend/adapters/storage/run_poc006.py`** : si l'entrée est un `.xlsx`, la convertir
   d'abord en CSV normalisé voisin, puis dérouler **exactement le chemin actuel** sur ce CSV.

## Tests prévus (`tests/unit/test_xlsx_export.py`)

| # | Test |
|---|---|
| 1 | Aller-retour CSV → xlsx → lignes relues **égales** aux dicts de `csv.DictReader` sur le CSV source |
| 2 | En-tête : 16 colonnes, même ordre, ligne 1 |
| 3 | Cellule vide → `""`, jamais `None` |
| 4 | xlsx forgé avec `int` / `float` / `datetime` / `None` → tout ressort en `str` propre |
| 5 | Nom à emoji (les 2 profils réels) survit à l'aller-retour |
| 6 | `justification` longue avec virgules, `;` et retour-ligne survit |
| 7 | `url` relue en texte, pas en objet lien |
| 8-10 | En-tête non conforme : colonne insérée, supprimée, réordonnée → erreur explicite et bloquante |
| 11 | Classeur vide / sans en-tête → erreur explicite |
| 12 | Aiguillage `run_poc006` : `.xlsx` et `.csv` mènent au même état de base |

Non-régression : `tests/unit/test_profile_store.py` et la suite complète. Départ **123 passed**.

## Critère d'acceptation

Aller-retour vérifié **sur le magasin réel** (81 profils) : sauvegarde datée de `profils.db` →
export → conversion `.xlsx` → annotation de quelques `commentaire_client` → ré-import du `.xlsx`
→ commentaires en base **et aucune autre colonne modifiée**, vérifié ligne à ligne contre la
sauvegarde.

## Hors périmètre

Toute modification du contenu de l'export (colonnes, ordre, valeurs) ; `profile_store.py` ;
`csv_export.py` ; le scoring et ses règles ; les règles de conflit du ré-import ; toute migration
de schéma ; tout refactoring ou renommage.
