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

Le script privilégie `darwin.index` lorsqu'il trouve `darwin.pth`.

## Audio introuvable

Par défaut, l'audio source est :

```text
MyDrive/ma_voix.wav
```

Si nécessaire, modifie uniquement `drive.input_audio` dans `config/config.json`.

## RMVPE ou ContentVec manquant

Relance la cellule d'installation. Les ressources Applio sont téléchargées automatiquement par `core.py prerequisites`.

## GPU absent

Le diagnostic indique si CUDA est disponible. L'inférence peut fonctionner sur CPU, mais elle sera nettement plus lente. L'entraînement du Niveau 3 doit, lui, être considéré comme une étape GPU.

## L'inférence se termine mais aucun fichier n'est créé

Le script `inference.py` affiche et sauvegarde toujours :

- la commande complète ;
- le code retour ;
- `stdout` ;
- `stderr`.

Le log horodaté est enregistré dans `MyDrive/ApplioExported/`.

## Les arguments Applio ont-ils changé ?

Le pipeline a été aligné sur la CLI actuelle d'Applio au moment de la préparation du dépôt. Si Applio modifie ultérieurement sa CLI, le `stderr` du log indiquera l'argument concerné.
