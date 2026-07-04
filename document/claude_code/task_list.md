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
| POC-002 | TODO | P1 | scraping | Extraction de l'email depuis la page profil individuelle | À cadrer (voir prompt_POC-002.md) |

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
