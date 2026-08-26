"""Shared M2.1 test fixtures with clean, isolated Git provenance."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from unfrozen_schemas.evaluation.benchmark_lifecycle import build_benchmark
from unfrozen_schemas.evaluation.benchmark_models import BenchmarkPurpose, CandidateManifest
from unfrozen_schemas.evaluation.benchmark_validation import validate_benchmark_manifest


@pytest.fixture
def engineering_source() -> Path:
    return Path("tests/fixtures/benchmark_lifecycle/source").resolve()


@pytest.fixture
def clean_benchmark_repository(tmp_path: Path) -> Path:
    repository = tmp_path / "provenance-repository"
    repository.mkdir()
    for relative in (
        "benchmarks/frozen",
        "benchmarks/private",
        "benchmarks/selection",
    ):
        repository.joinpath(relative).mkdir(parents=True)
    shutil.copyfile(Path("CODEX_SPEC.md"), repository / "CODEX_SPEC.md")
    subprocess.run(["git", "init"], cwd=repository, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "benchmark-tests@example.invalid"],
        cwd=repository,
        check=True,
    )
    subprocess.run(["git", "config", "user.name", "Benchmark Tests"], cwd=repository, check=True)
    subprocess.run(["git", "add", "CODEX_SPEC.md"], cwd=repository, check=True)
    subprocess.run(
        ["git", "commit", "-m", "test provenance"],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    return repository


@pytest.fixture
def built_candidate(
    tmp_path: Path, engineering_source: Path, clean_benchmark_repository: Path
) -> tuple[Path, CandidateManifest, Path]:
    output = tmp_path / "candidate"
    result = build_benchmark(
        source_directory=engineering_source,
        output_directory=output,
        version="engineering-benchmark-lifecycle-v1",
        purpose=BenchmarkPurpose.ENGINEERING,
        repository_root=clean_benchmark_repository,
    )
    assert result.manifest_path is not None
    manifest_path = Path(result.manifest_path)
    manifest = validate_benchmark_manifest(manifest_path)
    assert isinstance(manifest, CandidateManifest)
    return manifest_path, manifest, clean_benchmark_repository
