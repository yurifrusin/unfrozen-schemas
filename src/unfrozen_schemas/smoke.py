"""Offline CPU smoke execution for the Milestone 0 foundation."""

from __future__ import annotations

import json
import time
import tracemalloc
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from unfrozen_schemas.budgets import ResourceBudget
from unfrozen_schemas.config import ResolvedSmokeConfig
from unfrozen_schemas.constants import (
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
    Phase1GateMetadata,
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
    """Raised after a failed run has been cleanly recorded."""

    def __init__(self, message: str, run_directory: Path, manifest_path: Path) -> None:
        super().__init__(message)
        self.run_directory = run_directory
        self.manifest_path = manifest_path


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
    candidate = budget.model_copy(
        update={"stored_artifact_count": count, "stored_artifact_bytes": stored_bytes}
    )
    for _ in range(10):
        write_json(path, candidate)
        observed_bytes = sum(item.stat().st_size for item in existing_paths) + path.stat().st_size
        if observed_bytes == candidate.stored_artifact_bytes:
            return candidate
        candidate = candidate.model_copy(update={"stored_artifact_bytes": observed_bytes})
    raise RuntimeError("Resource-budget artifact size did not reach a stable value")


def _relative_artifacts(run_directory: Path, paths: list[Path]) -> list[ArtifactRecord]:
    return [artifact_record(run_directory, path) for path in paths if path.is_file()]


def _manifest(
    *,
    config: ResolvedSmokeConfig,
    run_id: str,
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
            "git": capture_git_state(config.repository_root),
            "resolved_configuration": config,
            "package_versions": collect_package_versions(),
            "platform": collect_platform_information(),
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


def run_smoke(config: ResolvedSmokeConfig, *, run_id: str | None = None) -> SmokeResult:
    """Execute one complete, offline, CPU-only engineering smoke run."""

    resolved_run_id = create_run_id(config.run.name) if run_id is None else run_id
    run_directory = config.run.output_root / resolved_run_id
    run_directory.mkdir(parents=True, exist_ok=False)

    resolved_path = run_directory / RESOLVED_CONFIG_FILENAME
    gate_path = run_directory / GATE_METADATA_FILENAME
    budget_path = run_directory / BUDGET_FILENAME
    toy_path = run_directory / TOY_OUTPUT_FILENAME
    log_path = run_directory / LOG_FILENAME
    manifest_path = run_directory / MANIFEST_FILENAME

    started_at = utc_now()
    start_tick = time.perf_counter()
    gate_metadata = Phase1GateMetadata()
    budget = ResourceBudget(run_id=resolved_run_id)
    logger = configure_logging(log_path, config.logging.level)
    tracing_was_active = tracemalloc.is_tracing()
    if tracing_was_active:
        tracemalloc.stop()
    tracemalloc.start()

    write_json(resolved_path, config)
    write_json(gate_path, gate_metadata)
    write_json(budget_path, budget)
    logger.info(
        "Milestone 0 smoke run started",
        extra={"event": "smoke_started", "run_id": resolved_run_id},
    )
    initial_manifest = _manifest(
        config=config,
        run_id=resolved_run_id,
        started_at=started_at,
        ended_at=None,
        end_status="RUNNING",
        failure_reason=None,
        budget=budget,
        gate_metadata=gate_metadata,
        artifacts=_relative_artifacts(run_directory, [resolved_path, gate_path, budget_path]),
    )
    write_json(manifest_path, initial_manifest)

    forward_passes = 0
    try:
        toy_output = _load_and_run_fixture(config)
        forward_passes = 1
        write_json(toy_path, toy_output)
        logger.info(
            "Tiny local fixture forward pass completed",
            extra={
                "event": "fixture_forward_completed",
                "run_id": resolved_run_id,
                "device": "cpu",
            },
        )
        elapsed_seconds = time.perf_counter() - start_tick
        peak_memory = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        logger.info(
            "Milestone 0 smoke run completed",
            extra={"event": "smoke_completed", "run_id": resolved_run_id},
        )
        close_logging(logger)

        budget = budget.model_copy(
            update={
                "forward_passes": forward_passes,
                "elapsed_compute_seconds": elapsed_seconds,
                "peak_memory_bytes": peak_memory,
            }
        )
        stable_paths = [resolved_path, gate_path, toy_path, log_path]
        budget = _write_budget_with_stable_size(budget_path, budget, stable_paths)
        artifact_paths = [*stable_paths, budget_path]
        final_manifest = _manifest(
            config=config,
            run_id=resolved_run_id,
            started_at=started_at,
            ended_at=utc_now(),
            end_status="COMPLETED",
            failure_reason=None,
            budget=budget,
            gate_metadata=gate_metadata,
            artifacts=_relative_artifacts(run_directory, artifact_paths),
        )
        write_json(manifest_path, final_manifest)
        return SmokeResult(
            run_id=resolved_run_id,
            run_directory=run_directory,
            manifest_path=manifest_path,
            toy_output=toy_output,
        )
    except Exception as exc:
        elapsed_seconds = time.perf_counter() - start_tick
        peak_memory = tracemalloc.get_traced_memory()[1] if tracemalloc.is_tracing() else 0
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        logger.exception(
            "Milestone 0 smoke run failed",
            extra={"event": "smoke_failed", "run_id": resolved_run_id},
        )
        close_logging(logger)
        reason = f"{type(exc).__name__}: {exc}"
        budget = budget.model_copy(
            update={
                "forward_passes": forward_passes,
                "elapsed_compute_seconds": elapsed_seconds,
                "peak_memory_bytes": peak_memory,
            }
        )
        stable_paths = [resolved_path, gate_path, toy_path, log_path]
        budget = _write_budget_with_stable_size(budget_path, budget, stable_paths)
        artifact_paths = [path for path in [*stable_paths, budget_path] if path.is_file()]
        failed_manifest = _manifest(
            config=config,
            run_id=resolved_run_id,
            started_at=started_at,
            ended_at=utc_now(),
            end_status="FAILED",
            failure_reason=reason,
            budget=budget,
            gate_metadata=gate_metadata,
            artifacts=_relative_artifacts(run_directory, artifact_paths),
        )
        write_json(manifest_path, failed_manifest)
        raise SmokeRunError(reason, run_directory, manifest_path) from exc
    finally:
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        if tracing_was_active:
            tracemalloc.start()
        if logger.handlers:
            close_logging(logger)
