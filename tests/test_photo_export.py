"""Explicit photo export with synthetic images, without models or private photos."""

import io

import pytest
from PIL import Image

from trueme.core.images import decode_image
from trueme.core.photos import export_photo
from trueme.errors import InputError


@pytest.mark.parametrize(
    ("preset", "dimensions"),
    [
        ("one-inch", (295, 413)), ("two-inch", (413, 579)), ("small-two-inch", (413, 531)),
        ("small-one-inch", (260, 378)), ("large-one-inch", (390, 567)),
        ("large-two-inch", (413, 626)), ("five-inch", (1050, 1500)),
        ("six-inch", (1200, 1800)), ("seven-inch", (1500, 2100)),
        ("eight-inch", (1800, 2400)),
    ],
)
def test_photo_export_dimensions_dpi_and_original_bytes(preset, dimensions):
    source = io.BytesIO()
    Image.new("RGB", (500, 700), (220, 30, 40)).save(source, format="PNG")
    original = source.getvalue()
    result = export_photo(original, preset)
    with Image.open(io.BytesIO(result)) as photo:
        assert photo.format == "JPEG"
        assert photo.size == dimensions
        assert photo.info["dpi"] == (300, 300)
        assert photo.getpixel((0, 0)) == pytest.approx((220, 30, 40), abs=2)
    assert source.getvalue() == original


def test_export_crops_to_fit_without_stretching():
    source = io.BytesIO()
    image = Image.new("RGB", (1000, 413), "red")
    image.paste("green", (352, 0, 647, 413))
    image.save(source, format="PNG")
    with Image.open(io.BytesIO(export_photo(source.getvalue(), "one-inch"))) as photo:
        assert photo.getpixel((147, 206)) == pytest.approx((0, 128, 0), abs=2)
        assert photo.getpixel((10, 206)) == pytest.approx((0, 128, 0), abs=2)


def test_export_rejects_invalid_size_and_image():
    with pytest.raises(InputError, match="photo size"):
        export_photo(b"not an image", "unknown")
    with pytest.raises(InputError, match="Cannot read image"):
        export_photo(b"not an image", "one-inch")


@pytest.mark.parametrize(
    ("width_mm", "height_mm", "dimensions"),
    [(50.8, 25.4, (600, 300)), (300.5 / 300 * 25.4, 25.4, (301, 300))],
)
def test_custom_photo_dimensions(width_mm, height_mm, dimensions):
    source = io.BytesIO()
    Image.new("RGB", (600, 400), "blue").save(source, format="PNG")
    with Image.open(io.BytesIO(export_photo(
        source.getvalue(), "custom", width_mm=width_mm, height_mm=height_mm
    ))) as photo:
        assert photo.size == dimensions
        assert photo.info["dpi"] == (300, 300)


@pytest.mark.parametrize("dimension", [None, float("nan"), float("inf"), 9, 301])
def test_custom_dimensions_must_be_finite_and_bounded(dimension):
    with pytest.raises(InputError, match="10 to 300 mm"):
        export_photo(b"", "custom", width_mm=dimension, height_mm=25)


def test_preset_does_not_accept_custom_dimensions():
    with pytest.raises(InputError, match="only supported for custom"):
        export_photo(b"", "one-inch", width_mm=25, height_mm=35)


@pytest.mark.parametrize("format", ["jpeg", "png"])
def test_export_preserves_png_alpha_or_composites_jpeg_on_white(format):
    source = io.BytesIO()
    image = Image.new("RGBA", (295, 413), (255, 0, 0, 0))
    image.paste((255, 0, 0, 128), (148, 0, 295, 413))
    image.save(source, format="PNG")
    original = source.getvalue()
    with Image.open(io.BytesIO(export_photo(original, "one-inch", format=format))) as photo:
        assert photo.size == (295, 413)
        assert photo.info["dpi"] == pytest.approx((300, 300), abs=0.01)
        if format == "png":
            assert photo.mode == "RGBA"
            assert photo.getpixel((20, 20))[3] == 0
            assert photo.getpixel((200, 20)) == (255, 0, 0, 128)
        else:
            assert photo.mode == "RGB"
            assert photo.getpixel((20, 20)) == (255, 255, 255)
            assert photo.getpixel((200, 20)) == pytest.approx((255, 127, 127), abs=2)
    assert source.getvalue() == original
    # Comparison decoding retains its established three-channel BGR contract.
    decoded = decode_image(original)
    assert decoded.shape == (413, 295, 3)
    assert tuple(decoded[20, 200]) == (0, 0, 255)


def test_export_rejects_unsupported_format():
    with pytest.raises(InputError, match="jpeg or png"):
        export_photo(b"", "one-inch", format="gif")
