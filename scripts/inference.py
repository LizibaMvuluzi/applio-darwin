"""
inference.py — NIVEAU 1 : conversion vocale avec le modèle 'darwin'.

N'affiche jamais un simple "le fichier n'a pas été créé" : montre toujours
la commande exécutée, le code retour, stdout et stderr en entier, et
sauvegarde tout dans un fichier log sur Google Drive (survit même si la
session Colab plante juste après).

Usage :
    python scripts/inference.py --config config/config.json
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.json")
    parser.add_argument("--input-audio", default=None, help="Surcharge le chemin audio du config.json")
    args = parser.parse_args()

    config = load_config(args.config)
    log_lines = []

    def log(msg):
        print(msg)
        log_lines.append(str(msg))

    model_name = config["model_name"]
    install_dir = Path(config["applio"]["install_dir"])
    drive_root = Path(config["drive"]["root"])
    backup_dir = drive_root / config["drive"]["backup_folder"] / model_name
    export_dir = drive_root / config["drive"]["export_folder"]
    audio_path = Path(args.input_audio) if args.input_audio else drive_root / config["drive"]["input_audio"]

    p = config["inference"]

    log("=" * 60)
    log(f"INFÉRENCE — modèle : {model_name}")
    log("=" * 60)

    export_dir.mkdir(parents=True, exist_ok=True)

    def fail(message):
        log(message)
        fail_log = export_dir / f"inference_log_{datetime.now():%Y%m%d_%H%M%S}_FAILED.txt"
        fail_log.write_text("\n".join(log_lines), encoding="utf-8")
        print(f"\\n📄 Diagnostic sauvegardé : {fail_log}")
        sys.exit(1)

    if not install_dir.exists() or not (install_dir / "core.py").exists():
        fail("❌ Applio n'est pas installé. Lance d'abord scripts/setup.py")

    if not backup_dir.exists():
        fail(f"❌ Dossier modèle introuvable : {backup_dir}")

    pth_candidates = sorted(backup_dir.glob("*.pth"), key=lambda x: x.stat().st_mtime, reverse=True)
    if not pth_candidates:
        fail(f"❌ Aucun fichier .pth dans {backup_dir}")
    pth_file = str(pth_candidates[0])

    # La CLI Applio actuelle exige un fichier .index pour l'inférence.
    # On privilégie l'index qui porte le même nom de base que le .pth.
    matching_index = backup_dir / f"{Path(pth_file).stem}.index"
    if matching_index.exists():
        index_file = str(matching_index)
    else:
        index_candidates = sorted(backup_dir.glob("*.index"), key=lambda x: x.stat().st_mtime, reverse=True)
        index_file = str(index_candidates[0]) if index_candidates else ""

    if not index_file:
        fail(f"❌ Aucun fichier .index dans {backup_dir}. La version actuelle d'Applio exige --index-path pour l'inférence.")

    if not audio_path.exists():
        fail(f"❌ Audio introuvable : {audio_path}")
    output_path = export_dir / f"{model_name}_output.wav"
    output_path.unlink(missing_ok=True)

    log(f"Modèle .pth   : {pth_file}")
    log(f"Modèle .index : {index_file or '(aucun)'}")
    log(f"Audio source  : {audio_path}")
    log(f"Sortie prévue : {output_path}")

    cmd = [
        sys.executable, "core.py", "infer",
        "--pitch", str(p["pitch"]),
        "--volume-envelope", str(p["volume_envelope"]),
        "--index-rate", str(p["index_rate"]),
        "--protect", str(p["protect"]),
        "--f0-method", p["f0_method"],
        "--input-path", str(audio_path),
        "--output-path", str(output_path),
        "--pth-path", pth_file,
        "--index-path", index_file,
        "--clean-strength", str(p["clean_strength"]),
        "--export-format", p["export_format"],
        "--embedder-model", p["embedder_model"],
        "--formant-qfrency", str(p["formant_qfrency"]),
        "--formant-timbre", str(p["formant_timbre"]),
    ]

    if p.get("clean_audio", False):
        cmd.insert(cmd.index("--clean-strength"), "--clean-audio")

    if p.get("formant_shifting", False):
        cmd.insert(cmd.index("--formant-qfrency"), "--formant-shifting")

    log("\nCommande exécutée :")
    log(" ".join(cmd))

    result = subprocess.run(cmd, cwd=str(install_dir), capture_output=True, text=True)

    log(f"\nCode de retour : {result.returncode}")
    log("\n--- STDOUT ---")
    log(result.stdout or "(vide)")
    log("\n--- STDERR ---")
    log(result.stderr or "(vide)")

    log("\n" + "=" * 60)
    if output_path.exists():
        log(f"✅ SUCCÈS — fichier généré : {output_path}")
    else:
        log(f"❌ ÉCHEC — {output_path} n'a pas été créé.")
    log("=" * 60)

    log_path = export_dir / f"inference_log_{datetime.now():%Y%m%d_%H%M%S}.txt"
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"\n📄 Log complet sauvegardé : {log_path}")

    sys.exit(0 if output_path.exists() else 1)


if __name__ == "__main__":
    main()
