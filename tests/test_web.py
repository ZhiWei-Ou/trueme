"""Live web contracts with controlled model fixtures; no camera, weights, or photos."""

import http.client
import io
import json
import threading
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image

from trueme.web.server import create_server


def png(size=(100, 100)):
    buffer = io.BytesIO()
    Image.new("RGB", size, "gray").save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def live():
    """Serve fake models; `faces` controls how many faces each image contains."""
    state = SimpleNamespace(faces=1, feature=np.array([1.0, 0.0]))
    face = SimpleNamespace(bbox=(10.0, 10.0, 80.0, 80.0))
    bundle = SimpleNamespace(
        detector=SimpleNamespace(detect=lambda image: [face] * state.faces),
        recognizer=SimpleNamespace(embed=lambda image, face: state.feature),
        metadata=lambda: [{"name": "fake"}],
        device_info=lambda: {"requested": "cpu"},
    )
    server = create_server("127.0.0.1", 0, bundle)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]

    def request(method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        data = response.read()
        connection.close()
        return response, data

    state.request = request
    yield state
    server.shutdown()
    server.server_close()


def post(live, path, body, **headers):
    response, data = live.request(
        "POST", path, body, {"Content-Type": "image/png", **headers}
    )
    return response.status, json.loads(data)


def test_frame_scores_only_against_a_reference(live):
    status, frame = post(live, "/api/frame", png())
    assert status == 200 and frame["faces"] == 1 and frame["cosine_similarity"] is None

    assert post(live, "/api/reference", png())[1]["reference_set"] is True
    live.feature = np.array([1.0, 1.0])
    status, frame = post(live, "/api/frame", png())
    assert frame["cosine_similarity"] == pytest.approx(2**-0.5)
    assert frame["face"] == [10.0, 10.0, 80.0, 80.0]
    assert set(frame) == {"frame", "faces", "face", "cosine_similarity", "quality_warnings"}

    live.request("DELETE", "/api/reference")
    assert post(live, "/api/frame", png())[1]["cosine_similarity"] is None


@pytest.mark.parametrize("count", [0, 2])
def test_frames_without_exactly_one_face_have_no_score(live, count):
    post(live, "/api/reference", png())
    live.faces = count
    status, frame = post(live, "/api/frame", png())
    assert status == 200
    assert frame["faces"] == count and frame["face"] is None and frame["cosine_similarity"] is None


def test_reference_requires_exactly_one_face(live):
    live.faces = 2
    status, body = post(live, "/api/reference", png())
    assert status == 400 and "exactly one face; detected 2" in body["error"]["message"]
    assert json.loads(live.request("GET", "/api/status")[1])["reference_set"] is False


def test_rejects_invalid_and_cross_site_requests(live):
    assert post(live, "/api/frame", b"not an image")[0] == 400
    response, _ = live.request("POST", "/api/frame", b"x", {"Content-Type": "text/plain"})
    assert response.status == 415
    assert post(live, "/api/frame", png(), Origin="http://evil.example")[0] == 403
    response, _ = live.request("GET", "/", headers={"Host": "evil.example"})
    assert response.status == 403


def test_page_is_packaged_with_restrictive_headers(live):
    response, body = live.request("GET", "/")
    assert response.status == 200 and b"TrueMe Live" in body
    assert "default-src 'self'" in response.getheader("Content-Security-Policy")
    assert response.getheader("Cache-Control") == "no-store"
    assert live.request("GET", "/app.js")[0].status == 200
    assert b"photo-export.js" in body
    assert live.request("GET", "/photo-export.js")[0].status == 200


def test_photo_export_download_and_validation(live):
    response, body = live.request(
        "POST", "/api/photo-export?size=two-inch", png(), {"Content-Type": "image/png"}
    )
    assert response.status == 200
    assert response.getheader("Content-Type") == "image/jpeg"
    assert response.getheader("Content-Disposition") == 'attachment; filename="trueme-two-inch.jpg"'
    assert response.getheader("Cache-Control") == "no-store"
    with Image.open(io.BytesIO(body)) as photo:
        assert photo.size == (413, 579)
        assert photo.info["dpi"] == (300, 300)
    assert json.loads(live.request("GET", "/api/status")[1])["reference_set"] is False
    for query in ("", "?size=unknown", "?size=one-inch&size=two-inch"):
        assert post(live, f"/api/photo-export{query}", png())[0] == 400
    assert post(live, "/api/photo-export?size=one-inch", b"invalid")[0] == 400
    assert post(
        live, "/api/photo-export?size=one-inch", png(), Origin="http://evil.example"
    )[0] == 403


def test_custom_photo_export_and_parameter_contract(live):
    response, body = live.request(
        "POST", "/api/photo-export?size=custom&width_mm=50.8&height_mm=25.4",
        png(), {"Content-Type": "image/png"},
    )
    assert response.status == 200
    assert response.getheader("Content-Disposition") == 'attachment; filename="trueme-custom.jpg"'
    with Image.open(io.BytesIO(body)) as photo:
        assert photo.size == (600, 300)
    for query in (
        "size=custom", "size=custom&width_mm=25", "size=one-inch&width_mm=25&height_mm=35",
        "size=custom&width_mm=25&height_mm=35&extra=1",
        "size=custom&width_mm=25&width_mm=30&height_mm=35",
        "size=custom&width_mm=nan&height_mm=35",
        "size=custom&width_mm=no&height_mm=35",
        "size=custom&width_mm=301&height_mm=35",
    ):
        assert post(live, f"/api/photo-export?{query}", png())[0] == 400


def test_png_photo_export_and_format_validation(live):
    source = io.BytesIO()
    Image.new("RGBA", (295, 413), (10, 20, 30, 128)).save(source, format="PNG")
    response, body = live.request(
        "POST", "/api/photo-export?size=one-inch&format=png", source.getvalue(),
        {"Content-Type": "image/png"},
    )
    assert response.status == 200
    assert response.getheader("Content-Type") == "image/png"
    assert response.getheader("Content-Disposition") == 'attachment; filename="trueme-one-inch.png"'
    with Image.open(io.BytesIO(body)) as photo:
        assert photo.mode == "RGBA"
        assert photo.getpixel((100, 100)) == (10, 20, 30, 128)
    for query in ("format=gif", "format=", "format=png&format=jpeg"):
        assert post(live, f"/api/photo-export?size=one-inch&{query}", png())[0] == 400
