"""M1 Parquet, manifest, accounting, logical-hash, and failure contracts."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

import unfrozen_schemas.data.core_runner as core_runner_module
from unfrozen_schemas.budgets import ResourceBudget
from unfrozen_schemas.config import sha256_file
from unfrozen_schemas.core_config import ResolvedCoreConfig, load_core_config
from unfrozen_schemas.data.core_models import CoreRunError, CoreRunManifest
from unfrozen_schemas.data.core_persistence import (
    EPISODE_SCHEMA,
    STEP_SCHEMA,
    read_episode_table,
    read_step_table,
    write_episode_table,
    write_step_table,
)
from unfrozen_schemas.data.core_runner import (
    CORE_MANIFEST_FILENAME,
    generate_core,
    validate_core_manifest,
)
from unfrozen_schemas.envs.schema_world.actions import Action, ActionKind
from unfrozen_schemas.envs.schema_world.dynamics import TransitionTrace
from unfrozen_schemas.envs.schema_world.serialization import (
    PrimaryObservation,
    canonical_record_bytes,
)
from unfrozen_schemas.envs.schema_world.state import WorldState
from unfrozen_schemas.envs.schema_world.templates import EpisodePlan
from unfrozen_schemas.provenance import artifact_record, write_json


def _generate(tmp_path: Path, run_id: str = "core-unit-run") -> Path:
    config = load_core_config(
        Path("configs/experiment/milestone1_core_smoke.yaml"),
        output_root_override=tmp_path,
    )
    result = generate_core(config, run_id=run_id)
    return Path(result.manifest_path)


def _refresh_artifact(manifest_path: Path, artifact_name: str) -> None:
    manifest = CoreRunManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    refreshed = artifact_record(manifest_path.parent, manifest_path.parent / artifact_name)
    artifacts = tuple(
        refreshed if item.path == artifact_name else item for item in manifest.artifacts
    )
    write_json(manifest_path, manifest.model_copy(update={"artifacts": artifacts}))


def _mutate_steps(manifest_path: Path, mutation: Callable[[list[dict[str, Any]]], None]) -> None:
    path = manifest_path.parent / "steps.parquet"
    rows = read_step_table(path)
    mutation(rows)
    write_step_table(path, rows)
    _refresh_artifact(manifest_path, "steps.parquet")


def _mutate_episodes(manifest_path: Path, mutation: Callable[[list[dict[str, Any]]], None]) -> None:
    path = manifest_path.parent / "episodes.parquet"
    rows = read_episode_table(path)
    mutation(rows)
    write_episode_table(path, rows)
    _refresh_artifact(manifest_path, "episodes.parquet")


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


def test_independent_validator_rejects_mutated_stored_action_for_the_planned_step(
    tmp_path: Path,
) -> None:
    manifest_path = _generate(tmp_path)

    def mutate(rows: list[dict[str, Any]]) -> None:
        row = next(
            item
            for item in rows
            if Action.model_validate_json(item["action_json"]).kind is not ActionKind.NOOP
        )
        row["action_json"] = canonical_record_bytes(Action(kind=ActionKind.NOOP))

    _mutate_steps(manifest_path, mutate)
    with pytest.raises(ValueError, match="Stored action does not match planned action"):
        validate_core_manifest(manifest_path)


def test_independent_validator_rejects_state_continuity_mutation(tmp_path: Path) -> None:
    manifest_path = _generate(tmp_path)

    def mutate(rows: list[dict[str, Any]]) -> None:
        state = WorldState.model_validate_json(rows[0]["state_before_json"])
        changed = state.model_copy(update={"noise_seed": state.noise_seed + 1})
        rows[0]["state_before_json"] = canonical_record_bytes(changed)

    _mutate_steps(manifest_path, mutate)
    with pytest.raises(ValueError, match="First state-before does not equal plan initial state"):
        validate_core_manifest(manifest_path)


def test_independent_validator_rejects_relation_mutation(tmp_path: Path) -> None:
    manifest_path = _generate(tmp_path)

    def mutate(rows: list[dict[str, Any]]) -> None:
        rows[0]["relations_after_json"] = canonical_record_bytes(())

    _mutate_steps(manifest_path, mutate)
    with pytest.raises(ValueError, match="Recomputed privileged relations mismatch"):
        validate_core_manifest(manifest_path)


def test_independent_validator_rejects_trace_mutation(tmp_path: Path) -> None:
    manifest_path = _generate(tmp_path)

    def mutate(rows: list[dict[str, Any]]) -> None:
        trace = TransitionTrace.model_validate_json(rows[0]["trace_json"])
        rows[0]["trace_json"] = canonical_record_bytes(trace.model_copy(update={"notes": ()}))

    _mutate_steps(manifest_path, mutate)
    with pytest.raises(ValueError, match="Recomputed transition trace mismatch"):
        validate_core_manifest(manifest_path)


def test_independent_validator_rejects_transition_hash_mutation(tmp_path: Path) -> None:
    manifest_path = _generate(tmp_path)

    def mutate(rows: list[dict[str, Any]]) -> None:
        rows[0]["transition_hash"] = "0" * 64

    _mutate_steps(manifest_path, mutate)
    with pytest.raises(ValueError, match="Recomputed transition hash mismatch"):
        validate_core_manifest(manifest_path)


def test_independent_validator_rejects_observation_mutation(tmp_path: Path) -> None:
    manifest_path = _generate(tmp_path)

    def mutate(rows: list[dict[str, Any]]) -> None:
        observation = PrimaryObservation.model_validate_json(rows[0]["observation_after_json"])
        rows[0]["observation_after_json"] = canonical_record_bytes(
            observation.model_copy(update={"step_index": observation.step_index + 1})
        )

    _mutate_steps(manifest_path, mutate)
    with pytest.raises(ValueError, match="observation-after does not match state-after"):
        validate_core_manifest(manifest_path)


def test_independent_validator_rejects_final_state_mutation(tmp_path: Path) -> None:
    manifest_path = _generate(tmp_path)

    def mutate(rows: list[dict[str, Any]]) -> None:
        plan = EpisodePlan.model_validate_json(rows[0]["plan_json"])
        rows[0]["final_state_json"] = canonical_record_bytes(plan.initial_state)

    _mutate_episodes(manifest_path, mutate)
    with pytest.raises(ValueError, match="final_state_json does not equal last state-after"):
        validate_core_manifest(manifest_path)


def test_independent_validator_rejects_budget_file_mutation(tmp_path: Path) -> None:
    manifest_path = _generate(tmp_path)
    budget_path = manifest_path.parent / "resource_budget.json"
    budget = ResourceBudget.model_validate_json(budget_path.read_text(encoding="utf-8"))
    assert budget.environment_steps is not None
    write_json(
        budget_path,
        budget.model_copy(update={"environment_steps": budget.environment_steps + 1}),
    )
    _refresh_artifact(manifest_path, "resource_budget.json")
    with pytest.raises(ValueError, match="does not equal the embedded ResourceBudget"):
        validate_core_manifest(manifest_path)


def test_independent_validator_rejects_resolved_config_file_mutation(tmp_path: Path) -> None:
    manifest_path = _generate(tmp_path)
    config_path = manifest_path.parent / "resolved_core_config.json"
    config = ResolvedCoreConfig.model_validate_json(config_path.read_text(encoding="utf-8"))
    changed_run = config.run.model_copy(update={"name": "mutated-core-config"})
    write_json(config_path, config.model_copy(update={"run": changed_run}))
    _refresh_artifact(manifest_path, "resolved_core_config.json")
    with pytest.raises(ValueError, match="does not equal the embedded resolved configuration"):
        validate_core_manifest(manifest_path)


@pytest.mark.parametrize("unsafe_path", ["../episodes.parquet", "C:/outside.parquet"])
def test_independent_validator_rejects_unsafe_artifact_paths(
    tmp_path: Path, unsafe_path: str
) -> None:
    manifest_path = _generate(tmp_path)
    manifest = CoreRunManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    changed = manifest.artifacts[0].model_copy(update={"path": unsafe_path})
    write_json(
        manifest_path,
        manifest.model_copy(update={"artifacts": (changed, *manifest.artifacts[1:])}),
    )
    with pytest.raises(ValueError, match=r"absolute|path traversal"):
        validate_core_manifest(manifest_path)


def test_independent_validator_rejects_duplicate_episode_ids_and_step_keys(
    tmp_path: Path,
) -> None:
    episode_manifest = _generate(tmp_path / "episodes", "duplicate-episodes")

    def duplicate_episode(rows: list[dict[str, Any]]) -> None:
        rows[1]["episode_id"] = rows[0]["episode_id"]

    _mutate_episodes(episode_manifest, duplicate_episode)
    with pytest.raises(ValueError, match="duplicate episode IDs"):
        validate_core_manifest(episode_manifest)

    step_manifest = _generate(tmp_path / "steps", "duplicate-steps")

    def duplicate_step(rows: list[dict[str, Any]]) -> None:
        rows[1]["episode_id"] = rows[0]["episode_id"]
        rows[1]["step_index"] = rows[0]["step_index"]

    _mutate_steps(step_manifest, duplicate_step)
    with pytest.raises(ValueError, match="duplicate episode/step keys"):
        validate_core_manifest(step_manifest)


def test_manifest_rejects_duplicate_pair_ids(tmp_path: Path) -> None:
    manifest_path = _generate(tmp_path)
    manifest = CoreRunManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    duplicated = (manifest.pair_ids[0], manifest.pair_ids[0], *manifest.pair_ids[1:])
    with pytest.raises(ValidationError, match="pair_ids must be unique"):
        CoreRunManifest.model_validate({**manifest.model_dump(), "pair_ids": duplicated})


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
