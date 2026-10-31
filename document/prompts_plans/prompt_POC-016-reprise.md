Tu travailles dans le repo ProspectionLinkedIn avec Claude Code dans VS Code.

Je viens de faire un /clear. Tu reprends **POC-016, en attente de la décision du client**. Séance
préparatoire close le 31/10/2026 après le relevé de DOM, la mesure et la rédaction du mail. Ne relis
pas tout le repository.

> Contexte : call client **confirmé le 05/11/2026 après-midi**. Les sauvegardes vont dans
> `D:\Documents\Dev\_backup_prospection\`. `task_list.md` (POC-016 `IN_PROGRESS`), `handoff.md`
> (section 20), `Backlog.md` et `CLAUDE.md` sont à jour au 31/10 : **le ticket n'est pas terminé**.

## Documents à lire en premier

1. `CLAUDE.md`
2. `document/prompts_plans/plan_POC-016.md` — **le plan validé**, avec les décisions de
   l'utilisateur, les réponses proposées au client et l'actualisation du 31/10
3. `document/prompts_plans/prompt_POC-016.md` — le prompt d'origine (périmètre, critères
   d'acceptation, risques)
4. `document/compte_rendu/2026 10 30 - brouillon mail Michel - test lecture Experience avant call (a coller dans Outlook).txt`
   — le brouillon du mail au client, à jour (dossier hors suivi Git)

Puis le code :

* `source/backend/core/parcours.py` — en entier
* `source/backend/adapters/scraping/run_poc002.py` — en entier
* `source/backend/adapters/scraping/profile_email.py` — `scroll_profile_page`,
  `extract_section_text`, `extract_rubriques_from_profile_page`
* `source/backend/adapters/scraping/selectors.py` — `LinkedInProfileSelectors`

## Ce qui est fait

### Commits sur `master`

| Commit | Contenu |
|---|---|
| `1a26fc3` | `docs:` plan POC-016 |
| `c42a30a` | `fix:` `run_poc002` ne visite plus que les profils au seuil. Reliquat réel : **97 profils** |
| `f0f8001` | `feat:` signaux de parcours (`core/parcours.py`), lecture des rubriques, mode `--releve` |
| `ba01cf4` | `docs:` ancienne version de ce prompt |
| `ded0226` | `feat:` corrections de `parcours.py`, signal fonction publique |
| `177170d` | `fix:` sélecteurs vérifiés, défilement, arrêt du relevé sur page de blocage |
| `b948281` | `docs:` version du 30/10 de ce prompt |

### Modifications du 30/10, committées le 31/10 (`ded0226`, `177170d`, 306 tests au vert)

`profile_email.py`, `run_poc002.py`, `selectors.py`, `core/parcours.py`, `tests/unit/test_parcours.py`,
`tests/unit/test_profile_email.py`, `tests/unit/test_run_poc002.py`.

* **Sélecteurs** : `not(.//section)` ajouté. Une section englobant tout le profil correspondait
  aussi et venait en premier, si bien que Formation et Activité étaient lues comme des postes.
  Vérifiés sur DOM réel, résultat consigné en commentaire dans `selectors.py`.
* **Défilement** : souris placée au centre de la page avant la molette, crans de 600 px (9 crans)
  au lieu de 900 px (6), plus courts que la fenêtre de 720 px.
* **Arrêt du relevé** sur page de blocage (`page_bloquee` : titre Cloudflare observé, URL
  `/checkpoint/`, `/authwall`, `/login`). Agit à l'ouverture des profils, **pas sur la page
  d'accueil** : là, `ensure_logged_in` attend Entrée.
* **Relevé** : page enregistrée pour chaque profil, plus seulement en cas de section absente.
* **`parcours.py`** :
  * durée calculée quand LinkedIn n'en affiche pas (dates en années seules) ;
  * poste à date unique (« nov. 2024 ») lu comme terminé, durée 0 ;
  * titre de statut seul (auto-entrepreneur, freelance…) : coach si la ligne de compétences le
    dit. Réservé à ces titres, pour qu'une compétence « Coaching » ne masque pas le second poste
    d'un DRH ;
  * nouveau signal `fonction_publique`, lu dans le type de contrat « Fonctionnaire ».

`core/parcours.py` est hors du périmètre initial du prompt ; placé dans `core/` parce que le scoring
le lira, confirmé par l'utilisateur le 31/10.

## Résultat du relevé (30/10/2026)

7 visites de profil (5 profils, 2 relus après correction), postes comparés à la main sur LinkedIn.

| Profil | Note | Verdict client | Coach en cours | Autre poste en cours | Ancien dirigeant | Fonction publique |
|---|---|---|---|---|---|---|
| Edouard Pierre | 60 | excellent | oui, 156 mois | non | non | non |
| Cécile Belot | 60 | bon | oui, 34 mois | non | oui | non |
| Magali Lafaye | 60 | mauvais, multi fonction | **non** | oui | non | non |
| Patrick Sisco | 60 | mauvais | oui, 34 mois | non | oui | **oui** |
| Narjess Kalifa | 100 | mauvais, multi fonction | **non** | oui | non | non |

* Signal le plus net : **pas de poste de coach en cours**. « Ancien dirigeant » et l'ancienneté ne
  séparent pas ces profils.
* **La définition proposée à la question 4 laisse passer Patrick Sisco.** La fonction publique est
  une hypothèse à faire confirmer par le client ; le signal a été ajouté après avoir vu ce profil.
* Illustration sur 5 profils choisis, avec une lecture ajustée en les regardant : **pas une preuve**.

**Limites connues, laissées en l'état** :
* intitulés des postes groupés mal lus (« 10 ans 1 mois », lieu du poste précédent) : rien ne
  distingue une entreprise d'un lieu dans le texte seul. Signaux justes sur ces profils, mais un
  mot-clé dans la ligne précédant un poste groupé pourrait en fausser un ;
* « Afficher les N expériences » jamais observé : signal de liste tronquée non vérifié.

## L'incident du 30/10/2026

Au premier lancement, page Cloudflare « Sorry, you have been blocked » sur la page d'accueil, avant
toute visite. Ray ID non noté. Compte accessible dans Firefox, pas d'exit node Tailscale. Un test de
connexion a ensuite répondu `CONNECTE` et les 7 visites sont passées. **Cause inconnue.**
Accès revenu en 13 minutes au plus (blocage signalé à 10:10, `CONNECTE` à 10:23, heures locales),
avant la première modification de code du jour (10:27) ; `browser_session.py` inchangé depuis le
03/07 : le code est écarté. Clé Wi-Fi changée **avant** le lancement et conservée (réponse de
l'utilisateur, 31/10) : même clé pour le blocage et le retour de l'accès, elle ne suffit donc pas à
l'expliquer. Consigné dans `handoff.md`. Pas de contournement (masquage de l'automatisation, VPN ou
changement d'IP pour repasser) : si le blocage revient, s'arrêter et en référer au client.

## État vérifié au 30/10/2026

* Tests : **306 passed** (277 au départ du ticket).
* Magasin **non modifié** : 131 profils, 131 commentaires, `user_version` 2, empreinte MD5
  `189e64e0f6c1aa234851422686103ff5`. 101 profils au seuil, 97 jamais visités.
* `config/scoring_rules.json` intact.
* Pages du relevé `tests/temp/poc016_releve_*.html` : absentes au 31/10, rien à supprimer.

## Ce qui reste

**Avant le call** :
* envoi du mail par l'utilisateur (non parti au 31/10, brouillon à jour ; statut à lui demander).
  Call du 05/11 après-midi **confirmé** ;
* partage de la note de mesure avec le client, par l'utilisateur : page privée
  https://claude.ai/artifact/EJA5ZEqaYND76Z95aHpdYz (chiffres recalculés le 31/10, sans nom de
  profil) ;
* objet du mail : il ne parle que du test de lecture ; proposition faite à l'utilisateur, sans
  réponse : « Prospection LinkedIn - mesure des règles et test de lecture avant notre call du
  5 novembre ».

**Le mail propose au client, section « POUR CONTINUER »** (décision de l'utilisateur du 31/10, à
faire valider au call ; rien de cela n'est implémenté) :
* lire **les 131 profils**, en 8 lancements environ, et non plus les 97 au seuil ;
* construire la note avec « Expérience » : 81 annotations pour régler, 50 pour contrôler ;
* garder le texte brut dans la base locale, hors des fichiers envoyés au client, puis le supprimer
  au plus tard 3 mois après la lecture ; ne garder ensuite que les indicateurs ;
* confirmer la définition de « pratiquer le coaching » et la raison du verdict de Patrick Sisco.

**Réserve signalée à l'utilisateur** : les 30 profils sous le seuil ajoutent 30 visites, alors que le
client les a tous jugés mauvais ou « rien à voir » (27 et 3). Option plus prudente : les 101 au seuil.

**RGPD, question de l'utilisateur** : l'intérêt légitime peut fonder le traitement, sans dispenser de
la minimisation ni de la durée limitée. Recommandation : garder la suppression sous 3 mois. Conserver
le texte plus longtemps relèverait du client et de son conseil. Lecture non juridique : aucune analyse
juridique dans le projet.

**Conditionné à la réponse du client** :
* code de migration v3, écrit et testé sur base temporaire sans être appliqué : non commencé,
  inutile si le client renonce aux visites. Colonnes selon sa réponse sur les données conservées.

**Après le call, si le client accepte** : actualiser le plan selon ses décisions (périmètre 131 ou
101 ; `run_poc002` reste restreint au seuil tant que ce n'est pas décidé) ; sauvegarde, migration ;
brancher la lecture des rubriques et l'écriture dans le run normal de `run_poc002` ; runs par
paliers ; évaluateur étendu ; mesure ; proposition de note au client.

**À la clôture du ticket** : les quatre fichiers de `CLAUDE.md`, le prompt de POC-017, commit final.

## Interdit avant l'accord du client

* appliquer une migration au magasin réel ;
* écrire du texte de parcours dans le magasin ;
* modifier `config/scoring_rules.json` ;
* lancer une collecte. L'utilisateur a évoqué un run de 50 profils ; déconseillé, et le mail annonce
  qu'aucune collecte n'aura lieu avant la décision du client.

## Rappels

* **Les runs LinkedIn réels sont lancés par l'utilisateur** : préparer, donner la commande, attendre
  la sortie collée. Plafonds validés : 5, puis 10, puis 20 par run.
* Avant tout run qui écrit le magasin : sauvegarde datée du magasin et de `journal_collecte.csv`,
  puis contrôle des `commentaire_client` contre la sauvegarde.
* Mesure de l'apport, après le call : si le client accepte les 131 profils, régler sur le lot 1 (81)
  et mesurer sur le lot 2 (50) ; s'il s'en tient au seuil, 60 et 41. Ne jamais régler et mesurer sur
  les mêmes profils.
* `profil_dirigeant` : recommandation de garder la règle jusqu'à ce qu'un signal de parcours la
  remplace ; décision au call. Mesure en mémoire : à 80 et plus sur le lot 1, sa neutralisation fait
  tomber les excellents de 6/6 à 2/6 ; sur le lot 2, 0/3 dans les deux cas.
* Réponses en français, commentaires de code en anglais, affirmations taguées
  [Code] / [Documentation] / [Inférence].

## Première réponse attendue

Ne modifie aucun fichier. Vérifie la branche, l'état Git, la suite de tests (306) et l'empreinte du
magasin, résume en 5 lignes où en est la session, puis demande à l'utilisateur si le mail est parti,
si la note de mesure est partagée et quelle est la décision du client.
