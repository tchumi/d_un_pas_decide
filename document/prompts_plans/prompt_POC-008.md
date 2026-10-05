Tu travailles dans le repo ProspectionLinkedIn avec Claude Code dans VS Code.

Je viens de faire un /clear pour réduire le contexte. Tu dois reprendre proprement à partir de la
documentation projet, mais sans relire tout le repository.

> Contexte de rédaction : prompt écrit le 05/10/2026 sur le **poste principal**, à la clôture de
> POC-015. Les sauvegardes vont dans `D:\Documents\Dev\_backup_prospection\`.
>
> Il **remplace** la version du 28/08/2026 (mise à jour le 08/09/2026 pour l'itinérance), devenue
> contradictoire avec les décisions du 11/09, du 19/09 et du 05/10/2026. L'ancienne version reste
> lisible dans l'historique Git (`git show bc49646:document/prompts_plans/prompt_POC-008.md`) ; ce
> qu'elle contenait de toujours valable est repris ci-dessous.

## Ticket à traiter

Ticket : POC-008
Titre : Diversification des requêtes (découpage géographique + vocabulaire)
Objectif : Fournir le **prochain lot de profils promis au client** (mail du 19/09/2026, « au plus
tard fin septembre », engagement dépassé). La requête actuelle n'a plus qu'environ un run d'avance
(page 8 atteinte sur ~10) et ramène des profils trop homogènes pour éprouver le scoring v2. Il
faut pouvoir lancer **plusieurs requêtes configurables**, et découper l'espace de recherche par
région pour passer sous le plafond d'une recherche LinkedIn. La géographie est un **moyen de
découpage**, pas un critère de sélection : toutes les régions sont balayées.

Critère d'acceptation :

- Les requêtes sont **décrites en configuration** (dans `config/`, à l'image de
  `scoring_rules.json`) et non plus en dur dans `run_poc001.py` ; en ajouter une ne demande pas de
  toucher au code. Le fichier est **validé au chargement**, avec une erreur explicite s'il est
  absent ou malformé.
- La requête actuelle est reprise **à l'identique** comme première entrée (chaîne vérifiée dans le
  code, pas recopiée de mémoire) ; un run sans nouvelle requête se comporte comme avant.
- **Plusieurs requêtes sont parcourues en séquence**, chacune avec un libellé lisible. La sortie
  dit **par requête** combien de profils nouveaux elle a ramenés et pourquoi elle s'est arrêtée.
- **`urls_connues` est passé et enrichi d'une requête à la suivante** : la déduplication vaut
  *entre* les requêtes, sinon deux requêtes qui se recouvrent ramènent deux fois le même profil.
- Le parcours des requêtes se teste avec une **fonction de recherche injectée**, comme la boucle
  de pagination.
- Le filtre géographique est une **facette native LinkedIn**, pas le texte `AND (France)` dans
  `keywords`. Le paramètre d'URL correspondant est **vérifié sur un run réel**, pas supposé.
- Un run réel, plafonné et validé avant lancement, ramène un lot de profils **nouveaux**
  (déduplication de POC-006 intacte) ; la requête d'origine de chaque profil est traçable.
- Le lot est scoré (règles v2 **inchangées**), exporté avec la colonne département (POC-015), et le
  nombre de profils par requête, par région et par tranche de score est publié.
- Les 81 `commentaire_client` sont intacts — vérifié contre une sauvegarde datée prise avant tout
  run qui écrit le magasin.
- Tests : partir de **214 passed** et ne rien casser.

La branche attendue est `master` (214+ tests).

## Périmètre autorisé

* `source/backend/adapters/scraping/profile_search.py` — `build_search_url` et la recherche.
* `source/backend/adapters/scraping/run_poc001.py` — `SEARCH_QUERY`, le lancement.
* `source/backend/adapters/scraping/selectors.py` — seulement si une facette exige un sélecteur.
* `config/` — le fichier de requêtes.
* `source/backend/core/` — le chargement et la validation de ce fichier, si c'est de la logique pure.
* Tests unitaires de la construction d'URL et du chargement des requêtes.

Hors périmètre :
* toute modification des règles de scoring (la v2 attend le lot annoté ; lancer
  `run_poc014_evaluation` **avant** toute retouche) ;
* l'extraction des rubriques « Expérience » et « Infos » (POC-016) ;
* la collecte, le scoring et la visite de profil en une seule session (POC-010) ;
* **toute migration de schéma sans plan validé et sauvegarde explicite** — si tracer la requête
  d'origine demande une colonne, c'est à trancher au plan ;
* toute écriture dans `commentaire_client` ;
* pas de refactoring global, pas de renommage de module, pas de suppression de fichier, pas de
  modification de secrets ou fichiers sensibles (`.env.local`, `browser_profile/`).

## Documents à lire en premier

Lis uniquement ces fichiers au démarrage :

1. `CLAUDE.md`
2. `document/claude_code/AGENTS.md`
3. `document/claude_code/handoff.md` — la **dernière section** (n°16) et, dans la section 7
   (POC-006), ce qui concerne la pagination et le plafond de pages
4. `document/Backlog.md` — uniquement la section `## POC-008`
5. `document/claude_code/task_list.md` — lignes POC-008 et POC-006

Puis (OBLIGATOIRE avant d'écrire une ligne) :

* `source/backend/adapters/scraping/profile_search.py` — `build_search_url`,
  `collecter_profils_inconnus`, `search_and_extract`, `message_arret`
* `source/backend/adapters/scraping/run_poc001.py` — en entier
* `source/backend/adapters/scraping/selectors.py`
* `source/backend/adapters/storage/profile_store.py` — **uniquement** `urls_connues` et
  `enregistrer_profils`
* `tests/unit/test_profile_search.py` — pour voir ce qui est déjà couvert

Ne lis pas tout le repo.

## Faits vérifiés

* **[Code]** `build_search_url` place toute la requête, `AND (France)` compris, dans le seul
  paramètre `keywords` : c'est une correspondance textuelle, pas un filtre géographique.
* **[Code]** La requête actuelle est en dur dans `run_poc001.py` :
  `("coach business" OR "coach professionnel" OR "coach entreprise") AND (France) NOT ("life coach" OR "sportif")`.
* **[Code]** `search_and_extract` n'est que le câblage Playwright autour d'une **boucle pure
  injectable** ; `collecter_profils_inconnus` s'arrête sur `quota_atteint`, `gisement_epuise` ou
  `plafond_pages` (plafond 10 pages). C'est le point d'entrée à étendre, pas à réécrire.
* **[Documentation, POC-009]** Deux recherches sur la même requête à deux moments différents n'ont
  pas ramené le même lot (recouvrement 19/25) : à garder en tête pour juger la stabilité d'un
  gisement.
* **[Documentation]** Les 5 mots-clés outdoor du client (08/07/2026 : *coach nature*, *coach qui
  marche*, *coach outdoor*, *coach hors-les-murs*, *coaching en itinérance*) n'ont jamais été
  interrogés ; la catégorie `coach_outdoor` n'a jamais été observée sur données réelles.
* **[Documentation, run réel du 26/08/2026]** ~10 profils par page, page 8 atteinte sur un plafond
  **estimé** à 10 pages. Le plafond exact n'a jamais été mesuré.
* **[Documentation]** Le brainstorming de requêtes dû par le client (point d'action n°3 du call du
  04/09/2026) **n'est pas arrivé**. La grille du 11/09/2026 oriente le vocabulaire vers les coachs
  d'anciens dirigeants (« executive coach », « coach de dirigeants »).
* **[Code, POC-007]** Piège de sous-chaîne : « coach qui marche » se réduit à `marche`, déjà
  présent dans 3 titres via « Analyste Marché ».
* **[Code, POC-015]** L'export porte 17 colonnes ; `departement` est dérivée de `localisation` et
  reste vide pour une aire urbaine (« Paris et périphérie »). `run_poc015` régénère CSV et classeur
  sans écrire le magasin et liste les localisations laissées vides — à relire sur le nouveau lot.
* **État du magasin au 05/10/2026** : 81 profils, 81 commentaires client, `user_version` 2,
  empreinte MD5 `7bf1cbb0fa4d015ade51ab9a942e4f41`.

## Risque principal

Le compte LinkedIn. Multiplier les requêtes augmente le volume de sollicitations, donc le risque
de détection : le rapport bénéfice/risque fait partie du ticket. **Aucun run réel sans validation
explicite de son plafond** (nombre de requêtes, de pages, de profils), et le premier est petit.
Second risque : croire qu'une facette filtre alors que le paramètre d'URL est ignoré — d'où la
vérification sur DOM réel avant de s'appuyer dessus.

## Points d'attention

* **N'invente pas de requêtes métier à la place du client.** Sans son brainstorming, amorce avec
  la requête actuelle et des requêtes clairement étiquetées comme provisoires, à me faire valider.
* **Mesurer au lieu d'estimer** : profiter d'un run réel pour relever le sélecteur de la barre de
  pagination numérotée et journaliser la taille réelle du gisement par requête. Le « ~10 pages »
  est une estimation.
* [Inférence] Un profil outdoor authentique peut ne pas contenir le mot `coach` dans son titre et
  se faire exclure par `exclusion_non_coach`. Si le cas se présente, le **signaler** : le scoring
  est hors périmètre.
* Les sélecteurs CSS LinkedIn restent centralisés dans `selectors.py` (AGENTS.md §4).

## Branche et sécurité Git

```powershell
git status --short
git branch --show-current
```

La branche attendue est `master`. Ne change pas de branche sans validation humaine.

Ne fais jamais :
* git reset --hard ;
* checkout destructif ;
* suppression de fichiers ;
* amend de commit ;
* modification de fichiers non liés au ticket.

## Méthode obligatoire

Étape 1 — Lecture et diagnostic :
* lis les fichiers de documentation listés ;
* lis ensuite uniquement les fichiers de code nécessaires au ticket ;
* identifie les appels entrants/sortants des fonctions concernées ;
* vérifie le magasin **en lecture seule** (comptages, empreinte) ;
* ne modifie aucun fichier, ne lance aucun run LinkedIn.

Étape 2 — Plan court :
Réponds d'abord avec :
1. résumé du ticket en 5 lignes maximum ;
2. fichiers à lire ou modifier ;
3. risque principal ;
4. tests prévus ;
5. plan en 3 à 5 étapes, **en séparant le volet hors-ligne** (requêtes en configuration) **du volet
   à run réel** (facettes de lieu) ;
6. questions bloquantes éventuelles, dont : quelles requêtes sans le brainstorming du client ;
   découpage par région seule ou région × vocabulaire ; plafond du premier run et des suivants ;
   comment tracer la requête d'origine d'un profil (colonne stockée, donc migration, ou journal à
   part) ; taille visée pour le lot à envoyer.

Attends ma validation avant toute modification. Puis sauvegarde le plan dans
`document/prompts_plans/plan_POC-008.md` et committe
(`git commit -m "docs: POC-008 plan — description courte"`).

Étape 3 — Implémentation contrôlée :
Après validation :
* applique uniquement l'étape validée ;
* fais un petit diff ;
* évite toute modification opportuniste ;
* explique le diff ;
* lance uniquement les tests ciblés ;
* **demande une validation distincte avant chaque run LinkedIn réel.**

Étape 4 — Vérification :
```powershell
uv run --extra test pytest tests/unit/test_profile_search.py -v
uv run --extra test pytest tests/ -q
```

```powershell
uv run --extra test pytest tests/ --collect-only -q
```

Puis, sur les données réelles : sauvegarde datée du magasin, run plafonné, comptage des nouveaux
profils par requête et par région, scoring, `run_poc015` pour le CSV et le classeur, contrôle des
81 commentaires client contre la sauvegarde.

Étape 5 — Fin de session (OBLIGATOIRE) :
* `document/Backlog.md` — section POC-008 : décisions, mesures (plafond réel, profils par requête), limites ;
* `document/claude_code/task_list.md` : POC-008 → DONE avec métriques ;
* `document/claude_code/handoff.md` : nouvelle section (ce qui a été fait, fichiers modifiés, prochain ticket) ;
* `CLAUDE.md` — section « État actuel » : dernière session (ID + date) et prochain ticket actif,
  **deux lignes, aucune métrique** (elles vivent dans `task_list.md`) ; compléter aussi « Structure
  du repository » si un dossier a été créé ;
* sauvegarder le prompt du prochain ticket (POC-016, après l'envoi du lot et le rendez-vous client)
  dans `document/prompts_plans/prompt_POC-016.md` ;
* commit : `git commit -m "docs: POC-008 DONE — description courte"`.

## Contraintes de style

* Réponses en français.
* Commentaires de code en anglais.
* Toute affirmation importante taguée [Code] / [Documentation] / [Inférence].
* Ne corrige jamais silencieusement une donnée métier sensible.

## Première réponse attendue

Ne modifie aucun fichier.

Commence par :
1. vérifier la branche et l'état Git ;
2. lire les fichiers listés → résumer le ticket ;
3. proposer un plan court ;
4. attendre ma validation.
