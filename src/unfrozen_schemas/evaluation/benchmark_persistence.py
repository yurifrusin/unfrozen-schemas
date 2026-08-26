"""Canonical JSONL persistence and safe artifact-path handling for M2.1."""

from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, TypeVar

from pydantic import BaseModel

from unfrozen_schemas.config import sha256_file
from unfrozen_schemas.evaluation.benchmark_hashing import canonical_logical_bytes
from unfrozen_schemas.evaluation.benchmark_models import SLUG_PATTERN, BenchmarkPurpose
from unfrozen_schemas.provenance import ArtifactRecord

ModelT = TypeVar("ModelT", bound=BaseModel)


def validate_benchmark_version(version: str) -> str:
    """Validate one path-safe benchmark-version slug before any path construction."""

    if not version or not re.fullmatch(SLUG_PATTERN, version):
        raise ValueError(
            "Benchmark version must be a non-empty lowercase slug containing only "
            "letters, digits, dot, underscore, or hyphen"
        )
    posix = PurePosixPath(version)
    windows = PureWindowsPath(version)
    if (
        posix.is_absolute()
        or windows.is_absolute()
        or windows.drive
        or len(posix.parts) != 1
        or len(windows.parts) != 1
        or version in {".", ".."}
        or "/" in version
        or "\\" in version
    ):
        raise ValueError("Benchmark version must be exactly one safe path component")
    return version


def resolve_version_path(repository_root: Path, area: str, version: str) -> Path:
    """Resolve a version directory below one canonical lifecycle storage area."""

    if area not in {"private", "selection", "frozen"}:
        raise ValueError(f"Unsupported benchmark version area: {area}")
    safe_version = validate_benchmark_version(version)
    base = (repository_root.resolve() / "benchmarks" / area).resolve()
    resolved = (base / safe_version).resolve()
    if resolved.parent != base:
        raise ValueError(f"Benchmark version path escapes benchmarks/{area}: {version}")
    return resolved


def resolve_candidate_version_path(
    repository_root: Path,
    version: str,
    purpose: BenchmarkPurpose,
) -> Path:
    """Resolve the one canonical PRIVATE candidate directory for a scientific purpose."""

    if purpose is BenchmarkPurpose.SELECTION:
        area = "selection"
    elif purpose in {BenchmarkPurpose.OUTCOME, BenchmarkPurpose.RETENTION}:
        area = "private"
    else:
        raise ValueError("Engineering candidates do not have a canonical repository destination")
    return resolve_version_path(repository_root, area, version)


def resolve_frozen_version_path(
    repository_root: Path,
    version: str,
    purpose: BenchmarkPurpose,
) -> Path:
    """Resolve the canonical frozen directory for an otherwise authorised purpose."""

    if purpose is BenchmarkPurpose.SELECTION:
        raise ValueError("SELECTION-purpose freezing is refused throughout M2.1")
    if purpose is BenchmarkPurpose.ENGINEERING:
        raise ValueError("Engineering fixtures do not have a canonical repository destination")
    return resolve_version_path(repository_root, "frozen", version)


def write_canonical_json(path: Path, value: BaseModel | dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_logical_bytes(value))


def read_canonical_model(path: Path, model_type: type[ModelT]) -> ModelT:
    payload = path.read_bytes()
    value = model_type.model_validate_json(payload)
    if canonical_logical_bytes(value) != payload:
        raise ValueError(f"Non-canonical JSON encoding: {path.name}")
    return value


def write_canonical_jsonl(path: Path, values: list[BaseModel]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"".join(canonical_logical_bytes(value) for value in values))


def read_jsonl_models(
    path: Path, model_type: type[ModelT], *, require_canonical: bool
) -> tuple[ModelT, ...]:
    payload = path.read_bytes()
    if not payload:
        raise ValueError(f"JSONL file is empty: {path.name}")
    if not payload.endswith(b"\n"):
        raise ValueError(f"JSONL file must end with a newline: {path.name}")
    result: list[ModelT] = []
    for index, line in enumerate(payload.splitlines(keepends=True), start=1):
        if not line.strip():
            raise ValueError(f"Blank JSONL line at {path.name}:{index}")
        try:
            value = model_type.model_validate(json.loads(line.decode("utf-8")))
        except Exception as exc:
            raise ValueError(
                f"Invalid {model_type.__name__} at {path.name}:{index}: {exc}"
            ) from exc
        if require_canonical and canonical_logical_bytes(value) != line:
            raise ValueError(f"Non-canonical JSONL record at {path.name}:{index}")
        result.append(value)
    return tuple(result)


def resolve_safe_relative_path(root: Path, declared: str, *, must_exist: bool = True) -> Path:
    if not declared or "\\" in declared or "//" in declared:
        raise ValueError("Artifact path must be a canonical non-empty POSIX relative path")
    posix = PurePosixPath(declared)
    windows = PureWindowsPath(declared)
    if posix.is_absolute() or windows.is_absolute() or windows.drive:
        raise ValueError(f"Artifact path must not be absolute or drive-qualified: {declared}")
    if posix.as_posix() != declared or any(part in {"", ".", ".."} for part in posix.parts):
        raise ValueError(
            f"Artifact path contains non-canonical or traversal components: {declared}"
        )
    resolved_root = root.resolve()
    path = resolved_root.joinpath(*posix.parts)
    resolved = path.resolve(strict=must_exist)
    if not resolved.is_relative_to(resolved_root):
        raise ValueError(f"Artifact path escapes its declared root: {declared}")
    return resolved


def make_artifact_records(root: Path, paths: list[Path]) -> tuple[ArtifactRecord, ...]:
    resolved_root = root.resolve()
    records: list[ArtifactRecord] = []
    for path in sorted(paths, key=lambda value: value.as_posix()):
        resolved = path.resolve(strict=True)
        if not resolved.is_relative_to(resolved_root):
            raise ValueError(f"Artifact is outside benchmark root: {path}")
        records.append(
            ArtifactRecord(
                path=resolved.relative_to(resolved_root).as_posix(),
                sha256=sha256_file(resolved),
                size_bytes=resolved.stat().st_size,
            )
        )
    return tuple(records)


def verify_artifact_records(
    root: Path, records: tuple[ArtifactRecord, ...], *, expected_paths: set[str]
) -> None:
    declared = [record.path for record in records]
    if len(declared) != len(set(declared)):
        raise ValueError("Artifact manifest contains duplicate paths")
    if set(declared) != expected_paths:
        raise ValueError(
            "Artifact set mismatch; "
            f"missing={sorted(expected_paths - set(declared))}, "
            f"unexpected={sorted(set(declared) - expected_paths)}"
        )
    if declared != sorted(declared):
        raise ValueError("Artifact records must use canonical path ordering")
    for record in records:
        path = resolve_safe_relative_path(root, record.path)
        if not path.is_file():
            raise ValueError(f"Declared artifact is not a regular file: {record.path}")
        if path.stat().st_size != record.size_bytes:
            raise ValueError(f"Artifact size mismatch: {record.path}")
        observed = sha256_file(path)
        if observed != record.sha256:
            raise ValueError(f"Artifact SHA-256 mismatch: {record.path}")
