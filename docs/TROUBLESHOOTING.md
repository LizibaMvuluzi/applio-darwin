# Dépannage

Ce document rassemble les problèmes réellement rencontrés lors des sessions
précédentes du projet, et comment ce dépôt les prévient ou les diagnostique.

## Incohérence Darwin / darwin

**Symptôme observé :** certaines cellules de l'ancien notebook utilisaient
`model_name = "Darwin"` (majuscule), d'autres `"darwin"` (minuscule).
Linux étant sensible à la casse, cela créait deux dossiers différents
(`logs/Darwin/` et `logs/darwin/`), ce qui aurait cassé l'entraînement au
moment de le lancer.

**Correction dans ce dépôt :** un seul endroit définit le nom du modèle —
`config.json` → `"model_name": "darwin"`. Tous les scripts (`inference.py`,
`train.py`, `check_environment.py`) lisent cette valeur, aucun ne la
réécrit en dur. Il est donc structurellement impossible d'avoir deux noms
différents.

## Modèle introuvable

**Symptôme :** `check_environment.py` affiche `❌ Dossier modèle
introuvable`.

**Causes possibles et vérifications :**
- Google Drive n'est pas monté → réexécute la cellule 2 du notebook.
- Le modèle n'est pas dans `ApplioBackup/darwin/` exactement — vérifie
  l'arborescence contre `docs/INSTALLATION.md`.
- Le chemin `drive.root` dans `config.json` a été modifié par erreur.

## Fichier .index introuvable

Ce n'est pas bloquant — l'index améliore la précision de la conversion
mais n'est pas obligatoire. `check_environment.py` affiche un `⚠️` (pas un
`❌`) dans ce cas et l'inférence continue normalement.

## Audio introuvable

Vérifie que `ma_voix.wav` est bien à la racine de `MyDrive/`, pas dans un
sous-dossier, sauf si tu as modifié `drive.input_audio` dans `config.json`
en conséquence.

## Environnement Colab réinitialisé en cours de route

**Symptôme :** une cellule qui fonctionnait auparavant échoue avec des
erreurs sur des fichiers ou dossiers introuvables, alors que rien n'a
changé dans le code.

**Cause :** chaque nouvelle session Colab repart de zéro — rien n'est
conservé en dehors de Google Drive. Si tu rouvres le notebook après une
déconnexion, il faut ré-exécuter TOUTES les cellules depuis le début,
dans l'ordre — ce n'est jamais un bug, c'est le comportement normal d'un
environnement jetable.

## RMVPE ou ContentVec manquant

**Symptôme :** `check_environment.py` affiche `❌` sur l'une de ces deux
ressources.

**Cause :** `scripts/setup.py` n'a pas terminé son installation
(souvent parce que la session a été interrompue en plein téléchargement).

**Correction :** relance simplement `python scripts/setup.py --config
config/config.json` — le script est conçu pour être relancé sans risque.

## GPU absent ou non garanti

Colab et Kaggle ne garantissent jamais un GPU précis sur leur offre
gratuite. `check_environment.py` détecte simplement s'il y en a un ou non,
sans jamais faire de promesse. Si aucun GPU n'est disponible, l'inférence
fonctionne quand même, juste plus lentement (CPU).

## "L'inférence se termine mais aucun fichier n'est créé"

C'est exactement le problème qui a bloqué la version précédente du projet.
**Cause identifiée après audit du code source d'Applio :** ce message est
une conséquence, pas la cause réelle — l'erreur véritable se trouve dans
`stderr`, que l'ancien notebook n'affichait pas dans tous les cas.

**Correction dans ce dépôt :** `scripts/inference.py` affiche
systématiquement le code retour, `stdout` ET `stderr` en entier, quel que
soit le résultat, et sauvegarde tout dans un fichier log horodaté sur
Google Drive. Si le problème se reproduit, ouvre ce fichier log et
regarde la section `--- STDERR ---` : c'est là que se trouve la vraie
erreur (le plus souvent une ressource manquante — voir la section RMVPE
ci-dessus).

## Les arguments de la ligne de commande Applio ont-ils changé ?

Vérifié directement contre le code source de `core.py` sur le dépôt
officiel `IAHispano/Applio` au moment de la construction de ce projet :
tous les arguments utilisés dans `inference.py` et `train.py`
(`--pitch`, `--f0-method`, `--index-rate`, etc.) sont valides dans la
version auditée. Si Applio publie une mise à jour qui renomme un
argument, le message d'erreur de `click` (la bibliothèque CLI utilisée
par Applio) l'indiquera explicitement dans `stderr` — inutile de deviner,
le log l'affichera clairement.
