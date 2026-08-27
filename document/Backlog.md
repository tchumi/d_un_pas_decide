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
