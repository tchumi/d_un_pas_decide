# handoff.md — État du sprint en cours

<!--
Format de chaque section :
## [N]. [ID_TICKET] — [Titre court] ([date JJ/MM/AAAA])
- Ce qui a été fait
- Fichiers modifiés
- Tests lancés / résultats
- Points de vigilance
- Prochain ticket recommandé
-->

## 1. Initialisation projet (02/07/2026)

- Squelette de gouvernance Claude créé depuis `claude-project-template`, adapté au projet ProspectionLinkedIn (POC prospection coachs business sur LinkedIn pour D'un Pas Décidé).
- Fichiers initiaux : `CLAUDE.md`, `AGENTS.md`, `task_list.md`, `handoff.md`, `prompt_générique.md`, `Backlog.md`, `ARCHITECTURE.md`.
- Stack retenue : Streamlit (UI) + Playwright (scraping) + SQLite + pandas, avec isolation stricte frontend/backend (zéro import Streamlit dans `core/`/`adapters/`) pour permettre une UI desktop en remplacement futur.
- Identifiants LinkedIn (`LINKEDIN_EMAIL`/`LINKEDIN_PASSWORD`) prévus dans `.env.local` (non commité).
- Prochain ticket : POC-001 — Script de recherche + extraction basique de profils LinkedIn

## 2. POC-001 — Script de recherche + extraction basique de profils LinkedIn (03/07/2026)

- Squelette du module scraping/storage créé : `pyproject.toml` (deps playwright, pandas, streamlit, pytest) + arborescence `source/backend/adapters/{scraping,storage}/`.
- Sélecteurs CSS LinkedIn centralisés dans `source/backend/adapters/scraping/selectors.py` (repris et isolés depuis `document/spec/linkedin_search_poc.py`, avec commentaires sur les points fragiles : sélecteur du nom, bouton de pagination dépendant de la langue du compte).
- Login manuel (bloquant via `input()`, pas d'auto-remplissage) isolé dans `browser_session.py` (`ensure_logged_in`) pour faciliter un futur remplacement non bloquant sans toucher au reste.
- Recherche + extraction + pagination dans `profile_search.py`, logique pure (`build_search_url`, `clean_profile_url`) séparée de la partie Playwright pour rester testable sans navigateur.
- Export CSV (nom, url, localisation, titre — sans email) dans `storage/csv_export.py`.
- Script exécutable d'assemblage : `source/backend/adapters/scraping/run_poc001.py` (requête booléenne de la spec, `MAX_PROFILES=5` pour la première phase de debug — décision explicite utilisateur, à remonter à 20-25 une fois un run validé sans blocage de compte).
- `.env.local` créé avec placeholders `LINKEDIN_EMAIL`/`LINKEDIN_PASSWORD` (non lus par le code, non commité).
- `.gitignore` : ajout de `browser_profile/` (dossier de session Playwright, cookies LinkedIn) et `profils_extraits.csv` (validé explicitement par l'utilisateur, hors périmètre initial du ticket).
- Zéro import Streamlit dans les modules créés (vérifié).
- Fichiers créés : `pyproject.toml`, `source/backend/**/__init__.py`, `source/backend/adapters/scraping/{selectors,browser_session,profile_search,run_poc001}.py`, `source/backend/adapters/storage/csv_export.py`, `tests/unit/{__init__,test_csv_export,test_profile_search}.py`, `.env.local` (non commité).
- Fichiers modifiés : `.gitignore`, `document/claude_code/task_list.md`, `document/claude_code/handoff.md`.
- Tests lancés : `pytest tests/unit/ -v` → 7 passed ; `pytest tests/ --collect-only -q` → 7 tests collectés. Import de tous les modules (y compris Playwright) vérifié sans erreur.
- **Bugs corrigés en cours de test live** (voir commits `fix: POC-001 ...`) :
  1. `is_logged_in` traitait la page d'accueil non connectée comme déjà authentifiée (absence de marqueur "login"/"authwall" dans l'URL) → fenêtre fermée avant la saisie du login. Corrigé : seule la redirection vers `/feed/` compte comme connecté.
  2. Course entre la confirmation du login (`input()`) et la navigation suivante, qui interrompait la navigation vers la recherche (`interrupted by another navigation to /login/fr`). Corrigé : attente explicite de `/feed/` avec plusieurs tentatives avant d'abandonner avec un message clair.
  3. Sélecteurs CSS obsolètes (`reusable-search__*`, `entity-result__*`) : LinkedIn utilise désormais des classes hashées régénérées à chaque déploiement → 0 profils extraits malgré des résultats visibles. Diagnostiqué via un dump HTML d'une vraie page de résultats (session utilisateur, une seule requête ponctuelle). Corrigé avec des attributs structurels stables : `role="listitem"`/`role="list"` pour les cartes, ancre imbriquée dans un `<p>` pour le nom, traversal XPath pour titre/localisation, `data-testid="pagination-controls-next-button-visible"` pour la pagination (remplace l'ancien `aria-label` dépendant de la langue).
- **Run réel validé** (03/07/2026, `MAX_PROFILES=5`) : 5 profils cohérents extraits (noms, URLs, localisations, titres de coachs conformes à la requête), aucun blocage/restriction de compte constaté.
- `MAX_PROFILES` remonté à **25** dans `run_poc001.py` pour le test final du critère d'acceptation.
- Points de vigilance restants : les sélecteurs XPath pour titre/localisation supposent une structure à 3 `<p>` fixe (nom, titre, localisation) dans le bloc info de la carte — un profil qui n'affiche pas l'un de ces champs peut décaler l'extraction des champs suivants (dégrade vers `""`, ne fait pas planter le run).
- Lancement de l'app **non nécessaire** : aucun fichier `frontend_streamlit/` touché.
- **Run final validé (04/07/2026, `MAX_PROFILES=25`)** : 25 profils cohérents extraits (noms, URLs, localisations, titres tous liés au coaching professionnel), export CSV vérifié par script (4 colonnes attendues, aucun nom/URL vide, aucune URL avec résidu de query string, aucune colonne email). Aucun blocage/restriction de compte constaté ; l'utilisateur a enregistré ce run (OBS) comme démo pour Henri-Pierre Michaud et Christophe Hoffsteter (client D'un Pas Décidé).
- **POC-001 → DONE.** Tous les critères d'acceptation sont remplis.
- Prochain ticket : **POC-002** — Extraction de l'email depuis la page profil individuelle (hors scope POC-001, décision du 02/07/2026 dans Backlog.md). Prompt préparé dans `document/prompts_plans/prompt_POC-002.md`.

## 3. POC-002 — Extraction de l'email depuis la page profil individuelle (07/07/2026)

- Plan validé par l'utilisateur (5 profils, script `run_poc002.py` dédié plutôt que d'étendre `run_poc001.py`) et sauvegardé dans `document/prompts_plans/plan_POC-002.md`.
- Sélecteurs de la page profil ajoutés dans `source/backend/adapters/scraping/selectors.py` (`LinkedInProfileSelectors`) : lien "Coordonnées" matché par son texte visible (XPath) car sans id/data-testid/href stable sur le DOM réel — l'hypothèse initiale d'une route overlay dédiée (`overlay/contact-info`) était fausse (l'href pointe juste vers l'URL du profil suivie de `#`) ; corrigée après un dump HTML réel (même méthode que pour les sélecteurs POC-001). La fenêtre elle-même (`dialog[data-testid="dialog"]`) et le lien email (`a[href^="mailto:"]`) sont en revanche stables et vérifiés sur un dump réel.
- Nouveau module `source/backend/adapters/scraping/profile_email.py` : `clean_email` (logique pure, testable sans navigateur), `extract_email_from_profile_page`/`visit_profile_and_extract_email`/`enrich_profiles_with_email` (Playwright, dégradent toujours vers `""` au lieu de lever une exception).
- Nouveau script `source/backend/adapters/scraping/run_poc002.py` : recherche (réutilise `search_and_extract` de POC-001) puis enrichissement email profil par profil, `MAX_PROFILES=5`, export vers `profils_extraits_email.csv` (fichier distinct de la démo POC-001, ajouté au `.gitignore` — contient des emails).
- `source/backend/adapters/storage/csv_export.py` étendu avec la colonne `email` (`restval=""` pour ne jamais planter si un profil ne l'a pas encore).
- Tests ajoutés : `tests/unit/test_profile_email.py` (4 tests, validation/nettoyage d'email) ; `tests/unit/test_csv_export.py` mis à jour (colonne email, valeur par défaut si absente).
- Aparté hors ticket, à la demande de l'utilisateur : correction de `.claude/settings.local.json` — `"Bash(*)"`/`"PowerShell(*)"`/`"Read(**)"` ne sont pas des motifs blanket-allow valides (matchent un préfixe littéral `*`, jamais une vraie commande) ; remplacés par les noms d'outils seuls (`"Bash"`, `"PowerShell"`, `"Read"`).
- **Run réel validé** (07/07/2026, `MAX_PROFILES=5`) : recherche + visite individuelle des 5 pages profil, fenêtre "Coordonnées" ouverte avec succès pour les 5, aucun blocage/restriction de compte constaté. CSV exporté avec la colonne email (`profils_extraits_email.csv`, non commité).
- **Aucun des 5 profils testés n'affichait son email publiquement** (champ vide pour les 5) — comportement LinkedIn attendu (l'email de contact n'est visible par défaut qu'au propriétaire du profil). Le mécanisme d'extraction a été vérifié structurellement (même structure de fenêtre confirmée avec un vrai lien `mailto:` sur le propre profil LinkedIn de l'utilisateur), mais l'extraction positive sur un profil tiers n'a pas pu être observée dans ce lot précis.
- Fichiers créés : `source/backend/adapters/scraping/{profile_email,run_poc002}.py`, `tests/unit/test_profile_email.py`, `document/prompts_plans/plan_POC-002.md`.
- Fichiers modifiés : `source/backend/adapters/scraping/selectors.py`, `source/backend/adapters/storage/csv_export.py`, `tests/unit/test_csv_export.py`, `.gitignore`, `.claude/settings.local.json`, `document/Backlog.md`, `document/claude_code/task_list.md`.
- Tests lancés : `pytest tests/unit/ -v` → 12 passed, 0 failed ; `pytest tests/ --collect-only -q` → 12 tests collectés.
- **Run remonté à 25 profils** (07/07/2026, `MAX_PROFILES=25` dans `run_poc002.py`, même progression que POC-001) : aucun blocage/restriction de compte constaté, export CSV complet (25 lignes). **0 profil sur 25 n'affichait son email publiquement** (confirmé visuellement par l'utilisateur pendant l'exécution) — confirme sur un échantillon plus large le constat du lot de 5 initial (0/5 puis 0/25, soit 0/30 au total). Le mécanisme reste validé structurellement mais n'a jamais été déclenché positivement sur un profil tiers réel.
- **POC-002 → DONE**, avec la réserve documentée ci-dessus (email jamais observé positivement sur un tiers, sur 30 profils testés au total). Point ouvert non cadré : demande client d'un "autre moyen de contact direct" si l'email est indisponible (Backlog.md POC-002) — décision business en attente, d'autant plus pertinente vu ce taux de 0/30, aucun développement prévu.
- Lancement de l'app **non nécessaire** : aucun fichier `frontend_streamlit/` touché.
- Prochain ticket : **POC-003** — Scoring et catégorisation des profils (Phase 2), toujours **BLOCKED** en attente des exemples de calibration du client (2 reçus sur 5-10+2-3 attendus). Prompt de cadrage préparé dans `document/prompts_plans/prompt_POC-003.md` en anticipation, mais le ticket ne peut pas démarrer réellement tant que le complément n'est pas reçu.

## 4. POC-005 — Test de faisabilité d'envoi d'une invitation LinkedIn avec note (08/07/2026)

- Plan validé par l'utilisateur (liste blanche 2 URLs au départ, sauvegardé dans `document/prompts_plans/plan_POC-005.md`), puis étendue à 3 URLs en cours de session (ajout de Wanda Kleck, fille de l'utilisateur, décision utilisateur documentée dans `Backlog.md`).
- Sélecteurs ajoutés dans `selectors.py` (`LinkedInInviteSelectors`), identifiés via inspection DOM en direct avec l'utilisateur (menu du navigateur + dumps HTML ponctuels), même méthode que POC-001/POC-002. Deux difficultés inattendues, résolues et documentées dans `Backlog.md` : (1) le menu déroulant "..." nécessite d'essayer chaque élément correspondant individuellement plutôt que de dépendre du filtre `:visible` de Playwright, qui échouait alors que le bouton était visible à l'écran ; (2) la fenêtre "Ajouter une note à votre invitation ?" s'est révélée être un composant à part (probablement Shadow DOM, invisible à `page.content()`/XPath malgré un rendu visuel confirmé), résolu avec des sélecteurs CSS `:has-text()` de Playwright (qui traverse le Shadow DOM) plutôt que du XPath.
- Nouveau module `source/backend/adapters/scraping/internal_invite_test.py` : liste blanche en dur (`WHITELISTED_PROFILE_URLS`, 3 URLs), `is_url_whitelisted`/`validate_note_length` (logique pure), `send_invitation_with_note` qui refuse structurellement (lève une exception) toute URL hors liste avant toute navigation, et renvoie un statut explicite parmi `sent`/`already_connected`/`failed` (pas juste succès/échec binaire) pour distinguer un profil déjà connecté en 1er degré (sans objet) d'un vrai échec technique.
- Nouveau script `source/backend/adapters/scraping/run_poc005.py` : exécution unique et manuelle sur les 3 profils, notes statiques validées par l'utilisateur.
- Tests ajoutés : `tests/unit/test_internal_invite_test.py` (7 tests : refus de toute URL hors liste blanche avec variantes proches, acceptation des 3 URLs whitelistées, longueur de note aux limites).
- **Run réel exécuté (08/07/2026)** : Henri-Pierre → `already_connected` confirmé (déjà 1er degré, pas d'option "Se connecter"). Christophe → invitation avec note envoyée et **confirmée réellement reçue** par l'utilisateur (statut "En attente" sur son profil + présente dans la liste "Envoyées" du compte de test). Wanda → le script a rapporté `sent`, mais vérification sur son profil : bouton "Se connecter" resté actif, **l'invitation n'a en réalité jamais été reçue**. Décision utilisateur : pas de nouvelle tentative (risque de quota/blocage), le ticket se clôt sur ce résultat mixte plutôt que de forcer un 2e essai.
- **Limite importante découverte et documentée dans le code** (`internal_invite_test.py`, commentaire sur le retour `SENT`) : le statut `sent` signifie seulement que le clic sur "Envoyer" n'a pas levé d'erreur côté script — ce n'est pas une confirmation que LinkedIn a traité l'invitation côté serveur. Le cas Wanda le prouve concrètement. Toute réutilisation future de ce mécanisme devrait ajouter une vérification post-envoi avant de faire confiance à ce statut.
- Aucun blocage/restriction du compte LinkedIn constaté. Quota LinkedIn réellement consommé : 1 invitation personnalisée sur 3 pour le mois en cours (Christophe uniquement).
- Fichiers créés : `source/backend/adapters/scraping/{internal_invite_test,run_poc005}.py`, `tests/unit/test_internal_invite_test.py`, `document/prompts_plans/plan_POC-005.md`.
- Fichiers modifiés : `source/backend/adapters/scraping/selectors.py` (ajout `LinkedInInviteSelectors`), `.gitignore` (ajout `debug_poc005/`, captures de diagnostic), `document/Backlog.md`, `document/claude_code/task_list.md`.
- Fichiers temporaires de diagnostic (non commités, gitignorés) : `debug_poc005/` (captures d'écran + dumps HTML des étapes en échec pendant le débogage en direct) — peuvent être supprimés localement, aucune information sensible au-delà du contenu de pages LinkedIn déjà publiques.
- Tests lancés : `pytest tests/unit/ -v` → 19 passed, 0 failed ; `pytest tests/ --collect-only -q` → 19 tests collectés.
- **POC-005 → DONE**, avec les deux réserves documentées ci-dessus (résultat mixte 1 envoi réel/1 sans objet/1 échec réel malgré statut erroné ; fiabilité du statut `sent` à améliorer avant toute réutilisation au-delà d'un test de faisabilité).
- Lancement de l'app **non nécessaire** : aucun fichier `frontend_streamlit/` touché.
- Prochain ticket recommandé : **POC-004** — Enrichissement web des profils (coordonnées alternatives), toujours **TODO**, pas encore cadré en détail (garde-fous RGPD déjà posés dans `Backlog.md`, base légale à valider par un professionnel du droit avant tout développement au-delà du POC). POC-003 reste **BLOCKED** en attente des exemples de calibration du client. Prompt préparé dans `document/prompts_plans/prompt_POC-004.md`.
