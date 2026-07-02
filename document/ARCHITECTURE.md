# ARCHITECTURE.md — [PROJECT_NAME]

> Dernière mise à jour : [DATE]

## Stack technique

| Composant | Technologie | Version |
|---|---|---|
| UI desktop | PyQt6 | ≥ 6.4 |
| Base de données | [SQLite / PostgreSQL] | — |
| ORM | [SQLAlchemy] | [≥ x.x] |
| Migration schéma | [Alembic] | — |
| API interne | [FastAPI / N/A] | — |
| Gestionnaire de paquets | uv | — |

## Arborescence réelle

```
source/
  main.py
  frontend_qt/
    main_window.py
    pages/
    widgets/
    dialogs/
  backend/
    core/
      models/        # dataclasses métier
      services/      # services purs (pas de PyQt6, pas d'ORM direct)
    adapters/
      database/      # engine, models ORM, migrations Alembic
      workspace/     # WorkspaceManager
tests/
  unit/
  integration/
  e2e/
document/
  claude_code/
  prompts_plans/
```

## Modules actifs

| Module | Chemin | Rôle |
|---|---|---|
| [Nom] | `source/[chemin]/` | [Description courte] |

## Contraintes d'architecture

- Zéro import PyQt6 dans `backend/core/` et `backend/adapters/`.
- Les services `core/` sont testables sans Qt (pytest sans event loop).
- [Autres contraintes projet]

## Décisions d'architecture

| Date | Décision | Alternatives rejetées |
|---|---|---|
| [Date] | [Décision] | [Alternative] |
