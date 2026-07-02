# Backlog — ProspectionLinkedIn

<!--
Ce fichier est le référentiel de SPECS, pas de statuts.
- Les statuts courants sont dans document/claude_code/task_list.md.
- Ajouter une section ici pour chaque nouveau ticket (specs, critères, décisions).
- Ne pas supprimer les sections des tickets terminés : elles servent d'historique.
-->

## Convention de nommage des tickets

| Préfixe | Domaine |
|---|---|
| POC- | Recherche/extraction/scoring/catégorisation — cœur du pipeline POC |
| UI- | Interface Streamlit |
| BUG- | Bugs identifiés en test ou prod |

---

## POC-001 — Script de recherche + extraction basique de profils LinkedIn

**Objectif** : Valider que le scraping LinkedIn via Playwright permet de rechercher des
profils selon une requête booléenne définie manuellement, et d'extraire de façon fiable
nom, URL LinkedIn, localisation et titre/résumé — sur un petit lot de test, sans
déclencher de blocage ou restriction du compte. L'email est explicitement hors scope
de ce ticket (voir décisions).

**Critères d'acceptation** :
- [ ] Script fonctionnel qui extrait au moins 20-25 profils cohérents sur une requête booléenne donnée
- [ ] Aucun blocage/restriction du compte LinkedIn constaté pendant les tests
- [ ] Sélecteurs CSS LinkedIn documentés et isolés dans un module dédié (facilite la maintenance si le DOM change)
- [ ] Export CSV propre avec les champs : nom, URL, localisation, titre/résumé (sans email)
- [ ] Session LinkedIn persistée localement ; identifiants (`LINKEDIN_EMAIL`/`LINKEDIN_PASSWORD`) dans `.env.local`, jamais en dur dans le code

**Périmètre** :
- `source/backend/adapters/scraping/` — recherche + extraction Playwright, sélecteurs CSS centralisés
- `source/backend/adapters/storage/` — export CSV
- `.env.local` — identifiants LinkedIn (non commité)

**Décisions** :
- 02/07/2026 — Pas de scoring/catégorisation dans ce premier ticket (réservé à la Phase 2) ; lecture seule uniquement, aucun envoi de message/invitation ; volume limité à un petit lot de test, pas de contournement des mesures anti-bot LinkedIn.
- 02/07/2026 — Extraction de l'email hors scope de POC-001 : nécessite de visiter la page profil individuelle (non disponible depuis les cartes de résultats de recherche), donc plus de requêtes par profil. Reporté à un ticket séparé, à cadrer une fois POC-001 validé.
- 02/07/2026 — Identifiants LinkedIn dans `.env.local` confirmés ; connexion initiale reste manuelle dans la fenêtre Playwright (le script ne remplit pas le formulaire de login automatiquement) — la session persistée évite une reconnexion à chaque run. Le remplissage automatique du login à partir de `.env.local` pourra être ajouté plus tard si besoin, sans changer le stockage des identifiants.
