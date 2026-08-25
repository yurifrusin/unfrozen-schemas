"""Failure-path preservation tests for the smoke runner."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

import unfrozen_schemas.smoke as smoke_module
from unfrozen_schemas.budgets import ResourceBudget
from unfrozen_schemas.config import ResolvedSmokeConfig, load_smoke_config
from unfrozen_schemas.constants import (
    BOOTSTRAP_FAILURE_FILENAME,
    BUDGET_FILENAME,
    GATE_METADATA_FILENAME,
    MANIFEST_FILENAME,
    RESOLVED_CONFIG_FILENAME,
)
from unfrozen_schemas.provenance import (
    ArtifactRecord,
    BootstrapFailureRecord,
    GitState,
    RunManifest,
    write_json,
)
from unfrozen_schemas.smoke import SmokeRunError, run_smoke


def _resolved_config(tmp_path: Path) -> ResolvedSmokeConfig:
    return load_smoke_config(Path("configs/experiment/smoke.yaml"), output_root_override=tmp_path)


def test_failed_started_smoke_run_records_complete_failure_manifest(tmp_path: Path) -> None:
    resolved = _resolved_config(tmp_path)
    missing_model = resolved.model.model_copy(update={"fixture_path": tmp_path / "missing.json"})
    failing_config = resolved.model_copy(update={"model": missing_model})

    with pytest.raises(SmokeRunError) as captured:
        run_smoke(failing_config, run_id="failure-reporting-test")

    run_directory = captured.value.run_directory
    manifest_path = run_directory / MANIFEST_FILENAME
    manifest = RunManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))

    assert captured.value.failure_artifact_kind == "failure_manifest"
    assert captured.value.failure_artifact_path == manifest_path
    assert captured.value.manifest_path == manifest_path
    assert manifest.start_status == "STARTED"
    assert manifest.end_status == "FAILED"
    assert manifest.ended_at is not None
    assert manifest.resource_budget.interval_start == manifest.started_at
    assert manifest.resource_budget.interval_end == manifest.ended_at
    assert manifest.failure_reason is not None
    assert "FileNotFoundError" in manifest.failure_reason
    assert manifest.phase1_gate_metadata.permits_phase2_scientific_work is False
    assert (run_directory / RESOLVED_CONFIG_FILENAME).is_file()
    assert (run_directory / BUDGET_FILENAME).is_file()
    assert (run_directory / GATE_METADATA_FILENAME).is_file()


def test_started_run_budget_finalisation_failure_preserves_original_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    resolved = _resolved_config(tmp_path)
    missing_model = resolved.model.model_copy(update={"fixture_path": tmp_path / "missing.json"})
    failing_config = resolved.model_copy(update={"model": missing_model})
    original_snapshot = smoke_module._snapshot_budget
    snapshot_calls = 0

    def fail_second_budget_snapshot(
        budget: ResourceBudget,
        *,
        start_tick: float,
        forward_passes: int,
        interval_end: datetime | None,
    ) -> ResourceBudget:
        nonlocal snapshot_calls
        snapshot_calls += 1
        if snapshot_calls == 2:
            raise OSError("started-run budget finalisation sentinel")
        return original_snapshot(
            budget,
            start_tick=start_tick,
            forward_passes=forward_passes,
            interval_end=interval_end,
        )

    monkeypatch.setattr(smoke_module, "_snapshot_budget", fail_second_budget_snapshot)

    with pytest.raises(SmokeRunError) as captured:
        run_smoke(failing_config, run_id="started-budget-finalisation-failure-test")

    error = captured.value
    assert "FileNotFoundError" in str(error)
    assert isinstance(error.__cause__, FileNotFoundError)
    assert error.failure_artifact_kind == "failure_manifest"
    assert error.failure_artifact_path is not None
    manifest = RunManifest.model_validate_json(
        error.failure_artifact_path.read_text(encoding="utf-8")
    )
    assert manifest.failure_reason == str(error)
    assert manifest.resource_budget.interval_end == manifest.ended_at
    assert manifest.resource_budget.elapsed_compute_seconds is None
    elapsed_basis = manifest.resource_budget.measurement_basis["elapsed_compute_seconds"]
    assert elapsed_basis.status == "unavailable"
    assert elapsed_basis.reason is not None
    assert "started-run budget finalisation sentinel" in elapsed_basis.reason


def test_one_shot_initial_artifact_write_failure_records_bootstrap_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    resolved = _resolved_config(tmp_path)
    failure_injected = False

    def fail_first_resolved_write(path: Path, value: BaseModel | Mapping[str, Any]) -> None:
        nonlocal failure_injected
        if path.name == RESOLVED_CONFIG_FILENAME and not failure_injected:
            failure_injected = True
            raise OSError("one-shot initial artifact failure")
        write_json(path, value)

    monkeypatch.setattr(smoke_module, "write_json", fail_first_resolved_write)

    with pytest.raises(SmokeRunError) as captured:
        run_smoke(resolved, run_id="initial-artifact-failure-test")

    error = captured.value
    bootstrap_path = error.run_directory / BOOTSTRAP_FAILURE_FILENAME
    record = BootstrapFailureRecord.model_validate_json(bootstrap_path.read_text(encoding="utf-8"))

    assert failure_injected is True
    assert error.failure_artifact_kind == "bootstrap_failure"
    assert error.failure_artifact_path == bootstrap_path
    assert error.manifest_path is None
    assert record.run_declared_started is False
    assert record.failure_stage == "initial_artifact_writes"
    assert record.original_exception_type == "OSError"
    assert "one-shot initial artifact failure" in record.original_failure_reason
    assert record.resource_budget.interval_start == record.started_at
    assert record.resource_budget.interval_end == record.ended_at
    elapsed = record.resource_budget.elapsed_compute_seconds
    assert elapsed is not None
    assert elapsed > 0
    assert (error.run_directory / RESOLVED_CONFIG_FILENAME).is_file()
    assert (error.run_directory / GATE_METADATA_FILENAME).is_file()
    assert (error.run_directory / BUDGET_FILENAME).is_file()


def test_logging_setup_failure_records_valid_bootstrap_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    resolved = _resolved_config(tmp_path)

    def fail_logging_setup(_path: Path, _level: str) -> logging.Logger:
        raise PermissionError("logging bootstrap denied")

    monkeypatch.setattr(smoke_module, "configure_logging", fail_logging_setup)

    with pytest.raises(SmokeRunError) as captured:
        run_smoke(resolved, run_id="logging-bootstrap-failure-test")

    error = captured.value
    assert error.failure_artifact_kind == "bootstrap_failure"
    assert error.failure_artifact_path is not None
    record = BootstrapFailureRecord.model_validate_json(
        error.failure_artifact_path.read_text(encoding="utf-8")
    )
    assert record.failure_stage == "logging_setup"
    assert record.run_declared_started is False
    assert record.original_exception_type == "PermissionError"
    assert record.original_failure_reason == "PermissionError: logging bootstrap denied"
    assert record.resource_budget.interval_end == record.ended_at
    assert record.resource_budget.peak_memory_bytes is None
    peak_basis = record.resource_budget.measurement_basis["peak_memory_bytes"]
    assert peak_basis.status == "unavailable"
    assert peak_basis.reason is not None


def test_budget_finalisation_failure_preserves_original_bootstrap_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    resolved = _resolved_config(tmp_path)

    def fail_logging_setup(_path: Path, _level: str) -> logging.Logger:
        raise PermissionError("original failure before resource tracking")

    def fail_budget_snapshot(_budget: object, **_kwargs: object) -> None:
        raise OSError("budget finalisation sentinel")

    monkeypatch.setattr(smoke_module, "configure_logging", fail_logging_setup)
    monkeypatch.setattr(smoke_module, "_snapshot_budget", fail_budget_snapshot)

    with pytest.raises(SmokeRunError) as captured:
        run_smoke(resolved, run_id="budget-finalisation-failure-test")

    error = captured.value
    assert str(error) == "PermissionError: original failure before resource tracking"
    assert isinstance(error.__cause__, PermissionError)
    assert error.failure_artifact_kind == "bootstrap_failure"
    assert error.failure_artifact_path is not None
    record = BootstrapFailureRecord.model_validate_json(
        error.failure_artifact_path.read_text(encoding="utf-8")
    )
    assert record.original_failure_reason == str(error)
    assert record.resource_budget.interval_end == record.ended_at
    assert record.resource_budget.elapsed_compute_seconds is None
    elapsed_basis = record.resource_budget.measurement_basis["elapsed_compute_seconds"]
    assert elapsed_basis.status == "unavailable"
    assert elapsed_basis.reason is not None
    assert "budget finalisation sentinel" in elapsed_basis.reason
    assert any("budget finalisation sentinel" in item for item in record.recording_errors)


def test_initial_manifest_construction_failure_records_bootstrap_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    resolved = _resolved_config(tmp_path)

    def fail_initial_artifact_accounting(
        _run_directory: Path, _paths: list[Path]
    ) -> list[ArtifactRecord]:
        raise RuntimeError("initial manifest construction sentinel")

    monkeypatch.setattr(smoke_module, "_relative_artifacts", fail_initial_artifact_accounting)

    with pytest.raises(SmokeRunError) as captured:
        run_smoke(resolved, run_id="initial-manifest-failure-test")

    error = captured.value
    assert error.failure_artifact_kind == "bootstrap_failure"
    assert error.failure_artifact_path is not None
    record = BootstrapFailureRecord.model_validate_json(
        error.failure_artifact_path.read_text(encoding="utf-8")
    )
    assert record.failure_stage == "initial_manifest_construction"
    assert record.run_declared_started is False
    assert "initial manifest construction sentinel" in record.original_failure_reason


def test_provenance_preflight_failure_does_not_create_run_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    resolved = _resolved_config(tmp_path)

    def fail_git_preflight(_repository_root: Path) -> GitState:
        raise RuntimeError("provenance preflight sentinel")

    monkeypatch.setattr("unfrozen_schemas.smoke.capture_git_state", fail_git_preflight)

    with pytest.raises(RuntimeError, match="provenance preflight sentinel"):
        run_smoke(resolved, run_id="preflight-failure-test")

    assert list(tmp_path.iterdir()) == []


def test_secondary_recording_failure_does_not_mask_original_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    resolved = _resolved_config(tmp_path)

    def fail_logging_setup(_path: Path, _level: str) -> logging.Logger:
        raise PermissionError("original bootstrap reason")

    def fail_bootstrap_record(**_kwargs: object) -> Path | None:
        raise OSError("secondary recording failure")

    monkeypatch.setattr(smoke_module, "configure_logging", fail_logging_setup)
    monkeypatch.setattr(smoke_module, "_record_bootstrap_failure", fail_bootstrap_record)

    with pytest.raises(SmokeRunError) as captured:
        run_smoke(resolved, run_id="secondary-recording-failure-test")

    error = captured.value
    assert str(error) == "PermissionError: original bootstrap reason"
    assert isinstance(error.__cause__, PermissionError)
    assert error.failure_artifact_path is None
    assert error.failure_artifact_kind is None
    assert any("secondary recording failure" in item for item in error.recording_errors)
