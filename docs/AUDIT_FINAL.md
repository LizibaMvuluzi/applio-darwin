# Audit final — applio-darwin

Cette version a été réexaminée à partir du ZIP actuel du dépôt fourni pour
le contrôle. Les erreurs révélées pendant le lancement réel dans Colab ont été
intégrées dans cette version corrigée.

## Corrections principales

- correction définitive du problème d'installation de `uv` dans Colab : le
  projet n'attend plus un exécutable à un chemin fixe et utilise `python -m uv` ;
- installation automatique de `uv` via le Python système de Colab ;
- utilisation de `sys.executable` dans la cellule d'installation du notebook,
  plutôt que de supposer qu'une commande `python` particulière est active ;
- diagnostic `setup.py` conservant stdout, stderr et code de sortie ;
- blocage explicite si l'interpréteur `/content/applio-env/bin/python` n'existe
  pas après l'installation ;
- `--pretraineds-hifigan` est explicitement désactivé pendant le Niveau 1 :
  les ressources HiFi-GAN d'entraînement ne sont téléchargées qu'au Niveau 3 ;
- séquence d'entraînement du notebook corrigée en `preprocess → extract → train`.
  Dans la CLI actuelle d'Applio, `train` génère ensuite l'index à la fin ;
- conservation du garde-fou `RUN_TRAINING = False` ;
- conservation des vérifications `core.py <commande> --help` avant les commandes
  réelles ;
- conservation de la validation stricte de `darwin.pth`, `darwin.index` et du
  WAV d'entrée/sortie ;
- conservation du verrouillage automatique du commit Applio sur Google Drive.

## Contrôles statiques réalisés

- intégrité de l'archive ZIP : OK ;
- syntaxe Python des 4 scripts : OK ;
- JSON de configuration : OK ;
- notebook nbformat 4 : OK ;
- toutes les cellules Python du notebook : syntaxe OK ;
- `RUN_TRAINING` initialisé à `False` ;
- aucun appel d'entraînement dans les cellules normales du Niveau 1 ;
- modèle strict `darwin` ;
- noms stricts `darwin.pth` + `darwin.index` ;
- GPU CUDA obligatoire ;
- validation de PyTorch/CUDA dans le même environnement Python qu'Applio ;
- vérification de la CLI réelle avant inférence et entraînement ;
- téléchargement HiFi-GAN réservé à l'étape `train` ;
- archive finale testée avec `ZipFile.testzip()`.

## Compatibilité Applio vérifiée

La branche actuelle d'Applio utilise Python 3.12 et ses dépendances actuelles
pinent notamment `torch==2.11.0` et `torchaudio==2.11.0`. La commande officielle
Linux utilise également l'index CUDA 12.8 pour l'installation des dépendances.

Le dépôt Darwin ne copie pas Applio dans Git : il clone la version choisie à
chaque nouvelle session et verrouille ensuite son SHA exact sur Drive.

## Limite honnête

Cette archive a été auditée statiquement et corrigée à partir des erreurs
réelles observées dans Colab. Elle n'a pas été lancée ici contre GitHub et le
GPU T4 réel de l'utilisateur. Le prochain lancement Colab constitue donc la
validation finale de l'installation réseau, du téléchargement des dépendances
et de l'inférence réelle avec `darwin.pth` / `darwin.index`.
