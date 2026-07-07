# Plan — POC-002 : Extraction de l'email depuis la page profil individuelle

## Résumé du ticket
Étendre le pipeline POC-001 pour visiter la page profil individuelle de chaque profil
déjà extrait et en récupérer l'email s'il est visible publiquement, sans invitation ni
message automatisé (hors périmètre, refusé pour cette phase — décision Backlog.md
04/07/2026). Demande confirmée par le client (Christophe Hoffstetter, 04/07 et
07/07/2026).

## Critère d'acceptation retenu
Email récupéré pour les profils qui l'affichent publiquement, champ vide sinon, sur le
même lot de test que POC-001 (5 profils), aucun blocage de compte constaté, export CSV
étendu avec la colonne email.

## Décisions validées par l'utilisateur (07/07/2026)
1. Volume de test limité à **5 profils** (`MAX_PROFILES=5`), par prudence — une requête
   supplémentaire par profil (visite de page individuelle) augmente le risque de
   blocage/restriction de compte par rapport à la simple recherche de POC-001.
2. Script d'exécution dédié : **`run_poc002.py`** (nouveau), plutôt que d'étendre
   `run_poc001.py` (POC-001 est DONE, réutilise `search_and_extract`).
3. Pas d'invitation/message automatisé (inchangé, lecture seule).
4. La demande client d'un "autre moyen de contact direct" (si email indisponible) reste
   **ouverte, non cadrée**, à documenter dans Backlog.md POC-002 sans développement.

## Fichiers à créer/modifier
- `source/backend/adapters/scraping/selectors.py` — ajout des sélecteurs page profil
  (bouton/lien "coordonnées", overlay contact info, champ email).
- `source/backend/adapters/scraping/profile_email.py` (nouveau) — logique pure de
  nettoyage/validation d'email (testable sans navigateur) + fonction Playwright de
  visite de page profil et extraction (dégrade vers `""` si absent, jamais d'échec
  bloquant).
- `source/backend/adapters/scraping/run_poc002.py` (nouveau) — script d'exécution :
  recherche (réutilise `search_and_extract`) puis enrichissement email par profil,
  avec pause humaine entre chaque visite.
- `source/backend/adapters/storage/csv_export.py` — ajout de `"email"` à
  `PROFILE_CSV_FIELDS`.
- `tests/unit/test_profile_email.py` (nouveau) — validation/nettoyage email.
- `tests/unit/test_csv_export.py` (mise à jour) — colonne email.

## Risque principal
Volume de requêtes supplémentaire (1 visite de page profil par profil déjà extrait) →
risque de blocage/restriction de compte plus élevé qu'en POC-001. Mitigation : lot
réduit à 5, pauses humaines aléatoires entre visites de profil, arrêt propre sans retry
agressif si LinkedIn affiche un signal de restriction/challenge.

## Tests prévus
- Unitaires (sans navigateur) : validation/nettoyage du format email extrait,
  comportement de `csv_export` avec/sans email.
- Non testable hors conditions réelles : présence et structure effective du bouton
  "coordonnées"/overlay sur une vraie page profil LinkedIn, fréquence réelle des
  emails publics, absence de blocage de compte sur le run réel.

## Étapes d'implémentation
1. Sélecteurs page profil dans `selectors.py`.
2. `profile_email.py` (logique pure + fonction Playwright).
3. `run_poc002.py` (assemblage recherche + enrichissement email, `MAX_PROFILES=5`).
4. Extension `csv_export.py` (colonne email).
5. Tests unitaires ciblés + mise à jour Backlog/task_list/handoff en fin de session.

## Point ouvert (non cadré, hors périmètre de ce ticket)
Demande client d'un "autre moyen de contact direct" si l'email n'est pas disponible —
laissé ouvert dans `document/Backlog.md` (section POC-002), aucun développement prévu
pour ce ticket.
