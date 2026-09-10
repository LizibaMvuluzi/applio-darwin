"""
train.py — NIVEAU 3 : entraînement / amélioration du modèle 'darwin'.

⚠️ NE PAS UTILISER avant d'avoir validé le Niveau 1 (inference.py) et le
Niveau 2 (qualité du résultat jugée satisfaisante à l'oreille).

Ce script encapsule les étapes d'entraînement RVC dans l'ordre
utile pour la version actuelle d'Applio : preprocess → extract → train.
La génération de l'index est effectuée automatiquement par la commande train
à la fin de l'entraînement dans la CLI actuelle d'Applio.
Utilise "darwin" (minuscule) partout — voir docs/TROUBLESHOOTING.md pour
l'historique du bug Darwin/darwin corrigé ici.

SÉCURITÉ CLI : avant chaque étape, ce script vérifie que les arguments qu'il
s'apprête à envoyer existent réellement dans la version d'Applio installée
(via `core.py <étape> --help`). Si un argument n'existe plus ou a changé de
nom, le script s'arrête AVANT de consommer du GPU, au lieu d'échouer en
cours de route. C'est nécessaire car la documentation publique d'Applio
(docs.applio.org) utilise une orthographe (underscores : --model_name)
différente du code source actuel de la branche main (tirets :
--model-name) — la documentation n'est donc pas fiable pour ce projet ;
seule cette vérification en direct, contre la version réellement installée,
fait foi.

Usage :
    python scripts/train.py --config config/config.json --step preprocess
    python scripts/train.py --config config/config.json --step extract
        python scripts/train.py --config config/config.json --step train
"""

import argparse
import json
import subprocess
import sys
from multiprocessing import cpu_count
from pathlib import Path


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_flags_exist(python_bin, install_dir, subcommand, cmd):
    """Vérifie, via --help, que chaque --flag envoyé existe réellement dans
    cette version d'Applio, AVANT de lancer la vraie commande (qui peut
    consommer du GPU).

    RÈGLE STRICTE : si --help échoue, ne renvoie rien, ou si une option
    manque, on BLOQUE. On ne devine jamais et on ne continue jamais "avec
    prudence" — un --help défaillant est traité comme un échec, pas comme
    une simple incertitude."""
    help_result = subprocess.run(
        [python_bin, "core.py", subcommand, "--help"],
        cwd=str(install_dir), capture_output=True, text=True,
    )
    help_text = help_result.stdout + help_result.stderr

    if help_result.returncode != 0:
        print(f"❌ 'core.py {subcommand} --help' a échoué (code {help_result.returncode}).")
        print("   → Rien n'a été lancé, aucun GPU n'a été consommé.")
        print(help_text)
        return False

    if not help_text.strip():
        print(f"❌ 'core.py {subcommand} --help' n'a produit aucune sortie exploitable.")
        print("   → Rien n'a été lancé, aucun GPU n'a été consommé.")
        return False

    import re
    option_tokens = set(re.findall(r"(?<![A-Za-z0-9_])--[a-z0-9-]+", help_text))
    flags_sent = [tok for tok in cmd if tok.startswith("--")]
    missing = [f for f in flags_sent if f not in option_tokens]

    if missing:
        print(f"❌ Ces options n'existent pas dans 'core.py {subcommand} --help' :")
        for f in missing:
            print(f"   {f}")
        print("   → La CLI d'Applio a probablement changé. Rien n'a été lancé,")
        print("     aucun GPU n'a été consommé. Copie ce message et le contenu de :")
        print(f"     core.py {subcommand} --help")
        print("     pour obtenir la correction exacte.")
        return False

    print(f"✅ Options de '{subcommand}' vérifiées contre --help : toutes valides.")
    return True


def run(cmd, cwd):
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    print(result.stdout or "(vide)")
    if result.returncode != 0:
        print("--- STDERR ---")
        print(result.stderr or "(vide)")
        sys.exit(1)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.json")
    parser.add_argument(
        "--step", required=True,
        choices=["preprocess", "extract", "index", "train"],
        help="Étape à exécuter, une à la fois, dans cet ordre.",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    model_name = config["model_name"]
    if model_name != "darwin":
        print("❌ Le projet est verrouillé sur le modèle 'darwin'.")
        sys.exit(1)

    try:
        import torch
        if not torch.cuda.is_available():
            print("❌ Aucun GPU CUDA exploitable. Le Niveau 3 est bloqué.")
            sys.exit(1)
    except Exception as exc:
        print(f"❌ Impossible de valider CUDA avant l'entraînement : {exc}")
        sys.exit(1)
    install_dir = Path(config["applio"]["install_dir"])
    drive_root = Path(config["drive"]["root"])
    dataset_path = drive_root / config["drive"]["dataset_folder"]
    t = config["training"]
    sr = int(t["sample_rate"].rstrip("k")) * 1000
    cpu_cores = cpu_count()

    print(f"Modèle cible : {model_name}  (convention : toujours en minuscule)")

    if args.step == "preprocess":
        if not dataset_path.exists():
            print(f"❌ Dataset introuvable : {dataset_path}")
            sys.exit(1)
        cmd = [
            sys.executable, "core.py", "preprocess",
            "--model-name", model_name,
            "--dataset-path", str(dataset_path),
            "--sample-rate", str(sr),
            "--cpu-cores", str(cpu_cores),
            "--cut-preprocess", "Automatic",
            "--noise-reduction",
            "--noise-reduction-strength", str(t["noise_reduction_strength"]),
            "--chunk-len", "3.0",
            "--overlap-len", "0.3",
            "--normalization-mode", "none",
        ]
        if t.get("process_effects", False):
            cmd.append("--process-effects")

    elif args.step == "extract":
        cmd = [
            sys.executable, "core.py", "extract",
            "--model-name", model_name,
            "--f0-method", t["f0_method"],
            "--sample-rate", str(sr),
            "--cpu-cores", str(cpu_cores),
            "--gpu", "0",
            "--embedder-model", t["embedder_model"],
            "--include-mutes", "2",
        ]

    elif args.step == "index":
        cmd = [
            sys.executable, "core.py", "index",
            "--model-name", model_name,
            "--index-algorithm", "Auto",
        ]

    elif args.step == "train":
        cmd = [
            sys.executable, "core.py", "train",
            "--model-name", model_name,
            "--save-every-epoch", str(t["save_every_epoch"]),
            "--total-epoch", str(t["total_epoch"]),
            "--sample-rate", str(sr),
            "--batch-size", str(t["batch_size"]),
            "--gpu", "0",
            "--vocoder", t["vocoder"],
            "--save-only-latest",
            "--pretrained",
        ]

    if not verify_flags_exist(sys.executable, install_dir, args.step, cmd):
        sys.exit(1)

    if args.step == "train":
        # Vérifier la commande prerequisites AVANT tout téléchargement.
        prereq = [sys.executable, "core.py", "prerequisites", "--pretraineds-hifigan"]
        if not verify_flags_exist(sys.executable, install_dir, "prerequisites", prereq):
            sys.exit(1)
        print("📦 Téléchargement des pretraineds HiFi-GAN (Niveau 3 uniquement)...")
        run(prereq, cwd=str(install_dir))

    run(cmd, cwd=str(install_dir))
    print(f"\n✅ Étape '{args.step}' terminée pour le modèle '{model_name}'.")


if __name__ == "__main__":
    main()
