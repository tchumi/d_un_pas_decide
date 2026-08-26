# Plan POC-003 — Scoring et catégorisation des profils (Phase 2)

Plan validé par l'utilisateur le 26/08/2026. Branche `master`, working tree propre au démarrage.

## 1. Résumé

Catégoriser et scorer les 25 profils déjà extraits (`profils_extraits.csv`), **sans nouvelle
extraction LinkedIn et sans appel LLM** : moteur de règles déterministe sur le seul signal
textuel disponible, le `titre`. Chaque profil sort avec `categorie`, `score`, `justification`
(règles ayant matché, demandée par le client le 04/07/2026) et `commentaire_client` (retour de
pertinence, colonne vide à remplir par le client). La distinction débutant/expérimenté est
**hors scope** (non décidable depuis le titre) → repli `coach_business_indifferencie`.
Le module expose de quoi sélectionner un sous-ensemble « intéressant » en aval, pour
l'enrichissement POC-004 devenu conditionnel (décision client 13/07/2026), **sans modifier
POC-004**.

[Documentation] Sources : `Backlog.md` sections POC-003 (calibration client des 04/07 et
08/07/2026) et POC-004 (décisions du 13/07/2026).

## 2. État vérifié avant modification

- [Code] Branche `master`, `git status --short` vide.
- [Code] `profils_extraits.csv` présent : 26 lignes (25 profils + en-tête), colonnes
  `nom,url,localisation,titre` conformes. Fichier gitignoré (données personnelles).
- [Code] `source/backend/core/` **n'existe pas encore** — à créer.
- [Code] `source/frontend_streamlit/` n'existe pas encore : le menu configuration est **à
  prévoir**, hors périmètre de ce ticket.

## 3. Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `source/backend/core/__init__.py` | créer (package) |
| `source/backend/core/profile_scoring.py` | créer — logique pure, zéro import Streamlit/Playwright, zéro réseau |
| `config/scoring_rules.json` | créer — règles de scoring encodées, éditables |
| `source/backend/adapters/storage/run_poc003.py` | créer — script d'assemblage CSV → scoring → CSV |
| `source/backend/adapters/storage/csv_export.py` | modifier — +4 colonnes, `restval=""` |
| `tests/unit/test_profile_scoring.py` | créer |
| `tests/unit/test_csv_export.py` | modifier — nouvelles colonnes |
| `.gitignore` | modifier — ajout du CSV de sortie |

[Inférence] Le script d'assemblage va dans `adapters/storage/` et non dans `core/` : `core/`
ne doit pas importer d'adapter (AGENTS.md §4), et ce script est une coquille impérative
CSV → CSV. Même esprit que `run_poc001.py` / `run_poc004.py`, colocalisés avec leur adapter.

## 4. Règles de scoring (échelle 0–100)

Normalisation préalable du titre **et** des mots-clés : minuscules, accents supprimés,
ponctuation → espaces. Gère `coach-professionnel`, `coach d'entreprise`, `Coach Professionnelle`.

| Règle | Type | Poids | Déclencheur |
|---|---|---|---|
| `exclusion_non_coach` | exclusion (absence) | → exclu, score 0 | aucune occurrence de `coach` |
| `exclusion_hors_metier` | exclusion (présence) | → exclu, score 0 | `coach de vie`, `life coach` |
| `base_coach` | bonus | +20 | marqueur `coach` présent |
| `focus_business` | bonus | +40 | `coach business`, `business coach`, `coach d'entreprise`, `coach en entreprise`, `coach professionnel`, `coaching professionnel`, `executive coach`, `coach de dirigeant`, `coach d'équipe` |
| `certification` | bonus | +15 | `icf`, `rncp`, `certifi`, `accredit`, `level 2`, `pcc`, `mcc` |
| `cible_business` | bonus | +10 | `dirigeant`, `entrepreneur`, `manager`, `management`, `leadership`, `executive`, `business`, `entreprise`, `équipe`, `commercial` |
| `hors_cible` | malus | −25 | `développement personnel`, `scolaire` (malus **sans** exclusion — cas Anne-Laure F.) |

Chaque règle s'applique **une seule fois**, quel que soit le nombre de mots-clés matchés.
Score final borné à `[0, 100]`.

**Catégories** : `exclu` / `coach_outdoor` (mots-clés fournis par le client : *coach nature*,
*coach qui marche*, *coach outdoor*, *coach hors-les-murs*, *coaching en itinérance*) /
`coach_business_indifferencie` (défaut). L'outdoor est **score-neutre** : le client n'a jamais
indiqué qu'un profil outdoor valait plus ou moins qu'un autre.

**Profils exclus conservés dans le CSV** avec `categorie=exclu, score=0` plutôt que supprimés
silencieusement (AGENTS.md §3, pas de correction silencieuse de données métier).

**Titre vide** → `exclusion_non_coach` (pas de marqueur coach) → exclu, score 0.

### Décisions de calibration prises avec l'utilisateur le 26/08/2026

1. **Seuil « profil intéressant » = 60**, fixé pour cadrer les idées, **paramétrable** :
   stocké dans le JSON et surchargeable par argument. À exposer dans le futur menu
   configuration (à prévoir, hors périmètre).
2. **`coach de vie` / `life coach` → exclusion** (et non malus). [Inférence] Lecture littérale
   de la réponse utilisateur ; aucun profil du lot de 25 n'est concerné, le critère
   d'acceptation n'est donc pas affecté. Repasser en malus = déplacer la règle dans le JSON.
   Risque documenté : un titre mixte (« business coach et life coach ») serait exclu à tort.
3. **Pas de malus sur `coach professionnel en formation`** (Séverine GRAVOT, Jérémy Azoulay) :
   le client a validé les 23 profils en bloc le 08/07/2026.
4. **CSV de sortie** : `profils_extraits_scores.csv` (gitignoré, données personnelles).
5. **Colonne `commentaire_client`** : vide à l'export, destinée au retour du client sur la
   pertinence du critère / du score.
6. **Règles encodées en JSON** (`config/scoring_rules.json`), avec `charger_regles()` /
   `sauvegarder_regles()` dans `core/` pour permettre édition et sauvegarde depuis le futur
   menu configuration.

### Schéma du JSON de règles

```json
{
  "version": 1,
  "score_min": 0,
  "score_max": 100,
  "seuil_profil_interessant": 60,
  "categorie_exclusion": "exclu",
  "categorie_par_defaut": "coach_business_indifferencie",
  "regles": [
    {"id": "...", "type": "exclusion_absence|exclusion_presence|bonus|malus",
     "poids": 0, "mots_cles": ["..."], "libelle": "..."}
  ],
  "categories": [{"id": "coach_outdoor", "mots_cles": ["..."], "libelle": "..."}]
}
```

## 5. Point d'architecture intégré (sans coder POC-004)

Décision client du 13/07/2026 : l'enrichissement web cesse d'être systématique et devient
**conditionnel, après le scoring**, sur les seuls profils intéressants. Le module expose
`selectionner_profils_interessants(profils, seuil=None)` → sous-ensemble filtrable, prêt à
être passé en entrée de `run_poc004.py` dans un ticket ultérieur. **Aucune modification de
POC-004 dans ce ticket.**

## 6. Risque assumé et documenté

Les règles sont calibrées sur les 25 profils qui servent aussi de jeu de référence : c'est du
sur-mesure sur un échantillon minuscule. Mitigation retenue : **6 règles seulement**, aucune ne
nommant un profil ou un cas particulier, toutes lisibles et éditables depuis le JSON. La
revalidation devra se faire sur un **lot fraîchement extrait**.

## 7. Tests prévus (logique pure, sans navigateur ni réseau)

- normalisation (accents, casse, ponctuation, apostrophes typographiques) ;
- exclusion sans marqueur `coach` ; **titre vide → exclu score 0** ; exclusion `life coach` ;
- chaque règle isolée (base, focus_business, certification, cible_business, hors_cible) ;
- cumul de règles et bornage `[0, 100]` ;
- détection des 5 mots-clés outdoor + catégorie par défaut ;
- `justification` non vide et listant les règles ayant matché ;
- `selectionner_profils_interessants` au seuil (par défaut et surchargé) ;
- `charger_regles` / `sauvegarder_regles` (aller-retour) ;
- **3 tests d'acceptation sur titres réels** : Cécile Pollin exclue, Anne-Laure F. sous la
  médiane, 23 autres conservés.

## 8. Étapes

1. `config/scoring_rules.json` + `core/__init__.py` + `core/profile_scoring.py` + tests unitaires.
2. `csv_export.py` : +`categorie`, `score`, `justification`, `commentaire_client` ; mise à jour
   de `test_csv_export.py`.
3. `run_poc003.py` : lecture `profils_extraits.csv` → scoring → export
   `profils_extraits_scores.csv` ; ligne `.gitignore`.
4. Run réel + **relecture du classement complet avec l'utilisateur**, puis fin de session
   (Backlog / task_list / handoff / prompt du ticket suivant / commit).

## 9. Critère d'acceptation — résultat du prototype (validé avant implémentation)

Prototype exécuté sur les 25 profils réels : `conservés=24, exclus=1, médiane=75`.

- Cécile Pollin → `exclu`, score 0
- Anne-Laure F. → conservée, score 10, dernière du classement, très sous la médiane
- 23 autres conservés (85 ×9, 75 ×5, 70 ×5, 60 ×2, 45, 20)

Obtenu **sans aucune règle ad hoc nommant un profil**.

## 10. Lancement de l'application

**Non nécessaire** : aucun fichier `frontend_streamlit/` touché (le dossier n'existe pas).
