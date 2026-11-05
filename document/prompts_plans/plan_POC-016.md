# Plan POC-016 — Extraction des rubriques « Expérience » et « Infos »

Validé par l'utilisateur le 29/10/2026. Session préparatoire avant le call client du 05/11/2026.

## Diagnostic (29/10/2026)

- Magasin vérifié en lecture seule : 131 profils, 131 commentaires, `user_version` 2, 0 opposé,
  empreinte `189e64e0f6c1aa234851422686103ff5`. 5 profils visités pour l'email (28/08), 0 email.
  **101 profils au seuil 60 ou plus, dont 97 jamais visités.**
- [Code] `run_poc002` **ne filtrait pas sur le score** : il visitait tout profil non visité et non
  opposé. Un des 5 profils visités le 28/08 est sous le seuil ou exclu. La restriction est à
  ajouter, sur le modèle de `run_poc004`.
- [Code] Le scoring et `run_poc014_evaluation` ne lisent que le `titre` : mesurer l'apport exige
  d'étendre l'évaluateur (périmètre élargi, décision utilisateur n°6).
- [Inférence, à vérifier au relevé] La page profil ne montre peut-être qu'une partie de
  l'expérience (lien vers `/details/experience/`) et charge ses sections au défilement : « sans
  visite supplémentaire » n'est tenable qu'avec une capture partielle.
- [Inférence] Le « multi-fonction » illisible dans le titre peut se lire dans la **structure** de
  l'expérience (nombre de postes en cours simultanément), sans piège de sous-chaîne.

## Décisions de l'utilisateur (29/10/2026)

1–5. Ne pas attendre le call : proposer au client des réponses par défaut, à faire valider (par
     mail avant le call, ou au call).
6.   Périmètre élargi à `run_poc014_evaluation.py`, et à `core/profile_scoring.py` quand une règle
     naîtra.
7.   Restriction de `run_poc002` au seuil 60 : **tout de suite**.
8.   Relevé de DOM : oui, sur des profils qui confrontent le titre au commentaire du client et
     testent la discrimination.
9.   Plafonds : 5, puis 10, puis 20 par run après un run sans incident.
10.  `profil_dirigeant` : mesurer sa neutralisation en mémoire maintenant, trancher après le call.

## Réponses proposées au client (questions 1 à 5, à faire valider)

| # | Question | Proposition par défaut |
|---|---|---|
| 1 | Faire le ticket ? | Oui : ~100 visites de profil, au rythme actuel (pauses humaines, lots de 5, 10, puis 20), **arrêt immédiat en cas de blocage**. Le client arbitre en connaissant l'incident du 30/10 (voir plus bas). |
| 2 | Texte brut ou signaux ? | Texte brut **temporaire** pendant la mesure, puis purge ; ne restent que des signaux dérivés. |
| 3 | Durée de conservation du texte brut | Jusqu'à la fin de la mesure, **au plus 3 mois** ; purge tracée dans `handoff.md`. |
| 4 | Qu'est-ce que « pratiquer le coaching » ? | Un poste de coach **en cours**, en activité indépendante ou en cabinet, **depuis au moins 2 ans**, et **pas d'autre poste salarié en cours**. À corriger par le client : cette définition laisse passer Patrick Sisco (voir plus bas). |
| 5 | Capture partielle acceptable ? | Oui : on lit seulement les postes visibles sur la page principale ; on ne visite pas de seconde page. |

Signaux dérivés candidats : nombre de postes en cours ; présence d'un poste de coach en cours et
son ancienneté ; ancienne fonction de direction (parcours, plus le titre) ; employeur public ;
longueur et présence de « Infos ».

### Actualisation du 31/10/2026, après le relevé

- **Question 1, incident du 30/10** : page Cloudflare sur la page d'accueil, avant toute visite,
  signalée à 10:10 (heure locale). Accès revenu à 10:23 au plus tard, avant la première modification
  de code du jour (10:27) ; `browser_session.py` inchangé depuis le 03/07. Clé Wi-Fi changée avant le
  lancement et conservée, donc présente au blocage comme au retour de l'accès. **Cause inconnue.**
  Pas de contournement : si le blocage revient, arrêt et décision du client.
- **Question 4, Patrick Sisco** : verdict « mauvais profil », sans justification. Le parcours montre
  un coach en cours sans autre poste, plus un poste de directeur sous contrat « Fonctionnaire ». La
  grille du client classe « Carrière fonction publique » en mauvais profil (`Backlog.md`, retour du
  11/09) : explication probable, à faire confirmer. Sur les titres, ce critère était resté au taux
  de base (1/3).
- **Le scoring reste fondé sur le seul titre à ce jour.**
- **Proposition au client, décidée par l'utilisateur le 31/10, à faire valider au call** : lire
  **les 131 profils**, y compris les 30 sous le seuil, et construire la note avec « Expérience »,
  réglée sur les 81 premières annotations et contrôlée sur les 50 suivantes. Si le client accepte, cela
  remplace la décision n°7 et le critère d'acceptation « visite restreinte au seuil » (`run_poc002`
  reste restreint au seuil tant que ce n'est pas décidé), le découpage 60/41 et le ticket distinct
  envisagé pour la note.

## Actualisation du 05/11/2026, après le call

Sources : mail de Christophe du 03/11 (« OK pour tes autres propositions dans POUR CONTINUER »,
grille mise à jour), compte rendu Geremy du call du 05/11, décisions de l'utilisateur du 05/11.
**Ce qui suit remplace, là où il les contredit, les décisions n°5, 7 et 9, les réponses proposées
aux questions 1 à 5 et les étapes 5 et suivantes.**

### Décisions

| # | Sujet | Décision | Source |
|---|---|---|---|
| D1 | Périmètre | Lecture des **131 profils** non opposés. Les 81 du lot 1 d'abord, puis les 50 du lot du 07/10 | Client, 03/11 |
| D2 | Coordonnées | La visite de lecture **n'ouvre plus la fenêtre « Coordonnées »** (0 email sur 30). Le code de l'email reste en place, non appelé | Utilisateur, 05/11 |
| D3 | Stockage | Texte brut des deux rubriques en base locale, hors des fichiers envoyés. Indicateurs et verdict estimé **calculés, non stockés**, tant que les règles bougent ; figés en base à la suppression du texte | Client, 03/11 |
| D4 | Conservation | Proposition : suppression **au plus tard 30 jours après la présentation de la nouvelle note**. **À confirmer par écrit par le client** | Call, 05/11 |
| D5 | Blocage | Arrêt immédiat ; reprise décidée **au cas par cas entre l'utilisateur et l'agent** | Utilisateur, 05/11 |
| D6 | Rythme | Paliers 5, 10, puis 20 ; **2 lancements par jour** au plus ; volume à rediscuter entre nous | Utilisateur, 05/11 |
| D7 | Annotations | Non reclassées, `commentaire_client` intact. Le **verdict estimé par le nouveau scoring** va dans une colonne distincte. Correction d'Edouard Pierre (« bon ») demandée au client par le retour Excel | Utilisateur, 05/11 |
| D8 | Excel | Verdict estimé et variables intermédiaires dans l'export : **ticket distinct POC-018** | Utilisateur, 05/11 |

### Grille du client, règles retenues

Ordre : **les critères négatifs l'emportent**. (a) Pas de coach business en activité → rien à
voir ; (b) sinon, fonction publique, activité en parallèle ou coach de vie → mauvais ; (c) sinon,
ancien dirigeant privé → excellent ; (d) sinon → bon. Le mail du 03/11 le dit déjà (« même si coach
en activité », « quelle que soit la carrière »).

- **Ancien dirigeant** : DG, PDG, gérant, fondateur, directeur d'une fonction. Ni « responsable »
  ni « manager ».
- **Coach business** : mots-clés du 22/10, plus « coach de leader » et « leadership coaching ». Un coach
  sans qualificatif compte comme business ; un coach de vie est mauvais.
- **Indépendant** : n'est plus un filtre. Le salarié ou l'associé d'un cabinet est gardé.
- **Moins de 2 ans** : non éliminatoire, classé bon, avec un indicateur « coach récent ». Durées
  de postes de coach successifs non cumulées.
- **Activité en parallèle**, salariée ou non (mandat associatif inscrit dans « Expérience » compris)
  → mauvais. « Coach et formateur » dans un même poste ne suffit pas.
- **Fonction publique** : un poste suffit. Contrat « Fonctionnaire » **et** noms d'employeurs
  publics. Liste à valider par l'utilisateur ; faux positifs comptés sur le lot 1.
- **Associatif** : ne compte pas comme privé pour « excellent » (dirigeant associatif → bon). Noms
  d'employeurs associatifs, liste à valider ; un EHPAD seul ne suffit pas.
- **`profil_dirigeant`** (règle sur le titre) : proposé au remplacement par le signal de parcours
  « ancien dirigeant privé ». Tranché à la mesure.

### Étapes actualisées

5. **Mail de confirmation** au client (brouillon dans `document/compte_rendu/`, envoyé par
   l'utilisateur) : D4, D7, grille.
6. **Migration v3** (hors ligne) : `texte_experience`, `texte_infos`, `date_lecture_parcours`,
   additive et idempotente comme v2. Code et tests sur base temporaire, **sauvegarde datée**, puis
   application et contrôle ligne à ligne.
7. **Run de lecture** (réel, lancé par l'utilisateur) : `run_poc002` lit les deux rubriques et
   écrit texte et date ; profils non lus et non opposés, lot 1 d'abord ; marqueur posé même si
   rien n'est trouvé ; arrêt sur page de blocage ; sauvegarde et contrôle des `commentaire_client`
   avant et après chaque run.
8. **Signaux et verdict estimé** (hors ligne) : nouveaux signaux dans `core/parcours.py`
   (coach business, coach de vie, dirigeant privé, fonction publique et associatif par employeur),
   verdict selon la grille, fonction pure dans `core/`.
9. **Mesure** (hors ligne) : évaluateur étendu, réglage sur le lot 1, contrôle sur le lot 2.
   Décision à contacter / à écarter, et excellent à part ; Edouard Pierre signalé comme erreur
   d'annotation connue. `config/scoring_rules.json` inchangé avant la mesure.
10. **Présentation au client**, avant tout changement de la note. Échéance annoncée : fin de la
    semaine du 09/11, sans engagement ferme.
11. **Suppression du texte** dans le délai confirmé, indicateurs figés auparavant.

### Critères d'acceptation modifiés

- « Capturées pendant la visite que `run_poc002` fait déjà pour l'email » devient : capturées
  pendant **une seule visite par profil**, sans ouvrir la fenêtre « Coordonnées ».
- « Visite restreinte aux profils au seuil 60 » devient : lecture des **131 profils non opposés**.
- Ajouté : le verdict estimé est mesuré contre les annotations du client avant toute présentation.

## Ce qui se fait hors ligne, ce qui exige un run réel

| | Hors ligne (aucune visite LinkedIn) | Run réel (lancé par l'utilisateur) |
|---|---|---|
| **Objectif** | Préparer et sécuriser : code, tests, mesures en mémoire sur ce qu'on a déjà | Observer ce que seul LinkedIn montre : DOM, texte des rubriques |
| **Avant le call** | Restriction au seuil ; mesure de `profil_dirigeant` neutralisé ; extraction et dérivation des signaux sur HTML synthétique + tests ; code de migration v3 testé sur base temporaire **sans l'appliquer** | **Relevé de DOM sur 5 profils** : rien d'écrit en base, signaux calculés en mémoire et affichés en regard du verdict client |
| **Après accord du client** | Sauvegarde datée ; migration v3 appliquée ; contrôle ligne à ligne ; évaluateur étendu ; mesure de l'apport | Runs de production par lots (5, 10, 20) jusqu'aux 97 profils ; contrôle des `commentaire_client` après chaque run |
| **Interdit avant accord** | Migration appliquée au magasin réel ; modification de `config/scoring_rules.json` | Écriture de texte de parcours dans le magasin |

## Profils du relevé (décision n°8)

Cinq profils, choisis pour la discrimination, plafond 5 du premier run :

- **Le même titre, « Coach professionnel », score 60, verdicts opposés** (lot du 07/10) :
  1 excellent, 1 bon, 1 « mauvais, multi fonction », 1 mauvais sans précision. Le titre ne peut
  pas les départager ; le relevé dit si le parcours le peut.
- **Un « mauvais, multi fonction » noté 100** (faux positif de tête) : le parcours montre-t-il
  plusieurs postes en cours ?

Ces 5 profils ne sont pas marqués visités par le relevé : la production les revisitera (5 visites
de plus, assumées).

## Étapes

1. **Restriction au seuil de `run_poc002`** (hors ligne) — sélection au seuil puis reliquat, comme
   `run_poc004` ; test unitaire.
2. **Extraction et signaux** (hors ligne) — fonctions pures sur HTML synthétique, sélecteurs
   provisoires dans `selectors.py` ; rubrique absente ou illisible → `""`, jamais d'exception.
3. **Relevé de DOM** (run réel, 5 profils) — mode `--releve` de `run_poc002`, aucune écriture en
   base ; sélecteurs confirmés ou corrigés ensuite.
4. **Mesure de `profil_dirigeant` neutralisé** (hors ligne, en mémoire, règles candidates hors de
   `config/`).
5. **Après accord du client** : migration v3 (sauvegarde, contrôle), runs de production, mesure de
   l'apport — signaux réglés sur les profils au seuil du lot 1 (60), mesurés sur ceux du lot 2
   (41), pour éviter le sur-apprentissage de POC-014.

## Tests prévus

- Sélection de `run_poc002` : sous le seuil, exclu, déjà visité → écartés.
- Extraction : rubrique présente, absente, tronquée, illisible ; postes en cours comptés.
- Migration v3 (si décidée) : additive, idempotente, aucune donnée existante touchée,
  `commentaire_client` intact.
- Point de départ : 277 passed.
