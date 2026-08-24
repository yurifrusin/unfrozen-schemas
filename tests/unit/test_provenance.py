"""Determinism, Git provenance, hashing, and serialization tests."""

from __future__ import annotations

import random
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from unfrozen_schemas.budgets import ResourceBudget
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
    budget = ResourceBudget(
        run_id="serialization-test",
        external_language_tokens=2,
        self_generated_language_tokens=3,
        sensor_observations=5,
        sensor_bytes=7,
        environment_steps=11,
        optimisation_steps=13,
        forward_passes=17,
        backward_passes=19,
        elapsed_compute_seconds=0.25,
        peak_memory_bytes=23,
        stored_artifact_count=1,
        stored_artifact_bytes=29,
    )
    gate = Phase1GateMetadata()
    budget_path = tmp_path / "budget.json"
    gate_path = tmp_path / "gate.json"

    write_json(budget_path, budget)
    write_json(gate_path, gate)

    assert ResourceBudget.model_validate_json(budget_path.read_text(encoding="utf-8")) == budget
    restored_gate = Phase1GateMetadata.model_validate_json(gate_path.read_text(encoding="utf-8"))
    assert restored_gate == gate
    assert restored_gate.status == "NOT_EVALUATED"
    assert restored_gate.permits_phase2_scientific_work is False


def test_artifact_record_uses_relative_path_size_and_hash(tmp_path: Path) -> None:
    artifact = tmp_path / "nested/artifact.txt"
    artifact.parent.mkdir()
    artifact.write_text("deterministic\n", encoding="utf-8")

    record = artifact_record(tmp_path, artifact)

    assert record.path == "nested/artifact.txt"
    assert record.size_bytes == artifact.stat().st_size
    assert len(record.sha256) == 64
