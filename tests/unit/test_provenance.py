"""Determinism, Git provenance, hashing, and serialization tests."""

from __future__ import annotations

import random
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from unfrozen_schemas.budgets import (
    RESOURCE_FIELDS,
    MeasurementStatus,
    ResourceBudget,
    ResourceField,
    ResourceMeasurementBasis,
)
from unfrozen_schemas.provenance import (
    Phase1GateMetadata,
    artifact_record,
    capture_git_state,
    create_run_id,
    seed_everything,
    write_json,
)


def _git(repository: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _complete_measurement_basis() -> dict[ResourceField, ResourceMeasurementBasis]:
    return {
        field: ResourceMeasurementBasis(status="measured", method=f"test measurement for {field}")
        for field in RESOURCE_FIELDS
    }


def _budget_data() -> dict[str, object]:
    started_at = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
    return {
        "run_id": "serialization-test",
        "interval_kind": "run",
        "interval_start": started_at,
        "interval_end": started_at,
        "external_language_tokens": 2,
        "self_generated_language_tokens": 3,
        "sensor_observations": 5,
        "sensor_bytes": 7,
        "environment_steps": 11,
        "optimisation_steps": 13,
        "forward_passes": 17,
        "backward_passes": 19,
        "elapsed_compute_seconds": 0.25,
        "peak_memory_bytes": 23,
        "stored_artifact_count": 1,
        "stored_artifact_bytes": 29,
        "measurement_basis": _complete_measurement_basis(),
    }


def test_seed_handling_is_deterministic_for_global_and_isolated_generators() -> None:
    first_generator = seed_everything(1729)
    first_global = [random.random() for _ in range(3)]
    first_isolated = [first_generator.random() for _ in range(3)]

    second_generator = seed_everything(1729)
    second_global = [random.random() for _ in range(3)]
    second_isolated = [second_generator.random() for _ in range(3)]

    assert first_global == second_global
    assert first_isolated == second_isolated


def test_run_id_is_sortable_and_exactly_reproducible_with_injected_inputs() -> None:
    instant = datetime(2026, 8, 24, 12, 34, 56, tzinfo=UTC)

    run_id = create_run_id("Milestone 0 Smoke", now=instant, nonce="abc")

    assert run_id == "milestone-0-smoke-20260824T123456000000Z-ba7816bf8f"


def test_git_commit_and_dirty_state_capture(tmp_path: Path) -> None:
    repository = tmp_path / "git-repository"
    repository.mkdir()
    _git(repository, "init")
    _git(repository, "config", "user.email", "tests@example.invalid")
    _git(repository, "config", "user.name", "Offline Tests")
    tracked = repository / "tracked.txt"
    tracked.write_text("committed\n", encoding="utf-8")
    _git(repository, "add", "tracked.txt")
    _git(repository, "commit", "-m", "test fixture")

    clean = capture_git_state(repository)
    (repository / "untracked.txt").write_text("dirty\n", encoding="utf-8")
    dirty = capture_git_state(repository)

    assert clean.dirty is False
    assert dirty.dirty is True
    assert clean.commit == dirty.commit


def test_resource_budget_and_gate_metadata_serialize_canonically(tmp_path: Path) -> None:
    budget = ResourceBudget.model_validate(_budget_data())
    gate = Phase1GateMetadata()
    budget_path = tmp_path / "budget.json"
    gate_path = tmp_path / "gate.json"

    write_json(budget_path, budget)
    write_json(gate_path, gate)

    assert ResourceBudget.model_validate_json(budget_path.read_text(encoding="utf-8")) == budget
    assert budget.schema_version == "2"
    restored_gate = Phase1GateMetadata.model_validate_json(gate_path.read_text(encoding="utf-8"))
    assert restored_gate == gate
    assert restored_gate.status == "NOT_EVALUATED"
    assert restored_gate.permits_phase2_scientific_work is False


def test_resource_budget_requires_exact_measurement_coverage() -> None:
    data = _budget_data()
    basis = _complete_measurement_basis()
    del basis["sensor_bytes"]
    data["measurement_basis"] = basis

    with pytest.raises(ValidationError, match="must cover every resource field exactly once"):
        ResourceBudget.model_validate(data)


def test_resource_budget_validates_observed_zero_and_unavailable_values() -> None:
    observed_zero_data = _budget_data()
    observed_zero_basis = _complete_measurement_basis()
    observed_zero_basis["external_language_tokens"] = ResourceMeasurementBasis(
        status="observed_zero", method="test observed absence"
    )
    observed_zero_data["measurement_basis"] = observed_zero_basis
    with pytest.raises(ValidationError, match="must equal zero"):
        ResourceBudget.model_validate(observed_zero_data)

    unavailable_data = _budget_data()
    unavailable_basis = _complete_measurement_basis()
    unavailable_basis["peak_memory_bytes"] = ResourceMeasurementBasis(
        status="unavailable", method="test probe", reason="probe did not start"
    )
    unavailable_data["measurement_basis"] = unavailable_basis
    with pytest.raises(ValidationError, match="must be null"):
        ResourceBudget.model_validate(unavailable_data)

    unavailable_data["peak_memory_bytes"] = None
    assert ResourceBudget.model_validate(unavailable_data).peak_memory_bytes is None

    with pytest.raises(ValidationError, match="requires a reason"):
        ResourceMeasurementBasis(status="unavailable", method="test probe")


@pytest.mark.parametrize("status", ["measured", "derived"])
def test_resource_budget_rejects_null_available_values(status: MeasurementStatus) -> None:
    data = _budget_data()
    basis = _complete_measurement_basis()
    basis["stored_artifact_bytes"] = ResourceMeasurementBasis(
        status=status,
        method="test artifact accounting",
    )
    data["stored_artifact_bytes"] = None
    data["measurement_basis"] = basis

    with pytest.raises(ValidationError, match="cannot be null"):
        ResourceBudget.model_validate(data)


def test_resource_budget_rejects_reversed_or_naive_intervals() -> None:
    reversed_data = _budget_data()
    reversed_data["interval_end"] = datetime(2026, 8, 24, 11, 59, tzinfo=UTC)
    with pytest.raises(ValidationError, match="cannot precede"):
        ResourceBudget.model_validate(reversed_data)

    naive_data = _budget_data()
    naive_data["interval_start"] = datetime(2026, 8, 24, 12, 0)
    with pytest.raises(ValidationError, match="must be timezone-aware"):
        ResourceBudget.model_validate(naive_data)


def test_artifact_record_uses_relative_path_size_and_hash(tmp_path: Path) -> None:
    artifact = tmp_path / "nested/artifact.txt"
    artifact.parent.mkdir()
    artifact.write_text("deterministic\n", encoding="utf-8")

    record = artifact_record(tmp_path, artifact)

    assert record.path == "nested/artifact.txt"
    assert record.size_bytes == artifact.stat().st_size
    assert len(record.sha256) == 64
