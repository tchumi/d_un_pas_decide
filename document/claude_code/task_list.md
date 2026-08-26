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
| POC-003 | TODO | P1 | scoring | Scoring et catégorisation des profils (Phase 2) | À cadrer — **débloqué** (requalifié le 25/08/2026 après relecture des mails client des 08 et 13/07/2026, restés non consignés). Calibration bon/mauvais couverte (validation en bloc du CSV de démo + 1 exclusion explicite) et vocabulaire de la catégorie outdoor fourni ; priorité client explicite du 13/07 sur ce ticket. Périmètre cadrable : exclusion des non-coachs, catégorie outdoor par mots-clés, score de pertinence — **débutant/expérimenté laissé indifférencié** (nécessiterait d'extraire la durée d'expérience de la page profil, et une réponse d'Henri-Pierre Michaud sur un scoring plus nuancé, toujours en attente). Détail et sources dans `document/Backlog.md`. |
| POC-006 | TODO | P2 | scraping/storage | Renouvellement du gisement de profils (mémoire des profils déjà vus) | À cadrer — créé le 26/08/2026. Deux runs successifs de la même requête ramènent le même lot (`search_and_extract` repart de la page 1 ; `export_profiles_to_csv` écrase en mode `"w"`, aucune persistance ni déduplication) → cible client de 50 profils/semaine inatteignable. Introduire un magasin persistant (SQLite, dans la stack mais jamais introduit) dédupliqué sur l'URL de profil, et paginer jusqu'à N profils **inconnus**. Solde au passage deux garde-fous RGPD déjà inscrits au Backlog mais intenables avec un CSV écrasé (`date_collecte`, marquage « à ne plus traiter »). **À enchaîner après POC-003** : les deux touchent `csv_export.py`. Détail dans `document/Backlog.md`. |

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
| POC-004 | DONE | P2 | enrichissement | Enrichissement web des profils — pipeline v1 déterministe (Brave Search API, sans LLM) | Run réel du 10/07/2026 sur 25 profils (CSV POC-002) : 11/25 candidats après filtrage de domaines, dont 1/25 vrai positif confirmé (site + email personnels), 1/25 positif partiel (site pertinent, email non personnel), 7/25 faux positifs (liste noire étendue de 4 domaines en conséquence), 2/25 non vérifiés, 14/25 sans candidat. **Taux de pertinence observé : 1/25 (4%) exploitable tel quel, 2/25 (8%) en comptant le partiel** — donnée à trancher avec le client pour juger de l'utilité d'un palier LLM (Palier 1, non activé). Deux bugs trouvés et corrigés en conditions réelles : dépassement de la limite de 50 mots de l'API Brave Search (titres LinkedIn longs) et regex de validation email trop permissive (caractère résiduel `\` sur un cas réel). Zéro appel LLM, clé lue depuis `.env.local`. Tests : 35 passed, 0 failed. |
