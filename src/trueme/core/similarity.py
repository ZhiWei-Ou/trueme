"""Cosine similarity of validated model feature vectors."""

import numpy as np

from trueme.errors import ProcessingError


def cosine_similarity(reference: np.ndarray, probe: np.ndarray) -> float:
    vectors = []
    for vector in (reference, probe):
        vector = np.asarray(vector, dtype=np.float64)
        if vector.ndim != 1 or vector.size == 0 or not np.isfinite(vector).all():
            raise ProcessingError(
                "Model features must be finite, nonempty one-dimensional vectors."
            )
        # Scaling before normalization avoids overflow for finite model outputs.
        scale = np.max(np.abs(vector))
        if scale == 0:
            raise ProcessingError("Model returned a zero feature vector.")
        scaled = vector / scale
        vectors.append(scaled / np.linalg.norm(scaled))
    if vectors[0].shape != vectors[1].shape:
        raise ProcessingError("Reference and probe feature dimensions do not match.")
    return float(np.clip(np.dot(*vectors), -1.0, 1.0))
