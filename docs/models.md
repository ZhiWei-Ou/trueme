# Model integration

TrueMe uses the unquantized OpenCV Zoo YuNet `2023mar` detector and SFace
`2021dec` recognizer. Weights are separate downloads and are never included in
Git or Python distributions. Comparison does not contact the network.

## Sources and licenses

The packaged [manifest](../src/trueme/models/manifest.json) pins OpenCV Zoo commit
`48b10fa505aeb51fbd127fc60a5c660040e823b7`, filenames, source/download URLs,
license evidence, and SHA-256 values. These digests come from the publisher's
Git LFS pointers, not just a local download hash. Every comparison validates
both files before creating sessions. These checks establish agreement with the
pinned publisher artifacts, not a guarantee about model training data.

| Component | Weight license | Code license and evidence |
| --- | --- | --- |
| YuNet 2023mar | MIT | Its directory, including model and wrapper, is explicitly covered by [the directory's license declaration](https://github.com/opencv/opencv_zoo/blob/48b10fa505aeb51fbd127fc60a5c660040e823b7/models/face_detection_yunet/README.md#license) and [MIT terms](https://github.com/opencv/opencv_zoo/blob/48b10fa505aeb51fbd127fc60a5c660040e823b7/models/face_detection_yunet/LICENSE). |
| SFace 2021dec | Apache-2.0 | Its directory explicitly covers all files under [Apache-2.0](https://github.com/opencv/opencv_zoo/blob/48b10fa505aeb51fbd127fc60a5c660040e823b7/models/face_recognition_sface/README.md#license); see [the full terms](https://github.com/opencv/opencv_zoo/blob/48b10fa505aeb51fbd127fc60a5c660040e823b7/models/face_recognition_sface/LICENSE). |

Both licenses permit commercial use and redistribution subject to their terms.
MIT requires retaining its notice; Apache-2.0 requires its license, applicable
notices, and change notices for modified files. The upstream declarations apply
to the weight directories specifically; TrueMe does not infer weight licensing
from its own MIT license or OpenCV Zoo's root license. This is not a clearance
of rights in training subjects, input photographs, or a deployment's use case.

The OpenCV library and its reference inference implementations use Apache-2.0.
TrueMe implements the documented tensor and alignment contracts independently;
OpenCV remains a separately licensed dependency.

## Acquire the pinned weights

Run these explicit downloads in PowerShell from the project directory. They
fetch model weights only and never send photographs. `models` may be replaced
by another directory and passed with `--model-dir`.

```powershell
New-Item -ItemType Directory -Force models | Out-Null
$revision = "48b10fa505aeb51fbd127fc60a5c660040e823b7"
$base = "https://media.githubusercontent.com/media/opencv/opencv_zoo/$revision/models"
Invoke-WebRequest "$base/face_detection_yunet/face_detection_yunet_2023mar.onnx" -OutFile "models/face_detection_yunet_2023mar.onnx"
Invoke-WebRequest "$base/face_recognition_sface/face_recognition_sface_2021dec.onnx" -OutFile "models/face_recognition_sface_2021dec.onnx"
Get-FileHash models/*.onnx -Algorithm SHA256
.venv\Scripts\python -m trueme doctor --model-dir models --json
```

On Linux/macOS, download those same URLs with a browser or `curl -fL URL -o FILE`
after creating the destination directory. A GitHub `raw` link to an LFS file
returns a small pointer, not a usable weight; the media URLs above serve the
actual bytes. Expected files:

| File | Bytes | Publisher SHA-256 |
| --- | ---: | --- |
| `face_detection_yunet_2023mar.onnx` | 232589 | `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4` |
| `face_recognition_sface_2021dec.onnx` | 38696353 | `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79` |

Publisher pointers: [YuNet](https://raw.githubusercontent.com/opencv/opencv_zoo/48b10fa505aeb51fbd127fc60a5c660040e823b7/models/face_detection_yunet/face_detection_yunet_2023mar.onnx),
[SFace](https://raw.githubusercontent.com/opencv/opencv_zoo/48b10fa505aeb51fbd127fc60a5c660040e823b7/models/face_recognition_sface/face_recognition_sface_2021dec.onnx).

## Tensor and geometry contracts

Image loading applies EXIF orientation and produces BGR uint8 in memory. YuNet's
pinned graph has float32 NCHW input `1 x 3 x 640 x 640`. TrueMe fits the image
within that square while preserving aspect ratio, pads the bottom/right with
zeros, and uses raw BGR values without mean subtraction. The three strides
(8, 16, 32) produce classification, objectness, box, and five-landmark outputs.
The detector combines classification/objectness with a square root, decodes
centers and exponential box dimensions, then applies non-maximum suppression.
Detector score threshold 0.9, NMS IoU threshold 0.3, and top-k 5000 are detection
settings; they are **not** identity or similarity thresholds. Geometry is mapped
back to the oriented input. TrueMe requires exactly one surviving face.
The decode contract follows the [OpenCV detector implementation](https://github.com/opencv/opencv/blob/4.12.0/modules/objdetect/src/face_detect.cpp).

SFace takes a five-landmark similarity transform into a 112 x 112 crop, using
OpenCV's canonical eye/nose/mouth positions. It receives float32 NCHW raw RGB
values; input normalization is already part of the graph. Its output is a
128-element feature vector. TrueMe validates it and computes L2-normalized
cosine similarity. See the [OpenCV recognition implementation](https://github.com/opencv/opencv/blob/4.12.0/modules/objdetect/src/face_recognize.cpp).
CPU and CUDA use the same preprocessing. All image crops and embeddings remain
in memory and are absent from reports.

The fixed detector canvas can lose very small faces in large images. The
upstream model describes a limited trained face-size range. Detection failure
is an error, not evidence of dissimilarity. Neither these model choices nor any
single cosine value predicts a third-party verification decision.

## Runtime and device behavior

CPU setup pins `onnxruntime==1.20.1`; GPU setup pins `onnxruntime-gpu==1.20.2`.
Never install both distributions into one environment. Official [CUDA provider requirements](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html#requirements)
list the PyPI 1.20.x GPU build with CUDA 12.x and cuDNN 9.x. cuDNN 8 and 9 are
not interchangeable. Windows also needs the Visual C++ runtime and CUDA/cuDNN
DLL directories available to the process. Linux needs corresponding shared
libraries on its loader path. macOS uses the CPU installation.

`auto` attempts CUDA when its provider is listed, checks that it survived
session initialization, and otherwise initializes CPU with a reported reason.
If CUDA execution fails, `auto` recreates that model session on CPU and repeats
that inference once. `cuda` fails on provider absence, initialization failure,
or execution failure. ONNX Runtime's implicit Python execution fallback is
disabled. `cpu` requests only the CPU provider. Model sessions may have different
configured providers after an execution fallback; reports preserve each session's
state. A configured CUDA provider does not prove that every graph operation ran
on GPU; CPU kernels remain available for unsupported operations.

`doctor` separates provider enumeration from initialization and does not run
inference. A real `compare` call is necessary to exercise execution. These are
standard ONNX graphs; the actual checks performed in the current environment
are recorded in the acceptance handoff, separately from mocked device tests.
