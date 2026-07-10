Tu travailles dans le repo ProspectionLinkedIn avec Claude Code dans VS Code.

Je viens de faire un /clear pour réduire le contexte. Tu dois reprendre proprement à partir de la documentation projet, mais sans relire tout le repository.

## Ticket à traiter

Ticket : POC-004
Titre : Enrichissement web des profils (coordonnées alternatives) — pipeline v1 déterministe
Objectif : Pour chaque profil déjà extrait (CSV issu de POC-001/POC-002), rechercher sur
le web un moyen de contact alternatif quand l'email LinkedIn n'est pas public (constat
POC-002 : 0/30 profils avec email public), en réponse à la demande client du 04/07/2026.
**Pipeline v1 100% déterministe, sans LLM** : recherche via une vraie API de recherche
(Brave Search API), filtrage par liste noire de domaines non pertinents, puis extraction
par regex (pas d'interprétation par un modèle) d'un email et/ou d'un site sur la page
candidate restante. Les paliers avec LLM/agents (voir `Backlog.md`) sont hors scope de ce
ticket — à n'activer que si ce v1 démontre ses limites.

Critère d'acceptation :
- Requête de recherche construite depuis nom + titre + localisation de chaque profil (Brave Search API), top 3-5 résultats récupérés
- Filtrage déterministe par liste noire de domaines (linkedin.com, facebook.com, pagesjaunes, annuaires, wikipedia, etc.)
- Pour le(s) candidat(s) restant(s) : visite HTTP simple de la page + extraction regex de `email_web` (lien `mailto:` ou pattern email) et `site_web` (URL racine)
- Champs vides si rien de concluant (pas d'échec bloquant), même logique que POC-002
- Export CSV étendu avec les colonnes `email_web` et `site_web`
- Zéro appel LLM dans cette version
- Clé `BRAVE_SEARCH_API_KEY` dans `.env.local` (déjà présente), jamais en dur dans le code
- Aucun scraping direct des pages de résultats de moteurs de recherche (uniquement l'API Brave)

La branche attendue est `master` (19 tests passants, 0 échec, 0 skipped à l'issue de POC-005).

## Périmètre autorisé

* `source/backend/adapters/enrichment/` — nouveau module (ex. `web_search.py` pour l'appel Brave Search API, `email_site_extractor.py` pour le filtrage de domaines + extraction regex, `run_poc004.py` pour l'assemblage)
* `source/backend/adapters/storage/csv_export.py` — extension avec les colonnes `email_web`/`site_web`
* `pyproject.toml` — ajout d'une dépendance HTTP légère si nécessaire (ex. `requests`), à documenter dans le plan
* `.env.local` — `BRAVE_SEARCH_API_KEY` déjà présent, à lire (pas à recréer)
* `tests/unit/` — tests ciblés : construction de requête, filtrage de domaines par liste noire, regex d'extraction email/site (logique pure, sans appel réseau réel)

Hors périmètre :
* pas de refactoring global ;
* pas de changement d'architecture ;
* pas de renommage de module ;
* pas de suppression de fichier ;
* pas de modification de secrets ou fichiers sensibles ;
* pas d'appel LLM ni de framework agent (LangChain/LangGraph) — hors scope du v1, voir paliers conditionnels dans `Backlog.md` ;
* pas de scoring/catégorisation (POC-003) ;
* pas d'envoi de message/invitation (inchangé depuis POC-001/002/005) ;
* pas de scraping direct des pages de résultats Google/Bing — uniquement l'API Brave Search.

## Documents à lire en premier

Lis uniquement ces fichiers au démarrage :

1. `CLAUDE.md`
2. `document/claude_code/AGENTS.md`
3. `document/claude_code/handoff.md` — section POC-005 (la plus récente)
4. `document/Backlog.md` — uniquement la section `## POC-004` (pipeline v1, garde-fous RGPD, décisions — y compris le choix de Brave Search API et l'abandon des paliers LLM/agents pour cette version)
5. `document/claude_code/task_list.md` — ligne POC-004

Puis (OBLIGATOIRE avant d'écrire une ligne) :
* `source/backend/adapters/storage/csv_export.py` — export existant à étendre (schéma `PROFILE_CSV_FIELDS`)
* `source/backend/adapters/scraping/profile_email.py` — pattern déjà utilisé en POC-002 pour l'extraction d'email (champ vide plutôt qu'échec bloquant), à réutiliser dans l'esprit pour `email_site_extractor.py`

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
* lis `csv_export.py` et `profile_email.py` pour identifier les patterns existants à réutiliser ;
* vérifie que `BRAVE_SEARCH_API_KEY` est bien lue depuis `.env.local` (déjà présente, ne pas la recréer ni l'afficher) ;
* ne modifie aucun fichier.

Étape 2 — Plan court :
Réponds d'abord avec :
1. résumé du ticket en 5 lignes maximum ;
2. fichiers à créer ou modifier ;
3. risque principal (mauvais candidat retenu — homonyme, page non pertinente — contenu par le filtrage de domaines et la relecture humaine avant tout contact) ;
4. tests prévus (unitaires sur la logique pure : construction de requête, filtrage de domaines, regex d'extraction ; note sur ce qui ne peut être vérifié qu'en conditions réelles, avec une vraie clé API) ;
5. plan en 3 à 5 étapes ;
6. questions bloquantes éventuelles (ex : liste noire de domaines précise à valider, volume de test initial à choisir par prudence comme pour POC-001/002, format exact de la requête de recherche par profil).

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
* `document/Backlog.md` — section POC-004 : compléter les specs et critères d'acceptation définitifs, documenter le taux de candidats pertinents observé (utile pour juger si un palier LLM devient nécessaire) ;
* `document/claude_code/task_list.md` : POC-004 → DONE avec métriques ;
* `document/claude_code/handoff.md` : nouvelle section (ce qui a été fait, fichiers modifiés, prochain ticket) ;
* sauvegarder le prompt du prochain ticket dans `document/prompts_plans/prompt_[NEXT_TICKET].md` ;
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
