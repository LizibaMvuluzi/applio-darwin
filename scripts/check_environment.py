"""
check_environment.py — Préflight strict avant Niveau 1.

Bloquant si :
- Applio/core.py absent ;
- Python/PyTorch/CUDA du venv Applio n'est pas exploitable ;
- GPU CUDA absent ;
- darwin.pth ou darwin.index exacts manquants/vides ;
- audio source absent/invalide.

Les ressources Applio téléchargées par `prerequisites --models --exe` sont
signalées à titre informatif ; leur chargement réel est validé par l'inférence.
"""

import argparse
import json
import sys
import wave
from pathlib import Path


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def validate_wav(path: Path):
    if not path.exists():
        return False, "fichier absent"
    if path.stat().st_size == 0:
        return False, "fichier vide"
    try:
        with wave.open(str(path), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / rate if rate else 0
            if duration <= 0:
                return False, "durée nulle"
            return True, f"{duration:.2f}s · {rate} Hz"
    except (wave.Error, EOFError) as exc:
        return False, f"WAV illisible : {exc}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.json")
    args = parser.parse_args()

    config = load_config(args.config)
    if config.get("model_name") != "darwin":
        print("❌ model_name doit être exactement 'darwin'.")
        sys.exit(1)

    install_dir = Path(config["applio"]["install_dir"])
    drive_root = Path(config["drive"]["root"])
    backup_dir = drive_root / config["drive"]["backup_folder"] / "darwin"
    audio_path = drive_root / config["drive"]["input_audio"]
    problems = []

    section("1. INSTALLATION APPLIO")
    core_py = install_dir / "core.py"
    if core_py.exists():
        print(f"✅ core.py trouvé : {core_py}")
    else:
        print(f"❌ core.py introuvable dans {install_dir}")
        problems.append("Applio non installé")

    section("2. PYTHON / PYTORCH / CUDA")
    print(f"Interpréteur Python : {sys.executable}")
    print(f"Version Python      : {sys.version.split()[0]}")
    if "applio-env" not in str(Path(sys.executable)):
        problems.append("Mauvais interpréteur Python")
        print("❌ Ce script doit être exécuté avec le Python du venv Applio.")
    try:
        import torch
        print(f"Version PyTorch     : {torch.__version__}")
        print(f"CUDA compilé dans PyTorch : {torch.version.cuda or '(CPU only)'}")
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            mem_total = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            print(f"✅ GPU CUDA détecté : {name} ({mem_total:.1f} Go VRAM)")
        else:
            print("❌ Aucun GPU CUDA exploitable.")
            print("   Dans Colab : Runtime → Change runtime type → GPU, puis relance.")
            problems.append("GPU CUDA absent")
    except Exception as exc:
        print(f"❌ PyTorch/CUDA non exploitable : {exc}")
        problems.append("PyTorch/CUDA indisponible")

    section("3. MODÈLE 'darwin' — CORRESPONDANCE STRICTE")
    if backup_dir.exists():
        expected_pth = backup_dir / "darwin.pth"
        expected_index = backup_dir / "darwin.index"
        if expected_pth.is_file() and expected_pth.stat().st_size > 0:
            print(f"✅ darwin.pth trouvé ({expected_pth.stat().st_size / 1024 / 1024:.1f} Mo)")
        else:
            print(f"❌ darwin.pth absent ou vide : {expected_pth}")
            problems.append("darwin.pth manquant/vide")
        if expected_index.is_file() and expected_index.stat().st_size > 0:
            print(f"✅ darwin.index trouvé ({expected_index.stat().st_size / 1024 / 1024:.1f} Mo)")
        else:
            print(f"❌ darwin.index absent ou vide : {expected_index}")
            problems.append("darwin.index manquant/vide")
    else:
        print(f"❌ Dossier modèle introuvable : {backup_dir}")
        problems.append("Dossier modèle introuvable")

    section("4. AUDIO SOURCE")
    ok, detail = validate_wav(audio_path)
    if ok:
        print(f"✅ Audio valide : {audio_path} — {detail}")
    else:
        print(f"❌ Audio invalide : {audio_path} — {detail}")
        problems.append("Audio source invalide")

    section("5. RESSOURCES APPLIO")
    # On ne prétend pas qu'un simple nom de fichier prouve le chargement.
    # prerequisites + l'inférence réelle constituent la validation fiable.
    print("ℹ️ RMVPE / ContentVec sont téléchargés par setup.py via")
    print("   `core.py prerequisites --models --exe`.")
    print("ℹ️ Leur chargement effectif sera confirmé par l'inférence Niveau 1.")

    section("RÉSUMÉ")
    if problems:
        print(f"❌ {len(problems)} problème(s) bloquant(s) :")
        for problem in problems:
            print(f"   - {problem}")
        print("\nAucune inférence ne doit être lancée.")
        sys.exit(1)

    print("✅ Préflight réussi : environnement GPU, modèle et audio sont prêts.")
    print("   L'inférence effectuera une seconde vérification de la CLI Applio.")


if __name__ == "__main__":
    main()
