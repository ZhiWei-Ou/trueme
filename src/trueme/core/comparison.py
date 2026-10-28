"""Pairwise processing; intermediate images and features stay in memory."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from trueme.core.images import load_image
from trueme.core.quality import quality_warnings
from trueme.core.similarity import cosine_similarity
from trueme.errors import InputError

if TYPE_CHECKING:
    from trueme.models.interfaces import Detector, Face, Recognizer


def embed_single_face(
    image: np.ndarray, role: str, detector: Detector, recognizer: Recognizer
) -> tuple[np.ndarray, list[str], Face]:
    """Return the feature, quality hints, and face of an image with exactly one face."""
    faces = detector.detect(image)
    if len(faces) != 1:
        raise InputError(f"The {role} image must contain exactly one face; detected {len(faces)}.")
    face = faces[0]
    return recognizer.embed(image, face), quality_warnings(image, face.bbox), face


def compare_images(
    reference: Path, probe: Path, detector: Detector, recognizer: Recognizer
) -> dict:
    features = []
    warnings = {}
    for role, path in (("reference", reference), ("probe", probe)):
        feature, warnings[role], _ = embed_single_face(
            load_image(path), role, detector, recognizer
        )
        features.append(feature)
    return {
        "cosine_similarity": cosine_similarity(*features),
        "quality_warnings": warnings,
    }
