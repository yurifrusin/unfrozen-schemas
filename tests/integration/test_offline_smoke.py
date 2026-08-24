"""End-to-end offline smoke command and artifact-contract tests."""

from __future__ import annotations

import logging
import socket
from pathlib import Path
from typing import NoReturn

import pytest
from typer.testing import CliRunner

import unfrozen_schemas.cli as cli_module
import unfrozen_schemas.smoke as smoke_module
from unfrozen_schemas.cli import app
from unfrozen_schemas.config import ResolvedSmokeConfig, sha256_file
from unfrozen_schemas.constants import (
    BOOTSTRAP_FAILURE_FILENAME,
    BUDGET_FILENAME,
    GATE_METADATA_FILENAME,
    LOG_FILENAME,
    MANIFEST_FILENAME,
    RESOLVED_CONFIG_FILENAME,
    TOY_OUTPUT_FILENAME,
)
from unfrozen_schemas.provenance import BootstrapFailureRecord, RunManifest
from unfrozen_schemas.smoke import SmokeRunError


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


def test_smoke_cli_reports_nonzero_with_valid_claimed_bootstrap_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output_root = tmp_path / "runs"

    def fail_logging_setup(_path: Path, _level: str) -> logging.Logger:
        raise PermissionError("cli bootstrap sentinel")

    monkeypatch.setattr(smoke_module, "configure_logging", fail_logging_setup)

    result = CliRunner().invoke(app, ["smoke", "--output-root", str(output_root)])

    assert result.exit_code == 1
    assert "Smoke failure reason: PermissionError: cli bootstrap sentinel" in result.output
    assert "validated bootstrap failure record" in result.output
    run_directories = list(output_root.iterdir())
    assert len(run_directories) == 1
    bootstrap_path = run_directories[0] / BOOTSTRAP_FAILURE_FILENAME
    assert str(bootstrap_path) in result.output
    record = BootstrapFailureRecord.model_validate_json(bootstrap_path.read_text(encoding="utf-8"))
    assert record.original_failure_reason == "PermissionError: cli bootstrap sentinel"


def test_smoke_cli_does_not_claim_an_artifact_when_recording_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output_root = tmp_path / "runs"

    def fail_without_artifact(config: ResolvedSmokeConfig) -> NoReturn:
        raise SmokeRunError(
            "RuntimeError: original failure",
            config.run.output_root / "unrecorded-run",
            None,
            None,
            ("OSError: artifact recording failed",),
        )

    monkeypatch.setattr(cli_module, "run_smoke", fail_without_artifact)

    result = CliRunner().invoke(app, ["smoke", "--output-root", str(output_root)])

    assert result.exit_code == 1
    assert "Smoke failure reason: RuntimeError: original failure" in result.output
    assert "no validated failure artifact could be written" in result.output
    assert "validated failure manifest" not in result.output
    assert "validated bootstrap failure record" not in result.output
