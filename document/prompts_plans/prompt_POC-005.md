Tu travailles dans le repo ProspectionLinkedIn avec Claude Code dans VS Code.

Je viens de faire un /clear pour réduire le contexte. Tu dois reprendre proprement à partir de la documentation projet, mais sans relire tout le repository.

## Ticket à traiter

Ticket : POC-005
Titre : Test de faisabilité d'envoi d'une invitation LinkedIn avec note (validation interne uniquement)
Objectif : Valider techniquement la faisabilité d'envoyer une invitation LinkedIn avec
note personnalisée via Playwright — c'est le mécanisme réel derrière la demande client du
04/07/2026 ("inviter automatiquement chaque profil extrait"), pas un simple message :
Michel n'est très probablement pas connecté en 1er degré avec Christophe et Henri-Pierre
sur le compte de test, donc un message direct est impossible sans invitation préalable
acceptée. **Uniquement à titre de test de faisabilité, sur 2 destinataires internes et
consentants** (Christophe Hoffsteter, Henri-Pierre Michaud), jamais sur un profil issu du
pipeline de scraping/prospects.

**Dérogation ponctuelle et bornée à la règle "lecture seule"** de la spec (qui exclut
l'envoi de messages/invitations automatisées "dans cette phase") : ce ticket introduit
une exception étroite et documentée, réservée à la validation technique. Ce n'est pas
une réouverture du scope vers l'automatisation de la prospection réelle — toute
extension au-delà de ce test reste hors scope tant qu'elle n'a pas été explicitement
redécidée.

Critère d'acceptation :
- Liste blanche en dur dans le code contenant uniquement ces 2 URLs LinkedIn :
  - `linkedin.com/in/henri-pierre-michaud-19a0a6b0` (Henri-Pierre Michaud)
  - `linkedin.com/in/choffstetter` (Christophe Hoffsteter)
- La fonction d'envoi refuse structurellement toute URL absente de cette liste (test unitaire dédié qui le prouve)
- Invitation avec note personnalisée envoyée avec succès aux 2 destinataires, ou échec documenté clairement
- Note d'invitation statique, validée par l'utilisateur avant envoi (≤ ~300 caractères, limite LinkedIn)
- Volume strictement limité à 2 invitations, exécution manuelle unique (pas de boucle, pas de tâche planifiée)
- Aucun blocage/restriction du compte LinkedIn constaté pendant/après le test

La branche attendue est `master` (12 tests passants, 0 échec, 0 skipped à l'issue de POC-002).

## Périmètre autorisé

* `source/backend/adapters/scraping/` — nouveau module dédié (ex. `internal_invite_test.py`), sélecteurs du bouton "Se connecter"/note d'invitation ajoutés dans `selectors.py`, script d'exécution unique dédié (ex. `run_poc005.py`)
* `tests/unit/` — tests ciblés : refus d'une URL hors liste blanche, logique pure (validation d'URL, longueur de la note)

Hors périmètre :
* pas de refactoring global ;
* pas de changement d'architecture ;
* pas de renommage de module ;
* pas de suppression de fichier ;
* pas de modification de secrets ou fichiers sensibles ;
* pas d'envoi vers un profil hors liste blanche — aucune exception, y compris pour tester ;
* pas de boucle ni de tâche planifiée — une seule exécution manuelle ;
* pas d'envoi de message direct (dépend de l'acceptation de l'invitation, hors scope de ce ticket) ;
* pas de scoring/catégorisation ;
* pas d'extension à de vrais prospects (ce ticket ne modifie pas le statut "lecture seule" du reste du pipeline).

## Documents à lire en premier

Lis uniquement ces fichiers au démarrage :

1. `CLAUDE.md`
2. `document/claude_code/AGENTS.md`
3. `document/claude_code/handoff.md` — section POC-002 (la plus récente)
4. `document/Backlog.md` — uniquement la section `## POC-005` (garde-fous et décisions) et les décisions POC-002 du 04/07/2026 relatives à la demande client d'auto-invite
5. `document/claude_code/task_list.md` — ligne POC-005

Puis (OBLIGATOIRE avant d'écrire une ligne) :
* `source/backend/adapters/scraping/selectors.py`, `browser_session.py` — patterns de sélecteurs et gestion de session existants, à réutiliser pour l'invitation

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
* modification de fichiers non liés au ticket ;
* envoi vers une URL absente de la liste blanche, même à des fins de debug.

## Méthode obligatoire

Étape 1 — Lecture et diagnostic :
* lis les fichiers de documentation listés ;
* lis les modules `selectors.py`/`browser_session.py` existants pour identifier ce qui est réutilisable (session persistée, détection de login) ;
* vérifie sur le compte de test l'état de connexion réel avec Christophe et Henri-Pierre (1er degré ou non) avant de proposer le plan ;
* ne modifie aucun fichier.

Étape 2 — Plan court :
Réponds d'abord avec :
1. résumé du ticket en 5 lignes maximum ;
2. fichiers à créer ou modifier ;
3. risque principal (envoi d'invitations = comportement surveillé par LinkedIn, mais faible à ce volume vers des contacts réels connus) ;
4. tests prévus (unitaires sur la logique pure, notamment le refus de la liste blanche ; note sur ce qui ne peut être vérifié qu'en conditions réelles) ;
5. plan en 3 à 5 étapes ;
6. questions bloquantes éventuelles — notamment :
   - Contenu exact de la note d'invitation à envoyer (≤ ~300 caractères) ;
   - Compte de test à utiliser pour l'envoi (le même que le scraping, ou un compte dédié ?) ;
   - Confirmation de l'état de connexion actuel avec les 2 destinataires (probablement pas encore connectés).

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
* `document/Backlog.md` — section POC-005 : compléter les specs et critères d'acceptation définitifs, documenter le résultat réel du test (envoyé / échoué / bloqué) ;
* `document/claude_code/task_list.md` : POC-005 → DONE (ou BLOCKED si l'état de connexion empêche le test tel quel) avec métriques ;
* `document/claude_code/handoff.md` : nouvelle section (ce qui a été fait, fichiers modifiés, prochain ticket) ;
* sauvegarder le prompt du prochain ticket dans `document/prompts_plans/prompt_[NEXT_TICKET].md` ;
* commit : `git commit -m "docs: POC-005 DONE — description courte"`.

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
