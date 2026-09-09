"""
check_environment.py — Diagnostic complet avant inférence ou entraînement.

Vérifie, dans l'ordre, tout ce qui peut manquer :
- installation d'Applio et point d'entrée (core.py)
- ressources critiques (RMVPE, ContentVec)
- disponibilité GPU
- présence du modèle (.pth + .index)
- présence et lisibilité du fichier audio source

N'échoue jamais silencieusement : chaque vérification affiche clairement
✅ ou ❌, et explique quoi faire en cas de problème.

Usage :
    python scripts/check_environment.py --config config/config.json
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.json")
    args = parser.parse_args()

    config = load_config(args.config)
    problems = []

    install_dir = Path(config["applio"]["install_dir"])
    model_name = config["model_name"]
    drive_root = Path(config["drive"]["root"])
    backup_dir = drive_root / config["drive"]["backup_folder"] / model_name
    audio_path = drive_root / config["drive"]["input_audio"]

    # 1. Applio installé ?
    section("1. INSTALLATION APPLIO")
    core_py = install_dir / "core.py"
    if core_py.exists():
        print(f"✅ core.py trouvé : {core_py}")
    else:
        print(f"❌ core.py introuvable dans {install_dir}")
        print("   → Lance d'abord : python scripts/setup.py --config config/config.json")
        problems.append("Applio non installé")

    # 2. Version Applio (si détectable)
    if core_py.exists():
        try:
            result = subprocess.run(
                [sys.executable, "core.py", "--version"],
                cwd=str(install_dir), capture_output=True, text=True, timeout=30,
            )
            print(f"   Version : {result.stdout.strip() or '(non détectée)'}")
        except Exception as e:
            print(f"   ⚠️ Impossible de lire la version : {e}")

    # 3. Ressources critiques (RMVPE, ContentVec)
    section("2. RESSOURCES CRITIQUES")
    if install_dir.exists():
        rmvpe_found = list(install_dir.rglob("*rmvpe*"))
        embedder_found = list(install_dir.rglob("*contentvec*")) + list(install_dir.rglob("*hubert*"))

        print(f"RMVPE : {len(rmvpe_found)} fichier(s) trouvé(s)")
        for p in rmvpe_found[:3]:
            print(f"   {p}")
        if not rmvpe_found:
            print("   ❌ Aucun fichier RMVPE — réexécute scripts/setup.py")
            problems.append("RMVPE manquant")

        print(f"Embedder (ContentVec/Hubert) : {len(embedder_found)} fichier(s) trouvé(s)")
        for p in embedder_found[:3]:
            print(f"   {p}")
        if not embedder_found:
            print("   ❌ Aucun embedder — réexécute scripts/setup.py")
            problems.append("Embedder manquant")
    else:
        print("⏭️  Ignoré (Applio non installé)")

    # 4. GPU
    section("3. GPU")
    try:
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            mem_total = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            print(f"✅ GPU détecté : {name} ({mem_total:.1f} Go VRAM)")
        else:
            print("⚠️ Aucun GPU détecté — l'inférence fonctionnera mais lentement (CPU).")
            print("   Ce n'est jamais garanti sur le plan gratuit de Colab/Kaggle.")
    except ImportError:
        print("⚠️ PyTorch non installé — impossible de vérifier le GPU pour l'instant.")
        print("   Normal si scripts/setup.py n'a pas encore été exécuté.")

    # 5. Modèle (.pth + .index)
    section("4. MODÈLE 'darwin'")
    if backup_dir.exists():
        print(f"✅ Dossier modèle trouvé : {backup_dir}")
        pth_files = list(backup_dir.glob("*.pth"))
        index_files = list(backup_dir.glob("*.index"))

        if pth_files:
            print(f"✅ Fichier(s) .pth : {[p.name for p in pth_files]}")
        else:
            print("❌ Aucun fichier .pth trouvé.")
            problems.append("Fichier .pth manquant")

        if index_files:
            print(f"✅ Fichier(s) .index : {[p.name for p in index_files]}")
        else:
            print("⚠️ Aucun fichier .index (optionnel, mais réduit la précision).")
    else:
        print(f"❌ Dossier modèle introuvable : {backup_dir}")
        print("   → Vérifie que Google Drive est bien monté et que le modèle")
        print("     'darwin' a bien été sauvegardé dans ApplioBackup/darwin/")
        problems.append("Dossier modèle introuvable")

    # 6. Audio source
    section("5. AUDIO SOURCE")
    if audio_path.exists():
        size_mb = audio_path.stat().st_size / (1024 * 1024)
        print(f"✅ Fichier audio trouvé : {audio_path} ({size_mb:.2f} Mo)")
        if size_mb == 0:
            print("❌ Le fichier fait 0 Mo — probablement corrompu ou vide.")
            problems.append("Fichier audio vide")
    else:
        print(f"❌ Fichier audio introuvable : {audio_path}")
        problems.append("Fichier audio introuvable")

    # Résumé
    section("RÉSUMÉ")
    if problems:
        print(f"❌ {len(problems)} problème(s) détecté(s) :")
        for p in problems:
            print(f"   - {p}")
        print("\nCorrige ces points avant de lancer scripts/inference.py")
        sys.exit(1)
    else:
        print("✅ Tout est en ordre. Tu peux lancer :")
        print("   python scripts/inference.py --config config/config.json")


if __name__ == "__main__":
    main()
