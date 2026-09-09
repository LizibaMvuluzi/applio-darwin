# Installation et premier dépôt

## 1. GitHub Desktop — une seule fois

1. Décompresse ce ZIP.
2. Place son contenu directement dans le dossier local du dépôt `applio-darwin` déjà créé avec GitHub Desktop.
3. GitHub Desktop doit alors afficher les nouveaux fichiers dans **Changes**.
4. Fais un commit initial clair, puis **Push origin**.

Le dépôt devient la source de vérité du code et du notebook.

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

## 3. Colab — aucun environnement manuel à reconstruire

Le notebook principal est :

`notebooks/Applio_Darwin_Colab.ipynb`

Le principe est :

```text
GitHub Desktop → GitHub
                  ↓
             nouveau Colab
                  ↓
        clone / mise à jour du dépôt
                  ↓
      montage automatique de Drive
                  ↓
      installation automatique d'Applio
                  ↓
           diagnostic complet
                  ↓
              inférence
                  ↓
        WAV → Google Drive
```

Après une nouvelle session Colab, on ne réinstalle rien à la main dans le runtime : le dépôt est récupéré et le runtime est reconstruit.

## 4. URL du dépôt

La variable `GITHUB_REPO` du notebook doit contenir l'URL de TON dépôt GitHub privé. Cette valeur n'a besoin d'être définie qu'une fois dans le notebook versionné ; elle n'est pas un secret.

## 5. Ordre de travail

1. Récupération du dépôt.
2. Montage Drive.
3. Création automatique de `config/config.json`.
4. Installation automatique d'Applio.
5. Diagnostic.
6. Inférence Niveau 1.
7. Écoute et validation Niveau 2.
8. Entraînement Niveau 3 uniquement après validation des deux premiers niveaux.

