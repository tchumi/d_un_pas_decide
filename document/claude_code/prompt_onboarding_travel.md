Tu reprends la conversation de **suivi de projet** ProspectionLinkedIn sur une machine
secondaire (ex : laptop en déplacement). Ce n'est pas une session de ticket au sens de
`prompt_générique.md` — c'est la reprise du rôle "copilote de projet" : suivi du backlog,
cadrage de tickets, rédaction de communication client, décisions d'architecture/outillage,
logistique d'environnement. Pas de `/clear` préalable requis pour ce prompt : au contraire,
il sert justement à reconstituer le contexte sur une machine qui n'a pas l'historique de
conversation.

> Dernière révision : 28/08/2026 (après POC-009). Ce fichier vieillit vite : si l'écart avec
> `task_list.md` est flagrant, c'est `task_list.md` qui a raison.

## ⚠️ Le point le plus important : `profils.db` n'est PAS sur cette machine

Depuis POC-006, la source de vérité du projet n'est plus un CSV mais un magasin SQLite,
`profils.db` à la racine. Il est **gitignoré** — donc absent après un `git clone`/`git pull`.
Il contient aujourd'hui 81 profils, leurs scores, les statuts de coordonnées relus à la main,
les commentaires client, les dates de collecte et les marquages d'opposition RGPD.

**Le piège** : [Code] `ouvrir_magasin` (`source/backend/adapters/storage/profile_store.py`)
fait `executescript(_SCHEMA)`, qui **crée la base si elle n'existe pas**. Lancer un
`run_pocNNN.py` sur cette machine ne provoquerait donc **aucune erreur** : le script
créerait un magasin vide et se mettrait à collecter dedans. On se retrouverait avec deux
jeux de données divergents — exactement le défaut que POC-009 a découvert et corrigé
(en juillet, deux recherches sur la même requête avaient produit deux lots différents,
6 profils n'étant jamais entrés en base).

**Règle en déplacement : ne lancer aucun script `run_pocNNN.py`.** Pas de collecte, pas de
scoring, pas d'enrichissement, pas d'export. Si un besoin réel se présente, restaurer
d'abord une sauvegarde (voir ci-dessous) et le dire explicitement à l'utilisateur avant
d'exécuter quoi que ce soit.

Les tests, eux, ne touchent jamais le magasin réel (aucun navigateur, aucun réseau, base en
mémoire) : `uv run --extra test pytest tests/ -q` est sans danger.

## Ce qui ne se synchronise pas par Git

Le code et la documentation sont dans le dépôt (`origin` = GitHub privé), donc à jour dès
`git pull`. En revanche, **rien de ce qui suit ne se synchronise** (volontairement, voir
`.gitignore`) et doit être vérifié ou accepté comme absent :

- **`profils.db`** — voir la section ci-dessus. Sans équivalent, sans reconstruction possible
  à l'identique : les commentaires client, dates de collecte et oppositions n'existent nulle
  part ailleurs.
- **`D:\Documents\Dev\_backup_prospection\`** — les sauvegardes datées du magasin. Chemin
  local à la machine principale, donc absent ici aussi.
- **`.env.local`** — notamment `BRAVE_SEARCH_API_KEY` (les identifiants LinkedIn y restent
  vides, le login est manuel, voir décisions POC-001 dans `Backlog.md`).
- **`browser_profile/`** — session Playwright/cookies LinkedIn. **Ne pas copier ce dossier
  d'une machine à l'autre** : un même cookie de session apparaissant depuis une nouvelle
  localisation ressemble à un vol de session pour les systèmes anti-fraude de LinkedIn.
  Préférer une connexion manuelle fraîche sur cette machine si un run réel est nécessaire,
  et naviguer normalement quelques instants avant de lancer le moindre script.
- **`document/compte_rendu/`** — toute la correspondance client (PDF des échanges avec
  Christophe Hoffstetter et Henri-Pierre Michaud, brouillons de mails). C'est l'historique
  des décisions business : sans lui, on ne peut ni citer un engagement ni vérifier une
  demande. À défaut, s'appuyer sur les décisions datées reportées dans `Backlog.md`, qui en
  sont le résumé fidèle.
- **Les CSV de profils** (`profils_extraits*.csv`, `profils_magasin.csv`) — données
  personnelles, à ne recopier qu'en cas de besoin réel et en quantité minimale.
- **Le binaire navigateur Playwright** (`playwright install chromium`) — distinct de
  `uv sync`, à ne pas oublier sur une machine neuve.

## Étape 1 — Vérification d'environnement (avant toute chose)

```powershell
git status --short
git branch --show-current
git log --oneline -5
```

Vérifier aussi, sans jamais afficher leur contenu :
- Présence et non-vacuité de `.env.local` (au minimum `BRAVE_SEARCH_API_KEY`).
- **Présence ou absence de `profils.db`** — et le signaler explicitement dans la réponse.
  Son absence est normale en déplacement ; ce qui ne l'est pas, c'est de l'ignorer.
- `playwright install chromium` a bien été exécuté sur cette machine (sinon le signaler,
  ne pas lancer de script de scraping avant).

```powershell
uv run --extra test pytest tests/ -q
```

Le nombre de tests attendu est dans `task_list.md` (ligne du dernier ticket DONE). Note :
`pytest` seul ou `python -m pytest` échoue — le module n'est pas dans le Python système,
il faut passer par `uv run --extra test`.

Si le dépôt n'est pas encore cloné sur cette machine :
```powershell
git clone https://github.com/tchumi/d_un_pas_decide.git
uv sync --extra test
playwright install chromium
```

## Étape 2 — Lecture pour reprendre le contexte

La documentation a beaucoup grossi (`Backlog.md` dépasse 1300 lignes, `handoff.md` compte
une section par ticket). **Ne plus tout lire en entier** — c'était l'instruction d'origine,
elle coûte trop cher aujourd'hui, surtout sur une petite machine. Lire dans cet ordre :

1. `CLAUDE.md` — en entier (court), en particulier « État actuel ».
2. `document/claude_code/task_list.md` — en entier (court) : **source de vérité des statuts
   et des métriques**. C'est le seul fichier à lire intégralement sans hésiter.
3. `document/claude_code/handoff.md` — les **deux dernières sections** seulement, plus un
   survol des titres pour situer l'enchaînement des tickets.
4. `document/claude_code/AGENTS.md` — en entier (règles de travail, conventions).
5. `document/Backlog.md` — **par sections ciblées**, jamais en entier : la section du ticket
   en cours, celle du ticket précédent, et la sous-section « Questions ouvertes à poser au
   client » de POC-003 (elle centralise les arbitrages en attente).

Ne pas lire le code source à ce stade — seulement si un ticket précis l'exige ensuite.

## Étape 3 — Première réponse attendue

Ne modifie aucun fichier. Réponds avec :

1. Résultat de la vérification d'environnement (Étape 1) — signaler explicitement tout
   élément manquant (`.env.local`, `profils.db`, navigateur Playwright, résultat des tests)
   sans bloquer la conversation pour autant.
2. Un point d'étape façon "faisons le point" : tickets `DONE`/`BLOCKED`/`TODO` en cours,
   dernière décision notable, prochain ticket recommandé — **en distinguant ce qui est
   faisable sur cette machine de ce qui ne l'est pas**.
3. Une question ouverte : qu'est-ce que l'utilisateur veut traiter dans cette session.

## Ce qui est faisable — et ce qui ne l'est pas — en déplacement

**Faisable sans risque** (ni LinkedIn, ni magasin, ni clé API) :
- cadrage et rédaction de tickets, prompts, plans ;
- communication client (un brouillon de reprise de contact attend d'être relu et envoyé,
  voir `document/compte_rendu/` sur la machine principale) ;
- logique pure et tests unitaires : le moteur de scoring (`core/profile_scoring.py`) et les
  règles (`config/scoring_rules.json`) sont versionnés et testables hors-ligne ;
- documentation, revue d'architecture, décisions d'outillage.

**À éviter en déplacement** :
- tout `run_pocNNN.py` (voir l'avertissement en tête de fichier) ;
- **POC-008** (diversification des requêtes) et **POC-010** (session LinkedIn unique) :
  ils **exigent** un run LinkedIn réel — les sélecteurs de facettes doivent être vérifiés
  sur un DOM réel, et le DOM LinkedIn change régulièrement ;
- toute manipulation du magasin ou migration de schéma.

**Bon candidat pour une session en déplacement** : **POC-011** (liste noire de domaines
éditable sans toucher au code) — logique pure et configuration, dans la lignée de ce qui a
déjà été fait pour `config/scoring_rules.json`, aucun accès externe requis. **POC-012**
(annuaires de coachs comme source hors LinkedIn) est cadrable, mais pas implémentable sans
accès réseau réel.

## Contraintes qui restent valables sur cette machine

- Mêmes règles Git que d'habitude : pas de `reset --hard`, pas de checkout destructif,
  pas d'amend, pas de force push.
- Plan court avant toute modification non triviale (comme d'habitude).
- Pas de migration de schéma sans plan validé **et backup explicite** — d'autant moins ici
  que les sauvegardes du magasin ne sont pas sur cette machine.
- Réponses en français, commentaires de code en anglais, comme dans `AGENTS.md`.
- Obligation de fin de session inchangée : `task_list.md`, `handoff.md`, `Backlog.md` et
  `CLAUDE.md` (voir CLAUDE.md, « Obligation de fin de session »).
