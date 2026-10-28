# TrueMe project instructions

## Scope and source of truth

TrueMe is a local CLI for comparing a reference face photo with an edited photo,
optionally including the original photo before retouching. Read
[the MVP specification](docs/mvp-spec.md) before implementation. That document
defines the target, not a claim that features already exist.

Work only within the current user request. The specification is not standing
authorization to implement every feature, publish a repository, upload data,
or commit future changes. Inspect Git status first and preserve unrelated work.
Read applicable nested instructions before editing. If CONTEXT.md exists at the
repository root, read it; do not create or maintain it without authorization.

## Product boundaries

- Compare only the user's own photos or photos used with explicit consent.
- Keep processing local. No identity search, surveillance, identity database,
  cloud APIs, telemetry, accounts, or background services.
- Do not add identity-verification or liveness-bypass features.
- Scores describe similarity under a selected model. Never label them as
  probabilities, identity judgments, or verification acceptance percentages.
- Never invent thresholds, scores, model URLs, checksums, or validation results.
- Never modify input images. Keep images, crops, and embeddings in memory;
  never log embeddings or persist intermediate crops by default.
- Write reports only on explicit request. Exclude full input paths by default.
  Do not claim secure memory erasure.

## Implementation conventions

- Target Python 3.11 and Windows first; keep core logic portable.
- Use a src/ package layout, pyproject.toml, Typer, Rich, ONNX Runtime,
  OpenCV, NumPy, Pillow, and pytest. Remain a pure CLI.
- Use a project-local .venv. Never modify global Python packages, global Git
  identity, or system execution policy.
- Verify dependency compatibility and pin a tested environment. Keep CPU and
  GPU installation paths separate: never install onnxruntime and
  onnxruntime-gpu together in one environment.
- Separate CLI presentation, image processing, model adapters, device selection,
  diagnostics, and reporting. Avoid databases and generic plugin frameworks.
- Load installed resources independently of the working directory. Resolve
  model locations by explicit option, environment variable, then user data dir.
- Keep help, version, and basic diagnostics usable without weights. Avoid eager
  model initialization at import time.
- Treat exactly one face per image as a contract; do not select the largest
  face silently. Handle EXIF orientation and multi-frame images explicitly.
- Validate finite, nonzero, dimensionally compatible feature vectors.
- In JSON mode emit exactly one JSON object to stdout, including errors;
  diagnostics go to stderr. Reject NaN and infinity.

## Models and devices

Before selecting weights, verify source, weight and code licenses separately,
commercial-use and redistribution restrictions, preprocessing, alignment,
output semantics, and ONNX Runtime compatibility. Record evidence in the model
manifest and model-selection documentation. Do not infer weight licensing from
the code license. Keep weights out of Git and package distributions.

CUDA provider enumeration alone is insufficient. Check session initialization
and handle execution failures. Auto mode may fall back to CPU with a reason;
explicit CUDA must fail rather than silently run a CPU-only session. Report
configured providers and known fallback without claiming every operation used
the GPU. Keep preprocessing identical across devices.

## Validation and delivery

- Start with checks for affected behavior; reuse existing coverage. Add tests
  for concrete regressions and public contracts, not implementation details.
- Unit tests and CI must run without personal photos, restricted weights,
  CUDA hardware, or paid services. Use mocks only as controlled unit fixtures.
- Report unit tests, real CPU inference, real CUDA inference, and blocked
  checks separately. Mocked tests are not real model validation.
- Use only user-provided or clearly licensed assets for integration checks;
  do not collect strangers' face photos. Verify inputs remain unchanged.
- Keep project documentation in English. Update affected usage and architecture
  documentation with implementation changes; do not claim planned commands work.
- Never commit photos, reports, weights, secrets, environments, or build output.
  Inspect the actual staged diff before an authorized commit. Use short,
  single-line English summaries, preferably within 50 characters.
- Commit only when the current request authorizes it. Never push, publish,
  rewrite history, or change global identity without explicit authorization.
- If blocked, finish independent work and state the exact missing conditions.

Original code uses MIT. Dependencies and weights retain their own licenses;
preserve existing copyright notices.
