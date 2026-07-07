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
| POC-002 | DONE | P1 | scraping | Extraction de l'email depuis la page profil individuelle | Run réel sur 5 profils (07/07/2026) : fenêtre "Coordonnées" ouverte pour les 5, export CSV étendu avec colonne email, aucun blocage de compte constaté. 0/5 email public dans ce lot (comportement LinkedIn normal, champ vide conforme au critère d'acceptation) ; mécanisme d'extraction validé structurellement (mailto: confirmé sur le propre profil de l'utilisateur) mais pas observé positivement sur un tiers dans ce lot. Tests : 12 passed, 0 failed. |
