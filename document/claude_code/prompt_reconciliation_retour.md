# Prompt de réconciliation au retour — du laptop vers le poste principal

> À coller sur le **poste principal**, au retour d'itinérance, **avant tout autre travail**.
> Rédigé le 08/09/2026 au départ, **complété le 05/10/2026 au retour** : l'itinérance est
> terminée, l'inventaire de l'étape 0 est **figé et vérifié**, il n'y a plus de session de
> déplacement à attendre.
> Pendant de `prompt_onboarding_travel.md`, qui gère le départ.

Tu reprends le projet ProspectionLinkedIn sur le **poste principal**, au retour d'une période
d'itinérance pendant laquelle le travail s'est fait sur le laptop. Ce n'est pas une session de
ticket : c'est une **opération de réconciliation de données**, à faire proprement avant de
reprendre quoi que ce soit d'autre.

## Le fait qui commande tout

**Pendant l'itinérance, le poste principal était éteint** (décision utilisateur du 08/09/2026).
Il n'a donc **rien écrit**, et cela simplifie radicalement la situation : il n'y a pas deux jeux
de modifications à fusionner, il y a une copie qui a vécu et une copie figée.

**La base du laptop fait foi. Celle du poste principal est périmée.**

C'est le cas favorable, et il ne le reste que si l'on ne fait pas d'erreur maintenant. SQLite
n'a aucun mécanisme de fusion : il n'y a pas de `git merge` pour recoller deux bases. La seule
opération correcte est un **remplacement**, précédé d'une **sauvegarde** et d'une **comparaison**.

Rappel de ce qui ne se reconstruit nulle part ailleurs : les **commentaires client**, les
**statuts relus à la main** (`valide`/`rejete`), les **dates de collecte** et les **marquages
d'opposition RGPD**. Les scores et les profils, eux, se recalculent depuis les CSV.

## État connu au départ (08/09/2026)

> **Mise à jour du 16/09/2026 — l'empreinte de départ ne vaut plus.** Le retour client du 11/09/2026 a été
> ré-importé sur le laptop : la base porte désormais **81 commentaires client** qui n'existent **nulle part
> ailleurs**. Le cas « rien à réconcilier » ci-dessous est **caduc** ; voir l'état à jour dans la section
> « Ce qui a été écrit sur le laptop ». Le poste principal, éteint, a toujours **0 commentaire client**.

Les deux bases étaient identiques au moment du départ :

| Mesure | Valeur au départ |
|---|---|
| Profils | **81** |
| Dernière `date_collecte` | **2026-08-26** |
| `statut_coordonnees` non vides | **20** (7 `valide`, 11 `rejete`, 2 `candidat`) |
| `PRAGMA user_version` | **2** |

Empreinte MD5 de `profils.db` au départ : `df1a7427c0db5aae23353ac0ad5a467f`.

Une sauvegarde datée du départ existe côté laptop dans
`C:\Users\HP\Documents\_backup_prospection\profils_20260908_laptop.db`.

**Si la base du laptop affiche encore exactement ces chiffres et cette empreinte, rien n'a été
écrit pendant le déplacement** : les deux copies sont identiques, il n'y a rien à réconcilier
côté données, et seules les étapes 1, 5 et 6 restent à faire.

## Ce qui a été écrit sur le laptop pendant l'itinérance

> **À compléter au fil des sessions du déplacement** — chaque session qui écrit dans le magasin
> ajoute une ligne ici. C'est cette liste qui rend la réconciliation vérifiable au lieu d'être
> une affaire de confiance.

| Date | Session / ticket | Écriture dans le magasin ? | Effet attendu sur les compteurs |
|---|---|---|---|
| 08/09/2026 | Onboarding itinérance + prise en compte du CR du 04/09 | **Non** — lecture seule | aucun |
| 08/09/2026 | POC-013 — livrable xlsx et ré-import | **Oui, puis annulée par restauration** | **aucun** — voir ci-dessous |
| 16/09/2026 | Ré-import du retour client du 11/09/2026 | **Oui — écriture réelle, conservée** | `commentaire_client` non vides : **0 → 81** ; tout le reste inchangé — voir ci-dessous |
| 19/09/2026 | Réponse au client (brouillon) + analyse du découpage géographique | **Non** — lecture seule | aucun — empreinte toujours `47b767d5…` |
| 05/10/2026 | **Fin d'itinérance** — inventaire de rapatriement | **Non** — lecture seule | aucun — **journal clos**, voir étape 0 |

**POC-013, détail de l'écriture et de son annulation.** Le critère d'acceptation du ticket
imposait un aller-retour sur le magasin réel : le livrable a été ouvert et annoté dans le **vrai
Excel**, puis ré-importé. Cela a écrit **5 cellules** (4 `commentaire_client` + le
`statut_coordonnees` d'Eric Fritsch passé à `rejete`), vérifiées ligne à ligne contre une
sauvegarde prise avant — **les 14 autres colonnes intactes sur les 81 profils**.

Ces 5 valeurs étaient des **données de test**, pas un retour client. Les laisser aurait envoyé à
Christophe et Henri-Pierre un fichier portant de faux commentaires à leur nom, et aurait mis un
verdict humain factice dans une colonne qui, depuis POC-009, ne doit contenir que des décisions
humaines réelles. **La base a donc été restaurée** depuis la sauvegarde
`profils_avant_POC013_20260908_090426.db` (décision utilisateur du 08/09/2026).

**Conséquence pour la réconciliation — ⚠ PÉRIMÉ, ne pas appliquer.** Ce paragraphe disait qu'après
POC-013 la base avait retrouvé son empreinte de départ, donc qu'il n'y avait rien à réconcilier.
C'était vrai le 08/09/2026 ; **ce n'est plus vrai depuis le ré-import du 16/09/2026**. Il reste ici
pour la traçabilité de POC-013. L'état qui fait foi est celui du **05/10/2026**, plus bas.

**Sauvegardes ajoutées pendant le déplacement**, dans
`C:\Users\HP\Documents\_backup_prospection\` :

| Fichier | Contenu |
|---|---|
| `profils_avant_POC013_20260908_090426.db` | état d'avant le ticket — **c'est celui qui a été remis en place** |
| `profils_magasin_avant_POC013_20260908_090426.csv` | l'export correspondant |
| `profils_apres_test_POC013_<horodatage>.db` | état d'après l'aller-retour de test, **conservé comme preuve**, à ne pas restaurer |

**Deux fichiers de données nouveaux à la racine du laptop**, tous deux gitignorés depuis ce
ticket et à traiter comme les CSV existants : `profils_magasin.xlsx` (le livrable client) et
`profils_magasin.reimport.csv` (la trace de conversion d'un ré-import). Ils se régénèrent depuis
le magasin, il n'y a rien à rapatrier à la main.

**Ré-import du retour client du 11/09/2026 (16/09/2026) — écriture réelle, à rapatrier.**
Christophe et Henri-Pierre ont renvoyé le classeur annoté
(`document/compte_rendu/profils_magasin_2026_09_11.xlsx`, mail du 11/09/2026). Il a été ré-importé
par `run_poc006` après sauvegarde, puis vérifié cellule par cellule contre cette sauvegarde :
**exactement 81 cellules modifiées, toutes dans `commentaire_client`**, aucune autre colonne, aucun
profil ajouté, `user_version` inchangé. `profils_magasin.csv` a été régénéré depuis la base.

**Ces 81 verdicts sont la donnée la plus précieuse du projet** — le premier jeu de référence
humain, sur lequel POC-014 mesure le scoring. **Perdre la base du laptop, c'est les perdre**, sauf
à ré-importer le classeur client, conservé dans `compte_rendu/`.

**État de la base du laptop au 16/09/2026** — c'est la référence à comparer au retour :

| Mesure | Valeur |
|---|---|
| Profils | **81** |
| Dernière `date_collecte` | **2026-08-26** |
| `statut_coordonnees` non vides | **20** (7 `valide`, 11 `rejete`, 2 `candidat`) — inchangé |
| `commentaire_client` non vides | **81** (0 au départ) |
| Oppositions `ne_plus_traiter` | **0** |
| `PRAGMA user_version` | **2** |
| Empreinte MD5 | `47b767d5acca659a29511933dfa8352f` |

**Conséquence pour la réconciliation** : à l'étape 2, le laptop doit afficher **commentaires=81**
et le poste principal **commentaires=0**, toutes les autres mesures égales. C'est le cas normal
« le laptop a avancé » : **remplacer**, en suivant les étapes 3 et 4. Si le poste principal
affiche autre chose que 0 commentaire, **arrêter** — l'hypothèse « poste éteint » est contredite.

**Sauvegarde ajoutée**, dans `C:\Users\HP\Documents\_backup_prospection\` :
`profils_avant_retour_client_20260916_180620.db` et
`profils_magasin_avant_retour_client_20260916_180620.csv` — l'état juste avant le ré-import.

**Fichier de données nouveau hors dépôt** : la trace de conversion
`profils_magasin_2026_09_11.reimport.csv`, écrite à côté du classeur client dans `compte_rendu/`.
Même traitement que les autres copies de données personnelles à l'étape 6.

**Vérifié de nouveau le 05/10/2026, en lecture seule, avant rapatriement** : 81 profils,
collecte 2026-08-26, 20 statuts, **81 commentaires**, 0 opposition, `user_version` 2, empreinte
`47b767d5acca659a29511933dfa8352f`. **Rien n'a bougé depuis le 16/09/2026** — POC-014 n'a pas été
lancé pendant le déplacement.

## Étape 0 — Les fichiers à rapatrier à la main (hors Git)

**Inventaire établi et vérifié sur le laptop le 05/10/2026.** Le code et la documentation
circulent par Git (étape 1). Tout ce qui suit n'y est **pas** et ne se rapatrie que physiquement.

> **Un lot de transfert a été préparé le 05/10/2026** et rassemble tout ce qui suit dans un seul
> dossier. Il a été constitué sur le laptop, dans
> `C:\Users\HP\Downloads\d_un_pas_decide-20260829T165329Z-1-001\d_un_pas_decide\`, puis **copié sur
> le drive** pour arriver ici : **demander à l'utilisateur le chemin du lot sur cette machine**
> (dossier du drive synchronisé, ou copie locale) avant de commencer, et ne rien supposer.
>
> **Première chose à lire, dans le lot : `RAPATRIEMENT.txt`.** Il redonne pour chaque fichier sa
> destination et son empreinte MD5. Les tableaux ci-dessous restent la référence ; le lot n'en est
> que l'emballage.
>
> **Ne pas recopier ce dossier tel quel dans le dépôt** : `compte_rendu\` va dans
> `d_un_pas_decide\document\compte_rendu\` — **sous `document\`, pas à la racine du dépôt** — et
> `_backup_prospection\` dans `D:\Documents\Dev\_backup_prospection\`, hors dépôt.
>
> **Si `.env.local` se trouve encore dans le lot** (il y était au 05/10/2026, identique à celui du
> poste principal) : **ne pas le copier dans le dépôt** — celui du poste principal fait foi — et
> signaler à l'utilisateur qu'une copie de la clé Brave traîne sur le drive, à effacer.

### A. Irremplaçable — à rapatrier impérativement

| Source (laptop) | Destination (poste principal) | Pourquoi |
|---|---|---|
| `profils.db` à la racine du dépôt — MD5 `47b767d5acca659a29511933dfa8352f` | racine du dépôt, même nom | **Les 81 verdicts client.** Ne se reconstruit pas, sauf à ré-importer le classeur ci-dessous. |
| `compte_rendu\2026 09 11 - mail Christophe.pdf` | `d_un_pas_decide\document\compte_rendu\` | La réponse du client : la grille de profilage à 4 niveaux, en version originale. |
| `compte_rendu\profils_magasin_2026_09_11.xlsx` | `d_un_pas_decide\document\compte_rendu\` | **Le classeur annoté par le client** — la seule copie des 81 verdicts hors de la base. |
| `compte_rendu\2026 09 04 - CR call.pdf` | `d_un_pas_decide\document\compte_rendu\` | Le compte rendu du call qui a ouvert POC-013 et mandaté POC-008. |
| `compte_rendu\2026 09 08 - brouillon mail Michel - livraison tableau Excel.md` | `d_un_pas_decide\document\compte_rendu\` | Brouillon de la livraison. |
| `compte_rendu\2026 09 09 - mail Michel - livraison tableau Excel (a coller dans Outlook).txt` et `.html` | `d_un_pas_decide\document\compte_rendu\` | Le mail **effectivement envoyé** le 09/09/2026. |
| `compte_rendu\2026 09 19 - brouillon mail Michel - reponse retour du 11-09 (a coller dans Outlook).txt` | `d_un_pas_decide\document\compte_rendu\` | **Réponse rédigée, non envoyée** — à relire et envoyer. |
| `compte_rendu\profils_magasin_2026_09_11.reimport.csv` | `d_un_pas_decide\document\compte_rendu\` | Trace de conversion du ré-import ; utile si le ré-import doit être rejoué. |
| `C:\Users\HP\Documents\_backup_prospection\profils_avant_retour_client_20260916_180620.db` (+ le `.csv` du même horodatage) | `D:\Documents\Dev\_backup_prospection\` | **Point de retour arrière** : l'état juste avant le ré-import des verdicts. |

> ⚠ **Piège de chemin** : sur le laptop, les comptes rendus ne sont **pas** dans le dépôt. Ils sont
> dans `C:\Users\HP\Downloads\d_un_pas_decide-20260829T165329Z-1-001\d_un_pas_decide\compte_rendu\`.
> Sur le poste principal, leur place est `d_un_pas_decide\document\compte_rendu\` (gitignoré),
> **sous `document\`** — confirmé par l'utilisateur le 05/10/2026. Les quatre pièces
> antérieures au départ (les 3 PDF de juillet et le brouillon du 28/08) y sont déjà : **ne pas les
> écraser par mégarde**, seules les pièces listées ci-dessus sont nouvelles.

### B. Utile mais régénérable — copier si pratique, sinon reconstruire

| Fichier (racine du dépôt laptop) | Comment le reconstruire |
|---|---|
| `profils_magasin.csv` — MD5 `78377abefc59593adccc13585e70e62f` | export depuis la base |
| `profils_magasin.xlsx` — MD5 `f84325f91255c24550dc1b974f7102eb` | `python -m source.backend.adapters.storage.run_poc013` |
| `profils_magasin.reimport.csv` | trace du dernier ré-import, recréée au prochain |
| les autres sauvegardes de `_backup_prospection\` (POC-013, départ) | conservées comme preuves, aucune à restaurer |

**Les reconstruire suppose que la base soit déjà en place** : rapatrier `profils.db` d'abord.

### C. À ne surtout PAS rapatrier

- **`.env.local`** — contient la clé Brave. Le poste principal a déjà le sien ; recopier un secret
  d'une machine à l'autre n'apporte rien et multiplie les copies.
- **`.venv\`, `__pycache__\`, `.pytest_cache\`** — reconstruits par `uv sync` (étape 1).
- **`browser_profile\`** — n'a **jamais** été copié sur le laptop, et ne devait pas l'être. La
  session LinkedIn du poste principal est intacte.
- **`profils_extraits*.csv` et le `.bak`** — venus du poste principal au départ, **plus jamais
  écrits depuis POC-009**. Les originaux sont déjà là-bas.

### Contrôle avant de passer à la suite

Après copie, vérifier l'empreinte de la base **sur le poste principal** :

```powershell
Get-FileHash profils.db -Algorithm MD5
```

Elle doit valoir `47B767D5ACCA659A29511933DFA8352F`. Si elle diffère, **s'arrêter** : la copie a
échoué ou le fichier a été ouvert entre-temps.

## Étape 1 — Récupérer le code et la documentation

Le code et les documents ont circulé par Git, pas à la main. **Vérifié le 05/10/2026 : tout le
travail d'itinérance est poussé sur `origin/master`, jusqu'au commit `a926989` inclus.** Un
`git pull` suffit donc, il n'y a rien à récupérer autrement.

```powershell
git status --short
git branch --show-current
git pull
git log --oneline -15
```

Vérifier ensuite que l'environnement suit le code rapatrié — le déplacement a pu ajouter des
dépendances (POC-013 en ajoute une pour l'Excel) :

```powershell
uv sync --extra test
uv run --extra test pytest tests/ -q
```

Le nombre de tests attendu est **143** (dernier ticket DONE : POC-013 ; `task_list.md` fait foi).
`uv sync` est **nécessaire** : POC-013 a ajouté `openpyxl`, absent du poste principal.

## Étape 2 — Comparer les deux bases AVANT de toucher à quoi que ce soit

Ne rien écraser sans avoir regardé. Rendre le laptop accessible (clé USB, partage réseau), puis
comparer les deux fichiers **en lecture seule**, sans jamais passer par `ouvrir_magasin` — qui
créerait un magasin vide si un chemin était faux, et masquerait l'erreur au lieu de la révéler.

```powershell
uv run python -c "import sqlite3,sys
for nom, chemin in (('POSTE', 'profils.db'), ('LAPTOP', r'E:\profils.db')):
    c = sqlite3.connect(f'file:{chemin}?mode=ro', uri=True)
    n = c.execute('select count(*) from profils').fetchone()[0]
    d = c.execute('select max(date_collecte) from profils').fetchone()[0]
    s = c.execute(\"select count(*) from profils where coalesce(statut_coordonnees,'')<>''\").fetchone()[0]
    v = c.execute('pragma user_version').fetchone()[0]
    cm = c.execute(\"select count(*) from profils where coalesce(commentaire_client,'')<>''\").fetchone()[0]
    op = c.execute('select count(*) from profils where ne_plus_traiter').fetchone()[0]
    print(f'{nom:7} profils={n} collecte={d} statuts={s} commentaires={cm} oppositions={op} v={v}')"
```

Adapter le chemin du laptop. Lecture attendue :

- **LAPTOP ≥ POSTE sur toutes les mesures** → cas normal, le laptop a avancé : continuer.
- **Chiffres identiques** → rien n'a été écrit pendant le déplacement : il n'y a **rien à
  remplacer**, passer directement à l'étape 5.
- **POSTE > LAPTOP sur une mesure** → **arrêter**. Cela contredit l'hypothèse « poste éteint ».
  Ne rien écraser, le signaler à l'utilisateur, et instruire l'écart avant toute décision. C'est
  le seul cas où la réconciliation n'est pas une simple copie.

## Étape 3 — Sauvegarder la base du poste principal

**Avant** de la remplacer, et même si elle est réputée périmée. Écraser d'abord et constater
ensuite est irréversible.

```powershell
Copy-Item profils.db "D:\Documents\Dev\_backup_prospection\profils_AVANT_retour_$(Get-Date -Format 'yyyyMMdd').db"
Get-ChildItem "D:\Documents\Dev\_backup_prospection\"
```

Sauvegarder également `profils_magasin.csv` de la même façon.

## Étape 4 — Remplacer, puis vérifier que le remplacement a pris

Copier la base du laptop **par-dessus** celle du poste principal, à la racine du dépôt, sous le
nom `profils.db` — c'est le chemin qu'attend le code : [Code] `DEFAULT_DB_PATH = Path("./profils.db")`
dans `source/backend/adapters/storage/profile_store.py`, relatif au répertoire courant.

Rejouer ensuite **la requête de comparaison de l'étape 2** sur le seul poste principal et
vérifier qu'il affiche désormais **les chiffres du laptop**. Une copie qui échoue
silencieusement est un scénario réel : le magasin n'aurait aucun moyen de le signaler.

Rapatrier ensuite le reste de l'**étape 0** — les comptes rendus et le classeur annoté avant tout,
puis les exports si on ne veut pas les régénérer. Se souvenir que **la base fait foi, pas le CSV** :
un export figé au milieu d'une relecture a déjà annoncé 1 contact validé au lieu de 7 (28/08/2026).

## Étape 5 — Reprendre le rythme normal

- `browser_profile/` : **n'a jamais été copié sur le laptop**, et ne devait pas l'être. La
  session LinkedIn du poste principal est intacte, il n'y a rien à restaurer ni à nettoyer.
- **Prochain ticket : POC-014** (scoring v2 sur le titre, mesuré contre la grille client). Il est
  hors-ligne, il peut démarrer dès que la base est en place. Prompt prêt dans
  `document/prompts_plans/prompt_POC-014.md`.
- Les tickets qui exigent un run LinkedIn réel redeviennent possibles : **POC-016** (extraction
  « Expérience » et « Infos », le levier identifié par le retour client), **POC-008** et **POC-010**.
  Attention : le mandat **géographique** de POC-008 est tombé le 11/09/2026 (le client juge la
  géographie accessoire) ; ce qui reste est le **découpage** par région comme moyen d'accès au
  gisement, et sa priorité est à réexaminer (voir `Backlog.md`, POC-008).
- **Un mail attend d'être envoyé** : la réponse du 19/09/2026 au retour client, rapatriée à
  l'étape 0.
- Vérifier `playwright install chromium` si le navigateur a bougé.

## Étape 6 — Effacer les données personnelles du laptop

Le magasin et les CSV contiennent des **profils réels**. Une fois la réconciliation vérifiée —
et seulement à ce moment — supprimer du laptop :

- `profils.db`, `profils_magasin.csv`, `profils_magasin.xlsx`, `profils_magasin.reimport.csv` et
  les `profils_extraits*.csv` à la racine du dépôt laptop ;
- `C:\Users\HP\Documents\_backup_prospection\` en entier (7 fichiers, sauvegardes du déplacement) ;
- le dossier de comptes rendus du laptop,
  `C:\Users\HP\Downloads\d_un_pas_decide-20260829T165329Z-1-001\` — il contient le classeur
  annoté et la correspondance client ;
- `.env.local` si le laptop ne doit plus servir au projet (il porte la clé Brave).

Ne pas faire ce ménage avant que l'étape 4 soit vérifiée : tant que la copie du poste principal
n'est pas confirmée bonne, celle du laptop reste la seule qui vaille.

## Contraintes qui ne changent pas

- Pas de `git reset --hard`, pas de checkout destructif, pas d'amend, pas de force push.
- Pas de migration de schéma sans plan validé et backup explicite.
- Réponses en français, commentaires de code en anglais (`AGENTS.md`).
- Obligation de fin de session inchangée : `task_list.md`, `handoff.md`, `Backlog.md`, `CLAUDE.md`.
