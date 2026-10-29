"""Log output contracts for terminals, pipes, and dependency-free setup."""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("mode", [
    "pipe",
    pytest.param("terminal", marks=pytest.mark.skipif(
        sys.platform == "win32",
        reason="Rich renders forced colors on Windows standard streams via the console API",
    )),
    "no_color",
    "bootstrap",
])
def test_utc_logs_and_terminal_colors(mode):
    source = str(Path(__file__).resolve().parents[1] / "src")
    code = f"""
import logging
import sys
import time
sys.path.insert(0, {source!r})
from trueme.logging_config import configure_logging
if hasattr(time, "tzset"):
    time.tzset()
configure_logging()
for level in [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL,
              logging.INFO]:
    record = logging.LogRecord("trueme", level, "", 0, "Ready [literal]", (), None)
    record.created = 0
    logging.getLogger().handle(record)
"""
    env = dict(os.environ, TZ="Asia/Shanghai", TERM="xterm-256color", COLUMNS="160")
    for key in ("NO_COLOR", "FORCE_COLOR", "TTY_COMPATIBLE"):
        env.pop(key, None)
    if mode in {"terminal", "no_color"}:
        env["FORCE_COLOR"] = "1"
    if mode == "no_color":
        env["NO_COLOR"] = "1"
    result = subprocess.run(
        [sys.executable, *(["-S"] if mode == "bootstrap" else []), "-c", code],
        env=env, capture_output=True, text=True, check=True,
    )
    assert result.stdout == ""
    lines = re.sub(r"\x1b\[[0-9;]*m", "", result.stderr).splitlines()
    levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "INFO"]
    assert lines == [f"1970-01-01T00:00:00Z {level} Ready [literal]" for level in levels]
    if mode == "terminal":
        assert result.stderr.splitlines() == [
            f"1970-01-01T00:00:00Z \x1b[{color}m{level}\x1b[0m Ready [literal]"
            for level, color in zip(levels, ["36", "32", "33", "31", "1;31", "32"])
        ]
    else:
        assert "\x1b[" not in result.stderr
