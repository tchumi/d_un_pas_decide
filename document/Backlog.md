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

---

## POC-004 — Enrichissement web des profils (coordonnées alternatives)

**Objectif** : Rechercher des informations complémentaires sur le web pour les profils
déjà extraits (en priorité : un moyen de contact alternatif quand l'email LinkedIn n'est
pas public), en réponse à la demande client du 04/07/2026 et au constat POC-002 (0 email
public sur 30 profils testés). **Pas encore cadré** : ticket créé en stub ; cadrage
complet à faire au démarrage réel du ticket via le protocole habituel
(`prompt_générique.md`).

**Pipeline v1 (base, 100% déterministe, sans LLM)** :
1. **Recherche** via une vraie API de recherche (Brave Search API — voir décisions ;
   Bing Search API écarté, retiré par Microsoft le 11/08/2026), requête construite depuis
   nom + titre + localisation, top 3-5 résultats.
2. **Filtrage déterministe par liste noire de domaines** (linkedin.com, facebook.com,
   pagesjaunes, annuaires, wikipedia...) pour ne garder que des candidats plausibles
   (site perso/pro).
3. **Visite de la page candidate restante** (requête HTTP simple, même logique que le
   scraping existant) et **extraction par regex déterministe** (pas d'interprétation
   LLM) :
   - lien `mailto:` ou pattern d'email dans le texte → champ `email_web`
   - URL racine du site → champ `site_web`
4. Si rien de concluant : champs vides, comme le pattern déjà établi en POC-002 (champ
   vide plutôt qu'échec bloquant).

Le risque n'est plus l'hallucination (aucune génération/interprétation par un modèle)
mais le mauvais candidat retenu (homonyme, page non pertinente) — contenu par le
filtrage de domaines et par la relecture humaine avant tout contact, comme aujourd'hui.
Nouveau point à documenter : visiter la page candidate = requête HTTP vers un site tiers
(pas LinkedIn ni Google), usage standard à ce volume mais à noter dans le cadrage.

**Paliers conditionnels (non planifiés, à activer seulement si le v1 s'avère
insuffisant)** — inspirés de `document/spec/01_agentic_introduction_planner.ipynb` et
`02_agentic_supervisor.ipynb` :
- **Palier 1 — ajout d'un appel LLM de vérification/extraction** : si le taux de
  candidats pertinents du v1 est trop faible pour être exploitable tel quel, et qu'il
  faut filtrer/trancher automatiquement plutôt que de compter sur la relecture humaine.
- **Palier 2 — agent unique avec outils** (`web_search`, éventuellement visite de page) :
  si une seule recherche ne suffit pas (reformulation nécessaire, désambiguïsation).
- **Palier 3 — REWOO (plan + exécution par dépendances)** : a priori non pertinent ici,
  les profils sont traités indépendamment les uns des autres (pas de dépendances entre
  eux à orchestrer).
- **Palier 4 — architecture superviseur multi-agents** : pertinent uniquement en cas de
  fusion avec le scoring/catégorisation (POC-003) dans un système unique — décision
  architecturale à part entière, non engagée par ce ticket.
- Ces paliers introduiraient une nouvelle dépendance (LLM + clé API, ex. OpenAI/
  Anthropic dans `.env.local`) et un risque d'hallucination à gérer explicitement —
  aucun n'est nécessaire tant que le v1 n'a pas démontré ses limites en conditions
  réelles.

**Garde-fous RGPD à intégrer dès le cadrage** (base légale envisagée : intérêt légitime,
art. 6.1.f RGPD, prospection B2B) :
- **Nécessité / minimisation** : ne collecter que des champs directement utiles à la
  prospection (`email_web`, `site_web`) — pas de collecte "au cas où" ; le pipeline v1
  répond justement à une justification précise ("trouver le site/email que la personne
  publie elle-même publiquement"), pas une exploration ouverte du web.
- **Transparence** : prévoir dès la conception un moyen d'informer le prospect dès le
  premier contact (mention légale / template de message), même si l'implémentation
  concrète peut être un ticket ultérieur.
- **Droit d'opposition** : le modèle de données doit permettre de marquer un profil
  comme "à ne plus traiter" facilement.
- **Conservation limitée** : prévoir un champ `date_collecte` par profil pour permettre
  une purge future — pas de base qui s'accumule indéfiniment sans réponse du prospect.
- **Ne pas scraper directement les pages de résultats des moteurs de recherche**
  (Google/Bing) — passer par une vraie API de recherche pour ne pas reproduire le même
  risque ToS que celui déjà assumé sur LinkedIn.
- Ce point règle le rapport avec la personne recherchée (RGPD) ; il ne change rien au
  risque ToS/ blocage de compte LinkedIn, qui reste un sujet indépendant et déjà géré
  dans POC-001/POC-002.

**Décisions** :
- 07/07/2026 — Ticket ouvert suite à la demande client du 04/07/2026 ("autre moyen de
  contact direct") et au constat POC-002 (0/30 profils avec email public). Base légale
  envisagée : intérêt légitime (prospection B2B) — à valider par un professionnel du
  droit avant tout passage au-delà du POC, l'analyse ci-dessus n'étant qu'un cadrage
  technique préparatoire, pas un avis juridique.
- 10/07/2026 — Analyse d'une approche multi-agents (LangChain/LangGraph, inspirée de
  `01_agentic_introduction_planner.ipynb` et `02_agentic_supervisor.ipynb`) jugée
  disproportionnée pour ce ticket : ces patterns (REWOO, superviseur) répondent à des
  tâches où une requête complexe unique nécessite d'enchaîner des étapes dépendantes ou
  de croiser des agents spécialisés — notre besoin est une même petite tâche répétée
  indépendamment par profil, plus proche d'une boucle que d'une orchestration.
- 10/07/2026 — **Fournisseur de recherche retenu : Brave Search API** ($5/1000 requêtes,
  5$ de crédit gratuit renouvelé chaque mois — couvre largement notre volume ~200/mois).
  Bing Search API écarté (retiré par Microsoft le 11/08/2026) ; SerpAPI resterait une
  alternative si Brave s'avérait insuffisant (gratuit jusqu'à 250 recherches/mois, puis
  25$/mois pour 1000).
- 10/07/2026 — Pipeline v1 défini comme 100% déterministe (recherche + filtrage de
  domaines + regex d'extraction), sans LLM, pour éviter tout risque d'hallucination dès
  la première version et rester strictement dans la justification RGPD de minimisation.
  Les paliers avec LLM/agents restent conditionnels, non planifiés.

---

## POC-005 — Test de faisabilité d'envoi d'une invitation LinkedIn avec note (validation interne uniquement)

**Objectif** : Valider techniquement la faisabilité d'envoyer une invitation LinkedIn
avec note personnalisée via Playwright — c'est le mécanisme réel derrière la demande
client du 04/07/2026 ("inviter automatiquement chaque profil extrait"), et non un simple
message : Michel n'est très probablement **pas connecté en 1er degré** avec Christophe et
Henri-Pierre sur le compte de test, donc l'envoi d'un message direct n'est pas possible
sans passer d'abord par une invitation. **Uniquement à titre de test de faisabilité, sur
2 destinataires internes et consentants** (Christophe Hoffsteter, Henri-Pierre Michaud),
jamais sur un profil issu du pipeline de scraping/prospects. **Pas encore cadré** :
ticket créé en stub ; cadrage complet à faire au démarrage réel du ticket.

**Dérogation ponctuelle à la règle "lecture seule"** : la spec exclut explicitement
l'envoi de messages/invitations automatisées "dans cette phase". Ce ticket introduit une
exception étroite et documentée, réservée à la validation technique — ce n'est **pas**
une réouverture du scope vers l'automatisation de la prospection réelle. Toute extension
au-delà de ce test (sur de vrais prospects) reste hors scope tant qu'elle n'a pas été
explicitement redécidée.

**Garde-fous à intégrer dès le cadrage** :
- **Liste blanche en dur dans le code** : seules ces 2 URLs LinkedIn sont acceptées par
  la fonction d'envoi — structurellement impossible de la brancher sur la liste des
  prospects scrapés :
  - `linkedin.com/in/henri-pierre-michaud-19a0a6b0` (Henri-Pierre Michaud)
  - `linkedin.com/in/choffstetter` (Christophe Hoffsteter)
- **Volume strictement limité** : 2 invitations au total, exécution manuelle et unique
  (pas de boucle, pas de tâche planifiée).
- **Note d'invitation statique**, validée par l'utilisateur avant envoi (pas de contenu
  généré automatiquement) — LinkedIn limite la note à ~300 caractères.
- **Risque documenté, mais faible à ce volume** : l'envoi d'invitations automatisées est
  précisément le comportement que LinkedIn surveille (taux d'envoi, taux d'acceptation),
  mais 2 invitations vers des contacts réels et connus qui vont probablement accepter
  reste indiscernable d'un usage humain normal — risque non nul mais faible, à confirmer
  si c'est le même compte que celui du scraping ou un compte de test dédié.
- Si Christophe/Henri-Pierre acceptent l'invitation, l'envoi d'un message direct devient
  possible ensuite — mais ça dépend de leur action (non instantané, pas automatisable) et
  reste hors scope de ce ticket : la note d'invitation suffit à valider la faisabilité du
  "premier contact personnalisé" recherché par le client.

**Décisions** :
- 07/07/2026 — Ticket ouvert en réponse à la demande client sur l'automatisation des
  invitations (voir décisions POC-002 du 04/07/2026) — proposé comme validation de
  faisabilité bornée plutôt qu'un refus sec, dans l'attente d'une décision produit sur la
  Phase 3 (contact semi-automatisé supervisé).
- 07/07/2026 — Reformulé de "envoi de message" à "envoi d'invitation avec note" : Michel
  n'étant pas connecté en 1er degré avec les 2 destinataires sur le compte de test, un
  message direct est impossible sans invitation préalable acceptée. L'invitation avec
  note est de toute façon le mécanisme exact demandé par le client à l'origine.
- 08/07/2026 — État de connexion réel constaté sur le compte de test : Christophe
  Hoffstetter est en 2e degré (pas de bouton "Se connecter" direct sur son profil, option
  disponible uniquement sous le menu "..."), Henri-Pierre Michaud est en revanche **déjà
  connecté en 1er degré** — l'hypothèse initiale du ticket (aucun des deux connecté)
  était donc partiellement fausse. Pour lui, l'invitation n'a pas de sens (LinkedIn
  n'autorise pas d'inviter quelqu'un déjà dans son réseau) : traité comme un 3e statut
  explicite `already_connected` (ni succès, ni échec technique) plutôt que forcé ou
  ignoré silencieusement.
- 08/07/2026 — **Périmètre étendu de 2 à 3 URLs en liste blanche**, décision utilisateur :
  ajout de `linkedin.com/in/wanda-kleck-76ba342b8` (Wanda Kleck, fille de l'utilisateur,
  compte LinkedIn tout juste créé, pas encore connectée) — toujours interne/consentant,
  mais hors du périmètre initial (2 contacts professionnels internes). Volume révisé en
  conséquence : 3 tentatives d'invitation au total (dont 1 sans effet réel pour
  Henri-Pierre), toujours en exécution manuelle unique.
- 08/07/2026 — Notes d'invitation statiques validées par l'utilisateur : `"hello ici beau
  temps et mer calme"` (Christophe), `"hello Wanda, on arrive..."` (Wanda). Aucune note
  envoyée pour Henri-Pierre (statut `already_connected`, note sans objet).
- 08/07/2026 — **Contrainte découverte en cours de test, à respecter pour tout futur
  usage de ce mécanisme** : un compte LinkedIn gratuit est limité à **3 invitations
  personnalisées (avec note) par mois**. Ce ticket, avec 2 notes réellement envoyées
  (Christophe, Wanda), consomme déjà 2 des 3 disponibles pour le mois en cours sur le
  compte de test — à surveiller si une extension future de ce mécanisme est envisagée
  (ex. Phase 3 contact semi-automatisé), le quota redevient vite bloquant à un volume
  réaliste de prospection.
- 08/07/2026 — Sélecteurs identifiés via inspection DOM en direct (menu manuel du
  navigateur + un dump HTML ponctuel), même méthode que POC-001/POC-002 : bouton "..."
  du profil repéré par `aria-label="Plus"` (stable, contrairement à son icône SVG) ;
  item "Se connecter" du menu déroulant matché par texte (`<p>`, distinct des liens
  "Se connecter" du carrousel "Autres profils consultés" qui utilisent un `<span>`) ;
  boutons "Ajouter une note"/"Envoyer" de la fenêtre de note construits avec les classes
  standard du design system Artdeco de LinkedIn (`artdeco-button__text`, non hashées),
  matchés par texte ; zone de texte de la note avec un id stable et sémantique
  (`#custom-message`, non hashé) — plus fiable que les sélecteurs de la page de
  recherche/profil déjà en place.
- 08/07/2026 — **Correctif après mise en oeuvre réelle** : la fenêtre "Ajouter une note à
  votre invitation ?" s'est révélée être un composant distinct du reste de la page (carte
  arrondie, bouton "Ignorer" séparé), absent de tout dump HTML (`page.content()`) et de
  toute requête XPath malgré un rendu visuel confirmé à l'écran — cohérent avec un
  composant en Shadow DOM (XPath natif ne le traverse pas, contrairement au moteur de
  sélection CSS de Playwright). Les boutons "Ajouter une note"/"Envoyer" de cette fenêtre
  ont finalement été matchés par sous-chaîne (`:has-text()`) plutôt que par égalité
  exacte de texte, cette dernière échouant silencieusement en direct (probablement un
  noeud d'accessibilité caché dans le bouton). Un clic sur le menu déroulant "Se
  connecter" a aussi dû être retardé de 800ms après ouverture du menu "..." : cliqué trop
  vite après ouverture, il était accepté visuellement (encadré de focus) mais n'ouvrait
  pas la fenêtre suivante — hypothèse d'une garde anti-rebond du composant de menu.
- 08/07/2026 — **Run réel exécuté** : Henri-Pierre → statut `already_connected` confirmé
  (pas d'option "Se connecter" disponible, cohérent avec son 1er degré). Christophe →
  invitation avec note envoyée et **confirmée réellement reçue** par deux signaux
  indépendants (liste "Envoyées" du compte de test + statut "En attente" sur son propre
  profil, vérifiés par l'utilisateur). Wanda → le script a rapporté `sent`, mais
  vérification faite sur son profil : le bouton "Se connecter" y est resté actif,
  **l'invitation n'a en réalité jamais été reçue**. Décision utilisateur : pas de
  nouvelle tentative (risque de quota/blocage), le ticket s'arrête sur ce résultat mixte.
- 08/07/2026 — **Limite découverte, documentée dans le code** (`internal_invite_test.py`) :
  le statut `sent` ne garantit pas que LinkedIn a traité l'invitation côté serveur — il
  signifie seulement que le clic sur "Envoyer" n'a pas levé d'erreur côté script. Le cas
  Wanda le prouve (statut `sent` rapporté, invitation jamais reçue en réalité, aucune
  capture de diagnostic disponible puisque considérée comme un succès). Toute réutilisation
  future de ce mécanisme devrait ajouter une vérification post-envoi (ex. présence d'un
  toast de confirmation, ou re-vérification de l'état "En attente") avant de faire
  confiance au statut `sent`.
- 08/07/2026 — **Quota LinkedIn réellement consommé : 1 invitation personnalisée sur 3
  ce mois-ci** (Christophe uniquement — Wanda n'ayant jamais été réellement envoyée), et
  non 2 comme anticipé plus haut avant l'exécution réelle.
- 08/07/2026 — **POC-005 clos** : faisabilité technique validée (mécanisme d'invitation
  avec note fonctionnel via Playwright, liste blanche vérifiée par test unitaire dédié,
  statut `already_connected` distinct d'un échec technique), avec deux réserves
  documentées : (1) résultat mixte sur les 3 profils testés (1 envoi réel confirmé, 1 déjà
  connecté sans objet, 1 échec réel malgré un statut `sent` erroné), et (2) la fiabilité du
  statut `sent` lui-même, à améliorer avant toute réutilisation au-delà d'un test de
  faisabilité. Aucun blocage/restriction du compte LinkedIn constaté.
