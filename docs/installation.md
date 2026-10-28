# Installation and development

Use 64-bit Python 3.11 or newer (currently up to 3.13, the newest version with
ONNX Runtime 1.20 wheels) and GNU Make. The application targets Windows, Linux,
and macOS; actual validation coverage is recorded in the acceptance handoff.
No virtual-environment activation or PowerShell execution-policy change is needed.

## Windows (PowerShell)

Install Python 3.11-3.13 from python.org with the Python launcher. Install GNU Make
(for example, `choco install make` if Chocolatey is already installed), then open
a new PowerShell with `make` on PATH. Native GNU Make uses the command interpreter;
the recipes require neither WSL nor Unix utilities. In the repository:

```powershell
make setup PYTHON="py -3.11" DEVICE=cpu
.\.venv\Scripts\trueme.exe --help
make test
make lint
make build
```

Install the Microsoft Visual C++ runtime if ONNX Runtime reports missing native
runtime DLLs. Use the [official ORT installation guidance](https://onnxruntime.ai/docs/install/).

## Linux and macOS

Install Python 3.11-3.13 and GNU Make through your normal OS tooling. On systems where
GNU Make is named `gmake`, use that name for the commands below.

```sh
make setup PYTHON=python3.11 DEVICE=cpu
.venv/bin/trueme --help
make test
make lint
make build
```

Setup creates only the project's `.venv`, installs the editable project and
pinned development dependencies, and runs `pip check`. `pyproject.toml` defines
all direct dependencies; `requirements-lock.txt` constrains transitives for the
tested environment. Python 3.14 and newer are excluded until the pinned ONNX Runtime
provides wheels for them. Build produces a wheel and source archive under `dist/`; weights,
photos, reports, and environments are not packaged. The wheel includes the model
manifest and loads it via package resources.

## CPU and NVIDIA CUDA environments

Choose one runtime distribution per environment. CPU uses `onnxruntime==1.20.1`;
GPU uses `onnxruntime-gpu==1.20.2`. Setup refuses to add a runtime when the opposite
one is already installed. To change variants, remove or rename the local `.venv`
first, then run setup again. Never install both extras together.

```powershell
make setup PYTHON="py -3.11" DEVICE=gpu
.\.venv\Scripts\trueme.exe doctor
```

The pinned PyPI GPU build uses CUDA 12.x and cuDNN 9.x according to the
[official compatibility table](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html#requirements).
Install a compatible NVIDIA driver, CUDA runtime and cuDNN libraries; ensure
native libraries are discoverable (`PATH` on Windows, the dynamic loader path on
Linux). The cuDNN 8 and 9 major versions are not interchangeable. macOS uses CPU;
this project does not provide a CUDA runtime there. Dependency installation does
not establish usable GPU inference: provider availability, session initialization,
and real execution are separate checks. No GPU success is implied by the pins.

### Optional Linux CUDA runtime wheels

For Linux x86_64, the optional `requirements-gpu-runtime.txt` pins CUDA 12.8
runtime libraries and cuDNN 9.8 separately from the Python application.
[NVIDIA's cuDNN 9.8 support matrix](https://docs.nvidia.com/deeplearning/cudnn/backend/v9.8.0/reference/support-matrix.html)
lists Blackwell support with CUDA 12.8. A compatible host NVIDIA driver is still
required; these wheels do not install one. Starting with a fresh `.venv`:

```sh
make setup PYTHON=python3.11 DEVICE=gpu
.venv/bin/python -m pip install -r requirements-gpu-runtime.txt
CUDA_SITE="$(.venv/bin/python -c 'import sysconfig; print(sysconfig.get_path("purelib"))')"
for lib in "$CUDA_SITE"/nvidia/*/lib; do
    export LD_LIBRARY_PATH="$lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
done
.venv/bin/python -m pip check
.venv/bin/trueme doctor --model-dir models --json
.venv/bin/trueme compare --reference photos/a1.jpg --probe photos/p2.jpg --model-dir models --device cuda --json
```

On WSL, if the CUDA driver is not on the default loader path, also run
`export LD_LIBRARY_PATH="/usr/lib/wsl/lib:$LD_LIBRARY_PATH"` before the TrueMe
commands. These environment settings apply to the current shell only. On native
Windows, use the CUDA/cuDNN installation and DLL search-path instructions above;
the Linux wheel recipe is not a Windows validation claim.

Model downloads are separate explicit steps in [models.md](models.md). Setup,
unit tests, lint, and builds never download model weights or inspect private photos.
For installing a built wheel in a fresh local Python 3.11-3.13 virtual environment,
use `python -m pip install 'dist/trueme-0.1.0-py3-none-any.whl[cpu]'` (or `[gpu]`),
using the new environment's Python executable.

## Model storage

The CLI resolves `--model-dir`, then `TRUEME_MODEL_DIR`, then the per-user default:

| Platform | Default |
| --- | --- |
| Windows | `%LOCALAPPDATA%\TrueMe\models` (fallback: `~/AppData/Local/TrueMe/models`) |
| macOS | `~/Library/Application Support/TrueMe/models` |
| Linux | `$XDG_DATA_HOME/trueme/models`, or `~/.local/share/trueme/models` |

A relative `XDG_DATA_HOME` is ignored as required by the XDG convention. Model
lookup never creates directories or downloads files. Explicit and environment
model paths support `~`, and relative paths resolve against the invocation directory.
