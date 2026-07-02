# Spécification projet — POC Prospection LinkedIn automatisée

## Contexte

Client : D'un Pas Décidé (Henri-Pierre Michaud & Christophe Hoffsteter), organisme
de coaching business, 15 ans d'expérience. Ils recrutent aujourd'hui des coachs
prospects sur LinkedIn entièrement à la main (recherche, qualification, contact,
relance) et veulent automatiser la partie la plus chronophage sans se mettre en
danger vis-à-vis des CGU LinkedIn.

## Objectif du POC

Valider qu'on peut automatiser, à petit volume, la chaîne :
recherche LinkedIn → extraction de profils → scoring/catégorisation → base de
données exploitable — en partant de leur méthode manuelle actuelle, sans usine à
gaz.

## Ce que le projet DOIT faire (scope POC)

- Rechercher des profils LinkedIn via une requête définie manuellement
  (expression booléenne du type `("coach business" OR "coach professionnel" OR
  "coach entreprise") AND (France) NOT ("life coach" OR "sportif")`).
- Extraire pour chaque profil : nom, URL LinkedIn, localisation, titre/résumé
  (pour la catégorisation), et l'adresse email si visible sur le profil.
- Catégoriser chaque profil dans une des 3 classes cibles :
  1. Coach business débutant
  2. Coach business expérimenté
  3. Coach business outdoor / nature
  (catégorie "indifférenciée" par défaut si aucune classe ne ressort clairement)
- Attribuer un score de pertinence par profil.
- Stocker les résultats dans une base simple (CSV ou SQLite au démarrage,
  pas de dépendance à un service tiers hébergé).
- Rester à volume faible : cible ~50 profils/semaine en sortie, donc quelques
  centaines de profils scrapés max par semaine en amont du filtrage.

## Ce que le projet NE DOIT PAS faire (hors scope explicite)

- Pas d'envoi de messages ni d'invitations automatisées dans cette phase
  (lecture seule uniquement).
- Pas d'infrastructure tournant en continu H24 — exécution ponctuelle,
  déclenchée manuellement ou via tâche planifiée légère, à faible fréquence.
- Pas de contournement actif des mesures anti-bot de LinkedIn (rotation de
  proxies agressive, empreintes falsifiées, etc.) — l'objectif est de rester
  à un volume qui ne nécessite pas ce genre de technique.
- Pas de traitement de masse (pas de cible à 100 000 profils, jamais).
- Pas de stockage de données personnelles sans base légale claire — la question
  RGPD/CNIL reste ouverte et doit être tranchée avant tout passage en
  production réelle (formulaire de consentement à prévoir côté client final).

## Contraintes techniques connues

- LinkedIn n'expose pas d'API publique utilisable pour ce cas d'usage (API
  officielle très restreinte, principalement de l'authentification OAuth).
  → Passage par scraping de l'interface web nécessaire.
- Le DOM LinkedIn change régulièrement : les sélecteurs CSS doivent être
  centralisés et faciles à corriger, pas dispersés dans le code.
- Connexion via compte LinkedIn réel (personnel en phase de test, compte dédié
  D'un Pas Décidé visé pour la suite) — pas de gestion de mot de passe en dur,
  session persistée localement.
- Stack cible : Python natif + Playwright (éviter d'empiler des frameworks
  tiers non maîtrisés). Décision à valider/challenger pendant le POC.
- Pas d'environnement cloud imposé au démarrage — un hébergement OVH existe
  déjà côté client si besoin d'y faire tourner un script ponctuel plus tard.

## Volumétrie de référence

- Cible réaliste : 15 à 30 conversions/an (recrutement final de coachs), soit
  environ 100 contacts qualifiés/mois → ~25 profils qualifiés/semaine en sortie
  de filtrage, avec un facteur d'entonnoir estimé x10 en amont (donc quelques
  centaines de profils bruts scrapés par semaine grand maximum).
- Ne jamais optimiser pour un volume supérieur sans validation explicite du
  client — la faible volumétrie est une contrainte assumée, pas une limitation
  technique à lever.

## Phasage envisagé

1. **Phase 1 (POC actuel)** : script de recherche + extraction basique sur un
   petit lot de profils, validation que l'extraction est fiable et que le
   volume reste sous le radar.
2. **Phase 2** : scoring/catégorisation automatisé (LLM ou règles) à partir
   d'exemples de "bons" et "mauvais" profils fournis par le client.
3. **Phase 3** : pipeline de contact semi-automatisé (angle d'approche
   personnalisé, statut de suivi), avec action d'envoi restant supervisée par
   le client dans un premier temps.
4. **Phase 4 (hors scope actuel)** : volet communauté / base de connaissances
   (migration des notes Obsidian du client vers un système structuré).

## Questions ouvertes / dépendances côté client

- Exemples concrets de "bons" et "mauvais" profils (5-10 de chaque) — bloquant
  pour calibrer le scoring, demandés mais non encore reçus.
- Décision sur la création d'un compte LinkedIn dédié à la prospection
  (recommandé, pas encore fait à ce stade).
- Position sur la conformité RGPD/CNIL pour la collecte de données de
  prospects B2B sans consentement préalable.

## Definition of Done du POC

- Script fonctionnel qui extrait au moins 20-25 profils cohérents sur une
  requête donnée, sans blocage de compte pendant les tests.
- Sélecteurs CSS documentés et isolés pour faciliter la maintenance.
- Export CSV propre avec les champs : nom, URL, localisation, titre/résumé.
- Retour explicite sur la faisabilité (fiable / fragile / bloquant) et sur la
  dette technique estimée si le scraping s'avère instable dans la durée.
