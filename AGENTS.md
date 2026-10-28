# TrueMe project instructions

## Scope and source of truth

TrueMe is a local CLI for comparing two face photos: reference (an enrollment
photo submitted to a face recognition system) and probe (a photo representing
a real-world camera capture). The MVP accepts --reference and --probe and
reports their similarity under the selected model. Future batch processing may
repeat this pairwise operation; it is not identity search. Read
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

- Target Python 3.11 on Linux, macOS, and Windows, with Windows as the primary
  platform. Use Makefile as the common development and build entry point;
  pyproject.toml remains the source of Python packaging metadata.
- Use a src/ package layout, pyproject.toml, Typer, Rich, ONNX Runtime,
  OpenCV, NumPy, Pillow, and pytest. Remain a pure CLI.
- Use a project-local .venv. Never modify global Python packages, global Git
  identity, or system execution policy.
- Verify dependency compatibility and pin a tested environment. Keep CPU and
  GPU installation paths separate: never install onnxruntime and
  onnxruntime-gpu together in one environment.
- Separate CLI presentation, image processing, model adapters, device selection,
  diagnostics, and reporting. Avoid databases and generic plugin frameworks.
- Put OS-dependent capabilities behind small abstract interfaces with Linux,
  macOS, and Windows infrastructure implementations. Define interfaces around
  actual callers and platform differences, and select implementations at the
  application entry boundary. Keep OS branching out of core comparison logic.
- Share portable code; do not duplicate the pipeline per platform or wrap
  every standard-library operation. Do not add speculative interfaces, unused
  layers, dependency injection containers, or automatic plugin discovery.
- Validate external inputs and model/runtime outputs at their boundaries.
  Trust established internal contracts instead of repeating checks throughout
  the call chain. Catch errors only where they can be handled or translated
  usefully; avoid broad exception swallowing, silent defaults, and speculative
  retries. Preserve required privacy, file safety, and device fallback checks.
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

## Agent collaboration

Use multiple subagents when independent, bounded tasks can reduce completion
time and keep the main agent's context focused. Delegate scoped research,
implementation, or review with only the context needed and clear ownership of
files. Avoid overlapping edits and duplicate investigation. Request concise
results with evidence, changed files, validation, and unresolved issues rather
than raw logs. The main agent owns integration, verification, and delivery.
Keep small or tightly coupled work in one agent when delegation overhead would
outweigh the benefit; do not create subagents merely to satisfy a process.

## Validation and delivery

- Start with checks for affected behavior; reuse existing coverage. Add tests
  for concrete regressions and public contracts, not implementation details.
- Keep unit tests focused and fast. Avoid exhaustive defensive cases without
  a credible failure scenario, redundant coverage, and costly test scaffolding
  with little practical value. Preserve the MVP's essential contract checks;
  run expensive real-model or hardware checks separately when relevant.
- A later human acceptance stage will assess actual workflows. Hand off clear
  verification results and remaining checks; do not claim human acceptance
  has occurred or use it as a substitute for necessary developer validation.
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
- When commits are authorized, commit incrementally at coherent, verified
  milestones instead of accumulating unrelated features into one large commit.
  Each commit should cover one logical change with its necessary caller,
  test, and documentation updates. Split by behavior or responsibility, not
  arbitrary file counts; do not split tightly coupled changes into broken
  intermediate states. The main agent coordinates commits across subagent work.
- If blocked, finish independent work and state the exact missing conditions.

Original code uses MIT. Dependencies and weights retain their own licenses;
preserve existing copyright notices.
