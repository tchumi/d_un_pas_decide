# Plan POC-005 — Test de faisabilité d'envoi d'une invitation LinkedIn avec note

Validé par l'utilisateur le 08/07/2026, après échanges itératifs (voir décisions ci-dessous).

## Périmètre final validé

**Liste blanche — 3 URLs** (extension du périmètre initial de 2 à 3, décision utilisateur du 08/07/2026, à documenter dans `Backlog.md`) :

- `linkedin.com/in/henri-pierre-michaud-19a0a6b0` (Henri-Pierre Michaud) — **déjà connecté en 1er degré** avec le compte de test (confirmé par l'utilisateur le 08/07/2026). Pas d'option "Se connecter" disponible : traité comme statut `already_connected`, pas comme un échec technique.
- `linkedin.com/in/choffstetter` (Christophe Hoffstetter) — 2e degré confirmé (capture d'écran utilisateur du 08/07/2026 : boutons "Suivre"/"Message"/"..." visibles, pas de "Se connecter" direct → option probablement sous le menu "..."). Invitation réelle tentée.
- `linkedin.com/in/wanda-kleck-76ba342b8` (Wanda Kleck, fille de l'utilisateur, compte LinkedIn tout juste créé) — pas connectée. Invitation réelle tentée. Ajout hors du périmètre initial du ticket (qui prévoyait 2 contacts internes professionnels) — accepté par l'utilisateur, reste interne/consentant.

**Notes d'invitation statiques** (validées par l'utilisateur, ≤300 caractères) :
- Christophe : `"hello ici beau temps et mer calme"`
- Wanda : `"hello Wanda, on arrive..."`
- Henri-Pierre : sans objet (statut `already_connected`, aucune note envoyée).

**Compte de test** : le même compte que le scraping (POC-001/POC-002), `browser_profile/` existant — pas de compte dédié.

## Conception : 3 issues possibles par profil

`send_invitation_with_note` renvoie un statut explicite par profil plutôt qu'un simple succès/échec binaire :
1. `sent` — invitation envoyée avec succès.
2. `already_connected` — pas de bouton "Se connecter" trouvé (déjà en 1er degré) ; cas attendu pour Henri-Pierre.
3. `failed` — erreur technique (sélecteur introuvable, blocage LinkedIn, etc.).

Ce design évite de faire planter le script sur Henri-Pierre et documente proprement que, sur les 3 destinataires, un seul (Henri-Pierre) ne relève pas réellement du mécanisme testé.

## Méthode : inspection HTML en direct avant d'écrire les sélecteurs

Comme pour POC-001 (cartes de résultats) et POC-002 (lien "Coordonnées"), les sélecteurs du bouton "Se connecter" (probablement sous le menu "...") et de la modale de note ne sont pas devinés a priori : un dump HTML réel (session utilisateur, requête ponctuelle) sera fait en premier, sur le profil de Christophe (seul profil confirmé en 2e degré avec accès à l'option), avant d'écrire `LinkedInInviteSelectors`.

## Fichiers à créer / modifier

- `source/backend/adapters/scraping/selectors.py` — ajout `LinkedInInviteSelectors` (bouton "...", "Se connecter"/"Connect", "Ajouter une note"/"Add a note", textarea, bouton d'envoi).
- `source/backend/adapters/scraping/internal_invite_test.py` (nouveau) — `WHITELISTED_PROFILE_URLS` (3 URLs en dur), `is_url_whitelisted(url)` (pur), `validate_note_length(note)` (pur), `send_invitation_with_note(page, url, note)` (Playwright, refuse toute URL hors liste avant toute navigation, renvoie un des 3 statuts).
- `source/backend/adapters/scraping/run_poc005.py` (nouveau) — script d'exécution unique et manuelle sur les 3 profils avec leurs notes respectives (Henri-Pierre inclus pour confirmer/documenter son statut `already_connected`, mais sans note puisque sans objet).
- `tests/unit/test_internal_invite_test.py` (nouveau) — tests ciblés sur la logique pure uniquement (refus liste blanche avec variantes proches, acceptation des 3 URLs, longueur de note).

## Risque principal

Volume très faible (3 tentatives dont 1 sans effet réel) vers des contacts réels/connus, indiscernable d'un usage humain normal. Risque technique dominant : sélecteurs du menu "..." / modale de note non vérifiés a priori, d'où l'inspection HTML en direct en premier.

## Hors scope (inchangé)

Pas d'envoi de message direct, pas de boucle/tâche planifiée, pas d'extension à de vrais prospects, liste blanche non branchée sur le pipeline de scraping.
