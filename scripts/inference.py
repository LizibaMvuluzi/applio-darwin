"""
inference.py — NIVEAU 1 : conversion vocale du modèle 'darwin'.

Le script est volontairement strict :
- GPU CUDA obligatoire ;
- modèle et index doivent s'appeler exactement darwin.pth/darwin.index ;
- la CLI réelle d'Applio est vérifiée avec `core.py infer --help` ;
- aucun fallback silencieux ;
- la sortie WAV est validée avant d'être déclarée réussie.

Usage:
    python scripts/inference.py --config config/config.json
"""

import argparse
import json
import subprocess
import sys
import wave
from datetime import datetime
from pathlib import Path


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_wav(path: Path) -> tuple[bool, str]:
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
            return True, f"{duration:.2f}s · {rate} Hz · {path.stat().st_size / 1024:.1f} Ko"
    except (wave.Error, EOFError) as exc:
        return False, f"WAV illisible : {exc}"


def help_contains_flags(help_text: str, flags: list[str]) -> list[str]:
    """Retourne les options réellement visibles dans l'aide qui manquent.

    On cherche les noms d'options comme tokens complets, pas comme sous-chaînes
    arbitraires. Cela évite les faux positifs dus à une phrase de description.
    """
    tokens = set()
    for token in help_text.replace(",", " ").split():
        token = token.strip("()[]{}:;")
        if token.startswith("--"):
            tokens.add(token.split("=")[0])
    return [flag for flag in flags if flag not in tokens]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.json")
    parser.add_argument("--input-audio", default=None)
    args = parser.parse_args()

    config = load_config(args.config)
    if config.get("model_name") != "darwin":
        raise SystemExit("❌ model_name doit être exactement 'darwin'.")

    model_name = "darwin"
    install_dir = Path(config["applio"]["install_dir"])
    drive_root = Path(config["drive"]["root"])
    backup_dir = drive_root / config["drive"]["backup_folder"] / model_name
    export_dir = drive_root / config["drive"]["export_folder"]
    audio_path = Path(args.input_audio) if args.input_audio else drive_root / config["drive"]["input_audio"]
    p = config["inference"]
    if str(p.get("export_format", "WAV")).upper() != "WAV":
        raise SystemExit("❌ Le Niveau 1 de ce projet exige export_format='WAV'.")

    export_dir.mkdir(parents=True, exist_ok=True)
    log_lines = []

    def log(msg):
        print(msg)
        log_lines.append(str(msg))

    def fail(message):
        log(message)
        fail_log = export_dir / f"inference_log_{datetime.now():%Y%m%d_%H%M%S}_FAILED.txt"
        fail_log.write_text("\n".join(log_lines), encoding="utf-8")
        print(f"\n📄 Diagnostic sauvegardé : {fail_log}")
        raise SystemExit(1)

    log("=" * 60)
    log(f"INFÉRENCE — modèle : {model_name}")
    log("=" * 60)

    if not install_dir.exists() or not (install_dir / "core.py").exists():
        fail(f"❌ Applio introuvable dans {install_dir}. Lance d'abord setup.py.")

    # Le script doit être lancé avec le Python du venv Applio.
    if Path(sys.executable).resolve().parent.name != "bin" or "applio-env" not in str(Path(sys.executable)):
        fail(
            f"❌ Mauvais interpréteur Python : {sys.executable}\n"
            "   Le notebook doit appeler inference.py avec APPLIO_PYTHON."
        )

    # GPU obligatoire : l'inférence ne bascule jamais silencieusement sur CPU.
    try:
        import torch
        if not torch.cuda.is_available():
            fail(
                "❌ Aucun GPU CUDA exploitable dans l'environnement Applio.\n"
                "   Dans Colab : Runtime → Change runtime type → GPU, puis relance le notebook."
            )
        log(f"✅ GPU : {torch.cuda.get_device_name(0)}")
        log(f"   PyTorch : {torch.__version__} · CUDA : {torch.version.cuda}")
    except Exception as exc:
        fail(f"❌ Impossible de valider CUDA dans le Python Applio : {exc}")

    if not backup_dir.exists():
        fail(f"❌ Dossier modèle introuvable : {backup_dir}")

    pth_path = backup_dir / f"{model_name}.pth"
    index_path = backup_dir / f"{model_name}.index"

    if not pth_path.is_file() or pth_path.stat().st_size == 0:
        fail(
            f"❌ Fichier modèle exact requis : {pth_path}\n"
            "   Le fichier doit s'appeler exactement darwin.pth et ne pas être vide."
        )
    if not index_path.is_file() or index_path.stat().st_size == 0:
        fail(
            f"❌ Fichier index exact requis : {index_path}\n"
            "   Le fichier doit s'appeler exactement darwin.index et ne pas être vide."
        )

    ok, detail = validate_wav(audio_path)
    if not ok:
        fail(f"❌ Audio source invalide : {audio_path} — {detail}")

    output_path = export_dir / f"{model_name}_output.wav"
    output_path.unlink(missing_ok=True)

    log(f"Modèle .pth   : {pth_path}")
    log(f"Modèle .index : {index_path}")
    log(f"Audio source  : {audio_path} — {detail}")
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
        "--pth-path", str(pth_path),
        "--index-path", str(index_path),
        "--clean-strength", str(p["clean_strength"]),
        "--export-format", p["export_format"],
        "--embedder-model", p["embedder_model"],
        "--formant-qfrency", str(p["formant_qfrency"]),
        "--formant-timbre", str(p["formant_timbre"]),
    ]
    if p.get("clean_audio", False):
        cmd.append("--clean-audio")
    if p.get("formant_shifting", False):
        cmd.append("--formant-shifting")

    # Contrat CLI réel de la version Applio installée.
    help_result = subprocess.run(
        [sys.executable, "core.py", "infer", "--help"],
        cwd=str(install_dir), capture_output=True, text=True, timeout=60,
    )
    help_text = help_result.stdout + help_result.stderr
    if help_result.returncode != 0:
        fail(
            f"❌ 'core.py infer --help' a échoué (code {help_result.returncode}).\n"
            "   Aucune inférence n'a été lancée.\n" + help_text
        )
    if not help_text.strip():
        fail("❌ 'core.py infer --help' ne renvoie aucune aide. Aucune inférence n'a été lancée.")

    flags_sent = [tok for tok in cmd if tok.startswith("--")]
    missing = help_contains_flags(help_text, flags_sent)
    if missing:
        fail(
            "❌ Options CLI absentes de la version Applio installée : "
            + ", ".join(missing)
            + "\n   Aucune inférence n'a été lancée."
        )

    log("\nCommande exécutée :")
    log(" ".join(cmd))
    result = subprocess.run(cmd, cwd=str(install_dir), capture_output=True, text=True)

    log(f"\nCode de retour : {result.returncode}")
    log("\n--- STDOUT ---")
    log(result.stdout or "(vide)")
    log("\n--- STDERR ---")
    log(result.stderr or "(vide)")

    ok, detail = validate_wav(output_path)
    if result.returncode != 0:
        log(f"❌ ÉCHEC — Applio a retourné le code {result.returncode}.")
        success = False
    elif not ok:
        log(f"❌ ÉCHEC — sortie WAV invalide : {detail}")
        success = False
    else:
        log(f"✅ SUCCÈS — fichier généré : {output_path}")
        log(f"   {detail}")
        success = True

    log("=" * 60)
    log_path = export_dir / f"inference_log_{datetime.now():%Y%m%d_%H%M%S}.txt"
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"\n📄 Log complet sauvegardé : {log_path}")
    raise SystemExit(0 if success else 1)


if __name__ == "__main__":
    main()
