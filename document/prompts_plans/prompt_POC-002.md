Tu travailles dans le repo ProspectionLinkedIn avec Claude Code dans VS Code.

Je viens de faire un /clear pour réduire le contexte. Tu dois reprendre proprement à partir de la documentation projet, mais sans relire tout le repository.

## Ticket à traiter

Ticket : POC-002
Titre : Extraction de l'email depuis la page profil individuelle
Objectif : Étendre le pipeline POC-001 (recherche + extraction basique) pour visiter la
page profil individuelle de chaque profil déjà extrait et en récupérer l'email s'il est
visible publiquement, sans dépasser un volume raisonnable et sans déclencher de blocage
ou restriction du compte LinkedIn.

Critère d'acceptation :
[COLLER_LE_CRITERE_D_ACCEPTATION — à cadrer avec l'utilisateur en Étape 2, voir questions
bloquantes ci-dessous ; base de départ possible : email récupéré pour les profils qui
l'affichent publiquement, champ vide sinon, sur le même lot de test que POC-001, aucun
blocage de compte constaté, export CSV étendu avec la colonne email]

La branche attendue est `master` (7 tests passants, 0 échec, 0 skipped à l'issue de POC-001).

## Périmètre autorisé

* `source/backend/adapters/scraping/` — nouvelle fonction/module de visite de page profil + extraction email, sélecteurs dédiés ajoutés dans `selectors.py`
* `source/backend/adapters/storage/` — extension de l'export CSV avec la colonne email
* `tests/unit/` — tests ciblés sur les modules ci-dessus (logique pure testable sans navigateur réel)

Hors périmètre :
* pas de refactoring global ;
* pas de changement d'architecture ;
* pas de renommage de module ;
* pas de suppression de fichier ;
* pas de modification de secrets ou fichiers sensibles ;
* pas de scoring/catégorisation (Phase 2) ;
* pas d'envoi de message/invitation (lecture seule uniquement).

## Documents à lire en premier

Lis uniquement ces fichiers au démarrage :

1. `CLAUDE.md`
2. `document/claude_code/AGENTS.md`
3. `document/claude_code/handoff.md` — section POC-001 (la plus récente)
4. `document/Backlog.md` — uniquement la section `## POC-002` (et les décisions POC-001 relatives à l'email)
5. `document/claude_code/task_list.md` — ligne POC-002

Puis (OBLIGATOIRE avant d'écrire une ligne) :
* `source/backend/adapters/scraping/selectors.py`, `profile_search.py`, `browser_session.py`, `run_poc001.py` — pipeline existant à étendre
* `source/backend/adapters/storage/csv_export.py` — export à étendre

Ne lis pas tout le repo.

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
* lis ensuite le pipeline existant (POC-001) en détail ;
* identifie comment brancher la visite de page profil sans casser le flux de recherche existant ;
* ne modifie aucun fichier.

Étape 2 — Plan court :
Réponds d'abord avec :
1. résumé du ticket en 5 lignes maximum ;
2. fichiers à créer ou modifier ;
3. risque principal (probablement : volume de requêtes supplémentaire → blocage de compte) ;
4. tests prévus (unitaires sur la logique pure ; note sur ce qui ne peut être testé qu'en conditions réelles) ;
5. plan en 3 à 5 étapes ;
6. questions bloquantes éventuelles (ex : volume de test initial à choisir par prudence, comme le MAX_PROFILES=5 initial de POC-001 ; définition exacte du critère d'acceptation).

Attends ma validation avant toute modification.

Étape 3 — Implémentation contrôlée :
Après validation :
* applique uniquement l'étape validée ;
* fais un petit diff ;
* évite toute modification opportuniste ;
* explique le diff ;
* lance uniquement les tests ciblés.

Étape 4 — Vérification :
```powershell
pytest tests/unit/ -v
```

```powershell
pytest tests/ --collect-only -q
```

Étape 5 — Fin de session (OBLIGATOIRE) :
* `document/Backlog.md` — section POC-002 : compléter les specs et critères d'acceptation définitifs ;
* `document/claude_code/task_list.md` : POC-002 → DONE avec métriques ;
* `document/claude_code/handoff.md` : nouvelle section (ce qui a été fait, fichiers modifiés, prochain ticket) ;
* sauvegarder le prompt du prochain ticket dans `document/prompts_plans/prompt_[NEXT_TICKET].md` ;
* commit : `git commit -m "docs: POC-002 DONE — description courte"`.

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
