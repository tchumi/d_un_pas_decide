Tu travailles dans le repo ProspectionLinkedIn avec Claude Code dans VS Code.

Je viens de faire un /clear pour réduire le contexte. Tu dois reprendre proprement à partir de la documentation projet, mais sans relire tout le repository.

## Ticket à traiter

Ticket : POC-003
Titre : Scoring et catégorisation des profils (Phase 2)
Objectif : Catégoriser chaque profil extrait dans une des 3 classes cibles (coach
business débutant, expérimenté, outdoor/nature — indifférencié par défaut) et lui
attribuer un score de pertinence.

**Ce ticket est BLOCKED au moment de la rédaction de ce prompt** (voir
`document/claude_code/task_list.md`) : en attente des 5-10 exemples de "bons" profils
et 2-3 "mauvais" demandés au client, seuls 2 reçus sur le total attendu. Ne pas
démarrer l'implémentation tant que ce complément n'est pas arrivé — le confirmer
explicitement avec l'utilisateur en premier lieu.

Critère d'acceptation :
[PAS ENCORE CADRÉ — dépend des exemples de calibration manquants ; voir questions
bloquantes ci-dessous]

La branche attendue est `master` (12 tests passants, 0 échec, 0 skipped à l'issue de POC-002).

## Périmètre autorisé

* `source/backend/core/` — nouveau module de scoring/catégorisation, zéro import Streamlit (voir CLAUDE.md)
* `tests/unit/` — tests ciblés sur la logique de scoring (pure, sans navigateur)
* Périmètre exact à confirmer une fois le cadrage fait (Étape 2)

Hors périmètre :
* pas de refactoring global ;
* pas de changement d'architecture ;
* pas de renommage de module ;
* pas de suppression de fichier ;
* pas de modification de secrets ou fichiers sensibles ;
* pas de nouvelle extraction/scraping (réutiliser les profils déjà extraits par POC-001/POC-002).

## Documents à lire en premier

Lis uniquement ces fichiers au démarrage :

1. `CLAUDE.md`
2. `document/claude_code/AGENTS.md`
3. `document/claude_code/handoff.md` — section POC-002 (la plus récente)
4. `document/Backlog.md` — uniquement la section `## POC-003` (exemples de calibration client déjà reçus)
5. `document/claude_code/task_list.md` — ligne POC-003

Puis (OBLIGATOIRE avant d'écrire une ligne) :
* Vérifier auprès de l'utilisateur si les exemples de calibration manquants (5-10 bons
  profils, 2-3 mauvais) sont arrivés depuis. Si non, s'arrêter là et ne pas cadrer le
  ticket en détail.

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
* vérifie le statut BLOCKED auprès de l'utilisateur (exemples de calibration reçus ou non) ;
* si toujours bloqué, ne pas aller plus loin dans le cadrage ;
* ne modifie aucun fichier.

Étape 2 — Plan court (uniquement si débloqué) :
Réponds d'abord avec :
1. résumé du ticket en 5 lignes maximum ;
2. fichiers à créer ou modifier ;
3. risque principal (probablement : critères de scoring subjectifs mal calibrés sur un petit échantillon) ;
4. tests prévus (logique de scoring pure, testable sans navigateur) ;
5. plan en 3 à 5 étapes ;
6. questions bloquantes éventuelles (ex : poids relatif des critères, seuils de score, gestion des cas ambigus comme "Anne-Laure F." déjà signalé par le client comme moins intéressant sans être exclu).

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
* `document/Backlog.md` — section POC-003 : compléter les specs et critères d'acceptation définitifs ;
* `document/claude_code/task_list.md` : POC-003 → DONE avec métriques ;
* `document/claude_code/handoff.md` : nouvelle section (ce qui a été fait, fichiers modifiés, prochain ticket) ;
* sauvegarder le prompt du prochain ticket dans `document/prompts_plans/prompt_[NEXT_TICKET].md` ;
* commit : `git commit -m "docs: POC-003 DONE — description courte"`.

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
3. demander explicitement si les exemples de calibration manquants sont arrivés ;
4. si oui seulement, proposer un plan court et attendre ma validation.
