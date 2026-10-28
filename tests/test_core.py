import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image

from trueme.core.comparison import compare_images
from trueme.core.images import load_image
from trueme.core.quality import quality_warnings
from trueme.core.reports import build_report, write_report
from trueme.core.similarity import cosine_similarity
from trueme.errors import InputError, ProcessingError, ReportError


def test_cosine_identical_and_orthogonal():
    assert cosine_similarity(np.array([3, 4]), np.array([3, 4])) == pytest.approx(1)
    assert cosine_similarity(np.array([1, 0]), np.array([0, 1])) == 0


@pytest.mark.parametrize(
    "reference,probe",
    [
        ([0, 0], [1, 0]),
        ([1], [1, 0]),
        ([float("nan")], [1]),
        ([float("inf")], [1]),
        ([], []),
    ],
)
def test_invalid_features(reference, probe):
    with pytest.raises(ProcessingError):
        cosine_similarity(np.array(reference), np.array(probe))


def test_unicode_exif_orientation_and_unchanged_input(tmp_path):
    path = tmp_path / "参考 照片.jpg"
    image = Image.new("RGB", (12, 6), (255, 0, 0))
    exif = image.getexif()
    exif[274] = 6
    image.save(path, exif=exif)
    original = path.read_bytes()
    loaded = load_image(path)
    assert loaded.shape == (12, 6, 3)
    assert loaded[0, 0, 2] > 240  # BGR, after orientation.
    assert path.read_bytes() == original


def test_invalid_and_animated_images(tmp_path):
    invalid = tmp_path / "bad.jpg"
    invalid.write_bytes(b"not an image")
    with pytest.raises(InputError, match="Cannot read"):
        load_image(invalid)
    animated = tmp_path / "animated.png"
    Image.new("RGB", (4, 4), "red").save(
        animated, save_all=True, append_images=[Image.new("RGB", (4, 4), "blue")]
    )
    with pytest.raises(InputError, match="multi-frame"):
        load_image(animated)


def test_quality_hints_are_heuristics():
    hints = quality_warnings(np.zeros((100, 100, 3), dtype=np.uint8), (0, 0, 30, 30))
    assert len(hints) == 3
    assert all(hint.startswith("Heuristic:") for hint in hints)


@pytest.mark.parametrize("count", [0, 2])
def test_comparison_rejects_non_single_face(tmp_path, count):
    source = tmp_path / "image.png"
    Image.new("RGB", (10, 10)).save(source)
    detector = SimpleNamespace(detect=lambda image: [object()] * count)
    with pytest.raises(InputError, match=f"exactly one face; detected {count}"):
        compare_images(source, source, detector, None)


def test_comparison_reports_pair_and_quality_without_features(tmp_path):
    source = tmp_path / "image.png"
    Image.new("RGB", (100, 100), "gray").save(source)
    detector = SimpleNamespace(detect=lambda image: [SimpleNamespace(bbox=(0, 0, 100, 100))])
    recognizer = SimpleNamespace(embed=lambda image, face: np.array([1, 0]))
    result = compare_images(source, source, detector, recognizer)
    assert result["cosine_similarity"] == 1
    assert set(result["quality_warnings"]) == {"reference", "probe"}
    assert set(result) == {"cosine_similarity", "quality_warnings"}


def report_fixture(reference=Path("private/reference.jpg"), probe=Path("private/probe.jpg")):
    return build_report(
        reference,
        probe,
        {
            "cosine_similarity": 0.25,
            "quality_warnings": {"reference": [], "probe": []},
            "embeddings": [1, 2],
            "image_data": "secret",
        },
        [{"name": "test", "version": "1"}],
        {"requested": "cpu"},
        "0.1.0",
    )


def test_report_contains_only_public_result_and_explicit_export(tmp_path):
    report = report_fixture()
    encoded = json.dumps(report)
    assert report["inputs"] == {"reference": "reference.jpg", "probe": "probe.jpg"}
    assert "private" not in encoded and "embeddings" not in encoded and "image_data" not in encoded
    target = tmp_path / "report.json"
    inputs = (tmp_path / "a.jpg", tmp_path / "b.jpg")
    write_report(report, target, inputs)
    assert json.loads(target.read_text()) == report
    with pytest.raises(ReportError, match="already exists"):
        write_report(report, target, inputs)
    write_report(report, target, inputs, overwrite=True)
    assert not list(tmp_path.glob(".trueme-*"))


@pytest.mark.parametrize("alias", ["direct", "hardlink", "symlink"])
def test_report_never_overwrites_input(tmp_path, alias):
    source = tmp_path / "source.jpg"
    source.write_bytes(b"original")
    target = source
    if alias != "direct":
        target = tmp_path / "alias.json"
        try:
            if alias == "hardlink":
                target.hardlink_to(source)
            else:
                target.symlink_to(source)
        except OSError:
            pytest.skip(f"{alias} creation unavailable on this platform")
    with pytest.raises(ReportError):
        write_report(report_fixture(), target, (source, tmp_path / "probe.jpg"), overwrite=True)
    assert source.read_bytes() == b"original"


def test_nonfinite_report_is_not_published(tmp_path):
    report = report_fixture()
    report["cosine_similarity"] = float("nan")
    target = tmp_path / "report.json"
    with pytest.raises(ReportError):
        write_report(report, target, (tmp_path / "a", tmp_path / "b"))
    assert not target.exists()
