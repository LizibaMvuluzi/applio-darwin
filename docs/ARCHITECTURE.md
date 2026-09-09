# Architecture

## Vue d'ensemble

```
                    GITHUB (ce dépôt)
                          │
                    code, notebook,
                    scripts, config
                          │
                          ▼
              NOUVEAU RUNTIME COLAB/KAGGLE
                    (jetable, temporaire)
                          │
              1. clone ce dépôt
              2. installe Applio (scripts/setup.py)
              3. vérifie l'environnement (check_environment.py)
                          │
                          ▼
                   GOOGLE DRIVE
          (source de vérité des gros fichiers)
      ┌───────────────┬──────────────┬───────────────┐
      ▼                ▼              ▼               ▼
ApplioBackup/     Darwin_Dataset/  ma_voix.wav   ApplioExported/
  darwin/
  ├─ darwin.pth
  └─ darwin.index
                          │
                          ▼
                 scripts/inference.py
                          │
                          ▼
              darwin_output.wav → ApplioExported/
                          │
                          ▼
                      BandLab
              (guitare réelle, mixage, mastering)
```

## Pourquoi cette séparation

- **GitHub** ne contient jamais de fichier lourd. Un dépôt Git n'est pas
  fait pour stocker des modèles de plusieurs centaines de Mo — au-delà de
  100 Mo, GitHub refuse même le fichier.
- **Google Drive** persiste indéfiniment, indépendamment de la durée de vie
  d'une session de calcul. C'est là que vivent les fichiers qui ont pris du
  temps à produire (le modèle entraîné, le dataset).
- **Colab/Kaggle** est jetable par nature : une session peut expirer,
  atteindre une limite GPU, ou simplement être fermée. Rien d'important ne
  doit dépendre de son état interne au-delà d'une session.

## Les trois niveaux

| Niveau | Objectif | Script | Pré-requis |
|---|---|---|---|
| 1 | Faire fonctionner l'inférence avec `darwin` | `inference.py` | Modèle déjà présent sur Drive |
| 2 | Juger si le résultat est exploitable musicalement | (écoute manuelle) | Niveau 1 validé |
| 3 | Entraîner/améliorer le modèle `darwin` | `train.py` | Niveau 2 jugé satisfaisant |

Ne jamais passer au niveau suivant avant d'avoir validé le précédent — c'est
ce qui a causé de la confusion dans les versions précédentes du projet.

## Compatibilité Kaggle

Le script `check_environment.py` détecte simplement si un GPU est
disponible, sans jamais supposer un modèle précis (T4, P100...) ni une
durée de session garantie. Cette approche fonctionne identiquement sur
Colab et sur Kaggle — seul le clonage initial du dépôt et le montage du
stockage (Drive vs Kaggle Datasets) diffèrent, le reste du pipeline
(`setup.py`, `inference.py`, `train.py`) est indépendant de la plateforme.
