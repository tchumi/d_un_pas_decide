# Backlog — ProspectionLinkedIn

<!--
Ce fichier est le référentiel de SPECS, pas de statuts.
- Les statuts courants sont dans document/claude_code/task_list.md.
- Ajouter une section ici pour chaque nouveau ticket (specs, critères, décisions).
- Ne pas supprimer les sections des tickets terminés : elles servent d'historique.
-->

## Convention de nommage des tickets

| Préfixe | Domaine |
|---|---|
| POC- | Recherche/extraction/scoring/catégorisation — cœur du pipeline POC |
| UI- | Interface Streamlit |
| BUG- | Bugs identifiés en test ou prod |

---

## POC-001 — Script de recherche + extraction basique de profils LinkedIn

**Objectif** : Valider que le scraping LinkedIn via Playwright permet de rechercher des
profils selon une requête booléenne définie manuellement, et d'extraire de façon fiable
nom, URL LinkedIn, localisation et titre/résumé — sur un petit lot de test, sans
déclencher de blocage ou restriction du compte. L'email est explicitement hors scope
de ce ticket (voir décisions).

**Critères d'acceptation** :
- [x] Script fonctionnel qui extrait au moins 20-25 profils cohérents sur une requête booléenne donnée (25 profils, 04/07/2026)
- [x] Aucun blocage/restriction du compte LinkedIn constaté pendant les tests
- [x] Sélecteurs CSS LinkedIn documentés et isolés dans un module dédié (facilite la maintenance si le DOM change)
- [x] Export CSV propre avec les champs : nom, URL, localisation, titre/résumé (sans email)
- [x] Session LinkedIn persistée localement ; identifiants (`LINKEDIN_EMAIL`/`LINKEDIN_PASSWORD`) dans `.env.local`, jamais en dur dans le code

**Périmètre** :
- `source/backend/adapters/scraping/` — recherche + extraction Playwright, sélecteurs CSS centralisés
- `source/backend/adapters/storage/` — export CSV
- `.env.local` — identifiants LinkedIn (non commité)

**Décisions** :
- 02/07/2026 — Pas de scoring/catégorisation dans ce premier ticket (réservé à la Phase 2) ; lecture seule uniquement, aucun envoi de message/invitation ; volume limité à un petit lot de test, pas de contournement des mesures anti-bot LinkedIn.
- 02/07/2026 — Extraction de l'email hors scope de POC-001 : nécessite de visiter la page profil individuelle (non disponible depuis les cartes de résultats de recherche), donc plus de requêtes par profil. Reporté à un ticket séparé, à cadrer une fois POC-001 validé.
- 02/07/2026 — Identifiants LinkedIn dans `.env.local` confirmés ; connexion initiale reste manuelle dans la fenêtre Playwright (le script ne remplit pas le formulaire de login automatiquement) — la session persistée évite une reconnexion à chaque run. Le remplissage automatique du login à partir de `.env.local` pourra être ajouté plus tard si besoin, sans changer le stockage des identifiants.
- 03/07/2026 — Volume de test ramené à 5 profils (`MAX_PROFILES=5`) pour la toute première phase de test/debug, au lieu des 20-25 du critère d'acceptation — décision explicite pour ne prendre aucun risque de blocage du compte LinkedIn personnel utilisé en test. Le paramètre est configurable ; passage à 20-25 prévu une fois un run validé sans blocage constaté.
- 03/07/2026 — Run à 5 profils validé : 5 profils cohérents extraits (noms, URLs, localisations, titres de coachs conformes à la requête), aucun blocage ni restriction de compte constaté. `MAX_PROFILES` remonté à 25 dans `run_poc001.py`. Test final à 25 profils prévu par l'utilisateur le 04/07/2026 au matin, avec enregistrement du run comme démo pour Henri-Pierre Michaud et Christophe Hoffsteter (client D'un Pas Décidé).
- 03/07/2026 — Requête booléenne de test confirmée : celle de `document/spec/spec_onboarding_prospection_linkedin.md` (`("coach business" OR "coach professionnel" OR "coach entreprise") AND (France) NOT ("life coach" OR "sportif")`).
- 03/07/2026 — Ajout de `browser_profile/` (dossier de session Playwright, cookies LinkedIn) et `profils_extraits.csv` au `.gitignore`, hors périmètre initialement listé pour ce ticket mais validé explicitement par l'utilisateur : aucun pattern existant ne couvrait le dossier de session, qui expose l'équivalent d'un accès au compte connecté s'il était commité par erreur.
- 04/07/2026 — Run final à 25 profils validé par l'utilisateur (enregistré en démo pour Henri-Pierre Michaud et Christophe Hoffsteter) : 25 profils cohérents, aucun blocage constaté. **POC-001 clos (DONE).**

---

## POC-002 — Extraction de l'email depuis la page profil individuelle

**Objectif** : Étendre le pipeline POC-001 pour récupérer l'email de chaque profil déjà
extrait, en visitant sa page profil individuelle (l'email n'est pas disponible depuis
les cartes de résultats de recherche).

**Critères d'acceptation** :
- [x] Email récupéré pour les profils qui l'affichent publiquement, champ vide sinon (07/07/2026)
- [x] Même lot de test que la première phase de POC-001 (`MAX_PROFILES=5`)
- [x] Aucun blocage/restriction du compte LinkedIn constaté pendant les tests
- [x] Export CSV étendu avec la colonne `email`

**Contraintes connues** (héritées de POC-001 et de la spec) :
- Une requête HTTP supplémentaire par profil → risque de blocage de compte plus élevé qu'une simple recherche ; volume et pauses "humaines" recalibrées en conséquence (`MAX_PROFILES=5`, pauses aléatoires entre chaque visite de profil).
- L'email n'est pas toujours visible publiquement sur la page profil (dépend des réglages de confidentialité du profil visité) — champ vide plutôt qu'échec bloquant.
- Lecture seule, pas d'envoi de message/invitation (inchangé depuis POC-001).

**Périmètre** :
- `source/backend/adapters/scraping/` — `selectors.py` (sélecteurs page profil), `profile_email.py` (nouveau), `run_poc002.py` (nouveau)
- `source/backend/adapters/storage/` — `csv_export.py` (colonne `email`)

**Décisions** :
- 02/07/2026 — Ticket créé en report de POC-001 (voir décisions POC-001 ci-dessus).
- 04/07/2026 — Retour client (Christophe Hoffsteter) sur le CSV de démo POC-001 : demande explicite de récupérer l'email ("pas possible de récupérer une adresse courriel ?"), confirme la priorité de ce ticket. Demande aussi un "autre moyen de contact direct" si l'email n'est pas disponible — **toujours pas cadré à la clôture de ce ticket** (voir résultat du run réel ci-dessous, qui rend la question d'autant plus pertinente) ; reporté à une décision business, aucun développement prévu tant que ça n'est pas cadré.
- 04/07/2026 — Le même retour client demande d'inviter automatiquement chaque profil extrait dans le réseau LinkedIn du compte utilisé. **Refusé pour cette phase** : contredit directement la spec ("pas d'envoi de messages ni d'invitations automatisées dans cette phase") et le périmètre hors-scope déjà listé ci-dessus pour ce ticket. Risque de restriction du compte LinkedIn si automatisé. Cohérent avec le phasage : la Phase 3 prévoit un contact semi-automatisé mais avec envoi resté supervisé par le client, pas une automatisation complète. Réponse à formuler côté business, aucun développement prévu sur ce point.
- 07/07/2026 — Volume de test limité à 5 profils (`MAX_PROFILES=5` dans `run_poc002.py`, script dédié distinct de `run_poc001.py`), par prudence : une requête supplémentaire par profil (visite de page individuelle) augmente le risque de blocage/restriction de compte par rapport à la simple recherche de POC-001.
- 07/07/2026 — Sélecteurs de la page profil corrigés après diagnostic sur DOM réel (même méthode que POC-001) : le lien "Coordonnées" n'a ni id ni data-testid et son href pointe vers l'URL du profil suivie de `#` (pas de route overlay dédiée comme supposé initialement) — matché par son texte visible à la place (dépendance à la langue du compte, comme l'ancien bouton de pagination POC-001). La fenêtre qui s'ouvre est en revanche un vrai `<dialog data-testid="dialog">`, et l'email y est un lien `mailto:` standard — ces deux derniers points sont stables et vérifiés.
- 07/07/2026 — **Run réel validé** sur le lot de 5 profils (recherche + visite individuelle) : la fenêtre "Coordonnées" s'ouvre correctement pour chacun des 5, aucun blocage/restriction de compte constaté, export CSV étendu avec la colonne `email`. **Aucun des 5 profils testés n'affichait son email publiquement** (champ vide pour les 5) — comportement LinkedIn attendu : par défaut, seul le propriétaire du profil voit son propre email dans "Coordonnées", les autres profils ne l'exposent que s'ils l'ont explicitement rendu visible, ce que peu de comptes font. Le mécanisme d'extraction lui-même a été vérifié structurellement valide (même structure de fenêtre/lien `mailto:` confirmée sur le propre profil de l'utilisateur), mais l'extraction positive d'un email tiers n'a pas été observée sur ce lot précis — [Inférence] probabilité faible mais non nulle qu'un profil avec email public déclenche un cas non testé. **POC-002 clos (DONE)**, avec cette réserve documentée.
- 07/07/2026 — Le taux de 0/5 email public observé renforce la pertinence de la demande client du 04/07/2026 sur un "autre moyen de contact direct" (voir ci-dessus) — reste une décision business ouverte, à trancher avant un éventuel ticket dédié.
- 07/07/2026 — `MAX_PROFILES` remonté à 25 dans `run_poc002.py` (même progression que POC-001) après validation du run à 5 profils sans blocage. **Run réel confirmé sur 25 profils** : recherche + visite individuelle des 25 pages profil, aucun blocage/restriction de compte constaté, export CSV complet (25 lignes + en-tête) avec la colonne `email`. **0 profil sur 25 n'affichait son email publiquement** (vérifié visuellement par l'utilisateur pendant l'exécution, en plus du CSV) — confirme sur un échantillon plus large le constat du lot de 5 : l'email de contact n'est quasiment jamais rendu visible publiquement par les profils tiers sur LinkedIn. Le mécanisme d'extraction reste validé structurellement (voir plus haut) mais n'a été déclenché positivement sur aucun profil réel à ce stade, sur 30 profils testés au total (5 + 25).

---

## POC-003 — Scoring et catégorisation des profils (Phase 2)

**Objectif** : Catégoriser chaque profil extrait dans une des 3 classes cibles (coach
business débutant, expérimenté, outdoor/nature — indifférencié par défaut) et lui
attribuer un score de pertinence. **Pas encore cadré** : ticket créé en stub pour ne pas
perdre les exemples de calibration reçus du client ; cadrage complet à faire au
démarrage réel du ticket (une fois POC-002 terminé), via le protocole habituel
(`prompt_générique.md`).

**Exemples de calibration reçus du client** (Christophe Hoffsteter, 04/07/2026, sur le
CSV de démo POC-001) :
- Anne-Laure F., "Coach en développement personnel, professionnel et scolaire certifiée
  par Coaching Ways France Level 2 ICF (RNCP niveau 6)" → catégorie indifférenciée
  acceptable mais moins intéressante (mélange avec développement personnel/scolaire).
- Cécile Pollin, "HR Senior Manager - Responsable RH Senior - Transformation" → à
  exclure, pas un coach du tout (faux positif de la recherche booléenne).

**Décisions** :
- 04/07/2026 — Toujours en attente des 5-10 exemples de "bons" profils et 2-3 "mauvais"
  demandés initialement au client (2 reçus sur le total attendu) — bloquant pour cadrer
  le scoring/la catégorisation en détail. Statut `BLOCKED` dans `task_list.md` en
  attendant ce complément.
