"""End-to-end offline smoke command and artifact-contract tests."""

from __future__ import annotations

import socket
from pathlib import Path

import pytest
from typer.testing import CliRunner

from unfrozen_schemas.cli import app
from unfrozen_schemas.config import sha256_file
from unfrozen_schemas.constants import (
    BUDGET_FILENAME,
    GATE_METADATA_FILENAME,
    LOG_FILENAME,
    MANIFEST_FILENAME,
    RESOLVED_CONFIG_FILENAME,
    TOY_OUTPUT_FILENAME,
)
from unfrozen_schemas.provenance import RunManifest


def _deny_network(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("Milestone 0 smoke attempted a network call")


def test_offline_smoke_cli_writes_complete_hashed_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(socket, "create_connection", _deny_network)
    monkeypatch.setattr(socket.socket, "connect", _deny_network)
    output_root = tmp_path / "runs"
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["smoke", "--output-root", str(output_root), "--seed", "314159"],
    )

    assert result.exit_code == 0, result.output
    assert "Smoke run completed successfully" in result.output
    run_directories = list(output_root.iterdir())
    assert len(run_directories) == 1
    run_directory = run_directories[0]
    required_paths = [
        run_directory / RESOLVED_CONFIG_FILENAME,
        run_directory / TOY_OUTPUT_FILENAME,
        run_directory / BUDGET_FILENAME,
        run_directory / GATE_METADATA_FILENAME,
        run_directory / LOG_FILENAME,
        run_directory / MANIFEST_FILENAME,
    ]
    assert all(path.is_file() for path in required_paths)

    manifest = RunManifest.model_validate_json(
        (run_directory / MANIFEST_FILENAME).read_text(encoding="utf-8")
    )
    assert manifest.start_status == "STARTED"
    assert manifest.end_status == "COMPLETED"
    assert manifest.failure_reason is None
    assert manifest.declared_random_seed == 314159
    assert manifest.device == "cpu"
    assert manifest.network_access is False
    assert manifest.secret_required is False
    assert manifest.git.commit
    assert manifest.package_versions
    assert manifest.platform.python_version.startswith("3.11")
    assert manifest.resource_budget.forward_passes == 1
    assert manifest.resource_budget.backward_passes == 0
    assert manifest.resource_budget.optimisation_steps == 0
    assert manifest.phase1_gate_metadata.status == "NOT_EVALUATED"
    assert manifest.phase1_gate_metadata.permits_phase2_scientific_work is False

    artifact_bytes = 0
    for record in manifest.artifacts:
        path = run_directory / record.path
        assert path.is_file()
        assert sha256_file(path) == record.sha256
        assert path.stat().st_size == record.size_bytes
        artifact_bytes += record.size_bytes
    assert manifest.resource_budget.stored_artifact_count == len(manifest.artifacts)
    assert manifest.resource_budget.stored_artifact_bytes == artifact_bytes

    restored = RunManifest.model_validate_json(manifest.model_dump_json())
    assert restored == manifest


def test_validate_config_cli_uses_pinned_local_fixture() -> None:
    result = CliRunner().invoke(
        app, ["validate-config", "--config", "configs/experiment/smoke.yaml"]
    )

    assert result.exit_code == 0, result.output
    assert "Valid Milestone 0 configuration" in result.output
