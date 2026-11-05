Tu travailles dans le repo ProspectionLinkedIn avec Claude Code dans VS Code.

Je viens de faire un /clear. Tu reprends **POC-016, accepté par le client**, à l'**étape 6 : migration
v3**. Ne relis pas tout le repository.

> Contexte : accord du client par mail le 03/11/2026, définitions précisées au call du 05/11. Plan
> actualisé et committé le 05/11 (`fd386aa`). Les sauvegardes vont dans
> `D:\Documents\Dev\_backup_prospection\`. `task_list.md` (POC-016 `IN_PROGRESS`), `handoff.md`
> (section 21), `Backlog.md` et `CLAUDE.md` sont à jour au 05/11.

## Documents à lire en premier

1. `CLAUDE.md`
2. `document/prompts_plans/plan_POC-016.md` — **en entier**, surtout la section « Actualisation du
   05/11/2026, après le call » : décisions D1 à D8, grille retenue, étapes 5 à 11, critères modifiés.
   Elle prime sur les sections plus anciennes là où elles se contredisent.
3. `document/claude_code/handoff.md` — section 21, et dans la section 9 (POC-009) ce qui concerne
   la migration v1 → v2

Puis le code :

* `source/backend/adapters/storage/profile_store.py` — `migrer_schema`, `ouvrir_magasin`, le schéma,
  `_CHAMPS_COMPLETABLES`, `_EtapeCoordonnees`, `enregistrer_email_linkedin`, `profils_a_visiter`
* `source/backend/adapters/scraping/run_poc002.py` — en entier
* `source/backend/adapters/scraping/profile_email.py` — `enrich_profiles_with_email`,
  `scroll_profile_page`, `extract_rubriques_from_profile_page`
* `source/backend/core/parcours.py` — en entier
* les tests unitaires de `profile_store` et de `run_poc002` — pour voir ce qui est couvert

## Ce qui est décidé (résumé, le plan fait foi)

* **131 profils** non opposés lus, lot 1 (81) d'abord, puis le lot du 07/10 (50).
* **Une seule visite par profil, sans ouvrir la fenêtre « Coordonnées »** (0 email sur 30). Le code
  de l'email reste en place, non appelé.
* **Migration v3** : `texte_experience`, `texte_infos`, `date_lecture_parcours`. Additive et
  idempotente comme v2. Le marqueur est posé même si rien n'est trouvé (« lu, rien trouvé » ≠
  « pas encore lu »).
* Indicateurs et verdict estimé **calculés, non stockés**, tant que les règles bougent ; figés en
  base à la suppression du texte.
* Texte supprimé dans le délai à confirmer par le client (proposé : 30 jours après la présentation
  de la nouvelle note).
* Blocage : arrêt immédiat, reprise décidée **au cas par cas entre l'utilisateur et l'agent**.
  Paliers 5, 10, 20 ; 2 lancements par jour au plus ; volume à rediscuter.
* `commentaire_client` jamais modifié. Verdict estimé dans une colonne distincte (export : POC-018).

## Ce qui reste à faire, dans l'ordre

6. **Migration v3** (hors ligne) : code et tests sur base temporaire → sauvegarde datée du magasin et de
   `journal_collecte.csv` → application **avec l'accord de l'utilisateur** → contrôle ligne à ligne
   (aucune colonne v2 modifiée, `commentaire_client` identiques).
7. **Run de lecture** : `run_poc002` lit et écrit texte et date ; sélection « non lus, non opposés »,
   lot 1 d'abord ; arrêt sur page de blocage. Runs lancés par l'utilisateur.
8. Signaux et verdict estimé dans `core/` (listes d'employeurs publics et associatifs à faire valider).
9. Mesure : réglage sur le lot 1, contrôle sur le lot 2.
10. Présentation au client. 11. Suppression du texte.

## État vérifié au 05/11/2026

* Tests : **306 passed**.
* Magasin **non modifié** : 131 profils, 131 commentaires, `user_version` 2, empreinte MD5
  `189e64e0f6c1aa234851422686103ff5`.
* `config/scoring_rules.json` intact.

## Interdit

* appliquer la migration au magasin réel sans sauvegarde datée **et** accord explicite ;
* modifier `config/scoring_rules.json` avant la mesure ;
* lancer soi-même un run LinkedIn réel ;
* écrire dans `commentaire_client`.

## Rappels

* **Les runs LinkedIn réels sont lancés par l'utilisateur** : préparer, donner la commande, attendre
  la sortie collée.
* Avant tout run qui écrit le magasin : sauvegarde datée du magasin et de `journal_collecte.csv`,
  puis contrôle des `commentaire_client` contre la sauvegarde.
* Ne jamais régler et mesurer sur les mêmes profils.
* Réponses en français, commentaires de code en anglais, affirmations taguées
  [Code] / [Documentation] / [Inférence].

## Première réponse attendue

Ne modifie aucun fichier. Vérifie la branche, l'état Git, la suite de tests (306) et l'empreinte du
magasin. Demande à l'utilisateur si le mail de confirmation est parti et si le client a répondu sur la
durée de conservation. Puis propose le plan détaillé de l'étape 6 (colonnes, ordre de migration,
tests prévus, contrôle), et attends la validation.
