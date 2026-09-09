# Architecture

## Vue d'ensemble

```text
                    GITHUB (ce dépôt)
                          │
                    code, notebook,
                    scripts, config
                          │
                          ▼
              NOUVEAU RUNTIME COLAB/KAGGLE
                    (jetable, temporaire)
                          │
              1. clone / mise à jour du dépôt
              2. installe Applio + Python 3.12
              3. vérifie l'environnement
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

- **GitHub** ne contient que le code, le notebook, les scripts et la configuration d'exemple.
- **Google Drive** conserve le modèle, l'index, le dataset, l'audio source et les exports.
- **Colab/Kaggle** fournit uniquement le calcul temporaire. Une session peut disparaître sans supprimer les données persistantes.

## Les trois niveaux

| Niveau | Objectif | Script | Pré-requis |
|---|---|---|---|
| 1 | Faire fonctionner l'inférence avec `darwin` | `inference.py` | `.pth` + `.index` présents sur Drive |
| 2 | Juger si le résultat est exploitable musicalement | écoute | Niveau 1 validé |
| 3 | Entraîner/améliorer le modèle `darwin` | `train.py` | Niveau 2 jugé satisfaisant |

Ne jamais passer au niveau suivant avant d'avoir validé le précédent.

## Point important sur l'index

La CLI actuelle d'Applio déclare `--index-path` comme argument requis pour `infer`. Le pipeline exige donc désormais explicitement `darwin.index` avant de lancer le Niveau 1. Le script cherche d'abord l'index portant le même nom de base que le `.pth`, puis utilise le dernier `.index` disponible dans le dossier si nécessaire.

## Compatibilité Colab/Kaggle

Le notebook utilise un environnement Python 3.12 isolé dans le runtime. Le dépôt reste indépendant de la plateforme ; seul le stockage persistant diffère entre Google Drive et un stockage Kaggle équivalent.
