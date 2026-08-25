"""M1 Parquet, manifest, accounting, logical-hash, and failure contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

import unfrozen_schemas.data.core_runner as core_runner_module
from unfrozen_schemas.config import sha256_file
from unfrozen_schemas.core_config import load_core_config
from unfrozen_schemas.data.core_models import CoreRunError, CoreRunManifest
from unfrozen_schemas.data.core_persistence import (
    EPISODE_SCHEMA,
    STEP_SCHEMA,
    read_episode_table,
    read_step_table,
)
from unfrozen_schemas.data.core_runner import (
    CORE_MANIFEST_FILENAME,
    generate_core,
    validate_core_manifest,
)


def _generate(tmp_path: Path, run_id: str = "core-unit-run") -> Path:
    config = load_core_config(
        Path("configs/experiment/milestone1_core_smoke.yaml"),
        output_root_override=tmp_path,
    )
    result = generate_core(config, run_id=run_id)
    return Path(result.manifest_path)


def test_parquet_round_trip_manifest_and_resource_budget(tmp_path: Path) -> None:
    manifest_path = _generate(tmp_path)
    manifest = validate_core_manifest(manifest_path)
    assert manifest.schema_version == "1"
    assert manifest.resource_budget.schema_version == "2"
    assert manifest.status == "COMPLETED"
    assert manifest.engineering_only is True
    assert manifest.scientific_result is False
    assert len(manifest.episodes) == 12
    assert len(manifest.pair_ids) == 6
    assert {episode.schema_name for episode in manifest.episodes} == {
        "CONTAINMENT",
        "SUPPORT",
    }
    assert {episode.seed for episode in manifest.episodes} == {101, 202}
    assert manifest.resource_budget.environment_steps == 12
    assert manifest.resource_budget.sensor_observations == 24
    assert manifest.resource_budget.forward_passes == 0
    assert manifest.resource_budget.backward_passes == 0
    assert manifest.resource_budget.optimisation_steps == 0
    assert manifest.resource_budget.external_language_tokens == 0
    assert manifest.resource_budget.self_generated_language_tokens == 0
    assert manifest.resource_budget.measurement_basis["peak_memory_bytes"].method.startswith(
        "tracemalloc"
    )
    assert sum(item.size_bytes for item in manifest.artifacts) == (
        manifest.resource_budget.stored_artifact_bytes
    )
    assert len(manifest.artifacts) == manifest.resource_budget.stored_artifact_count

    assert manifest.episodes_path is not None and manifest.steps_path is not None
    episode_rows = read_episode_table(manifest_path.parent / manifest.episodes_path)
    step_rows = read_step_table(manifest_path.parent / manifest.steps_path)
    assert len(episode_rows) == 12
    assert len(step_rows) == 12
    assert EPISODE_SCHEMA.names == list(episode_rows[0])
    assert STEP_SCHEMA.names == list(step_rows[0])


def test_canonical_identity_is_independent_of_output_path_and_parquet_container(
    tmp_path: Path,
) -> None:
    left = validate_core_manifest(_generate(tmp_path / "left", "left-run"))
    right = validate_core_manifest(_generate(tmp_path / "right", "right-run"))
    assert left.episodes == right.episodes
    assert left.pair_ids == right.pair_ids
    assert left.resolved_configuration == right.resolved_configuration
    left_files = {artifact.path: artifact.sha256 for artifact in left.artifacts}
    right_files = {artifact.path: artifact.sha256 for artifact in right.artifacts}
    assert left_files["episodes.parquet"] == right_files["episodes.parquet"]
    assert left_files["steps.parquet"] == right_files["steps.parquet"]
    assert (
        sha256_file(tmp_path / "left/left-run/episodes.parquet") == left_files["episodes.parquet"]
    )


def test_generation_failure_preserves_validated_failure_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = load_core_config(
        Path("configs/experiment/milestone1_core_smoke.yaml"),
        output_root_override=tmp_path,
    )

    def fail_steps(_path: Path, _rows: list[dict[str, object]]) -> None:
        raise OSError("step persistence sentinel")

    monkeypatch.setattr(core_runner_module, "write_step_table", fail_steps)
    with pytest.raises(CoreRunError, match="step persistence sentinel") as captured:
        generate_core(config, run_id="failed-core-run")
    assert captured.value.manifest_path is not None
    manifest_path = Path(captured.value.manifest_path)
    manifest = CoreRunManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    assert manifest.status == "FAILED"
    assert manifest.failure_reason == "OSError: step persistence sentinel"
    assert manifest.resource_budget.interval_end == manifest.ended_at
    assert (tmp_path / "failed-core-run" / CORE_MANIFEST_FILENAME).is_file()
