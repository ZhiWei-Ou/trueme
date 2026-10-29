"""Model acquisition contracts using synthetic bytes and no network access."""

import hashlib
import json
import runpy
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def downloader(tmp_path, monkeypatch):
    script = Path(__file__).resolve().parents[1] / "scripts/dev.py"
    download = runpy.run_path(str(script))["download_models"]
    monkeypatch.setitem(download.__globals__, "ROOT", tmp_path)
    manifest = tmp_path / "src/trueme/models/manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps([{
        "filename": "fixture.onnx",
        "download_url": "https://example.invalid/fixture.onnx",
        "sha256": hashlib.sha256(b"fixture weight").hexdigest(),
    }]))
    return download, tmp_path / "models/fixture.onnx"


def test_download_verifies_and_skips_existing_weights(downloader, monkeypatch):
    download, target = downloader
    calls = []

    def fetch(command, *, check):
        assert check
        assert command[-1] == "https://example.invalid/fixture.onnx"
        calls.append(command)
        Path(command[command.index("--output") + 1]).write_bytes(b"fixture weight")

    monkeypatch.setattr(subprocess, "run", fetch)
    download()
    download()
    assert len(calls) == 1
    assert target.read_bytes() == b"fixture weight"
    assert list(target.parent.iterdir()) == [target]


@pytest.mark.parametrize("network_failure", [False, True])
def test_failed_download_leaves_no_weight_or_temporary_files(
    downloader, monkeypatch, network_failure
):
    download, target = downloader

    def fetch(command, *, check):
        Path(command[command.index("--output") + 1]).write_bytes(b"incomplete")
        if network_failure:
            raise subprocess.CalledProcessError(22, command)

    monkeypatch.setattr(subprocess, "run", fetch)
    expected = subprocess.CalledProcessError if network_failure else SystemExit
    with pytest.raises(expected):
        download()
    assert list(target.parent.iterdir()) == []


def test_mismatched_existing_weight_is_preserved(downloader, monkeypatch):
    download, target = downloader
    target.parent.mkdir()
    target.write_bytes(b"existing weight")

    def unexpected_download(*args, **kwargs):
        pytest.fail("Existing mismatched weights must not trigger downloads")

    monkeypatch.setattr(subprocess, "run", unexpected_download)
    with pytest.raises(SystemExit, match="move or remove"):
        download()
    assert target.read_bytes() == b"existing weight"
