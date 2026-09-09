# Applio Darwin

> Baseline propre pour le nouveau dépôt GitHub. Le runtime Colab est jetable ; GitHub et Google Drive sont les deux sources persistantes.\n
Système de conversion vocale par IA (Applio/RVC), utilisant un modèle vocal
personnel nommé **darwin**, pensé pour convertir une performance chantée réelle
(notamment en lingala) en conservant au maximum la diction et le phrasé
d'origine, tout en changeant le timbre.

Ce projet fait partie du flux de production plus large :

```
Suno (maquette) → BandLab (arrangement) → voix réelle enregistrée
   → Applio/RVC (ce dépôt) → WAV converti → BandLab (mixage/mastering)
```

## Principe d'architecture

Trois responsabilités, trois emplacements, jamais mélangés :

| Élément | Emplacement | Pourquoi |
|---|---|---|
| Code, notebook, scripts, configuration | **GitHub** (ce dépôt) | Versionné, jamais perdu, léger |
| Modèle `.pth`, `.index`, dataset, fichiers audio | **Google Drive** | Fichiers lourds, doivent persister au-delà d'une session de calcul |
| Calcul (installation d'Applio, inférence, entraînement) | **Google Colab** (ou Kaggle) | Environnement jetable — peut être détruit et recréé sans perte |

Le principe central : **si le runtime Colab disparaît, rien n'est perdu.**
Le code se retrouve en clonant ce dépôt, les fichiers lourds sont sur Drive.

## Convention de nommage

Le modèle s'appelle **`darwin`, toujours en minuscules**, partout : dans les
noms de dossiers, les scripts, la configuration, le notebook. Les anciennes
versions du projet mélangeaient `Darwin` et `darwin`, ce qui créait deux
dossiers différents sous Linux (sensible à la casse). C'est corrigé
définitivement ici — voir `docs/TROUBLESHOOTING.md`.

## Structure du dépôt

```
applio-darwin/
├── README.md
├── requirements.txt
├── .gitignore
├── notebooks/
│   └── Applio_Darwin_Colab.ipynb   → notebook principal, à ouvrir dans Colab
├── scripts/
│   ├── setup.py                    → installe Applio (une fois par session)
│   ├── check_environment.py        → diagnostic complet avant toute action
│   ├── inference.py                → Niveau 1 : conversion vocale
│   └── train.py                    → Niveau 3 : entraînement (plus tard)
├── config/
│   └── config.example.json         → chemins et paramètres, à copier en config.json
└── docs/
    ├── ARCHITECTURE.md
    ├── INSTALLATION.md
    └── TROUBLESHOOTING.md
```

## Démarrage rapide

1. Sur Google Drive, prépare cette arborescence (voir `docs/INSTALLATION.md`
   pour le détail) :
   ```
   MyDrive/
   ├── ApplioBackup/darwin/darwin.pth
   ├── ApplioBackup/darwin/darwin.index
   ├── Darwin_Dataset/           (pour plus tard, niveau 3)
   ├── ma_voix.wav
   └── ApplioExported/
   ```
2. Copie `config/config.example.json` vers `config/config.json` et ajuste les
   chemins si besoin (les valeurs par défaut correspondent à l'arborescence
   ci-dessus).
3. Ouvre `notebooks/Applio_Darwin_Colab.ipynb` dans Google Colab.
4. Exécute les cellules dans l'ordre — chaque cellule vérifie ce qui existe
   avant de continuer, aucune étape manuelle cachée n'est nécessaire.
5. Le résultat WAV est automatiquement sauvegardé dans
   `MyDrive/ApplioExported/`.

## Les trois niveaux de travail

Ce projet sépare volontairement trois objectifs, pour ne jamais les mélanger :

- **Niveau 1 — Inférence** : faire fonctionner la conversion vocale avec le
  modèle `darwin` existant. C'est la priorité actuelle.
- **Niveau 2 — Qualité** : valider que le résultat est exploitable
  musicalement (fidélité de la diction lingala, qualité du timbre).
- **Niveau 3 — Entraînement** : créer ou améliorer le modèle `darwin` à
  partir d'un dataset vocal personnel. À faire seulement après validation du
  Niveau 1 et 2.

## En cas de problème

Consulte `docs/TROUBLESHOOTING.md` — il documente déjà les problèmes
rencontrés lors des sessions précédentes (modèle introuvable, RMVPE manquant,
GPU absent, incohérence Darwin/darwin, sortie non créée) et comment les
diagnostiquer.
