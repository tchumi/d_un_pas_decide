Tu travailles dans le repo ProspectionLinkedIn avec Claude Code dans VS Code.

Je viens de faire un /clear pour réduire le contexte. Tu dois reprendre proprement à partir de la documentation projet, mais sans relire tout le repository.

## Ticket à traiter

Ticket : POC-004
Titre : Enrichissement web des profils (coordonnées alternatives)
Objectif : Rechercher des informations complémentaires sur le web pour les profils déjà
extraits (en priorité : un moyen de contact alternatif quand l'email LinkedIn n'est pas
public), en réponse à la demande client du 04/07/2026 et au constat POC-002 (0 email
public sur 30 profils testés, confirmé par un mécanisme d'extraction validé
structurellement mais jamais déclenché positivement).

**Ticket pas encore cadré** : c'est une session de cadrage avant tout développement.
Les garde-fous RGPD sont déjà posés dans `Backlog.md` (base légale envisagée : intérêt
légitime, art. 6.1.f RGPD, prospection B2B — à valider par un professionnel du droit
avant tout développement au-delà du POC) mais les critères d'acceptation précis, la
source de données à utiliser (API de recherche, pas de scraping direct de moteur de
recherche) et le périmètre technique restent à définir avec l'utilisateur en début de
session.

Critère d'acceptation :
À définir en session — voir garde-fous RGPD dans `Backlog.md` section `## POC-004`
(nécessité/minimisation, transparence, droit d'opposition, conservation limitée, pas de
scraping direct des pages de résultats Google/Bing).

La branche attendue est `master` (19 tests passants, 0 échec, 0 skipped à l'issue de
POC-005).

## Périmètre autorisé

À définir en session, probablement :
* `source/backend/adapters/enrichment/` (nouveau module, source web externe)
* `source/backend/adapters/storage/` — éventuel champ `date_collecte` (garde-fou RGPD
  conservation limitée)
* `tests/unit/`

Hors périmètre :
* pas de refactoring global ;
* pas de changement d'architecture ;
* pas de renommage de module ;
* pas de suppression de fichier ;
* pas de modification de secrets ou fichiers sensibles ;
* pas de scraping direct des pages de résultats de moteurs de recherche (Google/Bing) —
  passer par une vraie API de recherche (ex. Bing Search API, SerpAPI) ;
* pas d'envoi de message/invitation automatisée (POC-005 reste une exception bornée,
  non reconduite ici).

## Documents à lire en premier

Lis uniquement ces fichiers au démarrage :

1. `CLAUDE.md`
2. `document/claude_code/AGENTS.md`
3. `document/claude_code/handoff.md` — section POC-005 (la plus récente)
4. `document/Backlog.md` — uniquement la section `## POC-004` (garde-fous RGPD et
   décisions) et les décisions POC-002 du 04/07/2026 et 07/07/2026 relatives au constat
   0 email public
5. `document/claude_code/task_list.md` — ligne POC-004

Puis (OBLIGATOIRE avant d'écrire une ligne) :
* `source/backend/adapters/storage/csv_export.py` — pour évaluer l'ajout éventuel d'un
  champ `date_collecte` ou d'une colonne de contact alternatif
* `source/backend/core/` — vérifier s'il existe déjà un modèle de profil à étendre plutôt
  que dupliquer

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
* lis ensuite uniquement les fichiers de code nécessaires au ticket ;
* identifie les appels entrants/sortants des fonctions concernées ;
* ne modifie aucun fichier.

Étape 2 — Plan court :
Réponds d'abord avec :
1. résumé du ticket en 5 lignes maximum ;
2. fichiers à lire ou modifier ;
3. risque principal (RGPD + risque technique/ToS de la source choisie) ;
4. tests prévus ;
5. plan en 3 à 5 étapes ;
6. questions bloquantes éventuelles — notamment :
   - Quelle source web utiliser (API de recherche payante à souscrire, ou autre) ?
   - Quel volume de test raisonnable pour un premier run ?
   - Le champ `date_collecte` doit-il être ajouté dès ce ticket ou différé ?

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
* `document/Backlog.md` — section POC-004 : compléter les specs et critères
  d'acceptation définitifs ;
* `document/claude_code/task_list.md` : POC-004 → DONE (ou BLOCKED/DECIDED selon
  l'issue du cadrage) avec métriques ;
* `document/claude_code/handoff.md` : nouvelle section (ce qui a été fait, fichiers
  modifiés, prochain ticket) ;
* sauvegarder le prompt du prochain ticket dans
  `document/prompts_plans/prompt_[NEXT_TICKET].md` ;
* commit : `git commit -m "docs: POC-004 DONE — description courte"`.

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
