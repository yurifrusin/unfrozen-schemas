"""Offline CPU integration coverage for the corrected M2.2 pipeline."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from PIL import Image
from pydantic import ValidationError
from typer.testing import CliRunner

from unfrozen_schemas.cli import app
from unfrozen_schemas.config import ConfigLoadError
from unfrozen_schemas.envs.schema_world.renderer import BACKGROUND
from unfrozen_schemas.evaluation.benchmark_lifecycle import build_benchmark
from unfrozen_schemas.evaluation.benchmark_models import BenchmarkPurpose
from unfrozen_schemas.evaluation.benchmark_persistence import (
    make_artifact_records,
    read_canonical_model,
    read_jsonl_models,
    write_canonical_json,
)
from unfrozen_schemas.evaluation.benchmark_validation import validate_benchmark_manifest
from unfrozen_schemas.evaluation.literal_generation import generate_literal_source
from unfrozen_schemas.evaluation.literal_hashing import (
    operation_hash,
    review_manifest_hash,
)
from unfrozen_schemas.evaluation.literal_models import (
    LiteralAuditStatus,
    LiteralCandidateManifest,
    LiteralCueDispositionRecord,
    LiteralLexicalCategory,
    LiteralOperationError,
    LiteralOperationRecord,
    LiteralReviewItem,
    LiteralReviewManifest,
    LiteralSourceBundleManifest,
)
from unfrozen_schemas.evaluation.literal_review import (
    build_literal_review,
    materialize_literal_candidate,
    validate_literal_benchmark,
    validate_literal_review,
)
from unfrozen_schemas.evaluation.literal_validation import (
    CANDIDATE_MATERIALIZATION_OPERATION_FILE,
    CANDIDATE_VALIDATION_REPORT_FILE,
    COMPOSITE_CANDIDATE_FILE,
    GENERATION_OPERATION_FILE,
    LITERAL_DIRECTORY,
    LoadedLiteralSource,
    load_literal_source,
    validate_literal_source,
)
from unfrozen_schemas.literal_config import load_literal_config

Pipeline = tuple[
    Path,
    Path,
    Path,
    Path,
    LiteralCandidateManifest,
    LiteralReviewManifest,
]


@pytest.fixture
def materialized_pipeline(
    tmp_path: Path,
    clean_benchmark_repository: Path,
    literal_pipeline_source: LoadedLiteralSource,
) -> tuple[Path, Path, Path, LiteralCandidateManifest]:
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
    composite = materialize_literal_candidate(
        source_root=source,
        candidate_manifest_path=manifest_path,
        repository_root=clean_benchmark_repository,
    )
    assert (
        validate_literal_benchmark(
            source_root=source,
            candidate_manifest_path=manifest_path,
            repository_root=clean_benchmark_repository,
        )
        == composite
    )
    return source, candidate, manifest_path, composite


@pytest.fixture
def literal_pipeline(
    materialized_pipeline: tuple[Path, Path, Path, LiteralCandidateManifest], tmp_path: Path
) -> Pipeline:
    source, candidate, manifest_path, composite = materialized_pipeline
    review = tmp_path / "literal-review"
    build_literal_review(source_root=source, output_root=review)
    review_manifest = validate_literal_review(review_root=review, source_root=source)
    return source, candidate, manifest_path, review, composite, review_manifest


def _file_snapshot(root: Path) -> dict[str, tuple[int, int, int]]:
    return {
        path.relative_to(root).as_posix(): (
            path.stat().st_size,
            path.stat().st_mtime_ns,
            path.stat().st_ctime_ns,
        )
        for path in root.rglob("*")
        if path.is_file()
    }


def test_complete_pipeline_and_regression_hashes(literal_pipeline: Pipeline) -> None:
    source, candidate, _manifest_path, review, composite, review_manifest = literal_pipeline
    assert source.is_dir() and candidate.is_dir() and review.is_dir()
    assert composite.semantic_group_count == 8
    assert composite.source_item_count == 16
    assert composite.authoring_snapshot_sha256 == (
        "a85ded9dfa0c06da369699bb0d6bef5ff84221d477dc4af43034acb4821bef6d"
    )
    assert composite.m2_1_candidate_bundle_root_sha256 == (
        "dfd0594922338cd9ec86a9ef33f223f5da46867df658cb9c8e1d94ccd147e487"
    )
    assert composite.partition_plan_sha256 == (
        "5a2dc4f21978825fc744132f72d155b86ca7fe84395da95553ec77319f8cf9a1"
    )
    assert composite.template_registry_sha256 == (
        "d320923aaa794cc901d3f60215726ed157d7b3830d787a4aff545f78ce09a346"
    )
    assert composite.witness_bundle_sha256 == (
        "da7484f22355d3ebe380e2fea2493e67383338478e215c75944f5f14f6889092"
    )
    assert composite.literal_validation_report_sha256 == (
        "b60a2ec455ab39f773f7dc645e7a9321d75a98e1e7943680e4552ccff12b0a2c"
    )
    assert composite.literal_candidate_root_sha256 == (
        "69a92b6122679dd580cfcd93fc522f85b21f6ed2af34d1107ccceb78cffcb32a"
    )
    assert review_manifest.review_operation_sha256
    assert review_manifest.review_manifest_sha256 == (
        "c753f953cabd0919241564a90b3d97026b2c48127e76b3b8be9dac6d170abdef"
    )
    assert len(review_manifest.render_records) == 8 * composite.semantic_group_count
    assert len({record.path for record in review_manifest.render_records}) == 64
    assert (
        sum(
            record.view_kind == "scientific-full-frame" for record in review_manifest.render_records
        )
        == 32
    )
    assert sum(record.view_kind == "review-zoom" for record in review_manifest.render_records) == 32
    assert all(
        record.scientific_render_sha256 is not None
        and record.source_full_frame_raw_pixel_sha256 is None
        for record in review_manifest.render_records
        if record.view_kind == "scientific-full-frame"
    )
    assert all(
        record.scientific_render_sha256 is None
        and record.source_full_frame_raw_pixel_sha256 is not None
        for record in review_manifest.render_records
        if record.view_kind == "review-zoom"
    )


def test_validation_is_strictly_read_only(
    materialized_pipeline: tuple[Path, Path, Path, LiteralCandidateManifest],
    clean_benchmark_repository: Path,
) -> None:
    source, _candidate, manifest_path, composite = materialized_pipeline
    before = _file_snapshot(source)
    assert (
        validate_literal_benchmark(
            source_root=source,
            candidate_manifest_path=manifest_path,
            repository_root=clean_benchmark_repository,
        )
        == composite
    )
    assert _file_snapshot(source) == before
    with pytest.raises(FileExistsError, match="write-once"):
        materialize_literal_candidate(
            source_root=source,
            candidate_manifest_path=manifest_path,
            repository_root=clean_benchmark_repository,
        )


def test_source_operation_rejects_extra_input_key_after_hash_refresh(
    literal_pipeline_source: LoadedLiteralSource,
) -> None:
    source = literal_pipeline_source.root
    literal_root = source / LITERAL_DIRECTORY
    operation_path = literal_root / GENERATION_OPERATION_FILE
    bundle_path = literal_root / "literal_source_bundle.json"
    operation = read_canonical_model(operation_path, LiteralOperationRecord)
    provisional = operation.model_copy(
        update={
            "input_hashes": {**operation.input_hashes, "unexpected_sha256": "0" * 64},
            "operation_sha256": "0" * 64,
        }
    )
    changed = provisional.model_copy(update={"operation_sha256": operation_hash(provisional)})
    write_canonical_json(operation_path, changed)
    bundle = read_canonical_model(bundle_path, LiteralSourceBundleManifest)
    write_canonical_json(
        bundle_path,
        bundle.model_copy(update={"source_generation_operation_sha256": changed.operation_sha256}),
    )
    with pytest.raises(ValueError, match="operation provenance is inconsistent"):
        validate_literal_source(source)


def test_candidate_operation_rejects_extra_output_key_after_hash_refresh(
    materialized_pipeline: tuple[Path, Path, Path, LiteralCandidateManifest],
    clean_benchmark_repository: Path,
) -> None:
    source, _candidate, manifest_path, _composite = materialized_pipeline
    operation_path = source / LITERAL_DIRECTORY / CANDIDATE_MATERIALIZATION_OPERATION_FILE
    operation = read_canonical_model(operation_path, LiteralOperationRecord)
    provisional = operation.model_copy(
        update={
            "output_hashes": {**operation.output_hashes, "unexpected_sha256": "0" * 64},
            "operation_sha256": "0" * 64,
        }
    )
    write_canonical_json(
        operation_path,
        provisional.model_copy(update={"operation_sha256": operation_hash(provisional)}),
    )
    with pytest.raises(ValueError, match="operation provenance is inconsistent"):
        validate_literal_benchmark(
            source_root=source,
            candidate_manifest_path=manifest_path,
            repository_root=clean_benchmark_repository,
        )


def test_review_operation_rejects_extra_input_key_after_full_manifest_refresh(
    literal_pipeline: Pipeline,
) -> None:
    source, _candidate, _manifest, review, _composite, _review_manifest = literal_pipeline
    operation_path = review / "review_operation_record.json"
    manifest_path = review / "review_manifest.json"
    operation = read_canonical_model(operation_path, LiteralOperationRecord)
    provisional_operation = operation.model_copy(
        update={
            "input_hashes": {**operation.input_hashes, "unexpected_sha256": "0" * 64},
            "operation_sha256": "0" * 64,
        }
    )
    changed_operation = provisional_operation.model_copy(
        update={"operation_sha256": operation_hash(provisional_operation)}
    )
    write_canonical_json(operation_path, changed_operation)
    manifest = read_canonical_model(manifest_path, LiteralReviewManifest)
    artifact_paths = sorted(
        (
            path
            for path in review.rglob("*")
            if path.is_file() and path.name != "review_manifest.json"
        ),
        key=lambda path: path.relative_to(review).as_posix(),
    )
    provisional_manifest = manifest.model_copy(
        update={
            "review_operation_sha256": changed_operation.operation_sha256,
            "artifacts": make_artifact_records(review, artifact_paths),
            "review_manifest_sha256": "0" * 64,
        }
    )
    write_canonical_json(
        manifest_path,
        provisional_manifest.model_copy(
            update={"review_manifest_sha256": review_manifest_hash(provisional_manifest)}
        ),
    )
    with pytest.raises(ValueError, match="operation provenance is inconsistent"):
        validate_literal_review(review_root=review, source_root=source)


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
                loaded.source_bundle.authoring_snapshot_sha256,
            )
        )
        with pytest.raises(LiteralOperationError, match="authoring-only") as raised:
            generate_literal_source(config)
        assert raised.value.failure_record_path is not None
    assert identities[0] == identities[1]


def test_pipeline_never_attempts_network_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse_network(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "create_connection", refuse_network)
    config = load_literal_config(
        Path("configs/evaluation/m2_2_literal_smoke.yaml"),
        source_root_override=tmp_path / "offline-source",
        candidate_root_override=tmp_path / "offline-candidate",
        review_root_override=tmp_path / "offline-review",
    )
    assert generate_literal_source(config).semantic_group_count == 8


def test_review_artifact_and_decoded_png_mutations_are_rejected(
    literal_pipeline: Pipeline,
) -> None:
    source, _candidate, _manifest, review, _composite, _review_manifest = literal_pipeline
    checklist = review / "reviewer_checklist.md"
    checklist.write_text(checklist.read_text(encoding="utf-8") + "mutation\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"Artifact (size|SHA-256) mismatch"):
        validate_literal_review(review_root=review, source_root=source)


def test_review_zoom_is_bound_to_full_frame_and_magnifies_support_geometry(
    literal_pipeline: Pipeline,
) -> None:
    source, _candidate, _manifest, review, _composite, review_manifest = literal_pipeline
    review_items = read_jsonl_models(
        review / "item_review.jsonl", LiteralReviewItem, require_canonical=True
    )
    assert all(len(item.full_frame_render_paths) == 4 for item in review_items)
    assert all(len(item.review_zoom_render_paths) == 4 for item in review_items)
    support_item = next(item for item in review_items if item.schema_identity.value == "SUPPORT")
    full_path = review / support_item.full_frame_render_paths[0]
    zoom_path = review / support_item.review_zoom_render_paths[0]
    with Image.open(full_path) as image:
        full_pixels = tuple(image.convert("RGB").get_flattened_data())
    with Image.open(zoom_path) as image:
        zoom_pixels = tuple(image.convert("RGB").get_flattened_data())
    full_non_background = sum(pixel != BACKGROUND for pixel in full_pixels)
    zoom_non_background = sum(pixel != BACKGROUND for pixel in zoom_pixels)
    assert zoom_non_background > full_non_background
    zoom_relative = zoom_path.relative_to(review).as_posix()
    full_relative = full_path.relative_to(review).as_posix()
    zoom_record = next(
        record for record in review_manifest.render_records if record.path == zoom_relative
    )
    full_record = next(
        record for record in review_manifest.render_records if record.path == full_relative
    )
    assert zoom_record.source_full_frame_raw_pixel_sha256 == full_record.raw_pixel_sha256

    cue = read_canonical_model(review / "cue_disposition_pending.json", LiteralCueDispositionRecord)
    loaded = load_literal_source(source)
    expected_categories = {
        summary.category: summary.category_membership_sha256
        for summary in loaded.lexical_audit.category_summaries
        if summary.owner_disposition_required
    }
    assert cue.required_category_membership_hashes == expected_categories
    assert set(cue.required_category_membership_hashes) <= {
        LiteralLexicalCategory.NECESSARY_CAUSAL_CONDITION_VOCABULARY,
        LiteralLexicalCategory.PHYSICAL_MECHANISM_CORRELATION,
        LiteralLexicalCategory.DUPLICATE_MATCHED_WORDING,
    }
    assert cue.consequential_finding_ids == tuple(
        finding.finding_id
        for finding in loaded.lexical_audit.findings
        if finding.disposition is not LiteralAuditStatus.PASS
    )
    assert cue.accepted_category_membership_hashes == ()
    assert cue.rejected_category_membership_hashes == ()
    assert cue.accepted_finding_ids == ()
    assert cue.rejected_finding_ids == ()
    invalid = cue.model_dump(mode="json")
    invalid["accepted_finding_ids"] = ["0" * 64]
    with pytest.raises(ValidationError, match="unbound finding ID"):
        LiteralCueDispositionRecord.model_validate(invalid)
    assert not hasattr(cue, "required_finding_indexes")


def test_post_publication_source_failure_quarantines_and_records_original(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unfrozen_schemas.evaluation import literal_generation

    output = tmp_path / "post-publish-source"
    config = load_literal_config(
        Path("configs/evaluation/m2_2_literal_smoke.yaml"),
        source_root_override=output,
        candidate_root_override=tmp_path / "candidate",
        review_root_override=tmp_path / "review",
    )

    def fail_after_publish(_output: Path) -> None:
        raise RuntimeError("injected source primary failure")

    monkeypatch.setattr(literal_generation, "_after_literal_source_publication", fail_after_publish)
    with pytest.raises(LiteralOperationError, match="injected source primary failure") as raised:
        generate_literal_source(config)
    assert not output.exists()
    assert raised.value.failure_record_path is not None
    assert list(tmp_path.glob(".post-publish-source.invalid-literal-*"))


def test_final_source_readback_failure_never_leaves_requested_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unfrozen_schemas.evaluation import literal_validation

    output = (tmp_path / "final-readback-source").resolve()
    config = load_literal_config(
        Path("configs/evaluation/m2_2_literal_smoke.yaml"),
        source_root_override=output,
        candidate_root_override=tmp_path / "candidate",
        review_root_override=tmp_path / "review",
    )
    real_validate = literal_validation.validate_literal_source

    def fail_only_final(path: Path) -> LoadedLiteralSource:
        if path.resolve() == output:
            raise RuntimeError("injected final readback failure")
        return real_validate(path)

    monkeypatch.setattr(literal_validation, "validate_literal_source", fail_only_final)
    with pytest.raises(LiteralOperationError, match="injected final readback failure") as raised:
        generate_literal_source(config)
    assert not output.exists()
    assert raised.value.failure_record_path is not None


def test_post_publication_materialization_failure_restores_source(
    materialized_pipeline: tuple[Path, Path, Path, LiteralCandidateManifest],
    clean_benchmark_repository: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unfrozen_schemas.evaluation import literal_review

    source, _candidate, manifest_path, _composite = materialized_pipeline
    literal_root = source / LITERAL_DIRECTORY
    for name in (
        CANDIDATE_VALIDATION_REPORT_FILE,
        COMPOSITE_CANDIDATE_FILE,
        CANDIDATE_MATERIALIZATION_OPERATION_FILE,
    ):
        (literal_root / name).unlink()

    def fail_after_publish(_output: Path) -> None:
        raise RuntimeError("injected materialization primary failure")

    monkeypatch.setattr(
        literal_review,
        "_after_literal_candidate_publication",
        fail_after_publish,
    )
    with pytest.raises(
        LiteralOperationError, match="injected materialization primary failure"
    ) as raised:
        materialize_literal_candidate(
            source_root=source,
            candidate_manifest_path=manifest_path,
            repository_root=clean_benchmark_repository,
        )
    assert source.is_dir()
    assert not any(
        (literal_root / name).exists()
        for name in (
            CANDIDATE_VALIDATION_REPORT_FILE,
            COMPOSITE_CANDIDATE_FILE,
            CANDIDATE_MATERIALIZATION_OPERATION_FILE,
        )
    )
    assert raised.value.failure_record_path is not None


def test_post_publication_review_failure_quarantines_and_records_original(
    materialized_pipeline: tuple[Path, Path, Path, LiteralCandidateManifest],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unfrozen_schemas.evaluation import literal_review

    source, _candidate, _manifest_path, _composite = materialized_pipeline
    output = tmp_path / "post-publish-review"

    def fail_after_publish(_output: Path) -> None:
        raise RuntimeError("injected review primary failure")

    monkeypatch.setattr(literal_review, "_after_literal_review_publication", fail_after_publish)
    with pytest.raises(LiteralOperationError, match="injected review primary failure") as raised:
        build_literal_review(source_root=source, output_root=output)
    assert not output.exists()
    assert raised.value.failure_record_path is not None
    assert list(tmp_path.glob(".post-publish-review.invalid-review-*"))


def test_quarantine_move_failure_removes_publication_and_preserves_primary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unfrozen_schemas.evaluation import literal_generation

    output = tmp_path / "quarantine-fallback-source"
    config = load_literal_config(
        Path("configs/evaluation/m2_2_literal_smoke.yaml"),
        source_root_override=output,
        candidate_root_override=tmp_path / "candidate",
        review_root_override=tmp_path / "review",
    )
    real_replace = os.replace

    def selective_replace(source: Path | str, destination: Path | str) -> None:
        if ".invalid-literal-" in Path(destination).name:
            raise OSError("injected quarantine replace failure")
        real_replace(source, destination)

    def fail_move(*_args: object, **_kwargs: object) -> object:
        raise OSError("injected quarantine move failure")

    def primary(_output: Path) -> None:
        raise RuntimeError("injected primary remains primary")

    monkeypatch.setattr(os, "replace", selective_replace)
    monkeypatch.setattr(shutil, "move", fail_move)
    monkeypatch.setattr(literal_generation, "_after_literal_source_publication", primary)
    with pytest.raises(LiteralOperationError, match="injected primary remains primary") as raised:
        generate_literal_source(config)
    assert not output.exists()
    assert "publication cleanup failed" in str(raised.value)
    assert raised.value.failure_record_path is not None


def test_review_cleanup_compounded_failures_preserve_primary_and_invalidate_output(
    materialized_pipeline: tuple[Path, Path, Path, LiteralCandidateManifest],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unfrozen_schemas.evaluation import literal_review

    source, _candidate, _manifest_path, _composite = materialized_pipeline
    output = tmp_path / "compounded-review-cleanup"
    real_replace = os.replace
    real_move = shutil.move
    real_rmtree = shutil.rmtree
    real_unlink = Path.unlink

    def selective_replace(source_path: Path | str, destination: Path | str) -> None:
        if Path(source_path) == output:
            raise OSError("injected review quarantine replace failure")
        real_replace(source_path, destination)

    def selective_move(source_path: Path | str, destination: Path | str) -> object:
        if Path(source_path) == output:
            raise OSError("injected review quarantine move failure")
        return real_move(source_path, destination)

    def selective_rmtree(path: Path | str) -> None:
        if Path(path) == output:
            raise OSError("injected review removal failure")
        real_rmtree(path)

    def selective_unlink(path: Path, missing_ok: bool = False) -> None:
        if path == output / "review_manifest.json":
            raise OSError("injected review manifest unlink failure")
        real_unlink(path, missing_ok=missing_ok)

    def primary(_output: Path) -> None:
        raise RuntimeError("injected review primary remains primary")

    with monkeypatch.context() as faults:
        faults.setattr(os, "replace", selective_replace)
        faults.setattr(shutil, "move", selective_move)
        faults.setattr(shutil, "rmtree", selective_rmtree)
        faults.setattr(Path, "unlink", selective_unlink)
        faults.setattr(literal_review, "_after_literal_review_publication", primary)
        with pytest.raises(LiteralOperationError) as raised:
            build_literal_review(source_root=source, output_root=output)
        message = str(raised.value)
        assert message.startswith("RuntimeError: injected review primary remains primary")
        assert isinstance(raised.value.__cause__, RuntimeError)
        assert "review quarantine replace failed" in message
        assert "review quarantine move failed" in message
        assert "review removal failed" in message
        assert "review manifest unlink invalidation failed" in message
        assert "review manifest renamed to prevent validation" in message
        assert output.is_dir()
        with pytest.raises(FileNotFoundError, match=r"review_manifest\.json"):
            validate_literal_review(review_root=output, source_root=source)
        assert raised.value.failure_record_path is not None
        failure_path = Path(raised.value.failure_record_path)
        record = read_canonical_model(failure_path, LiteralOperationRecord)
        assert record.status == "FAILED"
        assert record.failure_reason is not None
        assert record.failure_reason.startswith(
            "RuntimeError: injected review primary remains primary"
        )
        assert operation_hash(record) == record.operation_sha256

    assert os.replace is real_replace
    assert shutil.move is real_move
    assert shutil.rmtree is real_rmtree
    assert Path.unlink is real_unlink
    shutil.rmtree(output)
    failure_path.unlink()
    assert not list(tmp_path.glob(f".{output.name}*"))


def test_review_failure_record_publication_failure_retains_valid_staged_record(
    materialized_pipeline: tuple[Path, Path, Path, LiteralCandidateManifest],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unfrozen_schemas.evaluation import literal_review

    source, _candidate, _manifest_path, _composite = materialized_pipeline
    output = tmp_path / "review-failure-record-fallback"
    real_replace = os.replace
    real_move = shutil.move

    def selective_replace(source_path: Path | str, destination: Path | str) -> None:
        if ".failure-" in Path(destination).name:
            raise OSError("injected failure-record replace failure")
        real_replace(source_path, destination)

    def selective_move(source_path: Path | str, destination: Path | str) -> object:
        if ".failure-" in Path(source_path).name:
            raise OSError("injected failure-record move failure")
        return real_move(source_path, destination)

    def primary(_output: Path) -> None:
        raise RuntimeError("injected review failure before record fallback")

    with monkeypatch.context() as faults:
        faults.setattr(os, "replace", selective_replace)
        faults.setattr(shutil, "move", selective_move)
        faults.setattr(literal_review, "_after_literal_review_publication", primary)
        with pytest.raises(LiteralOperationError) as raised:
            build_literal_review(source_root=source, output_root=output)
        message = str(raised.value)
        assert message.startswith("RuntimeError: injected review failure before record fallback")
        assert "failure-record write failed" in message
        assert "failure-record move fallback failed" in message
        assert "governed staged failure record retained" in message
        assert not output.exists()
        assert raised.value.failure_record_path is not None
        failure_path = Path(raised.value.failure_record_path)
        assert ".staging-" in failure_path.name
        record = read_canonical_model(failure_path, LiteralOperationRecord)
        assert record.status == "FAILED"
        assert record.failure_reason is not None
        assert record.failure_reason.startswith(
            "RuntimeError: injected review failure before record fallback"
        )
        assert operation_hash(record) == record.operation_sha256

    assert os.replace is real_replace
    assert shutil.move is real_move
    failure_path.unlink()
    assert not list(tmp_path.glob(f"..{output.name}.failure-*.staging-*"))


def _mock_outcome_root_contract(
    monkeypatch: pytest.MonkeyPatch,
    *,
    repository: Path,
    candidate_version: str,
) -> dict[str, bool]:
    from unfrozen_schemas import config as config_module
    from unfrozen_schemas import literal_config as literal_config_module
    from unfrozen_schemas.evaluation import literal_review, literal_validation

    engineering = {"enabled": False}

    def fake_loaded(root: Path) -> Any:
        return SimpleNamespace(
            root=root.resolve(),
            source_manifest=SimpleNamespace(
                benchmark_version=candidate_version,
                engineering_only=engineering["enabled"],
            ),
            source_bundle=SimpleNamespace(
                resolved_configuration={
                    "source_root": f"benchmarks/source/{candidate_version}",
                    "review_root": f"reports/private/{candidate_version}",
                }
            ),
        )

    monkeypatch.setattr(config_module, "find_repository_root", lambda _path: repository)
    monkeypatch.setattr(literal_config_module, "find_repository_root", lambda _path: repository)
    monkeypatch.setattr(literal_validation, "load_literal_source", fake_loaded)
    monkeypatch.setattr(
        literal_validation,
        "_validate_loaded_literal_source_content",
        lambda _loaded: SimpleNamespace(),
    )
    monkeypatch.setattr(
        literal_review,
        "_load_materialized_source",
        lambda source_root: (fake_loaded(source_root), None, None, None),
    )
    monkeypatch.setattr(
        literal_review,
        "_validate_literal_review_content",
        lambda **_kwargs: SimpleNamespace(),
    )
    return engineering


def _create_windows_junction(alias: Path, target: Path) -> None:
    completed = subprocess.run(
        ["cmd.exe", "/c", "mklink", "/J", str(alias), str(target)],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        pytest.fail(f"Windows junction creation failed: {completed.stderr or completed.stdout}")


def _remove_directory_alias(alias: Path) -> None:
    if os.path.lexists(alias):
        try:
            os.unlink(alias)
        except (IsADirectoryError, PermissionError):
            os.rmdir(alias)


def test_outcome_validators_accept_canonical_relative_and_absolute_roots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    version = "outcome-location-fixture-v1"
    repository = tmp_path / "root-contract-repository"
    source = repository / "benchmarks" / "source" / version
    review = repository / "reports" / "private" / version
    source.mkdir(parents=True)
    review.mkdir(parents=True)
    (source / "artifact.bin").write_bytes(b"canonical source")
    (review / "artifact.bin").write_bytes(b"canonical review")
    _mock_outcome_root_contract(
        monkeypatch,
        repository=repository,
        candidate_version=version,
    )
    monkeypatch.chdir(repository)

    relative_source = Path("benchmarks") / "source" / version
    relative_review = Path("reports") / "private" / version
    source_before = _file_snapshot(source)
    review_before = _file_snapshot(review)
    validate_literal_source(relative_source)
    validate_literal_source(source)
    validate_literal_review(review_root=relative_review, source_root=relative_source)
    validate_literal_review(review_root=review, source_root=source)
    assert _file_snapshot(source) == source_before
    assert _file_snapshot(review) == review_before


def test_outcome_validators_reject_copied_and_moved_roots_and_keep_engineering_overrides(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    version = "outcome-location-fixture-v1"
    repository = tmp_path / "root-contract-repository"
    source = repository / "benchmarks" / "source" / version
    review = repository / "reports" / "private" / version
    source.mkdir(parents=True)
    review.mkdir(parents=True)
    (source / "artifact.bin").write_bytes(b"exact source copy")
    (review / "artifact.bin").write_bytes(b"exact review copy")
    engineering = _mock_outcome_root_contract(
        monkeypatch,
        repository=repository,
        candidate_version=version,
    )
    monkeypatch.chdir(repository)

    outside_source = tmp_path / "copied-outcome-source"
    outside_review = tmp_path / "copied-outcome-review"
    shutil.copytree(source, outside_source)
    shutil.copytree(review, outside_review)
    source_before = _file_snapshot(outside_source)
    review_before = _file_snapshot(outside_review)
    with pytest.raises(ValueError, match=r"source_root.*configured canonical"):
        validate_literal_source(outside_source)
    with pytest.raises(ValueError, match=r"review_root.*configured canonical"):
        validate_literal_review(review_root=outside_review, source_root=source)
    assert _file_snapshot(outside_source) == source_before
    assert _file_snapshot(outside_review) == review_before

    moved_source = tmp_path / "moved-outcome-source"
    moved_review = tmp_path / "moved-outcome-review"
    shutil.move(str(outside_source), str(moved_source))
    shutil.move(str(outside_review), str(moved_review))
    with pytest.raises(ValueError, match=r"source_root.*configured canonical"):
        validate_literal_source(moved_source)
    with pytest.raises(ValueError, match=r"review_root.*configured canonical"):
        validate_literal_review(review_root=moved_review, source_root=source)

    engineering["enabled"] = True
    validate_literal_source(moved_source)
    validate_literal_review(review_root=moved_review, source_root=moved_source)


@pytest.mark.skipif(os.name == "nt", reason="POSIX symbolic-link semantics")
def test_posix_direct_to_canonical_source_and_review_symlinks_are_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    version = "outcome-location-fixture-v1"
    repository = tmp_path / "posix-alias-repository"
    source = repository / "benchmarks" / "source" / version
    review = repository / "reports" / "private" / version
    source.mkdir(parents=True)
    review.mkdir(parents=True)
    _mock_outcome_root_contract(
        monkeypatch,
        repository=repository,
        candidate_version=version,
    )
    monkeypatch.chdir(repository)
    source_alias = tmp_path / "direct-canonical-source-symlink"
    review_alias = tmp_path / "direct-canonical-review-symlink"
    source_alias.symlink_to(source, target_is_directory=True)
    review_alias.symlink_to(review, target_is_directory=True)

    with pytest.raises(ValueError, match="symbolic-link, junction, or reparse-point"):
        validate_literal_source(source_alias)
    with pytest.raises(ValueError, match="symbolic-link, junction, or reparse-point"):
        validate_literal_review(review_root=review_alias, source_root=source)
    runner = CliRunner()
    assert runner.invoke(app, ["validate-literal-source", "--source", str(source_alias)]).exit_code
    assert runner.invoke(
        app,
        [
            "validate-literal-review",
            "--source",
            str(source),
            "--review",
            str(review_alias),
        ],
    ).exit_code


@pytest.mark.skipif(os.name != "nt", reason="Windows junction semantics")
def test_windows_direct_to_canonical_source_and_review_junctions_are_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    version = "outcome-location-fixture-v1"
    repository = tmp_path / "junction-alias-repository"
    source = repository / "benchmarks" / "source" / version
    review = repository / "reports" / "private" / version
    source.mkdir(parents=True)
    review.mkdir(parents=True)
    _mock_outcome_root_contract(
        monkeypatch,
        repository=repository,
        candidate_version=version,
    )
    monkeypatch.chdir(repository)
    source_alias = tmp_path / "direct-canonical-source-junction"
    review_alias = tmp_path / "direct-canonical-review-junction"
    _create_windows_junction(source_alias, source)
    _create_windows_junction(review_alias, review)
    try:
        with pytest.raises(ValueError, match="symbolic-link, junction, or reparse-point"):
            validate_literal_source(source_alias)
        with pytest.raises(ValueError, match="symbolic-link, junction, or reparse-point"):
            validate_literal_review(review_root=review_alias, source_root=source)
        runner = CliRunner()
        source_result = runner.invoke(
            app,
            ["validate-literal-source", "--source", str(source_alias)],
        )
        review_result = runner.invoke(
            app,
            [
                "validate-literal-review",
                "--source",
                str(source),
                "--review",
                str(review_alias),
            ],
        )
        assert source_result.exit_code != 0
        assert review_result.exit_code != 0
        assert "reparse-point" in source_result.output
        assert "reparse-point" in review_result.output
    finally:
        _remove_directory_alias(source_alias)
        _remove_directory_alias(review_alias)


@pytest.mark.skipif(os.name != "nt", reason="Windows symbolic-link semantics")
def test_windows_directory_symlink_aliases_are_rejected_when_creation_is_available(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    version = "outcome-location-fixture-v1"
    repository = tmp_path / "windows-symlink-repository"
    source = repository / "benchmarks" / "source" / version
    review = repository / "reports" / "private" / version
    source.mkdir(parents=True)
    review.mkdir(parents=True)
    _mock_outcome_root_contract(
        monkeypatch,
        repository=repository,
        candidate_version=version,
    )
    monkeypatch.chdir(repository)
    source_alias = tmp_path / "direct-canonical-source-windows-symlink"
    review_alias = tmp_path / "direct-canonical-review-windows-symlink"
    try:
        source_alias.symlink_to(source, target_is_directory=True)
        review_alias.symlink_to(review, target_is_directory=True)
    except OSError as exc:
        _remove_directory_alias(source_alias)
        _remove_directory_alias(review_alias)
        pytest.skip(f"Windows symbolic-link creation is unavailable: {exc}")
    try:
        with pytest.raises(ValueError, match="symbolic-link, junction, or reparse-point"):
            validate_literal_source(source_alias)
        with pytest.raises(ValueError, match="symbolic-link, junction, or reparse-point"):
            validate_literal_review(review_root=review_alias, source_root=source)
    finally:
        _remove_directory_alias(source_alias)
        _remove_directory_alias(review_alias)


def test_alias_within_governed_canonical_source_components_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    version = "outcome-location-fixture-v1"
    repository = tmp_path / "governed-component-repository"
    repository.joinpath("benchmarks").mkdir(parents=True)
    repository.joinpath("reports", "private", version).mkdir(parents=True)
    external_source_parent = tmp_path / "governed-source-target"
    external_source_parent.joinpath(version).mkdir(parents=True)
    governed_alias = repository / "benchmarks" / "source"
    if os.name == "nt":
        _create_windows_junction(governed_alias, external_source_parent)
    else:
        governed_alias.symlink_to(external_source_parent, target_is_directory=True)
    _mock_outcome_root_contract(
        monkeypatch,
        repository=repository,
        candidate_version=version,
    )
    config_path = repository / "configs" / "evaluation" / "m2_2_literal_candidate.yaml"
    config_path.parent.mkdir(parents=True)
    source_config = Path(__file__).parents[2] / "configs" / "evaluation" / config_path.name
    shutil.copyfile(source_config, config_path)
    monkeypatch.chdir(repository)
    try:
        with pytest.raises(
            ConfigLoadError,
            match="symbolic-link, junction, or reparse-point",
        ):
            load_literal_config(config_path)
        with pytest.raises(ValueError, match="symbolic-link, junction, or reparse-point"):
            validate_literal_source(Path("benchmarks") / "source" / version)
    finally:
        _remove_directory_alias(governed_alias)
