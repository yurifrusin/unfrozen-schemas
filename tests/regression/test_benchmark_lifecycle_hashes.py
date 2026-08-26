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
        "ad8d51beea8582ab88533d928e3fee91a7449f0424518da4e0360cfb9fa078e3"
    )
    assert items[0].model_visible_sha256 == (
        "2c0e44064cd0168b8d7bf93b21a28274f17e8df388b48b643d4b9d48ac9165e5"
    )
    assert answers[0].private_answer_record_sha256 == (
        "2410ad382661e343aa9866d616a300d9d2d5b55a412e54f03d866a7a453f7628"
    )
    assert items[0].exact_displayed_input_fingerprint_sha256 == (
        "01b00a5aadd302f0e9aab72032279f2b70ab8ea058cc3f32889b1dd597c6788e"
    )
    assert items[0].order_neutral_item_content_fingerprint_sha256 == (
        "d432c21c9ce5037cb3e4f4e124d83da37faca14b8c329fcec9f84469059c3a2f"
    )
    assert candidate.private_answer_bundle_sha256 == (
        "06347cb6ccea1e406efb8a5e5fa5c3336e1749f0836ebd1e685f08649c6eac0e"
    )
    assert candidate.quarantine_scope_sha256 == (
        "a06591a6eb3808f687f2a9f3ac9d5315cf0bef9d653714f30158e3ff65b8ac07"
    )
    assert candidate.candidate_bundle_root_sha256 == (
        "4cad3f2bc0d4696906ad8f1653350c59d73aeac88ec6db2473e809a349025243"
    )
    assert candidate.public_metadata_bundle_sha256 == (
        "fe5e99d452c7002aee635d7ef93dcbe3548d23244b8a1579957ac956b2768496"
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
        quarantine_scope_sha256="9" * 64,
        freeze_approval_sha256="5" * 64,
        codex_spec_sha256="6" * 64,
        git_commit="7" * 40,
        artifacts=(ArtifactRecord(path="items.jsonl", sha256="8" * 64, size_bytes=123),),
        frozen_manifest_sha256="0" * 64,
    )
    assert frozen_manifest_hash(provisional) == (
        "4055288eff1e25ed5bcd710e8ad2922b62175dc0aea4a6b994807127a6008a41"
    )
