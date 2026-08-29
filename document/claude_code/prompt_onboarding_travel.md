Tu reprends la conversation de **suivi de projet** ProspectionLinkedIn sur une machine
secondaire (ex : laptop en déplacement). Ce n'est pas une session de ticket au sens de
`prompt_générique.md` — c'est la reprise du rôle "copilote de projet" : suivi du backlog,
cadrage de tickets, rédaction de communication client, décisions d'architecture/outillage,
logistique d'environnement. Pas de `/clear` préalable requis pour ce prompt : au contraire,
il sert justement à reconstituer le contexte sur une machine qui n'a pas l'historique de
conversation.

> Dernière révision : 28/08/2026 (après POC-009). Ce fichier vieillit vite : si l'écart avec
> `task_list.md` est flagrant, c'est `task_list.md` qui a raison.

## ⚠️ Le point le plus important : `profils.db` est ici une COPIE

Depuis POC-006, la source de vérité du projet n'est plus un CSV mais un magasin SQLite,
`profils.db` à la racine. Il est **gitignoré** : il ne circule pas par Git, il est **recopié
à la main** d'une machine à l'autre (décision utilisateur du 28/08/2026 — la base et les CSV
partent sur le laptop, contrairement à `browser_profile/`, voir plus bas). Il contient
aujourd'hui 81 profils, leurs scores, les statuts de coordonnées relus à la main, les
commentaires client, les dates de collecte et les marquages d'opposition RGPD.

**Le risque n'est donc pas l'absence, c'est la divergence.** Deux copies existent, et
**SQLite n'a aucun mécanisme de fusion** : si les deux sont modifiées, il n'y a pas de
`git merge` pour les réconcilier — il faut en sacrifier une, ou recoller les lignes à la
main. Le projet a déjà payé ce prix : POC-009 a découvert que deux recherches sur la même
requête, lancées à deux moments différents, avaient produit deux jeux divergents dont
6 profils qui n'étaient jamais entrés en base.

**Règle : une seule copie fait foi à un instant donné.**

- Décider **avant de partir** quelle machine écrit. En déplacement, c'est normalement le
  laptop, et le poste principal ne doit alors plus rien écrire jusqu'au retour.
- Ne jamais lancer un `run_pocNNN.py` sur les deux machines entre deux recopies. Toute
  écriture (collecte, scoring, enrichissement, ré-import) rend cette copie-ci la référence.
- **Au retour** : sauvegarder la base du poste principal dans
  `D:\Documents\Dev\_backup_prospection\` **avant** de la remplacer par celle du laptop.
  Écraser d'abord et constater ensuite est irréversible.
- En cas de doute sur la copie la plus récente, comparer avant d'écraser — nombre de
  profils, `max(date_collecte)`, et le compte des `statut_coordonnees` non vides.

**Ce qui ne se reconstruit pas** : les scores et les profils se recalculent depuis les CSV,
mais les **commentaires client**, les **statuts relus à la main** (`valide`/`rejete`), les
**dates de collecte** et les **marquages d'opposition** n'existent nulle part ailleurs.
Perdre la bonne copie, c'est perdre la seule trace du travail de relecture humaine et des
garde-fous RGPD.

**Piège technique à connaître** : [Code] `ouvrir_magasin`
(`source/backend/adapters/storage/profile_store.py`) fait `executescript(_SCHEMA)`, qui
**crée la base si elle n'existe pas**. Si la copie a été oubliée, un `run_pocNNN.py` ne
lèvera **aucune erreur** : il créera un magasin vide et collectera dedans. Toujours vérifier
que `profils.db` est bien là **et non vide** avant d'exécuter quoi que ce soit.

Les tests, eux, ne touchent jamais le magasin réel (aucun navigateur, aucun réseau, base en
mémoire) : `uv run --extra test pytest tests/ -q` est sans danger.

**Données personnelles sur une machine nomade** : la base et les CSV contiennent 81 profils
réels. Un laptop se perd plus facilement qu'un poste fixe — chiffrement du disque recommandé,
et effacer les copies au retour si elles n'ont plus lieu d'être.

## Ce qui ne se synchronise pas par Git

Le code et la documentation sont dans le dépôt (`origin` = GitHub privé), donc à jour dès
`git pull`. En revanche, **rien de ce qui suit ne se synchronise** (volontairement, voir
`.gitignore`). Deux catégories, à ne pas confondre : ce qui est **recopié à la main** et ce
qui ne doit **surtout pas** l'être.

**Recopié à la main d'une machine à l'autre** :

- **`profils.db`** — voir la section ci-dessus : c'est une copie, le risque est la
  divergence, et son contenu relu à la main ne se reconstruit pas.
- **Les CSV de profils** (`profils_extraits*.csv`, `profils_magasin.csv`) — recopiés
  également. `profils_magasin.csv` est l'export du magasin : s'il a été régénéré avant le
  départ il est cohérent avec la base, sinon il peut être périmé (c'est arrivé le
  28/08/2026 — un export figé au milieu d'une relecture annonçait 1 contact validé au lieu
  de 7). En cas de doute, **la base fait foi, pas le CSV**.

- **`document/compte_rendu/`** — la correspondance client (PDF des échanges avec Christophe
  Hoffstetter et Henri-Pierre Michaud, brouillons de mails), si un travail de communication
  est prévu pendant le déplacement. C'est l'historique des décisions business : sans lui, on
  ne peut ni citer un engagement ni vérifier une demande. À défaut, s'appuyer sur les
  décisions datées reportées dans `Backlog.md`, qui en sont le résumé fidèle.

**À ne JAMAIS recopier** :

- **`browser_profile/`** — session Playwright/cookies LinkedIn. Un même cookie de session
  apparaissant depuis une nouvelle localisation ressemble à un vol de session pour les
  systèmes anti-fraude de LinkedIn. C'est la seule exception vraiment non négociable de
  cette liste : préférer une connexion manuelle fraîche sur cette machine si un run réel est
  nécessaire, et naviguer normalement quelques instants avant de lancer le moindre script.

**Absent, à recréer ou à accepter tel quel** :

- **`.env.local`** — à recréer à la main plutôt qu'à copier (`BRAVE_SEARCH_API_KEY` au
  minimum ; les identifiants LinkedIn y restent vides, le login est manuel, voir décisions
  POC-001 dans `Backlog.md`).
- **`D:\Documents\Dev\_backup_prospection\`** — les sauvegardes datées du magasin. Chemin
  local au poste principal, donc absent ici. Conséquence directe : **en déplacement, il n'y
  a pas de filet** — la copie emportée est la seule, en faire un double avant toute
  opération d'écriture.
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
- `playwright install chromium` a bien été exécuté sur cette machine (sinon le signaler,
  ne pas lancer de script de scraping avant).

**Et surtout, l'état du magasin** — une base présente mais vide est le scénario dangereux
(voir l'avertissement en tête). Vérifier en lecture seule, sans passer par `ouvrir_magasin`
qui écrirait le schéma :

```powershell
uv run python -c "import sqlite3; c=sqlite3.connect('profils.db'); print('profils:', c.execute('select count(*) from profils').fetchone()[0]); print('derniere collecte:', c.execute('select max(date_collecte) from profils').fetchone()[0]); print('statuts relus:', c.execute(\"select count(*) from profils where coalesce(statut_coordonnees,'')<>''\").fetchone()[0])"
```

Comparer au dernier ticket DONE de `handoff.md` (au 28/08/2026 : **81 profils**, dernière
collecte du 26/08/2026, **20 statuts relus** dont 7 `valide`). Trois lectures possibles :
- **chiffres cohérents** → la copie est bonne, continuer ;
- **base absente ou à 0 profil** → la copie a été oubliée : **ne lancer aucun
  `run_pocNNN.py`**, le signaler à l'utilisateur, et se limiter au travail hors magasin ;
- **chiffres inférieurs à l'attendu** → copie périmée : le dire avant toute écriture, écrire
  dedans figerait la divergence.

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

**Sans risque — n'écrit pas dans le magasin, donc ne crée aucune divergence** :
- cadrage et rédaction de tickets, prompts, plans ;
- communication client (un brouillon de reprise de contact attend d'être relu et envoyé,
  dans `document/compte_rendu/`) ;
- logique pure et tests unitaires : le moteur de scoring (`core/profile_scoring.py`) et les
  règles (`config/scoring_rules.json`) sont versionnés et testables hors-ligne ;
- **lecture** du magasin (requêtes SQL en lecture seule, statistiques, vérifications) ;
- documentation, revue d'architecture, décisions d'outillage.

**Possible, mais rend cette copie la référence** — à faire seulement si l'utilisateur
confirme que le poste principal n'écrira rien d'ici le retour, et après un double de la base :
- `run_poc003.py` (re-scoring depuis le magasin — hors-ligne, pas de LinkedIn) ;
- `run_poc006.py` (amorçage ou ré-import d'un CSV annoté — c'est le chemin qui rapatrie les
  commentaires client s'ils arrivent pendant le déplacement) ;
- `run_poc004.py` (enrichissement web — nécessite `BRAVE_SEARCH_API_KEY` et le réseau).

**À éviter en déplacement** :
- tout ce qui ouvre une session LinkedIn : `run_poc001.py`, `run_poc002.py` — le login est
  manuel, la session doit être fraîche sur cette machine, et le quota comme le risque de
  restriction de compte se gèrent mieux depuis le poste habituel ;
- **POC-008** (diversification des requêtes) et **POC-010** (session LinkedIn unique) :
  ils **exigent** un run LinkedIn réel — les sélecteurs de facettes doivent être vérifiés
  sur un DOM réel, et le DOM LinkedIn change régulièrement ;
- toute migration de schéma : la procédure impose un backup explicite, et le dossier de
  sauvegardes n'est pas sur cette machine.

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
