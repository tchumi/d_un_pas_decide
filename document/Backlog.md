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
- 08/07/2026 — **Position acceptée par le client** (mail Christophe Hoffstetter du 08/07/2026, 12:54 : « Ok pour Email et invitations automatiques »), en réponse à l'argumentaire envoyé le 07/07 (risque de restriction de compte sur un rythme d'envoi non humain, contact supervisé renvoyé à la Phase 3, automatisation par email à étudier une fois le scoring validé). Ce point n'est donc plus une réponse à formuler : il est clos côté business. Reste hors scope de développement, inchangé.
- 07/07/2026 — Volume de test limité à 5 profils (`MAX_PROFILES=5` dans `run_poc002.py`, script dédié distinct de `run_poc001.py`), par prudence : une requête supplémentaire par profil (visite de page individuelle) augmente le risque de blocage/restriction de compte par rapport à la simple recherche de POC-001.
- 07/07/2026 — Sélecteurs de la page profil corrigés après diagnostic sur DOM réel (même méthode que POC-001) : le lien "Coordonnées" n'a ni id ni data-testid et son href pointe vers l'URL du profil suivie de `#` (pas de route overlay dédiée comme supposé initialement) — matché par son texte visible à la place (dépendance à la langue du compte, comme l'ancien bouton de pagination POC-001). La fenêtre qui s'ouvre est en revanche un vrai `<dialog data-testid="dialog">`, et l'email y est un lien `mailto:` standard — ces deux derniers points sont stables et vérifiés.
- 07/07/2026 — **Run réel validé** sur le lot de 5 profils (recherche + visite individuelle) : la fenêtre "Coordonnées" s'ouvre correctement pour chacun des 5, aucun blocage/restriction de compte constaté, export CSV étendu avec la colonne `email`. **Aucun des 5 profils testés n'affichait son email publiquement** (champ vide pour les 5) — comportement LinkedIn attendu : par défaut, seul le propriétaire du profil voit son propre email dans "Coordonnées", les autres profils ne l'exposent que s'ils l'ont explicitement rendu visible, ce que peu de comptes font. Le mécanisme d'extraction lui-même a été vérifié structurellement valide (même structure de fenêtre/lien `mailto:` confirmée sur le propre profil de l'utilisateur), mais l'extraction positive d'un email tiers n'a pas été observée sur ce lot précis — [Inférence] probabilité faible mais non nulle qu'un profil avec email public déclenche un cas non testé. **POC-002 clos (DONE)**, avec cette réserve documentée.
- 07/07/2026 — Le taux de 0/5 email public observé renforce la pertinence de la demande client du 04/07/2026 sur un "autre moyen de contact direct" (voir ci-dessus) — reste une décision business ouverte, à trancher avant un éventuel ticket dédié.
- 07/07/2026 — `MAX_PROFILES` remonté à 25 dans `run_poc002.py` (même progression que POC-001) après validation du run à 5 profils sans blocage. **Run réel confirmé sur 25 profils** : recherche + visite individuelle des 25 pages profil, aucun blocage/restriction de compte constaté, export CSV complet (25 lignes + en-tête) avec la colonne `email`. **0 profil sur 25 n'affichait son email publiquement** (vérifié visuellement par l'utilisateur pendant l'exécution, en plus du CSV) — confirme sur un échantillon plus large le constat du lot de 5 : l'email de contact n'est quasiment jamais rendu visible publiquement par les profils tiers sur LinkedIn. Le mécanisme d'extraction reste validé structurellement (voir plus haut) mais n'a été déclenché positivement sur aucun profil réel à ce stade, sur 30 profils testés au total (5 + 25).

---

## POC-003 — Scoring et catégorisation des profils (Phase 2)

**Objectif** : Catégoriser chaque profil extrait dans une des 3 classes cibles (coach
business débutant, expérimenté, outdoor/nature — indifférencié par défaut) et lui
attribuer un score de pertinence. **Cadré et réalisé le 26/08/2026** en périmètre réduit
(voir « Specs définitives » en fin de section) : la distinction débutant/expérimenté est
restée hors scope, ces profils sortent en catégorie indifférenciée.

**Exemples de calibration reçus du client** (Christophe Hoffsteter, 04/07/2026, sur le
CSV de démo POC-001) :
- Anne-Laure F., "Coach en développement personnel, professionnel et scolaire certifiée
  par Coaching Ways France Level 2 ICF (RNCP niveau 6)" → catégorie indifférenciée
  acceptable mais moins intéressante (mélange avec développement personnel/scolaire).
- Cécile Pollin, "HR Senior Manager - Responsable RH Senior - Transformation" → à
  exclure, pas un coach du tout (faux positif de la recherche booléenne).

**Complément de calibration reçu le 08/07/2026** (mail Christophe Hoffstetter, 12:54) :
- **Le reste du CSV de démo est validé en bloc** : « tous les profils dans le CSV sont de
  "bons" coach business ». Les 25 profils du lot POC-001 constituent donc de fait un lot
  d'exemples positifs, moins Cécile Pollin (exclue) et Anne-Laure F. (acceptable mais
  moins intéressante).
- **Mots-clés de la catégorie outdoor** (aucun profil exemple disponible, mais
  vocabulaire fourni) : *coach nature*, *coach qui marche*, *coach outdoor*, *coach
  hors-les-murs*, *coaching en itinérance*.
- **Distinction débutant / expérimenté impossible sur les données actuelles** : « les
  exemples de ton fichier CSV ne permettent pas de faire la différence entre Business
  Coach débutant et Business Coach expérimenté. Il manque la durée qui doit apparaître
  dans leur CV / parcours mais je ne sais pas si tu as accès à celui-ci. » Le titre
  LinkedIn seul (unique champ textuel extrait à ce stade) ne porte pas l'ancienneté.

**Décisions** :
- 04/07/2026 — Toujours en attente des 5-10 exemples de "bons" profils et 2-3 "mauvais"
  demandés initialement au client (2 reçus sur le total attendu) — bloquant pour cadrer
  le scoring/la catégorisation en détail. Statut `BLOCKED` dans `task_list.md` en
  attendant ce complément.
- 08/07/2026 — **Blocage requalifié, pas levé intégralement** (report fait le 25/08/2026
  à la relecture du mail du 08/07, resté non consigné jusque-là) : la calibration binaire
  bon/mauvais est en réalité couverte (validation en bloc du CSV ci-dessus + 1 exclusion
  explicite), et la catégorie outdoor dispose de son vocabulaire. Ce qui manque
  réellement se réduit à **la granularité débutant / expérimenté**, elle-même
  conditionnée par deux points ouverts : (1) extraire ou non la durée d'expérience depuis
  la section parcours de la page profil — techniquement à portée puisque POC-002 visite
  déjà chaque page individuelle, donc sans requête supplémentaire, mais hors périmètre de
  l'extraction actuelle (titre + localisation) ; (2) une réponse d'Henri-Pierre Michaud,
  sollicité nommément dans le même mail (« Henri-Pierre, tu arrives à être plus fin que
  cela pour un scoring plus nuancé ? »), toujours sans réponse à ce jour.
- 08/07/2026 — [Inférence] Un POC-003 en périmètre réduit est donc cadrable sans attendre
  ces deux points : exclusion des non-coachs, détection de la catégorie outdoor par
  mots-clés, score de pertinence — en laissant **débutant/expérimenté indifférencié**,
  ce qui correspond exactement au repli annoncé par le client le 04/07 (« par défaut
  Coach business indifférencié »). L'ajout de l'ancienneté resterait un incrément
  ultérieur, une fois la source de la durée tranchée.
- 13/07/2026 — **Priorité client explicite sur ce ticket** (mail Christophe Hoffstetter
  du 13/07/2026, 09:12) : « ne pas s'acharner sur ce point [l'enrichissement web] et
  mettre l'énergie sur la catégorisation/le scoring des profils, qui apporte plus de
  valeur immédiate ». POC-003 devient le prochain ticket prioritaire (voir décisions
  POC-004 du 13/07 pour l'arbitrage complet). Statut passé de `BLOCKED` à `TODO` dans
  `task_list.md`.

### Specs définitives (cadrage et réalisation du 26/08/2026)

**Entrée** : `profils_extraits.csv` (25 profils, lot POC-001, gitignoré). **Aucune nouvelle
extraction LinkedIn, aucun appel LLM, aucune nouvelle dépendance.** Le `titre` LinkedIn est
le seul signal textuel exploitable.

**Choix d'architecture** : moteur de règles 100 % déterministe. Justification : le client
demande une colonne `justification` à côté du score (demande du 04/07/2026) ; un moteur de
règles la produit par construction et elle est vérifiable, un LLM la génère sans qu'elle le
soit. Cohérent avec POC-004 (pipeline v1 déterministe, paliers LLM non activés).

**Règles de scoring**, échelle 0–100, encodées dans `config/scoring_rules.json` :

| Règle | Type | Poids | Déclencheur |
|---|---|---|---|
| `exclusion_non_coach` | exclusion (absence) | → exclu, score 0 | aucune occurrence de `coach` |
| `exclusion_hors_metier` | exclusion (présence) | → exclu, score 0 | `coach de vie`, `life coach` |
| `base_coach` | bonus | +20 | marqueur `coach` présent |
| `focus_business` | bonus | +40 | `coach business`, `business coach`, `coach d'entreprise`, `coach en entreprise`, `coach professionnel`, `coaching professionnel`, `executive coach`, `coach de dirigeant`, `coach d'équipe` |
| `certification` | bonus | +15 | `icf`, `rncp`, `certifi`, `accredit`, `level 2`, `pcc`, `mcc` |
| `cible_business` | bonus | +10 | `dirigeant`, `entrepreneur`, `manager`, `management`, `leadership`, `executive`, `business`, `entreprise`, `équipe`, `commercial` |
| `hors_cible` | malus | −25 | `développement personnel`, `scolaire` (malus **sans** exclusion) |

**Règle d'agrégation, déclarée explicitement dans le JSON** (bloc `agregation`, lu et
validé par le moteur, pas un commentaire décoratif) : le score est la **somme algébrique**
des poids des règles déclenchées — un bonus a un poids positif (additionné), un malus un
poids négatif (soustrait) ; l'ordre est sans importance ; le total est borné dans
`[score_min, score_max]`. Le drapeau `regle_appliquee_une_seule_fois` (à `true`) fait
qu'une règle compte **au plus une fois**, quel que soit le nombre de mots-clés trouvés ; à
`false`, son poids est compté une fois par mot-clé. Une règle d'exclusion court-circuite
tout le calcul. Un `mode` autre que `"somme"` est **refusé au chargement** (`ValueError`)
plutôt qu'ignoré silencieusement.

**Catégories** : `exclu` / `coach_outdoor` (les 5 mots-clés fournis par le client le
08/07/2026) / `coach_business_indifferencie` (défaut). La catégorie outdoor est
**score-neutre** : le client n'a jamais indiqué qu'un profil outdoor valait plus ou moins.

**Sortie** : `profils_extraits_scores.csv` (gitignoré), trié par score décroissant, avec
4 nouvelles colonnes dans `csv_export.py` (`restval=""`, même pattern que `email` en
POC-002) : `categorie`, `score`, `justification`, et **`commentaire_client`** — colonne
exportée vide, destinée au retour du client sur la pertinence du critère/du score
(demande utilisateur du 26/08/2026). Le scoring **n'écrase jamais** un `commentaire_client`
déjà rempli si on rejoue le calcul sur un CSV annoté.

**Profils exclus conservés dans le CSV** (`categorie=exclu`, `score=0`) plutôt que
supprimés : l'exclusion reste auditable par le client.

### Critères d'acceptation — vérifiés sur les 25 profils réels le 26/08/2026

Run réel : **24 conservés, 1 exclu, médiane des conservés = 75**, 21 profils au-dessus du
seuil « intéressant ».

1. **Cécile Pollin exclue** — `exclu`, score 0, justification « aucun marqueur 'coach' dans
   le titre ».
2. **Anne-Laure F. conservée sous la médiane** — score **10** contre une médiane de **75**,
   dernière du classement.
3. **Les 23 autres profils conservés** — distribution : 85 ×9, 75 ×5, 70 ×5, 60 ×2, 45, 20.
4. Colonnes `categorie` / `score` / `justification` renseignées pour les 25 profils.
5. Tests unitaires : **67 passants**, sans navigateur ni appel réseau.

Obtenu **sans aucune règle ad hoc nommant un profil** : les 6 règles sont génériques.

### Relecture du classement avec l'utilisateur (26/08/2026) — validée

Trois arbitrages signalés et **validés en l'état** :

- **Gabriel Abadie, score 45** (« PNC 25 ans Air France | Coach certifié RNCP 7 | Projet :
  formateur soft skills ») : aucune formule « coach professionnel/business » dans le titre,
  donc pas de `focus_business`. Passe **sous le seuil de 60** → hors sélection POC-004. Coach
  en reconversion, score bas jugé cohérent.
- **Manuel BOSSU, score 20** (« Coach d'intégration professionnelle ») : coaching
  d'insertion/langue, pas business. Score bas cohérent, mais à noter — c'est **le seul vrai
  positif confirmé du run POC-004** (site + email personnels trouvés). Il sortirait donc de
  la sélection conditionnelle.
- **Jérémy Azoulay et Elsa Dogliotti, score 60** : pile au seuil, donc **dans** la
  sélection. Un seuil à 65 les en sortirait.

**Aucun profil outdoor dans le lot** : la catégorie et ses 5 mots-clés sont couverts par des
tests unitaires mais **jamais observés sur données réelles**.

### Décisions (26/08/2026)

- **Seuil « profil intéressant » = 60**, valeur de départ assumée, stockée dans le JSON et
  surchargeable par argument. **À exposer dans un menu configuration** en version production
  (à prévoir, hors périmètre de ce ticket — `source/frontend_streamlit/` n'existe pas encore).
- **Règles encodées en JSON éditable** (`config/scoring_rules.json`) avec `charger_regles()` /
  `sauvegarder_regles()` côté `core/` : l'**édition et la sauvegarde des règles depuis le menu
  configuration** sont à prévoir. L'aller-retour charger/sauvegarder est testé.
- **`coach de vie` / `life coach` → exclusion** (et non malus), sur décision utilisateur.
  Aucun profil du lot n'est concerné, le critère d'acceptation n'en dépend donc pas. Risque
  documenté : un titre mixte (« business coach et life coach ») serait exclu à tort ; repasser
  en malus = déplacer la règle dans le JSON.
- **Pas de malus sur « coach professionnel en formation »** (Séverine GRAVOT, Jérémy Azoulay) :
  le client a validé ces profils en bloc le 08/07/2026.
- **Débutant / expérimenté toujours hors scope** : non décidable depuis le titre, nécessiterait
  d'extraire la durée d'expérience de la page profil, et attend une réponse d'Henri-Pierre
  Michaud. Repli en `coach_business_indifferencie`, conforme à l'annonce client du 04/07/2026.

### Point d'architecture intégré (POC-004 conditionnel)

Décision client du 13/07/2026 : l'enrichissement web cesse d'être une étape systématique et
devient **conditionnelle, appliquée après le scoring** aux seuls profils intéressants. Le
module expose `selectionner_profils_interessants(profils, seuil=None)`, qui est ce point de
sélection. **POC-004 n'a pas été modifié dans ce ticket** ; le branchement effectif des deux
étapes reste à faire dans un ticket ultérieur.

### Risque assumé — à revalider

Les règles sont calibrées sur les 25 profils qui servent **aussi** de jeu de référence : c'est
du sur-mesure sur un échantillon minuscule, et ça ne se corrige pas par de la technique.
Mitigation retenue : 6 règles seulement, aucune ne nommant un profil ou un cas particulier,
toutes lisibles et éditables depuis le JSON. **La revalidation devra se faire sur un lot
fraîchement extrait** — ce que POC-006 (renouvellement du gisement) rendra possible.

### Questions ouvertes à poser au client à la reprise de contact

Le CSV scoré sert de support à la reprise de contact (silence client depuis le 13/07/2026) :

1. La nuance **débutant / expérimenté** — question adressée nommément à Henri-Pierre Michaud
   le 08/07/2026, toujours sans réponse.
2. L'arbitrage sur l'**extraction de la durée d'expérience** depuis la page profil (à portée
   technique puisque POC-002 visite déjà chaque page, mais hors périmètre d'extraction actuel).
3. **Validation du seuil à 60** et des trois arbitrages de classement relevés ci-dessus.

**Quatre questions ajoutées le 27/08/2026 par POC-007** (anomalies A → D de la section
POC-007, relevées sur le lot frais ; décision utilisateur de **ne rien modifier avant retour
client**, ces points ne sont donc pas des bugs ouverts mais des arbitrages métier en attente) :

4. **`coach de vie` / `life coach` doit-il rester une exclusion ?** La règle n'a jamais été
   observée positivement (0/75), et un cas réel montre qu'elle est fragile dans les deux sens :
   « Certified Life & Business Coach » n'est **pas** exclu (score 85) parce que l'esperluette
   sépare les deux mots. Le client veut-il exclure ce profil, ou le conserver ?
5. **Un coach professionnel certifié ICF qui fait aussi du coaching scolaire est-il hors
   cible ?** Le malus `scolaire` (−25) fait passer Marc Michaud et Stéphanie GOYON de 75 à 50,
   donc sous le seuil, alors que leur ancrage business est explicite dans le titre.
6. **Un profil qui n'exerce pas le coaching à titre principal compte-t-il ?** Au seuil de 60
   entrent Christine Fabayre (retraitée, animatrice d'ateliers philo pour enfants, bénévole)
   et Vincent LEROUX (directeur d'agence plomberie, coach en second métier).
7. **Le pouvoir discriminant du score suffit-il au client ?** 48 % du lot frais est à
   **75 pile** : le score trie bien le pertinent du non-pertinent, mais ne hiérarchise plus
   à l'intérieur du pertinent. Faut-il un critère de départage supplémentaire, ou une simple
   liste non ordonnée suffit-elle à son usage ?

### Call client du 04/09/2026 — le silence est rompu, les questions sont dépassées

**Le silence client, ouvert le 13/07/2026, a pris fin le 04/09/2026** par un call de suivi
réunissant Michel Kleck, Henri-Pierre et Christophe (CR dans `document/compte_rendu/`,
« 2026 09 04 - CR call.pdf »). Le brouillon de reprise de contact du 28/08/2026 est donc
**caduc** : il n'a pas été envoyé et n'a plus d'objet.

**Effet sur les sept questions ci-dessus** : elles n'ont **pas** été posées telles quelles. Le
call a porté sur l'usage de l'outil, pas sur le détail des règles, et Christophe a tranché en
pratique plutôt qu'en théorie — *« même sans scoring sophistiqué, la simple constitution d'un
tableau Excel avec des colonnes exploitables représente déjà une avancée considérable »*. Cela
répond en creux à la question 7 : **le pouvoir discriminant du score n'est pas un sujet pour le
client à ce stade**, il veut trier et filtrer lui-même dans Excel. Les questions 1 à 6 restent
ouvertes mais **descendent en priorité** : le retour d'usage promis (point d'action n°5) est le
chemin par lequel elles seront tranchées, sur pièces plutôt que dans l'abstrait.

**Huitième question, ajoutée par POC-009** (qui valide les coordonnées, nous ou le client) :
également non posée, et en partie répondue par le dispositif convenu — le client annote le
fichier, nous le réinjectons.

**Décisions et engagements pris au call** :

1. **Livrable attendu — un tableau Excel de plus d'une dizaine de profils**, colonnes de scoring
   et colonne `commentaire_client`, **pour la fin de la semaine du 08/09/2026**. C'est le seul
   engagement daté du projet. Il a ouvert **POC-013**.
2. **La boucle de retour est confirmée comme le mécanisme central** : Michel envoie le tableau,
   Christophe et Henri-Pierre le manipulent dans Excel (tri, filtres) et documentent la colonne
   `commentaire_client`, Michel réinjecte manuellement en base. Christophe a relevé le caractère
   fastidieux de la réinjection ; réponse retenue : c'est la seule solution viable pour démarrer,
   en attendant une automatisation ultérieure.
3. **Le ciblage géographique devient l'axe stratégique n°1.** Christophe a insisté sur les
   Vosges (Remiremont) et le Grand Est, en citant Bordeaux comme contre-exemple non pertinent :
   l'enjeu est de réunir un quota de participants suffisant pour lancer un bootcamp sur une zone
   donnée. Michel a confirmé que c'est un point essentiel de l'outil. **Cela mandate POC-008**
   (points d'action 2 et 4).
4. **Multiplication de requêtes ciblées plutôt qu'une requête générique unique** — proposition de
   Christophe (« Coach business » + géographie, « Executive coaching », etc.), complétée par
   Michel sur la distinction entre types de coachs et l'exclusion de « coach sportif ».
   Christophe et Henri-Pierre doivent fournir un **brainstorming de requêtes** (point d'action
   n°3) : **dépendance externe** à leur charge.
5. **Approche pragmatique et itérative validée** : d'abord un scrapping fonctionnel qui alimente
   l'Excel, l'amélioration ensuite. Christophe a explicitement écarté toute pression de rythme
   (« ton rythme sera le bon »).
6. **Sales Navigator** — mis en veille. Michel ne souhaite pas s'y investir à ce stade ;
   Christophe et Henri-Pierre peuvent l'explorer de leur côté.
7. **Passage du scrapping sur serveur** — reporté. Obstacle identifié : la session LinkedIn doit
   être locale, une origine « serveur » exposerait le compte à un blocage immédiat.

**Deux imprécisions du CR, relevées et sans conséquence** (le CR est une synthèse de réunion,
pas une spécification) :

- Le scoring y est résumé en « +10 si le mot-clé est présent, −10 s'il est absent ». [Code] Le
  moteur réel est une somme algébrique bornée de 6 règles pondérées déclarées dans
  `config/scoring_rules.json`.
- Le CR rapporte « 90 % des mêmes profils d'une semaine à l'autre ». C'est un constat antérieur
  à POC-006 : [Code, run réel du 26/08/2026] la déduplication persistante a produit deux lots
  **strictement disjoints**. La limite réelle n'est pas la redondance mais l'**épuisement du
  gisement** — page 8 sur ~10 atteinte sur la requête actuelle.

**Mesure faite le 08/09/2026 sur le magasin, à l'appui du point 3** — répartition géographique
des 81 profils, en lecture seule :

| Zone | Profils |
|---|---|
| **Grand Est** | **5** (Labry 85, Colmar 75, Saint-Avold 75, Strasbourg 70, Haguenau 45) |
| Île-de-France / Paris | 21 |
| Bordeaux | 2 |
| « France » sans précision | 6 |

**5 profils sur 81 dans la zone que le client dit prioritaire, dont 4 au-dessus du seuil**,
contre 21 en Île-de-France. C'est l'argument chiffré le plus direct en faveur de POC-008, et il
confirme le diagnostic déjà posé : [Code] `build_search_url` place `AND (France)` dans le seul
paramètre `keywords`, ce qui est une correspondance textuelle et non un filtre géographique.

### Retour client du 11/09/2026 — la grille de profilage et le premier jeu de référence

**Ce qui est arrivé** : réponse de Christophe (Henri-Pierre en copie) au mail de livraison de
POC-013, avec le classeur annoté (`document/compte_rendu/`, « 2026 09 11 - mail Christophe.pdf »
et `profils_magasin_2026_09_11.xlsx`). **81 commentaires sur 81**, aucune autre colonne modifiée,
en-tête intact : la boucle de retour de POC-013 a fonctionné sur un vrai retour, sans retouche.
**Ré-importé le 16/09/2026** dans le magasin — 81 cellules `commentaire_client` écrites, aucune
autre cellule modifiée, vérifié contre une sauvegarde prise avant.

**La grille de profilage du client** (texte du mail) :

| Verdict | Définition client | Profils |
|---|---|---|
| **Excellent profil** | Ancien dirigeant. Coach business qui travaille avec dirigeants et CODIRs, donc aussi pour des équipes | 6 |
| **Bon profil** | Carrière entreprise privée. Coach business qui travaille ou pas avec des équipes | 20 |
| **Mauvais profil** | Carrière fonction publique. Coach de vie ou multicarte ou autre type de coaching ou de métier | 46 |
| **Rien à voir** | Pas coach | 9 |

Cinq commentaires portent une justification libre : « numérologie », « consultant » (×2),
« coach interne », « service aux coachs ».

**Déclaration clé du mail** : *« Nous avons beaucoup utilisé, en plus du titre, les champs
"Expérience" et "Infos" qui sont très utiles pour le profilage. »* [Code] Le scoring ne lit que
le `titre` (`scorer_titre`). Deux des trois axes de la grille — ancien dirigeant, carrière
privée ou publique — relèvent du parcours, pas du titre.

**Mesures du 16/09/2026, score v1 contre verdict client** (lecture seule) :

| Score | Profils | Excellent | Bon | Mauvais | Rien à voir |
|---|---|---|---|---|---|
| 85 | 18 | 3 | 7 | 8 | 0 |
| 75 | 30 | 0 | 9 | 17 | 4 |
| 60–74 | 17 | 3 | 4 | 8 | 2 |
| < 60 | 16 | 0 | 0 | 13 | 3 |

- **Le seuil 60 ne rate aucun bon profil** : les 26 bons ou excellents sont tous à 60 ou plus.
  Comme filtre d'exclusion, le score fonctionne, et c'est vraisemblablement ce que Christophe
  appelle « pertinent ». **Monter le seuil serait une erreur** : à 75, 7 bons profils sortiraient,
  dont 3 des 6 excellents (scores 70, 70, 60).
- **Au-dessus du seuil, le score ne classe pas** : 26 bons sur 65 retenus (**précision 40 %**,
  pour un taux de base de 32 %). Au score maximal de 85, **8 mauvais pour 10 bons ou excellents**.
- **Pouvoir discriminant par règle** (part de bons ou excellents parmi les profils où la règle
  s'est déclenchée, pour un taux de base de 32 %) :

  | Règle | Déclenchée | Bons / excellents |
  |---|---|---|
  | `base_coach` (+20) | 78 | 33 % |
  | `certification` (+15) | 55 | **35 % — aucun signal** |
  | `focus_business` (+40) | 67 | 39 % — signal faible, pour le plus gros poids |
  | `cible_business` (+10) | 31 | **45 % — seul bonus qui discrimine**, pour le plus petit poids |
  | `exclusion_non_coach` | 3 | 0 % — juste |
  | `hors_cible` (malus) | 4 | 0 % — juste |

  Les exclusions et le malus ne se sont jamais trompés ; les bonus sont **pondérés à l'envers de
  leur pouvoir discriminant**. La certification Coaching Ways, omniprésente dans le lot d'août,
  n'est pas une règle en soi : elle déclenche `focus_business` (« coach professionnel ») **et**
  `certification`, d'où le bloc de profils à 75.
- **Ce que disent les titres des 6 excellents** : Directeur (monde industriel), Directeur associé,
  Co-fondateur, VP Human Resources, Executive Coach, « je coache les dirigeants ». [Inférence] Le
  critère « ancien dirigeant » est **partiellement** visible dans le titre quand la personne
  l'affiche ; il ne l'est pas quand elle ne le fait pas, d'où le besoin des rubriques
  « Expérience » et « Infos ».
- **« Consultant » n'est pas un critère d'exclusion en soi** : cité comme motif pour 2 mauvais
  profils, il apparaît aussi dans le titre d'un excellent (Eric Fritsch). Le client vise le
  **multicarte**, pas le mot.

**Questions ouvertes tranchées par ce retour** :

- **Q4 (`life coach`)** : Elise Rousseau, « Certified Life & Business Coach », jugée **mauvais
  profil**. L'exclusion aurait dû la capter : l'anomalie A était bien un raté.
- **Q5 (malus `scolaire`)** : Marc Michaud et Stéphanie GOYON jugés **mauvais profil**. Le malus
  était juste ; l'inquiétude de l'anomalie C n'était pas fondée.
- **Q6 (coaching en second métier)** : Christine Fabayre **rien à voir**, Vincent LEROUX **mauvais
  profil**. Ils doivent sortir de la sélection (anomalie D confirmée).
- **Q7 (pouvoir discriminant)** : répondue par la grille elle-même — le client veut **4 niveaux**.
- **5ᵉ anomalie (Manon Dumartin, score 0 mais conservée)** : **mauvais profil**, confirmée.
- **Q1 (débutant / expérimenté)** : répondue de biais — le critère n'est pas l'ancienneté dans le
  coaching mais **la carrière d'avant** (ancien dirigeant, privé contre public).
- **Seuil 60 (Q3)** : non discuté par le client, mais **validé par la mesure** — zéro faux négatif.

**Deux faits annexes** :

- **Les coordonnées ont été cherchées pour les mauvais profils** : sur les 7 profils à
  `statut_coordonnees = valide`, **5 sont jugés mauvais** (Elise Rousseau, Emmanuel Poilane,
  Julie Leger, Sylvie DUCHENE, Manuel BOSSU). La recherche web s'enclenche au seuil 60, qui ne
  classe pas (voir POC-017).
- **Suggestion du client** : *« une nouvelle colonne numéro de département ou nom du département
  serait la bienvenue »* (voir POC-015).

**Décisions** :
- 11/09/2026 — Grille de profilage à 4 niveaux définie par le client.
- 11/09/2026 — **Géographie déclarée critère accessoire** par le client (voir POC-008).
- 16/09/2026 — Retour ré-importé dans le magasin, avant toute évolution des colonnes de l'export
  (sinon le contrôle d'en-tête de POC-013 aurait refusé le fichier).
- 16/09/2026 — Itération validée par l'utilisateur : POC-014 (scoring v2 sur le titre, mesuré
  contre la grille), POC-015 (colonne département), POC-016 (extraction « Expérience » et
  « Infos »), POC-017 (recherche de coordonnées déclenchée par le verdict).



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
- 10/07/2026 — **Implémentation et run réels effectués** (module
  `source/backend/adapters/enrichment/`). Deux bugs trouvés et corrigés en cours de test
  réel (même méthode que POC-001/002 : diagnostic sur cas réel, pas de correction
  silencieuse) :
  1. L'API Brave Search rejette les requêtes de plus de 50 mots (HTTP 422) ; les titres
     LinkedIn peuvent être une bio complète (69 mots observés sur un profil réel) →
     `build_search_query` tronque désormais le titre en priorité (nom + localisation
     conservés intégralement, décision utilisateur du 10/07/2026).
  2. Le regex de validation d'email était trop permissif sur la partie finale (domaine),
     laissant passer un caractère résiduel (`\`) issu d'un contenu HTML/JS avec guillemet
     échappé (observé sur une page réelle) → TLD restreint à `[A-Za-z]{2,}`.
- 10/07/2026 — **Liste noire de domaines étendue à 4 domaines supplémentaires**
  (`noomii.com` — annuaire de coachs, `journaldunet.com` — héberge d'anciens profils
  Viadeo, `spotify.com`, `amazon.co.uk` — plateformes grand public), suite aux faux
  positifs confirmés sur le run réel de 25 profils ci-dessous.
- 10/07/2026 — **Run réel validé sur 25 profils** (CSV issu de POC-002,
  `MAX_PROFILES=25`) : 11/25 profils avec un candidat passant le filtre de domaines
  (avant extension de la liste noire ci-dessus), dont après relecture humaine :
  - **1 vrai positif confirmé** : Manuel BOSSU → `mycoachonline.fr` /
    `manuel@mycoachonline.fr` (site et email personnels confirmés par l'utilisateur).
  - **1 positif partiel** : Sylvie WEILER → `memepascap.fr` (site professionnel
    pertinent, mais email `bonjour@memepascap.fr` non personnel — adresse partagée
    d'un cabinet à plusieurs coachs, confirmé par l'utilisateur). Illustre une limite non
    anticipée : un site pertinent peut malgré tout ne pas donner un contact personnel.
  - **7 faux positifs confirmés**, désormais couverts par l'extension de liste noire
    ci-dessus (4 domaines) ou déjà écartés individuellement par relecture humaine :
    `intercariforef.org` (page de contact générique d'un organisme public, non
    nominative) et `je-change-de-metier.com` (site édité par une agence tierce, pas par
    le prospect lui-même).
  - **2 candidats non vérifiés individuellement** (`villepratique.fr`,
    `lafrenchcom.fr` — ce dernier avec un indice de non-pertinence, email `urgent@...`
    typique d'une adresse générique d'agence).
  - **14/25 sans aucun candidat retenu** après filtrage.
  - **Taux de pertinence observé : 1/25 (4%) exploitable tel quel, 2/25 (8%) en comptant
    le positif partiel.** Confirme concrètement le risque documenté ci-dessus (mauvais
    candidat retenu bien plus fréquent que le bon) : le filtrage de domaines élimine les
    catégories évidentes (réseaux sociaux, annuaires, plateformes) mais ne garantit
    aucunement la pertinence métier (homonymes, sites d'agences tierces, pages
    institutionnelles génériques, emails d'équipe non personnels) — la relecture humaine
    reste indispensable avant tout contact, exactement comme prévu.
  - **Élément à trancher pour la suite** (non décidé dans ce ticket) : ce taux de 4-8%
    est-il suffisant pour justifier de maintenir le v1 tel quel (avec relecture humaine
    systématique), ou justifie-t-il d'activer le Palier 1 (vérification/désambiguïsation
    par LLM) pour améliorer la précision avant relecture humaine ? Décision à prendre
    avec le client, pas unilatéralement par ce ticket.
- 10/07/2026 — **Critères d'acceptation du ticket tous remplis** : requête construite
  (nom + titre + localisation, tronquée si nécessaire), filtrage par liste noire,
  extraction regex email/site sur la page candidate restante, champs vides si rien de
  concluant, colonnes `email_web`/`site_web` ajoutées à l'export CSV, zéro appel LLM,
  clé lue depuis `.env.local` (jamais en dur), aucun scraping direct des pages de
  résultats de moteurs de recherche (uniquement l'API Brave).
- 13/07/2026 — **Élément à trancher ci-dessus : tranché par le client.** Point d'étape
  envoyé le 13/07 (08:34) présentant le résultat réel du run (1/25 exploitable, 1/25
  partiel) et trois pistes soumises à arbitrage : (A) ajouter une étape de vérification
  plus intelligente pour mieux trier les résultats — c'est le Palier 1 (LLM) ; (B) tester
  un service spécialisé payant type Kaspr, conçu pour retrouver un contact à partir d'un
  profil LinkedIn ; (C) ne pas s'acharner et réorienter l'effort vers la
  catégorisation/le scoring.
  **Réponse de Christophe Hoffstetter le 13/07 (09:12) : « ne pas s'acharner sur ce point
  et mettre l'énergie sur la catégorisation/le scoring des profils, voire permet de ne
  rechercher les coordonnées que pour les profils les plus "intéressants" ».** (Le mail
  écrit littéralement « j'opte pour l'option B » tout en explicitant la piste C ; la
  formulation explicite fait foi, elle est sans ambiguïté — à confirmer d'un mot si le
  sujet est rouvert.)
  Conséquences, à considérer comme actées :
  - **Palier 1 (LLM) non activé** et service payant type Kaspr non testé — ni l'un ni
    l'autre n'est planifié. La question posée le 10/07 est close.
  - **L'enrichissement web cesse d'être une étape systématique du pipeline** : il devient
    une étape **conditionnelle, appliquée après le scoring** aux seuls profils jugés
    intéressants. Le code de POC-004 reste en place et fonctionnel, sa position dans la
    chaîne change — à intégrer au cadrage de POC-003 plutôt qu'à retoucher maintenant.
  - **Le client accepte un repli manuel** pour les coordonnées : « au vu des volumes, une
    alternative manuelle à la recherche de coordonnées est envisageable voire utiliser
    "manuellement" la messagerie interne LinkedIn ». Le taux de 4-8 % n'est donc plus un
    problème à résoudre techniquement.
  - La demande client du 04/07 sur un « autre moyen de contact direct » (voir POC-002)
    est close par la même occasion : la réponse retenue est le traitement manuel à ce
    volume, pas un canal automatisé supplémentaire.

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

---

## POC-006 — Renouvellement du gisement de profils (mémoire des profils déjà vus)

**Objectif** : Faire en sorte que deux exécutions successives du pipeline ramènent des
profils **nouveaux** plutôt que le même lot, et rendre ainsi atteignable la cible client
de **50 profils/semaine** (mail Christophe Hoffstetter du 04/07/2026). Ticket créé en
stub le 26/08/2026 ; cadrage détaillé à faire au démarrage réel via `prompt_générique.md`.

**Constat à l'origine du ticket** (26/08/2026, vérifié dans le code) :

1. [Code] `search_and_extract` (`source/backend/adapters/scraping/profile_search.py`)
   repart systématiquement de la page 1 de la même URL de recherche et retient les
   `max_profiles` **premières** cartes dans l'ordre du DOM. La pagination
   (`go_to_next_page`) ne sert qu'à compléter le lot jusqu'à `max_profiles`, jamais à
   aller au-delà de ce qui a déjà été vu.
2. [Code] `export_profiles_to_csv` (`source/backend/adapters/storage/csv_export.py`)
   ouvre le fichier en mode `"w"` : chaque run **écrase** le précédent. Il n'existe
   aucune persistance, aucune déduplication, aucune notion de « profil déjà traité »
   dans le code.
3. [Inférence] Les deux défauts se composent : non seulement un second run ramène la même
   tête de liste, mais l'écrasement du CSV empêche de le constater. Le classement de
   recherche LinkedIn étant personnalisé et instable, le recouvrement réel est *partiel
   et imprévisible* — plus difficile à diagnostiquer qu'une duplication franche.
4. [Documentation] La cible client est de 50 profils/semaine ; le pipeline actuel plafonne
   à 25 profils toujours identiques. L'écart n'est pas un réglage de volume
   (`MAX_PROFILES`) mais un défaut de conception.

**Périmètre pressenti** :
- `source/backend/adapters/storage/` — magasin persistant des profils déjà extraits
  (SQLite, annoncé dans la stack `CLAUDE.md` mais jamais introduit : `storage/` ne
  contient à ce jour que l'export CSV).
- `source/backend/adapters/scraping/profile_search.py` — passer d'une boucle « les N
  premières cartes » à « les N cartes **inconnues** », en paginant tant que le quota de
  nouveaux profils n'est pas atteint.
- `source/backend/adapters/storage/csv_export.py` — l'export cesse d'être la source de
  vérité pour devenir une vue exportée du magasin.

**Clé de déduplication** : l'URL de profil, déjà normalisée par `clean_profile_url`
(suppression des query params et du fragment) — clé naturelle stable.

**Critères d'acceptation (définitifs, tous vérifiés le 26/08/2026)** :
- [x] Deux exécutions successives de la même requête booléenne produisent deux lots
      **disjoints** de profils (aucune URL commune), tant que le gisement de la requête
      n'est pas épuisé. → *Vérifié sur deux runs réels : 75 profils, 75 URLs distinctes.*
- [x] Quand le gisement est épuisé, le comportement est explicite (lot plus petit que
      demandé, message clair) plutôt qu'une boucle infinie ou un lot silencieusement
      incomplet. → *`ResultatRecherche.raison_arret` ∈ {`quota_atteint`,
      `gisement_epuise`, `plafond_pages`} + `message_arret`, couverts par tests.*
- [x] Aucun profil déjà collecté n'est perdu par un nouveau run (fin de l'écrasement).
      → *Le CSV est réécrit depuis le magasin complet ; `enregistrer_profils` ne remplace
      jamais un champ rempli par une valeur vide.*
- [x] Un CSV dont la colonne `commentaire_client` a été remplie par le client est
      ré-importé, et un nouveau run de scoring conserve ces commentaires — vérifié sur
      l'**aller-retour réel** (export → annotation → ré-import → run), pas sur un
      dictionnaire construit à la main. → *Vérifié en test unitaire **et** sur les
      données réelles des 25 profils.*
- [x] Logique de déduplication, de pagination et de ré-import testable **sans navigateur
      ni réseau**. → *`filtrer_profils_inconnus` et `collecter_profils_inconnus` sont
      pures (les deux accès au navigateur sont injectés) ; le magasin se teste sur une
      base `tmp_path`.*
- [x] Tests unitaires passants. → *102 passed, 0 failed, 0 skipped (67 avant le ticket).*

**Garde-fous RGPD — ce ticket solde une dette déjà inscrite au Backlog** :
La section POC-004 engage deux garde-fous qui sont **aujourd'hui structurellement
intenables** avec un CSV écrasé à chaque run, et que le magasin persistant rend
réalisables pour la première fois :
- **Conservation limitée** : champ `date_collecte` par profil, pour permettre une purge
  future — impossible tant qu'aucune date n'est conservée d'un run à l'autre.
- **Droit d'opposition** : pouvoir marquer un profil « à ne plus traiter » — inefficace
  si le marquage est effacé au run suivant. Ce marquage doit en outre **exclure le profil
  des collectes futures**, sans quoi il serait réextrait indéfiniment.
- **Minimisation** : le magasin ne stocke que les champs déjà justifiés par les tickets
  précédents ; ce ticket n'introduit aucune nouvelle catégorie de donnée personnelle.

**Piste complémentaire à cadrer avec (ou après) ce ticket — diversification des requêtes** :
La déduplication seule se heurte au plafond de la recherche LinkedIn pour un compte
gratuit ([Inférence] ~100 résultats / 10 pages par requête, plus le quota mensuel
« commercial use limit »). Elle donne quelques runs d'avance, pas un gisement infini.
Varier les requêtes attaque le problème par l'autre bout, chaque requête ayant sa propre
tête de liste :
- **Filtre géographique réel** : [Code] `build_search_url` place aujourd'hui toute la
  requête — y compris `AND (France)` — dans le seul paramètre `keywords`. Ce n'est donc
  **pas** un filtre géographique mais une correspondance textuelle. Passer par les
  facettes géographiques natives de LinkedIn serait à la fois plus précis et un axe de
  variation (par ville/région).
- **Vocabulaire outdoor non couvert** : les 5 mots-clés fournis par le client le
  08/07/2026 (*coach nature*, *coach qui marche*, *coach outdoor*, *coach hors-les-murs*,
  *coaching en itinérance*, voir section POC-003) n'apparaissent dans **aucune** requête
  actuelle — gisement inexploité, et précisément la catégorie que POC-003 apprend à
  reconnaître.
- **Synonymes et certifications** : « coach de dirigeants », « coach exécutif », ICF,
  RNCP, « business coach » (anglais).
- **Mesurer le plafond réel au lieu de l'estimer** (noté le 26/08/2026, à la suite d'une
  question de l'utilisateur sur le fonctionnement de la pagination LinkedIn) :
  [Documentation] LinkedIn affiche en bas de la page de résultats une barre de pagination
  numérotée dont le **dernier numéro est le nombre de pages réellement atteignables** — à
  ne pas confondre avec le compteur « Environ N résultats » du haut de page, qui compte
  les correspondances de la requête et non ce qu'un compte gratuit peut feuilleter (source
  de confusion courante : on lit quelques milliers de résultats, on pagine, et on bute sur
  un mur sans explication). [Code] Le scraping n'exploite aujourd'hui que le bouton
  « suivant » (`LinkedInSearchSelectors.NEXT_BUTTON`) : il *découvre* la fin du gisement
  (`raison_arret = "gisement_epuise"`) au lieu de la prévoir. [Inférence] Le nom du
  `data-testid` (`pagination-controls-next-button-visible`) suggère que les boutons
  numérotés appartiennent au même bloc DOM, donc qu'un sélecteur du dernier numéro serait
  à portée — **à vérifier sur un dump DOM réel** avant d'y compter, comme cela a été fait
  le 03/07/2026 pour les autres sélecteurs. Journaliser ce nombre à chaque run donnerait
  la **taille exacte du gisement par requête**, donc un dimensionnement chiffré de la
  diversification au lieu de l'estimation ~100 résultats / 10 pages. Volontairement **non
  fait dans POC-006**, qui n'en a pas besoin pour être complet.

**Hors périmètre de ce ticket** (notés pour mémoire, non planifiés) :
- Changer de porte d'entrée : profils « également consultés » (les pages profil sont déjà
  visitées par POC-002), commentateurs de publications du domaine, groupes LinkedIn de
  coachs. Meilleur rendement en pertinence, mais davantage de scraping par profil et
  d'exposition ToS — à traiter comme un ticket distinct s'il devient nécessaire.
- Exploiter le recouvrement comme signal de scoring (un profil ressortant sur plusieurs
  requêtes indépendantes est [Inférence] plus central dans le domaine) : quasi gratuit une
  fois le magasin en place, mais relève de POC-003, pas de ce ticket.

**Décisions** :
- 26/08/2026 — Ticket ouvert après un doute exprimé par l'utilisateur sur la pertinence de
  la méthode de recherche (« deux exécutions de la même requête booléenne ramènent
  probablement le même CSV »), vérifié et confirmé dans le code (voir constat ci-dessus).
- 26/08/2026 — **Ordre retenu : déduplication persistante d'abord, diversification des
  requêtes ensuite.** Sans mémoire des profils déjà vus, varier les requêtes ne ferait que
  produire des doublons non détectés — la piste de diversification n'a de valeur qu'une
  fois le magasin en place.
- 26/08/2026 — **À enchaîner après POC-003, pas en parallèle** : les deux tickets modifient
  `source/backend/adapters/storage/csv_export.py` (POC-003 y ajoute les colonnes de
  scoring, POC-006 en change le rôle). Travail concurrent = conflit assuré.
- 26/08/2026 — [Inférence] Ticket développable et testable **entièrement hors-ligne**
  (logique de persistance et de déduplication pure), sans session LinkedIn ni risque de
  restriction de compte. Seule la validation finale du renouvellement effectif du lot
  demandera un run réel.
- 26/08/2026 — **Périmètre étendu au ré-import du retour client**, après vérification du
  code à la relecture du prompt POC-006 :
  - [Code] POC-003 a implémenté la préservation de `commentaire_client` côté moteur
    (`scorer_profils` ne remplace jamais une valeur existante, test unitaire dédié).
  - [Code] Mais son unique appelant, `run_poc003.py`, lit `profils_extraits.csv` (CSV brut
    d'extraction, sans cette colonne) et écrit `profils_extraits_scores.csv` en mode `"w"` :
    le fichier annoté par le client n'est **jamais relu**, relancer le scoring écrase ses
    commentaires.
  - [Inférence] La protection est donc du code correct et testé mais **inatteignable en
    pratique** — le test la valide sur un dictionnaire construit à la main, jamais sur un
    aller-retour réel. La colonne `commentaire_client` reste décorative tant qu'aucun
    chemin de ré-import n'existe.
  - Décision : le ré-import entre dans POC-006 plutôt que dans un ticket séparé. Le magasin
    persistant est l'endroit où le retour client doit vivre, au même titre que
    `date_collecte` et le marquage « à ne plus traiter » — trois données qui ne survivent
    pas à un CSV écrasé ; les séparer reviendrait à construire deux fois le même mécanisme
    de persistance. Reste à trancher au cadrage : clé de réconciliation (a priori l'URL,
    même clé que la déduplication) et règle de conflit si un commentaire diffère des deux
    côtés.
- 26/08/2026 — **Emplacement de `run_poc003.py` conservé dans `adapters/storage/`**, après
  remise en cause puis vérification de la convention réelle : chaque script d'assemblage
  `run_pocNNN.py` vit auprès de l'adaptateur qui porte ses **entrées/sorties** —
  `run_poc001`/`run_poc002` dans `scraping/` (I/O Playwright), `run_poc004` dans
  `enrichment/` (I/O API Brave), `run_poc003` dans `storage/` (I/O CSV, seule I/O du
  scoring). Le placement est donc cohérent, pas accidentel. Aucun déplacement : ce serait
  du bruit juste avant que POC-006 ne remanie ce flux de données.

**Solution livrée (26/08/2026)** :
- `source/backend/adapters/storage/profile_store.py` — magasin SQLite (`profils.db`, déjà
  couvert par `.gitignore`), clé primaire = URL normalisée par `clean_profile_url`
  (importée depuis `profile_search`, jamais redupliquée : une seconde règle de
  normalisation aurait été le vrai défaut). Schéma en `PRAGMA user_version = 1`, créé et
  jamais migré. `enregistrer_profils` complète champ par champ via
  `COALESCE(NULLIF(...))` : une valeur entrante vide ne blanchit jamais une colonne
  remplie, et `date_collecte` est figée à la première insertion.
- `source/backend/adapters/scraping/profile_search.py` — `collecter_profils_inconnus` est
  une boucle **pure** à deux callables injectés (`extraire_page`, `page_suivante`) : toute
  la logique d'arrêt est testable sans navigateur. `search_and_extract` n'en est plus que
  la coquille Playwright et renvoie un `ResultatRecherche(profils, raison_arret,
  pages_visitees)`. Deux gardes rendent la boucle infinie impossible : absence de page
  suivante **et** plafond `MAX_PAGES = 10`.
- `source/backend/adapters/storage/run_poc006.py` — amorçage d'un magasin depuis un CSV
  existant et ré-import d'un CSV annoté par le même chemin de code, avec rapport détaillé.
- `run_poc001` exclut les URLs connues et réécrit le CSV depuis le magasin complet ;
  `run_poc003` lit et réécrit le magasin au lieu de `profils_extraits.csv`.

**Résultat des deux runs réels (26/08/2026)** :
- Magasin amorcé à 25 profils (lot de juillet ré-importé, daté du 03/07/2026 et non du
  jour — dater « aujourd'hui » un CSV antérieur aurait sous-estimé son ancienneté au
  regard de la règle de conservation).
- Run 1 : `25 profils deja connus` → **25 nouveaux collectés en 5 pages**.
- Run 2 : `50 profils deja connus` → **25 nouveaux collectés en 8 pages**.
- État final : **75 profils, 75 URLs distinctes**, 0 nom vide, 0 titre vide. Les trois
  lots sont deux à deux disjoints — critère d'acceptation 1 vérifié sur données réelles.
- Re-scoring des 25 profils de juillet depuis le magasin : **0 ligne de scoring modifiée**
  par rapport à l'export POC-003 (24 conservés, 1 exclu, 21 intéressants) — le changement
  de source de vérité n'a rien altéré.
- **Mesure du gisement** : ~10 profils par page, page 8 atteinte sur un plafond estimé à
  10 → [Inférence] il reste environ **un run d'avance** sur cette requête booléenne. C'est
  le chiffre qui justifie POC-008.

**Décisions complémentaires (26/08/2026, clôture)** :
- **Règle de conflit sur `commentaire_client`** (validée par l'utilisateur) : magasin vide
  + CSV rempli → écrit ; magasin rempli + CSV vide → **conservé** (un blanc n'efface
  jamais un retour client) ; les deux remplis et différents → **le CSV client prime**, et
  la substitution est **listée dans le rapport**, jamais appliquée silencieusement ; URL
  absente du magasin → non créée, comptée en « ignorées ». Clé de réconciliation : l'URL,
  même clé que la déduplication.
- **`date_collecte` et `ne_plus_traiter` sont des colonnes exportées** (décision
  utilisateur : visibles pour le client). Conséquence assumée : le ré-import lit aussi
  `ne_plus_traiter`, ce qui permet au client d'exprimer une opposition directement dans le
  CSV ; un `0` ou un blanc **ne lève jamais** un marquage existant.
- **`run_poc003` lit désormais le magasin** et non plus `profils_extraits.csv` : c'est ce
  qui rend le critère 4 atteignable. La protection de `scorer_profils` (POC-003) cesse
  d'être du code mort.
- **Le lot frais n'a volontairement pas été analysé dans ce ticket** : la revalidation des
  règles de scoring est l'objet de POC-007.
- **Renumérotation** : `document/prompts_plans/plan_POC-006.md` désigne la diversification
  des requêtes comme « POC-007 ». À la clôture, la revalidation des règles de scoring a
  pris ce numéro (elle est la raison d'être de l'enchaînement et le lot frais est
  disponible), et la diversification est devenue **POC-008**. Signalé ici plutôt que
  corrigé dans le plan, qui est un document daté.

---

## POC-007 — Revalidation des règles de scoring POC-003 sur le lot frais

**Objectif** : Statuer sur le sur-apprentissage des 6 règles de `config/scoring_rules.json`,
calibrées sur les 25 profils qui servaient aussi de jeu de référence, en les confrontant
aux **50 profils frais** extraits le 26/08/2026 par POC-006.

**Pourquoi maintenant** : [Documentation] C'est la réserve n°1 de POC-003, et la raison
d'être explicite de l'enchaînement POC-003 → POC-006. Le jeu de contrôle qui manquait
existe désormais : 50 profils jamais vus, **déjà scorés** dans le magasin.

### Résultats de l'analyse (27/08/2026) — revalidation concluante

**Aucune extraction, aucun re-scoring** : le lot était déjà scoré (vérifié dans `profils.db`,
75 profils porteurs d'un score, 25 datés du 03/07/2026 et 50 du 26/08/2026). *(Une version
antérieure de cette section annonçait `score = ''` et « scorer le lot frais » comme première
étape ; le prompt POC-007 avait été corrigé au commit `0b02bf8`, pas le Backlog.)*

**[Code] Comparaison des deux distributions** — juillet = lot de calibration, août = lot frais :

| | Juillet (n=25) | Août (n=50) |
|---|---|---|
| Exclus | 1 (4 %) | 2 (4 %) |
| Conservés | 24 | 48 |
| **Médiane des conservés** | **75** | **75** |
| Moyenne | 70,2 | 67,1 |
| Écart-type | 19,4 | 17,5 |
| Q1 / Q2 / Q3 | 70 / 75 / 85 | 60 / 75 / 75 |
| Min / Max | 10 / 85 | 20 / 85 |
| ≥ seuil 60 | 21/25 (84 %) | 39/50 (78 %) |

Distribution : juillet 85 ×9, 75 ×5, 70 ×5, 60 ×2, 45, 20, 10, 0 — août 85 ×7, **75 ×24**,
70 ×3, 60 ×5, 50 ×2, 45 ×2, 35, 30, 20 ×3, 0 ×2.

**Verdict : le sur-apprentissage n'est pas confirmé.** Médiane identique, taux d'exclusion
identique, dispersion comparable, moyenne en baisse de 3 points seulement. Une distribution
nettement plus basse sur le lot frais aurait signé le sur-apprentissage ; ce n'est pas ce
qu'on observe. **La réserve n°1 de POC-003 est levée** : les 6 règles tiennent sur 50 profils
qu'elles n'avaient jamais vus.

**[Code] Défaut découvert à la place, invisible en juillet : la perte de pouvoir
discriminant.** 24 profils sur 50 (48 % du lot frais) sont **exactement à 75**, et
Q2 = Q3 = 75 : le classement ne classe presque plus. Cause mesurée dans les justifications
stockées — taux de déclenchement par règle :

| Règle | Juillet | Août |
|---|---|---|
| `base_coach` +20 | 96 % | 96 % |
| `focus_business` +40 | 84 % | 82 % |
| `certification` +15 | 64 % | 72 % |
| `cible_business` +10 | **60 %** | **26 %** |
| `hors_cible` −25 | 4 % | 4 % |
| `exclusion_non_coach` | 4 % | 4 % |

C'est `cible_business` (+10) qui séparait 85 de 75 en juillet ; il ne se déclenche plus que
sur un quart du lot frais. Le lot d'août est un bloc homogène de « Coach professionnel
certifié par Coaching Ways France Level 2 ICF » → 20 + 40 + 15 = 75 pile. [Inférence] Ce
n'est pas un défaut de règle mais un effet de l'homogénéité de la requête : POC-008
(diversification) devrait faire remonter la variance, et c'est un argument de plus en sa
faveur.

**[Code] Deux règles jamais observées positivement sur données réelles, pas une seule** :
`coach_outdoor` → **0/75**, conforme à l'attendu (aucun mot-clé outdoor dans la requête) —
**non-observation, pas validation** ; et `exclusion_hors_metier` (`coach de vie` /
`life coach`) → **0/75** également. `developpement personnel` : 1/75 (Anne-Laure F., juillet).

### Quatre anomalies relevées à la relecture humaine (27/08/2026)

Trouvées sur profils réels nommés, **toutes laissées en l'état** (voir décision ci-dessous) :

- **A — Le risque « titre mixte » de POC-003 est désormais observé, et la règle n'a pas
  fonctionné.** [Code] Elise Rousseau, **score 85**, titre « Certified Life & Business
  Coach | Author | PhD Researcher… ». Vérifié en exécutant `normaliser` : le titre donne
  `certified life business coach`, où la sous-chaîne `life coach` **n'est pas présente** —
  l'esperluette a écarté les deux mots. Elle échappe à `exclusion_hors_metier` par accident
  d'ordre des mots, pas par décision. POC-003 avait documenté le risque inverse (« business
  coach et life coach » exclu à tort) ; la règle est en fait fragile **dans les deux sens**.
- **B — `mcc` capte `EMCC` : bonne réponse, mauvaise raison.** [Code] 4 profils d'août
  (Angélique LAUMOND, Sylvie DUCHENE, Emmanuel Poilane, Yannick GRANGIS). L'EMCC est bien un
  organisme d'accréditation, le +15 tombe donc sur les bons profils, mais par appariement de
  sous-chaîne (`mcc` ⊂ `emcc`), pas parce que le mot-clé aurait été prévu. Pour Angélique
  LAUMOND (35) c'est le **seul** déclencheur de `certification`. Le mot-clé `mcc` reste
  justifié en soi : Denise Sin Blima est une vraie MCC ICF.
- **C — Le malus `scolaire` (−25) sort deux coachs business avérés de la sélection.**
  [Code] Marc Michaud, 50 (« Coach professionnel certifié par Coaching Ways France, accrédité
  par ICF – Coach scolaire ») et Stéphanie GOYON, 50 (« Coach professionnel & scolaire
  certifié »). Même schéma qu'Anne-Laure F. en juillet, mais ici sur des profils dont
  l'ancrage business est explicite dans le titre.
- **D — Le seuil de 60 laisse entrer deux profils discutables.** [Code] 5 profils pile à 60
  en août (contre 2 en juillet), dont Christine Fabayre (« Retired From Industry – Animatrice
  Atelier Philo pour Enfants – Bénévole Association SEVE – Ile de France Coach Professionnel »)
  et Vincent LEROUX (« Directeur Agence Plomberie EQUANS… Coach professionnel »). Sensibilité
  mesurée du seuil : 60 → 21/25 et 39/50 ; 65 ou 70 → 19/25 et 34/50 ; 75 → 14/25 et 31/50.

### Décision (27/08/2026) — aucune règle modifiée avant retour client

**Décision utilisateur : `config/scoring_rules.json` reste inchangé.** Motif : la revalidation
est concluante, et ajuster des poids sur quatre profils repérés à l'œil rouvrirait exactement
le sur-mesure sur petit échantillon que ce ticket vient de refermer. Les quatre anomalies
A → D deviennent des **questions client**, ajoutées à la liste de reprise de contact de la
section POC-003. Conséquences : zéro modification de code, zéro re-scoring, la suite de tests
reste à 102 passants, et les 3 critères d'acceptation client de POC-003 sont intacts par
construction (rien n'a bougé).

**Aucun `plan_POC-007.md` n'a été produit** : le plan proposé n'a pas été exécuté, la décision
ayant été de ne rien modifier. Les résultats ci-dessus tiennent lieu de livrable du ticket.

**Hors périmètre, confirmé** : magasin et scraping (POC-006 clos), diversification des
requêtes (POC-008).

**[Code] Avertissement transmis à POC-008** : le mot-clé outdoor « coach qui marche » passerait
par la sous-chaîne `marche`, déjà présente dans 3 titres du lot frais via « Analyste **Marché**
en ophtalmologie » et « expert du **marché** allemand ». À traiter avant d'écrire les mots-clés
de la requête outdoor.

---

## POC-008 — Diversification des requêtes (vocabulaire outdoor + filtre géographique réel)

**Objectif** : Élargir le gisement au-delà de ce qu'une requête booléenne unique peut
livrer, en variant les requêtes plutôt qu'en creusant la même.

**Pourquoi** : [Code + run réel du 26/08/2026] La déduplication persistante de POC-006
donne de l'avance, pas un gisement infini. Mesure faite : ~10 profils par page, **page 8
atteinte sur un plafond estimé à 10 pages** → [Inférence] environ un run restant sur la
requête actuelle. La cible client de 50 profils/semaine n'est pas tenable sans nouvelles
requêtes.

**Deux axes déjà documentés (voir aussi la section POC-006)** :
- **Filtre géographique réel** : [Code] `build_search_url` place toute la requête — y
  compris `AND (France)` — dans le seul paramètre `keywords`. Ce n'est donc pas un filtre
  géographique mais une correspondance textuelle. Les facettes natives de LinkedIn
  seraient plus précises *et* un axe de variation par ville/région.
- **Vocabulaire outdoor** : les 5 mots-clés fournis par le client le 08/07/2026 (*coach
  nature*, *coach qui marche*, *coach outdoor*, *coach hors-les-murs*, *coaching en
  itinérance*) n'apparaissent dans aucune requête actuelle. Une requête dédiée rendrait
  enfin observable la catégorie `coach_outdoor` de POC-003.
  **[Code] Piège mesuré par POC-007 (27/08/2026)** : « coach qui marche » se réduit à la
  sous-chaîne `marche` après normalisation, déjà présente dans **3 titres du lot frais** via
  « Analyste **Marché** en ophtalmologie » et « expert du **marché** allemand ». Les mots-clés
  outdoor doivent être écrits en tenant compte de cet appariement par sous-chaîne, sous peine
  de faux positifs dès la première requête.

**Contrainte forte, contrairement à POC-006** : ce ticket **exige des runs LinkedIn
réels** — les sélecteurs des facettes de recherche doivent être vérifiés sur un DOM réel,
comme l'ont été ceux de POC-001/002/005. Il n'est pas développable entièrement hors-ligne.

**Piste opportuniste** : profiter d'un run réel pour vérifier le sélecteur de la barre de
pagination numérotée et journaliser la taille exacte du gisement par requête (voir la
piste « Mesurer le plafond réel au lieu de l'estimer » en section POC-006).

### Mandat client du 04/09/2026 — le ticket change de nature

Jusqu'ici POC-008 était justifié par des constats **internes** : gisement à ~1 run d'avance,
catégorie `coach_outdoor` jamais observée, pouvoir discriminant écrasé par l'homogénéité de la
requête. Le call du 04/09/2026 y ajoute une **demande client explicite**, et elle est plus
exigeante que ce que le ticket prévoyait.

- **La géographie n'est pas un axe de variation parmi d'autres, c'est un besoin métier.**
  Christophe a cité les Vosges (Remiremont) et le Grand Est, et Bordeaux comme contre-exemple :
  l'objectif est de réunir sur une zone donnée un quota de participants suffisant pour lancer un
  bootcamp. Un profil pertinent mais lointain a donc une valeur faible — ce que le scoring
  actuel ne modélise pas du tout.
- **Mesure du 08/09/2026 sur les 81 profils en base** : **5 en Grand Est** (Labry 85, Colmar 75,
  Saint-Avold 75, Strasbourg 70, Haguenau 45 — donc 4 au-dessus du seuil), contre **21 en
  Île-de-France** et 2 à Bordeaux. Le gisement constitué est presque orthogonal au besoin
  exprimé. C'est l'argument le plus fort du dossier, et il est chiffré.
- **Point d'action n°2 (Michel)** : tester le remplacement de `France` par `Grand Est` dans la
  requête, et mesurer l'effet sur la variance des résultats. **Exige un run LinkedIn réel.**
- **Point d'action n°4 (Michel)** : étudier la faisabilité technique d'intégrer **facilement
  plusieurs requêtes** dans l'outil. [Inférence] Ce volet-là est de la **configuration**, dans la
  lignée de `config/scoring_rules.json` : il est instruisable et implémentable **hors-ligne**,
  sans DOM réel. Le ticket se scinde donc naturellement en une partie configurable hors-ligne et
  une partie « facettes / DOM » qui reste conditionnée à un run.
- **Point d'action n°3 (client)** : Christophe et Henri-Pierre doivent fournir un brainstorming
  de requêtes ciblées (« Coach business » + géographie, « Executive coaching », types de coachs,
  exclusion de « coach sportif »). **Dépendance externe** : le vocabulaire de la campagne ne sera
  pas décidé unilatéralement, et attendre cette liste avant de figer le format de configuration
  évite de la définir deux fois.
- **Arbitrage rappelé par Michel au call** : multiplier les requêtes augmente mécaniquement le
  volume de sollicitations, donc le risque de détection. Le rapport bénéfice/risque fait partie
  du ticket, il n'est pas un détail d'implémentation.
- Le piège de POC-007 reste entier et s'applique au vocabulaire que le client fournira : « coach
  qui marche » se réduit à la sous-chaîne `marche`, déjà présente dans 3 titres du lot frais.

**Décisions** :
- 04/09/2026 — Ciblage géographique confirmé comme **besoin métier prioritaire** par le client.
- 08/09/2026 — [Inférence] Le volet « plusieurs requêtes configurables » est identifié comme
  faisable hors-ligne ; le volet « facettes natives / filtre géographique réel » reste
  conditionné à un run LinkedIn, donc au retour d'itinérance.

### Retour du 11/09/2026 — la géographie redevient secondaire

Le mail de Christophe du 11/09/2026 contredit la lecture du call du 04/09/2026 : *« Nous n'avons
pas tenu compte de la géographie qui reste pour nous un critère accessoire à ce stade. […] Il n'y
a pas de mauvais profil géographique. »* Le mandat géographique de la sous-section précédente
**tombe**. Ce qui reste :

- **Le volume et la variété** : le gisement de la requête actuelle est toujours à ~1 run
  d'avance (page 8 sur ~10). C'est de nouveau l'argument principal du ticket.
- **Le brainstorming de requêtes** dû par le client (point d'action n°3) **n'est pas arrivé** avec
  ce mail. Dépendance externe toujours ouverte.
- **La grille de profilage du 11/09 réoriente le vocabulaire** : viser des coachs d'anciens
  dirigeants et de CODIR (« executive coach », « coach de dirigeants ») plutôt que multiplier des
  variantes géographiques.

**Décisions** :
- 11/09/2026 — Géographie déclarée **critère accessoire** par le client.
- 16/09/2026 — Priorité **P1 → P2** : le levier le plus direct sur la qualité est désormais
  POC-014 puis POC-016 ; POC-008 reste nécessaire pour le volume.


---

## POC-009 — Raccordement de POC-002 et POC-004 au magasin (sans refaire le scraping)

**Objectif** : Faire vivre dans le magasin les résultats de l'extraction d'email (POC-002) et
de l'enrichissement web (POC-004), comme POC-006 l'a fait pour les profils — **sans que
`run_poc002` refasse la recherche déjà effectuée par `run_poc001`**.

**Constat (vérifié dans le code et en base le 26/08/2026, à la clôture de POC-006)** :

1. [Code] POC-006 a câblé `run_poc001` (extraction) et `run_poc003` (scoring) au magasin,
   parce que c'est ce que son périmètre couvrait. `run_poc002` et `run_poc004` sont restés
   sur le schéma CSV → CSV d'avant.
2. [Code] `run_poc002` appelle `search_and_extract` **puis** `enrich_profiles_with_email` :
   il refait donc intégralement la recherche de `run_poc001` avant de visiter les pages
   profil. Coût inutile en quota LinkedIn et en exposition ToS, pour un résultat que le
   magasin détient déjà.
3. [Code] `run_poc004` lit `profils_extraits_email.csv` et écrit
   `profils_extraits_enrichis.csv` : le magasin n'est jamais touché.
4. [Code] **En base au 26/08/2026 : 0 `email`, 0 `email_web`, 0 `site_web` sur 75 profils.**
   Les colonnes existent depuis POC-002/POC-004 mais rien ne les alimente.

**Le piège à ne pas contourner naïvement** : on pourrait croire qu'un simple
`run_poc006 profils_extraits_enrichis.csv` suffirait à rapatrier l'existant. **Il ne faut
pas le faire tel quel.** Ce fichier contient 5 `email_web` et 11 `site_web`, dont — d'après
la relecture humaine déjà consignée en section POC-004 — **1 seul vrai positif confirmé**
(Manuel BOSSU → `mycoachonline.fr`), 1 positif partiel (Sylvie WEILER → `memepascap.fr`,
adresse de cabinet non personnelle) et **7 faux positifs confirmés** (`intercariforef.org`,
`spotify.com`, `noomii.com`, `amazon.co.uk`, `journaldunet.com`, `je-change-de-metier.com`,
`lafrenchcom.fr` avec son `urgent@` typique d'une agence). Les importer en l'état
inscrirait des faux positifs dans le magasin **comme s'ils étaient des faits établis**.

**La vraie question à trancher au cadrage** : le magasin ne sait pas distinguer
« pas encore enrichi » de « enrichi, rien trouvé » de « candidat trouvé, non validé par un
humain » — une colonne vide veut dire les trois. C'est exactement la même classe de problème
que celle réglée par POC-006 pour les profils : **sans marqueur, chaque run refait le
travail**, et sans statut, un candidat incertain devient une donnée de contact.

Pistes à cadrer (aucune n'est décidée) :
- un marqueur « déjà visité pour email » et « déjà enrichi », datés, pour ne traiter que le
  reliquat à chaque run — [Inférence] c'est ce qui remplace la recherche supprimée de
  `run_poc002` : la liste des profils à visiter vient du magasin, pas d'un nouveau scraping ;
- un **statut de validation** sur les coordonnées trouvées (candidat / validé / rejeté),
  pour que la relecture humaine — indispensable au vu du taux de pertinence de 1/25 mesuré
  le 10/07/2026 — soit conservée au lieu d'être refaite ;
- `run_poc004` devient conditionnel après le scoring (décision client du 13/07/2026) :
  sa liste d'entrée est `selectionner_profils_interessants()` appliqué au magasin.

**Attention — évolution de schéma** : ce ticket ajoute très probablement des colonnes au
magasin. Règle CLAUDE.md n°5 : **pas de migration sans plan validé et backup explicite** du
fichier `profils.db`, qui est local, gitignoré et sans sauvegarde.

**Point d'hygiène à traiter au passage** :
[Code] Depuis POC-006, `profils_extraits.csv` ne contient plus l'extraction brute que son nom
suggère, mais une vue complète du magasin (75 lignes, 13 colonnes). Et deux scripts exportent
deux vues du même magasin dans deux fichiers différents (`run_poc001` →
`profils_extraits.csv`, `run_poc003` → `profils_extraits_scores.csv`), qui portent le même
contenu une fois le scoring passé. Un seul fichier d'export suffirait, avec un nom qui dise
ce qu'il est. Renommer relevait de l'hygiène, pas du périmètre de POC-006.

**Décisions** :
- 26/08/2026 — Ticket ouvert à la demande de l'utilisateur, à la clôture de POC-006, après
  constat que le magasin restait vide de toute coordonnée. Contrainte posée par l'utilisateur
  dès l'ouverture : **`run_poc002` ne doit pas refaire le scraping de `run_poc001`**.
- 26/08/2026 — Le rapatriement de `profils_extraits_enrichis.csv` par `run_poc006` est
  **explicitement déconseillé en l'état** (faux positifs, voir ci-dessus). Si l'existant doit
  être récupéré, ce doit être après relecture, ou accompagné d'un statut de validation.

**Résultats du ticket (28/08/2026)** :

*Décisions de cadrage validées par l'utilisateur le 28/08/2026* :
- **(a) Marqueurs datés** `date_visite_email` et `date_enrichissement_web`, `TEXT DEFAULT ''`,
  écrits **même quand rien n'est trouvé** — c'est cette écriture systématique qui distingue
  enfin « pas encore traité » de « traité, rien trouvé ». Reliquat = colonne vide, pas de
  ré-essai automatique dans ce ticket.
- **(a-bis) abandonnée** : `run_poc002` **ne devient pas** conditionnel au score ; son reliquat
  reste l'ensemble des profils non visités. Seul `run_poc004` est conditionnel, conformément à
  la décision client du 13/07/2026.
- **(b) Statut de validation** `statut_coordonnees` : `''` / `candidat` / `valide` / `rejete`,
  **portant sur les coordonnées web uniquement**. L'email LinkedIn de POC-002 n'en relève pas :
  la personne l'a publié sur son propre profil, c'est un fait et non un candidat. `run_poc004`
  écrit `candidat` et jamais `valide` ; seul un humain écrit `valide`/`rejete`, par le CSV
  ré-importé — ce qui a imposé d'étendre `importer_commentaires_csv`, sans quoi la décision (b)
  restait inerte. `candidat` est refusé à l'import : c'est le mot de la machine.
- **(c) Rapatriement nominatif** de `profils_extraits_enrichis.csv`, jamais en bloc.
- **(§5)** Les trois colonnes sont exportées au CSV : c'est par lui que la relecture revient.
- **(§6) Export unifié** : constante `EXPORT_CSV` (`profils_magasin.csv`) partagée par les
  quatre scripts, gitignorée. Les anciens fichiers restent sur disque sans être écrits.

*Migration de schéma* : `user_version` 1 → 2 par `migrer_schema`, idempotente et purement
additive. Backup pris hors dépôt avant tout `ALTER`, migration **vérifiée ligne à ligne contre
le backup : 0 colonne v1 modifiée sur 75 lignes**. Défaut corrigé au passage : [Code]
`ouvrir_magasin` posait `PRAGMA user_version` **inconditionnellement** et aurait marqué une base
v1 comme v2 sans y ajouter une seule colonne.

*Runs réels, un par un* :
- `run_poc002`, 5 profils : **la recherche a bien disparu** — aucune pagination, aucun
  chargement de page de résultats, 5 pages profil et 0 page de recherche. **0 email public
  trouvé**, conforme au 0/30 mesuré le 07/07/2026 : le résultat utile est le marqueur, pas
  l'email. Reliquat 75 → 70.
- `run_poc004`, 4 runs (5 + 25 + 25 + 6) : **56 profils enrichis, 14 candidats trouvés (25 %)**.
  La sélection conditionnelle a fonctionné : 65 profils intéressants traités, **14 profils sous
  le seuil ou exclus jamais interrogés** — 14 appels Brave et 14 collectes de données
  personnelles évités, au titre de la minimisation RGPD.

*Découverte majeure, non anticipée* : [Code, vérifié le 28/08/2026] **6 des 25 profils du lot
POC-002/POC-004 de juillet n'étaient jamais entrés dans le magasin** (recouvrement 19/25,
vérifié : ce n'est pas un défaut d'appariement d'URL). En juillet, `run_poc002` faisait **sa
propre recherche**, distincte de celle de `run_poc001` ; deux recherches sur la même requête
booléenne à deux moments différents n'ont pas ramené le même lot. **La redondance supprimée par
ce ticket ne coûtait pas que du quota : elle produisait deux jeux de données divergents.** Les 6
profils manquants ont été ajoutés au magasin, datés du 07/07/2026, puis scorés — **0 profil
préexistant modifié**. Magasin : 75 → 81 profils.

*Relecture humaine faite avec l'utilisateur le 28/08/2026*, sur les 14 candidats du jour plus
les 11 rapatriés de juillet. **État final : 7 `valide`, 11 `rejete`, 2 `candidat`.**
- Les 7 validés : Elise Rousseau, Isabelle Zelmat, Emmanuel Poilane, Julie Leger, Sylvie
  DUCHENE, Alexandre Schuers, Manuel BOSSU (rapatrié de juillet).
- Faux positifs instructifs : `rgpd@emccfrance.org` retenu pour **deux** profils — l'adresse du
  délégué à la protection des données de la fédération EMCC, le pire destinataire possible ;
  `bibliotheque@ehesp.fr` (employeur, pas homonyme, mais mauvais type de contact) ;
  `music.amazon.com`, que la liste noire a laissé passer alors qu'elle contient `amazon.co.uk` —
  elle raisonne par domaine exact, pas par marque ; `allocine.fr` (homonyme).
- **Modification explicite signalée** : pour Alexandre Schuers, `site_web` (`intch.org`, une
  plateforme) a été **effacé** et l'email `sophro-theatre@schuers.fr` conservé — le pipeline
  avait retenu deux choses d'origines différentes sur la même ligne.
- **Bilan de fond** : **7 coordonnées exploitables sur 56 profils (12,5 %)**, contre 1/25 (4 %)
  en juillet. [Inférence] Amélioration réelle mais non attribuable : liste noire élargie ou
  meilleur lot, les deux effets sont confondus.

*Bug trouvé sur données réelles et corrigé* : deux profils du magasin portent un **emoji dans
leur nom**. L'affichage nominatif du lot, ajouté par ce ticket, levait `UnicodeEncodeError` sur
une console Windows cp1252 et tuait le run **avant le premier appel Brave** — rien n'avait été
écrit en base. Corrigé dans les deux scripts (`run_poc002` portait la même faiblesse sans
l'avoir révélée), avec un test de non-régression sur le chemin des données.

*Laissé en l'état, délibérément* :
- **Titre divergent d'Erwan Jorand** : le CSV du 07/07 porte `certifié RNCP N6 et ICF Level 2`,
  le magasin `certifié ICF Level 2`. Les 19 profils déjà en base n'ont pas été réimportés pour
  ne pas écraser un titre sur lequel un score a été calculé. L'un des deux est périmé, on ne
  sait pas lequel.
- **Anomalie de scoring, 5ᵉ du genre** (après les quatre de POC-007, questions 4 à 7) : **Manon
  Dumartin, score 0 mais catégorie `coach_business_indifferencie`**, donc conservée et non
  exclue. Justification : `base_coach +20 | hors_cible -25`, soit **−5 borné à 0**. Le bornage
  rend un profil de signal **net négatif** indistinguable d'un profil sans aucun signal, alors
  que Cécile Pollin est à 0 *et* exclue. Deux états métier différents, une seule valeur. Non
  corrigé : POC-007 a décidé le 27/08/2026 de ne rien ajuster avant retour client.
- **14 profils du magasin n'ont jamais eu de recherche web** : les 11 sous le seuil et les 3
  exclus, moins les 2 rapatriés. C'est le comportement voulu. Si le seuil passait de 60 à 50,
  Marc Michaud et Stéphanie GOYON entreraient dans la sélection et **le marqueur les reprendrait
  automatiquement**, sans rien refaire.

*Tickets ouverts par ce ticket* : **POC-010** (fusion collecte/scoring/email en une session),
**POC-011** (liste noire éditable — alimenté par `emccfrance.org`, `ehesp.fr`, `allocine.fr` et
la faiblesse `amazon.co.uk` qui n'attrape pas `amazon.com`), **POC-012** (annuaires de coachs
comme source de prospects).

*Question client n°8 produite, non tranchée* : qui valide les coordonnées, nous ou le client ?
La colonne `statut_coordonnees` est exportée dans le CSV, donc visible de lui.

---

## POC-010 — Collecte, scoring et extraction d'email en une seule session LinkedIn

**Objectif** : Faire de `run_poc001` un run complet — collecte des cartes de résultats,
scoring en mémoire, puis visite des pages profil **des seuls profils intéressants** — au
lieu d'une collecte nue suivie d'une seconde session qui refait la même recherche. Une
session LinkedIn, une seule passe, aucune recherche refaite.

**Origine** : ticket ouvert le 28/08/2026 à la demande de l'utilisateur, pendant le cadrage
de POC-009, sur la question « il faudrait une version enrichie de `run_poc001` qui en
profite pour récupérer l'email ». La proposition brute a été instruite puis **amendée** :
voir la décision du 28/08/2026 ci-dessous.

**Constat (vérifié dans le code le 28/08/2026)** :

1. [Code] `run_poc001.main()` enchaîne `ouvrir_magasin` → `urls_connues` →
   `search_and_extract` → `enregistrer_profils` → `lister_profils` →
   `export_profiles_to_csv`. **Aucune visite de page profil, aucun email** :
   `extract_profile_from_card` renvoie exactement `nom`, `titre`, `localisation`, `url`.
2. [Code] `scorer_titre(titre, regles)` ne lit **que le `titre`**, champ disponible dès la
   carte de résultat. **Le score est donc calculable pendant le run de collecte, sans
   visiter une seule page profil.** C'est le fait qui rend ce ticket possible et qui n'avait
   jamais été explicité.
3. [Code] `enrich_profiles_with_email(page, profils)` ne lit que `profil["url"]` et renvoie
   les mêmes dicts + une clé `email` : elle est indifférente à la provenance de la liste.
4. [Code] `_CHAMPS_COMPLETABLES` (`profile_store.py`) contient déjà `email`, `email_web` et
   `site_web` : **`enregistrer_profils` sait déjà écrire l'email**. Aucune migration de
   schéma n'est requise par ce ticket au titre de l'email.

**Design retenu au cadrage** :

```
search_and_extract (pagination complète, aucune visite de page profil)
  → scorer_profils en mémoire              ← ne demande que le titre, déjà présent
  → selectionner_profils_interessants
  → enrich_profiles_with_email SUR CETTE SÉLECTION SEULEMENT
  → enregistrer_profils (profils, scores, emails trouvés)
  → export
```

Pas d'entrelacement risqué : la pagination est entièrement terminée avant la première
visite de page profil.

**Ce que ce ticket ne remplace pas** : [Code] les profils déjà en base sont dans
`urls_connues`, donc `run_poc001` ne les reverra **jamais**. Ce ticket ne fait rien pour le
stock existant. La passe de rattrapage alimentée par le magasin (`run_poc002` version
POC-009) reste nécessaire, et reste le seul chemin pour un profil dont le statut change
après coup — passé sous ou au-dessus du seuil par un ajustement de règles ou par POC-008.

**Points à trancher au cadrage (aucun n'est décidé)** :
- **couplage collecte ↔ règles de scoring** : le run de collecte se met à dépendre de
  `config/scoring_rules.json` — changer une règle change ce qui est visité. Acceptable en
  l'état, ou faut-il un garde-fou (seuil de visite distinct du seuil « intéressant »,
  plafond de visites par run, mode « collecte seule ») ?
- **profils non visités** : ils entrent en base avec `email` vide et sans marqueur de
  visite, ce qui est exact. Vérifier que le reliquat de `run_poc002` les reprend bien et ne
  les considère pas comme traités.
- **un script ou deux** : enrichir `run_poc001` en place, ou livrer un `run_poc010` distinct
  en laissant `run_poc001` intact comme collecte nue ? Pour deux scripts : garder une
  collecte bon marché et sans risque. Pour un seul : deux scripts qui paginent la même
  requête, c'est exactement le doublon que POC-009 supprime.

**Contrainte forte, comme POC-008 et contrairement à POC-009** : ce ticket **exige un run
LinkedIn réel** — seule une session réelle montre que la pagination se termine proprement
avant les visites et qu'aucune restriction de compte n'apparaît. Premier run plafonné à
5 profils, sélection montrée avant visite. Chaque profil collecté entre définitivement dans
`urls_connues` : un run de test consomme du gisement pour de bon.

**Ordre des tickets — trois tickets convergent sur `run_poc001.py` et `profile_search.py`** :
[Code] POC-008 (plusieurs requêtes, facettes géographiques natives dans `build_search_url`)
et POC-010. Ordre recommandé : **POC-009 → POC-008 → POC-010**.
- POC-009 d'abord : il supprime la recherche de `run_poc002`, et donc la duplication de la
  constante `SEARCH_QUERY`, aujourd'hui présente à l'identique dans `run_poc001.py` **et**
  `run_poc002.py` — après quoi POC-008 n'a plus qu'un seul endroit à modifier ;
- POC-008 ensuite : P1, gisement mesuré à ~1 run restant, et c'est lui qui produira les
  profils frais sur lesquels POC-010 a un intérêt ;
- POC-010 en dernier, en vérifiant au démarrage l'état **réel** de `run_poc001.main()` : si
  POC-008 est passé, la fonction boucle probablement sur plusieurs requêtes et le point
  d'insertion du scoring et de la visite n'est plus celui décrit ci-dessus.

**Décisions** :
- 28/08/2026 — Ticket ouvert à la demande de l'utilisateur pendant le cadrage de POC-009.
- 28/08/2026 — **La fusion naïve (visiter la page profil de tous les profils collectés) est
  écartée**, pour trois raisons instruites au cadrage : (1) [Documentation, POC-002] la
  visite d'une page profil « ajoute une requête par profil au-dessus de la recherche, ce qui
  élève le risque de restriction du compte » — fusionner sans filtre rendrait
  **systématique** l'étape la plus risquée du pipeline ; (2) [Documentation, POC-004] le run
  réel de POC-002 a donné **0 email public sur 30 profils** — payer 25 visites par run pour
  une espérance de 0 email est le pire ratio risque/rendement de la chaîne ; (3)
  [Documentation, décision client du 13/07/2026] les coordonnées ne sont cherchées que pour
  les profils intéressants, or dans une fusion naïve **le score n'existe pas encore au
  moment de la visite** — la décision client serait contournée par construction. La variante
  retenue est le scoring en session décrit ci-dessus, rendu possible par le constat n°2.
- 28/08/2026 — **Ce ticket ne rend pas POC-009 caduc** : la passe de rattrapage reste
  nécessaire pour le stock des 75 profils déjà en base et pour tout profil dont le statut
  change après coup.
- 28/08/2026 — Prompt de cadrage préparé dans
  `document/prompts_plans/prompt_POC-010.md`.

### Retour du 11/09/2026 — la prémisse du ticket est fragilisée

[Code] POC-010 reposait sur un fait : `scorer_titre` ne lit que le `titre`, disponible dès la
carte de résultat, donc le score est calculable **sans visiter une seule page profil**. Le retour
client du 11/09/2026 montre que **le titre ne suffit pas** à reproduire le jugement du client, qui
s'appuie sur « Expérience » et « Infos ». Si POC-016 confirme ce besoin, **le scoring utile
exigera une visite de profil**, et l'ordre « scorer d'abord, visiter ensuite » devient « filtrer
sur le titre (seuil 60, zéro faux négatif sur le lot du 11/09), visiter, scorer ». À réinstruire
après POC-016, pas avant.


---

## POC-011 — Liste noire de domaines éditable sans toucher au code

**Objectif** : Sortir `BLACKLISTED_DOMAINS` du code Python pour la placer dans un fichier de
configuration éditable, comme `config/scoring_rules.json` l'a fait pour les règles de scoring.

**Origine** : ticket ouvert le 28/08/2026 à la demande de l'utilisateur, pendant le
rapatriement C2 de POC-009, après constat d'une asymétrie de traitement entre deux corpus de
connaissance métier de même nature.

**Constat (vérifié dans le code le 28/08/2026)** :

1. [Code] `BLACKLISTED_DOMAINS` est un `frozenset` Python de **18 domaines** dans
   `source/backend/adapters/enrichment/email_site_extractor.py` : 14 posés au cadrage de
   POC-004 (réseaux sociaux, annuaires, encyclopédies) et 4 ajoutés le 10/07/2026 après le run
   réel (`noomii.com`, `journaldunet.com`, `spotify.com`, `amazon.co.uk`), chacun pour un faux
   positif nommé.
2. [Code] `is_domain_blacklisted` retire le `www.` puis compare en domaine exact **ou
   sous-domaine** — c'est ce qui fait que `viadeo.journaldunet.com` et `creators.spotify.com`
   sont bloqués.
3. [Code] **Asymétrie** : les règles de scoring vivent dans `config/scoring_rules.json`,
   éditables par l'utilisateur sans toucher au code, avec `charger_regles`/`sauvegarder_regles`
   et un aller-retour testé. La liste noire, de même nature — de la connaissance métier qui
   s'affine à chaque run réel — exige une modification de source, un commit et un test.
4. [Code, mesuré le 28/08/2026] Sur les 11 candidats du run POC-004 de juillet, **5 sont
   aujourd'hui bloqués** par la liste noire (les 4 domaines ajoutés en juillet, `journaldunet`
   comptant pour 2 profils) et **4 passeraient encore** : `intercariforef.org`,
   `je-change-de-metier.com`, `villepratique.fr`, `lafrenchcom.fr`. Aucun de ces 4 n'est un
   annuaire ni une plateforme — rien dans la logique actuelle ne peut les écarter.

**Question de fond, à instruire au cadrage** : le rejet d'un candidat existe aujourd'hui à
**deux granularités qui ne se recouvrent pas**, et POC-009 l'a mis en évidence :
- **par domaine** (liste noire) : protège tous les profils, pour toujours, sans effet de bord ;
- **par profil** (`statut_coordonnees = rejete`, POC-009) : [Code] `_STATUTS_HUMAINS` gèle le
  profil — il ne recevra plus jamais de coordonnées d'un run, même légitimes.

Marquer `rejete` un profil dont le seul tort est d'avoir capté un mauvais domaine l'exclut donc
définitivement de l'enrichissement, alors que la bonne réponse est d'écarter le domaine. Le
ticket doit dire quel mécanisme répond à quel cas, et éventuellement offrir un troisième
niveau (rejeter une **coordonnée** sans geler le profil).

**Périmètre pressenti (à confirmer au cadrage)** :
- `source/backend/adapters/enrichment/email_site_extractor.py` — chargement depuis la config ;
- `config/` — nouveau fichier, ou section d'un fichier existant ;
- tests unitaires — chargement, valeurs par défaut, aller-retour d'édition, sous-domaines.

**Hors périmètre** : le scoring et ses règles ; l'activation du Palier 1 (LLM) de POC-004 ; la
modification du pipeline d'enrichissement lui-même.

**Lien avec le menu configuration** : POC-003 a déjà identifié un besoin de menu de
configuration Streamlit (seuil « profil intéressant » + édition des règles de scoring), non
planifié car `source/frontend_streamlit/` n'existe pas. La liste noire est un troisième
candidat naturel pour ce menu. [Inférence] Regrouper les trois dans un même ticket d'UI serait
plus cohérent que trois écrans séparés — à arbitrer quand l'UI sera cadrée.

**Décisions** :
- 28/08/2026 — Ticket ouvert à la demande de l'utilisateur, pendant POC-009, après mesure de
  l'effet réel de la liste noire sur les 11 candidats de juillet (5 bloqués, 4 passants).
- 28/08/2026 — Aucune modification de la liste noire n'a été faite dans POC-009 :
  `email_site_extractor.py` était hors de son périmètre. Les 4 domaines qui passent encore
  restent donc actifs en attendant ce ticket.

---

## POC-012 — Annuaires de coachs comme source de prospects (gisement hors LinkedIn)

**Objectif** : Instruire les annuaires de coachs en ligne comme **source de prospection à part
entière**, indépendante de LinkedIn — là où POC-008 diversifie les requêtes sur la même source.

**Origine** : idée de l'utilisateur le 28/08/2026, pendant la relecture humaine des candidats de
POC-009 : « on peut garder les annuaires sous la main et essayer de les scraper ».

**Le retournement qui fonde le ticket** : [Code + run réel du 28/08/2026] les domaines que le
pipeline POC-004 doit **écarter** comme candidats sont précisément ceux qui **listent des
coachs**. `noomii.com` est en liste noire depuis le 10/07/2026 pour cette raison ; le run du
28/08 y a ajouté `priorise.fr`, `mon-coach.tel` et `intch.org`, tous rejetés à la relecture
comme annuaires ou plateformes de mise en contact. **Le même domaine est un mauvais candidat
pour un profil donné et une bonne source de prospects.** POC-011 les traite comme des domaines à
exclure ; ce ticket les traite comme des sources à exploiter. Les deux sont liés et distincts.

**Trois arguments en faveur** :

1. **Gisement indépendant de LinkedIn.** [Code, mesuré le 26/08/2026] la requête booléenne
   actuelle est à la page 8 sur ~10, soit [Inférence] environ un run d'avance. POC-008 répond en
   variant les requêtes, mais reste sur la même source et la même exposition ToS. Un annuaire
   est une source entièrement distincte.
2. **Situation RGPD plus favorable, pas moins.** Sur LinkedIn on **infère** un moyen de contact
   à partir d'une recherche web ; dans un annuaire professionnel, la personne a **publié ses
   coordonnées dans le but explicite d'être contactée**. L'intérêt légitime (art. 6.1.f) y est
   sensiblement plus facile à défendre que dans le pipeline actuel.
3. **Taux de pertinence sans commune mesure.** [Documentation] Le pipeline POC-004 mesure 1 vrai
   positif sur 25 en juillet, 7 coordonnées validées sur 56 profils le 28/08/2026. Une fiche
   d'annuaire est structurée : la personne y est identifiée comme coach, avec sa spécialité et
   ses coordonnées, sans inférence.

**Réserves à instruire, pas à balayer** :

- **CGU propres à chaque annuaire** : on ne supprime pas un risque ToS, on le déplace. Chaque
  site doit être examiné pour lui-même, comme LinkedIn l'a été en POC-001.
- **Couverture et volumétrie inconnues** : nombre de coachs français réellement listés, fraîcheur
  des fiches, recouvrement avec le gisement LinkedIn déjà collecté — tout est à mesurer avant
  d'écrire une ligne d'extracteur.
- **Un extracteur par site** : là où LinkedIn n'en demande qu'un, N annuaires en demandent N,
  chacun avec ses sélecteurs et sa maintenance. Le coût croît linéairement.
- **[Code] La clé de déduplication ne tient plus.** `profils` a pour clé primaire l'URL LinkedIn
  normalisée par `clean_profile_url`, et `urls_connues` en dépend entièrement. Un prospect venu
  d'un annuaire n'a pas d'URL LinkedIn. Il faut soit une autre clé, soit un rapprochement
  nom + localisation — avec le risque d'homonymie que tout le reste du projet s'efforce
  d'éviter. **C'est le vrai point dur du ticket, et il touche au schéma du magasin.**
- **Le scoring est calibré sur le `titre` LinkedIn** : une fiche d'annuaire n'a pas ce champ
  sous la même forme. `scorer_titre` s'appliquerait-il tel quel, ou faut-il un mapping ?

**Pistes de départ identifiées par le pipeline lui-même** (aucune évaluée) : `noomii.com`,
`priorise.fr`, `mon-coach.tel`, `intch.org`.

**Périmètre pressenti (à confirmer au cadrage)** : un nouveau module d'adaptateur de collecte,
`profile_store` pour la question de la clé, les tests associés. **Aucun code avant une étape
d'instruction** : couverture, CGU et volumétrie d'abord, extracteur ensuite.

**Hors périmètre** : le scoring et ses règles ; la liste noire (POC-011) ; la diversification des
requêtes LinkedIn (POC-008), qui reste utile et n'est pas remplacée par ce ticket.

**Décisions** :
- 28/08/2026 — Ticket ouvert à la demande de l'utilisateur, pendant la relecture de POC-009,
  après que 4 annuaires soient sortis du pipeline comme faux positifs.
- 28/08/2026 — **Ne remplace pas POC-008** : diversifier les requêtes LinkedIn et ouvrir une
  source hors LinkedIn répondent au même problème de gisement par deux chemins indépendants,
  dont aucun ne rend l'autre inutile.

---

## POC-013 — Livrable Excel client et boucle de retour au format xlsx

**Objectif** : Honorer le point d'action n°1 du call du 04/09/2026 — livrer un **tableau Excel**
que Christophe et Henri-Pierre puissent trier et filtrer, et **accepter en retour le `.xlsx`
annoté**, sans leur demander de le reconvertir.

**Origine** : ticket ouvert le 08/09/2026, depuis le laptop en itinérance, à la lecture du CR du
call du 04/09/2026. **C'est le seul ticket du projet porteur d'une échéance ferme** : fin de la
semaine du 08/09/2026.

**Pourquoi ce n'est pas déjà fait** :

1. [Code] `export_profiles_to_csv` écrit en `encoding="utf-8"` **sans BOM**, avec le séparateur
   virgule par défaut de `csv.DictWriter`. Ouvert d'un double-clic dans un Excel français, ce
   fichier arrive **entièrement en colonne A, accents cassés**. Or le livrable convenu est un
   tableau qu'Henri-Pierre — décrit au call comme « un grand connaisseur d'Excel » — doit trier
   et filtrer. Le format actuel est un obstacle dès la première ouverture.
2. [Code] `importer_commentaires_csv` lit le fichier elle-même (`open(...)` puis
   `csv.DictReader`) : elle ne sait pas lire un classeur. Livrer de l'Excel sans traiter le
   retour reporterait la conversion chez le client, sur un Excel français où « enregistrer en
   CSV » produit exactement le fichier cassé du point 1 — en pire, puisque le séparateur
   deviendrait `;` et que la relecture, elle, attend `,`.

Les deux points forment donc **un seul ticket** : livrer de l'Excel sans savoir le relire
casserait la boucle de retour, qui est le mécanisme central confirmé au call.

**Périmètre — volontairement minimal (décision utilisateur du 08/09/2026)** :

- **Export** : *convertir le CSV existant sans le modifier*. Les 16 colonnes de
  `PROFILE_CSV_FIELDS`, leur ordre et leur contenu restent **strictement identiques**. Ce ticket
  ajoute une conversion, il ne retouche pas l'export.
- **Import** : la boucle de retour accepte un `.xlsx`, en s'appuyant sur l'extension du fichier.

**Risque principal, et vraie raison d'être des tests** : ce n'est pas le code, c'est **ce
qu'Excel fait aux données en chemin**. `csv.DictReader` rend des `str` ; openpyxl rend des
`int`, des `float`, des `datetime` et des `None`. Une date `2026-08-26` peut revenir en
`26/08/2026` ou en numéro de série, un `score` en flottant, un `ne_plus_traiter` en entier, une
cellule vide en `None` — et [Code] `_importer_statut_coordonnees` fait `.strip().lower()` sur
cette valeur, tandis que `_STATUTS_IMPORTABLES` compare des chaînes. Tout doit être relu **en
texte**, une cellule vide valant `""`.

**Piège aggravant, vérifié le 08/09/2026** : [Code] `run_poc006.main` appelle
`enregistrer_profils` **avant** `importer_commentaires_csv`. La première passe complète les
champs des profils connus depuis le fichier relu : c'est elle qui écrirait en base une valeur
reformatée par Excel. Le projet a déjà un titre divergent entre CSV et magasin dont personne ne
sait lequel est le bon (Erwan Jorand, point de vigilance de POC-009) ; ce ticket ne doit pas en
créer un second.

**Exigence héritée de POC-009** : un en-tête non conforme — colonne insérée, supprimée ou
réordonnée par le client — doit être **signalé et bloquant**, jamais deviné. Même logique que les
`statuts_refuses` : la donnée métier est chère, on ne la corrige pas en silence.

**Périmètre pressenti (à confirmer au cadrage)** :
- `source/backend/adapters/storage/xlsx_export.py` — nouveau : conversion CSV → xlsx et lecture
  xlsx → `list[dict[str, str]]` ;
- `source/backend/adapters/storage/run_poc006.py` — accepter un `.xlsx` en entrée ;
- `source/backend/adapters/storage/run_poc013.py` — nouveau, si retenu : produit le `.xlsx`
  depuis l'export CSV, ce qui laisse les quatre `run_pocNNN.py` existants intacts ;
- `pyproject.toml` — dépendance xlsx (openpyxl n'est pas installé aujourd'hui ; pandas l'est,
  mais via Streamlit et sans moteur Excel) ;
- `tests/unit/test_xlsx_export.py` — nouveau.

**Hors périmètre** : toute modification du contenu de l'export (aucune colonne ajoutée, retirée,
renommée ni réordonnée, aucune valeur reformatée) ; la mise en forme Excel (largeurs, filtre
automatique, figeage d'en-tête, styles), **hors périmètre par défaut**, à proposer comme
arbitrage explicite ; le scoring et ses règles ; les règles de conflit du ré-import, acquises
depuis POC-006 et POC-009 ; toute migration de schéma.

**Question ouverte, à trancher au cadrage** : quelles lignes livrer ? Le magasin compte **81
profils, dont 65 au-dessus du seuil 60**. Le client demandait « plus d'une dizaine de noms ».
[Inférence] Livrer les 81 avec la colonne `score` est cohérent avec ce qu'il a dit vouloir faire
— trier et filtrer lui-même, notamment par localisation — et lui laisse l'arbitrage du seuil,
qui est précisément l'une des questions ouvertes. Les profils marqués `ne_plus_traiter` restent
exclus de l'export, comme depuis POC-006.

**Décisions** :
- 08/09/2026 — Ticket ouvert depuis le laptop, à la lecture du CR du 04/09/2026.
- 08/09/2026 — **Périmètre minimal retenu** (utilisateur) : conversion du CSV sans modification,
  et ré-import du `.xlsx`. Pas de refonte de l'export, pas de mise en forme par défaut.
- 08/09/2026 — Ticket **réalisable en itinérance** : aucun run LinkedIn, aucun réseau, lecture du
  magasin puis une écriture maîtrisée au ré-import de vérification. Prompt prêt dans
  `document/prompts_plans/prompt_POC-013.md`.
- 08/09/2026 — **Question « quelles lignes livrer » tranchée (utilisateur) : le CSV intégral**,
  soit les 81 profils moins les `ne_plus_traiter`, **sans filtre de seuil**. Cohérent avec un
  client qui a dit vouloir trier et filtrer lui-même ; l'arbitrage du seuil lui revient, et c'est
  précisément l'une des questions ouvertes que le retour d'usage doit trancher.
- 08/09/2026 — **Bascule xlsx → lignes : option A** (utilisateur). `run_poc006` convertit le
  classeur en CSV voisin, puis déroule son chemin actuel. **`profile_store.py` n'est pas
  touché** : c'est lui qui porte les règles de conflit de POC-006 et POC-009, et l'option B
  (ajouter un paramètre `lignes` à `importer_commentaires_csv`) aurait modifié le seul module où
  une régression coûterait des données client. Bénéfice secondaire retenu : le CSV intermédiaire
  est une **trace inspectable** de ce qu'Excel a rendu.
- 08/09/2026 — **Mise en forme : minimum strict accepté** (utilisateur) — figeage de la ligne
  d'en-tête et filtre automatique, **rien d'autre**. Aucune valeur touchée.
- 08/09/2026 — **Données de test retirées du magasin** (utilisateur). L'aller-retour de
  vérification avait écrit 4 `commentaire_client` et 1 `statut_coordonnees` inventés ; les
  laisser aurait livré au client de faux commentaires à son nom et un verdict humain factice.
  Base restaurée depuis la sauvegarde, empreinte de départ retrouvée.

**Réalisé le 08/09/2026 — ce que le run réel a appris**

- **`openpyxl>=3.1`** ajouté aux dépendances. Nouveau module
  `source/backend/adapters/storage/xlsx_export.py` : `convertir_csv_en_xlsx`, `lire_xlsx`,
  `xlsx_vers_csv`, et l'exception `EnteteXlsxInvalide`. Nouveau script `run_poc013.py` ; les
  quatre `run_pocNNN.py` existants sont restés intacts, sauf `run_poc006.py` qui reçoit
  l'aiguillage par extension.
- **La parade au risque principal est en deux temps, pas un.** À l'aller, chaque cellule est
  écrite **en texte** (format Excel `"@"`), ce qui empêche Excel de réinterpréter une date ou un
  score à l'ouverture. Au retour, tout est ramené en `str` et une cellule vide vaut `""`. Le
  premier temps est ce qui fait que le second n'a presque rien à rattraper.
- **Détail vérifié à l'écriture** : [Code] openpyxl type une chaîne commençant par `=` comme une
  **formule**. Un `commentaire_client` ou une `justification` commençant par `=` serait devenu
  une formule Excel ; les cellules sont donc forcées en type `s`.
- **Aller-retour fait dans le vrai Excel** (Excel 16.0 piloté par COM), pas simulé — c'est ce que
  demandait le critère. Résultat mesuré : après ouverture et enregistrement par Excel,
  **exactement 5 cellules divergentes sur 81 × 16, les 5 annotées à la main**. Aucune date
  reformatée, aucun score en flottant, **aucun des 6 noms à emoji abîmé**. Puis ré-import et
  comparaison ligne à ligne contre la sauvegarde : **14 colonnes sur 16 intactes**, seules
  `commentaire_client` et `statut_coordonnees` ont bougé. Le piège de `enregistrer_profils`
  appelé en premier n'a rien abîmé.
- **Trou de POC-009 découvert par ce run et corrigé** : [Code] `_afficher_rapport` de
  `run_poc006` n'imprimait **ni `statuts_tranches` ni `statuts_refuses`**. Les deux champs
  existent dans `RapportReimport` depuis POC-009 et `_importer_statut_coordonnees` les remplit,
  mais aucun script ne les affichait — un statut entrait en base sans trace, et surtout une
  valeur **non reconnue** (« Validé » accentué, « OK ») était **écartée en silence**, ce que la
  règle de POC-009 interdit explicitement. Corrigé (décision utilisateur du 08/09/2026), avec un
  test. Le run de contrôle affiche désormais les 19 statuts tranchés et 0 refusé.
- **Angle mort RGPD refermé** : `profils_magasin.xlsx` et `profils_magasin.reimport.csv`
  n'étaient couverts par **aucune** règle de `.gitignore`, qui listait les CSV **un par un**.
  Deux fichiers de données personnelles de 81 personnes réelles étaient à un `git add .` d'être
  versionnés. `*.xlsx` et `*.reimport.csv` ajoutés.
- **Le bug cp1252 de POC-009 s'est reproduit** — dans un script d'analyse jetable de la session,
  pas dans le code du projet, qui lui a tenu. Confirmation que le magasin contient **6 profils à
  emoji** et non 2 comme le handoff le laissait entendre : ce sont 2 profils qui avaient fait
  planter le run, sur 6 porteurs du risque.
- **Comportement idempotent constaté, sans conséquence** : chaque ré-import ré-écrit les statuts
  déjà tranchés avec la même valeur, et les signale comme tranchés. Rien n'est perdu ; c'est
  seulement bruyant sur un gros lot. Non corrigé, hors périmètre.
- Tests : **143 passed, 0 failed, 0 skipped** (123 avant POC-013), dont 20 nouveaux dans
  `tests/unit/test_xlsx_export.py`.

**Reste ouvert après POC-013** : le fichier est produit, il n'est pas **envoyé**. L'envoi à
Christophe et Henri-Pierre est un geste humain, hors outil. Le retour d'usage promis au call
(point d'action n°5) reste la dépendance qui débloque les arbitrages de scoring.

---

## POC-014 — Scoring v2 sur le titre, mesuré contre la grille de profilage du client

**Objectif** : Mesurer, et pousser aussi loin que raisonnable, ce que le **titre seul** permet de
reproduire du jugement client du 11/09/2026 — sans extraction supplémentaire, sans run LinkedIn.

**Origine** : ticket ouvert le 16/09/2026, à l'analyse du retour client du 11/09/2026 (section
POC-003, « Retour client du 11/09/2026 »).

**Pourquoi** : pour la première fois, le projet dispose d'un **jeu de référence humain** — 81
profils jugés par le client. Le score v1 écarte correctement (zéro faux négatif au seuil 60) mais
ne classe pas (précision 40 % au-dessus du seuil, pour un taux de base de 32 %), et ses bonus sont
pondérés à l'envers de leur pouvoir discriminant mesuré.

**Pistes relevées à l'analyse, à instruire — pas à appliquer d'office** :
- **Catégorie** : remplacer `coach_business_indifferencie` (78 profils sur 81) par les 4 niveaux
  du client (excellent, bon, mauvais, rien à voir), ou une projection du score sur ces niveaux.
- **Exclusions ou malus nommés par le client** : numérologie, coach interne (salarié d'une
  entreprise, ex. « chez Stellantis »), service aux coachs, coach « en formation ».
- **Fonction publique** : indices dans le titre (Conseil Régional, Fédération Hospitalière, cadre
  de santé…) — **couverture partielle attendue**, le critère relève surtout du parcours.
- **Ancien dirigeant** : signaux visibles dans 5 des 6 titres excellents (Directeur, Directeur
  associé, Co-fondateur, VP, Executive Coach, « coache les dirigeants »).
- **Anomalie A** : « Life & Business Coach » doit être exclu — normalisation de l'esperluette ou
  mot-clé dédié.
- **Rééquilibrer les poids** : `certification` (+15) n'apporte aucun signal (35 % pour 32 % de
  base), `focus_business` (+40) presque aucun, `cible_business` (+10) est le plus discriminant.
- **« Consultant » n'est pas un motif d'exclusion** : un excellent le porte. Le client vise le
  multicarte.

**Risque principal — le sur-apprentissage** : ajuster des règles sur 81 profils **et** les évaluer
sur les mêmes 81 reproduit exactement le défaut que POC-007 a dû lever pour POC-003. Garde-fous à
arrêter au cadrage :
- **règles génériques uniquement**, jamais un mot-clé qui ne vise qu'un profil nommé ;
- chaque règle ajoutée justifiée par **la définition du client**, pas par un profil ;
- métriques publiées **avant et après** (précision au-dessus du seuil, rappel, matrice
  score × verdict), et **validation obligatoire sur le prochain lot annoté** avant de s'y fier.
- **Ne jamais dégrader le rappel** : aujourd'hui aucun bon profil n'est écarté ; une v2 qui en
  écarte un doit le justifier explicitement.

**Critère de sortie attendu** : un chiffre honnête — « le titre seul permet d'atteindre X % de
précision sans perte de rappel » — qui dira si POC-016 est **indispensable** ou seulement utile.

**Périmètre pressenti** : `config/scoring_rules.json` ; `source/backend/core/profile_scoring.py`
si un nouveau type de règle ou la catégorie à 4 niveaux l'exige ; un script d'évaluation
**en lecture seule** contre les verdicts stockés ; tests unitaires. **Aucune migration** si la
catégorie reste dans la colonne `categorie` existante.

**Hors périmètre** : extraction de nouveaux champs LinkedIn (POC-016) ; colonne département
(POC-015) ; toute modification de `commentaire_client`, qui est la vérité terrain.

**Faisable en itinérance** : oui — hors-ligne, magasin lu, puis re-scoring par `run_poc003` après
sauvegarde.

**Décisions** :
- 16/09/2026 — Ticket ouvert, itération validée par l'utilisateur.

---

## POC-015 — Colonne département dans l'export

**Objectif** : Répondre à la suggestion du client du 11/09/2026 — *« une nouvelle colonne numéro
de département ou nom du département serait la bienvenue »* — pour **trier**, la géographie
restant un critère accessoire.

**Constat mesuré le 16/09/2026** : la `localisation` LinkedIn n'est pas homogène. **52 profils** au
format « Ville, Région, France » (département dérivable via une table commune → département),
**28** en libellé unique (« Paris et périphérie », « Lille et périphérie », « France ») dont une
partie **n'est pas rattachable** à un département, 1 en deux parties. Une valeur vide doit rester
possible et assumée, jamais devinée.

**Point de vigilance hérité de POC-013** : [Code] le ré-import **refuse** un classeur dont
l'en-tête ne correspond pas à `PROFILE_CSV_FIELDS`. Ajouter une colonne rend **inimportables les
classeurs déjà envoyés au client**. C'est pourquoi le retour du 11/09/2026 a été ré-importé
**avant** ce ticket. Le cadrage doit décider : colonne dérivée à l'export seulement (pas de
migration) ou stockée ; et comment traiter un ancien classeur qui reviendrait.

**Périmètre pressenti** : table de correspondance statique versionnée ; fonction pure de
dérivation ; `csv_export.py` ; tests. **Hors périmètre** : tout filtrage géographique de collecte
(POC-008).

**Faisable en itinérance** : oui.

**Décisions** :
- 11/09/2026 — Suggestion client.
- 16/09/2026 — Ticket ouvert, **après** le ré-import du retour du 11/09/2026.

---

## POC-016 — Extraction des rubriques « Expérience » et « Infos » du profil LinkedIn

**Objectif** : Donner au scoring les informations que le client utilise réellement pour juger un
profil.

**Origine** : retour client du 11/09/2026 — *« Nous avons beaucoup utilisé, en plus du titre, les
champs "Expérience" et "Infos" qui sont très utiles pour le profilage. »* Deux des trois axes de
leur grille (ancien dirigeant ; carrière privée contre fonction publique) relèvent du parcours.

**Levier identifié** : [Code] `run_poc002` **visite déjà** la page profil pour l'email — pour
**0 email public sur 30 profils** testés. Capturer « Expérience » et « Infos » pendant cette même
visite rendrait enfin utile l'étape la plus risquée du pipeline, sans ajouter de visite. Restreinte
aux profils au seuil 60 ou plus, la visite n'aurait écarté **aucun** bon profil du lot du 11/09.

**Contraintes fortes** :
- **Run LinkedIn réel obligatoire** — sélecteurs à vérifier sur DOM vivant, centralisés dans
  `selectors.py`. **Pas en itinérance** : attend le retour sur le poste principal et sa session.
- **Migration de schéma** (nouvelles colonnes) — **plan validé et sauvegarde explicite**.
- **RGPD** : « Expérience » et « Infos » sont des données personnelles plus riches que le titre.
  Minimisation à instruire au cadrage : stocker le texte brut, ou seulement les signaux dérivés.
- **Volume de texte** : des règles par mots-clés sur un texte long déclenchent beaucoup plus
  facilement que sur un titre ; le piège de sous-chaîne de POC-007 (« marche » / « marché ») y est
  aggravé. [Inférence] C'est aussi le premier endroit où le palier LLM, écarté jusqu'ici, pourrait
  se justifier — la philosophie « pas de sophistication inutile » du call du 04/09 impose de
  mesurer d'abord le déterministe.

**Dépend de** : POC-014, dont le chiffre dira si ce ticket est indispensable ou seulement utile.
**Remet en cause** : la prémisse de POC-010.

**Décisions** :
- 16/09/2026 — Ticket ouvert, itération validée par l'utilisateur. Réalisation au retour
  d'itinérance.

---

## POC-017 — Recherche de coordonnées déclenchée par le verdict, pas par le seuil

**Objectif** : Ne plus chercher les coordonnées des profils que le client ne contactera pas.

**Constat du 16/09/2026** : sur les **7** profils dont les coordonnées ont été validées à la main
(POC-009), **5 sont jugés mauvais profil** par le client. [Code] `run_poc004` s'enclenche sur
`selectionner_profils_interessants`, c'est-à-dire le seuil 60, qui écarte bien mais ne classe pas.
Le coût est double : appels Brave et relecture humaine dépensés au mauvais endroit, et collecte de
données personnelles sur des personnes qui ne seront pas contactées (**minimisation RGPD**).

**Pistes** : déclencher sur le verdict client quand il existe (`bon` ou `excellent`), et sur le
score v2 de POC-014 sinon. Question ouverte : que faire des coordonnées **déjà** collectées pour
des profils jugés mauvais — les conserver, ou les effacer au titre de la minimisation.

**Faisable en itinérance** : la sélection oui ; un run d'enrichissement demande `BRAVE_SEARCH_API_KEY`
et le réseau, disponibles sur le laptop, et **écrit dans le magasin** (à consigner dans le prompt
de réconciliation).

**Dépend de** : POC-014.

**Décisions** :
- 16/09/2026 — Ticket ouvert, itération validée par l'utilisateur.
