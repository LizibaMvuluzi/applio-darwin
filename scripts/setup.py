"""
setup.py — Installe Applio dans l'environnement de calcul (Colab/Kaggle).

Idempotent : si Applio est déjà installé dans cette session, ne réinstalle
rien. Conçu pour être appelé au début de CHAQUE session, sans dépendre d'un
état laissé par une session précédente (les runtimes Colab/Kaggle sont
jetables : rien ne survit d'une session à l'autre, sauf ce qui est sur Drive).

Usage :
    python scripts/setup.py --config config/config.json
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run(cmd, **kwargs):
    print(f"$ {' '.join(map(str, cmd))}")
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        print(f"❌ Commande échouée (code {result.returncode})")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        raise RuntimeError(f"Commande échouée : {cmd}")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.json")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        example = config_path.with_name("config.example.json")
        if example.exists():
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"✅ Configuration créée automatiquement : {config_path}")
        else:
            raise FileNotFoundError(f"Configuration introuvable : {config_path}")

    config = load_config(str(config_path))
    install_dir = Path(config["applio"]["install_dir"])
    repo_url = config["applio"]["repo_url"]

    print("=" * 60)
    print("SETUP — Installation d'Applio")
    print("=" * 60)

    if install_dir.exists() and (install_dir / "core.py").exists():
        print(f"✅ Applio déjà présent dans {install_dir} — pas de réinstallation.")
    else:
        print(f"📦 Clonage d'Applio dans {install_dir} ...")
        run(["git", "config", "--global", "advice.detachedHead", "false"])
        run(["git", "clone", repo_url, str(install_dir)])

    print("\n📦 Installation des dépendances Applio (peut prendre plusieurs minutes)...")
    uv_bin = Path.home() / ".local" / "bin" / "uv"
    if not uv_bin.exists():
        run(["curl", "-LsSf", "https://astral.sh/uv/install.sh", "-o", "/tmp/install_uv.sh"])
        run(["sh", "/tmp/install_uv.sh"])
    if not uv_bin.exists():
        raise FileNotFoundError("uv n'a pas été installé à l'emplacement attendu.")

    run(
        [
            str(uv_bin), "pip", "install", "--system", "-q", "-r", "requirements.txt",
            "--extra-index-url", "https://download.pytorch.org/whl/cu128",
            "--index-strategy", "unsafe-best-match",
        ],
        cwd=str(install_dir),
    )
    # No extra notebook package is required here; keep the runtime minimal.

    print("\n📦 Téléchargement des ressources Applio (RMVPE, ContentVec, pretraineds)...")
    run(
        [sys.executable, "core.py", "prerequisites", "--models", "--pretraineds-hifigan", "--exe"],
        cwd=str(install_dir),
    )

    config_template = install_dir / "assets" / "config_template.json"
    config_target = install_dir / "assets" / "config.json"
    if config_template.exists():
        config_target.write_text(config_template.read_text(encoding="utf-8"), encoding="utf-8")

    print("\n✅ Setup terminé.")
    print("   Prochaine étape : python scripts/check_environment.py --config config/config.json")


if __name__ == "__main__":
    main()
