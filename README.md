<h1 align="center">TrueMe</h1>

<p align="center">🪞 Did your retouched photo just stop looking like <em>you</em>?<br>See how a face recognition model sees it, entirely offline.</p>

<p align="center">
  <a href="https://github.com/ZhiWei-Ou/trueme/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/ZhiWei-Ou/trueme/ci.yml?branch=main&label=checks" alt="CI status"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/python-%E2%89%A53.11-3776AB?logo=python&logoColor=white" alt="Python 3.11 or newer"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/ZhiWei-Ou/trueme" alt="MIT license"></a>
  <a href="https://github.com/ZhiWei-Ou/trueme/commits/main"><img src="https://img.shields.io/github/last-commit/ZhiWei-Ou/trueme" alt="Last commit"></a>
  <a href="https://github.com/ZhiWei-Ou/trueme/issues"><img src="https://img.shields.io/github/issues/ZhiWei-Ou/trueme" alt="Open issues"></a>
  <a href="https://github.com/ZhiWei-Ou/trueme/stargazers"><img src="https://img.shields.io/github/stars/ZhiWei-Ou/trueme?style=flat" alt="GitHub stars"></a>
</p>

<p align="center">
  <a href="#quick-start">🚀 Quick Start</a> ·
  <a href="#documentation">📚 Documentation</a> ·
  <a href="https://github.com/ZhiWei-Ou/trueme/issues">🐛 Issues</a> ·
  <a href="CONTRIBUTING.md">🤝 Contributing</a>
</p>

<p align="center">
  <img src="docs/assets/sface-score-guide.svg" alt="SFace cosine similarity scale: below 0.363 is below the published LFW reference, 0.363 meets it, and 0.5 or higher is marked as comfortably similar" width="640">
</p>

Smoothed the skin, slimmed the jaw, brightened the eyes ✨, and now the office
gate stares at you blankly? 🚪🤨

Give TrueMe your edited ID, badge, or profile photo and a plain camera shot of
yourself. It scores how similar the two faces are under the SFace model, so you
get a rough hint whether everyday face recognition, such as door access or
check-in kiosks, would still see the same person. 🙂

> [!NOTE]
> The score is a reference, not a guarantee: real systems use their own models,
> thresholds, and liveness checks. Use only your own photos or photos used with
> explicit consent.

## 💼 Everyday uses

| | Situation | What to compare |
| --- | --- | --- |
| 🪪 | About to submit a retouched photo for a work badge, gym card, or campus card | The edited photo vs. a plain selfie taken today |
| 🎚️ | Unsure how far to push the beauty filter | Each edit level vs. the same selfie; see where the score drops |
| 🗂️ | Choosing one enrollment photo out of several shots | Every candidate vs. the same selfie; keep the most similar one |
| 💇 | New haircut, glasses, beard, or a few years have passed | Your old registered photo vs. a fresh selfie; decide whether to update it |
| 💡 | The door camera keeps missing you | Live page with your enrollment photo; see how lighting and angle move the score |
| 👨‍👩‍👧 | Helping family set up their check-in photo | Their photo vs. their selfie, with their consent |

## ✨ Features

- 🎭 **Edited photo vs. real you.** One reference photo, one probe photo or live
  camera, one similarity score with a simple scale to read it.
- 🔒 **Purely local.** Everything runs in a process on your machine: no uploads,
  accounts, or telemetry, and nothing is saved unless you ask for a report.
- 📸 **Live camera page.** `trueme web` scores your webcam against the reference
  in real time.
- 🛠️ **CLI for scripts.** JSON output, stable exit codes, CPU or CUDA.

<a id="quick-start"></a>

## 🚀 Quick Start

Three steps on Linux or macOS with a CPU. 🐧🍎 Windows and CUDA setup are in the
[installation guide](docs/installation.md).

You need Python 3.11–3.13, Git, GNU Make, and `curl`.

### 1️⃣ Install

```sh
git clone https://github.com/ZhiWei-Ou/trueme.git
cd trueme
make setup DEVICE=cpu
```

This creates a project-local `.venv`; no activation needed. If `python3` is not
3.11–3.13, add `PYTHON=python3.12` (or another supported version).

### 2️⃣ Download the models

```sh
make download-models
```

This uses `curl` to download the pinned weights into `models/` and verifies
their SHA-256 checksums. Matching existing files are skipped; mismatched files
are preserved with an error. The weights are not in Git.
Sources and licenses: [model guide](docs/models.md).

### 3️⃣ Open the live page

```sh
.venv/bin/trueme web --model-dir models --device cpu
```

Or run `make run` to start the page with `models/` and automatic device selection.
This uses the project-local virtual environment on Linux, macOS, and Windows.

Open <http://127.0.0.1:8765/>, choose your edited photo as the reference, and
start the camera. Watch the score move as you turn your head. 🎯
Press Ctrl+C to stop; the photo and frames are discarded.

## 🧰 Usage

### Export a reference photo

In the live page, choose a reference photo, then click **Export** beside
**Clear**. Select a size and adjust zoom and horizontal/vertical position in the
preview. Choose JPEG or PNG, then **Download JPEG/PNG** to save through your browser with 300 DPI
metadata. The original photo and background are preserved; the export contains
no camera overlay or comparison score.
Downloads keep the original filename stem and append the selected size, for
example `portrait-two-inch.jpg` or `portrait-50x70mm.png` for a custom size.
PNG preserves existing transparency, shown over a checkerboard in the preview.
JPEG fills transparent areas with white. Selecting PNG does not remove the
background from an opaque photo.

| Preset | Printed size | Pixels at 300 DPI |
| --- | --- | --- |
| Small 1 inch | 22 × 32 mm | 260 × 378 |
| 1 inch | 25 × 35 mm | 295 × 413 |
| Large 1 inch | 33 × 48 mm | 390 × 567 |
| Small 2 inch | 35 × 45 mm | 413 × 531 |
| 2 inch | 35 × 49 mm | 413 × 579 |
| Large 2 inch | 35 × 53 mm | 413 × 626 |
| 5 inch (3.5 × 5 in) | 88.9 × 127 mm | 1050 × 1500 |
| 6 inch (4 × 6 in) | 101.6 × 152.4 mm | 1200 × 1800 |
| 7 inch (5 × 7 in) | 127 × 177.8 mm | 1500 × 2100 |
| 8 inch (6 × 8 in) | 152.4 × 203.2 mm | 1800 × 2400 |

**Custom dimensions** accepts width and height from 10 to 300 mm, including
landscape sizes. Output pixels are rounded from `mm / 25.4 × 300`. The print
presets use exact inch conversions rather than rounded millimeter labels.

These are common size presets, not a certification that a photo meets an
employer's or issuing authority's requirements. Confirm the required dimensions
and background for your use. The app keeps the source and crop in memory and
only saves a file when you explicitly download it. The local backend must be
running to encode the download. A reference retained by the server after a page
reload has no source image in the browser; choose the photo again to export it.

### 🖼️ Compare two photo files

```sh
.venv/bin/trueme compare --reference edited.jpg --probe camera.jpg --model-dir models --device cpu
```

Each photo must contain exactly one face. Add `--json` for machine-readable
output, or `--output result.report.json` to save a report.

### 🎚️ Compare several edits at once

Score every version of an edited photo against the same selfie:

```sh
for photo in edits/*.jpg; do
  score=$(.venv/bin/trueme compare --reference "$photo" --probe selfie.jpg --model-dir models --json |
    python3 -c 'import json, sys; print(json.load(sys.stdin)["cosine_similarity"])')
  printf '%.3f  %s\n' "$score" "$photo"
done | sort -r
```

Each comparison runs independently; there is no batch mode or saved history.

### 🌐 Change the web address

```sh
.venv/bin/trueme web --model-dir models --host 127.0.0.1 --port 9000
```

Keep a loopback host: browsers allow camera access only on `localhost` or HTTPS,
and any other host exposes the page to the network without authentication.

### 📏 Reading the score

| Cosine score | Rough read |
| --- | --- |
| Below 0.363 | 😶 Below the reference — camera, let's get acquainted again |
| 0.363 to below 0.5 | 🙂 Meets the reference |
| 0.5 or higher | 😄 Comfortably you — the camera's warming up to you |

<a id="a-score-with-a-little-personality"></a>

<details>
<summary>🔬 Where these numbers come from</summary>

0.363 is the cosine threshold for LFW reported by the
[OpenCV 4.12 SFace tutorial](https://docs.opencv.org/4.12.0/d0/dd4/tutorial_dnn_face.html)
and used by the
[OpenCV Zoo demo at our pinned revision](https://github.com/opencv/opencv_zoo/blob/48b10fa505aeb51fbd127fc60a5c660040e823b7/models/face_recognition_sface/sface.py).
0.5 is an informal rule of thumb for a comfortable margin; it has no published
source and has not been measured by TrueMe. The captions are for fun.

The score is cosine similarity, not a confidence percentage. It does not
establish identity, predict acceptance by a specific system, or certify ID-photo
compliance. The CLI reports the raw score without applying any threshold.

</details>

<details>
<summary>🧾 JSON output and exit codes</summary>

`--json` prints exactly one JSON object to stdout, including errors; diagnostics
go to stderr through Python's standard-library `logging` package. Use
`compare --verbose` for DEBUG device diagnostics. Logs use UTC ISO 8601 timestamps
and colored levels in terminals, for example `2026-10-29T08:30:00Z INFO Message`.
Only the level is colored; fields are separated by a single space without padding.
Levels use cyan for DEBUG, green for INFO, yellow for WARNING, red for ERROR,
and bold red for CRITICAL.
Redirected output is plain text; `NO_COLOR=1` disables terminal colors. Logs are
not saved to files. Reports (schema `1.0`) contain the score, model names and hashes,
device details, input basenames, and quality warnings. They never contain
images, embeddings, or full paths. An existing report is replaced only with
`--overwrite`, and an input image is never overwritten.

| Code | Meaning |
| --- | --- |
| 0 | Completed |
| 2 | Invalid input or command usage |
| 3 | Missing, invalid, or incompatible model |
| 4 | Device initialization or execution failure |
| 5 | Face processing or invalid model output |
| 6 | Unsafe or unwritable report destination |

</details>

<details>
<summary>💡 Tips and limits</summary>

- Lighting, pose, blur, and small faces lower scores; TrueMe warns about likely
  quality problems.
- Animated or multi-frame files use their first frame only.
- `trueme doctor --model-dir models` checks the runtime and models without photos.
- No identity search, surveillance, liveness checks, or identity verification.

</details>

## ⚙️ Configuration

| Setting | Purpose | Default |
| --- | --- | --- |
| `--model-dir` | Folder with both model files | `TRUEME_MODEL_DIR`, then a per-user folder |
| `--device` | `auto`, `cpu`, or `cuda` | `auto` |
| `--host` / `--port` | Address of the live page (`web`) | `127.0.0.1` / `8765` |

`export TRUEME_MODEL_DIR="$PWD/models"` lets you omit `--model-dir`. `auto` tries
CUDA and falls back to CPU with a reason; `cuda` fails instead of falling back.
Details: [installation guide](docs/installation.md).

<a id="documentation"></a>

## 📚 Documentation

| Guide | Use it for |
| --- | --- |
| [Installation](docs/installation.md) | Windows, CPU/GPU setup, model folders |
| [Models](docs/models.md) | Sources, licenses, checksums, preprocessing |
| [Architecture](docs/architecture.md) | Modules and the live page's boundaries |
| [Validation](docs/validation.md) | What has been tested, and on what |
| [Security](SECURITY.md) | Privacy and vulnerability reporting |

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and report problems in
[GitHub Issues](https://github.com/ZhiWei-Ou/trueme/issues). After `make setup`:

```sh
make test && make lint && make build
```

Never commit photos, weights, reports, or environments. If TrueMe made you
smile, a ⭐ helps others find it.

## 📄 License

Code is [MIT](LICENSE). Dependencies and model weights keep their own licenses;
see the [model licenses](docs/models.md#sources-and-licenses) before
redistributing weights.
