"""Generation, validation, replay, inspection, provenance, and accounting for M1."""

from __future__ import annotations

import json
import time
import tracemalloc
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, cast

from unfrozen_schemas.budgets import (
    RESOURCE_FIELDS,
    ResourceBudget,
    ResourceField,
    ResourceMeasurementBasis,
)
from unfrozen_schemas.codecs.opaque_tokens import EncodedRecord, OpaqueDiscreteCodec
from unfrozen_schemas.config import find_repository_root, sha256_file
from unfrozen_schemas.core_config import LoadedCoreConfig, ResolvedCoreConfig
from unfrozen_schemas.data.core_models import (
    CoreEpisodeDigest,
    CoreRunError,
    CoreRunManifest,
    CoreRunResult,
    ReplayReport,
)
from unfrozen_schemas.data.core_persistence import (
    read_episode_table,
    read_step_table,
    write_episode_table,
    write_step_table,
)
from unfrozen_schemas.envs.schema_world.dynamics import transition
from unfrozen_schemas.envs.schema_world.relations import derive_relations
from unfrozen_schemas.envs.schema_world.renderer import render_raw_pixels, save_png
from unfrozen_schemas.envs.schema_world.serialization import (
    assert_relation_labels_absent,
    canonical_hash,
    canonical_record_bytes,
    primary_observation,
)
from unfrozen_schemas.envs.schema_world.state import WorldState
from unfrozen_schemas.envs.schema_world.templates import (
    EpisodePlan,
    MatchedPair,
    audit_matched_pair,
    generate_matched_pair,
)
from unfrozen_schemas.provenance import (
    ArtifactRecord,
    artifact_record,
    capture_git_state,
    collect_package_versions,
    collect_platform_information,
    create_run_id,
    utc_now,
    write_json,
)

CORE_MANIFEST_FILENAME = "core_manifest.json"
CORE_EPISODES_FILENAME = "episodes.parquet"
CORE_STEPS_FILENAME = "steps.parquet"
CORE_BUDGET_FILENAME = "resource_budget.json"
CORE_RESOLVED_CONFIG_FILENAME = "resolved_core_config.json"
CORE_REPLAY_REPORT_FILENAME = "replay_report.json"


class _Counters:
    def __init__(self) -> None:
        self.environment_steps = 0
        self.sensor_observations = 0
        self.sensor_bytes = 0


def _basis(
    status: Literal["measured", "derived", "observed_zero", "unavailable"],
    method: str,
    reason: str | None = None,
) -> ResourceMeasurementBasis:
    return ResourceMeasurementBasis(status=status, method=method, reason=reason)


def _measurement_basis(peak_available: bool) -> dict[ResourceField, ResourceMeasurementBasis]:
    observed_zero = {
        "external_language_tokens",
        "self_generated_language_tokens",
        "optimisation_steps",
        "forward_passes",
        "backward_passes",
    }
    result: dict[ResourceField, ResourceMeasurementBasis] = {}
    for field in RESOURCE_FIELDS:
        if field in observed_zero:
            result[field] = _basis("observed_zero", "M1 core code-path observation")
        elif field in {"stored_artifact_count", "stored_artifact_bytes"}:
            result[field] = _basis("derived", "sum of retained hash-stable run files")
        elif field == "elapsed_compute_seconds":
            result[field] = _basis("measured", "time.perf_counter monotonic elapsed time")
        elif field == "peak_memory_bytes":
            result[field] = (
                _basis("measured", "tracemalloc peak traced Python allocations")
                if peak_available
                else _basis(
                    "unavailable",
                    "tracemalloc peak traced Python allocations",
                    "tracemalloc did not start",
                )
            )
        elif field == "environment_steps":
            result[field] = _basis("measured", "accepted SchemaWorld transition count")
        elif field == "sensor_observations":
            result[field] = _basis("measured", "derived primary observation event count")
        elif field == "sensor_bytes":
            result[field] = _basis("measured", "canonical primary-observation UTF-8 bytes")
        else:
            raise AssertionError(field)
    return result


def _budget(
    *,
    run_id: str,
    started_at: datetime,
    ended_at: datetime,
    elapsed: float,
    peak_memory: int | None,
    counters: _Counters,
    artifact_count: int,
    artifact_bytes: int,
) -> ResourceBudget:
    return ResourceBudget(
        run_id=run_id,
        interval_kind="run",
        interval_start=started_at,
        interval_end=ended_at,
        external_language_tokens=0,
        self_generated_language_tokens=0,
        sensor_observations=counters.sensor_observations,
        sensor_bytes=counters.sensor_bytes,
        environment_steps=counters.environment_steps,
        optimisation_steps=0,
        forward_passes=0,
        backward_passes=0,
        elapsed_compute_seconds=elapsed,
        peak_memory_bytes=peak_memory,
        stored_artifact_count=artifact_count,
        stored_artifact_bytes=artifact_bytes,
        measurement_basis=_measurement_basis(peak_memory is not None),
    )


def _stabilize_budget(
    *,
    budget_path: Path,
    stable_paths: list[Path],
    run_id: str,
    started_at: datetime,
    ended_at: datetime,
    elapsed: float,
    peak_memory: int | None,
    counters: _Counters,
) -> ResourceBudget:
    count = len([path for path in stable_paths if path.is_file()]) + 1
    stored_bytes = sum(path.stat().st_size for path in stable_paths if path.is_file())
    candidate = _budget(
        run_id=run_id,
        started_at=started_at,
        ended_at=ended_at,
        elapsed=elapsed,
        peak_memory=peak_memory,
        counters=counters,
        artifact_count=count,
        artifact_bytes=stored_bytes,
    )
    for _ in range(12):
        write_json(budget_path, candidate)
        observed_bytes = sum(path.stat().st_size for path in stable_paths if path.is_file())
        observed_bytes += budget_path.stat().st_size
        if observed_bytes == candidate.stored_artifact_bytes:
            return candidate
        candidate = candidate.model_copy(update={"stored_artifact_bytes": observed_bytes})
    raise RuntimeError("M1 resource-budget artifact size did not reach a stable value")


def _artifact_records(run_directory: Path, paths: list[Path]) -> tuple[ArtifactRecord, ...]:
    return tuple(
        artifact_record(run_directory, path)
        for path in sorted(
            (path for path in paths if path.is_file()), key=lambda item: item.as_posix()
        )
    )


def _json_value(value: bytes) -> Any:
    return json.loads(value.decode("utf-8"))


def _trajectory_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "step_index": row["step_index"],
        "state_before": _json_value(row["state_before_json"]),
        "observation_before": _json_value(row["observation_before_json"]),
        "action": _json_value(row["action_json"]),
        "state_after": _json_value(row["state_after_json"]),
        "observation_after": _json_value(row["observation_after_json"]),
        "trace": _json_value(row["trace_json"]),
        "relations_after": _json_value(row["relations_after_json"]),
    }


def _execute_episode(
    plan: EpisodePlan,
    *,
    config: ResolvedCoreConfig,
    codec: OpaqueDiscreteCodec,
    counters: _Counters,
) -> tuple[dict[str, Any], list[dict[str, Any]], CoreEpisodeDigest]:
    state = plan.initial_state
    observation = primary_observation(state)
    assert_relation_labels_absent(observation)
    states: list[WorldState] = [state]
    observations = [observation]
    counters.sensor_observations += 1
    counters.sensor_bytes += len(canonical_record_bytes(observation))
    step_rows: list[dict[str, Any]] = []
    for action in plan.actions:
        before_state = state
        before_observation = observation
        result = transition(before_state, action)
        state = result.state
        observation = primary_observation(state)
        assert_relation_labels_absent(observation)
        relations = derive_relations(state, result.trace)
        encoded_before = codec.encode(before_observation, record_kind="observation")
        encoded_action = codec.encode(action, record_kind="action")
        encoded_after = codec.encode(observation, record_kind="observation")
        row = {
            "episode_id": plan.episode_id,
            "step_index": state.step_index,
            "state_before_json": canonical_record_bytes(before_state),
            "observation_before_json": canonical_record_bytes(before_observation),
            "opaque_observation_before_json": canonical_record_bytes(encoded_before),
            "action_json": canonical_record_bytes(action),
            "opaque_action_json": canonical_record_bytes(encoded_action),
            "state_after_json": canonical_record_bytes(state),
            "observation_after_json": canonical_record_bytes(observation),
            "opaque_observation_after_json": canonical_record_bytes(encoded_after),
            "trace_json": canonical_record_bytes(result.trace),
            "relations_after_json": canonical_record_bytes(relations),
            "state_before_hash": canonical_hash(before_state),
            "observation_before_hash": canonical_hash(before_observation),
            "state_after_hash": canonical_hash(state),
            "observation_after_hash": canonical_hash(observation),
            "transition_hash": result.transition_hash,
        }
        step_rows.append(row)
        states.append(state)
        observations.append(observation)
        counters.environment_steps += 1
        counters.sensor_observations += 1
        counters.sensor_bytes += len(canonical_record_bytes(observation))

    _, render_hash = render_raw_pixels(
        state, width=config.renderer.width, height=config.renderer.height
    )
    state_hash = canonical_hash(states)
    observation_hash = canonical_hash(observations)
    trajectory_hash = canonical_hash([_trajectory_payload(row) for row in step_rows])
    digest = CoreEpisodeDigest(
        episode_id=plan.episode_id,
        parent_pair_id=plan.parent_pair_id,
        template_id=plan.template_id.value,
        schema_name=plan.schema_name.value,
        seed=plan.seed,
        noise_seed=plan.noise_seed,
        initial_state_hash=plan.initial_state_hash,
        initial_observation_hash=plan.initial_observation_hash,
        state_hash=state_hash,
        observation_hash=observation_hash,
        trajectory_hash=trajectory_hash,
        action_sequence_hash=plan.action_sequence_hash,
        render_hash=render_hash,
    )
    episode_row = {
        "episode_id": plan.episode_id,
        "parent_pair_id": plan.parent_pair_id,
        "condition_index": plan.condition_index,
        "template_id": plan.template_id.value,
        "schema_name": plan.schema_name.value,
        "environment_version": plan.environment_version,
        "seed": plan.seed,
        "noise_seed": plan.noise_seed,
        "audited_target_factor": plan.audited_target_factor,
        "declared_difference_paths": list(plan.declared_difference_paths),
        "initial_state_hash": plan.initial_state_hash,
        "initial_observation_hash": plan.initial_observation_hash,
        "state_hash": state_hash,
        "observation_hash": observation_hash,
        "trajectory_hash": trajectory_hash,
        "action_sequence_hash": plan.action_sequence_hash,
        "render_hash": render_hash,
        "codec_version": config.codec.version,
        "renderer_version": config.renderer.version,
        "plan_json": canonical_record_bytes(plan),
        "final_state_json": canonical_record_bytes(state),
    }
    return episode_row, step_rows, digest


def _peak_and_stop(tracing_started: bool) -> int | None:
    if not tracing_started:
        return None
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak


def _manifest(
    *,
    run_kind: Literal["generate_core", "replay_core"],
    run_id: str,
    config: ResolvedCoreConfig,
    repository_root: Path,
    started_at: datetime,
    ended_at: datetime,
    status: Literal["COMPLETED", "FAILED"],
    failure_reason: str | None,
    source_manifest_sha256: str | None,
    episodes_path: str | None,
    steps_path: str | None,
    replay_report_path: str | None,
    digests: tuple[CoreEpisodeDigest, ...],
    artifacts: tuple[ArtifactRecord, ...],
    budget: ResourceBudget,
) -> CoreRunManifest:
    return CoreRunManifest(
        run_kind=run_kind,
        run_id=run_id,
        git=capture_git_state(repository_root),
        codex_spec_sha256=sha256_file(repository_root / "CODEX_SPEC.md"),
        resolved_configuration=config,
        package_versions=collect_package_versions(),
        platform=collect_platform_information(),
        started_at=started_at,
        ended_at=ended_at,
        status=status,
        failure_reason=failure_reason,
        source_manifest_sha256=source_manifest_sha256,
        episodes_path=episodes_path,
        steps_path=steps_path,
        budget_path=CORE_BUDGET_FILENAME,
        replay_report_path=replay_report_path,
        pair_ids=tuple(sorted({digest.parent_pair_id for digest in digests})),
        episodes=tuple(sorted(digests, key=lambda item: item.episode_id)),
        artifacts=artifacts,
        resource_budget=budget,
    )


def generate_core(config: LoadedCoreConfig, *, run_id: str | None = None) -> CoreRunResult:
    """Generate, parity-audit, persist, and account for the tracked tiny M1 curriculum."""

    resolved = config.resolved
    generated_run_id = run_id or create_run_id(resolved.run.name)
    run_directory = config.output_root / generated_run_id
    manifest_path = run_directory / CORE_MANIFEST_FILENAME
    started_at = utc_now()
    started_counter = time.perf_counter()
    tracing_started = False
    counters = _Counters()
    digests: tuple[CoreEpisodeDigest, ...] = ()
    run_directory.mkdir(parents=True, exist_ok=False)
    resolved_path = run_directory / CORE_RESOLVED_CONFIG_FILENAME
    episodes_path = run_directory / CORE_EPISODES_FILENAME
    steps_path = run_directory / CORE_STEPS_FILENAME
    budget_path = run_directory / CORE_BUDGET_FILENAME
    stable_paths: list[Path] = [resolved_path, episodes_path, steps_path]
    try:
        tracemalloc.start()
        tracing_started = True
        write_json(resolved_path, resolved)
        codec = OpaqueDiscreteCodec()
        episode_rows: list[dict[str, Any]] = []
        step_rows: list[dict[str, Any]] = []
        digest_list: list[CoreEpisodeDigest] = []
        for seed in resolved.generator.seeds:
            noise_seed = seed + resolved.generator.noise_seed_offset
            if noise_seed > 4_294_967_295:
                raise ValueError("Derived noise seed exceeds the unsigned 32-bit contract")
            for template_id in resolved.template_families:
                pair = generate_matched_pair(
                    template_id,
                    seed=seed,
                    noise_seed=noise_seed,
                    gravity=resolved.environment.gravity_per_step,
                    max_steps=resolved.environment.max_steps,
                )
                audit_matched_pair(pair)
                for plan in pair.episodes:
                    episode_row, episode_steps, digest = _execute_episode(
                        plan, config=resolved, codec=codec, counters=counters
                    )
                    episode_rows.append(episode_row)
                    step_rows.extend(episode_steps)
                    digest_list.append(digest)
        episode_rows.sort(key=lambda row: cast(str, row["episode_id"]))
        step_rows.sort(key=lambda row: (cast(str, row["episode_id"]), cast(int, row["step_index"])))
        digests = tuple(sorted(digest_list, key=lambda item: item.episode_id))
        write_episode_table(episodes_path, episode_rows)
        write_step_table(steps_path, step_rows)
        ended_at = utc_now()
        elapsed = time.perf_counter() - started_counter
        peak_memory = _peak_and_stop(tracing_started)
        tracing_started = False
        budget = _stabilize_budget(
            budget_path=budget_path,
            stable_paths=stable_paths,
            run_id=generated_run_id,
            started_at=started_at,
            ended_at=ended_at,
            elapsed=elapsed,
            peak_memory=peak_memory,
            counters=counters,
        )
        artifact_paths = [*stable_paths, budget_path]
        manifest = _manifest(
            run_kind="generate_core",
            run_id=generated_run_id,
            config=resolved,
            repository_root=config.repository_root,
            started_at=started_at,
            ended_at=ended_at,
            status="COMPLETED",
            failure_reason=None,
            source_manifest_sha256=None,
            episodes_path=CORE_EPISODES_FILENAME,
            steps_path=CORE_STEPS_FILENAME,
            replay_report_path=None,
            digests=digests,
            artifacts=_artifact_records(run_directory, artifact_paths),
            budget=budget,
        )
        write_json(manifest_path, manifest)
    except Exception as exc:
        peak_memory = _peak_and_stop(True) if tracing_started else None
        ended_at = utc_now()
        elapsed = time.perf_counter() - started_counter
        failure_reason = f"{type(exc).__name__}: {exc}"
        failure_manifest_path: str | None = None
        try:
            budget = _stabilize_budget(
                budget_path=budget_path,
                stable_paths=stable_paths,
                run_id=generated_run_id,
                started_at=started_at,
                ended_at=ended_at,
                elapsed=elapsed,
                peak_memory=peak_memory,
                counters=counters,
            )
            artifact_paths = [*stable_paths, budget_path]
            failure_manifest = _manifest(
                run_kind="generate_core",
                run_id=generated_run_id,
                config=resolved,
                repository_root=config.repository_root,
                started_at=started_at,
                ended_at=ended_at,
                status="FAILED",
                failure_reason=failure_reason,
                source_manifest_sha256=None,
                episodes_path=CORE_EPISODES_FILENAME if episodes_path.is_file() else None,
                steps_path=CORE_STEPS_FILENAME if steps_path.is_file() else None,
                replay_report_path=None,
                digests=digests,
                artifacts=_artifact_records(run_directory, artifact_paths),
                budget=budget,
            )
            write_json(manifest_path, failure_manifest)
            CoreRunManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
            failure_manifest_path = str(manifest_path)
        except Exception:
            failure_manifest_path = None
        raise CoreRunError(
            failure_reason,
            run_directory=str(run_directory),
            manifest_path=failure_manifest_path,
        ) from exc
    return CoreRunResult(
        run_id=generated_run_id,
        run_directory=str(run_directory),
        manifest_path=str(manifest_path),
    )


def _episode_digest_from_row(row: dict[str, Any]) -> CoreEpisodeDigest:
    return CoreEpisodeDigest(
        episode_id=row["episode_id"],
        parent_pair_id=row["parent_pair_id"],
        template_id=row["template_id"],
        schema_name=row["schema_name"],
        seed=row["seed"],
        noise_seed=row["noise_seed"],
        initial_state_hash=row["initial_state_hash"],
        initial_observation_hash=row["initial_observation_hash"],
        state_hash=row["state_hash"],
        observation_hash=row["observation_hash"],
        trajectory_hash=row["trajectory_hash"],
        action_sequence_hash=row["action_sequence_hash"],
        render_hash=row["render_hash"],
    )


def _validate_generation_records(
    manifest_path: Path, manifest: CoreRunManifest
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    run_directory = manifest_path.parent
    assert manifest.episodes_path is not None and manifest.steps_path is not None
    episode_rows = read_episode_table(run_directory / manifest.episodes_path)
    step_rows = read_step_table(run_directory / manifest.steps_path)
    steps_by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in step_rows:
        steps_by_episode[cast(str, row["episode_id"])].append(row)
    plans_by_pair: dict[str, list[EpisodePlan]] = defaultdict(list)
    observed_digests: list[CoreEpisodeDigest] = []
    codec = OpaqueDiscreteCodec()
    for row in episode_rows:
        plan = EpisodePlan.model_validate_json(row["plan_json"])
        plans_by_pair[plan.parent_pair_id].append(plan)
        if canonical_hash(plan.initial_state) != row["initial_state_hash"]:
            raise ValueError(f"Initial state hash mismatch for {plan.episode_id}")
        if (
            canonical_hash(primary_observation(plan.initial_state))
            != row["initial_observation_hash"]
        ):
            raise ValueError(f"Initial observation hash mismatch for {plan.episode_id}")
        if canonical_hash(plan.actions) != row["action_sequence_hash"]:
            raise ValueError(f"Action sequence hash mismatch for {plan.episode_id}")
        episode_steps = sorted(
            steps_by_episode[plan.episode_id], key=lambda item: cast(int, item["step_index"])
        )
        states: list[Any] = [plan.initial_state.model_dump(mode="json")]
        observations: list[Any] = [primary_observation(plan.initial_state).model_dump(mode="json")]
        for step_row in episode_steps:
            before_obs = _json_value(step_row["observation_before_json"])
            after_obs = _json_value(step_row["observation_after_json"])
            assert_relation_labels_absent(before_obs)
            assert_relation_labels_absent(after_obs)
            encoded_before = EncodedRecord.model_validate_json(
                step_row["opaque_observation_before_json"]
            )
            encoded_after = EncodedRecord.model_validate_json(
                step_row["opaque_observation_after_json"]
            )
            encoded_action = EncodedRecord.model_validate_json(step_row["opaque_action_json"])
            if codec.decode_bytes(encoded_before) != step_row["observation_before_json"]:
                raise ValueError(f"Opaque before-observation mismatch for {plan.episode_id}")
            if codec.decode_bytes(encoded_after) != step_row["observation_after_json"]:
                raise ValueError(f"Opaque after-observation mismatch for {plan.episode_id}")
            if codec.decode_bytes(encoded_action) != step_row["action_json"]:
                raise ValueError(f"Opaque action mismatch for {plan.episode_id}")
            states.append(_json_value(step_row["state_after_json"]))
            observations.append(after_obs)
        if canonical_hash(states) != row["state_hash"]:
            raise ValueError(f"State sequence hash mismatch for {plan.episode_id}")
        if canonical_hash(observations) != row["observation_hash"]:
            raise ValueError(f"Observation sequence hash mismatch for {plan.episode_id}")
        if (
            canonical_hash([_trajectory_payload(item) for item in episode_steps])
            != row["trajectory_hash"]
        ):
            raise ValueError(f"Trajectory hash mismatch for {plan.episode_id}")
        final_state = WorldState.model_validate_json(row["final_state_json"])
        _, render_hash = render_raw_pixels(
            final_state,
            width=manifest.resolved_configuration.renderer.width,
            height=manifest.resolved_configuration.renderer.height,
        )
        if render_hash != row["render_hash"]:
            raise ValueError(f"Raw-pixel render hash mismatch for {plan.episode_id}")
        observed_digests.append(_episode_digest_from_row(row))
    for pair_id, plans in plans_by_pair.items():
        if len(plans) != 2:
            raise ValueError(f"Pair {pair_id} must contain exactly two episode plans")
        ordered = tuple(sorted(plans, key=lambda item: item.condition_index))
        pair = MatchedPair(
            pair_id=pair_id,
            target_factor=ordered[0].audited_target_factor,
            declared_difference_paths=ordered[0].declared_difference_paths,
            episodes=(ordered[0], ordered[1]),
        )
        audit_matched_pair(pair)
    if tuple(sorted(observed_digests, key=lambda item: item.episode_id)) != manifest.episodes:
        raise ValueError("Manifest episode digests do not match the Parquet logical records")
    return episode_rows, step_rows


def validate_core_manifest(manifest_path: Path) -> CoreRunManifest:
    """Validate manifest, artifacts, explicit Parquet schemas, hashes, codec, and pair parity."""

    path = manifest_path.resolve()
    manifest = CoreRunManifest.model_validate_json(path.read_text(encoding="utf-8"))
    run_directory = path.parent
    for record in manifest.artifacts:
        artifact = run_directory / record.path
        if not artifact.is_file():
            raise ValueError(f"Manifest artifact is missing: {record.path}")
        if artifact.stat().st_size != record.size_bytes or sha256_file(artifact) != record.sha256:
            raise ValueError(f"Manifest artifact identity mismatch: {record.path}")
    if manifest.run_kind == "generate_core" and manifest.status == "COMPLETED":
        _validate_generation_records(path, manifest)
    if manifest.run_kind == "replay_core" and manifest.status == "COMPLETED":
        if manifest.replay_report_path is None:
            raise ValueError("Completed replay manifest lacks replay_report_path")
        report = ReplayReport.model_validate_json(
            (run_directory / manifest.replay_report_path).read_text(encoding="utf-8")
        )
        if report.source_manifest_sha256 != manifest.source_manifest_sha256:
            raise ValueError("Replay report and manifest source hashes differ")
    return manifest


def replay_core(source_manifest_path: Path, *, run_id: str | None = None) -> CoreRunResult:
    """Regenerate every source trajectory and record a separate accounted replay run."""

    source_path = source_manifest_path.resolve()
    source = validate_core_manifest(source_path)
    if source.run_kind != "generate_core" or source.status != "COMPLETED":
        raise ValueError("Replay requires a completed generate_core manifest")
    source_rows = read_episode_table(source_path.parent / cast(str, source.episodes_path))
    source_sha = sha256_file(source_path)
    repository_root = find_repository_root(Path.cwd())
    generated_run_id = run_id or create_run_id("milestone-1-core-replay")
    output_root = source_path.parent.parent
    run_directory = output_root / generated_run_id
    run_directory.mkdir(parents=True, exist_ok=False)
    manifest_path = run_directory / CORE_MANIFEST_FILENAME
    report_path = run_directory / CORE_REPLAY_REPORT_FILENAME
    budget_path = run_directory / CORE_BUDGET_FILENAME
    started_at = utc_now()
    started_counter = time.perf_counter()
    counters = _Counters()
    observed: list[CoreEpisodeDigest] = []
    tracemalloc.start()
    try:
        codec = OpaqueDiscreteCodec()
        for row in source_rows:
            plan = EpisodePlan.model_validate_json(row["plan_json"])
            replay_row, _, digest = _execute_episode(
                plan,
                config=source.resolved_configuration,
                codec=codec,
                counters=counters,
            )
            expected = _episode_digest_from_row(row)
            if digest != expected:
                raise ValueError(
                    f"Replay hash mismatch for {plan.episode_id}: "
                    f"expected={expected.model_dump()}, observed={digest.model_dump()}"
                )
            if replay_row["final_state_json"] != row["final_state_json"]:
                raise ValueError(f"Replay final state bytes differ for {plan.episode_id}")
            observed.append(digest)
        report = ReplayReport(
            source_manifest_sha256=source_sha,
            matched_episode_ids=tuple(sorted(item.episode_id for item in observed)),
        )
        write_json(report_path, report)
        ended_at = utc_now()
        elapsed = time.perf_counter() - started_counter
        peak_memory = _peak_and_stop(True)
        budget = _stabilize_budget(
            budget_path=budget_path,
            stable_paths=[report_path],
            run_id=generated_run_id,
            started_at=started_at,
            ended_at=ended_at,
            elapsed=elapsed,
            peak_memory=peak_memory,
            counters=counters,
        )
        artifacts = _artifact_records(run_directory, [report_path, budget_path])
        manifest = _manifest(
            run_kind="replay_core",
            run_id=generated_run_id,
            config=source.resolved_configuration,
            repository_root=repository_root,
            started_at=started_at,
            ended_at=ended_at,
            status="COMPLETED",
            failure_reason=None,
            source_manifest_sha256=source_sha,
            episodes_path=None,
            steps_path=None,
            replay_report_path=CORE_REPLAY_REPORT_FILENAME,
            digests=tuple(observed),
            artifacts=artifacts,
            budget=budget,
        )
        write_json(manifest_path, manifest)
    except Exception as exc:
        peak_memory = _peak_and_stop(True) if tracemalloc.is_tracing() else None
        ended_at = utc_now()
        elapsed = time.perf_counter() - started_counter
        failure_reason = f"{type(exc).__name__}: {exc}"
        failure_manifest_path: str | None = None
        try:
            budget = _stabilize_budget(
                budget_path=budget_path,
                stable_paths=[report_path],
                run_id=generated_run_id,
                started_at=started_at,
                ended_at=ended_at,
                elapsed=elapsed,
                peak_memory=peak_memory,
                counters=counters,
            )
            artifacts = _artifact_records(run_directory, [report_path, budget_path])
            failure_manifest = _manifest(
                run_kind="replay_core",
                run_id=generated_run_id,
                config=source.resolved_configuration,
                repository_root=repository_root,
                started_at=started_at,
                ended_at=ended_at,
                status="FAILED",
                failure_reason=failure_reason,
                source_manifest_sha256=source_sha,
                episodes_path=None,
                steps_path=None,
                replay_report_path=(CORE_REPLAY_REPORT_FILENAME if report_path.is_file() else None),
                digests=tuple(observed),
                artifacts=artifacts,
                budget=budget,
            )
            write_json(manifest_path, failure_manifest)
            CoreRunManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
            failure_manifest_path = str(manifest_path)
        except Exception:
            failure_manifest_path = None
        raise CoreRunError(
            failure_reason,
            run_directory=str(run_directory),
            manifest_path=failure_manifest_path,
        ) from exc
    return CoreRunResult(
        run_id=generated_run_id,
        run_directory=str(run_directory),
        manifest_path=str(manifest_path),
    )


def locate_episode_manifest(episode_id: str, *, root: Path = Path("runs")) -> Path:
    matches: list[Path] = []
    for manifest_path in sorted(
        root.glob(f"*/{CORE_MANIFEST_FILENAME}"), key=lambda item: item.as_posix()
    ):
        try:
            manifest = CoreRunManifest.model_validate_json(
                manifest_path.read_text(encoding="utf-8")
            )
            if manifest.run_kind == "generate_core" and any(
                episode.episode_id == episode_id for episode in manifest.episodes
            ):
                matches.append(manifest_path)
        except Exception:
            continue
    if not matches:
        raise ValueError(f"No generated core manifest contains episode {episode_id}")
    if len(matches) > 1:
        raise ValueError(
            f"Episode {episode_id} occurs in multiple manifests; pass --manifest explicitly"
        )
    return matches[0]


def inspect_episode(
    episode_id: str,
    *,
    manifest_path: Path,
    render: bool,
    output_path: Path | None = None,
) -> dict[str, str | int | bool]:
    manifest = validate_core_manifest(manifest_path)
    if manifest.run_kind != "generate_core" or manifest.episodes_path is None:
        raise ValueError("Episode inspection requires a completed generation manifest")
    rows = read_episode_table(manifest_path.parent / manifest.episodes_path)
    matches = [row for row in rows if row["episode_id"] == episode_id]
    if len(matches) != 1:
        raise ValueError(f"Expected one episode {episode_id}, observed {len(matches)}")
    row = matches[0]
    state = WorldState.model_validate_json(row["final_state_json"])
    summary: dict[str, str | int | bool] = {
        "episode_id": episode_id,
        "template_id": row["template_id"],
        "schema_name": row["schema_name"],
        "state_hash": row["state_hash"],
        "observation_hash": row["observation_hash"],
        "trajectory_hash": row["trajectory_hash"],
        "render_hash": row["render_hash"],
        "rendered": render,
    }
    if render:
        pixels, observed_hash = render_raw_pixels(
            state,
            width=manifest.resolved_configuration.renderer.width,
            height=manifest.resolved_configuration.renderer.height,
        )
        if observed_hash != row["render_hash"]:
            raise ValueError("Inspection renderer hash differs from the generated logical record")
        destination = output_path or (manifest_path.parent / "inspection" / f"{episode_id}.png")
        save_png(
            destination,
            pixels,
            width=manifest.resolved_configuration.renderer.width,
            height=manifest.resolved_configuration.renderer.height,
        )
        summary["render_path"] = str(destination)
        summary["png_sha256"] = sha256_file(destination)
    return summary
