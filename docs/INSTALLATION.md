# Installation et premier dépôt

## 1. GitHub Desktop — une seule fois

1. Décompresse le ZIP reçu.
2. Place son contenu directement dans le dossier local du dépôt `applio-darwin` déjà créé avec GitHub Desktop.
3. GitHub Desktop détecte les modifications dans **Changes**.
4. Fais le commit puis **Push origin**.

Ensuite, les corrections se font de la même manière : on remplace le contenu du dépôt local par le nouveau ZIP corrigé, puis Commit → Push.

## 2. Google Drive — données persistantes

Conserve uniquement les fichiers lourds et personnels sur Drive :

```text
MyDrive/
├── ApplioBackup/
│   └── darwin/
│       ├── darwin.pth
│       └── darwin.index
├── Darwin_Dataset/       ← pour le Niveau 3
├── ma_voix.wav
└── ApplioExported/       ← créé/rempli automatiquement
```

Rien de tout cela ne doit être ajouté au dépôt GitHub.

## 3. Colab — environnement entièrement reconstruit

Le notebook principal est :

`notebooks/Applio_Darwin_Colab.ipynb`

Le pipeline est :

```text
GitHub
  ↓
clone / mise à jour automatique
  ↓
montage automatique de Google Drive
  ↓
création automatique de config.json
  ↓
installation automatique d'Applio + Python 3.12
  ↓
diagnostic complet
  ↓
inférence Niveau 1
  ↓
WAV → Google Drive
```

Aucune modification du notebook n'est nécessaire pour renseigner l'URL du dépôt : elle est déjà configurée pour `LizibaMvuluzi/applio-darwin`.

### Dépôt GitHub privé

Le dépôt est privé. Le notebook utilise le gestionnaire de secrets de Colab pour récupérer `GITHUB_TOKEN` sans l'écrire dans le notebook ni dans Git.

À faire une seule fois dans Colab :

1. ouvrir l'onglet **🔑 Secrets** ;
2. créer le secret `GITHUB_TOKEN` ;
3. activer **Notebook access** pour ce notebook.

Après cela, les sessions suivantes récupèrent automatiquement le dépôt.

## 4. Ordre de travail

1. Récupération du dépôt.
2. Montage Drive.
3. Création automatique de `config/config.json`.
4. Installation automatique d'Applio.
5. Diagnostic.
6. Inférence Niveau 1.
7. Écoute et validation Niveau 2.
8. Entraînement Niveau 3 uniquement après validation des deux premiers niveaux.
