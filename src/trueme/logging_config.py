"""UTC operational logs, with terminal colors when Rich is installed."""

import logging
import time
from datetime import datetime, timezone


def configure_logging() -> None:
    try:
        from rich.console import Console
        from rich.highlighter import NullHighlighter
        from rich.logging import RichHandler
        from rich.text import Text
        from rich.theme import Theme
    except ModuleNotFoundError as exc:
        if exc.name != "rich":
            raise
        # Development commands also run before project dependencies are installed.
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%SZ"
        )
        formatter.converter = time.gmtime
        handler.setFormatter(formatter)
    else:
        class LogHandler(RichHandler):
            def render(self, *, record, traceback, message_renderable):
                timestamp = datetime.fromtimestamp(record.created, timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
                style = "" if self.console.no_color else f"logging.level.{record.levelname.lower()}"
                return Text.assemble(
                    timestamp, " ",
                    (record.levelname, style),
                    " ", message_renderable,
                )

        handler = LogHandler(
            console=Console(stderr=True, theme=Theme({
                "logging.level.debug": "cyan",
                "logging.level.info": "green",
                "logging.level.warning": "yellow",
                "logging.level.error": "red",
                "logging.level.critical": "bold red",
            })),
            highlighter=NullHighlighter(),
            keywords=[],
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[handler])
