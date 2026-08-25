"""Strict configuration for SchemaWorld Core generation and replay."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import Field

from unfrozen_schemas.codecs.opaque_tokens import CODEC_VERSION
from unfrozen_schemas.config import ConfigLoadError, FrozenModel, find_repository_root
from unfrozen_schemas.envs.schema_world.dynamics import TRANSITION_STAGE_ORDER
from unfrozen_schemas.envs.schema_world.renderer import RENDERER_VERSION
from unfrozen_schemas.envs.schema_world.rng import GENERATOR_ALGORITHM, GENERATOR_VERSION
from unfrozen_schemas.envs.schema_world.templates import TemplateFamily


class CoreEnvironmentConfig(FrozenModel):
    environment_version: Literal["schemaworld-core-v1"] = "schemaworld-core-v1"
    coordinate_unit: Literal["microunit"] = "microunit"
    coordinate_min: Literal[0] = 0
    coordinate_max: Literal[10_000] = 10_000
    fixed_point_scale: Literal[1] = 1
    gravity_per_step: int = Field(le=0)
    max_steps: int = Field(gt=0)
    transition_stage_order: tuple[str, ...]


class CoreGeneratorConfig(FrozenModel):
    algorithm: Literal["splitmix64"] = GENERATOR_ALGORITHM
    version: Literal["1"] = GENERATOR_VERSION
    seeds: tuple[int, ...] = Field(min_length=1)
    noise_seed_offset: int = Field(ge=1)


class CoreCodecConfig(FrozenModel):
    version: Literal["opaque-byte-v1"] = CODEC_VERSION


class CoreRendererConfig(FrozenModel):
    version: Literal["schemaworld-raster-v1"] = RENDERER_VERSION
    width: int = Field(gt=0, le=1024)
    height: int = Field(gt=0, le=1024)


class CoreRunConfig(FrozenModel):
    name: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9-]*$")
    output_root: str = Field(min_length=1)
    device: Literal["cpu"]
    offline: Literal[True]
    requires_secret: Literal[False]
    engineering_only: Literal[True]


class CoreConfig(FrozenModel):
    schema_version: Literal["1"]
    run: CoreRunConfig
    environment: CoreEnvironmentConfig
    generator: CoreGeneratorConfig
    template_families: tuple[TemplateFamily, ...] = Field(min_length=1)
    codec: CoreCodecConfig
    renderer: CoreRendererConfig


class ResolvedCoreConfig(CoreConfig):
    source_config_path: str


@dataclass(frozen=True, slots=True)
class LoadedCoreConfig:
    resolved: ResolvedCoreConfig
    repository_root: Path
    output_root: Path


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ConfigLoadError(f"Core configuration file does not exist: {path}")
    try:
        value: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigLoadError(f"Invalid core YAML in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ConfigLoadError("Core configuration root must be a mapping")
    return {str(key): item for key, item in value.items()}


def load_core_config(path: Path, *, output_root_override: Path | None = None) -> LoadedCoreConfig:
    source_path = path.resolve()
    repository_root = find_repository_root(Path.cwd())
    config = CoreConfig.model_validate(_load_yaml(source_path))
    if config.environment.transition_stage_order != TRANSITION_STAGE_ORDER:
        raise ConfigLoadError(
            "Core transition_stage_order must exactly match the frozen M1 operational contract"
        )
    if len(set(config.generator.seeds)) != len(config.generator.seeds):
        raise ConfigLoadError("Core generator seeds must be unique")
    if len(set(config.template_families)) != len(config.template_families):
        raise ConfigLoadError("Core template families must be unique")
    configured_output = Path(config.run.output_root)
    if configured_output.is_absolute():
        raise ConfigLoadError("Tracked core output_root must be repository-relative")
    default_output = (repository_root / configured_output).resolve()
    if not default_output.is_relative_to(repository_root):
        raise ConfigLoadError("Tracked core output_root must remain inside the repository")
    output_root = output_root_override.resolve() if output_root_override else default_output
    try:
        relative_source = source_path.relative_to(repository_root).as_posix()
    except ValueError as exc:
        raise ConfigLoadError("Core configuration must reside inside the repository") from exc
    resolved = ResolvedCoreConfig(
        **config.model_dump(),
        source_config_path=relative_source,
    )
    return LoadedCoreConfig(
        resolved=resolved,
        repository_root=repository_root,
        output_root=output_root,
    )
