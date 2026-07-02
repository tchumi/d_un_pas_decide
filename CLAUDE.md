# CLAUDE.md — ProspectionLinkedIn

## Objectif du projet

POC d'automatisation de la prospection de coachs business sur LinkedIn (recherche,
extraction, scoring/catégorisation de profils) pour D'un Pas Décidé.
Stack : Python ≥ 3.12, Streamlit, Playwright, SQLite, pandas.

## Structure du repository

```
source/
  main.py                    # point d'entrée Streamlit (streamlit run)
  frontend_streamlit/        # pages/composants Streamlit (présentation uniquement)
  backend/
    core/                    # scoring, catégorisation, modèles métier — zéro import Streamlit
    adapters/
      scraping/               # Playwright, sélecteurs CSS LinkedIn centralisés, session
      storage/                # SQLite / export CSV
tests/
  unit/    integration/    e2e/
document/
  Backlog.md                 # référentiel de specs (ne pas y mettre les statuts)
  ARCHITECTURE.md
  claude_code/               # kit gouvernance : AGENTS.md, handoff.md, task_list.md…
```

## État actuel (02/07/2026)

- Branche active : `master` (base `master`)
- Tests : 0 passants, 0 échecs, 0 skipped
- Prochain ticket actif : POC-001

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

Mettre à jour **les trois fichiers** à la fin de chaque session :

1. `document/claude_code/task_list.md` — statut du ticket → DONE (ou DECIDED/BLOCKED)
2. `document/claude_code/handoff.md` — ce qui a été fait, fichiers modifiés, prochain ticket
3. **`document/Backlog.md`** — **obligatoire si** : nouveau ticket créé, périmètre modifié, critères d'acceptation changés, décision prise. Ne pas y mettre les statuts.

La session n'est pas considérée comme terminée sans ces trois mises à jour.
Commit final : `git commit -m "docs: [ID_TICKET] DONE — description courte"`.

Indiquer explicitement si le lancement de l'application est nécessaire avant de passer au ticket suivant :
- **Oui** si : un module existant a été modifié, une feature UI touchée, un service ou route API change de comportement.
- **Non** si : seuls des fichiers nouveaux sans appelant ont été créés, des tests ajoutés, ou de la documentation mise à jour.

Proposer le prompt du prochain ticket en remplissant les placeholders de `document/claude_code/prompt_générique.md`. Le sauvegarder dans `document/prompts_plans/prompt_[ID_TICKET].md` et committer.

## Commandes essentielles

```powershell
uv sync --extra test                        # installation
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
