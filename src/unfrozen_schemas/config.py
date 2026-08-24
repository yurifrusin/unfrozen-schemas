"""Validated, repository-relative configuration for Milestone 0."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from unfrozen_schemas.constants import SPECIFICATION_FILENAME


class ConfigLoadError(ValueError):
    """Raised when configuration cannot be loaded or resolved safely."""


class FrozenModel(BaseModel):
    """Base for immutable configuration models that reject unknown fields."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class RunConfig(FrozenModel):
    """Repository-relative run settings accepted from YAML."""

    name: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9-]*$")
    output_root: Path
    seed: int = Field(ge=0, le=4_294_967_295)
    device: Literal["cpu"]
    offline: Literal[True]
    requires_secret: Literal[False]
    engineering_only: Literal[True]


class LoggingConfig(FrozenModel):
    """Supported console and structured-log levels."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"


class SmokeConfig(FrozenModel):
    """Top-level experiment configuration before paths are resolved."""

    schema_version: Literal["1"]
    run: RunConfig
    model_config_path: Path = Field(alias="model_config")
    logging: LoggingConfig = LoggingConfig()


class TinyModelConfig(FrozenModel):
    """Local fixture declaration before paths are resolved."""

    schema_version: Literal["1"]
    model_type: Literal["tiny_linear_fixture"]
    fixture_path: Path
    expected_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class ResolvedRunConfig(FrozenModel):
    """Absolute, execution-ready run configuration."""

    name: str
    output_root: Path
    seed: int
    device: Literal["cpu"]
    offline: Literal[True]
    requires_secret: Literal[False]
    engineering_only: Literal[True]


class ResolvedModelConfig(FrozenModel):
    """Absolute, hash-pinned tiny-model configuration."""

    schema_version: Literal["1"]
    model_type: Literal["tiny_linear_fixture"]
    config_path: Path
    fixture_path: Path
    fixture_sha256: str


class ResolvedSmokeConfig(FrozenModel):
    """Fully resolved settings embedded in every run manifest."""

    schema_version: Literal["1"]
    source_config_path: Path
    repository_root: Path
    run: ResolvedRunConfig
    model: ResolvedModelConfig
    logging: LoggingConfig


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file without loading it all into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_repository_root(start: Path) -> Path:
    """Locate the Git root that also contains the immutable Revision 4 specification."""

    candidate = start.resolve()
    if candidate.is_file():
        candidate = candidate.parent
    for directory in (candidate, *candidate.parents):
        if (directory / ".git").exists() and (directory / SPECIFICATION_FILENAME).is_file():
            return directory
    raise ConfigLoadError(
        f"Could not find a Git repository containing {SPECIFICATION_FILENAME!r} from {start}"
    )


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ConfigLoadError(f"Configuration file does not exist: {path}")
    try:
        raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigLoadError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigLoadError(f"Configuration root must be a mapping: {path}")
    return {str(key): value for key, value in raw.items()}


def _repository_path(repository_root: Path, configured_path: Path, label: str) -> Path:
    resolved = (
        configured_path.resolve()
        if configured_path.is_absolute()
        else (repository_root / configured_path).resolve()
    )
    if not resolved.is_relative_to(repository_root):
        raise ConfigLoadError(f"{label} must remain inside the repository: {configured_path}")
    return resolved


def load_smoke_config(
    path: Path,
    *,
    output_root_override: Path | None = None,
    seed_override: int | None = None,
) -> ResolvedSmokeConfig:
    """Load, validate, resolve, and hash-check a Milestone 0 smoke configuration."""

    source_path = path.resolve()
    repository_root = find_repository_root(source_path)
    source = SmokeConfig.model_validate(_load_yaml_mapping(source_path))

    model_config_path = _repository_path(repository_root, source.model_config_path, "model_config")
    model_source = TinyModelConfig.model_validate(_load_yaml_mapping(model_config_path))
    fixture_path = _repository_path(
        repository_root, model_source.fixture_path, "model.fixture_path"
    )
    if not fixture_path.is_file():
        raise ConfigLoadError(f"Tiny model fixture does not exist: {fixture_path}")
    observed_hash = sha256_file(fixture_path)
    if observed_hash != model_source.expected_sha256:
        raise ConfigLoadError(
            "Tiny model fixture hash mismatch: "
            f"expected {model_source.expected_sha256}, observed {observed_hash}"
        )

    if seed_override is not None and not 0 <= seed_override <= 4_294_967_295:
        raise ConfigLoadError("Seed override must be between 0 and 4294967295")

    output_root = (
        output_root_override.resolve()
        if output_root_override is not None
        else _repository_path(repository_root, source.run.output_root, "run.output_root")
    )
    resolved_seed = source.run.seed if seed_override is None else seed_override

    return ResolvedSmokeConfig(
        schema_version=source.schema_version,
        source_config_path=source_path,
        repository_root=repository_root,
        run=ResolvedRunConfig(
            name=source.run.name,
            output_root=output_root,
            seed=resolved_seed,
            device=source.run.device,
            offline=source.run.offline,
            requires_secret=source.run.requires_secret,
            engineering_only=source.run.engineering_only,
        ),
        model=ResolvedModelConfig(
            schema_version=model_source.schema_version,
            model_type=model_source.model_type,
            config_path=model_config_path,
            fixture_path=fixture_path,
            fixture_sha256=observed_hash,
        ),
        logging=source.logging,
    )
