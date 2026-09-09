"""
setup.py — Installe Applio dans l'environnement de calcul (Colab/Kaggle).

Le runtime est jetable : Applio et son environnement Python sont reconstruits
à chaque nouvelle session. Les gros fichiers personnels restent sur Google Drive.

Usage:
    python scripts/setup.py --config config/config.json
"""

import argparse
import json
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
    applio_ref = config["applio"].get("ref", "main")
    python_env_dir = Path(config.get("runtime", {}).get("python_env_dir", "/content/applio-env"))
    uv_bin = Path.home() / ".local" / "bin" / "uv"

    print("=" * 60)
    print("SETUP — Installation d'Applio")
    print("=" * 60)

    if install_dir.exists() and (install_dir / "core.py").exists():
        print(f"✅ Applio déjà présent dans {install_dir} — pas de re-clonage.")
    else:
        if install_dir.exists():
            print(f"⚠️ Dossier Applio incomplet, suppression : {install_dir}")
            import shutil
            shutil.rmtree(install_dir)
        print(f"📦 Clonage d'Applio ({applio_ref}) dans {install_dir} ...")
        run(["git", "config", "--global", "advice.detachedHead", "false"])
        run([
            "git", "clone", "--depth", "1", "--branch", applio_ref,
            repo_url, str(install_dir)
        ])

    print("\n🧰 Préparation d'un environnement Python 3.12 isolé...")
    if not uv_bin.exists():
        run(["curl", "-LsSf", "https://astral.sh/uv/install.sh", "-o", "/tmp/install_uv.sh"])
        run(["sh", "/tmp/install_uv.sh"])
    if not uv_bin.exists():
        raise FileNotFoundError("uv n'a pas été installé à l'emplacement attendu.")

    # Applio fournit lui-même son installateur Windows en Python 3.12 ; on
    # reproduit ici ce choix dans le runtime Linux Colab/Kaggle.
    run([str(uv_bin), "python", "install", "3.12"])

    venv_python = python_env_dir / "bin" / "python"
    if not venv_python.exists():
        run([str(uv_bin), "venv", "--python", "3.12", str(python_env_dir)])

    print("\n📦 Installation des dépendances Applio (peut prendre plusieurs minutes)...")
    run(
        [
            str(uv_bin), "pip", "install", "--python", str(venv_python), "-q",
            "-r", "requirements.txt",
            "--extra-index-url", "https://download.pytorch.org/whl/cu128",
            "--index-strategy", "unsafe-best-match",
        ],
        cwd=str(install_dir),
    )

    print("\n📦 Téléchargement des ressources Applio (RMVPE, embedders, pretraineds)...")
    run(
        [str(venv_python), "core.py", "prerequisites", "--models", "--pretraineds-hifigan", "--exe"],
        cwd=str(install_dir),
    )

    config_template = install_dir / "assets" / "config_template.json"
    config_target = install_dir / "assets" / "config.json"
    if config_template.exists():
        config_target.write_text(config_template.read_text(encoding="utf-8"), encoding="utf-8")

    print("\n✅ Setup terminé.")
    print(f"   Python Applio : {venv_python}")
    print("   Prochaine étape : scripts/check_environment.py --config config/config.json")


if __name__ == "__main__":
    main()
