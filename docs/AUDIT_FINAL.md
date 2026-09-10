# Audit final — applio-darwin

Cette version a été réexaminée et corrigée directement à partir du ZIP fourni.

## Contrôles réalisés

- intégrité ZIP : OK
- correction du bug bloquant `NameError: re is not defined` dans `setup.py`
- écriture effective du verrou `applio_commit.lock` après résolution du commit
- syntaxe Python des 4 scripts : OK
- JSON de configuration : OK
- notebook nbformat 4 valide : OK
- une seule affectation réelle `RUN_TRAINING = False` : OK
- aucune occurrence exécutable de `RUN_TRAINING = True` : OK
- un seul appel `train.py` dans le notebook : OK
- `.gitignore` présent
- modèle strict `darwin.pth` + `darwin.index`
- validation WAV entrée et sortie
- GPU CUDA obligatoire
- vérification PyTorch/CUDA dans le même venv qu'Applio
- vérification de `core.py infer --help` avant inférence
- vérification `--help` avant chaque étape d'entraînement
- téléchargement HiFi-GAN réservé au Niveau 3
- verrouillage automatique du commit Applio sur Google Drive
- installation explicite de Torch/Torchaudio CUDA 12.8
- archive finale testée avec `ZipFile.testzip()`

## Limite honnête

Aucun audit statique ne peut remplacer un premier lancement réel dans Colab.
La première session devra donc valider l'installation réseau, le GPU attribué
par Colab, les ressources téléchargées et l'inférence réelle du modèle
`darwin`.

Le projet est conçu pour que ces points soient bloquants et diagnostiqués,
plutôt que de poursuivre silencieusement avec un environnement incorrect.

## Décision de compatibilité CLI

Le code source actuel d'Applio utilise notamment :

- `--input-path`
- `--output-path`
- `--pth-path`
- `--index-path`
- `--volume-envelope`
- `--clean-strength`
- `--formant-qfrency`
- `--formant-timbre`
- `--noise-reduction-strength`
- `--process-effects`

Le script ne se fie pas uniquement à cette liste : il demande aussi le
`--help` de la version réellement installée avant d'exécuter la commande.
