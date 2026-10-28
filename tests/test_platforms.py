from pathlib import Path

from trueme.config import resolve_model_dir
from trueme.platforms.infrastructure import LinuxPaths, MacOSPaths, WindowsPaths


def test_directory_precedence(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    paths = LinuxPaths()
    assert resolve_model_dir(None, paths) == tmp_path / "data/trueme/models"
    monkeypatch.setenv("TRUEME_MODEL_DIR", str(tmp_path / "environment"))
    assert resolve_model_dir(None, paths) == tmp_path / "environment"
    assert resolve_model_dir(tmp_path / "explicit", paths) == tmp_path / "explicit"


def test_platform_storage_conventions(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("XDG_DATA_HOME", "relative-is-invalid")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    assert LinuxPaths().model_dir() == tmp_path / ".local/share/trueme/models"
    assert MacOSPaths().model_dir() == tmp_path / "Library/Application Support/TrueMe/models"
    assert WindowsPaths().model_dir() == tmp_path / "local/TrueMe/models"
