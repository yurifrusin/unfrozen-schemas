"""Offline CPU integration coverage for the corrected M2.2 pipeline."""

from __future__ import annotations

import os
import shutil
import socket
from pathlib import Path

import pytest
from PIL import Image

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
    LiteralCandidateManifest,
    LiteralCueDispositionRecord,
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
        "71fad8211ae65f71548a85af713f9314ca56033e3eb00da320db43855dc9e2ca"
    )
    assert composite.m2_1_candidate_bundle_root_sha256 == (
        "b2db23f28ad841c83900be5c488b0e65368beb67be17d69663b3e9034764518b"
    )
    assert composite.partition_plan_sha256 == (
        "8d5978ae90ada2c725db19d029c6a789495f56a48a01755f061f278673bbdda1"
    )
    assert composite.template_registry_sha256 == (
        "7ec1508923f21a779fa4f038fbc72a48b6b9808df967f128050be607b8d4fc0b"
    )
    assert composite.witness_bundle_sha256 == (
        "afc6b013c42de6152243b18aebb621ea7ed0b9152490b22cfbfeb34be17da8df"
    )
    assert composite.literal_validation_report_sha256 == (
        "32be1e8af71d11b6b69dfa76e41bc84a81cd46d75f7be09381a196ba17d72d11"
    )
    assert composite.literal_candidate_root_sha256 == (
        "23a3e1a75adf70fecacf1f7fab4fdc350a2bd68cbf60b0a23c3840a341a235d7"
    )
    assert review_manifest.review_operation_sha256
    assert review_manifest.review_manifest_sha256 == (
        "21a7466cefb2acbe13a462c6ff7bb81740a93a7d8c739c6271e2790bc5851102"
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
    _source, _candidate, _manifest, review, _composite, review_manifest = literal_pipeline
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
    assert cue.required_category_membership_hashes
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
