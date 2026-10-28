"""Decode user images without changing the originals."""

import io
import warnings
from pathlib import Path
from typing import BinaryIO

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from trueme.errors import InputError


def load_image(path: Path) -> np.ndarray:
    """Return the first frame as an EXIF-oriented BGR image."""
    return _decode(path)


def decode_image(data: bytes) -> np.ndarray:
    """Decode in-memory image bytes, such as a camera frame, like a file."""
    return _decode(io.BytesIO(data))


def _decode(source: Path | BinaryIO) -> np.ndarray:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(source) as image:
                if image.format not in {"JPEG", "MPO", "PNG", "WEBP"}:
                    raise InputError("Use a JPEG, PNG, or WebP image.")
                image.seek(0)
                oriented = ImageOps.exif_transpose(image).convert("RGB")
                return np.array(oriented, dtype=np.uint8)[:, :, ::-1].copy()
    except (OSError, UnidentifiedImageError, ValueError) as exc:
        raise InputError(
            "Cannot read image; check that it is a valid, accessible JPEG, PNG, or WebP."
        ) from exc
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise InputError("Image exceeds Pillow's safe pixel limit; use a smaller image.") from exc
