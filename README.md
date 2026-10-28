<h1 align="center">TrueMe</h1>

<p align="center">Compare a reference photo and a probe photo locally with a Python CLI.</p>

<p align="center">
  <a href="https://github.com/ZhiWei-Ou/trueme/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/ZhiWei-Ou/trueme/ci.yml?branch=main&label=checks" alt="CI status"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/python-%E2%89%A53.11-3776AB?logo=python&logoColor=white" alt="Python 3.11 or newer"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/ZhiWei-Ou/trueme" alt="MIT license"></a>
  <a href="https://github.com/ZhiWei-Ou/trueme/commits/main"><img src="https://img.shields.io/github/last-commit/ZhiWei-Ou/trueme" alt="Last commit"></a>
  <a href="https://github.com/ZhiWei-Ou/trueme/issues"><img src="https://img.shields.io/github/issues/ZhiWei-Ou/trueme" alt="Open issues"></a>
  <a href="https://github.com/ZhiWei-Ou/trueme/stargazers"><img src="https://img.shields.io/github/stars/ZhiWei-Ou/trueme?style=flat" alt="GitHub stars"></a>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> ·
  <a href="#documentation">Documentation</a> ·
  <a href="https://github.com/ZhiWei-Ou/trueme/issues">Issues</a> ·
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

<p align="center">
  <img src="docs/assets/sface-score-guide.svg" alt="SFace cosine similarity scale: scores below 0.363 are below the published LFW reference; scores at or above it meet the reference" width="640">
</p>

TrueMe uses YuNet to detect and align faces, then SFace to compare their features.
Use your own photos or photos used with explicit consent. Scores describe
similarity under this model; they are not confidence percentages, identity
verdicts, or predictions of third-party verification acceptance.

## Features

- **One pair, one score.** Compare an enrollment/reference photo with a probe
  representing camera conditions; require exactly one face in each image.
- **Local processing.** No uploads, telemetry, accounts, or automatic history.
  Inputs remain unchanged; crops and embeddings stay in memory.
- **Photo handling.** JPEG, PNG, and WebP, Unicode paths, EXIF orientation, and
  heuristic warnings for small faces, blur, and extreme exposure.
- **Explicit device control.** CPU or CUDA, with observable automatic CPU fallback
  and strict failure when explicitly requested CUDA cannot run.
- **Scriptable results.** Structured JSON, stable exit codes, environment
  diagnostics, and optional reports protected against overwriting input images.

## Quick Start

The steps below use a Unix shell (Linux or macOS) and the CPU runtime. Windows
PowerShell and CUDA setup are covered in the [installation guide](docs/installation.md).

**Prerequisites:** Python 3.11 or newer (currently up to 3.13, the newest version
with ONNX Runtime 1.20 wheels), Git, GNU Make, and `curl`.

### 1. Set up the environment

```sh
git clone https://github.com/ZhiWei-Ou/trueme.git
cd trueme
make setup DEVICE=cpu
.venv/bin/trueme --version
```

`make setup` creates a project-local `.venv` and installs pinned dependencies;
activation is unnecessary. It uses `python3` by default; if that is not 3.11–3.13,
pass the interpreter explicitly, for example `make setup PYTHON=python3.12 DEVICE=cpu`.
Use `gmake` where GNU Make has that name.

### 2. Download the models

Weights are not included in Git. Fetch the two pinned OpenCV Zoo models:

```sh
mkdir -p models
base=https://media.githubusercontent.com/media/opencv/opencv_zoo/48b10fa505aeb51fbd127fc60a5c660040e823b7/models
curl -fL -o models/face_detection_yunet_2023mar.onnx "$base/face_detection_yunet/face_detection_yunet_2023mar.onnx"
curl -fL -o models/face_recognition_sface_2021dec.onnx "$base/face_recognition_sface/face_recognition_sface_2021dec.onnx"
.venv/bin/trueme doctor --model-dir models
```

TrueMe verifies both checksums before initialization; sources and licenses are in
the [model guide](docs/models.md). In a CPU installation, `doctor` reporting
unavailable CUDA is expected; CPU initialization should succeed.

### 3. Compare two photos

Place two consented, single-frame photos in the project root as `reference.jpg`
and `probe.jpg`, each containing exactly one face:

```sh
.venv/bin/trueme compare --reference reference.jpg --probe probe.jpg --model-dir models --device cpu
```

The result includes cosine similarity, model names, configured providers, any
quality warnings, and an interpretation notice. A higher score means greater
feature similarity under SFace; TrueMe applies no pass/fail threshold.

## Usage

### Inspect the installation

```sh
.venv/bin/trueme --help
.venv/bin/trueme models list --json
.venv/bin/trueme doctor --model-dir models --json
```

Help, version, and basic diagnostics work without weights. `doctor` distinguishes
provider enumeration and session initialization from actual inference. Use
`compare` to exercise inference; `--verbose` adds device diagnostics to stderr.

### Export a report

```sh
.venv/bin/trueme compare --reference reference.jpg --probe probe.jpg --model-dir models --json --output result.report.json
```

`--json` writes one JSON object to stdout, including errors; diagnostics go to
stderr. `--output` explicitly saves a report. Existing reports require
`--overwrite`; input images and their aliases cannot be replaced. The parent
directory must exist. Filenames and scores in reports may still be sensitive.

<details>
<summary>JSON schema and exit codes</summary>

Success reports use schema `1.0` and include `schema_version`, a timezone-aware
`timestamp`, `application_version`, model names/versions/hashes, requested device,
configured providers and fallback details, reference/probe basenames,
`cosine_similarity`, `quality_warnings`, and `interpretation`.
Images, embeddings, and full input paths are excluded. NaN and infinity are rejected.
Errors contain `error.type`, `error.message`, and `error.exit_code`.

| Code | Meaning |
| --- | --- |
| 0 | Completed; doctor may still report unavailable capabilities |
| 2 | Invalid input or command usage |
| 3 | Missing, invalid, or incompatible model |
| 4 | Device initialization or execution failure |
| 5 | Face processing or invalid model output |
| 6 | Unsafe or unwritable report destination |

</details>

<a id="a-score-with-a-little-personality"></a>

<details>
<summary>What the score illustration is based on</summary>

The [OpenCV 4.12 SFace tutorial](https://docs.opencv.org/4.12.0/d0/dd4/tutorial_dnn_face.html)
reports a cosine threshold of **0.363** for LFW. The
[OpenCV Zoo demo at our pinned revision](https://github.com/opencv/opencv_zoo/blob/48b10fa505aeb51fbd127fc60a5c660040e823b7/models/face_recognition_sface/sface.py)
uses the same value. The illustration places a score relative to that reference:

| Cosine score | Rough evaluation |
| --- | --- |
| Below 0.363 | Below the reference |
| At least 0.363 | Meets the reference |

"Meets the reference" means reaching the published SFace/LFW threshold, not a
calibrated TrueMe acceptance decision. This guide does not establish identity,
predict door access or attendance acceptance, or certify ID-photo compliance.
TrueMe's CLI continues to report raw cosine similarity without applying a threshold.

</details>

### Input limits and common errors

Run each reference/probe pair independently. Batch processing and live capture
are outside this MVP. Animated and multi-frame files, including MPO containers
with `.jpg` extensions, are rejected; explicitly export the intended single frame.
No/multiple-face errors require an input containing exactly one visible face.
Quality warnings are heuristics; lighting, pose, and alignment can affect scores.

For missing weights, follow the model guide and check the model directory.
For CUDA failures, check the GPU setup or select CPU. Report errors require a
writable destination distinct from the inputs. The CLI offers no identity search,
surveillance, liveness checks, or identity verification, and does not promise
secure memory erasure.

## Configuration

| Setting | Purpose | Default |
| --- | --- | --- |
| `--model-dir` | Directory containing both model files | Environment variable, then per-user storage |
| `TRUEME_MODEL_DIR` | Model directory when the option is omitted | Unset |
| `--device auto\|cpu\|cuda` | Select inference device | `auto` |
| `--output` | Explicit JSON report destination | No file written |
| `--overwrite` | Allow replacement of an existing report | Off |

Model lookup uses `--model-dir` → `TRUEME_MODEL_DIR` → the
[platform's per-user directory](docs/installation.md#model-storage). It does not
automatically search the project's `models/` directory. To skip `--model-dir`
in the current shell, run `export TRUEME_MODEL_DIR="$PWD/models"`.

`auto` attempts CUDA and reports CPU fallback on unavailability, initialization
failure, or execution failure. `cuda` fails instead of silently using a CPU-only
session; `cpu` forces CPU. Configured providers do not prove every operation ran
on GPU. CPU and GPU environments must never contain both `onnxruntime` and
`onnxruntime-gpu`; see [GPU setup](docs/installation.md#cpu-and-nvidia-cuda-environments).

## Documentation

| Guide | Use it for |
| --- | --- |
| [Installation](docs/installation.md) | Windows, macOS/Linux, CPU/GPU setup, model directories |
| [Models](docs/models.md) | Acquisition, licenses, checksums, preprocessing, device behavior |
| [Architecture](docs/architecture.md) | Module responsibilities and platform boundaries |
| [Validation](docs/validation.md) | Actual CPU/CUDA checks and human acceptance steps |
| [Security](SECURITY.md) | Privacy and vulnerability reporting guidance |

Windows is the primary target; Linux, macOS, and Windows CI jobs are configured.
Recorded local runtime validation covers Linux CPU and CUDA. Native Windows/macOS
and hosted CI execution are not established by that validation record.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) for scope, implementation conventions,
and privacy requirements. Report bugs or ideas through
[GitHub Issues](https://github.com/ZhiWei-Ou/trueme/issues). After setup, run:

```sh
make test
make lint
make build
```

These targets do not download weights or process personal photos. Keep photos,
weights, reports, and environments out of commits. Builds produce a wheel and
source archive under `dist/`.

## License

Original code is licensed under [MIT](LICENSE). Dependencies and model weights
retain separate licenses and notices; consult the [model licenses](docs/models.md#sources-and-licenses)
before using or redistributing weights.
