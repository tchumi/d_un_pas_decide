Tu travailles dans le repo ProspectionLinkedIn avec Claude Code dans VS Code.

Je viens de faire un /clear. Tu reprends **POC-016 en cours de session**, mise en pause le
30/10/2026 après le relevé de DOM et la rédaction du mail au client. Ne relis pas tout le
repository.

> Contexte : session préparatoire avant le call client (**05/11/2026 après-midi d'après le plan**,
> Henri-Pierre proposait aussi le 03/11 au matin : confirmation non vue). Les sauvegardes vont dans
> `D:\Documents\Dev\_backup_prospection\`. **Ce n'est pas une fin de session** : `task_list.md`,
> `handoff.md`, `Backlog.md` et `CLAUDE.md` n'ont pas encore été mis à jour pour POC-016 — ce sera
> fait à la clôture.

## Documents à lire en premier

1. `CLAUDE.md`
2. `document/prompts_plans/plan_POC-016.md` — **le plan validé**, avec les décisions de
   l'utilisateur et les réponses proposées au client (questions 1 et 4 à actualiser, voir plus bas)
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

### Modifications du 30/10 **non committées** (7 fichiers, 306 tests au vert)

L'utilisateur n'a pas encore demandé le commit : ne pas committer sans sa demande.

`profile_email.py`, `run_poc002.py`, `selectors.py`, `core/parcours.py`, `tests/unit/test_parcours.py`,
`tests/unit/test_profile_email.py`, `tests/unit/test_run_poc002.py`, plus ce prompt.

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

**Toujours à confirmer** : `core/parcours.py` est hors du périmètre initial du prompt. Placé dans
`core/` parce que le scoring le lira ; signalé, non confirmé par l'utilisateur.

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
connexion a ensuite répondu `CONNECTE` et les 7 visites sont passées. **Cause inconnue.** Le
changement de clé Wi-Fi de l'utilisateur est peut-être lié : avant ou après le blocage, à lui
demander. À consigner dans `handoff.md`. Pas de contournement (masquage de l'automatisation, VPN ou
changement d'IP pour repasser) : si le blocage revient, s'arrêter et en référer au client.

## État vérifié au 30/10/2026

* Tests : **306 passed** (277 au départ du ticket).
* Magasin **non modifié** : 131 profils, 131 commentaires, `user_version` 2, empreinte MD5
  `189e64e0f6c1aa234851422686103ff5`. 101 profils au seuil, 97 jamais visités.
* `config/scoring_rules.json` intact.
* **Pages enregistrées encore présentes** : `tests/temp/poc016_releve_{1,2,3,4}.html` (gitignoré,
  **données personnelles**). Plus utiles, à supprimer par l'utilisateur, les règles du projet
  l'interdisant à l'agent : `Remove-Item tests\temp\poc016_releve_*.html`

## Ce qui reste

**Avant le call** :
* envoi du mail par l'utilisateur (statut d'envoi inconnu : à lui demander). Il annonce la mesure
  sur les 50 annotations pour le call ;
* actualiser dans `plan_POC-016.md` les questions 1 (ajouter l'incident) et 4 (cas Patrick Sisco) ;
* commit des modifications, à la demande de l'utilisateur.

**Conditionné à la réponse du client** :
* code de migration v3, écrit et testé sur base temporaire sans être appliqué : non commencé,
  inutile si le client renonce aux visites. Colonnes selon sa réponse à la question 2.

**Après le call** : sauvegarde, migration, runs par paliers, évaluateur étendu, mesure de l'apport.

**À la clôture** : les quatre fichiers de `CLAUDE.md`, le prompt de POC-017, commit final.

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
* Mesure de l'apport, après le call : signaux réglés sur les profils au seuil du lot 1 (60), mesurés
  sur ceux du lot 2 (41) — ne pas régler et mesurer sur les mêmes profils.
* `profil_dirigeant` : recommandation de garder la règle jusqu'à ce qu'un signal de parcours la
  remplace ; décision au call. Mesure en mémoire : à 80 et plus sur le lot 1, sa neutralisation fait
  tomber les excellents de 6/6 à 2/6 ; sur le lot 2, 0/3 dans les deux cas.
* Réponses en français, commentaires de code en anglais, affirmations taguées
  [Code] / [Documentation] / [Inférence].

## Première réponse attendue

Ne modifie aucun fichier. Vérifie la branche, l'état Git (7 fichiers modifiés, plus ce prompt), la
suite de tests (306) et l'empreinte du magasin, résume en 5 lignes où en est la session, puis
demande à l'utilisateur si le mail est parti, si le call du 05/11 est confirmé et s'il veut committer.
