"""Separate Milestone 1 manifests that preserve released Milestone 0 contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from unfrozen_schemas.budgets import ResourceBudget
from unfrozen_schemas.config import FrozenModel
from unfrozen_schemas.core_config import ResolvedCoreConfig
from unfrozen_schemas.provenance import ArtifactRecord, GitState, PlatformInformation


class CoreEpisodeDigest(FrozenModel):
    episode_id: str
    parent_pair_id: str
    template_id: str
    schema_name: Literal["CONTAINMENT", "SUPPORT"]
    seed: int
    noise_seed: int
    initial_state_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    initial_observation_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    state_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    observation_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    trajectory_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    action_sequence_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    render_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


class CoreRunManifest(FrozenModel):
    """M1 generation/replay record; not interchangeable with the M0 RunManifest."""

    schema_version: Literal["1"] = "1"
    manifest_kind: Literal["schemaworld_core_run"] = "schemaworld_core_run"
    run_kind: Literal["generate_core", "replay_core"]
    run_id: str = Field(min_length=1)
    scientific_phase: Literal[1] = 1
    engineering_only: Literal[True] = True
    scientific_result: Literal[False] = False
    git: GitState
    codex_spec_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    resolved_configuration: ResolvedCoreConfig
    package_versions: dict[str, str]
    platform: PlatformInformation
    device: Literal["cpu"] = "cpu"
    network_access: Literal[False] = False
    secret_required: Literal[False] = False
    generator_identity: Literal["splitmix64-v1"] = "splitmix64-v1"
    codec_version: Literal["opaque-byte-v1"] = "opaque-byte-v1"
    renderer_version: Literal["schemaworld-raster-v1"] = "schemaworld-raster-v1"
    started_at: datetime
    ended_at: datetime
    status: Literal["COMPLETED", "FAILED"]
    failure_reason: str | None
    source_manifest_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    episodes_path: str | None
    steps_path: str | None
    budget_path: str
    replay_report_path: str | None
    pair_ids: tuple[str, ...]
    episodes: tuple[CoreEpisodeDigest, ...]
    artifacts: tuple[ArtifactRecord, ...]
    resource_budget: ResourceBudget

    @model_validator(mode="after")
    def validate_terminal_contract(self) -> CoreRunManifest:
        if self.started_at.tzinfo is None or self.ended_at.tzinfo is None:
            raise ValueError("Core run timestamps must be timezone-aware")
        if self.ended_at < self.started_at:
            raise ValueError("Core run ended_at cannot precede started_at")
        if self.status == "FAILED" and not self.failure_reason:
            raise ValueError("A failed core manifest requires a failure_reason")
        if self.status == "COMPLETED" and self.failure_reason is not None:
            raise ValueError("A completed core manifest cannot have a failure_reason")
        if self.run_kind == "replay_core" and self.source_manifest_sha256 is None:
            raise ValueError("A replay manifest requires source_manifest_sha256")
        if self.run_kind == "generate_core" and self.source_manifest_sha256 is not None:
            raise ValueError("A generation manifest cannot name a source manifest")
        if self.resource_budget.schema_version != "2":
            raise ValueError("M1 must reuse the released resource-budget schema version 2")
        if self.resource_budget.run_id != self.run_id:
            raise ValueError("Core manifest and budget run IDs must match")
        if self.resource_budget.interval_start != self.started_at:
            raise ValueError("Core manifest and budget must start together")
        if self.resource_budget.interval_end != self.ended_at:
            raise ValueError("Core manifest and budget must end together")
        if tuple(sorted(self.pair_ids)) != self.pair_ids:
            raise ValueError("Core pair_ids must use canonical ordering")
        if tuple(sorted(self.episodes, key=lambda item: item.episode_id)) != self.episodes:
            raise ValueError("Core episode digests must use canonical episode_id ordering")
        return self


class ReplayReport(FrozenModel):
    schema_version: Literal["1"] = "1"
    source_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    matched_episode_ids: tuple[str, ...]
    all_hashes_match: Literal[True] = True


class CoreRunResult(FrozenModel):
    run_id: str
    run_directory: str
    manifest_path: str


class CoreRunError(RuntimeError):
    """Raised after preserving the strongest available M1 failure manifest."""

    def __init__(self, message: str, *, run_directory: str, manifest_path: str | None) -> None:
        super().__init__(message)
        self.run_directory = run_directory
        self.manifest_path = manifest_path
