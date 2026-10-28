# Architecture

`cli.py` composes platform paths, model adapters, image comparison, and report
export. It translates application and parser errors to stable exit codes and
structured JSON. Imports do not initialize models. `diagnostics.py` independently
reports environment facts and attempts CPU/CUDA session initialization without
performing photo inference.

`config.py` resolves explicit, environment, and platform model locations.
`platforms/` defines a narrow abstract per-user storage capability and Linux,
macOS, and Windows implementations, selected at the application boundary. Core
comparison has no OS branching. Standard filesystem and image operations remain
portable rather than being wrapped in platform services.

`models/` holds the installed manifest, integrity checks, independent detector
and recognizer contracts, ONNX adapters, and runtime provider handling. Model
resources load through package resources regardless of the working directory.
Weights are external and excluded from packages. Device choice is based on
runtime capabilities, not the operating system.

`core/images.py` validates and orients images into an in-memory BGR array.
`core/comparison.py` runs the same sequence for reference and probe: detect,
require one face, gather quality warnings, align/extract features, then compare.
`core/similarity.py` validates features and computes normalized cosine similarity.
`core/quality.py` supplies explicitly heuristic warnings.
`core/reports.py` constructs privacy-limited reports and safely publishes an
explicit export, protecting input paths and aliases. Images and features never
enter the report schema.

Boundary failures use `errors.py`: invalid input, model, device, processing, and
report errors are separately actionable. Tests use synthetic images/vectors and
controlled runtime fixtures; real model checks are separate from the fast suite.
