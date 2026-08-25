"""Typer command-line entry points for governed offline engineering workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from unfrozen_schemas.config import ConfigLoadError, load_smoke_config
from unfrozen_schemas.core_config import load_core_config
from unfrozen_schemas.data.core_models import CoreRunError
from unfrozen_schemas.data.core_runner import (
    generate_core,
    locate_episode_manifest,
    replay_core,
    validate_core_manifest,
)
from unfrozen_schemas.data.core_runner import (
    inspect_episode as inspect_core_episode,
)
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
DEFAULT_CORE_CONFIG = Path("configs/experiment/milestone1_core_smoke.yaml")


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


@app.command("generate-core")
def generate_core_command(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="SchemaWorld Core YAML configuration.",
        ),
    ] = DEFAULT_CORE_CONFIG,
    output_root: Annotated[
        Path | None,
        typer.Option(
            "--output-root",
            file_okay=False,
            help="Optional isolated output root for tests and engineering smoke runs.",
        ),
    ] = None,
) -> None:
    """Generate the deterministic M1 core curriculum on CPU without network access."""

    try:
        loaded = load_core_config(config, output_root_override=output_root)
        result = generate_core(loaded)
    except (ConfigLoadError, ValidationError) as exc:
        _report_configuration_error(exc)
        return
    except CoreRunError as exc:
        typer.echo(f"Core generation failed: {exc}", err=True)
        if exc.manifest_path is not None:
            typer.echo(f"Validated failure manifest: {exc.manifest_path}", err=True)
        else:
            typer.echo(
                f"No validated failure manifest could be written in {exc.run_directory}",
                err=True,
            )
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        typer.echo(f"Core generation preflight failed: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Core generation completed: {result.run_id}")
    typer.echo(f"Run directory: {result.run_directory}")
    typer.echo(f"Core manifest: {result.manifest_path}")


@app.command("validate-core")
def validate_core_command(
    manifest: Annotated[
        Path,
        typer.Option(
            "--manifest",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Core generation or replay manifest.",
        ),
    ],
) -> None:
    """Validate M1 schemas, hashes, codec streams, pair parity, and artifact provenance."""

    try:
        validated = validate_core_manifest(manifest)
    except Exception as exc:
        typer.echo(f"Core validation failed: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(
        f"Core manifest valid: {validated.run_id}; "
        f"{len(validated.episodes)} episodes; {len(validated.pair_ids)} pairs"
    )


@app.command("replay-core")
def replay_core_command(
    manifest: Annotated[
        Path,
        typer.Option(
            "--manifest",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Completed generate-core manifest.",
        ),
    ],
) -> None:
    """Replay M1 trajectories and require byte-identical logical states and hashes."""

    try:
        result = replay_core(manifest)
    except CoreRunError as exc:
        typer.echo(f"Core replay failed: {exc}", err=True)
        if exc.manifest_path:
            typer.echo(f"Validated failure manifest: {exc.manifest_path}", err=True)
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        typer.echo(f"Core replay preflight failed: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Core replay completed: {result.run_id}")
    typer.echo(f"Replay manifest: {result.manifest_path}")


@app.command("inspect-episode")
def inspect_episode_command(
    episode_id: Annotated[
        str,
        typer.Option("--episode-id", help="Stable SchemaWorld episode ID."),
    ],
    manifest: Annotated[
        Path | None,
        typer.Option(
            "--manifest",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Generation manifest; inferred only when the episode occurs exactly once.",
        ),
    ] = None,
    render: Annotated[
        bool,
        typer.Option("--render", help="Write a deterministic human inspection PNG."),
    ] = False,
    output: Annotated[
        Path | None,
        typer.Option("--output", dir_okay=False, help="Optional inspection PNG path."),
    ] = None,
) -> None:
    """Inspect one persisted core episode and optionally render it headlessly."""

    try:
        selected_manifest = manifest or locate_episode_manifest(episode_id)
        summary = inspect_core_episode(
            episode_id,
            manifest_path=selected_manifest,
            render=render,
            output_path=output,
        )
    except Exception as exc:
        typer.echo(f"Episode inspection failed: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(summary, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    app()
