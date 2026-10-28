"""Decode user images without changing the originals."""

import warnings
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from trueme.errors import InputError


def load_image(path: Path) -> np.ndarray:
    """Return an EXIF-oriented BGR image; reject unsupported or multi-frame input."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path) as image:
                if getattr(image, "n_frames", 1) != 1:
                    raise InputError("Animated and multi-frame images are not supported.")
                if image.format not in {"JPEG", "PNG", "WEBP"}:
                    raise InputError("Use a JPEG, PNG, or WebP image.")
                oriented = ImageOps.exif_transpose(image).convert("RGB")
                return np.array(oriented, dtype=np.uint8)[:, :, ::-1].copy()
    except (OSError, UnidentifiedImageError, ValueError) as exc:
        raise InputError(
            "Cannot read image; check that it is a valid, accessible JPEG, PNG, or WebP."
        ) from exc
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise InputError("Image exceeds Pillow's safe pixel limit; use a smaller image.") from exc
