"""Portable local environment setup; Make remains the development entry point."""

import argparse
import json
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def setup(device: str) -> None:
    if sys.version_info[:2] != (3, 11):
        raise SystemExit("Setup requires Python 3.11; set make PYTHON to its executable.")
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["help", "setup"])
    parser.add_argument("--device", choices=["cpu", "gpu"], default="cpu")
    args = parser.parse_args()
    if args.command == "setup":
        setup(args.device)
    else:
        print("make setup DEVICE=cpu|gpu  Create local Python 3.11 environment")
        print("make test                 Run unit tests (no weights or photos)")
        print("make lint                 Check Python style and errors")
        print("make build                Build wheel and source distribution")
        print("Set PYTHON to a Python 3.11 executable when running setup.")


if __name__ == "__main__":
    main()
