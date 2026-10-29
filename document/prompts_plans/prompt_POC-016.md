Tu travailles dans le repo ProspectionLinkedIn avec Claude Code dans VS Code.

Je viens de faire un /clear pour réduire le contexte. Tu dois reprendre proprement à partir de la
documentation projet, mais sans relire tout le repository.

> Contexte de rédaction : prompt écrit le 07/10/2026 à la clôture de POC-008, **mis à jour le
> 29/10/2026** après le retour client du 22/10/2026. Les sauvegardes vont dans
> `D:\Documents\Dev\_backup_prospection\`.
>
> **Session préparatoire, avant le call client du 05/11/2026 (après-midi).** Le choix de faire ce
> ticket revient au client, qui en connaît les coûts (risque pour le compte LinkedIn, données
> personnelles conservées, moins de profils par semaine). D'ici le call : diagnostic, plan avec
> options et questions pour le client, éventuellement un relevé de DOM sans stockage. **Aucune
> migration de schéma, aucune collecte de texte stockée et aucune modification des règles avant la
> décision du call.**

## Ticket à traiter

Ticket : POC-016
Titre : Extraction des rubriques « Expérience » et « Infos » du profil LinkedIn
Objectif : Donner au scoring les informations que le client utilise réellement pour juger un
profil. Le client juge sur le parcours (ancien dirigeant, carrière privée contre fonction
publique) en lisant « Expérience » et « Infos » ; le scoring ne lit que le titre, et un titre
générique ne se départage pas (28 des 81 premiers profils à 65 pile, 29 des 50 du lot du
07/10/2026 à 60 ou 65 pile).

Critère d'acceptation :

- Les rubriques « Expérience » et « Infos » sont capturées **pendant la visite de profil que
  `run_poc002` fait déjà** pour l'email, sans visite supplémentaire.
- La visite reste **restreinte aux profils au seuil 60 ou plus** et aux profils non opposés.
- Les sélecteurs sont **vérifiés sur DOM réel** et centralisés dans `selectors.py`.
- Une rubrique absente ou illisible donne une valeur vide, jamais un échec du run ni une valeur
  devinée ; « visité, rien trouvé » se distingue de « pas encore visité ».
- Ce qui est stocké est **tranché au plan** au regard de la minimisation RGPD (texte brut ou
  signaux dérivés), et la migration de schéma éventuelle est faite sur **plan validé et sauvegarde
  explicite**, additive et idempotente comme celle de POC-009.
- L'apport est **mesuré** contre les verdicts du client avec `run_poc014_evaluation`, avant toute
  retouche des règles ; les règles de scoring ne changent pas sans cette mesure.
- Les `commentaire_client` sont intacts — vérifié contre une sauvegarde datée prise avant tout run
  qui écrit le magasin.
- Tests : partir de **277 passed** et ne rien casser.

La branche attendue est `master` (277+ tests).

## Périmètre autorisé

* `source/backend/adapters/scraping/profile_email.py` — la visite de profil.
* `source/backend/adapters/scraping/run_poc002.py` — le lancement.
* `source/backend/adapters/scraping/selectors.py` — les sélecteurs des deux rubriques.
* `source/backend/adapters/storage/profile_store.py` — seulement si le plan validé prévoit une
  migration.
* Tests unitaires correspondants.

Hors périmètre :
* toute modification des règles de scoring avant la mesure par `run_poc014_evaluation` ;
* la recherche et les requêtes (POC-008, clos) ;
* la collecte, le scoring et la visite en une seule session (POC-010) ;
* le déclenchement de la recherche de coordonnées par le verdict (POC-017) ;
* **toute migration de schéma sans plan validé et sauvegarde explicite** ;
* toute écriture dans `commentaire_client` ;
* pas de refactoring global, pas de renommage de module, pas de suppression de fichier, pas de
  modification de secrets ou fichiers sensibles (`.env.local`, `browser_profile/`).

## Documents à lire en premier

Lis uniquement ces fichiers au démarrage :

1. `CLAUDE.md`
2. `document/claude_code/AGENTS.md`
3. `document/claude_code/handoff.md` — la **dernière section** (n°18), la section 15 (POC-014) et,
   dans la section 9 (POC-009), ce qui concerne `run_poc002` et la migration v1 → v2
4. `document/Backlog.md` — uniquement la section `## POC-016`
5. `document/claude_code/task_list.md` — lignes POC-016, POC-014 et POC-009

Puis (OBLIGATOIRE avant d'écrire une ligne) :

* `source/backend/adapters/scraping/profile_email.py` — en entier
* `source/backend/adapters/scraping/run_poc002.py` — en entier
* `source/backend/adapters/scraping/selectors.py` — `LinkedInProfileSelectors`
* `source/backend/adapters/storage/profile_store.py` — `migrer_schema`, `_CHAMPS_COMPLETABLES` et
  les fonctions que `run_poc002` appelle
* les tests unitaires de ces modules — pour voir ce qui est déjà couvert

Ne lis pas tout le repo.

## Faits vérifiés

* **[Code]** `run_poc002` visite la page profil pour l'email, par lots plafonnés
  (`MAX_PROFILES = 5`), sans refaire de recherche. **[Documentation]** 0 email public sur 30
  profils testés.
* **[Documentation, POC-014]** Sur les 81 premiers profils annotés, précision au seuil 60 de 43 %,
  rappel 100 % ; 28 profils à 65 pile, portés par 8 bons, 16 mauvais et 4 « rien à voir ».
* **[Documentation, retour client du 22/10/2026]** Les 50 profils du lot du 07/10/2026 sont
  annotés : 3 excellents, 16 bons, 31 mauvais dont 13 « mauvais profil, multi fonction ». Le client
  écrit : *« de nombreux profils indiquent "coach certifié" dans leur en-tête mais ne pratiquent en
  fait pas […] On détecte ça en balayant le champ expérience. »*
* **[Mesure du 29/10/2026, hors échantillon]** Sur ces 50 profils jamais vus par les règles v2 :
  rappel au seuil 60 **100 %** (19/19), précision 46 % pour un taux de base de 38 % ; **tranche 80
  et plus : 7 profils, 29 % de bons, 0 excellent** (contre 76 % et 6/6 sur les 81 de réglage) ; les
  3 excellents sont à 60 ou 65. Le bonus `profil_dirigeant` passe de 12/18 positifs à **1/6** : il
  récompense les titres multi-fonctions que le client rejette.
* **[Mesure du 29/10/2026]** Le « multi-fonction » ne se lit pas dans le titre : une détection par
  séparateurs et mots de fonction signale 14 des 16 profils « multi fonction », mais aussi 33 des
  45 bons ou excellents.
* **État du magasin au 29/10/2026** : 131 profils, **131 commentaires client** (annotations du
  22/10 importées par `run_poc006`), `user_version` 2, empreinte MD5
  `189e64e0f6c1aa234851422686103ff5`. Le journal `journal_collecte.csv` (hors magasin, gitignoré)
  trace la requête d'origine des 50 derniers.
* **[Documentation]** Le client a fourni ses mots-clés de recherche le 22/10/2026 (coach business,
  coach professionnel, coach entreprise, coach executive, executive coaching, coach dirigeant,
  coach équipe(s), et les variantes « coaching ») : ils concernent la collecte (configuration de
  POC-008), **pas ce ticket**.
* **[Documentation, POC-008]** `ensure_logged_in` a redemandé la connexion manuelle à chaque
  lancement des 06 et 07/10/2026. Cause non instruite.

## Risque principal

Le compte LinkedIn : la visite de profil est l'étape la plus risquée du pipeline, et ce ticket la
rend systématique au-dessus du seuil. **Aucun run réel sans validation explicite de son plafond**,
et le premier est petit (5 profils). **Les runs LinkedIn réels sont lancés par l'utilisateur dans
son terminal** : préparer la configuration, donner la commande, attendre la sortie collée.
Second risque : la donnée personnelle. « Expérience » et « Infos » sont plus riches que le titre ;
ce qui est stocké, et pour combien de temps, se décide au plan.

## Points d'attention

* **Mesurer avant de régler** : des règles par mots-clés sur un texte long déclenchent bien plus
  facilement que sur un titre ; le piège de sous-chaîne (« marche » / « marché ») y est aggravé.
* [Inférence] C'est le premier endroit où un palier LLM pourrait se justifier ; mesurer d'abord le
  déterministe.
* Les sélecteurs de la page profil n'ont pas d'identifiant stable (voir
  `LinkedInProfileSelectors`) : prévoir un relevé de DOM réel avant d'écrire l'extraction.
* Les 131 profils sont annotés : la mesure de l'apport peut porter sur tout le magasin, à
  condition de ne pas régler et mesurer sur les mêmes profils (POC-014 a montré le sur-apprentissage).
* Le sort de `profil_dirigeant` est à trancher dans le plan, pas avant.

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
5. plan en 3 à 5 étapes, **en séparant le volet hors-ligne du volet à run réel** ;
6. questions bloquantes éventuelles, dont : texte brut ou signaux dérivés ; durée de conservation ;
   colonnes et migration ; plafond du premier run et des suivants ; sur quels profils mesurer
   l'apport. **Sépare les questions qui reviennent au client (à poser au call du 05/11) de celles
   qui me reviennent.**

Attends ma validation avant toute modification. Puis sauvegarde le plan dans
`document/prompts_plans/plan_POC-016.md` et committe
(`git commit -m "docs: POC-016 plan — description courte"`).

Étape 3 — Implémentation contrôlée :
Après validation :
* applique uniquement l'étape validée ;
* fais un petit diff ;
* évite toute modification opportuniste ;
* explique le diff ;
* lance uniquement les tests ciblés ;
* **demande une validation distincte avant chaque run LinkedIn réel, et laisse-moi le lancer.**

Étape 4 — Vérification :
```powershell
uv run --extra test pytest tests/unit/ -q
uv run --extra test pytest tests/ -q
```

```powershell
uv run --extra test pytest tests/ --collect-only -q
```

Puis, sur les données réelles : sauvegarde datée du magasin et du journal, run plafonné, contrôle
des `commentaire_client` contre la sauvegarde, mesure par `run_poc014_evaluation`.

Étape 5 — Fin de session (OBLIGATOIRE) :
* `document/Backlog.md` — section POC-016 : décisions, mesures, limites ;
* `document/claude_code/task_list.md` : POC-016 → DONE avec métriques ;
* `document/claude_code/handoff.md` : nouvelle section (ce qui a été fait, fichiers modifiés, prochain ticket) ;
* `CLAUDE.md` — section « État actuel » : dernière session (ID + date) et prochain ticket actif,
  **deux lignes, aucune métrique** (elles vivent dans `task_list.md`) ; compléter aussi « Structure
  du repository » si un dossier a été créé ;
* sauvegarder le prompt du prochain ticket (POC-017) dans
  `document/prompts_plans/prompt_POC-017.md` ;
* commit : `git commit -m "docs: POC-016 DONE — description courte"`.

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
