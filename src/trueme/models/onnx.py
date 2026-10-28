"""YuNet decoding and SFace alignment/preprocessing for ONNX Runtime."""

import cv2
import numpy as np

from trueme.errors import ModelError, ProcessingError

from .device import ModelSession
from .interfaces import Face


class YuNet:
    def __init__(self, session: ModelSession):
        self.runtime = session
        shape = session.session.get_inputs()[0].shape
        if len(shape) != 4 or shape[:2] != [1, 3] or not all(isinstance(n, int) for n in shape[2:]):
            raise ModelError("YuNet requires its pinned static NCHW model.")
        self.height, self.width = shape[2:]
        self.output_names = [
            f"{kind}_{stride}" for kind in ("cls", "obj", "bbox", "kps") for stride in (8, 16, 32)
        ]

    def detect(self, bgr: np.ndarray) -> list[Face]:
        height, width = bgr.shape[:2]
        scale = min(self.width / width, self.height / height)
        resized_width = max(1, round(width * scale))
        resized_height = max(1, round(height * scale))
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        canvas[:resized_height, :resized_width] = cv2.resize(bgr, (resized_width, resized_height))
        tensor = np.ascontiguousarray(canvas.transpose(2, 0, 1)[None], dtype=np.float32)
        outputs = self.runtime.run(tensor, self.output_names)
        if len(outputs) != 12:
            raise ProcessingError("YuNet returned an unexpected number of outputs.")
        predictions = dict(zip(self.output_names, outputs, strict=True))
        faces = []
        for stride in (8, 16, 32):
            rows, cols = self.height // stride, self.width // stride
            size = rows * cols
            arrays = []
            for kind, channels in (("cls", 1), ("obj", 1), ("bbox", 4), ("kps", 10)):
                value = np.asarray(predictions[f"{kind}_{stride}"])
                if value.shape != (1, size, channels) or not np.isfinite(value).all():
                    raise ProcessingError("YuNet returned malformed or non-finite detections.")
                arrays.append(value.reshape(size, channels))
            cls, obj, boxes, points = arrays
            scores = np.sqrt(np.clip(cls[:, 0], 0, 1) * np.clip(obj[:, 0], 0, 1))
            for index in np.flatnonzero(scores >= 0.9):
                grid = np.array([index % cols, index // cols])
                center = (grid + boxes[index, :2]) * stride
                with np.errstate(over="ignore"):
                    dimensions = np.exp(boxes[index, 2:]) * stride
                bounds = np.concatenate((center - dimensions / 2, dimensions)) / scale
                landmarks = (points[index].reshape(5, 2) + grid) * stride / scale
                if not np.isfinite(bounds).all() or np.any(dimensions <= 0):
                    raise ProcessingError("YuNet returned invalid face bounds.")
                # Padding is outside the image and cannot represent an input face.
                if center[0] >= resized_width or center[1] >= resized_height:
                    continue
                faces.append(
                    Face(
                        tuple(float(v) for v in bounds),
                        landmarks.astype(np.float32),
                        float(scores[index]),
                    )
                )
        if not faces:
            return []
        keep = cv2.dnn.NMSBoxes(
            [list(face.bbox) for face in faces],
            [face.score for face in faces],
            0.9,
            0.3,
            top_k=5000,
        )
        return [faces[int(index)] for index in np.asarray(keep).reshape(-1)]


# The five landmarks in OpenCV's SFace 112 x 112 alignment contract.
SFACE_TARGET = np.array(
    [
        [38.2946, 51.6963],
        [73.5318, 51.5014],
        [56.0252, 71.7366],
        [41.5493, 92.3655],
        [70.7299, 92.2041],
    ],
    dtype=np.float64,
)


def align_face(bgr: np.ndarray, landmarks: np.ndarray) -> np.ndarray:
    source = np.asarray(landmarks, dtype=np.float64)
    if source.shape != (5, 2) or not np.isfinite(source).all():
        raise ProcessingError("Face landmarks must contain five finite points.")
    source_mean = source.mean(axis=0)
    target_mean = SFACE_TARGET.mean(axis=0)
    centered = source - source_mean
    variance = np.square(centered).sum() / 5
    if variance < 1e-12:
        raise ProcessingError("Face landmarks are degenerate; alignment is impossible.")
    covariance = (SFACE_TARGET - target_mean).T @ centered / 5
    u, singular, vt = np.linalg.svd(covariance)
    signs = np.array([1.0, -1.0 if np.linalg.det(u @ vt) < 0 else 1.0])
    rotation = (u * signs) @ vt
    scale = float(singular @ signs) / variance
    matrix = np.column_stack((scale * rotation, target_mean - scale * rotation @ source_mean))
    return cv2.warpAffine(bgr, matrix, (112, 112), flags=cv2.INTER_LINEAR)


class SFace:
    def __init__(self, session: ModelSession):
        self.runtime = session
        if session.session.get_inputs()[0].shape != [1, 3, 112, 112]:
            raise ModelError("SFace requires its pinned 112 x 112 NCHW model.")

    def embed(self, bgr: np.ndarray, face: Face) -> np.ndarray:
        aligned = align_face(bgr, face.landmarks)
        # The ONNX graph contains normalization; its public input is raw RGB [0,255].
        tensor = np.ascontiguousarray(
            aligned[:, :, ::-1].transpose(2, 0, 1)[None], dtype=np.float32
        )
        output = self.runtime.run(tensor)
        if len(output) != 1 or np.asarray(output[0]).shape != (1, 128):
            raise ProcessingError("SFace returned an unexpected embedding shape.")
        vector = np.asarray(output[0][0], dtype=np.float64)
        if not np.isfinite(vector).all() or np.linalg.norm(vector) == 0:
            raise ProcessingError("SFace returned a non-finite or zero embedding.")
        return vector
