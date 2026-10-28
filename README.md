# TrueMe

TrueMe is a local Python CLI that compares a reference (enrollment) photo with a
probe (camera-condition) photo using YuNet detection and SFace embeddings.
Use only your own photos or photos used with explicit consent. Each image must
contain exactly one face. Batch processing and live capture are outside this MVP.

The raw cosine similarity is model-specific: it is not a confidence percentage,
identity judgment, or probability of passing verification. There is no universal
acceptance threshold. Lighting, pose, image quality, and alignment affect results.

## A score, with a little personality

![SFace example scores with offsets from the published LFW threshold and playful captions](docs/assets/sface-score-guide.svg)

The numerical reference comes from the [OpenCV 4.12 SFace tutorial](https://docs.opencv.org/4.12.0/d0/dd4/tutorial_dnn_face.html):
its published cosine thresholds are 0.363 (LFW), 0.340 (CALFW), 0.275 (CPLFW),
0.277 (AgeDB-30), and 0.212 (CFP-FP). The
[OpenCV Zoo demo at our pinned revision](https://github.com/opencv/opencv_zoo/blob/48b10fa505aeb51fbd127fc60a5c660040e823b7/models/face_recognition_sface/sface.py)
also uses 0.363. These are dataset-specific references, not a ranking of security
systems or thresholds calibrated for TrueMe's pipeline and user photos.

The illustration uses example scores, not calibrated ranges. Its offsets are
simply `score - 0.363`; captions are playful editorial copy. A larger offset is
not a confidence estimate, identity verdict, or guarantee of acceptance. TrueMe
continues to report raw cosine similarity without applying a pass/fail threshold.

## Installation

Python 3.11 and GNU Make are required for development. Windows is the primary
target; Linux and macOS share the same portable pipeline. See
[installation](docs/installation.md) for PowerShell setup and separate CPU/GPU
environments, and [models](docs/models.md) for verified sources, weight licenses,
checksums, acquisition commands, and preprocessing.

```powershell
make setup DEVICE=cpu PYTHON=python
.\.venv\Scripts\trueme.exe --help
.\.venv\Scripts\trueme.exe --version
```

On Linux/macOS use `.venv/bin/trueme` or `.venv/bin/python -m trueme`.
No command downloads model weights automatically. Original code is MIT;
model weights and dependencies retain their own licenses and notices.

## Usage

After acquiring the two documented model files:

```powershell
.\.venv\Scripts\trueme.exe models list --json
.\.venv\Scripts\trueme.exe doctor --model-dir "C:\Models\TrueMe" --json
.\.venv\Scripts\trueme.exe compare --reference "photos\a1.jpg" --probe "photos\p1.jpg" --model-dir "C:\Models\TrueMe" --device cpu
.\.venv\Scripts\trueme.exe compare --reference "photos\a1.jpg" --probe "photos\p2.jpg" --model-dir "C:\Models\TrueMe" --json --output "result.report.json"
```

Run each pair independently. JPEG, PNG, and WebP are accepted, including Unicode
paths. EXIF orientation is applied in memory. Animated and multi-frame images
are rejected. Small face, blur, and exposure warnings are heuristics, not
calibrated quality measurements.

Model directory precedence is `--model-dir`, then `TRUEME_MODEL_DIR`, then the
platform's per-user directory documented in the installation guide.

`--device auto` attempts CUDA and falls back to CPU with a recorded reason when
CUDA is unavailable or fails initialization/execution. `--device cuda` requires
successful CUDA session configuration and execution; failure is an error.
`--device cpu` forces CPU. Configured providers do not prove every operation ran
on the GPU. `doctor` distinguishes provider availability and session initialization
from inference; use `compare` to exercise actual inference. `--verbose` on
`compare` prints device diagnostics to stderr.

## JSON and reports

`--json` emits one JSON object on stdout; errors also use JSON and a nonzero exit
status. Diagnostics go to stderr. Success uses schema `1.0`:

- `schema_version`, timezone-aware `timestamp`, `application_version`;
- `models`: model identifiers and hashes;
- `device`: requested device, configured providers, fallback details;
- `inputs`: `reference` and `probe` basenames;
- `cosine_similarity`, `quality_warnings`, and `interpretation`.

Errors contain `error.type`, `error.message`, and `error.exit_code`.
No NaN or infinity is emitted. `--output` explicitly exports the same report as
JSON. Existing files require `--overwrite`; input images and aliases cannot be
replaced. Parent directories must already exist. Report basenames and scores
may still be sensitive.

| Exit code | Meaning |
| --- | --- |
| 0 | Command completed (doctor findings may describe unavailable capabilities) |
| 2 | Invalid input or command usage |
| 3 | Missing, invalid, or incompatible model |
| 4 | Device initialization or execution failure |
| 5 | Face processing or invalid model output |
| 6 | Unsafe or unwritable report destination |

## Privacy and limitations

Processing is local: no uploads, telemetry, accounts, database, background
service, or automatic history. Inputs are never modified. Crops and embeddings
stay in memory and are not included in reports or logs. Secure memory erasure
is not promised. No identity search, surveillance, identity verification, or
liveness capability is provided.

Missing weights: follow the model acquisition guide and set the model directory.
No/multiple faces: provide a photo containing exactly one clearly visible face.
CUDA failures: check the documented runtime/CUDA/cuDNN combination, or select
CPU. Report errors: choose a new writable file outside the input paths.

## Development and acceptance

```powershell
make test
make lint
make build
```

These targets do not download weights or use personal photos. CI exercises them
on Linux, macOS, and Windows without CUDA. See [architecture](docs/architecture.md)
and [validation](docs/validation.md) for implementation boundaries, actual checks,
and remaining human acceptance work. Configured CI is not evidence of a completed
run on those platforms.
