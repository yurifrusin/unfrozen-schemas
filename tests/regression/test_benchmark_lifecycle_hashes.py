"""Pinned cross-platform canonical logical identities for the M2.1 engineering fixture."""

from __future__ import annotations

from pathlib import Path

from unfrozen_schemas.evaluation.benchmark_hashing import frozen_manifest_hash
from unfrozen_schemas.evaluation.benchmark_models import (
    BenchmarkPurpose,
    BuiltBenchmarkItem,
    CandidateManifest,
    FrozenManifest,
    PrivateAnswerRecord,
    SourceSnapshot,
)
from unfrozen_schemas.evaluation.benchmark_persistence import (
    read_canonical_model,
    read_jsonl_models,
)
from unfrozen_schemas.evaluation.benchmark_validation import validate_benchmark_manifest
from unfrozen_schemas.provenance import ArtifactRecord


def test_engineering_fixture_logical_regression_hashes(
    built_candidate: tuple[Path, CandidateManifest, Path],
) -> None:
    manifest_path, candidate, _ = built_candidate
    validated = validate_benchmark_manifest(manifest_path)
    assert isinstance(validated, CandidateManifest)
    assert validated.purpose is BenchmarkPurpose.ENGINEERING
    snapshot = read_canonical_model(manifest_path.parent / "source_snapshot.json", SourceSnapshot)
    items = read_jsonl_models(
        manifest_path.parent / "items.jsonl", BuiltBenchmarkItem, require_canonical=True
    )
    answers = read_jsonl_models(
        manifest_path.parent / "private_answers.jsonl",
        PrivateAnswerRecord,
        require_canonical=True,
    )
    assert snapshot.source_snapshot_sha256 == (
        "983cfab2c885718e828eec131f3c10b52a29608f10e16344ab1c37245acede54"
    )
    assert items[0].model_visible_sha256 == (
        "2c0e44064cd0168b8d7bf93b21a28274f17e8df388b48b643d4b9d48ac9165e5"
    )
    assert answers[0].private_answer_record_sha256 == (
        "2410ad382661e343aa9866d616a300d9d2d5b55a412e54f03d866a7a453f7628"
    )
    assert candidate.candidate_bundle_root_sha256 == (
        "bf9a798de640766ae410f683f01edd8e51dd7e3ba991b650e261094225b66e32"
    )
    assert candidate.public_metadata_bundle_sha256 == (
        "1c12719cd84e110ffc4494d3f3c4b2a836c2134232c47549798924b293292567"
    )


def test_frozen_manifest_logical_hash_domain_regression() -> None:
    provisional = FrozenManifest(
        benchmark_version="engineering-benchmark-lifecycle-v1",
        purpose=BenchmarkPurpose.ENGINEERING,
        engineering_only=True,
        scientific_eligible=False,
        promotable=False,
        item_count=2,
        candidate_manifest_sha256="1" * 64,
        candidate_bundle_root_sha256="2" * 64,
        private_answer_bundle_sha256="3" * 64,
        public_metadata_bundle_sha256="4" * 64,
        freeze_approval_sha256="5" * 64,
        codex_spec_sha256="6" * 64,
        git_commit="7" * 40,
        artifacts=(ArtifactRecord(path="items.jsonl", sha256="8" * 64, size_bytes=123),),
        frozen_manifest_sha256="0" * 64,
    )
    assert frozen_manifest_hash(provisional) == (
        "e52723e10f03bf446ec527c6045b2796e6042211db6dd8654b14f4519a9b0935"
    )
