# Developer validation and human acceptance handoff

The MVP is ready for subsequent human acceptance, subject to the limitations
below. This is developer validation, not completed human acceptance.

## Automated and packaging checks

On Linux x86-64 (WSL2), Python 3.11.16, CPU ONNX Runtime 1.20.1:

- `make test`: 35 focused tests passed, without personal photos or model weights.
- `make lint`: passed.
- `make build`: wheel and source distribution built; archives include the model
  manifest and exclude weights, photos, reports, and virtual environments.
- The built wheel was installed into an isolated target and its packaged model
  manifest loaded successfully outside the repository.
- Dependency `pip check` passed. CPU/GPU setup separation rejected adding the
  GPU distribution to an existing CPU environment.

Tests cover vector contracts, EXIF orientation, image errors, exactly-one-face
handling, heuristic warnings, report privacy and input alias protection, CLI
JSON/argument errors, missing models, CUDA initialization/execution fallback,
explicit CUDA failure, and platform directory precedence. Runtime fixtures in
unit tests do not establish real GPU behavior.

## Actual local inference

Both official model files matched the pinned upstream Git LFS SHA-256 values.
Independent real CPU comparisons completed for `a1.jpg` against `p2.jpg`, `p3.jpg`,
and `p4.jpg`. Scores were delivered in the handoff rather than committed as
personal reports. Auto mode also completed a real comparison using CPU and
recorded that CUDA was unavailable in the CPU environment. Real blank and
two-face tiled probes were rejected; Unicode/space-path copies produced the same
score. SFace embeddings agreed with the OpenCV reference pipeline at cosine
0.99999894 or better (small alignment rounding differences). Explicit report
export, existing-file refusal, overwrite, and input-file protection also passed
with real CPU inference. Original SHA-256 hashes were unchanged.

`p1.jpg` is a two-frame MPO container despite its `.jpg` filename. It is rejected
by the multi-frame input contract. To complete that pair, the user must supply
an intentionally selected, single-frame JPEG/PNG/WebP export; the original was
not altered and no frame was silently selected.

## Live web page

Photo export checks use synthetic images to verify JPEG/PNG dimensions, 300 DPI
metadata, crop behavior, unchanged input bytes, invalid input handling, and
HTTP attachment headers, plus preserved PNG alpha and JPEG white compositing. Run them with
`python -m pytest tests/test_photo_export.py tests/test_web.py` in the local
virtual environment. `node --test tests/web_photo_export.test.cjs` checks crop
geometry and the explicit reference-preview/download flow with controlled DOM
fixtures. Browser acceptance should check each size, portrait/landscape sources,
EXIF-oriented photos, keyboard controls, downloads, and backend disconnects;
these fixtures do not establish actual browser rendering or print quality.

The opening overlay's lifecycle regression tests run separately with Node.js:
`node --test tests/web_intro.test.cjs`. They execute the page script with
controlled DOM and animation fixtures, covering completion, repeated focus
changes, switching away during playback, keyboard focus, and reduced motion.
These checks do not replace a browser test: on Windows, verify that Alt+Tab
away and back during and after the opening never replays it, while reloading
the page still allows one opening when reduced motion is disabled.

On macOS (Apple Silicon), Python 3.11.18, CPU ONNX Runtime 1.20.1, with the
pinned models and one user-provided photo: `trueme web` served the page; the
API returned a face box and score for frames and no score for a blank frame;
a blank reference, non-image body, foreign `Origin`, and foreign Host header
were rejected; IPv6 loopback, port-in-use errors, and Ctrl+C shutdown behaved
as documented. Headless Chrome with a fake camera fed from that photo uploaded
the reference, streamed frames, drew the face box, and showed the score and
scale. 640-pixel frames took about 43 ms per request (median of 20) on that
machine. A physical webcam, other browsers, Windows, Linux, and CUDA were not
exercised for the web page.

## Device and platform limits

GPU access is blocked inside the execution sandbox, while an elevated query
identifies an NVIDIA GeForce RTX 5060. The CPU environment exposes only Azure
and CPU providers. In a separate Python 3.11 GPU environment, ONNX Runtime GPU
1.20.2 with CUDA 12.8 runtime libraries and cuDNN 9.8 completed explicit CUDA
comparisons for all three valid pairs. Both model sessions retained
CUDAExecutionProvider and CPUExecutionProvider, with no fallback. This establishes
real execution with CUDA configured, not that every operation used the GPU.
The maximum absolute CPU/CUDA score difference across these pairs was about
0.000802; this observation is not a general accuracy tolerance. The optional
GPU runtime pins and loader setup are in docs/installation.md. GPU dependency
`pip check` passed; the original five photo hashes remained unchanged.

Only Linux was executed locally. Windows/macOS implementations and CI jobs exist,
but neither native platform nor hosted CI has been run in this work. Their
presence is not a claim of platform acceptance.

## Human acceptance checklist

1. Follow the documented PowerShell installation and model acquisition flow on
   Windows; repeat platform smoke checks on macOS.
2. Compare consented reference/probe photos, reviewing warnings and interpretation.
3. Supply a chosen single-frame export for the rejected MPO probe and compare it.
4. Exercise JSON output and explicit export, existing-report overwrite, and input
   alias protection through actual workflows.
5. Run `trueme web`, choose a reference photo, and start a physical webcam;
   check the face box, score updates, multiple-face handling, and that stopping
   the server discards the reference.
6. On compatible NVIDIA hardware, run doctor followed by actual explicit CUDA
   comparisons; compare CPU/CUDA results with numerical tolerance, not exact
   floating-point equality. Initialization alone does not satisfy this check.

Human assessment must not interpret similarity as an identity verdict or
third-party verification acceptance probability.
