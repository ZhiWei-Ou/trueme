# Architecture

`cli.py` composes platform paths, model adapters, image comparison, and report
export. It translates application and parser errors to stable exit codes and
structured JSON. Imports do not initialize models. `diagnostics.py` independently
reports environment facts and attempts CPU/CUDA session initialization without
performing photo inference.

Operational messages use Python's standard-library `logging` package, configured
at the CLI entry point through `logging_config.py`. Each message on stderr has
a UTC ISO 8601 timestamp (`YYYY-MM-DDTHH:MM:SSZ`) and level, separated from the
message by single spaces without column padding. Rich colors only the level
in terminals; redirected output and `NO_COLOR=1` suppress colors. Development
commands share this configuration and use plain standard-library formatting
when Rich is not installed yet. `compare --verbose`
enables DEBUG device diagnostics. Results and structured JSON remain on stdout;
JSON errors are emitted once as structured results. Logs are not written to files,
and per-frame HTTP access logging remains disabled.

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

`web/server.py` backs the optional `trueme web` command with the standard
library HTTP server and packaged static files (`web/static/`). The page uses a
quiet editorial layout with system serif headings, warm neutral colors, and
responsive camera/reference sections. A compact header and viewport-limited
camera height keep the primary controls near the top; shorter desktop windows
also use a smaller reference preview. A local SVG ink opening reveals the page in 1.1 seconds, using
expanding organic shapes without moving the layout or intercepting input.
Reduced-motion preferences disable the opening. Its overlay is removed after
completion, keyboard focus, or leaving the window, so switching applications
cannot replay it within the same page load. Score interpretation is available in a
collapsed disclosure; scores and quality warnings remain visible. Fonts and
styles are local, with no external asset requests. The server holds one
reference feature in memory and compares each posted camera frame with the same
detector, `embed_single_face`, and cosine similarity used by the CLI; a frame
without exactly one face returns its face count and no score. Inference is
serialized by a lock. The frontend clears the previous face box if a frame
request fails, including when the backend disconnects. Requests must use an expected Host header (DNS-rebinding
protection, relaxed only for wildcard binds) and same-origin `Origin`, upload
bodies must declare an image type and stay within 15 MB, and responses carry a
restrictive Content-Security-Policy and `no-store`. Frames and the reference are
never written to disk or logged; they are discarded when the server stops.

`web/static/photo-export.js` provides explicit export of the currently displayed
reference photo. A modal previews a fixed-aspect crop with zoom and position
controls, preserving the original background. The modal and preview area use
viewport-bounded dimensions independent of the selected output size, with the
canvas fitted inside the preview without distortion. The browser draws the source
image into a separate canvas, without camera overlays, and sends a PNG crop to
`POST /api/photo-export?size=...&format=jpeg|png` only when Download is clicked.
`core/photos.py` decodes the crop and encodes JPEG or PNG with the selected pixel
dimensions and 300 DPI metadata, returned as an attachment. The server retains
neither export inputs nor output files; the browser handles the requested save.
The export route uses the same upload limits and Host/Origin checks as frame
uploads and does not alter the reference feature or perform inference. Closing
the editor releases its source image and canvas and cancels a pending request.
The original reference preview remains available for another export. Download
names use the original filename stem plus a size suffix. The source filename
stays in the browser and is not sent to the export endpoint. Ten presets
explicitly identify their millimeter and pixel dimensions, covering
portrait and print sizes. Custom exports add `width_mm` and `height_mm` query
parameters, each finite and between 10 and 300 mm, converted to pixels at 300 DPI.
Both frontend and backend validate custom dimensions. The fixed modal and
preview bounds are independent of preset selection and custom controls.
No preset claims official document-photo compliance.
PNG preserves the source alpha channel through cropping and export; JPEG
composites it onto white. The preview uses a CSS checkerboard behind transparent
pixels, which is never included in the exported image. This feature preserves
existing transparency and does not perform background segmentation. Comparison
continues to use the existing RGB/BGR image contract.

Boundary failures use `errors.py`: invalid input, model, device, processing, and
report errors are separately actionable. Tests use synthetic images/vectors and
controlled runtime fixtures; real model checks are separate from the fast suite.
