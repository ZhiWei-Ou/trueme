from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

from trueme.errors import DeviceError, ModelError, ProcessingError
from trueme.models.device import CPU, CUDA, ModelSession
from trueme.models.onnx import SFACE_TARGET, align_face
from trueme.models.registry import load_manifest, validated_models


@pytest.fixture
def runtime(monkeypatch):
    import onnxruntime as ort

    sessions = []
    settings = {"available": [CPU], "drop_cuda": False, "fail_init": False, "fail_run": False}

    def create(path, sess_options, providers):
        if settings["fail_init"] and CUDA in providers:
            raise RuntimeError("CUDA initialization failed")
        actual = [CPU] if settings["drop_cuda"] else providers
        session = Mock()
        session.get_providers.return_value = actual
        session.get_inputs.return_value = [SimpleNamespace(name="input")]
        session.run.side_effect = (
            RuntimeError("GPU execution failed")
            if settings["fail_run"] and CUDA in actual
            else None
        )
        session.run.return_value = [np.array([1.0])]
        sessions.append(session)
        return session

    monkeypatch.setattr(ort, "get_available_providers", lambda: settings["available"])
    monkeypatch.setattr(ort, "InferenceSession", create)
    return settings, sessions


def test_unavailable_cuda_auto_and_explicit(runtime):
    session = ModelSession(Path("weight.onnx"), "auto")
    assert session.info()["configured_providers"] == [CPU]
    assert "unavailable" in session.fallback_reason
    with pytest.raises(DeviceError, match="unavailable"):
        ModelSession(Path("weight.onnx"), "cuda")


@pytest.mark.parametrize("failure", ["drop_cuda", "fail_init"])
def test_cuda_initialization_must_retain_provider(runtime, failure):
    settings, sessions = runtime
    settings.update(available=[CUDA, CPU], **{failure: True})
    session = ModelSession(Path("weight.onnx"), "auto")
    assert session.info()["configured_providers"] == [CPU]
    assert "initialization failed" in session.fallback_reason
    with pytest.raises(DeviceError, match="initialization failed"):
        ModelSession(Path("weight.onnx"), "cuda")
    assert all(s.disable_fallback.called for s in sessions)


def test_cuda_execution_fallback_is_observable(runtime):
    settings, sessions = runtime
    settings.update(available=[CUDA, CPU], fail_run=True)
    session = ModelSession(Path("weight.onnx"), "auto")
    assert session.run(np.ones(1))[0] == np.array([1.0])
    assert session.info()["configured_providers"] == [CPU]
    assert "execution failed" in session.fallback_reason
    assert len(sessions) == 2
    explicit = ModelSession(Path("weight.onnx"), "cuda")
    with pytest.raises(DeviceError, match="execution failed"):
        explicit.run(np.ones(1))
    assert len(sessions) == 3  # no CPU session created for explicit CUDA


def test_cpu_execution_failure_is_processing_error(runtime):
    session = ModelSession(Path("weight.onnx"), "cpu")
    session.session.run.side_effect = RuntimeError("failed")
    with pytest.raises(ProcessingError, match="CPU"):
        session.run(np.ones(1))


def test_manifest_missing_and_wrong_weights(tmp_path):
    manifest = load_manifest()
    assert {m["role"] for m in manifest} == {"detector", "recognizer"}
    with pytest.raises(ModelError, match="Acquire"):
        validated_models(tmp_path)
    (tmp_path / manifest[0]["filename"]).write_bytes(b"not an ONNX weight")
    with pytest.raises(ModelError, match="Checksum"):
        validated_models(tmp_path)


def test_alignment_uses_similarity_transform():
    image = np.arange(112 * 112 * 3, dtype=np.uint8).reshape(112, 112, 3)
    np.testing.assert_array_equal(align_face(image, SFACE_TARGET), image)
    with pytest.raises(ProcessingError, match="degenerate"):
        align_face(image, np.ones((5, 2)))
