# Plan POC-014 — Scoring v2 sur le titre, mesuré contre la grille de profilage du client

Plan validé par l'utilisateur le 05/10/2026, sur le poste principal (itinérance terminée).

## Résumé

Mesurer ce que le **titre seul** reproduit du jugement client du 11/09/2026 sur les 81 profils,
puis l'améliorer sans perdre de rappel. Le livrable est un chiffre honnête, qui dira si POC-016
est indispensable ou seulement utile. Les règles dérivent de la grille du client, jamais d'un
profil nommé. `commentaire_client` reste intact ; ni migration, ni appel réseau.

## État vérifié au cadrage (05/10/2026)

- Branche `master`, arbre propre, 143 tests passants.
- Magasin lu en lecture seule : 81 profils, 81 commentaires client, `user_version` 2, empreinte
  `47b767d5acca659a29511933dfa8352f`.
- Les 81 commentaires commencent tous par un des quatre préfixes de la grille (6 excellents,
  20 bons, 46 mauvais, 9 rien à voir).
- Mesure v1 reproduite : 65 retenus au seuil 60, 26 bons ou excellents, précision 40 %, rappel 100 %.

## Écarts au prompt (écrit le 16/09/2026 en itinérance)

- Sauvegarde dans `D:\Documents\Dev\_backup_prospection\` (et non `C:\Users\HP\…`).
- Écriture et nouvelle empreinte consignées dans `handoff.md` et l'en-tête de `task_list.md` ;
  `prompt_reconciliation_retour.md`, procédure close, n'est pas touché.

## Constat du diagnostic

- [Code] Plafond structurel : plusieurs profils jugés bons n'ont pour titre que la formule
  générique « Coach professionnel certifié Coaching Ways / Level 2 ICF », que portent aussi
  plusieurs profils jugés mauvais ou rien à voir. À rappel constant, ces derniers restent retenus.
- [Code] « sophrologue » et « Expertise fonction publique » figurent chacun dans le titre d'un bon
  profil : un signal multicarte ou fonction publique ne peut être qu'un malus léger, pas une
  exclusion.

## Décisions prises au cadrage

1. **Score seul** : la colonne `categorie` reste telle quelle. L'évaluateur publie la projection
   du score sur les 4 niveaux comme mesure ; la décision d'affichage se prendra après le prochain
   lot annoté.
2. **Seuil 60 conservé** : c'est lui qui garantit le rappel de 100 %.
3. Consignation de l'empreinte dans `handoff.md` et `task_list.md`.

## Fichiers

- Créés : `source/backend/adapters/storage/run_poc014_evaluation.py` (évaluateur, connexion SQLite
  en lecture seule), `tests/unit/test_scoring_evaluation.py`.
- Modifiés : `config/scoring_rules.json`, `tests/unit/test_profile_scoring.py`, les quatre fichiers
  de fin de session.
- Non touchés a priori : `profile_scoring.py`, `profile_store.py`.

## Risque principal

Le sur-apprentissage : 81 profils, dont 6 excellents, servent à la fois à régler et à mesurer.
Garde-fou : chaque règle est écrite depuis le texte de la grille, mesurée une fois, gardée ou
retirée — sans retouche des poids pour gagner des points. La v2 n'est validée qu'après mesure sur
le prochain lot annoté.

## Tests prévus

- Évaluateur : parsing du verdict (quatre préfixes, motif après virgule, valeur inconnue signalée
  et non devinée), précision, rappel, matrice, pouvoir discriminant par règle, absence d'écriture.
- Scoring : un test par règle ajoutée ou modifiée, sur des titres fictifs.

## Étapes

1. **Évaluateur en lecture seule.** Il rescore les titres en mémoire avec un fichier de règles
   donné (mesure d'une v2 sans écrire dans le magasin) et publie matrice, précision, rappel et
   pouvoir discriminant par règle. Mesure v1 (40 % / 100 %) reproduite et committée avant toute
   règle.
2. **Règles v2, une à la fois, mesurée à chaque pas** : exclusion « Life & Business Coach »
   (anomalie A) ; malus « coach en formation » ; malus léger multicarte / autre pratique ; bonus
   « ancien dirigeant / coach de dirigeants » ; rééquilibrage des poids (`certification` en baisse,
   `cible_business` en hausse). Chaque mot-clé court vérifié contre les 81 titres (piège de
   sous-chaîne).
3. **Vérification** : tests complets, comparaison v1/v2 côte à côte, avec ce que les chiffres ne
   prouvent pas.
4. **Magasin réel** : sauvegarde datée, `run_poc003`, comparaison à la sauvegarde (seules
   `categorie`, `score`, `justification` bougent ; 81 commentaires identiques), nouvelle empreinte.
5. **Fin de session** : Backlog, `task_list.md`, `handoff.md`, `CLAUDE.md`, prompt du ticket
   suivant (POC-015), commit.
