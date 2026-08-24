"""Failure-path preservation tests for the smoke runner."""

from __future__ import annotations

from pathlib import Path

import pytest

from unfrozen_schemas.config import load_smoke_config
from unfrozen_schemas.constants import (
    BUDGET_FILENAME,
    GATE_METADATA_FILENAME,
    MANIFEST_FILENAME,
    RESOLVED_CONFIG_FILENAME,
)
from unfrozen_schemas.provenance import RunManifest
from unfrozen_schemas.smoke import SmokeRunError, run_smoke


def test_failed_smoke_run_records_complete_failure_manifest(tmp_path: Path) -> None:
    resolved = load_smoke_config(
        Path("configs/experiment/smoke.yaml"), output_root_override=tmp_path
    )
    missing_model = resolved.model.model_copy(update={"fixture_path": tmp_path / "missing.json"})
    failing_config = resolved.model_copy(update={"model": missing_model})

    with pytest.raises(SmokeRunError) as captured:
        run_smoke(failing_config, run_id="failure-reporting-test")

    run_directory = captured.value.run_directory
    manifest_path = run_directory / MANIFEST_FILENAME
    manifest = RunManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))

    assert captured.value.manifest_path == manifest_path
    assert manifest.start_status == "STARTED"
    assert manifest.end_status == "FAILED"
    assert manifest.ended_at is not None
    assert manifest.failure_reason is not None
    assert "FileNotFoundError" in manifest.failure_reason
    assert manifest.phase1_gate_metadata.permits_phase2_scientific_work is False
    assert (run_directory / RESOLVED_CONFIG_FILENAME).is_file()
    assert (run_directory / BUDGET_FILENAME).is_file()
    assert (run_directory / GATE_METADATA_FILENAME).is_file()
