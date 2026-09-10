"""
setup.py — Installation reproductible d'Applio pour Colab/Kaggle.

Le runtime est jetable : Applio et son environnement Python sont reconstruits
à chaque session. Les gros fichiers personnels restent sur Google Drive.

Usage:
    python scripts/setup.py --config config/config.json
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


PYTORCH_INDEX = "https://download.pytorch.org/whl/cu128"


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run(cmd, **kwargs):
    printable = " ".join(map(str, cmd))
    print(f"$ {printable}")
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        print(f"❌ Commande échouée (code {result.returncode})")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        raise RuntimeError(f"Commande échouée : {printable}")
    return result


def is_sha(ref: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-fA-F]{40}", ref))


def clone_applio(repo_url: str, ref: str, install_dir: Path) -> str:
    """Clone Applio and return the exact commit checked out."""
    if install_dir.exists():
        shutil.rmtree(install_dir)

    print(f"📦 Clonage d'Applio ({ref}) dans {install_dir} ...")

    if is_sha(ref):
        # --branch ne sait pas prendre un SHA. On clone d'abord, puis on
        # récupère explicitement le commit demandé et on le détache.
        run(["git", "clone", "--depth", "1", repo_url, str(install_dir)])
        run(["git", "-C", str(install_dir), "fetch", "--depth", "1", "origin", ref])
        run(["git", "-C", str(install_dir), "checkout", "--detach", ref])
    else:
        run([
            "git", "clone", "--depth", "1", "--branch", ref,
            repo_url, str(install_dir)
        ])

    sha_result = subprocess.run(
        ["git", "-C", str(install_dir), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    )
    sha = sha_result.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise RuntimeError(f"SHA Applio invalide ou introuvable : {sha!r}")

    if is_sha(ref) and sha.lower() != ref.lower():
        raise RuntimeError(
            f"Le SHA demandé ({ref}) ne correspond pas au commit obtenu ({sha})."
        )

    print("\n" + "=" * 60)
    print("📌 COMMIT APPLIO UTILISÉ")
    print(f"   {sha}")
    print("=" * 60)
    return sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.json")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        example = config_path.with_name("config.example.json")
        if example.exists():
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                example.read_text(encoding="utf-8"), encoding="utf-8"
            )
            print(f"✅ Configuration créée automatiquement : {config_path}")
        else:
            raise FileNotFoundError(f"Configuration introuvable : {config_path}")

    config = load_config(str(config_path))
    if config.get("model_name") != "darwin":
        raise ValueError(
            "Le projet est verrouillé sur le modèle 'darwin'. "
            "Corrige model_name dans config.json."
        )

    install_dir = Path(config["applio"]["install_dir"])
    repo_url = config["applio"]["repo_url"]
    applio_ref = str(config["applio"].get("ref", "main"))
    drive_root = Path(config["drive"]["root"])
    lock_path = drive_root / config["drive"]["export_folder"] / "applio_commit.lock"
    python_env_dir = Path(
        config.get("runtime", {}).get("python_env_dir", "/content/applio-env")
    )
    # On Colab, the uv executable location can vary. Use uv through the current Python.
    uv_cmd = [sys.executable, "-m", "uv"]

    print("=" * 60)
    print("SETUP — Installation d'Applio")
    print("=" * 60)

    # Pour la reproductibilité, on ne réutilise jamais silencieusement une
    # installation Applio provenant d'une autre session/version.
    if install_dir.exists():
        print(f"🧹 Suppression de l'ancienne installation : {install_dir}")
        shutil.rmtree(install_dir)

    effective_ref = applio_ref
    if applio_ref == "main" and lock_path.is_file():
        locked = lock_path.read_text(encoding="utf-8").strip()
        if is_sha(locked):
            effective_ref = locked
            print(f"🔒 Commit Applio verrouillé trouvé sur Drive : {effective_ref}")
        else:
            print("⚠️ Fichier de verrouillage Applio invalide — il sera recréé.")
    sha = clone_applio(repo_url, effective_ref, install_dir)

    # Persister le commit réellement utilisé afin que les sessions suivantes
    # réutilisent exactement la même version d'Applio.
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(sha + "\n", encoding="utf-8")
    print(f"🔒 Commit Applio enregistré sur Drive : {lock_path}")

    print("\n🧰 Préparation d'un environnement Python 3.12 isolé...")
    # Install uv through the system Python to avoid PATH problems in Colab.
    run([sys.executable, "-m", "pip", "install", "-q", "uv"])
    run(uv_cmd + ["--version"])
    run(uv_cmd + ["python", "install", "3.12"])

    # Un runtime Colab neuf ne possède normalement pas cet environnement.
    # S'il existe déjà, on le recrée pour éviter une contamination par une
    # ancienne installation.
    if python_env_dir.exists():
        shutil.rmtree(python_env_dir)
    run(uv_cmd + ["venv", "--python", "3.12", str(python_env_dir)])

    venv_python = python_env_dir / "bin" / "python"
    if not venv_python.exists():
        raise FileNotFoundError(f"Python du venv introuvable : {venv_python}")

    print("\n📦 Installation des dépendances Applio...")
    run(
        [
            *uv_cmd, "pip", "install", "--python", str(venv_python), "-q",
            "-r", "requirements.txt",
            "--extra-index-url", PYTORCH_INDEX,
            "--index-strategy", "unsafe-best-match",
        ],
        cwd=str(install_dir),
    )

    print("\n🎯 Installation explicite des wheels PyTorch CUDA 12.8...")
    run(
        [
            *uv_cmd, "pip", "install", "--python", str(venv_python), "-q",
            "--index-url", PYTORCH_INDEX,
            "--extra-index-url", "https://pypi.org/simple",
            "torch==2.11.0", "torchaudio==2.11.0",
        ]
    )

    # Vérification immédiate dans LE MÊME Python que l'inférence.
    print("\n🔎 Vérification immédiate PyTorch/CUDA...")
    check = subprocess.run(
        [
            str(venv_python), "-c",
            (
                "import sys, torch; "
                "print('Python:', sys.version.split()[0]); "
                "print('Torch:', torch.__version__); "
                "print('Torch CUDA:', torch.version.cuda or '(CPU only)'); "
                "print('CUDA disponible:', torch.cuda.is_available()); "
                "raise SystemExit(0 if torch.cuda.is_available() else 1)"
            ),
        ],
        capture_output=True, text=True,
    )
    print(check.stdout or "")
    if check.stderr:
        print(check.stderr)
    if check.returncode != 0:
        raise RuntimeError(
            "PyTorch/CUDA n'est pas exploitable dans l'environnement Applio. "
            "Le setup s'arrête avant toute inférence."
        )

    print("\n📦 Téléchargement des ressources Niveau 1 (RMVPE, embedders, ffmpeg)...")
    print("   --pretraineds-hifigan est volontairement réservé au Niveau 3.")
    run(
        [str(venv_python), "core.py", "prerequisites", "--no-pretraineds-hifigan", "--models", "--exe"],
        cwd=str(install_dir),
    )

    config_template = install_dir / "assets" / "config_template.json"
    config_target = install_dir / "assets" / "config.json"
    if config_template.exists():
        config_target.write_text(
            config_template.read_text(encoding="utf-8"), encoding="utf-8"
        )

    print("\n" + "=" * 60)
    print("✅ SETUP TERMINÉ")
    print(f"   Commit Applio : {sha}")
    print(f"   Python Applio : {venv_python}")
    print("   Prochaine étape : scripts/check_environment.py --config config/config.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
