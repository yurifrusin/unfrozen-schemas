"""Strict, repository-relative configuration for M2.2 literal authoring."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import Field, model_validator

from unfrozen_schemas.config import ConfigLoadError, FrozenModel, find_repository_root
from unfrozen_schemas.evaluation.literal_models import (
    LiteralSchema,
    LiteralTaskFamily,
    LiteralTransferLevel,
)


class LiteralCoverageConfig(FrozenModel):
    minimum_semantic_groups: int = Field(ge=1)
    records_per_group: Literal[2] = 2
    required_schemas: tuple[LiteralSchema, ...]
    required_levels: tuple[LiteralTransferLevel, ...]
    required_task_families: tuple[LiteralTaskFamily, ...]
    minimum_groups_per_schema: int = Field(ge=1)
    minimum_groups_per_schema_level: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_unique_requirements(self) -> LiteralCoverageConfig:
        for field_name in ("required_schemas", "required_levels", "required_task_families"):
            values = getattr(self, field_name)
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} must be unique")
        return self


class LiteralExecutionConfig(FrozenModel):
    device: Literal["cpu"] = "cpu"
    offline: Literal[True] = True
    network_access: Literal[False] = False
    model_access: Literal[False] = False
    gpu_access: Literal[False] = False
    requires_secret: Literal[False] = False


class LiteralConfig(FrozenModel):
    schema_version: Literal["1"]
    candidate_version: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    purpose: Literal["outcome", "engineering"]
    environment_version: Literal["schemaworld-core-v1"] = "schemaworld-core-v1"
    generator_version: Literal["literal-generator-v1"] = "literal-generator-v1"
    partition_plan_version: Literal["literal-partition-plan-v1"] = "literal-partition-plan-v1"
    authoring_manifest: str = Field(min_length=1)
    source_root: str = Field(min_length=1)
    candidate_root: str = Field(min_length=1)
    review_root: str = Field(min_length=1)
    generation_seeds: tuple[int, ...] = Field(min_length=1)
    coverage: LiteralCoverageConfig
    execution: LiteralExecutionConfig
    engineering_only: bool
    scientific_eligible: bool
    promotable: bool

    @model_validator(mode="after")
    def validate_classification(self) -> LiteralConfig:
        if self.purpose == "engineering":
            if not self.engineering_only or self.scientific_eligible or self.promotable:
                raise ValueError("Engineering literal configuration must be non-scientific")
        elif self.engineering_only:
            raise ValueError("Outcome literal configuration cannot be engineering-only")
        if len(self.generation_seeds) != len(set(self.generation_seeds)):
            raise ValueError("Literal candidate generation seeds must be unique")
        return self


class ResolvedLiteralConfig(LiteralConfig):
    source_config_path: str


@dataclass(frozen=True, slots=True)
class LoadedLiteralConfig:
    resolved: ResolvedLiteralConfig
    repository_root: Path
    authoring_manifest: Path
    source_root: Path
    candidate_root: Path
    review_root: Path


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ConfigLoadError(f"Literal configuration file does not exist: {path}")
    try:
        value: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigLoadError(f"Invalid literal YAML in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ConfigLoadError("Literal configuration root must be a mapping")
    return {str(key): item for key, item in value.items()}


def _resolve_repository_path(repository_root: Path, value: str, *, label: str) -> Path:
    configured = Path(value)
    if configured.is_absolute():
        raise ConfigLoadError(f"Tracked {label} must be repository-relative")
    resolved = (repository_root / configured).resolve()
    if not resolved.is_relative_to(repository_root):
        raise ConfigLoadError(f"Tracked {label} must remain inside the repository")
    return resolved


def load_literal_config(
    path: Path,
    *,
    source_root_override: Path | None = None,
    candidate_root_override: Path | None = None,
    review_root_override: Path | None = None,
) -> LoadedLiteralConfig:
    source_path = path.resolve()
    repository_root = find_repository_root(Path.cwd())
    config = LiteralConfig.model_validate(_load_yaml(source_path))
    try:
        relative_source = source_path.relative_to(repository_root).as_posix()
    except ValueError as exc:
        raise ConfigLoadError("Literal configuration must reside inside the repository") from exc

    authoring = _resolve_repository_path(
        repository_root, config.authoring_manifest, label="authoring_manifest"
    )
    default_source = _resolve_repository_path(
        repository_root, config.source_root, label="source_root"
    )
    default_candidate = _resolve_repository_path(
        repository_root, config.candidate_root, label="candidate_root"
    )
    default_review = _resolve_repository_path(
        repository_root, config.review_root, label="review_root"
    )
    if not config.engineering_only and any(
        value is not None
        for value in (source_root_override, candidate_root_override, review_root_override)
    ):
        raise ConfigLoadError("Non-engineering literal paths cannot be overridden")
    source_root = source_root_override.resolve() if source_root_override else default_source
    candidate_root = (
        candidate_root_override.resolve() if candidate_root_override else default_candidate
    )
    review_root = review_root_override.resolve() if review_root_override else default_review

    expected_source = repository_root / "benchmarks" / "source" / config.candidate_version
    expected_review = repository_root / "reports" / "private" / config.candidate_version
    if config.purpose == "outcome":
        expected_candidate = repository_root / "benchmarks" / "private" / config.candidate_version
        if source_root != expected_source.resolve():
            raise ConfigLoadError("Outcome literal source_root must use the canonical source path")
        if candidate_root != expected_candidate.resolve():
            raise ConfigLoadError(
                "Outcome literal candidate_root must use the canonical private path"
            )
        if review_root != expected_review.resolve():
            raise ConfigLoadError("Outcome literal review_root must use the canonical private path")

    return LoadedLiteralConfig(
        resolved=ResolvedLiteralConfig(**config.model_dump(), source_config_path=relative_source),
        repository_root=repository_root,
        authoring_manifest=authoring,
        source_root=source_root,
        candidate_root=candidate_root,
        review_root=review_root,
    )
