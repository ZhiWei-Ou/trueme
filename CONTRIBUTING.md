# Contributing to TrueMe

TrueMe is currently being initialized. Read [AGENTS.md](AGENTS.md) and the
[MVP specification](docs/mvp-spec.md) for scope and acceptance requirements.
The CLI, installation steps, and test commands are not available yet.

Keep changes focused and preserve unrelated work. Use English for project
documentation. Original contributions use the repository's MIT license;
dependencies and model weights retain their own licenses. Verify model weight
permissions independently of code licensing before proposing an integration.

Development targets Python 3.11 and a project-local .venv, with Windows as the
primary platform. Do not install packages globally or change execution policy.
CPU and GPU ONNX Runtime packages must use separate environments.

Include meaningful tests for changed behavior and update affected documentation.
CI must not require private photos, restricted weights, GPUs, or paid services.
Describe mocked tests separately from real model inference and state which
platforms and devices were actually verified.

Never add personal photos, reports, weights, embeddings, secrets, or environment
files. Image fixtures require clear licensing and an explicit exception to the
image ignore rules. Inspect staged contents before committing. Use concise,
single-line English commit summaries, preferably within 50 characters. Do not
push, publish, or rewrite history without authorization.
