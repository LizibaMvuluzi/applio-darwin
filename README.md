# Applio Darwin

> Pipeline propre pour un dépôt GitHub léger et un runtime Colab/Kaggle jetable. GitHub et Google Drive sont les deux sources persistantes.

Système de conversion vocale par IA (Applio/RVC), utilisant un modèle vocal personnel nommé **darwin**, pensé pour convertir une performance chantée réelle, notamment en lingala, en conservant au maximum la diction et le phrasé d'origine tout en changeant le timbre.

Flux de production :

```text
Suno (maquette) → BandLab (arrangement) → voix réelle enregistrée
   → Applio/RVC (ce dépôt) → WAV converti → BandLab (mixage/mastering)
```

## Principe d'architecture

| Élément | Emplacement | Pourquoi |
|---|---|---|
| Code, notebook, scripts, configuration d'exemple | **GitHub** | Versionné, léger |
| Modèle `.pth`, `.index`, dataset, fichiers audio | **Google Drive** | Fichiers lourds et persistants |
| Calcul et installation d'Applio | **Google Colab/Kaggle** | Runtime jetable |

Si le runtime disparaît, rien d'important n'est perdu : le code est récupéré depuis GitHub et les fichiers lourds depuis Drive.

## Structure du dépôt

```text
applio-darwin/
├── README.md
├── .gitignore
├── notebooks/
│   └── Applio_Darwin_Colab.ipynb
├── scripts/
│   ├── setup.py
│   ├── check_environment.py
│   ├── inference.py
│   └── train.py
├── config/
│   └── config.example.json
└── docs/
    ├── ARCHITECTURE.md
    ├── INSTALLATION.md
    └── TROUBLESHOOTING.md
```

## Démarrage rapide

Sur Google Drive :

```text
MyDrive/
├── ApplioBackup/darwin/darwin.pth
├── ApplioBackup/darwin/darwin.index
├── Darwin_Dataset/           ← plus tard, Niveau 3
├── ma_voix.wav
└── ApplioExported/           ← créé automatiquement
```

Puis ouvre `notebooks/Applio_Darwin_Colab.ipynb` dans Colab et exécute les cellules dans l'ordre.

Le notebook est déjà configuré pour le dépôt `LizibaMvuluzi/applio-darwin`. Comme le dépôt est privé, il utilise le secret Colab `GITHUB_TOKEN` pour le clone/mise à jour.

## Les trois niveaux

- **Niveau 1 — Inférence** : faire fonctionner la conversion avec le modèle `darwin` existant.
- **Niveau 2 — Qualité** : écouter et juger le résultat musicalement.
- **Niveau 3 — Entraînement** : créer ou améliorer `darwin` seulement après validation des deux premiers niveaux.

## En cas de problème

Consulte `docs/TROUBLESHOOTING.md` : dépôt privé, modèle/index manquant, audio manquant, ressources Applio, GPU et logs d'inférence y sont couverts.


## Sécurité du workflow

Le Niveau 1 exige un GPU CUDA et vérifie ce GPU dans le même environnement
Python que celui utilisé par Applio. `darwin.pth` et `darwin.index` doivent
porter exactement ces noms. La CLI `core.py infer --help` est contrôlée juste
avant chaque inférence et la sortie WAV est validée avant d'être déclarée
réussie.

Le Niveau 3 reste désactivé par défaut. Les commandes d'entraînement sont
protégées par la même vérification CLI et ne téléchargent leurs ressources
spécifiques qu'au moment où l'entraînement est volontairement activé.

La version d'Applio est verrouillée automatiquement après la première
résolution via `ApplioExported/applio_commit.lock` sur Google Drive.
