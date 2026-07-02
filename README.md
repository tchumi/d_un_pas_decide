# claude-project-template

Squelette de gouvernance Claude Code pour projets Python/PyQt6.
Cloner ce repo, remplir les placeholders, commencer à développer.

---

## Utilisation

### 1. Cloner comme template GitHub

Sur GitHub : **Use this template → Create a new repository**.
Ou manuellement :
```bash
git clone https://github.com/[TON_USER]/claude-project-template.git mon-projet
cd mon-projet
rm -rf .git
git init && git add . && git commit -m "chore: init from claude-project-template"
```

### 2. Laisser Claude remplir les placeholders (recommandé)

Ouvrir VS Code dans le repo cloné, puis dans Claude Code :

```
/clear
[coller le contenu de document/claude_code/prompt_onboarding.md]
```

Claude posera 9 questions groupées, remplira tous les fichiers et committera.
**Ce prompt est à usage unique** — ne l'utiliser qu'une seule fois au démarrage.

> **Alternative manuelle** : rechercher `[` dans tous les fichiers.
> Ordre : `CLAUDE.md` (8 placeholders) → `AGENTS.md` (4) → `ARCHITECTURE.md` → `Backlog.md` → `task_list.md` → `handoff.md` → `prompt_générique.md` → `.claude/memory/MEMORY.md`.

### 3. Configurer Claude Code

Dans VS Code avec l'extension Claude Code :
- Vérifier que `CLAUDE.md` est à la racine du repo (détection automatique).
- Le dossier `.claude/memory/` est lié à l'utilisateur OS — le chemin mémoire dans les settings Claude Code pointe vers `C:\Users\[USER]\.claude\projects\[REPO_PATH]\memory\`.

### 4. Premier ticket

```powershell
uv init           # si pas encore de pyproject.toml
uv add pyqt6      # dépendances de base
```

Ouvrir `document/claude_code/task_list.md`, créer le ticket `[PREFIX]-001`.
Remplir `document/claude_code/prompt_générique.md` avec les placeholders du ticket.
Dans VS Code : `/clear` puis coller le prompt rempli.

---

## Structure des fichiers de gouvernance

```
CLAUDE.md                              ← instructions principales pour Claude
document/
  claude_code/
    AGENTS.md                          ← règles détaillées + conventions
    task_list.md                       ← statuts courants (source de vérité)
    handoff.md                         ← notes de session / état du sprint
    prompt_onboarding.md               ← prompt unique de démarrage (1 seule utilisation)
    prompt_générique.md                ← template prompt par ticket
  prompts_plans/
    prompt_[ID].md                     ← prompt sauvegardé par ticket
    plan_[ID].md                       ← plan validé par ticket
  Backlog.md                           ← specs (pas de statuts ici)
  ARCHITECTURE.md                      ← structure réelle du projet
.claude/
  memory/
    MEMORY.md                          ← index mémoire persistante
```

## Protocole de session (rappel)

1. `/clear` en début de chaque nouveau ticket
2. Coller le prompt de `document/prompts_plans/prompt_[ID].md`
3. Claude lit les fichiers listés, propose un plan, attend validation
4. Implémentation par étapes validées
5. Fin de session : mettre à jour `task_list.md` + `handoff.md` + `Backlog.md` + commit

---

## Adapté depuis

[Opto](https://github.com/[TON_USER]/Opto) — gouvernance Claude Code stabilisée juin/juillet 2026.
