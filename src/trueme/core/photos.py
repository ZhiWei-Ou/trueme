"""Encode explicitly requested photo crops without retaining image data."""

import io
import math

from PIL import Image, ImageOps

from trueme.core.images import decode_rgba_image
from trueme.errors import InputError

PHOTO_SIZES = {
    "one-inch": (295, 413),
    "two-inch": (413, 579),
    "small-two-inch": (413, 531),
    "small-one-inch": (260, 378),
    "large-one-inch": (390, 567),
    "large-two-inch": (413, 626),
    "five-inch": (1050, 1500),
    "six-inch": (1200, 1800),
    "seven-inch": (1500, 2100),
    "eight-inch": (1800, 2400),
}


def export_photo(
    data: bytes, size: str, *, width_mm: float | None = None, height_mm: float | None = None,
    format: str = "jpeg",
) -> bytes:
    """Return a 300-DPI photo; PNG keeps alpha and JPEG composites onto white."""
    if format not in {"jpeg", "png"}:
        raise InputError("Choose jpeg or png photo format.")
    if size == "custom":
        if any(
            value is None or not math.isfinite(value) or not 10 <= value <= 300
            for value in (width_mm, height_mm)
        ):
            raise InputError("Custom width and height must each be 10 to 300 mm.")
        dimensions = (
            math.floor(width_mm / 25.4 * 300 + 0.5),
            math.floor(height_mm / 25.4 * 300 + 0.5),
        )
    else:
        if size not in PHOTO_SIZES:
            raise InputError("Choose a supported photo size or custom dimensions.")
        if width_mm is not None or height_mm is not None:
            raise InputError("Width and height are only supported for custom photo size.")
        dimensions = PHOTO_SIZES[size]
    image = Image.fromarray(decode_rgba_image(data))
    image = ImageOps.fit(image, dimensions, method=Image.Resampling.LANCZOS)
    output = io.BytesIO()
    if format == "jpeg":
        background = Image.new("RGB", image.size, "white")
        background.paste(image, mask=image.getchannel("A"))
        background.save(output, format="JPEG", quality=95, dpi=(300, 300))
    else:
        image.save(output, format="PNG", dpi=(300, 300))
    return output.getvalue()
