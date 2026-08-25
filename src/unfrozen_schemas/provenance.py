"""Run identity, provenance capture, hashing, and canonical serialization."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import random
import re
import subprocess
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from unfrozen_schemas.budgets import ResourceBudget
from unfrozen_schemas.config import ResolvedSmokeConfig, sha256_file


class FrozenRecord(BaseModel):
    """Base for immutable, strict provenance records."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class GitState(FrozenRecord):
    """Commit and complete working-tree dirty state for a run."""

    commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    dirty: bool


class PlatformInformation(FrozenRecord):
    """Host and interpreter details needed to contextualise a toy run."""

    system: str
    release: str
    version: str
    machine: str
    processor: str
    python_version: str
    python_implementation: str


class ArtifactRecord(FrozenRecord):
    """A hash-stable run artifact, addressed relative to the run directory."""

    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)


class Phase1GateMetadata(FrozenRecord):
    """Non-authorising placeholder emitted before the Phase I gate exists."""

    schema_version: Literal["1"] = "1"
    phase: Literal[1] = 1
    gate_type: Literal["primary"] = "primary"
    status: Literal["NOT_EVALUATED"] = "NOT_EVALUATED"
    is_placeholder: Literal[True] = True
    scientific_evidence: Literal[False] = False
    permits_phase2_scientific_work: Literal[False] = False
    report_hash: None = None
    approval_hash: None = None
    note: str = (
        "Milestone 0 engineering placeholder only; this is not a Phase I gate report or approval."
    )


class RunManifest(FrozenRecord):
    """Complete Milestone 0 run manifest for success and clean failure paths."""

    schema_version: Literal["2"] = "2"
    run_id: str
    run_kind: Literal["milestone_0_smoke"] = "milestone_0_smoke"
    scientific_phase: Literal[0] = 0
    engineering_only: Literal[True] = True
    scientific_result: Literal[False] = False
    git: GitState
    resolved_configuration: ResolvedSmokeConfig
    package_versions: dict[str, str]
    platform: PlatformInformation
    declared_random_seed: int
    device: Literal["cpu"] = "cpu"
    network_access: Literal[False] = False
    secret_required: Literal[False] = False
    model_fixture_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    started_at: datetime
    ended_at: datetime | None
    start_status: Literal["STARTED"] = "STARTED"
    end_status: Literal["RUNNING", "COMPLETED", "FAILED"]
    failure_reason: str | None
    resolved_configuration_path: str
    resource_budget_path: str
    phase1_gate_metadata_path: str
    structured_log_path: str
    artifacts: list[ArtifactRecord]
    resource_budget: ResourceBudget
    phase1_gate_metadata: Phase1GateMetadata

    @model_validator(mode="after")
    def validate_terminal_state(self) -> RunManifest:
        """Keep final status, timestamp, and failure reason mutually consistent."""

        if self.resource_budget.run_id != self.run_id:
            raise ValueError("The resource budget run ID must match the manifest run ID")
        if self.resource_budget.interval_kind != "run":
            raise ValueError("A run manifest requires a run-kind resource interval")
        if self.resource_budget.interval_start != self.started_at:
            raise ValueError("The resource budget must start with the surrounding run manifest")
        if self.end_status == "RUNNING":
            if self.ended_at is not None or self.failure_reason is not None:
                raise ValueError("A running manifest cannot have an end time or failure reason")
            if self.resource_budget.interval_end is not None:
                raise ValueError("A running manifest requires an open resource interval")
        elif self.ended_at is None:
            raise ValueError("A terminal manifest requires an end time")
        elif self.resource_budget.interval_end != self.ended_at:
            raise ValueError("A terminal resource interval must end with its run manifest")
        if self.end_status == "FAILED" and not self.failure_reason:
            raise ValueError("A failed manifest requires a failure reason")
        if self.end_status == "COMPLETED" and self.failure_reason is not None:
            raise ValueError("A completed manifest cannot have a failure reason")
        return self


class BootstrapFailureRecord(FrozenRecord):
    """Failure provenance when a complete terminal run manifest cannot be guaranteed."""

    schema_version: Literal["2"] = "2"
    record_kind: Literal["milestone_0_bootstrap_failure"] = "milestone_0_bootstrap_failure"
    run_id: str
    scientific_phase: Literal[0] = 0
    engineering_only: Literal[True] = True
    scientific_result: Literal[False] = False
    run_declared_started: bool
    failure_stage: str = Field(min_length=1)
    original_exception_type: str = Field(min_length=1)
    original_failure_reason: str = Field(min_length=1)
    started_at: datetime
    ended_at: datetime
    recorded_at: datetime
    git: GitState
    resolved_configuration: ResolvedSmokeConfig
    package_versions: dict[str, str]
    platform: PlatformInformation
    declared_random_seed: int
    resource_budget: ResourceBudget
    artifacts: list[ArtifactRecord]
    last_manifest_path: str | None
    last_manifest_status: Literal["RUNNING", "COMPLETED", "FAILED"] | None
    recording_errors: list[str]

    @model_validator(mode="after")
    def validate_terminal_budget(self) -> BootstrapFailureRecord:
        if self.resource_budget.run_id != self.run_id:
            raise ValueError("The resource budget run ID must match the bootstrap record run ID")
        if self.resource_budget.interval_kind != "run":
            raise ValueError("A bootstrap failure requires a run-kind resource interval")
        if self.resource_budget.interval_start != self.started_at:
            raise ValueError("The resource budget must start with the bootstrap failure interval")
        if self.resource_budget.interval_end != self.ended_at:
            raise ValueError("A bootstrap failure requires a closed matching resource interval")
        if self.recorded_at < self.ended_at:
            raise ValueError("A bootstrap failure cannot be recorded before its interval ends")
        return self


def utc_now() -> datetime:
    """Return an aware UTC timestamp."""

    return datetime.now(UTC)


def create_run_id(
    label: str,
    *,
    now: datetime | None = None,
    nonce: str | None = None,
) -> str:
    """Create a sortable run ID; injected time and nonce make it exactly testable."""

    safe_label = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
    if not safe_label:
        raise ValueError("Run label must contain at least one letter or number")
    timestamp_value = utc_now() if now is None else now
    if timestamp_value.tzinfo is None:
        raise ValueError("Run ID timestamps must be timezone-aware")
    timestamp = timestamp_value.astimezone(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    nonce_value = uuid.uuid4().hex if nonce is None else nonce
    suffix = hashlib.sha256(nonce_value.encode("utf-8")).hexdigest()[:10]
    return f"{safe_label}-{timestamp}-{suffix}"


def seed_everything(seed: int) -> random.Random:
    """Seed the standard-library global PRNG and return an isolated seeded generator."""

    if not 0 <= seed <= 4_294_967_295:
        raise ValueError("Seed must be between 0 and 4294967295")
    random.seed(seed)
    return random.Random(seed)


def capture_git_state(repository_root: Path) -> GitState:
    """Capture the exact commit and tracked/untracked dirty state without network access."""

    def git(*arguments: str) -> str:
        try:
            completed = subprocess.run(
                ["git", *arguments],
                cwd=repository_root,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise RuntimeError(f"Unable to capture Git provenance: {exc}") from exc
        return completed.stdout.strip()

    commit = git("rev-parse", "HEAD")
    status = git("status", "--porcelain=v1", "--untracked-files=normal")
    return GitState(commit=commit, dirty=bool(status))


def collect_package_versions() -> dict[str, str]:
    """Capture all installed distribution versions in stable name order."""

    versions: dict[str, str] = {}
    for distribution in importlib.metadata.distributions():
        try:
            name = distribution.metadata["Name"]
        except KeyError:
            name = None
        if name:
            versions[name.lower()] = distribution.version
    return dict(sorted(versions.items()))


def collect_platform_information() -> PlatformInformation:
    """Capture operating-system, architecture, and Python details."""

    return PlatformInformation(
        system=platform.system(),
        release=platform.release(),
        version=platform.version(),
        machine=platform.machine(),
        processor=platform.processor(),
        python_version=platform.python_version(),
        python_implementation=platform.python_implementation(),
    )


def canonical_json_bytes(value: BaseModel | Mapping[str, Any]) -> bytes:
    """Serialize a model or mapping as stable UTF-8 JSON with a final newline."""

    data = value.model_dump(mode="json") if isinstance(value, BaseModel) else dict(value)
    return (
        json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def write_json(path: Path, value: BaseModel | Mapping[str, Any]) -> None:
    """Write canonical JSON, creating only the requested parent directory."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))


def artifact_record(run_directory: Path, path: Path) -> ArtifactRecord:
    """Record a stable artifact using a portable run-relative path."""

    resolved_run = run_directory.resolve()
    resolved_path = path.resolve()
    if not resolved_path.is_relative_to(resolved_run):
        raise ValueError(f"Artifact is outside run directory: {path}")
    return ArtifactRecord(
        path=resolved_path.relative_to(resolved_run).as_posix(),
        sha256=sha256_file(resolved_path),
        size_bytes=resolved_path.stat().st_size,
    )
