"""Command presentation and application composition."""

import json
import logging
import sys
from pathlib import Path
from typing import Annotated

import click
import typer
from rich.console import Console

from trueme import __version__
from trueme.errors import TrueMeError
from trueme.logging_config import configure_logging

app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False)
models_app = typer.Typer(no_args_is_help=True)
app.add_typer(models_app, name="models")
console = Console()
logger = logging.getLogger(__name__)


def emit(value: dict, as_json: bool) -> None:
    if as_json:
        typer.echo(json.dumps(value, allow_nan=False, ensure_ascii=False))
    else:
        console.print_json(data=value)


def show_comparison(report: dict) -> None:
    console.print(f"Cosine similarity: {report['cosine_similarity']:.6f}")
    console.print(
        "Models: " + ", ".join(f"{model['name']} {model['version']}" for model in report["models"])
    )
    for role, session in report["device"]["sessions"].items():
        console.print(f"{role}: {', '.join(session['configured_providers'])}")
        if session["fallback_reason"]:
            console.print(session["fallback_reason"])
    for role, warnings in report["quality_warnings"].items():
        for warning in warnings:
            console.print(f"{role}: {warning}")
    console.print(report["interpretation"])


def version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def root(
    version: Annotated[
        bool, typer.Option("--version", callback=version_callback, is_eager=True)
    ] = False,
) -> None:
    """Compare two consented face photos locally under a selected model."""


def model_location(explicit: Path | None) -> Path:
    from trueme.config import resolve_model_dir
    from trueme.platforms import select_platform

    return resolve_model_dir(explicit, select_platform())


@app.command()
def compare(
    reference: Annotated[Path, typer.Option(help="Reference/enrollment photo.")],
    probe: Annotated[Path, typer.Option(help="Probe/camera-condition photo.")],
    model_dir: Annotated[
        Path | None, typer.Option(help="Directory containing model weights.")
    ] = None,
    device: Annotated[str, typer.Option(help="auto, cpu, or cuda.")] = "auto",
    as_json: Annotated[bool, typer.Option("--json", help="Emit one JSON object.")] = False,
    output: Annotated[Path | None, typer.Option(help="Explicit JSON report destination.")] = None,
    overwrite: Annotated[bool, typer.Option(help="Replace an existing report.")] = False,
    verbose: Annotated[bool, typer.Option(help="Print diagnostics to stderr.")] = False,
) -> None:
    """Detect, align, and compare exactly one face in each input."""
    from trueme.core.comparison import compare_images
    from trueme.core.reports import build_report, write_report
    from trueme.errors import InputError
    from trueme.models import create_models

    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    if device not in {"auto", "cpu", "cuda"}:
        raise InputError("Device must be auto, cpu, or cuda.")
    bundle = create_models(model_location(model_dir), device)
    comparison = compare_images(reference, probe, bundle.detector, bundle.recognizer)
    report = build_report(
        reference, probe, comparison, bundle.metadata(), bundle.device_info(), __version__
    )
    if output is not None:
        write_report(report, output, (reference, probe), overwrite=overwrite)
    logger.debug("Device diagnostics: %s", json.dumps(bundle.device_info(), allow_nan=False))
    if as_json:
        emit(report, True)
    else:
        show_comparison(report)


@app.command()
def web(
    host: Annotated[str, typer.Option(help="Address to listen on.")] = "127.0.0.1",
    port: Annotated[int, typer.Option(min=1, max=65535, help="Port to listen on.")] = 8765,
    model_dir: Annotated[
        Path | None, typer.Option(help="Directory containing model weights.")
    ] = None,
    device: Annotated[str, typer.Option(help="auto, cpu, or cuda.")] = "auto",
) -> None:
    """Serve a local page comparing live camera frames with one reference photo."""
    from trueme.errors import InputError
    from trueme.models import create_models
    from trueme.web.server import create_server, is_loopback

    if device not in {"auto", "cpu", "cuda"}:
        raise InputError("Device must be auto, cpu, or cuda.")
    bundle = create_models(model_location(model_dir), device)
    server = create_server(host, port, bundle)
    if not is_loopback(host):
        logger.warning(
            "Listening beyond this computer exposes the reference and camera frames "
            "to the network, and browsers allow camera access only on localhost or HTTPS."
        )
    logger.info("TrueMe Live: %s", server.url)
    logger.info("Press Ctrl+C to stop; the reference and frames are discarded on exit.")
    with server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


@app.command()
def doctor(
    model_dir: Annotated[Path | None, typer.Option()] = None,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Inspect dependencies, model files, and CPU/CUDA session initialization."""
    from trueme.diagnostics import diagnose

    emit(diagnose(model_location(model_dir)), as_json)


@models_app.command("list")
def list_models(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Show the packaged model manifest; no download is performed."""
    from trueme.models.registry import load_manifest

    emit({"models": load_manifest()}, as_json)


def main() -> None:
    """Keep parser and application failures machine-readable in JSON mode."""
    configure_logging()
    as_json = "--json" in sys.argv[1:]
    try:
        app(standalone_mode=False)
    except (TrueMeError, click.ClickException) as exc:
        code = exc.exit_code
        message = exc.format_message() if isinstance(exc, click.ClickException) else str(exc)
        error = {"error": {"type": type(exc).__name__, "message": message, "exit_code": code}}
        if as_json:
            emit(error, True)
        else:
            logger.error("%s", message)
        raise SystemExit(code) from None


if __name__ == "__main__":
    main()
