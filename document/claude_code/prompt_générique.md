Tu travailles dans le repo ProspectionLinkedIn avec Claude Code dans VS Code.

Je viens de faire un /clear pour réduire le contexte. Tu dois reprendre proprement à partir de la documentation projet, mais sans relire tout le repository.

## Ticket à traiter

Ticket : [ID_TICKET]
Titre : [TITRE_COURT]
Objectif : [OBJECTIF_METIER_OU_TECHNIQUE]

Critère d'acceptation :
[COLLER_LE_CRITERE_D_ACCEPTATION]

La branche attendue est `[BRANCHE]` ([N]+ tests).

## Périmètre autorisé

* [FICHIER_OU_MODULE_1]
* [FICHIER_OU_MODULE_2]
* [TESTS_CIBLES]

Hors périmètre :
* pas de refactoring global ;
* pas de changement d'architecture ;
* pas de renommage de module ;
* pas de suppression de fichier ;
* pas de modification de secrets ou fichiers sensibles.

## Documents à lire en premier

Lis uniquement ces fichiers au démarrage :

1. `CLAUDE.md`
2. `document/claude_code/AGENTS.md`
3. `document/claude_code/handoff.md` — sections récentes liées au ticket
4. `document/Backlog.md` — uniquement la section `## [ID_TICKET]`
5. `document/claude_code/task_list.md` — ligne [ID_TICKET]

Puis (OBLIGATOIRE avant d'écrire une ligne) :
[FICHIERS_MÉTIER_À_LIRE]

Ne lis pas tout le repo.

## Branche et sécurité Git

```powershell
git status --short
git branch --show-current
```

La branche attendue est `[BRANCHE]`. Ne change pas de branche sans validation humaine.

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
* ne modifie aucun fichier.

Étape 2 — Plan court :
Réponds d'abord avec :
1. résumé du ticket en 5 lignes maximum ;
2. fichiers à lire ou modifier ;
3. risque principal ;
4. tests prévus ;
5. plan en 3 à 5 étapes ;
6. questions bloquantes éventuelles.

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
[COMMANDES_TESTS_CIBLES]
```

```powershell
pytest tests/ --collect-only -q
```

Étape 5 — Fin de session (OBLIGATOIRE) :
* `document/Backlog.md` — section [ID_TICKET] : ajouter ou compléter les specs ;
* `document/claude_code/task_list.md` : [ID_TICKET] → DONE avec métriques ;
* `document/claude_code/handoff.md` : nouvelle section (ce qui a été fait, fichiers modifiés, prochain ticket) ;
* sauvegarder le prompt du prochain ticket dans `document/prompts_plans/prompt_[NEXT_TICKET].md` ;
* commit : `git commit -m "docs: [ID_TICKET] DONE — description courte"`.

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
