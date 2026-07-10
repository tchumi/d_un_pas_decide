# task_list.md — Backlog priorisé

## 1. Règles de statut

- `TODO` : à faire.
- `IN_PROGRESS` : démarré et non terminé.
- `DONE` : terminé et vérifié.
- `DECIDED` : décision prise, pas de code à produire (tickets de cadrage).
- `BLOCKED` : en attente d'un prérequis explicite.

## 2. Backlog courant

| ID | Statut | Priorité | Module | Tâche | Critère d'acceptation |
|---|---|---|---|---|---|
| POC-003 | BLOCKED | P2 | scoring | Scoring et catégorisation des profils (Phase 2) | À cadrer — bloqué en attente des 5-10 bons/2-3 mauvais profils exemples du client (2 reçus sur le total attendu) |
| POC-004 | TODO | P2 | enrichissement | Enrichissement web des profils — pipeline v1 déterministe (Brave Search API, sans LLM), paliers LLM/agents conditionnels | À cadrer — voir pipeline v1 et garde-fous RGPD dans Backlog.md, base légale à valider par un professionnel du droit |

<!-- 
Conventions :
- Priorité : P0 (bloquant), P1 (sprint courant), P2 (next), P3 (backlog)
- ID prefix : choisir un préfixe par domaine fonctionnel (ex: MGD-, LDG-, BUG-)
- Ne pas mettre de specs détaillées ici → dans document/Backlog.md
- Les statuts et métriques (nb tests) vont ICI uniquement
-->

## 3. Tâches déjà considérées faites

| ID | Statut | Priorité | Module | Tâche | Critère d'acceptation |
|---|---|---|---|---|---|
| POC-001 | DONE | P1 | scraping | Script de recherche + extraction basique de profils LinkedIn (Playwright) | 25 profils cohérents extraits sur la requête donnée (04/07/2026), export CSV nom/URL/localisation/titre sans email, sélecteurs CSS isolés dans selectors.py, aucun blocage de compte constaté. Tests : 7 passed, 0 failed. |
| POC-002 | DONE | P1 | scraping | Extraction de l'email depuis la page profil individuelle | Run réel remonté à 25 profils (07/07/2026, `MAX_PROFILES=25`) : fenêtre "Coordonnées" ouverte à chaque fois, export CSV étendu avec colonne email, aucun blocage de compte constaté. 0/25 email public (0/5 puis 0/25, comportement LinkedIn normal, champ vide conforme au critère d'acceptation) ; mécanisme d'extraction validé structurellement (mailto: confirmé sur le propre profil de l'utilisateur) mais jamais observé positivement sur un tiers, sur 30 profils testés au total. Tests : 12 passed, 0 failed. |
| POC-005 | DONE | P2 | scraping | Test de faisabilité d'envoi d'une invitation LinkedIn avec note (3 destinataires internes, liste étendue en cours de ticket) | Run réel du 08/07/2026 : Henri-Pierre → `already_connected` (confirmé, déjà 1er degré) ; Christophe → invitation envoyée et **confirmée reçue** ("En attente" sur son profil + liste "Envoyées") ; Wanda → statut `sent` rapporté par le script mais **invitation jamais reçue en réalité** (bouton "Se connecter" resté actif) — limite documentée : le statut `sent` ne prouve pas la confirmation serveur, seulement l'absence d'erreur au clic. Liste blanche en dur (3 URLs) avec refus structurel de toute autre URL, prouvé par test dédié. Aucun blocage/restriction de compte LinkedIn constaté. Quota réellement consommé : 1/3 invitations personnalisées du mois. Tests : 19 passed, 0 failed. |
