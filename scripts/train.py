"""
train.py — NIVEAU 3 : entraînement / amélioration du modèle 'darwin'.

⚠️ NE PAS UTILISER avant d'avoir validé le Niveau 1 (inference.py) et le
Niveau 2 (qualité du résultat jugée satisfaisante à l'oreille).

Ce script encapsule les quatre étapes d'entraînement RVC dans l'ordre
obligatoire : preprocess → extract → index → train.
Utilise "darwin" (minuscule) partout — voir docs/TROUBLESHOOTING.md pour
l'historique du bug Darwin/darwin corrigé ici.

Usage :
    python scripts/train.py --config config/config.json --step preprocess
    python scripts/train.py --config config/config.json --step extract
    python scripts/train.py --config config/config.json --step index
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
    model_name = config["model_name"]  # toujours "darwin", minuscule
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
            "--noise-reduction-strength", "0.7",
            "--chunk-len", "3.0",
            "--overlap-len", "0.3",
            "--normalization-mode", "none",
        ]
        run(cmd, cwd=str(install_dir))

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
        run(cmd, cwd=str(install_dir))

    elif args.step == "index":
        cmd = [
            sys.executable, "core.py", "index",
            "--model-name", model_name,
            "--index-algorithm", "Auto",
        ]
        run(cmd, cwd=str(install_dir))

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
        run(cmd, cwd=str(install_dir))

    print(f"\n✅ Étape '{args.step}' terminée pour le modèle '{model_name}'.")


if __name__ == "__main__":
    main()
