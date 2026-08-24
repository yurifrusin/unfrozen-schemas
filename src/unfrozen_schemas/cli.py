"""Typer command-line entry points for the Milestone 0 foundation."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from unfrozen_schemas.config import ConfigLoadError, load_smoke_config
from unfrozen_schemas.provenance import BootstrapFailureRecord, RunManifest
from unfrozen_schemas.smoke import SmokeRunError, run_smoke

app = typer.Typer(
    name="unfrozen",
    help="Reproducible Unfrozen Schemas research tooling.",
    no_args_is_help=True,
    add_completion=False,
    pretty_exceptions_enable=False,
)

DEFAULT_SMOKE_CONFIG = Path("configs/experiment/smoke.yaml")


def _report_configuration_error(exc: Exception) -> None:
    typer.echo(f"Configuration error: {exc}", err=True)
    raise typer.Exit(code=2)


@app.command("validate-config")
def validate_config(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Smoke experiment YAML to validate.",
        ),
    ] = DEFAULT_SMOKE_CONFIG,
) -> None:
    """Validate and resolve the Milestone 0 smoke configuration."""

    try:
        resolved = load_smoke_config(config)
    except (ConfigLoadError, ValidationError) as exc:
        _report_configuration_error(exc)
        return
    typer.echo(
        "Valid Milestone 0 configuration: "
        f"CPU, offline, engineering-only, fixture {resolved.model.fixture_sha256[:12]}"
    )


@app.command()
def smoke(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Smoke experiment YAML.",
        ),
    ] = DEFAULT_SMOKE_CONFIG,
    output_root: Annotated[
        Path | None,
        typer.Option(
            "--output-root",
            file_okay=False,
            help="Optional run root override; primarily for isolated tests.",
        ),
    ] = None,
    seed: Annotated[
        int | None,
        typer.Option("--seed", min=0, max=4_294_967_295, help="Declared seed override."),
    ] = None,
) -> None:
    """Run the complete offline CPU-only Milestone 0 smoke path."""

    try:
        resolved = load_smoke_config(
            config,
            output_root_override=output_root,
            seed_override=seed,
        )
    except (ConfigLoadError, ValidationError) as exc:
        _report_configuration_error(exc)
        return

    try:
        result = run_smoke(resolved)
    except SmokeRunError as exc:
        typer.echo(f"Smoke failure reason: {exc}", err=True)
        artifact_path = exc.failure_artifact_path
        artifact_kind = exc.failure_artifact_kind
        artifact_valid = False
        if artifact_path is not None and artifact_path.is_file():
            try:
                if artifact_kind == "failure_manifest":
                    RunManifest.model_validate_json(artifact_path.read_text(encoding="utf-8"))
                    artifact_valid = True
                elif artifact_kind == "bootstrap_failure":
                    BootstrapFailureRecord.model_validate_json(
                        artifact_path.read_text(encoding="utf-8")
                    )
                    artifact_valid = True
            except Exception:
                artifact_valid = False
        if artifact_valid:
            if artifact_kind == "failure_manifest":
                typer.echo(
                    f"Smoke run failed; validated failure manifest: {artifact_path}", err=True
                )
            else:
                typer.echo(
                    f"Smoke bootstrap failed; validated bootstrap failure record: {artifact_path}",
                    err=True,
                )
        else:
            typer.echo(
                "Smoke run failed; no validated failure artifact could be written. "
                f"Run directory: {exc.run_directory}",
                err=True,
            )
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        typer.echo(
            f"Smoke preflight failed before run creation: {type(exc).__name__}: {exc}",
            err=True,
        )
        raise typer.Exit(code=1) from exc

    typer.echo(f"Smoke run completed successfully: {result.run_id}")
    typer.echo(f"Run directory: {result.run_directory}")
    typer.echo(f"Provenance manifest: {result.manifest_path}")


if __name__ == "__main__":
    app()
