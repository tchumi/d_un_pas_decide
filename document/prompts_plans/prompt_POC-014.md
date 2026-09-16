Tu travailles dans le repo ProspectionLinkedIn avec Claude Code dans VS Code.

Je viens de faire un /clear pour réduire le contexte. Tu dois reprendre proprement à partir de
la documentation projet, mais sans relire tout le repository.

> Contexte de rédaction : prompt écrit le 16/09/2026 depuis le **laptop en itinérance**, après
> ré-import du retour client du 11/09/2026. Le poste principal est **éteint** : la base du laptop
> est la seule copie qui vit, et elle porte désormais 81 verdicts client qui n'existent nulle part
> ailleurs. Voir `document/claude_code/prompt_reconciliation_retour.md`.

## Ticket à traiter

Ticket : POC-014
Titre : Scoring v2 sur le titre, mesuré contre la grille de profilage du client
Objectif : Mesurer — et améliorer autant que raisonnable — ce que **le titre seul** permet de
reproduire du jugement client du 11/09/2026, sans nouvelle extraction ni run LinkedIn. Le vrai
livrable est **un chiffre honnête** : il dira si POC-016 (extraction « Expérience » et « Infos »)
est indispensable ou seulement utile.

Critère d'acceptation :

- **Un évaluateur en lecture seule** compare le score au verdict client stocké et publie, **avant
  et après** modification des règles : la matrice score × verdict, la précision au-dessus du seuil
  (part de bons ou excellents parmi les retenus), le rappel (part des bons ou excellents retenus),
  et le pouvoir discriminant par règle. Référence v1 mesurée le 16/09/2026 : **précision 40 %,
  rappel 100 %** au seuil 60, taux de base 32 % (26/81).
- **Le rappel ne baisse pas** : aujourd'hui aucun bon ni excellent profil n'est sous le seuil. Une
  v2 qui en écarte un doit le justifier explicitement et le faire valider.
- **Chaque règle ajoutée ou modifiée est rattachée à la définition du client** (texte de la grille
  ou justification écrite dans un commentaire), **jamais à un profil nommé**. Pas de mot-clé qui ne
  vise qu'une personne.
- **Les 81 `commentaire_client` sont intacts** après re-scoring — vérifié contre une sauvegarde.
- Tests : partir de **143 passed** et ne rien casser.

La branche attendue est `master` (143 tests).

## La grille du client (mail du 11/09/2026, texte exact)

- **Excellent profil** : Ancien dirigeant. Coach business qui travaille avec dirigeants et CODIRs,
  donc aussi pour des équipes
- **Bon profil** : Carrière entreprise privée. Coach business qui travaille ou pas avec des équipes.
- **Mauvais profil** : Carrière fonction publique. Coach de vie ou multicarte ou autre type de
  coaching ou de métier
- **Rien à voir** : Pas coach

Justifications libres données : « numérologie », « consultant » (×2), « coach interne », « service
aux coachs ». **Attention** : « consultant » figure aussi dans le titre d'un profil **excellent**.
Le client vise le multicarte, pas le mot.

## Périmètre autorisé

* `config/scoring_rules.json` — règles, poids, catégories.
* `source/backend/core/profile_scoring.py` — **seulement si** un nouveau type de règle ou une
  catégorie à 4 niveaux l'exige.
* Un script d'évaluation **en lecture seule** (nouveau, dans `source/backend/adapters/storage/` à
  l'image des `run_pocNNN.py`) — il ne doit **jamais** écrire dans le magasin.
* `tests/unit/test_profile_scoring.py` et un test pour l'évaluateur (verdict parsé, métriques).

Hors périmètre :
* toute extraction de nouveaux champs LinkedIn (POC-016) ; la colonne département (POC-015) ;
  le déclenchement de l'enrichissement (POC-017) ;
* **toute écriture dans `commentaire_client`** : c'est la vérité terrain ;
* toute migration de schéma — **en particulier en itinérance**, sans le dossier de sauvegardes du
  poste principal. Si une colonne `verdict_client` dédiée paraît nécessaire, la proposer comme
  arbitrage, ne pas la créer ;
* pas de refactoring global, pas de renommage de module, pas de suppression de fichier.

## Documents à lire en premier

1. `CLAUDE.md`
2. `document/claude_code/AGENTS.md`
3. `document/claude_code/handoff.md` — la **dernière section** (n°12) seulement
4. `document/Backlog.md` — uniquement `## POC-014`, la sous-section « Retour client du 11/09/2026 »
   de POC-003, et la section `## POC-007` (le précédent de sur-apprentissage)
5. `document/claude_code/task_list.md` — ligne POC-014

Puis (OBLIGATOIRE avant d'écrire une ligne) :

* `config/scoring_rules.json`
* `source/backend/core/profile_scoring.py` — `charger_regles`, `scorer_titre`, `normaliser`,
  `scorer_profils`, `selectionner_profils_interessants`
* `source/backend/adapters/storage/run_poc003.py` — le chemin de re-scoring
* `source/backend/adapters/storage/profile_store.py` — **uniquement** `mettre_a_jour_scoring` et
  `_CHAMPS_SCORING`

Ne lis pas tout le repo.

## Faits vérifiés le 16/09/2026

* **[Code] Pas de règle « Coaching Ways »** : la certification déclenche `focus_business`
  (« coach professionnel », +40) **et** `certification` (+15), d'où le bloc de profils à 75.
* **Pouvoir discriminant v1** (part de bons ou excellents quand la règle se déclenche, base 32 %) :
  `base_coach` 33 % ; `certification` **35 %, aucun signal** ; `focus_business` 39 % ;
  `cible_business` **45 %**, le plus discriminant pour le plus petit poids ; `exclusion_non_coach`
  et le malus `hors_cible` : 0 % d'erreur.
* **Matrice v1** : 85 → 3 excellents, 7 bons, 8 mauvais ; 75 → 0, 9, 17, 4 rien à voir ; 60–74 →
  3, 4, 8, 2 ; sous 60 → aucun bon ni excellent.
* **Titres des 6 excellents** : signaux d'ancien dirigeant dans la plupart (Directeur, Directeur
  associé, Co-fondateur, VP Human Resources, Executive Coach, « je coache les dirigeants »).
* **[Code] Le verdict n'a pas de colonne dédiée** : il vit dans `commentaire_client`, en texte
  libre commençant par « excellent profil », « bon profil », « mauvais profil » ou « rien à voir »,
  parfois suivi d'une virgule et d'un motif. L'évaluateur doit parser ce préfixe **et signaler**
  toute valeur qui n'y correspond pas, jamais la deviner.
* **[Code] `run_poc003` ré-écrit `categorie`, `score` et `justification`** pour tout le magasin et
  régénère `profils_magasin.csv` ; il ne touche pas `commentaire_client`.
* **Anomalie A** : « Certified Life & Business Coach » (Elise Rousseau) échappe à l'exclusion
  `life coach` parce que l'esperluette sépare les mots après normalisation — et le client la juge
  **mauvais profil**.
* **Piège de sous-chaîne (POC-007)** : les mots-clés sont appariés par sous-chaîne après
  normalisation (`mcc` capte `EMCC`, `marche` capte « marché »). Tout nouveau mot-clé court doit
  être vérifié contre les 81 titres.

## Le risque principal : le sur-apprentissage

81 profils, dont **6 excellents**. Régler des poids jusqu'à reproduire ces 81 verdicts donnerait
une précision flatteuse et fausse — exactement le défaut que POC-007 a dû lever pour POC-003.
Garde-fous :

* partir de la **définition du client**, puis mesurer — pas l'inverse ;
* préférer **peu de règles génériques** à beaucoup de règles ajustées ;
* publier les métriques v1 et v2 côte à côte, **et dire ce qu'elles ne prouvent pas** ;
* inscrire dans le Backlog que **la v2 n'est validée qu'après mesure sur le prochain lot annoté**.

## Branche et sécurité Git

```powershell
git status --short
git branch --show-current
```

La branche attendue est `master`. Ne jamais : `git reset --hard`, checkout destructif, suppression
de fichier, amend, modification hors ticket.

## Précautions propres à l'itinérance

* Vérifier le magasin **en lecture seule** avant tout, sans `ouvrir_magasin` : 81 profils,
  **81 commentaires client**, empreinte MD5 `47b767d5acca659a29511933dfa8352f`.
* **Sauvegarde datée dans `C:\Users\HP\Documents\_backup_prospection\` avant le re-scoring**
  (`run_poc003` écrit dans le magasin).
* Après re-scoring : comparer à la sauvegarde — seules `categorie`, `score` et `justification`
  doivent avoir bougé.
* **Consigner l'écriture et la nouvelle empreinte** dans
  `document/claude_code/prompt_reconciliation_retour.md`.
* Aucun run LinkedIn, aucun appel réseau.

## Méthode obligatoire

Étape 1 — Lecture et diagnostic : documents listés, puis code listé ; ne modifie aucun fichier.

Étape 2 — Plan court :
1. résumé du ticket en 5 lignes maximum ;
2. fichiers à lire ou modifier ;
3. risque principal ;
4. tests prévus ;
5. plan en 3 à 5 étapes — **l'évaluateur et la mesure v1 d'abord**, les règles ensuite ;
6. questions bloquantes éventuelles, dont : catégorie à 4 niveaux ou score seul ; projection du
   score sur les niveaux ; sort du seuil 60.

Attends ma validation. Puis sauvegarde le plan dans `document/prompts_plans/plan_POC-014.md` et
committe (`git commit -m "docs: POC-014 plan — description courte"`).

Étape 3 — Implémentation contrôlée : **évaluateur d'abord**, mesure v1 reproduite (précision 40 %,
rappel 100 %) avant de toucher une règle ; puis une modification de règles à la fois, mesurée.

Étape 4 — Vérification :

```powershell
uv run --extra test pytest tests/unit/test_profile_scoring.py -v
uv run --extra test pytest tests/ -q
uv run --extra test pytest tests/ --collect-only -q
```

Puis, sur le magasin réel : sauvegarde, re-scoring, contrôle des colonnes modifiées, métriques v2.

Étape 5 — Fin de session (OBLIGATOIRE) :
* `document/Backlog.md` — section POC-014 : métriques v1/v2, règles modifiées et leur rattachement à
  la grille client, limites ;
* `document/claude_code/task_list.md` : POC-014 → DONE avec métriques (nb tests) ;
* `document/claude_code/handoff.md` : nouvelle section ;
* `CLAUDE.md` — « État actuel » : deux lignes, aucune métrique ;
* `document/claude_code/prompt_reconciliation_retour.md` : écriture et empreinte ;
* commit : `git commit -m "docs: POC-014 DONE — description courte"`.

## Contraintes de style

* Réponses en français, commentaires de code en anglais.
* Toute affirmation importante taguée [Code] / [Documentation] / [Inférence].
* Ne corrige jamais silencieusement une donnée métier sensible.

## Première réponse attendue

Ne modifie aucun fichier. Vérifie la branche, l'état Git et le magasin en lecture seule, lis les
fichiers listés, résume le ticket, propose un plan court, et attends ma validation.
