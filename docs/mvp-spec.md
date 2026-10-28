# TrueMe CLI MVP specification

## Status and purpose

This document records the initial implementation target. The repository is in
the project-initialization stage: there is no installable CLI, selected model,
dependency lock, or verified inference yet. Implementation and model research
are subsequent work.

TrueMe compares two face photos locally with the user's consent:

- reference: a reference or enrollment photo, like one submitted to a face
  recognition system.
- probe: a photo representing a real-world camera capture to compare with
  the reference. The MVP accepts an image file; live camera capture is not
  required.

The purpose is to assess facial similarity between enrollment and camera
conditions. The output describes similarity under the selected model, not
general image resemblance or retouching intensity. There is no three-photo
before-and-after workflow. Future batch processing may repeat explicitly
specified reference/probe pairs; it is outside the initial MVP.

The user's practical question is whether a pair would be accepted in common
face recognition scenarios. A single model score cannot establish acceptance
across most real-world systems. Do not present that outcome as a product
capability without relevant system-specific validation. The MVP reports
similarity and quality warnings, not a universal pass/fail decision.

Identity search, surveillance, identity databases, and bypassing identity
verification or liveness detection are outside scope. No GUI, web interface,
server, cloud API, API key, paid service, or automatic history is required.

## Runtime and layout

Use Python 3.11, Typer, Rich, ONNX Runtime, OpenCV, NumPy, Pillow, and pytest.
Windows is the primary platform. Use pyproject.toml, src/trueme/, a local .venv,
and an installable trueme entry point plus python -m trueme.

Keep cli.py and config.py separate from core image loading, face processing,
similarity, quality, and report modules. Put model interfaces, registry,
device selection, and ONNX adapters in models/. Keep diagnostics separate.
Do not require Docker, databases, or a plugin framework. A standalone Windows
executable is optional and outside the initial MVP.

## CLI contract

Planned commands (not executable in the current repository):

```powershell
trueme compare --reference "reference.jpg" --probe "probe.jpg" --device auto
trueme compare --reference "reference.jpg" --probe "probe.jpg" --output "report.json"
trueme doctor
trueme models list
trueme --help
trueme --version
python -m trueme --help
```

Support --model-dir, --json, and --verbose where applicable. Model lookup order:
explicit --model-dir, TRUEME_MODEL_DIR, then a documented per-user application
data directory. Do not resolve installed resources relative to the current
working directory. Choose and document the exact per-platform default during
implementation.

JSON mode emits one valid JSON object to stdout without terminal decorations.
Progress and diagnostics go to stderr; errors are structured and exit nonzero.
Define stable distinct exit codes for invalid input, model errors, device
errors, and processing failures, and document their numeric values before
release. Missing or invalid models must not break help, version, or diagnostics;
comparison must fail with actionable guidance.

## Images and comparison

Accept JPEG, PNG, and WebP with Unicode paths, Chinese characters, and spaces.
Use Pillow for loading and EXIF orientation correction. Reject unreadable or
unsupported inputs with actionable errors. Explicitly reject or otherwise
document multi-frame and animated image handling; never choose an arbitrary
frame silently. Require exactly one detected face per image, rejecting zero
and multiple faces without selecting the largest.

Pipeline: load and orient; detect faces and landmarks; align according to the
recognition model; apply model-specific resizing, channel order, and
normalization; extract features; L2-normalize; compute cosine similarity.
Reject zero-norm, non-finite, or dimensionally incompatible vectors. Report
raw cosine similarity with reasonable precision, without universal thresholds
or definitive identity judgments. Never fabricate scores when weights are absent.

For reference R and probe P, report similarity(R, P). Both inputs are required.
Use reference and probe consistently in CLI options, internal interfaces,
reports, tests, and documentation. Lighting, pose, quality, and alignment can
affect scores. The score is not a confidence percentage, a probability of
shared identity, or a probability of passing another system's checks.

Warn where feasible about small face regions, possible blur, and severe
underexposure or overexposure. Label these as heuristics, not calibrated quality
judgments. Human-readable results must include:

> This score compares photos under the selected model. It does not predict acceptance by third-party identity verification systems.

## Models and compute

Use independent detector and recognition adapter interfaces. Before adopting
models, verify trustworthy sources, weight licenses, code licenses,
redistribution and commercial-use restrictions, input preprocessing,
alignment, output semantics, and CPU/CUDA compatibility. Prefer openly licensed
weights. Clearly disclose restrictions and keep weights separate from source.

Maintain a packaged manifest with model name, version or source identifier,
source URL, license URL and restrictions, expected filenames, and trusted
SHA-256 values when available. A locally computed hash identifies a file but
does not prove provenance. Do not invent checksums or download URLs. Downloads,
if implemented, require explicit invocation and verify trusted checksums when
available. Document exact acquisition and configuration steps if weights are
unavailable.

--device auto is the default: attempt CUDA and fall back to CPU with a clear
reason. --device cuda requires usable CUDA and fails clearly on initialization
or execution failure; never silently use a CPU-only session. --device cpu
forces CPU. Use ONNX Runtime execution providers, check actual initialization,
and handle execution failures as well as unavailable providers. Do not assume
an NVIDIA GPU or installed toolkit proves usability. Report configured
providers and known fallback, without claiming all operations ran on GPU.
Keep preprocessing and inference semantics consistent across devices.

Verify a compatible ONNX Runtime GPU / CUDA / cuDNN combination against current
official documentation when selecting dependencies. Pin a tested environment
and provide separate CPU/GPU installation instructions; never install both
onnxruntime and onnxruntime-gpu in one environment. Do not change system policy
or global Python packages.

## Diagnostics and reports

doctor reports Python/application/OS/ONNX Runtime versions, available providers,
resolved model directory and required file status, and whether configured
models can initialize on CPU and CUDA. Provide actionable guidance for missing
dependencies and incompatible GPU libraries. Clearly distinguish provider
enumeration, session initialization, and actual inference. Keep basic checks
lightweight; make expensive inference checks explicit or optional.

--output explicitly writes a JSON report. Require --overwrite before replacing
an existing report and always prohibit overwriting an input image, including
aliases to the same file. Reports contain:

- Schema version, timezone-aware timestamp, application version.
- Model names, versions, and file hashes when available.
- Requested device, configured providers, and known fallback details.
- Input basenames labeled reference and probe, without full paths by default.
- Reference/probe cosine similarity, quality warnings, and interpretation.

Exclude images, encoded contents, embeddings, and full input paths by default.
JSON must contain no NaN or infinity. Never modify inputs. Process images and
embeddings in memory, do not persist intermediate crops by default, never log
embeddings, and avoid logging full image paths. No telemetry, uploads, accounts,
analytics, or automatic comparison history. Do not promise secure memory erasure.

## Acceptance and documentation

Automated coverage must include identical and orthogonal nonzero vectors;
zero, mismatched and non-finite vectors; EXIF orientation; invalid image errors;
required reference/probe arguments; reports without embeddings or image data; parseable JSON
stdout; missing models; automatic CPU fallback; explicit CUDA failure; and
report destinations that would overwrite inputs.

Real integration checks must cover two-photo comparison with valid models,
no-face and multiple-face rejection, Unicode paths, CPU inference, CUDA when
compatible hardware is available, and unchanged original files. Use only
user-provided or clearly licensed assets. Do not collect strangers' photos.
Report unit tests, real CPU inference, real CUDA inference, and checks blocked
by models or photos separately. Mocks do not establish real inference validity.

Add lightweight CI for unit tests and basic quality checks without personal
photos, restricted weights, CUDA hardware, or paid services. Provide development,
test, and package-build instructions once commands exist. Verify packages exclude
weights and private assets.

The English README must cover purpose and limitations, requirements, CPU/GPU
setup, model acquisition and licenses, PowerShell examples, reference/probe
comparison, device fallback, score interpretation, JSON schema, exit codes,
privacy, development/testing, common errors, and known limitations. Add
architecture and model-integration documentation with the actual implementation.
Keep LICENSE, CONTRIBUTING.md, SECURITY.md, and .gitignore consistent with scope.
Original code is MIT; weights and dependencies retain separate licenses.

## Implementation sequence

1. Inspect repository, instructions, and environment.
2. Research model sources, licenses, and runtime compatibility.
3. Add packaging, local environment setup, and tested dependency pins.
4. Implement adapters and device handling, then image comparison.
5. Implement CLI, diagnostics, and JSON report export.
6. Add and run meaningful automated and available integration checks.
7. Complete README, architecture/model documentation, and CI.
8. When authorized, commit coherent checked changes with short English subjects.
9. Report actual results and remaining limitations without overstating validation.

Keep all work local unless publication is separately requested. Never change
global Git identity or rewrite history; if identity is missing, report how the
user can configure it instead of inventing one.
