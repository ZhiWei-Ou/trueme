"""Installed command contracts without weights or personal photos."""

import json
import os
import subprocess
import sys

import pytest


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "trueme", *args], capture_output=True, text=True, check=False
    )


@pytest.mark.parametrize("args", [("--help",), ("--version",), ("models", "list", "--json")])
def test_weight_independent_commands(args):
    result = run_cli(*args)
    assert result.returncode == 0, result.stderr
    assert result.stdout


def test_missing_required_arguments_json():
    result = run_cli("compare", "--json")
    assert result.returncode == 2
    assert json.loads(result.stdout)["error"]["exit_code"] == 2


def test_missing_models_json(tmp_path):
    result = run_cli(
        "compare",
        "--reference",
        "a.jpg",
        "--probe",
        "b.jpg",
        "--model-dir",
        str(tmp_path),
        "--json",
    )
    assert result.returncode == 3
    assert json.loads(result.stdout)["error"]["exit_code"] == 3


def test_invalid_device_json(tmp_path):
    result = run_cli(
        "compare",
        "--reference",
        "a.jpg",
        "--probe",
        "b.jpg",
        "--model-dir",
        str(tmp_path),
        "--device",
        "bogus",
        "--json",
    )
    assert result.returncode == 2
    assert json.loads(result.stdout)["error"]["type"] == "InputError"


def test_doctor_without_models(tmp_path):
    result = run_cli("doctor", "--model-dir", str(tmp_path), "--json")
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["inference"].startswith("not run")
    assert report["session_initialization"]["cpu"]["ok"] is False


def test_installed_resources_outside_project(tmp_path):
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-m", "trueme", "models", "list", "--json"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["models"]


def test_web_requires_models_before_listening(tmp_path):
    result = run_cli("web", "--model-dir", str(tmp_path), "--port", "1")
    assert result.returncode == 3
    assert "docs/models.md" in result.stderr
