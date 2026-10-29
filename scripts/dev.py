"""Portable local environment setup; Make remains the development entry point."""

import argparse
import hashlib
import json
import logging
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
logger = logging.getLogger(__name__)


def download_models() -> None:
    manifest = json.loads((ROOT / "src/trueme/models/manifest.json").read_text("utf-8"))
    destination = ROOT / "models"
    destination.mkdir(exist_ok=True)
    for model in manifest:
        target = destination / model["filename"]
        if target.exists():
            with target.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if digest != model["sha256"]:
                raise SystemExit(
                    f"Checksum mismatch for {target.name}; move or remove it before retrying."
                )
            logger.info("Already verified: %s", target.name)
            continue
        with tempfile.TemporaryDirectory(prefix=".download-", dir=destination) as temporary:
            downloaded = Path(temporary) / target.name
            logger.info("Downloading %s", target.name)
            subprocess.run([
                "curl.exe" if sys.platform == "win32" else "curl",
                "-fL", "--output", str(downloaded), model["download_url"],
            ], check=True)
            with downloaded.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if digest != model["sha256"]:
                raise SystemExit(f"Checksum mismatch for {target.name}; download discarded.")
            downloaded.replace(target)
            logger.info("Verified: %s", target.name)


def setup(device: str) -> None:
    if not (3, 11) <= sys.version_info[:2] < (3, 14):
        raise SystemExit("Setup requires Python 3.11-3.13; set make PYTHON to its executable.")
    environment = ROOT / ".venv"
    python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if not python.exists():
        venv.EnvBuilder(with_pip=True).create(environment)
    installed = json.loads(subprocess.check_output(
        [str(python), "-m", "pip", "list", "--format=json"], text=True
    ))
    names = {item["name"].lower() for item in installed}
    opposite = "onnxruntime-gpu" if device == "cpu" else "onnxruntime"
    if opposite in names:
        raise SystemExit(
            f"Existing .venv contains {opposite}. Create a fresh .venv before switching "
            "CPU/GPU; the distributions must never coexist."
        )
    subprocess.run([
        str(python), "-m", "pip", "install", "-c", "requirements-lock.txt",
        "setuptools==80.9.0", "wheel==0.45.1", "-e", f".[{device},dev]",
    ], cwd=ROOT, check=True)
    subprocess.run([str(python), "-m", "pip", "check"], check=True)


def main() -> None:
    sys.path.insert(0, str(ROOT / "src"))
    from trueme.logging_config import configure_logging

    configure_logging()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["help", "setup", "download-models"])
    parser.add_argument("--device", choices=["cpu", "gpu"], default="cpu")
    args = parser.parse_args()
    if args.command == "setup":
        setup(args.device)
    elif args.command == "download-models":
        try:
            download_models()
        except (OSError, subprocess.CalledProcessError) as exc:
            raise SystemExit(f"Model download failed: {exc}. Ensure curl is installed.") from exc
    else:
        print("make setup DEVICE=cpu|gpu  Create local Python environment")
        print("make download-models      Download and verify weights into models/")
        print("make run                  Start local web page using models/")
        print("make test                 Run unit tests (no weights or photos)")
        print("make lint                 Check Python style and errors")
        print("make build                Build wheel and source distribution")
        print("Set PYTHON to a Python 3.11-3.13 executable when running setup.")


if __name__ == "__main__":
    main()
