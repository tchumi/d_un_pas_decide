Tu reprends la conversation de **suivi de projet** ProspectionLinkedIn sur une machine
secondaire (ex : laptop en déplacement). Ce n'est pas une session de ticket au sens de
`prompt_générique.md` — c'est la reprise du rôle "copilote de projet" : suivi du backlog,
cadrage de tickets, rédaction de communication client, décisions d'architecture/outillage,
logistique d'environnement. Pas de `/clear` préalable requis pour ce prompt : au contraire,
il sert justement à reconstituer le contexte sur une machine qui n'a pas l'historique de
conversation.

## Ce qui a changé de machine

Le code et la documentation sont dans le dépôt Git (`origin` = GitHub privé), donc à jour
dès `git pull`/`git clone`. En revanche, **rien de ce qui suit ne se synchronise via Git**
(volontairement, voir `.gitignore`) et doit être vérifié/recréé localement sur cette
machine :

- `.env.local` — notamment `BRAVE_SEARCH_API_KEY` (les identifiants LinkedIn y restent
  vides, le login est manuel, voir décisions POC-001 dans `Backlog.md`).
- `browser_profile/` — session Playwright/cookies LinkedIn. **Ne pas copier ce dossier
  d'une machine à l'autre** : un même cookie de session apparaissant depuis une nouvelle
  localisation ressemble à un vol de session pour les systèmes anti-fraude de LinkedIn.
  Préférer une connexion manuelle fraîche sur cette machine si un run réel est nécessaire,
  et naviguer normalement quelques instants avant de lancer le moindre script.
- Les CSV de profils (`profils_extraits*.csv`) — données personnelles, à ne recopier
  qu'en cas de besoin réel et en quantité minimale.
- Le binaire navigateur Playwright (`playwright install chromium`) — distinct de
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

Si le dépôt n'est pas encore cloné sur cette machine :
```powershell
git clone https://github.com/tchumi/d_un_pas_decide.git
uv sync --extra test
playwright install chromium
```

## Étape 2 — Lecture pour reprendre le contexte

Lire, dans cet ordre, **et rien d'autre** au démarrage :

1. `CLAUDE.md`
2. `document/claude_code/AGENTS.md`
3. `document/claude_code/handoff.md` — en entier (état du sprint)
4. `document/claude_code/task_list.md` — en entier (statuts de tous les tickets)
5. `document/Backlog.md` — en entier (specs, décisions, garde-fous RGPD, tickets en stub)

Ne pas lire le reste du code source à ce stade — seulement si un ticket précis
l'exige ensuite.

## Étape 3 — Première réponse attendue

Ne modifie aucun fichier. Réponds avec :

1. Résultat de la vérification d'environnement (Étape 1) — signaler explicitement tout
   élément manquant (`.env.local`, navigateur Playwright) sans bloquer la conversation
   pour autant.
2. Un point d'étape façon "faisons le point" : tickets `DONE`/`BLOCKED`/`TODO` en cours,
   dernière décision notable, prochain ticket recommandé.
3. Une question ouverte : qu'est-ce que l'utilisateur veut traiter dans cette session —
   cadrage d'un nouveau ticket, suite d'un ticket existant, travail sur la logique pure
   (sans toucher LinkedIn), ou autre chose ?

## Contraintes qui restent valables sur cette machine

- Mêmes règles Git que d'habitude : pas de `reset --hard`, pas de checkout destructif,
  pas d'amend, pas de force push.
- Plan court avant toute modification non triviale (comme d'habitude).
- Pendant un déplacement, privilégier le travail qui ne nécessite ni session LinkedIn ni
  vraie clé API (logique pure, tests unitaires, cadrage de tickets, documentation) — pas
  une règle absolue, mais le fil par défaut tant qu'il n'y a pas de raison explicite de
  faire un run réel depuis cette machine.
- Réponses en français, commentaires de code en anglais, comme dans `AGENTS.md`.
