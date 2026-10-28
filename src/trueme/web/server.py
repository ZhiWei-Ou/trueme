"""Loopback web page comparing live camera frames with one in-memory reference."""

from __future__ import annotations

import ipaddress
import json
import socket
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from typing import TYPE_CHECKING

from trueme.core.comparison import embed_single_face
from trueme.core.images import decode_image
from trueme.core.quality import quality_warnings
from trueme.core.similarity import cosine_similarity
from trueme.errors import DeviceError, InputError, ModelError, ProcessingError, TrueMeError

if TYPE_CHECKING:
    from trueme.models import ModelBundle

MAX_UPLOAD_BYTES = 15 * 1024 * 1024
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/favicon.svg": ("favicon.svg", "image/svg+xml"),
}
SECURITY_HEADERS = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' blob:; media-src 'self' blob:; "
        "object-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    ),
}
ERROR_STATUS = {
    InputError: HTTPStatus.BAD_REQUEST,
    ProcessingError: HTTPStatus.UNPROCESSABLE_ENTITY,
    DeviceError: HTTPStatus.SERVICE_UNAVAILABLE,
    ModelError: HTTPStatus.INTERNAL_SERVER_ERROR,
}
INTERPRETATION = (
    "Cosine similarity under SFace, not a confidence percentage, identity verdict, "
    "or prediction of third-party verification acceptance."
)


class LiveComparison:
    """One reference feature held in memory; frames are compared and discarded."""

    def __init__(self, bundle: ModelBundle):
        self._bundle = bundle
        self._reference = None
        # Serialize inference: sessions may fall back and replace themselves.
        self._lock = threading.Lock()

    def set_reference(self, data: bytes) -> dict:
        image = decode_image(data)
        with self._lock:
            feature, warnings, _ = embed_single_face(
                image, "reference", self._bundle.detector, self._bundle.recognizer
            )
            self._reference = feature
        return {"reference_set": True, "quality_warnings": warnings}

    def clear_reference(self) -> dict:
        with self._lock:
            self._reference = None
        return {"reference_set": False}

    def compare_frame(self, data: bytes) -> dict:
        image = decode_image(data)
        height, width = image.shape[:2]
        result = {
            "frame": {"width": width, "height": height},
            "faces": 0,
            "face": None,
            "cosine_similarity": None,
            "quality_warnings": [],
        }
        with self._lock:
            reference = self._reference
            faces = self._bundle.detector.detect(image)
            result["faces"] = len(faces)
            # A live frame without exactly one face is a normal state, not an error.
            if len(faces) != 1:
                return result
            face = faces[0]
            feature = self._bundle.recognizer.embed(image, face)
        result.update(
            face=[round(value, 1) for value in face.bbox],
            quality_warnings=quality_warnings(image, face.bbox),
        )
        if reference is not None:
            result["cosine_similarity"] = cosine_similarity(reference, feature)
        return result

    def status(self) -> dict:
        with self._lock:
            return {
                "reference_set": self._reference is not None,
                "models": self._bundle.metadata(),
                "device": self._bundle.device_info(),
                "interpretation": INTERPRETATION,
            }


def is_loopback(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def is_wildcard(host: str) -> bool:
    return host in {"", "0.0.0.0", "::"}


class Handler(BaseHTTPRequestHandler):
    server: LiveServer

    def log_message(self, format, *args) -> None:
        # Frames arrive several times per second; keep stderr for real diagnostics.
        pass

    def do_GET(self) -> None:
        if not self._trusted_host():
            return
        if self.path == "/api/status":
            self._json(HTTPStatus.OK, self.server.live.status())
        elif self.path in STATIC_FILES:
            name, content_type = STATIC_FILES[self.path]
            body = resources.files("trueme.web").joinpath("static", name).read_bytes()
            self._send(HTTPStatus.OK, body, content_type)
        else:
            self._error(HTTPStatus.NOT_FOUND, "NotFound", "Unknown path.")

    def do_POST(self) -> None:
        if not (self._trusted_host() and self._same_origin()):
            return
        routes = {
            "/api/reference": self.server.live.set_reference,
            "/api/frame": self.server.live.compare_frame,
        }
        if self.path not in routes:
            self._error(HTTPStatus.NOT_FOUND, "NotFound", "Unknown path.")
            return
        # Requiring an image type also forces a CORS preflight for cross-site scripts.
        if not self.headers.get("Content-Type", "").startswith("image/"):
            self._error(
                HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "InputError", "Send a JPEG, PNG, or WebP body."
            )
            return
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self._error(HTTPStatus.LENGTH_REQUIRED, "InputError", "Content-Length is required.")
            return
        if not 0 < length <= MAX_UPLOAD_BYTES:
            self._error(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "InputError", "Images must be 1 B to 15 MB."
            )
            return
        data = self.rfile.read(length)
        try:
            self._json(HTTPStatus.OK, routes[self.path](data))
        except TrueMeError as exc:
            status = ERROR_STATUS.get(type(exc), HTTPStatus.INTERNAL_SERVER_ERROR)
            self._error(status, type(exc).__name__, str(exc))

    def do_DELETE(self) -> None:
        if not (self._trusted_host() and self._same_origin()):
            return
        if self.path == "/api/reference":
            self._json(HTTPStatus.OK, self.server.live.clear_reference())
        else:
            self._error(HTTPStatus.NOT_FOUND, "NotFound", "Unknown path.")

    def _trusted_host(self) -> bool:
        """Reject DNS-rebinding requests whose Host header names another site."""
        host = self.headers.get("Host", "")
        if self.server.allowed_hosts is None or host in self.server.allowed_hosts:
            return True
        self._error(HTTPStatus.FORBIDDEN, "Forbidden", "Unexpected Host header.")
        return False

    def _same_origin(self) -> bool:
        origin = self.headers.get("Origin")
        if origin is None or origin == f"http://{self.headers.get('Host', '')}":
            return True
        self._error(HTTPStatus.FORBIDDEN, "Forbidden", "Cross-origin requests are not allowed.")
        return False

    def _json(self, status: HTTPStatus, value: dict) -> None:
        body = json.dumps(value, allow_nan=False, ensure_ascii=False).encode()
        self._send(status, body, "application/json; charset=utf-8")

    def _error(self, status: HTTPStatus, kind: str, message: str) -> None:
        self._json(status, {"error": {"type": kind, "message": message}})

    def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for name, value in SECURITY_HEADERS.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)


class LiveServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, host: str, port: int, live: LiveComparison):
        self.address_family = socket.AF_INET6 if ":" in host else socket.AF_INET
        super().__init__((host, port), Handler)
        self.live = live
        port = self.server_address[1]
        if is_wildcard(host):
            # Clients reach a wildcard bind through addresses the server cannot enumerate.
            self.allowed_hosts = None
        else:
            names = {"localhost", "127.0.0.1", "[::1]", f"[{host}]" if ":" in host else host}
            self.allowed_hosts = {f"{name}:{port}" for name in names}
            if port == 80:
                self.allowed_hosts |= names

    @property
    def url(self) -> str:
        host, port = self.server_address[:2]
        return f"http://[{host}]:{port}/" if ":" in host else f"http://{host}:{port}/"


def create_server(host: str, port: int, bundle: ModelBundle) -> LiveServer:
    try:
        return LiveServer(host, port, LiveComparison(bundle))
    except OSError as exc:
        raise InputError(f"Cannot listen on {host}:{port}: {exc.strerror or exc}.") from exc
