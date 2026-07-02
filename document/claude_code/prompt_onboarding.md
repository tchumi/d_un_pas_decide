Tu travailles dans un projet Python/PyQt6 qui vient d'être créé depuis le template
`claude-project-template`. Les fichiers de gouvernance contiennent des placeholders
`[EN_MAJUSCULES]` à remplir.

Ce prompt est utilisé **une seule fois**, au démarrage du projet.
Pour les tickets suivants, utiliser `document/claude_code/prompt_générique.md`.

---

## Objectif

Remplir tous les placeholders dans les fichiers de gouvernance et faire un commit
initial propre, sans toucher au code source.

## Étape 1 — Collecte d'informations (avant toute modification)

Pose ces questions à l'utilisateur en une seule réponse groupée.
Ne pas modifier de fichier avant d'avoir reçu toutes les réponses.

**Questions obligatoires :**

1. **Nom du projet** (ex: `Opto`, `MonApp`) ?
2. **Description courte** en une phrase (ex: "Application desktop de gestion de portefeuille") ?
3. **Stack complémentaire** au-delà de Python ≥ 3.12 + PyQt6
   (ex: SQLAlchemy ≥ 1.4, FastAPI, Alembic, piecash — ou "aucune pour l'instant") ?
4. **Arborescence `source/`** — décrire les sous-dossiers principaux prévus
   (ex: `frontend_qt/`, `backend/core/`, `backend/adapters/`) ?
5. **Préfixes de tickets** — un par domaine fonctionnel
   (ex: `MGD` pour gouvernance/docs, `LDG` pour ledger, `BUG` pour bugs) ?
6. **Fichiers sensibles à ne jamais exposer** (extensions, ex: `.db`, `.gnucash`, `.key`) ?
7. **Variables d'environnement** connues dès maintenant
   (ex: `APP_DB_PATH`, `API_KEY` — ou "aucune pour l'instant") ?
8. **Branche de base** (défaut : `main`) ?
9. **Premier ticket prévu** — ID + titre court (ex: `MGD-001 — Vérifier collecte pytest`) ?

---

## Étape 2 — Remplissage des placeholders

Après validation des réponses, remplir dans cet ordre :

### 2a. `CLAUDE.md`
Remplacer :
- `[PROJECT_NAME]` → nom du projet
- `[PROJECT_DESCRIPTION]` → description courte
- `[AUTRES_DEPENDANCES_CLÉS]` → stack complémentaire
- `[COLLER_ICI_L_ARBORESCENCE...]` → arborescence `source/` réelle
- `[DATE_JJ_MM_AAAA]` → date du jour
- `[BRANCHE_ACTIVE]` et `[BRANCHE_BASE]` → branche de base
- `[EXTENSIONS_FICHIERS_SENSIBLES]` → extensions sensibles
- `[ID_TICKET_SUIVANT]` → premier ticket

### 2b. `document/claude_code/AGENTS.md`
Remplacer :
- `[PROJECT_NAME]`, `[PROJECT_DESCRIPTION]`, `[BRANCHE_BASE]`
- `[VAR_ENV_x]` → variables d'environnement (ou supprimer la section si aucune)

### 2c. `document/ARCHITECTURE.md`
Remplir :
- Stack technique (tableau)
- Arborescence réelle
- Contraintes connues dès maintenant (laisser le reste vide)

### 2d. `document/Backlog.md`
Remplir :
- `[PROJECT_NAME]`
- Tableau des préfixes de tickets
- Section du premier ticket (ID, titre, objectif, critère d'acceptation à définir ensemble)

### 2e. `document/claude_code/task_list.md`
Remplacer la ligne exemple par le premier ticket réel :
```
| [PREFIX]-001 | TODO | P1 | [Module] | [Titre] | [Critère] |
```

### 2f. `document/claude_code/handoff.md`
Mettre à jour la section 1 avec la date réelle et le premier ticket.

### 2g. `document/claude_code/prompt_générique.md`
Remplacer `[PROJECT_NAME]` dans la première ligne.

### 2h. `.claude/memory/MEMORY.md`
Remplacer `[PROJECT_NAME]`.

---

## Étape 3 — Vérification

Après toutes les modifications, vérifier qu'il ne reste aucun placeholder :

```powershell
Select-String -Path "CLAUDE.md","document\claude_code\AGENTS.md","document\claude_code\task_list.md","document\claude_code\handoff.md","document\Backlog.md","document\ARCHITECTURE.md" -Pattern "\[EN_MAJUSCULES\]|\[PROJECT" | Select-Object Filename, LineNumber, Line
```

Si des occurrences résiduelles apparaissent, les corriger avant de committer.

---

## Étape 4 — Commit initial

```powershell
git add CLAUDE.md document/ .claude/memory/MEMORY.md
git status --short
```

Vérifier que seuls les fichiers de gouvernance sont staged (pas de fichiers source).

```powershell
git commit -m "docs: init gouvernance [PROJECT_NAME] depuis claude-project-template"
```

---

## Livrable attendu

À l'issue de ce prompt :
- Zéro placeholder `[...]` résiduel dans les fichiers de gouvernance.
- `document/claude_code/task_list.md` contient le premier ticket réel.
- `document/Backlog.md` contient la section du premier ticket avec critère d'acceptation.
- Commit de gouvernance initial présent dans `git log`.
- Instruction finale : "Ce prompt est consommé. Utiliser `prompt_générique.md` pour chaque ticket suivant."
