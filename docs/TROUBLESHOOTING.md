# Dépannage

Ce document rassemble les problèmes que le pipeline doit détecter automatiquement.

## Incohérence Darwin / darwin

Le nom du modèle est défini une seule fois dans `config/config.json` : `darwin`. Tous les scripts lisent cette valeur.

## Dépôt GitHub privé inaccessible dans Colab

Le notebook récupère le dépôt avec le secret Colab `GITHUB_TOKEN`.

Si la première cellule affiche que le dépôt est privé et que le secret manque :

1. ouvre **🔑 Secrets** dans Colab ;
2. crée `GITHUB_TOKEN` ;
3. active l'accès du notebook ;
4. relance la cellule.

Le token n'est pas écrit dans le notebook ni dans Git.

## Modèle introuvable

Vérifie :

- Google Drive est monté ;
- le modèle est dans `MyDrive/ApplioBackup/darwin/` ;
- le dossier contient au moins un `.pth` ;
- `drive.root` n'a pas été modifié dans `config.json`.

## Fichier .index introuvable

Le Niveau 1 s'arrête volontairement si aucun `.index` n'est trouvé. La CLI actuelle d'Applio exige `--index-path` pour `infer`.

Place donc `darwin.index` dans :

```text
MyDrive/ApplioBackup/darwin/
```

Le script exige exactement `darwin.pth` et `darwin.index` ; aucun autre fichier n'est sélectionné automatiquement.

## Audio introuvable

Par défaut, l'audio source est :

```text
MyDrive/ma_voix.wav
```

Si nécessaire, modifie uniquement `drive.input_audio` dans `config/config.json`.

## RMVPE ou ContentVec manquant

Relance la cellule d'installation. Les ressources Applio sont téléchargées automatiquement par `core.py prerequisites`.

## GPU absent

Le projet est volontairement bloquant sans GPU CUDA. Le notebook vérifie le GPU
avant l'installation, puis `check_environment.py` et `inference.py` revérifient
CUDA dans le même environnement Python qu'Applio.

Dans Colab : `Runtime → Change runtime type → GPU`, puis relance le notebook.

## L'inférence se termine mais aucun fichier n'est créé

Le script `inference.py` affiche et sauvegarde toujours :

- la commande complète ;
- le code retour ;
- `stdout` ;
- `stderr`.

Le log horodaté est enregistré dans `MyDrive/ApplioExported/`.

## Les arguments Applio ont-ils changé ?

Le pipeline a été aligné sur la CLI actuelle d'Applio au moment de la préparation du dépôt. Si Applio modifie ultérieurement sa CLI, le `stderr` du log indiquera l'argument concerné.

## La documentation officielle d'Applio est parfois désynchronisée du code

**Constaté lors de l'audit de cette version :** la documentation publique
(`docs.applio.org`) montre des exemples de commandes avec des underscores
(`--input_path`, `--f0_method`), alors que le code source réel de la
branche `main` sur GitHub utilise des tirets (`--input-path`,
`--f0-method`). Ce n'est pas une erreur de notre part — c'est la
documentation du projet qui n'a pas suivi un renommage effectué dans le
code.

**Conséquence pour ce dépôt :** on ne peut pas faire confiance aux
exemples de la documentation d'Applio pour écrire nos commandes. Chaque
script (`inference.py`, `train.py`) vérifie donc lui-même, à chaque
exécution, que les options qu'il envoie existent réellement dans
`core.py <commande> --help` de la version effectivement installée, avant
de lancer quoi que ce soit. Si Applio change encore sa CLI plus tard, le
script s'arrêtera avec un message clair au lieu d'échouer en pleine
exécution ou de gaspiller du GPU.

## Compatibilité CLI du Niveau 3

Le code source actuel d'Applio expose `--process-effects` et
`--noise-reduction-strength` pour `core.py preprocess`. `train.py` utilise ces
noms exacts et vérifie `core.py <étape> --help` avant toute commande réelle.

Pour l'étape `train`, le téléchargement des pretraineds HiFi-GAN est lui-même
précédé d'une vérification de `core.py prerequisites --help`. Aucun
téléchargement d'entraînement n'est effectué pendant le Niveau 1.

## Sélection stricte du modèle (mise à jour)

Le projet exige désormais exactement `darwin.pth` et `darwin.index` dans
`ApplioBackup/darwin/`. Si d'autres fichiers `.pth`/`.index` existent dans
ce dossier, ils sont ignorés — aucune sélection automatique n'est faite.
Si tes fichiers portent un autre nom, renomme-les avant de lancer
l'inférence.

## Le garde-fou --help bloque désormais réellement

Version précédente : si `core.py <commande> --help` échouait, le script
affichait un avertissement et continuait quand même — ce qui contredisait
l'objectif du garde-fou. C'est corrigé : un échec de `--help` (code
d'erreur ou sortie vide) arrête maintenant le script immédiatement, avant
toute commande réelle, aussi bien pour `inference.py` que pour `train.py`.

## Validation du fichier WAV produit

`inference.py` ne considère plus une inférence comme réussie sur la seule
base de "le fichier existe". Il vérifie, avec le module standard `wave` :
que le fichier n'est pas vide, que l'en-tête WAV est lisible, et que la
durée est supérieure à zéro. Un fichier de sortie présent mais invalide
est désormais traité comme un échec.

## Ressources d'entraînement (pretraineds HiFi-GAN)

`setup.py` ne télécharge plus `--pretraineds-hifigan` par défaut — ces
fichiers ne servent qu'à l'entraînement (Niveau 3). Ils sont téléchargés
automatiquement par `train.py`, une seule fois, uniquement quand l'étape
"train" est réellement atteinte (donc seulement si `RUN_TRAINING = True`).
Le Niveau 1 n'installe donc que le strict nécessaire.

## Figer la version d'Applio

`config.example.json` conserve `"ref": "main"` pour permettre une première
résolution. Après cette première résolution, `setup.py` écrit automatiquement
le SHA exact dans :

```text
MyDrive/ApplioExported/applio_commit.lock
```

Les sessions suivantes réutilisent ce SHA automatiquement tant que le fichier
de verrouillage existe. Aucun SHA n'est inventé et aucune modification
manuelle du code n'est nécessaire.

Pour volontairement revenir à la branche `main`, supprimer le fichier
`applio_commit.lock` de `ApplioExported/` avant une nouvelle session.


## Erreur `NameError: name 're' is not defined`

Cette erreur appartenait à une version précédente de `scripts/setup.py`. La version corrigée importe désormais le module `re` et ne nécessite aucune modification manuelle dans Colab.
