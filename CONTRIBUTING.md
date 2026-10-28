# Contributing to TrueMe

TrueMe implements the local pairwise CLI MVP. Read [AGENTS.md](AGENTS.md) and the
[MVP specification](docs/mvp-spec.md) for scope and acceptance requirements.
See README.md and docs/installation.md for installation, CLI, and live page usage.

Keep changes focused and preserve unrelated work. Use English for project
documentation. Original contributions use the repository's MIT license;
dependencies and model weights retain their own licenses. Verify model weight
permissions independently of code licensing before proposing an integration.

Development targets Python 3.11-3.13 and a project-local .venv on Linux, macOS, and
Windows, with Windows as the primary platform. Use `make setup DEVICE=cpu`,
`make test`, `make lint`, and `make build` through the project-local environment. Do not install packages globally or change execution policy.
CPU and GPU ONNX Runtime packages must use separate environments.

Put actual OS differences behind narrow abstract interfaces and platform-specific
infrastructure implementations. Share portable code and introduce abstractions
only with concrete callers. Keep validation at external boundaries, preserve
required safety checks, and avoid repeated internal checks, silent fallback,
speculative retries, and unnecessary frameworks.

Include meaningful tests for changed behavior and update affected documentation.
Favor fast tests of essential contracts and concrete regressions. Avoid
redundant, excessively defensive, or disproportionately costly unit tests.
Keep expensive model and hardware validation separate. Development is followed
by human acceptance testing; report completed checks and what remains for
acceptance without treating it as a replacement for necessary developer checks.
CI must not require private photos, restricted weights, GPUs, or paid services.
Describe mocked tests separately from real model inference and state which
platforms and devices were actually verified.

For agent-assisted development, use subagents for independent tasks when this
reduces elapsed time and keeps the main agent's context focused. Define scope
and file ownership, return concise findings, and keep integration responsibility
with the main agent. Small or tightly coupled tasks do not require delegation.

Never add personal photos, reports, weights, embeddings, secrets, or environment
files. Image fixtures require clear licensing and an explicit exception to the
image ignore rules. Inspect staged contents before committing. Use concise,
single-line English commit summaries, preferably within 50 characters. Do not
push, publish, or rewrite history without authorization.

When committing is authorized, create incremental commits as coherent stages
are completed and verified. Keep each commit focused on one logical change,
including its required caller, test, and documentation updates. Do not combine
unrelated features or responsibilities into a large end-of-task commit, or
split coupled changes into broken intermediate states. Coordinate subagent
contributions before staging so each commit contains only its intended scope.
