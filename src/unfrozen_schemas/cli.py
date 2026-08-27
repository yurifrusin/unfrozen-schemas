"""Typer command-line entry points for governed offline engineering workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from unfrozen_schemas.config import ConfigLoadError, find_repository_root, load_smoke_config
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
from unfrozen_schemas.evaluation.benchmark_lifecycle import (
    build_benchmark,
    create_engineering_freeze_approval,
    freeze_benchmark,
)
from unfrozen_schemas.evaluation.benchmark_models import (
    BenchmarkOperationError,
    BenchmarkPurpose,
)
from unfrozen_schemas.evaluation.benchmark_persistence import (
    resolve_candidate_version_path,
    resolve_version_path,
    validate_benchmark_version,
)
from unfrozen_schemas.evaluation.benchmark_validation import (
    audit_tracked_benchmark_paths,
    validate_benchmark_manifest,
)
from unfrozen_schemas.evaluation.literal_generation import generate_literal_source
from unfrozen_schemas.evaluation.literal_models import LiteralOperationError
from unfrozen_schemas.evaluation.literal_review import (
    build_literal_review,
    inspect_literal_item,
    materialize_literal_candidate,
    validate_literal_benchmark,
    validate_literal_review,
)
from unfrozen_schemas.evaluation.literal_validation import validate_literal_source
from unfrozen_schemas.literal_config import load_literal_config
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


def _resolve_benchmark_manifest(version: str) -> Path:
    repository = find_repository_root(Path.cwd())
    safe_version = validate_benchmark_version(version)
    candidates = (
        resolve_version_path(repository, "private", safe_version) / "candidate_manifest.json",
        resolve_version_path(repository, "selection", safe_version) / "candidate_manifest.json",
        resolve_version_path(repository, "frozen", safe_version) / "frozen_manifest.json",
    )
    private, _selection, frozen = candidates
    existing = tuple(path for path in candidates if path.is_file())
    if len(existing) == 1:
        return existing[0]
    if set(existing) == {private, frozen}:
        private_payload = json.loads(private.read_text(encoding="utf-8"))
        frozen_payload = json.loads(frozen.read_text(encoding="utf-8"))
        compatible = (
            private_payload.get("benchmark_version") == safe_version
            and frozen_payload.get("benchmark_version") == safe_version
            and private_payload.get("purpose") == frozen_payload.get("purpose")
            and private_payload.get("purpose") in {"outcome", "retention"}
            and private_payload.get("candidate_bundle_root_sha256")
            == frozen_payload.get("candidate_bundle_root_sha256")
        )
        if compatible:
            return frozen
    if existing:
        raise ValueError(
            f"Benchmark version {version!r} is ambiguous across canonical lifecycle roots"
        )
    raise ValueError(f"Version {version!r} has no canonical candidate or frozen manifest")


def _resolve_candidate_manifest(version: str) -> Path:
    repository = find_repository_root(Path.cwd())
    safe_version = validate_benchmark_version(version)
    candidates = (
        resolve_version_path(repository, "private", safe_version) / "candidate_manifest.json",
        resolve_version_path(repository, "selection", safe_version) / "candidate_manifest.json",
    )
    existing = tuple(path for path in candidates if path.is_file())
    if len(existing) > 1:
        raise ValueError(
            f"Benchmark version {version!r} is ambiguous across canonical candidate roots"
        )
    if existing:
        return existing[0]
    raise ValueError(f"Version {version!r} has no canonical PRIVATE candidate manifest")


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


@app.command("build-benchmark")
def build_benchmark_command(
    source: Annotated[
        Path,
        typer.Option(
            "--source",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing the one supported source_manifest.json + items.jsonl form.",
        ),
    ],
    version: Annotated[
        str, typer.Option("--version", help="Immutable benchmark version identity.")
    ],
    purpose: Annotated[
        BenchmarkPurpose,
        typer.Option("--purpose", case_sensitive=False, help="Quarantined benchmark purpose."),
    ],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            file_okay=False,
            help="Exact canonical destination; required only for engineering fixtures.",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Validate and derive logical identities without writes."),
    ] = False,
) -> None:
    """Build a deterministic answer-isolated PRIVATE benchmark candidate."""

    try:
        safe_version = validate_benchmark_version(version)
        repository = find_repository_root(Path.cwd())
        if output is None:
            if purpose is BenchmarkPurpose.ENGINEERING:
                raise ValueError("Engineering benchmark builds require an explicit --output")
            destination = resolve_candidate_version_path(repository, safe_version, purpose)
        else:
            destination = output
        result = build_benchmark(
            source_directory=source,
            output_directory=destination,
            version=safe_version,
            purpose=purpose,
            dry_run=dry_run,
            repository_root=repository,
        )
    except BenchmarkOperationError as exc:
        typer.echo(f"Benchmark build failed: {exc}", err=True)
        if exc.failure_record_path:
            typer.echo(f"Governed failure record: {exc.failure_record_path}", err=True)
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        typer.echo(f"Benchmark build preflight failed: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(result.model_dump(mode="json"), sort_keys=True, separators=(",", ":")))


@app.command("validate-benchmark")
def validate_benchmark_command(
    manifest: Annotated[
        Path | None,
        typer.Option(
            "--manifest",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="PRIVATE candidate or FROZEN manifest.",
        ),
    ] = None,
    version: Annotated[
        str | None,
        typer.Option(
            "--version",
            help="Resolve unambiguously under private, selection, or frozen canonical roots.",
        ),
    ] = None,
    against_manifest: Annotated[
        list[Path] | None,
        typer.Option(
            "--against-manifest",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Supplemental comparison in addition to the mandatory hash-bound scope.",
        ),
    ] = None,
) -> None:
    """Independently reconstruct benchmark schemas, hashes, partitions, and provenance."""

    try:
        if (manifest is None) == (version is None):
            raise ValueError("Provide exactly one of --manifest or --version")
        selected = manifest if manifest is not None else _resolve_benchmark_manifest(str(version))
        repository = find_repository_root(Path.cwd())
        validated = validate_benchmark_manifest(
            selected,
            against_manifests=tuple(against_manifest or ()),
            repository_root=repository,
        )
    except Exception as exc:
        typer.echo(f"Benchmark validation failed: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(
        f"Benchmark valid: {validated.benchmark_version}; {validated.lifecycle_state.value}; "
        f"purpose={validated.purpose.value}; items={validated.item_count}"
    )


@app.command("create-engineering-freeze-approval")
def create_engineering_freeze_approval_command(
    candidate_manifest: Annotated[
        Path,
        typer.Option(
            "--candidate-manifest",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", dir_okay=False, help="New engineering approval JSON path."),
    ],
    signer: Annotated[
        str, typer.Option("--signer", help="Non-empty engineering fixture signer/reference.")
    ],
) -> None:
    """Create an exact-hash approval usable only by the tracked engineering fixture."""

    try:
        approval = create_engineering_freeze_approval(
            candidate_manifest_path=candidate_manifest,
            output_path=output,
            signer=signer,
        )
    except Exception as exc:
        typer.echo(f"Engineering approval failed: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(approval.model_dump(mode="json"), sort_keys=True, separators=(",", ":")))


@app.command("freeze-benchmark")
def freeze_benchmark_command(
    approval: Annotated[
        Path,
        typer.Option(
            "--approval",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Exact-hash freeze approval JSON.",
        ),
    ],
    candidate_manifest: Annotated[
        Path | None,
        typer.Option(
            "--candidate-manifest",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    version: Annotated[
        str | None,
        typer.Option("--version", help="Resolve candidate under benchmarks/private/<version>."),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option("--output", file_okay=False, help="New write-once FROZEN destination."),
    ] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Validate candidate and approval without writes.")
    ] = False,
) -> None:
    """Freeze one validated PRIVATE candidate through an exact approval artifact."""

    try:
        if (candidate_manifest is None) == (version is None):
            raise ValueError("Provide exactly one of --candidate-manifest or --version")
        repository = find_repository_root(Path.cwd())
        safe_version = validate_benchmark_version(str(version)) if version is not None else None
        selected = (
            candidate_manifest
            if candidate_manifest is not None
            else _resolve_candidate_manifest(str(safe_version))
        )
        if not selected.is_file():
            raise ValueError(f"Candidate manifest does not exist: {selected}")
        if output is None and version is None:
            raise ValueError("--output is required when --candidate-manifest is used")
        destination = output or resolve_version_path(repository, "frozen", str(safe_version))
        result = freeze_benchmark(
            candidate_manifest_path=selected,
            approval_path=approval,
            output_directory=destination,
            dry_run=dry_run,
        )
    except BenchmarkOperationError as exc:
        typer.echo(f"Benchmark freeze failed: {exc}", err=True)
        if exc.failure_record_path:
            typer.echo(f"Governed failure record: {exc.failure_record_path}", err=True)
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        typer.echo(f"Benchmark freeze preflight failed: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(result.model_dump(mode="json"), sort_keys=True, separators=(",", ":")))


@app.command("audit-benchmark-git")
def audit_benchmark_git_command() -> None:
    """Reject tracked private, answer-bearing, selection, or v1_core benchmark content."""

    try:
        root = find_repository_root(Path.cwd())
        tracked = audit_tracked_benchmark_paths(root)
    except Exception as exc:
        typer.echo(f"Benchmark Git audit failed: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Benchmark Git audit passed: {len(tracked)} tracked safe path(s)")


@app.command("generate-literal-source")
def generate_literal_source_command(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Tracked M2.2 literal configuration.",
        ),
    ],
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Derive and validate logical identities without writes."),
    ] = False,
    source: Annotated[
        Path | None,
        typer.Option(
            "--source",
            file_okay=False,
            help="Engineering-only isolated source destination override.",
        ),
    ] = None,
) -> None:
    """Generate a private M2.1 source plus independently hash-bound M2.2 sidecars."""

    try:
        loaded = load_literal_config(config, source_root_override=source)
        result = generate_literal_source(loaded, dry_run=dry_run)
    except (LiteralOperationError, ConfigLoadError, ValidationError, ValueError) as exc:
        typer.echo(f"Literal source generation failed: {type(exc).__name__}: {exc}", err=True)
        if isinstance(exc, LiteralOperationError) and exc.failure_record_path:
            typer.echo(f"Governed failure record: {exc.failure_record_path}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(result.model_dump(mode="json"), sort_keys=True, separators=(",", ":")))


@app.command("validate-literal-source")
def validate_literal_source_command(
    source: Annotated[
        str,
        typer.Option("--source"),
    ],
) -> None:
    """Read-only reconstruction of one private literal source and every witness."""

    try:
        loaded = validate_literal_source(Path(source))
    except Exception as exc:
        typer.echo(f"Literal source validation failed: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(
        "Literal source valid: "
        f"version={loaded.source_manifest.benchmark_version}; "
        f"purpose={loaded.source_manifest.purpose.value}; "
        f"groups={len(loaded.item_bindings.bindings)}; items={len(loaded.items)}"
    )


@app.command("materialize-literal-candidate")
def materialize_literal_candidate_command(
    version: Annotated[
        str | None,
        typer.Option("--version", help="Canonical outcome candidate version."),
    ] = None,
    source: Annotated[
        Path | None,
        typer.Option(
            "--source",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Engineering source override.",
        ),
    ] = None,
    candidate_manifest: Annotated[
        Path | None,
        typer.Option(
            "--candidate-manifest",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Engineering M2.1 candidate-manifest override.",
        ),
    ] = None,
) -> None:
    """Atomically materialize M2.2 records beside a validated M2.1 candidate."""

    try:
        repository = find_repository_root(Path.cwd())
        if version is not None:
            if source is not None or candidate_manifest is not None:
                raise ValueError("--version cannot be combined with explicit engineering paths")
            safe_version = validate_benchmark_version(version)
            selected_source = repository / "benchmarks" / "source" / safe_version
            selected_candidate = (
                resolve_candidate_version_path(repository, safe_version, BenchmarkPurpose.OUTCOME)
                / "candidate_manifest.json"
            )
        else:
            if source is None or candidate_manifest is None:
                raise ValueError("Provide --version or both --source and --candidate-manifest")
            selected_source = source
            selected_candidate = candidate_manifest
        composite = materialize_literal_candidate(
            source_root=selected_source,
            candidate_manifest_path=selected_candidate,
            repository_root=repository,
        )
    except Exception as exc:
        typer.echo(
            f"Literal candidate materialization failed: {type(exc).__name__}: {exc}", err=True
        )
        raise typer.Exit(code=1) from exc
    typer.echo(
        "Literal candidate materialized: "
        f"version={composite.candidate_version}; purpose={composite.purpose}; "
        f"groups={composite.semantic_group_count}; items={composite.source_item_count}; "
        f"root={composite.literal_candidate_root_sha256}"
    )


@app.command("validate-literal-benchmark")
def validate_literal_benchmark_command(
    version: Annotated[
        str | None,
        typer.Option("--version", help="Canonical outcome candidate version."),
    ] = None,
    source: Annotated[
        Path | None,
        typer.Option(
            "--source",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Engineering source override.",
        ),
    ] = None,
    candidate_manifest: Annotated[
        Path | None,
        typer.Option(
            "--candidate-manifest",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Engineering M2.1 candidate-manifest override.",
        ),
    ] = None,
) -> None:
    """Read-only validation of an already materialized M2.2 composite."""

    try:
        repository = find_repository_root(Path.cwd())
        if version is not None:
            if source is not None or candidate_manifest is not None:
                raise ValueError("--version cannot be combined with explicit engineering paths")
            safe_version = validate_benchmark_version(version)
            selected_source = repository / "benchmarks" / "source" / safe_version
            selected_candidate = (
                resolve_candidate_version_path(repository, safe_version, BenchmarkPurpose.OUTCOME)
                / "candidate_manifest.json"
            )
        else:
            if source is None or candidate_manifest is None:
                raise ValueError("Provide --version or both --source and --candidate-manifest")
            selected_source = source
            selected_candidate = candidate_manifest
        composite = validate_literal_benchmark(
            source_root=selected_source,
            candidate_manifest_path=selected_candidate,
            repository_root=repository,
        )
    except Exception as exc:
        typer.echo(f"Literal benchmark validation failed: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(
        "Literal benchmark valid: "
        f"version={composite.candidate_version}; purpose={composite.purpose}; "
        f"groups={composite.semantic_group_count}; items={composite.source_item_count}; "
        f"root={composite.literal_candidate_root_sha256}"
    )


@app.command("build-literal-review")
def build_literal_review_command(
    version: Annotated[
        str | None,
        typer.Option("--version", help="Canonical outcome candidate version."),
    ] = None,
    source: Annotated[
        Path | None,
        typer.Option(
            "--source",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Engineering source override.",
        ),
    ] = None,
    output: Annotated[
        Path,
        typer.Option("--output", file_okay=False, help="New private review destination."),
    ] = Path("reports/private"),
) -> None:
    """Build a write-once local owner-review bundle; never upload it."""

    try:
        repository = find_repository_root(Path.cwd())
        if version is not None:
            if source is not None:
                raise ValueError("--version cannot be combined with --source")
            safe_version = validate_benchmark_version(version)
            selected_source = repository / "benchmarks" / "source" / safe_version
            expected = (repository / "reports" / "private" / safe_version).resolve()
            if output.resolve() != expected:
                raise ValueError(f"Outcome review output must be canonical: {expected}")
        elif source is not None:
            selected_source = source
        else:
            raise ValueError("Provide --version or an engineering --source")
        result = build_literal_review(source_root=selected_source, output_root=output)
    except Exception as exc:
        typer.echo(f"Literal review build failed: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(result.model_dump(mode="json"), sort_keys=True, separators=(",", ":")))


@app.command("validate-literal-review")
def validate_literal_review_command(
    review: Annotated[
        str,
        typer.Option("--review"),
    ],
    source: Annotated[
        str,
        typer.Option("--source"),
    ],
) -> None:
    """Read back a private review bundle and verify every retained file."""

    try:
        manifest = validate_literal_review(review_root=Path(review), source_root=Path(source))
    except Exception as exc:
        typer.echo(f"Literal review validation failed: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(
        f"Literal review valid: version={manifest.candidate_version}; "
        f"manifest={manifest.review_manifest_sha256}"
    )


@app.command("inspect-literal-item")
def inspect_literal_item_command(
    version: Annotated[str, typer.Option("--version", help="Private candidate version.")],
    item_id: Annotated[str, typer.Option("--item-id", help="Exact private item ID.")],
    render: Annotated[
        bool,
        typer.Option("--render", help="Write one deterministic private inspection PNG."),
    ] = False,
    output: Annotated[
        Path | None,
        typer.Option("--output", dir_okay=False, help="Required path when --render is used."),
    ] = None,
) -> None:
    """Explicitly disclose one locally held private item for owner inspection."""

    try:
        if render != (output is not None):
            raise ValueError("Use --render and --output together")
        repository = find_repository_root(Path.cwd())
        safe_version = validate_benchmark_version(version)
        summary = inspect_literal_item(
            source_root=repository / "benchmarks" / "source" / safe_version,
            item_id=item_id,
            render_path=output,
        )
    except Exception as exc:
        typer.echo(f"Literal item inspection failed: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(summary, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    app()
