"""Offline CPU smoke execution for the Milestone 0 foundation."""

from __future__ import annotations

import json
import logging
import time
import tracemalloc
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from unfrozen_schemas.budgets import ResourceBudget, ResourceMeasurementBasis
from unfrozen_schemas.config import ResolvedSmokeConfig
from unfrozen_schemas.constants import (
    BOOTSTRAP_FAILURE_FILENAME,
    BUDGET_FILENAME,
    GATE_METADATA_FILENAME,
    LOG_FILENAME,
    MANIFEST_FILENAME,
    RESOLVED_CONFIG_FILENAME,
    TOY_OUTPUT_FILENAME,
)
from unfrozen_schemas.logging_utils import close_logging, configure_logging
from unfrozen_schemas.provenance import (
    ArtifactRecord,
    BootstrapFailureRecord,
    GitState,
    Phase1GateMetadata,
    PlatformInformation,
    RunManifest,
    artifact_record,
    capture_git_state,
    collect_package_versions,
    collect_platform_information,
    create_run_id,
    seed_everything,
    utc_now,
    write_json,
)

FailureArtifactKind = Literal["failure_manifest", "bootstrap_failure"]


class TinyLinearFixture(BaseModel):
    """Validated representation of the local deterministic linear fixture."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1"]
    model_type: Literal["tiny_linear"]
    seed: int = Field(ge=0, le=4_294_967_295)
    input_size: int = Field(gt=0, le=32)
    output_size: int = Field(gt=0, le=32)
    weights: list[list[float]]
    bias: list[float]

    @model_validator(mode="after")
    def validate_dimensions(self) -> TinyLinearFixture:
        if len(self.weights) != self.output_size:
            raise ValueError("Fixture weight-row count must equal output_size")
        if any(len(row) != self.input_size for row in self.weights):
            raise ValueError("Every fixture weight row must equal input_size")
        if len(self.bias) != self.output_size:
            raise ValueError("Fixture bias length must equal output_size")
        return self


class ToyModelOutput(BaseModel):
    """Deterministic result of one fixture forward pass."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1"] = "1"
    fixture_model_type: Literal["tiny_linear"] = "tiny_linear"
    fixture_seed: int
    declared_run_seed: int
    fixture_sha256: str
    device: Literal["cpu"] = "cpu"
    input: list[float]
    output: list[float]


class SmokeResult(BaseModel):
    """Small in-process result returned to the CLI and integration tests."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str
    run_directory: Path
    manifest_path: Path
    toy_output: ToyModelOutput


class SmokeRunError(RuntimeError):
    """Raised with the strongest validated failure artifact that could be written."""

    def __init__(
        self,
        message: str,
        run_directory: Path,
        failure_artifact_path: Path | None,
        failure_artifact_kind: FailureArtifactKind | None,
        recording_errors: tuple[str, ...] = (),
    ) -> None:
        super().__init__(message)
        self.run_directory = run_directory
        self.failure_artifact_path = failure_artifact_path
        self.failure_artifact_kind = failure_artifact_kind
        self.recording_errors = recording_errors

    @property
    def manifest_path(self) -> Path | None:
        """Return the failure-manifest path only when a full manifest was validated."""

        if self.failure_artifact_kind == "failure_manifest":
            return self.failure_artifact_path
        return None


_PERF_COUNTER_METHOD = "time.perf_counter monotonic wall-clock difference"
_PEAK_MEMORY_METHOD = (
    "tracemalloc peak traced Python allocations; excludes total process RSS and system RAM"
)
_ARTIFACT_COUNT_METHOD = "derived from hash-stable retained run files"
_ARTIFACT_BYTES_METHOD = "derived from serialized sizes of hash-stable retained run files"


def _basis(
    status: Literal["measured", "derived", "observed_zero", "unavailable"],
    method: str,
    *,
    reason: str | None = None,
) -> ResourceMeasurementBasis:
    return ResourceMeasurementBasis(status=status, method=method, reason=reason)


def _initial_budget(run_id: str, started_at: datetime) -> ResourceBudget:
    """Create the open Milestone 0 interval with truthful per-field measurement bases."""

    unused_method = "observed absence in the Milestone 0 engineering smoke path"
    return ResourceBudget(
        run_id=run_id,
        interval_kind="run",
        interval_start=started_at,
        interval_end=None,
        external_language_tokens=0,
        self_generated_language_tokens=0,
        sensor_observations=0,
        sensor_bytes=0,
        environment_steps=0,
        optimisation_steps=0,
        forward_passes=0,
        backward_passes=0,
        elapsed_compute_seconds=0.0,
        peak_memory_bytes=None,
        stored_artifact_count=0,
        stored_artifact_bytes=0,
        measurement_basis={
            "external_language_tokens": _basis("observed_zero", unused_method),
            "self_generated_language_tokens": _basis("observed_zero", unused_method),
            "sensor_observations": _basis("observed_zero", unused_method),
            "sensor_bytes": _basis("observed_zero", unused_method),
            "environment_steps": _basis("observed_zero", unused_method),
            "optimisation_steps": _basis("observed_zero", unused_method),
            "forward_passes": _basis(
                "measured", "counted at each tiny fixture model forward invocation"
            ),
            "backward_passes": _basis("observed_zero", unused_method),
            "elapsed_compute_seconds": _basis("measured", _PERF_COUNTER_METHOD),
            "peak_memory_bytes": _basis(
                "unavailable",
                _PEAK_MEMORY_METHOD,
                reason="tracemalloc measurement has not started",
            ),
            "stored_artifact_count": _basis("derived", _ARTIFACT_COUNT_METHOD),
            "stored_artifact_bytes": _basis("derived", _ARTIFACT_BYTES_METHOD),
        },
    )


def _validated_budget_update(budget: ResourceBudget, **updates: object) -> ResourceBudget:
    data = budget.model_dump()
    data.update(updates)
    return ResourceBudget.model_validate(data)


def _load_and_run_fixture(config: ResolvedSmokeConfig) -> ToyModelOutput:
    raw = json.loads(config.model.fixture_path.read_text(encoding="utf-8"))
    fixture = TinyLinearFixture.model_validate(raw)
    generator = seed_everything(config.run.seed)
    model_input = [round(generator.uniform(-1.0, 1.0), 10) for _ in range(fixture.input_size)]
    model_output = [
        round(
            sum(weight * value for weight, value in zip(row, model_input, strict=True)) + bias, 10
        )
        for row, bias in zip(fixture.weights, fixture.bias, strict=True)
    ]
    return ToyModelOutput(
        fixture_seed=fixture.seed,
        declared_run_seed=config.run.seed,
        fixture_sha256=config.model.fixture_sha256,
        input=model_input,
        output=model_output,
    )


def _write_budget_with_stable_size(
    path: Path,
    budget: ResourceBudget,
    stable_paths: list[Path],
) -> ResourceBudget:
    """Include the ledger's own byte size without including the self-referential manifest."""

    existing_paths = [item for item in stable_paths if item.is_file()]
    count = len(existing_paths) + 1
    stored_bytes = sum(item.stat().st_size for item in existing_paths)
    candidate = _validated_budget_update(
        budget,
        stored_artifact_count=count,
        stored_artifact_bytes=stored_bytes,
    )
    for _ in range(10):
        write_json(path, candidate)
        observed_bytes = sum(item.stat().st_size for item in existing_paths) + path.stat().st_size
        if observed_bytes == candidate.stored_artifact_bytes:
            return candidate
        candidate = _validated_budget_update(candidate, stored_artifact_bytes=observed_bytes)
    raise RuntimeError("Resource-budget artifact size did not reach a stable value")


def _relative_artifacts(run_directory: Path, paths: list[Path]) -> list[ArtifactRecord]:
    return [artifact_record(run_directory, path) for path in paths if path.is_file()]


def _best_effort_artifacts(
    run_directory: Path,
    paths: list[Path],
    recording_errors: list[str],
) -> list[ArtifactRecord]:
    records: list[ArtifactRecord] = []
    for path in paths:
        if not path.is_file():
            continue
        try:
            records.append(artifact_record(run_directory, path))
        except Exception as exc:
            recording_errors.append(
                f"artifact accounting for {path.name}: {type(exc).__name__}: {exc}"
            )
    return records


def _manifest(
    *,
    config: ResolvedSmokeConfig,
    run_id: str,
    git: GitState,
    package_versions: dict[str, str],
    platform: PlatformInformation,
    started_at: datetime,
    ended_at: datetime | None,
    end_status: Literal["RUNNING", "COMPLETED", "FAILED"],
    failure_reason: str | None,
    budget: ResourceBudget,
    gate_metadata: Phase1GateMetadata,
    artifacts: list[ArtifactRecord],
) -> RunManifest:
    # Keeping this helper keyword-only avoids duplicating the complete manifest contract across
    # start, success, and failure paths.
    return RunManifest.model_validate(
        {
            "run_id": run_id,
            "git": git,
            "resolved_configuration": config,
            "package_versions": package_versions,
            "platform": platform,
            "declared_random_seed": config.run.seed,
            "model_fixture_sha256": config.model.fixture_sha256,
            "started_at": started_at,
            "ended_at": ended_at,
            "end_status": end_status,
            "failure_reason": failure_reason,
            "resolved_configuration_path": RESOLVED_CONFIG_FILENAME,
            "resource_budget_path": BUDGET_FILENAME,
            "phase1_gate_metadata_path": GATE_METADATA_FILENAME,
            "structured_log_path": LOG_FILENAME,
            "artifacts": artifacts,
            "resource_budget": budget,
            "phase1_gate_metadata": gate_metadata,
        }
    )


def _snapshot_budget(
    budget: ResourceBudget,
    *,
    start_tick: float,
    forward_passes: int,
    interval_end: datetime | None,
) -> ResourceBudget:
    elapsed = time.perf_counter() - start_tick
    previous_elapsed = budget.elapsed_compute_seconds or 0.0
    previous_forward_passes = budget.forward_passes or 0
    measurement_basis = dict(budget.measurement_basis)
    peak_memory_bytes = budget.peak_memory_bytes
    if tracemalloc.is_tracing():
        observed_peak = tracemalloc.get_traced_memory()[1]
        peak_memory_bytes = max(peak_memory_bytes or 0, observed_peak)
        measurement_basis["peak_memory_bytes"] = _basis("measured", _PEAK_MEMORY_METHOD)
    elif measurement_basis["peak_memory_bytes"].status != "measured":
        peak_memory_bytes = None
        measurement_basis["peak_memory_bytes"] = _basis(
            "unavailable",
            _PEAK_MEMORY_METHOD,
            reason="tracemalloc was not active for this interval",
        )
    return _validated_budget_update(
        budget,
        interval_end=interval_end,
        forward_passes=max(previous_forward_passes, forward_passes),
        elapsed_compute_seconds=max(previous_elapsed, elapsed),
        peak_memory_bytes=peak_memory_bytes,
        measurement_basis=measurement_basis,
    )


def _terminal_budget_after_accounting_failure(
    budget: ResourceBudget,
    *,
    ended_at: datetime,
    accounting_error: Exception,
) -> ResourceBudget:
    """Close an interval without pretending failed measurements are available."""

    reason = (
        f"measurement finalisation failed: {type(accounting_error).__name__}: {accounting_error}"
    )
    measurement_basis = dict(budget.measurement_basis)
    measurement_basis["elapsed_compute_seconds"] = _basis(
        "unavailable", _PERF_COUNTER_METHOD, reason=reason
    )
    measurement_basis["peak_memory_bytes"] = _basis(
        "unavailable", _PEAK_MEMORY_METHOD, reason=reason
    )
    return _validated_budget_update(
        budget,
        interval_end=ended_at,
        elapsed_compute_seconds=None,
        peak_memory_bytes=None,
        measurement_basis=measurement_basis,
    )


def _ensure_initial_artifacts(
    *,
    resolved_path: Path,
    config: ResolvedSmokeConfig,
    gate_path: Path,
    gate_metadata: Phase1GateMetadata,
) -> None:
    if not resolved_path.is_file():
        write_json(resolved_path, config)
    if not gate_path.is_file():
        write_json(gate_path, gate_metadata)


def _restore_initial_artifacts_best_effort(
    *,
    resolved_path: Path,
    config: ResolvedSmokeConfig,
    gate_path: Path,
    gate_metadata: Phase1GateMetadata,
    recording_errors: list[str],
) -> None:
    for label, path, value in (
        ("resolved configuration", resolved_path, config),
        ("gate metadata", gate_path, gate_metadata),
    ):
        if path.is_file():
            continue
        try:
            write_json(path, value)
        except Exception as exc:
            recording_errors.append(f"{label} recovery: {type(exc).__name__}: {exc}")


def _last_manifest_state(
    manifest_path: Path,
    recording_errors: list[str],
) -> tuple[str | None, Literal["RUNNING", "COMPLETED", "FAILED"] | None]:
    if not manifest_path.is_file():
        return None, None
    try:
        manifest = RunManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        recording_errors.append(f"prior manifest validation: {type(exc).__name__}: {exc}")
        return MANIFEST_FILENAME, None
    return MANIFEST_FILENAME, manifest.end_status


def _record_full_failure(
    *,
    config: ResolvedSmokeConfig,
    run_id: str,
    run_directory: Path,
    git: GitState,
    package_versions: dict[str, str],
    platform: PlatformInformation,
    started_at: datetime,
    ended_at: datetime,
    reason: str,
    budget: ResourceBudget,
    gate_metadata: Phase1GateMetadata,
    resolved_path: Path,
    gate_path: Path,
    budget_path: Path,
    toy_path: Path,
    log_path: Path,
    manifest_path: Path,
    recording_errors: list[str],
) -> Path:
    _ensure_initial_artifacts(
        resolved_path=resolved_path,
        config=config,
        gate_path=gate_path,
        gate_metadata=gate_metadata,
    )
    stable_paths = [resolved_path, gate_path, toy_path, log_path]
    budget = _write_budget_with_stable_size(budget_path, budget, stable_paths)
    artifact_paths = [*stable_paths, budget_path]
    failed_manifest = _manifest(
        config=config,
        run_id=run_id,
        git=git,
        package_versions=package_versions,
        platform=platform,
        started_at=started_at,
        ended_at=ended_at,
        end_status="FAILED",
        failure_reason=reason,
        budget=budget,
        gate_metadata=gate_metadata,
        artifacts=_relative_artifacts(run_directory, artifact_paths),
    )
    write_error: Exception | None = None
    try:
        write_json(manifest_path, failed_manifest)
    except Exception as exc:
        write_error = exc
    try:
        restored = RunManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    except Exception as validation_error:
        if write_error is not None:
            raise write_error from validation_error
        raise
    if restored.end_status != "FAILED" or restored.failure_reason != reason:
        raise RuntimeError("Failure manifest did not preserve the original failure reason")
    if write_error is not None:
        recording_errors.append(
            f"failure manifest writer raised after producing valid output: "
            f"{type(write_error).__name__}: {write_error}"
        )
    return manifest_path


def _record_bootstrap_failure(
    *,
    config: ResolvedSmokeConfig,
    run_id: str,
    run_directory: Path,
    git: GitState,
    package_versions: dict[str, str],
    platform: PlatformInformation,
    run_declared_started: bool,
    failure_stage: str,
    original_exception: Exception,
    reason: str,
    started_at: datetime,
    ended_at: datetime,
    budget: ResourceBudget,
    gate_metadata: Phase1GateMetadata,
    resolved_path: Path,
    gate_path: Path,
    budget_path: Path,
    toy_path: Path,
    log_path: Path,
    manifest_path: Path,
    bootstrap_path: Path,
    recording_errors: list[str],
) -> Path | None:
    _restore_initial_artifacts_best_effort(
        resolved_path=resolved_path,
        config=config,
        gate_path=gate_path,
        gate_metadata=gate_metadata,
        recording_errors=recording_errors,
    )
    stable_paths = [resolved_path, gate_path, toy_path, log_path]
    try:
        budget = _write_budget_with_stable_size(budget_path, budget, stable_paths)
    except Exception as exc:
        recording_errors.append(f"resource budget recovery: {type(exc).__name__}: {exc}")
    artifact_paths = [*stable_paths, budget_path]
    artifacts = _best_effort_artifacts(run_directory, artifact_paths, recording_errors)
    last_manifest_path, last_manifest_status = _last_manifest_state(manifest_path, recording_errors)
    record = BootstrapFailureRecord(
        run_id=run_id,
        run_declared_started=run_declared_started,
        failure_stage=failure_stage,
        original_exception_type=type(original_exception).__name__,
        original_failure_reason=reason,
        started_at=started_at,
        ended_at=ended_at,
        recorded_at=utc_now(),
        git=git,
        resolved_configuration=config,
        package_versions=package_versions,
        platform=platform,
        declared_random_seed=config.run.seed,
        resource_budget=budget,
        artifacts=artifacts,
        last_manifest_path=last_manifest_path,
        last_manifest_status=last_manifest_status,
        recording_errors=list(recording_errors),
    )
    write_error: Exception | None = None
    try:
        write_json(bootstrap_path, record)
    except Exception as exc:
        write_error = exc
    try:
        restored = BootstrapFailureRecord.model_validate_json(
            bootstrap_path.read_text(encoding="utf-8")
        )
    except Exception as validation_error:
        if write_error is not None:
            recording_errors.append(
                f"bootstrap failure record writing: {type(write_error).__name__}: {write_error}"
            )
        recording_errors.append(
            "bootstrap failure record validation: "
            f"{type(validation_error).__name__}: {validation_error}"
        )
        return None
    if restored.original_failure_reason != reason:
        recording_errors.append("bootstrap failure record did not preserve the original reason")
        return None
    if write_error is not None:
        recording_errors.append(
            f"bootstrap record writer raised after producing valid output: "
            f"{type(write_error).__name__}: {write_error}"
        )
    return bootstrap_path


def _close_logging_best_effort(
    logger: logging.Logger | None,
    recording_errors: list[str],
) -> None:
    if logger is None:
        return
    try:
        close_logging(logger)
    except Exception as exc:
        recording_errors.append(f"logging shutdown: {type(exc).__name__}: {exc}")


def run_smoke(config: ResolvedSmokeConfig, *, run_id: str | None = None) -> SmokeResult:
    """Execute one complete, offline, CPU-only engineering smoke run."""

    resolved_run_id = create_run_id(config.run.name) if run_id is None else run_id

    # Provenance capture is a preflight: no run directory exists and no run is declared started if
    # any of these operations fail.
    git = capture_git_state(config.repository_root)
    package_versions = collect_package_versions()
    platform = collect_platform_information()

    started_at = utc_now()
    start_tick = time.perf_counter()
    gate_metadata = Phase1GateMetadata()
    budget = _initial_budget(resolved_run_id, started_at)
    run_directory = config.run.output_root / resolved_run_id
    resolved_path = run_directory / RESOLVED_CONFIG_FILENAME
    gate_path = run_directory / GATE_METADATA_FILENAME
    budget_path = run_directory / BUDGET_FILENAME
    toy_path = run_directory / TOY_OUTPUT_FILENAME
    log_path = run_directory / LOG_FILENAME
    manifest_path = run_directory / MANIFEST_FILENAME
    bootstrap_path = run_directory / BOOTSTRAP_FAILURE_FILENAME

    logger: logging.Logger | None = None
    tracing_was_active = tracemalloc.is_tracing()
    tracing_started_here = False
    run_declared_started = False
    forward_passes = 0
    failure_stage = "logging_setup"

    run_directory.mkdir(parents=True, exist_ok=False)
    try:
        logger = configure_logging(log_path, config.logging.level)

        failure_stage = "resource_tracking_setup"
        if tracing_was_active:
            tracemalloc.stop()
        tracemalloc.start()
        tracing_started_here = True

        failure_stage = "initial_artifact_writes"
        budget = _snapshot_budget(
            budget,
            start_tick=start_tick,
            forward_passes=forward_passes,
            interval_end=None,
        )
        write_json(resolved_path, config)
        write_json(gate_path, gate_metadata)
        write_json(budget_path, budget)

        failure_stage = "initial_manifest_construction"
        initial_manifest = _manifest(
            config=config,
            run_id=resolved_run_id,
            git=git,
            package_versions=package_versions,
            platform=platform,
            started_at=started_at,
            ended_at=None,
            end_status="RUNNING",
            failure_reason=None,
            budget=budget,
            gate_metadata=gate_metadata,
            artifacts=_relative_artifacts(run_directory, [resolved_path, gate_path, budget_path]),
        )
        failure_stage = "initial_manifest_write"
        write_json(manifest_path, initial_manifest)
        RunManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
        run_declared_started = True

        failure_stage = "start_log_write"
        logger.info(
            "Milestone 0 smoke run started",
            extra={"event": "smoke_started", "run_id": resolved_run_id},
        )

        failure_stage = "fixture_execution"
        toy_output = _load_and_run_fixture(config)
        forward_passes = 1
        failure_stage = "toy_artifact_write"
        write_json(toy_path, toy_output)
        logger.info(
            "Tiny local fixture forward pass completed",
            extra={
                "event": "fixture_forward_completed",
                "run_id": resolved_run_id,
                "device": "cpu",
            },
        )

        failure_stage = "success_resource_accounting"
        ended_at = utc_now()
        budget = _snapshot_budget(
            budget,
            start_tick=start_tick,
            forward_passes=forward_passes,
            interval_end=ended_at,
        )
        if tracing_started_here and tracemalloc.is_tracing():
            tracemalloc.stop()
            tracing_started_here = False
        logger.info(
            "Milestone 0 smoke run completed",
            extra={"event": "smoke_completed", "run_id": resolved_run_id},
        )
        close_logging(logger)

        failure_stage = "success_artifact_finalization"
        stable_paths = [resolved_path, gate_path, toy_path, log_path]
        budget = _write_budget_with_stable_size(budget_path, budget, stable_paths)
        artifact_paths = [*stable_paths, budget_path]
        final_manifest = _manifest(
            config=config,
            run_id=resolved_run_id,
            git=git,
            package_versions=package_versions,
            platform=platform,
            started_at=started_at,
            ended_at=ended_at,
            end_status="COMPLETED",
            failure_reason=None,
            budget=budget,
            gate_metadata=gate_metadata,
            artifacts=_relative_artifacts(run_directory, artifact_paths),
        )
        write_json(manifest_path, final_manifest)
        restored_manifest = RunManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
        if restored_manifest.end_status != "COMPLETED":
            raise RuntimeError("Final smoke manifest is not complete")
        return SmokeResult(
            run_id=resolved_run_id,
            run_directory=run_directory,
            manifest_path=manifest_path,
            toy_output=toy_output,
        )
    except Exception as exc:
        reason = f"{type(exc).__name__}: {exc}"
        recording_errors: list[str] = []
        ended_at = utc_now()
        if not run_declared_started and failure_stage == "initial_manifest_write":
            try:
                interrupted_manifest = RunManifest.model_validate_json(
                    manifest_path.read_text(encoding="utf-8")
                )
                run_declared_started = interrupted_manifest.end_status == "RUNNING"
            except Exception as status_error:
                recording_errors.append(
                    "interrupted initial manifest validation: "
                    f"{type(status_error).__name__}: {status_error}"
                )
        try:
            budget = _snapshot_budget(
                budget,
                start_tick=start_tick,
                forward_passes=forward_passes,
                interval_end=ended_at,
            )
        except Exception as accounting_error:
            recording_errors.append(
                "failure resource accounting: "
                f"{type(accounting_error).__name__}: {accounting_error}"
            )
            try:
                budget = _terminal_budget_after_accounting_failure(
                    budget,
                    ended_at=ended_at,
                    accounting_error=accounting_error,
                )
            except Exception as fallback_error:
                recording_errors.append(
                    "failure resource-accounting fallback: "
                    f"{type(fallback_error).__name__}: {fallback_error}"
                )
        if logger is not None:
            try:
                logger.error(
                    "Milestone 0 smoke run failed",
                    extra={"event": "smoke_failed", "run_id": resolved_run_id},
                    exc_info=(type(exc), exc, exc.__traceback__),
                )
            except Exception as logging_error:
                recording_errors.append(
                    f"failure log writing: {type(logging_error).__name__}: {logging_error}"
                )
        _close_logging_best_effort(logger, recording_errors)

        failure_artifact_path: Path | None = None
        failure_artifact_kind: FailureArtifactKind | None = None
        if run_declared_started:
            try:
                failure_artifact_path = _record_full_failure(
                    config=config,
                    run_id=resolved_run_id,
                    run_directory=run_directory,
                    git=git,
                    package_versions=package_versions,
                    platform=platform,
                    started_at=started_at,
                    ended_at=ended_at,
                    reason=reason,
                    budget=budget,
                    gate_metadata=gate_metadata,
                    resolved_path=resolved_path,
                    gate_path=gate_path,
                    budget_path=budget_path,
                    toy_path=toy_path,
                    log_path=log_path,
                    manifest_path=manifest_path,
                    recording_errors=recording_errors,
                )
                failure_artifact_kind = "failure_manifest"
            except Exception as recording_error:
                recording_errors.append(
                    "failure manifest recording: "
                    f"{type(recording_error).__name__}: {recording_error}"
                )

        if failure_artifact_path is None:
            try:
                failure_artifact_path = _record_bootstrap_failure(
                    config=config,
                    run_id=resolved_run_id,
                    run_directory=run_directory,
                    git=git,
                    package_versions=package_versions,
                    platform=platform,
                    run_declared_started=run_declared_started,
                    failure_stage=failure_stage,
                    original_exception=exc,
                    reason=reason,
                    started_at=started_at,
                    ended_at=ended_at,
                    budget=budget,
                    gate_metadata=gate_metadata,
                    resolved_path=resolved_path,
                    gate_path=gate_path,
                    budget_path=budget_path,
                    toy_path=toy_path,
                    log_path=log_path,
                    manifest_path=manifest_path,
                    bootstrap_path=bootstrap_path,
                    recording_errors=recording_errors,
                )
            except Exception as recording_error:
                recording_errors.append(
                    "bootstrap failure recording: "
                    f"{type(recording_error).__name__}: {recording_error}"
                )
            if failure_artifact_path is not None:
                failure_artifact_kind = "bootstrap_failure"

        raise SmokeRunError(
            reason,
            run_directory,
            failure_artifact_path,
            failure_artifact_kind,
            tuple(recording_errors),
        ) from exc
    finally:
        try:
            if tracing_started_here and tracemalloc.is_tracing():
                tracemalloc.stop()
            if tracing_was_active and not tracemalloc.is_tracing():
                tracemalloc.start()
        except Exception:
            # Process-global tracing cleanup must not replace the original run outcome.
            pass
        if logger is not None and logger.handlers:
            # Cleanup is intentionally non-raising so it cannot replace the original run outcome.
            with suppress(Exception):
                close_logging(logger)
