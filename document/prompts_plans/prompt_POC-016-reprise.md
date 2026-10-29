Tu travailles dans le repo ProspectionLinkedIn avec Claude Code dans VS Code.

Je viens de faire un /clear. Tu reprends **POC-016 en cours de session**, interrompue le
29/10/2026 juste avant le relevé de DOM. Ne relis pas tout le repository.

> Contexte : session préparatoire avant le call client du **05/11/2026 (après-midi)**. Les
> sauvegardes vont dans `D:\Documents\Dev\_backup_prospection\`. **Ce n'est pas une fin de
> session** : `task_list.md`, `handoff.md`, `Backlog.md` et `CLAUDE.md` n'ont pas encore été mis
> à jour pour POC-016 — ce sera fait à la clôture.

## Documents à lire en premier

1. `CLAUDE.md`
2. `document/prompts_plans/plan_POC-016.md` — **le plan validé**, avec les décisions de
   l'utilisateur, les réponses proposées au client et le tableau hors ligne / run réel
3. `document/prompts_plans/prompt_POC-016.md` — le prompt d'origine (périmètre, critères
   d'acceptation, risques)

Puis le code produit par la session :

* `source/backend/core/parcours.py` — en entier
* `source/backend/adapters/scraping/run_poc002.py` — en entier
* `source/backend/adapters/scraping/profile_email.py` — les fonctions ajoutées
  (`scroll_profile_page`, `extract_section_text`, `extract_rubriques_from_profile_page`)
* `source/backend/adapters/scraping/selectors.py` — `LinkedInProfileSelectors`

## Ce qui est fait (commits sur `master`)

| Commit | Contenu |
|---|---|
| `1a26fc3` | `docs:` plan POC-016 |
| `c42a30a` | `fix:` `run_poc002` ne visite plus que les profils au seuil — `selectionner_reliquat` (sélection au seuil puis reliquat, comme `run_poc004`). Reliquat réel : **97 profils** |
| `f0f8001` | `feat:` signaux de parcours (`core/parcours.py`), lecture des rubriques, mode `--releve` de `run_poc002` |

* **Signaux** lus dans la **structure** du texte « Expérience » (lignes de dates), pas dans des
  mots-clés : nombre de postes, postes en cours, coach en cours et ancienneté, **autre poste en
  cours** (piste du « multi-fonction »), ancien dirigeant (poste de direction terminé), liste
  tronquée (« Afficher les N expériences »), longueur de « Infos ». Texte vide → signaux vides,
  jamais d'erreur.
* **Sélecteurs** : sections trouvées par leur titre visible (« Expérience »/« Experience »,
  « Infos »/« About »), **marqués NON VÉRIFIÉS** dans `selectors.py`.
* **Mode `--releve`** : magasin ouvert en lecture seule, rien n'est écrit (pas même le marqueur de
  visite), 5 URL au plus, toutes présentes dans le magasin ; en cas de section absente, titres de
  section affichés et page écrite dans `tests/temp/poc016_releve_N.html` (gitignoré, **données
  personnelles, à supprimer après usage**).
* **`core/parcours.py` est hors du périmètre initial du prompt** : placé dans `core/` parce que le
  scoring le lira. Signalé à l'utilisateur, pas encore confirmé.
* **Mesure en mémoire de `profil_dirigeant` neutralisé** (règles candidates dans le scratchpad,
  `config/scoring_rules.json` intact) :

| | Seuil 60 lot 1 / lot 2 | ≥ 80, lot 1 (81) | ≥ 80, lot 2 (50) |
|---|---|---|---|
| v2 actuelle | 43 % / 46 % | 21 profils, 16 bons, 6/6 excellents | 7 profils, 2 bons, 0/3 |
| sans `profil_dirigeant` | 44 % / 46 % | 13 profils, 9 bons, **2/6** | 4 profils, 1 bon, 0/3 |

  Recommandation : **garder la règle** jusqu'à ce qu'un signal de parcours la remplace ; décision
  au call.

## État vérifié au 29/10/2026

* Tests : **295 passed** (277 au départ du ticket).
* Magasin **non modifié** : 131 profils, 131 commentaires, `user_version` 2, empreinte MD5
  `189e64e0f6c1aa234851422686103ff5`. 101 profils au seuil, 97 jamais visités.
* Arbre Git propre après les commits ci-dessus (plus ce prompt).

## Prochaine étape : le relevé de DOM (run réel, lancé par l'utilisateur)

5 visites, aucune écriture en base. Profils choisis pour la discrimination : les quatre premiers
ont **le même titre « Coach professionnel » et le même score 60**, verdicts opposés ; le dernier
est un faux positif de tête.

```powershell
uv run python -m source.backend.adapters.scraping.run_poc002 --releve https://www.linkedin.com/in/adderusoutplacementcoaching/ https://www.linkedin.com/in/c%C3%A9cile-belot-213a92a6/ https://www.linkedin.com/in/magali-lafaye-0907b529a/ https://www.linkedin.com/in/patrick-sisco-0b4663254/ https://www.linkedin.com/in/narjess-kalifa-a633a03b0/
```

| # | Profil | Score | Verdict client |
|---|---|---|---|
| 1 | Edouard Pierre | 60 | excellent |
| 2 | Cécile BELOT | 60 | bon |
| 3 | Magali LAFAYE | 60 | mauvais, multi fonction |
| 4 | Patrick Sisco | 60 | mauvais |
| 5 | Narjess KALIFA | 100 | mauvais, multi fonction |

L'utilisateur colle la sortie. Trois questions à y lire :

1. **Les sélecteurs trouvent-ils les sections ?** Sinon, corriger `selectors.py` à partir des
   titres affichés et de la page écrite dans `tests/temp/`, puis demander un nouveau relevé.
2. **La lecture des postes est-elle juste ?** L'utilisateur compare les postes affichés avec la
   page LinkedIn ; corriger `parcours.py` et ses tests sur un texte **synthétique** reproduisant le
   cas (jamais un texte réel dans les tests).
3. **Les signaux séparent-ils les verdicts ?** En particulier « autre poste en cours » chez les deux
   « multi fonction » et pas chez l'excellent. Cinq profils sont une illustration pour le call, pas
   une preuve.

Après le relevé : retirer le marquage « NOT YET VERIFIED » des sélecteurs confirmés et consigner le
résultat (date, sections trouvées, écarts) en commentaire, comme pour le lien « Coordonnées ».

## Ce qui reste avant le call (hors ligne)

* Code de migration v3 **écrit et testé sur base temporaire, sans être appliqué** au magasin —
  colonnes selon la réponse du client à la question 2 (texte brut temporaire ou signaux seuls).
* Envoi au client, par l'utilisateur, des **réponses proposées aux questions 1 à 5** (tableau du
  plan) pour validation avant ou pendant le call. La question 4 (« qu'est-ce que pratiquer le
  coaching ») est celle qui fera la règle.

## Interdit avant l'accord du client (call du 05/11)

* appliquer une migration au magasin réel ;
* écrire du texte de parcours dans le magasin ;
* modifier `config/scoring_rules.json`.

## Rappels

* **Les runs LinkedIn réels sont lancés par l'utilisateur** : préparer, donner la commande,
  attendre la sortie collée. Plafonds validés : 5, puis 10, puis 20 par run.
* Avant tout run qui écrit le magasin : sauvegarde datée du magasin et de `journal_collecte.csv`,
  puis contrôle des `commentaire_client` contre la sauvegarde.
* Mesure de l'apport, après le call : signaux réglés sur les profils au seuil du lot 1 (60),
  mesurés sur ceux du lot 2 (41) — ne pas régler et mesurer sur les mêmes profils.
* Réponses en français, commentaires de code en anglais, affirmations taguées
  [Code] / [Documentation] / [Inférence].

## Première réponse attendue

Ne modifie aucun fichier. Vérifie la branche, l'état Git, la suite de tests (295) et l'empreinte du
magasin, résume en 5 lignes où en est la session, puis attends la sortie du relevé.
