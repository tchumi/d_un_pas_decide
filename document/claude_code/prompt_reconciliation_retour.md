# Prompt de réconciliation au retour — du laptop vers le poste principal

> À coller sur le **poste principal**, au retour d'itinérance, **avant tout autre travail**.
> Rédigé le 08/09/2026 depuis le laptop, au départ de l'itinérance.
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

**Conséquence pour la réconciliation : `profils.db` vaut de nouveau
`df1a7427c0db5aae23353ac0ad5a467f`, l'empreinte de départ.** Si elle est toujours celle-là au
retour, **il n'y a rien à réconcilier côté données** — seuls le code et la documentation ont
changé, et ils circulent par Git.

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

**Mettre à jour cette section et l'empreinte à chaque nouvelle écriture** (re-scoring de POC-014,
en particulier).

## Étape 1 — Récupérer le code et la documentation

Le code et les documents ont circulé par Git, pas à la main.

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

Le nombre de tests attendu est dans `task_list.md`, ligne du dernier ticket DONE.

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

Rapatrier aussi les CSV du laptop (`profils_magasin.csv` en particulier), et se souvenir que
**la base fait foi, pas le CSV** : un export figé au milieu d'une relecture a déjà annoncé
1 contact validé au lieu de 7 (28/08/2026).

## Étape 5 — Reprendre le rythme normal

- `browser_profile/` : **n'a jamais été copié sur le laptop**, et ne devait pas l'être. La
  session LinkedIn du poste principal est intacte, il n'y a rien à restaurer ni à nettoyer.
- Les tickets qui exigent un run LinkedIn réel redeviennent possibles : **POC-008** (requêtes
  ciblées et filtre géographique, désormais mandaté par le client — points d'action 2 et 4 du
  call du 04/09/2026) et **POC-010**.
- Vérifier `playwright install chromium` si le navigateur a bougé.

## Étape 6 — Effacer les données personnelles du laptop

Le magasin et les CSV contiennent des **profils réels**. Une fois la réconciliation vérifiée —
et seulement à ce moment — supprimer du laptop :

- `profils.db` et les CSV de profils à la racine du dépôt ;
- `C:\Users\HP\Documents\_backup_prospection\` (sauvegardes du déplacement) ;
- la copie des comptes rendus client si elle n'a plus lieu d'être.

Ne pas faire ce ménage avant que l'étape 4 soit vérifiée : tant que la copie du poste principal
n'est pas confirmée bonne, celle du laptop reste la seule qui vaille.

## Contraintes qui ne changent pas

- Pas de `git reset --hard`, pas de checkout destructif, pas d'amend, pas de force push.
- Pas de migration de schéma sans plan validé et backup explicite.
- Réponses en français, commentaires de code en anglais (`AGENTS.md`).
- Obligation de fin de session inchangée : `task_list.md`, `handoff.md`, `Backlog.md`, `CLAUDE.md`.
