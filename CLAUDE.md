# CLAUDE.md — ProspectionLinkedIn

## Objectif du projet

POC d'automatisation de la prospection de coachs business sur LinkedIn (recherche,
extraction, scoring/catégorisation de profils) pour D'un Pas Décidé.
Stack : Python ≥ 3.12, Streamlit, Playwright, SQLite, pandas.

## Structure du repository

Structure **visée**. Les entrées marquées `(à créer)` n'existent pas encore : le POC est
aujourd'hui piloté par des scripts `run_pocXXX.py` lancés en ligne de commande, sans UI.

```
config/
  scoring_rules.json         # règles de scoring POC-003, éditables (chargées par core/)
source/
  main.py                    # (à créer) point d'entrée Streamlit (streamlit run)
  frontend_streamlit/        # (à créer) pages/composants Streamlit (présentation uniquement)
  backend/
    core/                    # scoring, catégorisation, modèles métier — zéro import Streamlit
    adapters/
      scraping/               # Playwright, sélecteurs CSS LinkedIn centralisés, session
      storage/                # magasin SQLite persistant (POC-006) + export CSV
      enrichment/             # recherche web + extraction de coordonnées (POC-004)
tests/
  unit/    integration/    e2e/
document/
  Backlog.md                 # référentiel de specs (ne pas y mettre les statuts)
  ARCHITECTURE.md
  claude_code/               # kit gouvernance : AGENTS.md, handoff.md, task_list.md…
  prompts_plans/             # prompts et plans validés, un par ticket
```

## État actuel

- Branche active : `master` (base `master`)
- **Dernière session** : POC-006 — renouvellement du gisement de profils (26/08/2026)
- **Prochain ticket actif** : POC-007 — revalidation des règles de scoring sur le lot frais

Ces deux lignes sont les **seules** informations volatiles de ce fichier : elles se mettent à
jour en fin de session (voir « Obligation de fin de session »). Tout le reste — statuts,
métriques, nombre de tests — vit dans `document/claude_code/task_list.md`, qui en est la
**source de vérité unique** ; ne pas le recopier ici, c'est ce qui avait fait dériver cette
section.

## Méthode de travail par ticket

Avant chaque nouveau ticket :

1. L'utilisateur fait `/clear` pour repartir avec un contexte propre.
2. L'utilisateur remplit et colle le prompt `document/claude_code/prompt_générique.md` (placeholders `[ID_TICKET]`, `[TITRE_COURT]`, etc.).
3. L'agent lit les fichiers listés dans le prompt **et rien d'autre** avant de proposer un plan.

Ne jamais démarrer un ticket sans ce protocole si le contexte courant contient déjà plusieurs sessions.

## Règles non négociables

1. **Lire avant modifier** : lire le fichier cible + ses appelants avant toute modification.
2. **Plan d'abord** : proposer un plan court avant toute modification non triviale. Après validation, sauvegarder le plan dans `document/prompts_plans/plan_[ID_TICKET].md` et faire un commit : `git commit -m "docs: [ID_TICKET] plan — description courte"`.
3. **Pas de destructif** : pas de `git reset --hard`, pas de checkout destructif, pas de suppression de fichiers.
4. **Pas de secrets** : ne jamais exposer `.env`, `.env.local`, clés API, mots de passe, identifiants LinkedIn (`LINKEDIN_EMAIL`/`LINKEDIN_PASSWORD`), fichiers `.db`/`.sqlite`, session Playwright (ex: `storage_state.json`).
5. **Pas de migration schema sans plan validé et backup explicite**.
6. **Lancer l'UI uniquement via `streamlit run`** (ne jamais lancer les scripts de scraping/scoring en important Streamlit ailleurs) :
   ```powershell
   streamlit run source/main.py
   ```

## Obligation de fin de session

Mettre à jour **les quatre fichiers** à la fin de chaque session :

1. `document/claude_code/task_list.md` — statut du ticket → DONE (ou DECIDED/BLOCKED), **avec les métriques (nb tests)** : ce fichier en est la source de vérité unique.
2. `document/claude_code/handoff.md` — ce qui a été fait, fichiers modifiés, prochain ticket
3. **`document/Backlog.md`** — **obligatoire si** : nouveau ticket créé, périmètre modifié, critères d'acceptation changés, décision prise. Ne pas y mettre les statuts.
4. **`CLAUDE.md`** — section « État actuel » : dernière session (ID + date) et prochain ticket actif. **Deux lignes, rien d'autre** : ne jamais y recopier de métrique ni de statut, sous peine de la dérive que cette règle corrige. Mettre aussi à jour la section « Structure du repository » si un dossier a été créé ou est passé de `(à créer)` à réel.

La session n'est pas considérée comme terminée sans ces quatre mises à jour.
Commit final : `git commit -m "docs: [ID_TICKET] DONE — description courte"`.

Indiquer explicitement si le lancement de l'application est nécessaire avant de passer au ticket suivant :
- **Oui** si : un module existant a été modifié, une feature UI touchée, un service ou route API change de comportement.
- **Non** si : seuls des fichiers nouveaux sans appelant ont été créés, des tests ajoutés, ou de la documentation mise à jour.

Proposer le prompt du prochain ticket en remplissant les placeholders de `document/claude_code/prompt_générique.md`. Le sauvegarder dans `document/prompts_plans/prompt_[ID_TICKET].md` et committer.

## Commandes essentielles

```powershell
uv sync --extra test                        # installation
playwright install chromium                 # navigateur Playwright (une fois par machine)
streamlit run source\main.py                # lancement UI
pytest tests/ -v                            # tous les tests
pytest tests/unit/ -v                       # tests unitaires seuls
```

## Documentation de référence

- `document/claude_code/task_list.md` — **source de vérité courante** (tous tickets)
- `document/claude_code/handoff.md` — état du sprint en cours
- `document/claude_code/AGENTS.md` — règles détaillées, conventions, variables d'environnement
- `document/Backlog.md` — référentiel de specs complet ; ne pas y mettre les statuts
- `document/ARCHITECTURE.md` — structure réelle du projet

Ne pas lire tout le repository sans demande explicite.
