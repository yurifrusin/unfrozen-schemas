"""Offline CPU integration coverage for the complete M2.2 engineering pipeline."""

from __future__ import annotations

import socket
from pathlib import Path

import pytest

from unfrozen_schemas.evaluation.benchmark_lifecycle import build_benchmark
from unfrozen_schemas.evaluation.benchmark_models import BenchmarkPurpose
from unfrozen_schemas.evaluation.benchmark_validation import validate_benchmark_manifest
from unfrozen_schemas.evaluation.literal_generation import generate_literal_source
from unfrozen_schemas.evaluation.literal_models import (
    LiteralCandidateManifest,
    LiteralReviewManifest,
)
from unfrozen_schemas.evaluation.literal_review import (
    build_literal_review,
    validate_literal_benchmark,
    validate_literal_review,
)
from unfrozen_schemas.evaluation.literal_validation import (
    LoadedLiteralSource,
    load_literal_source,
)
from unfrozen_schemas.literal_config import load_literal_config


@pytest.fixture
def literal_pipeline(
    tmp_path: Path,
    clean_benchmark_repository: Path,
    literal_pipeline_source: LoadedLiteralSource,
) -> tuple[Path, Path, Path, LiteralCandidateManifest, LiteralReviewManifest]:
    source = literal_pipeline_source.root
    candidate = tmp_path / "literal-candidate"
    result = build_benchmark(
        source_directory=source,
        output_directory=candidate,
        version="engineering-literal-fixture-v1",
        purpose=BenchmarkPurpose.ENGINEERING,
        repository_root=clean_benchmark_repository,
    )
    assert result.manifest_path is not None
    manifest_path = Path(result.manifest_path)
    validate_benchmark_manifest(manifest_path)
    composite = validate_literal_benchmark(
        source_root=source,
        candidate_manifest_path=manifest_path,
        repository_root=clean_benchmark_repository,
    )
    review = tmp_path / "literal-review"
    build_literal_review(source_root=source, output_root=review)
    review_manifest = validate_literal_review(review_root=review, source_root=source)
    return source, candidate, review, composite, review_manifest


def test_complete_literal_pipeline_and_regression_hashes(
    literal_pipeline: tuple[Path, Path, Path, LiteralCandidateManifest, LiteralReviewManifest],
) -> None:
    source, candidate, review, composite, review_manifest = literal_pipeline
    assert source.is_dir() and candidate.is_dir() and review.is_dir()
    assert composite.semantic_group_count == 8
    assert composite.source_item_count == 16
    assert composite.partition_plan_sha256 == (
        "c16938eb5904f9452f9109d03c5b2844db1141c5bb45a7fe22113b29d0e81eb7"
    )
    assert composite.template_registry_sha256 == (
        "7e75caf0a77644d64023069d3cac6af60c7f80bb6f763628f73b1038b1988e48"
    )
    assert composite.witness_bundle_sha256 == (
        "0b136f5ca8a55f2a90df252125085ab46c17acb00c9953bb0388c7db3f8822b0"
    )
    loaded = load_literal_source(source)
    assert loaded.witness_bundle.witnesses[0].witness_sha256 == (
        "dae73ddebe7fd8776b35cff8342c08c3bc3b9ff785880611d98ebb752f289662"
    )
    assert composite.literal_validation_report_sha256 == (
        "88223ab07943cb7d080f01f1b49af9836fc4c02a78269963435f2a1f2a8f19f8"
    )
    assert composite.literal_candidate_root_sha256 == (
        "5c6aa8878dc57eacfc5ef26f150c7674784c1a2269b78c9de55c32c84ddf084f"
    )
    assert review_manifest.review_manifest_sha256 == (
        "4f021707f6683fe8a8942637aee4ebedb2724d8ad724b757a72231ce97aa984b"
    )


def test_source_generation_is_deterministic_and_refuses_overwrite(tmp_path: Path) -> None:
    identities = []
    for name in ("one", "two"):
        source = tmp_path / name
        config = load_literal_config(
            Path("configs/evaluation/m2_2_literal_smoke.yaml"),
            source_root_override=source,
            candidate_root_override=tmp_path / f"{name}-candidate",
            review_root_override=tmp_path / f"{name}-review",
        )
        result = generate_literal_source(config)
        loaded = load_literal_source(source)
        identities.append(
            (
                result.partition_plan_sha256,
                result.template_registry_sha256,
                result.witness_bundle_sha256,
                loaded.source_bundle.literal_source_bundle_sha256,
            )
        )
        with pytest.raises(Exception, match="generated files"):
            generate_literal_source(config)
    assert identities[0] == identities[1]


def test_pipeline_never_attempts_network_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse_network(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "create_connection", refuse_network)
    source = tmp_path / "offline-source"
    config = load_literal_config(
        Path("configs/evaluation/m2_2_literal_smoke.yaml"),
        source_root_override=source,
        candidate_root_override=tmp_path / "offline-candidate",
        review_root_override=tmp_path / "offline-review",
    )
    result = generate_literal_source(config)
    assert result.semantic_group_count == 8


def test_review_artifact_mutation_is_rejected(
    literal_pipeline: tuple[Path, Path, Path, LiteralCandidateManifest, LiteralReviewManifest],
) -> None:
    source, _candidate, review, _composite, _review_manifest = literal_pipeline
    checklist = review / "reviewer_checklist.md"
    checklist.write_text(checklist.read_text(encoding="utf-8") + "mutation\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"Artifact (size|SHA-256) mismatch"):
        validate_literal_review(review_root=review, source_root=source)
