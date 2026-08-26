"""M2.2 composite identity and private owner-review bundle operations."""

from __future__ import annotations

import time
import tracemalloc
from collections import Counter
from pathlib import Path
from typing import Any

from unfrozen_schemas.config import find_repository_root, sha256_file
from unfrozen_schemas.envs.schema_world.renderer import render_raw_pixels, save_png
from unfrozen_schemas.evaluation.benchmark_models import CandidateManifest
from unfrozen_schemas.evaluation.benchmark_persistence import (
    make_artifact_records,
    read_canonical_model,
    read_jsonl_models,
    verify_artifact_records,
    write_canonical_json,
    write_canonical_jsonl,
)
from unfrozen_schemas.evaluation.benchmark_validation import validate_benchmark_manifest
from unfrozen_schemas.evaluation.literal_generation import _resource_budget
from unfrozen_schemas.evaluation.literal_hashing import (
    literal_candidate_root_hash,
    operation_hash,
    review_content_bundle_hash,
    review_manifest_hash,
    validation_report_hash,
)
from unfrozen_schemas.evaluation.literal_models import (
    LiteralCandidateManifest,
    LiteralOperationRecord,
    LiteralOperationResult,
    LiteralPendingOwnerReview,
    LiteralReviewItem,
    LiteralReviewManifest,
    LiteralValidationReport,
)
from unfrozen_schemas.evaluation.literal_validation import (
    CANDIDATE_VALIDATION_OPERATION_FILE,
    CANDIDATE_VALIDATION_REPORT_FILE,
    COMPOSITE_CANDIDATE_FILE,
    LITERAL_DIRECTORY,
    REVIEW_OPERATION_FILE,
    LoadedLiteralSource,
    load_literal_source,
    pending_owner_review,
    review_content_records,
    validate_loaded_literal_source,
)
from unfrozen_schemas.provenance import (
    capture_git_state,
    collect_package_versions,
    collect_platform_information,
    create_run_id,
    utc_now,
)

REVIEW_MANIFEST_FILE = "review_manifest.json"
REVIEW_ITEMS_FILE = "item_review.jsonl"


def _counts(values: list[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def _candidate_report(loaded: LoadedLiteralSource) -> LiteralValidationReport:
    source_report = validate_loaded_literal_source(loaded)
    provisional = source_report.model_copy(
        update={
            "m2_1_lifecycle_validation": "PASS",
            "literal_validation_report_sha256": "0" * 64,
        }
    )
    return provisional.model_copy(
        update={"literal_validation_report_sha256": validation_report_hash(provisional)}
    )


def _composite_candidate(
    *,
    loaded: LoadedLiteralSource,
    candidate: CandidateManifest,
    candidate_manifest_path: Path,
    report: LiteralValidationReport,
) -> LiteralCandidateManifest:
    source = loaded.source_bundle
    review_hash = review_content_bundle_hash(review_content_records(loaded))
    provisional = LiteralCandidateManifest(
        candidate_version=candidate.benchmark_version,
        purpose=candidate.purpose.value,
        git=candidate.git,
        codex_spec_sha256=candidate.codex_spec_sha256,
        m2_1_candidate_manifest_file_sha256=sha256_file(candidate_manifest_path),
        m2_1_candidate_bundle_root_sha256=candidate.candidate_bundle_root_sha256,
        m2_1_source_snapshot_sha256=candidate.source_snapshot_sha256,
        m2_1_private_answer_bundle_sha256=candidate.private_answer_bundle_sha256,
        m2_1_public_metadata_bundle_sha256=candidate.public_metadata_bundle_sha256,
        m2_1_quarantine_scope_sha256=candidate.quarantine_scope_sha256,
        literal_source_bundle_sha256=source.literal_source_bundle_sha256,
        partition_plan_sha256=source.partition_plan_sha256,
        template_registry_sha256=source.template_registry_sha256,
        item_binding_bundle_sha256=source.item_binding_bundle_sha256,
        witness_bundle_sha256=source.witness_bundle_sha256,
        split_audit_sha256=source.split_audit_sha256,
        lexical_audit_sha256=source.lexical_audit_sha256,
        literal_validation_report_sha256=report.literal_validation_report_sha256,
        review_content_bundle_sha256=review_hash,
        semantic_group_count=report.semantic_group_count,
        source_item_count=report.source_item_count,
        literal_candidate_root_sha256="0" * 64,
    )
    return provisional.model_copy(
        update={"literal_candidate_root_sha256": literal_candidate_root_hash(provisional)}
    )


def validate_literal_benchmark(
    *,
    source_root: Path,
    candidate_manifest_path: Path,
    repository_root: Path | None = None,
) -> LiteralCandidateManifest:
    """Validate and persist an idempotent M2.2 composite record beside private source."""

    repository = (
        find_repository_root(Path.cwd()) if repository_root is None else repository_root.resolve()
    )
    loaded = load_literal_source(source_root)
    validate_loaded_literal_source(loaded)
    validated = validate_benchmark_manifest(
        candidate_manifest_path,
        repository_root=repository,
    )
    candidate = read_canonical_model(candidate_manifest_path, CandidateManifest)
    if validated.benchmark_version != loaded.source_manifest.benchmark_version:
        raise ValueError("M2.1 candidate and literal source versions differ")
    if validated.purpose is not loaded.source_manifest.purpose:
        raise ValueError("M2.1 candidate and literal source purposes differ")
    current_git = capture_git_state(repository)
    if not candidate.engineering_only:
        if candidate.git.dirty or current_git.dirty:
            raise ValueError(
                "Outcome literal candidate requires clean build and validation Git state"
            )
        if candidate.git.commit != current_git.commit:
            raise ValueError("Outcome literal candidate does not match the current branch head")
    report = _candidate_report(loaded)
    composite = _composite_candidate(
        loaded=loaded,
        candidate=candidate,
        candidate_manifest_path=candidate_manifest_path,
        report=report,
    )
    literal_root = loaded.root / LITERAL_DIRECTORY
    report_path = literal_root / CANDIDATE_VALIDATION_REPORT_FILE
    composite_path = literal_root / COMPOSITE_CANDIDATE_FILE
    operation_path = literal_root / CANDIDATE_VALIDATION_OPERATION_FILE
    existing = (report_path.exists(), composite_path.exists(), operation_path.exists())
    if any(existing):
        if not all(existing):
            raise ValueError("Partial literal-candidate validation artifacts are prohibited")
        if read_canonical_model(report_path, LiteralValidationReport) != report:
            raise ValueError("Existing candidate literal-validation report is stale")
        if read_canonical_model(composite_path, LiteralCandidateManifest) != composite:
            raise ValueError("Existing literal composite candidate is stale")
        operation = read_canonical_model(operation_path, LiteralOperationRecord)
        if operation_hash(operation) != operation.operation_sha256:
            raise ValueError("Candidate-validation operation hash does not reconstruct")
        if operation.output_hashes != {
            "literal_candidate_root_sha256": composite.literal_candidate_root_sha256,
            "literal_validation_report_sha256": report.literal_validation_report_sha256,
        }:
            raise ValueError("Candidate-validation operation output hashes are stale")
        verify_artifact_records(
            loaded.root,
            operation.artifacts,
            expected_paths={
                f"{LITERAL_DIRECTORY}/{CANDIDATE_VALIDATION_REPORT_FILE}",
                f"{LITERAL_DIRECTORY}/{COMPOSITE_CANDIDATE_FILE}",
            },
        )
        return composite

    operation_id = create_run_id("literal-candidate-validation")
    started_at = utc_now()
    start_tick = time.perf_counter()
    tracing_was_active = tracemalloc.is_tracing()
    if not tracing_was_active:
        tracemalloc.start()
    write_canonical_json(report_path, report)
    write_canonical_json(composite_path, composite)
    ended_at = utc_now()
    peak = tracemalloc.get_traced_memory()[1] if tracemalloc.is_tracing() else None
    if not tracing_was_active and tracemalloc.is_tracing():
        tracemalloc.stop()
    retained = [report_path, composite_path]
    budget = _resource_budget(
        operation_id=operation_id,
        started_at=started_at,
        ended_at=ended_at,
        elapsed=time.perf_counter() - start_tick,
        peak_memory=peak,
        witnesses=loaded.witness_bundle.witnesses,
        artifact_count=len(retained),
        artifact_bytes=sum(path.stat().st_size for path in retained),
    )
    operation_provisional = LiteralOperationRecord(
        operation_id=operation_id,
        operation_kind="validate_literal_source",
        candidate_version=composite.candidate_version,
        purpose=composite.purpose,
        engineering_only=candidate.engineering_only,
        git=current_git,
        codex_spec_sha256=candidate.codex_spec_sha256,
        resolved_configuration={
            "candidate_version": composite.candidate_version,
            "device": "cpu",
            "network_access": False,
            "model_access": False,
            "gpu_access": False,
        },
        input_hashes={
            "m2_1_candidate_manifest_file_sha256": sha256_file(candidate_manifest_path),
            "literal_source_bundle_sha256": loaded.source_bundle.literal_source_bundle_sha256,
        },
        output_hashes={
            "literal_candidate_root_sha256": composite.literal_candidate_root_sha256,
            "literal_validation_report_sha256": report.literal_validation_report_sha256,
        },
        item_count=composite.source_item_count,
        semantic_group_count=composite.semantic_group_count,
        schema_counts=report.schema_counts,
        level_counts=report.level_counts,
        family_counts=report.family_counts,
        status="COMPLETED",
        failure_reason=None,
        package_versions=collect_package_versions(),
        platform=collect_platform_information(),
        started_at=started_at,
        ended_at=ended_at,
        artifacts=make_artifact_records(loaded.root, retained),
        resource_budget=budget,
        operation_sha256="0" * 64,
    )
    operation = operation_provisional.model_copy(
        update={"operation_sha256": operation_hash(operation_provisional)}
    )
    write_canonical_json(operation_path, operation)
    return composite


def _review_items(loaded: LoadedLiteralSource) -> tuple[LiteralReviewItem, ...]:
    items = {item.item_id: item for item in loaded.items}
    witnesses = {item.semantic_group_id: item for item in loaded.witness_bundle.witnesses}
    result: list[LiteralReviewItem] = []
    for binding in loaded.item_bindings.bindings:
        witness = witnesses[binding.semantic_group_id]
        left, right = (items[item_id] for item_id in binding.item_ids)
        result.append(
            LiteralReviewItem(
                semantic_group_id=binding.semantic_group_id,
                item_ids=binding.item_ids,
                schema_identity=binding.schema_identity,
                transfer_level=binding.transfer_level,
                task_family=binding.task_family,
                prompt=left.model_visible.prompt,
                option_forms=(
                    tuple(
                        option.model_dump(mode="json")
                        for option in left.model_visible.ordered_options
                    ),
                    tuple(
                        option.model_dump(mode="json")
                        for option in right.model_visible.ordered_options
                    ),
                ),
                stable_correct_option_id=binding.stable_correct_option_id,
                simulator_rationale=(
                    "Independent replay changed the declared causal factor and reproduced "
                    "the stable actual and counterfactual outcomes."
                ),
                actual_outcome_code=witness.actual_outcome_code,
                counterfactual_outcome_code=witness.counterfactual_outcome_code,
                causal_factor=witness.declared_causal_factor,
                lexical_cue_annotations=left.scientific_annotations.lexical_cue_annotations,
                provenance=left.provenance,
                human_validation=left.human_validation,
                human_validation_status=(
                    "not_applicable_engineering"
                    if loaded.source_manifest.engineering_only
                    else "not_started"
                ),
                before_render_path=f"renders/{binding.semantic_group_id}-before.png",
                after_render_path=f"renders/{binding.semantic_group_id}-after.png",
                witness_sha256=witness.witness_sha256,
                item_binding_sha256=binding.item_binding_sha256,
            )
        )
    return tuple(result)


def _write_markdown(
    path: Path,
    *,
    title: str,
    lines: list[str],
) -> None:
    path.write_text("\n".join((f"# {title}", "", *lines, "")), encoding="utf-8", newline="\n")


def build_literal_review(
    *,
    source_root: Path,
    output_root: Path,
) -> LiteralOperationResult:
    """Build a private, write-once review bundle with deterministic renders."""

    loaded = load_literal_source(source_root)
    validate_loaded_literal_source(loaded)
    literal_root = loaded.root / LITERAL_DIRECTORY
    composite = read_canonical_model(
        literal_root / COMPOSITE_CANDIDATE_FILE, LiteralCandidateManifest
    )
    report = read_canonical_model(
        literal_root / CANDIDATE_VALIDATION_REPORT_FILE, LiteralValidationReport
    )
    expected_content_hash = review_content_bundle_hash(review_content_records(loaded))
    if expected_content_hash != composite.review_content_bundle_sha256:
        raise ValueError("Composite candidate review-content identity is stale")
    output = output_root.resolve()
    if output.exists():
        raise FileExistsError(f"Literal review destination already exists: {output}")
    operation_id = create_run_id("literal-review-build")
    started_at = utc_now()
    start_tick = time.perf_counter()
    tracing_was_active = tracemalloc.is_tracing()
    if not tracing_was_active:
        tracemalloc.start()
    output.mkdir(parents=True, exist_ok=False)
    review_items = _review_items(loaded)
    write_canonical_jsonl(output / REVIEW_ITEMS_FILE, list(review_items))
    write_canonical_json(output / "split_audit.json", loaded.split_audit)
    write_canonical_json(output / "lexical_audit.json", loaded.lexical_audit)
    write_canonical_json(output / "literal_validation_report.json", report)
    write_canonical_json(output / "witness_bundle.json", loaded.witness_bundle)
    write_canonical_json(
        output / "pending_owner_review.json",
        pending_owner_review(composite.candidate_version),
    )
    _write_markdown(
        output / "aggregate_summary.md",
        title="M2.2 private literal candidate review summary",
        lines=[
            f"Candidate version: `{composite.candidate_version}`",
            f"Purpose: `{composite.purpose}`",
            f"Semantic groups: {composite.semantic_group_count}",
            f"Source records: {composite.source_item_count}",
            "Status: `CANDIDATE_VALIDATED_OWNER_REVIEW_PENDING`",
            "Human validation, rights, ethics, freezing, and scientific evaluation remain pending.",
        ],
    )
    _write_markdown(
        output / "reviewer_checklist.md",
        title="M2.2 owner review decision template",
        lines=[
            "- [ ] Prompts are determinate, literal, and free of privileged implementation fields.",
            "- [ ] Reverse variants preserve meaning and stable answers.",
            "- [ ] L1/L2 and task-family classifications are appropriate.",
            "- [ ] Counterfactuals differ only on the declared causal dimension.",
            "- [ ] Cue-audit findings are acceptable for candidate review.",
            "- [ ] Owner decision records the exact PR, head SHA, and aggregate roots.",
            "",
            "Decision: PENDING",
        ],
    )
    witness_by_group = {
        witness.semantic_group_id: witness for witness in loaded.witness_bundle.witnesses
    }
    render_root = output / "renders"
    for item in review_items:
        witness = witness_by_group[item.semantic_group_id]
        for suffix, state in (
            ("before", witness.initial_privileged_state),
            ("after", witness.actual_final_state),
        ):
            pixels, _pixel_hash = render_raw_pixels(state, width=128, height=128)
            save_png(
                render_root / f"{item.semantic_group_id}-{suffix}.png",
                pixels,
                width=128,
                height=128,
            )
    retained = sorted(
        (path for path in output.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(output).as_posix(),
    )
    manifest_provisional = LiteralReviewManifest(
        candidate_version=composite.candidate_version,
        literal_candidate_root_sha256=composite.literal_candidate_root_sha256,
        witness_bundle_sha256=composite.witness_bundle_sha256,
        literal_validation_report_sha256=composite.literal_validation_report_sha256,
        review_content_bundle_sha256=expected_content_hash,
        artifacts=make_artifact_records(output, retained),
        review_manifest_sha256="0" * 64,
    )
    manifest = manifest_provisional.model_copy(
        update={"review_manifest_sha256": review_manifest_hash(manifest_provisional)}
    )
    manifest_path = output / REVIEW_MANIFEST_FILE
    write_canonical_json(manifest_path, manifest)
    ended_at = utc_now()
    peak = tracemalloc.get_traced_memory()[1] if tracemalloc.is_tracing() else None
    if not tracing_was_active and tracemalloc.is_tracing():
        tracemalloc.stop()
    review_files = [*retained, manifest_path]
    budget = _resource_budget(
        operation_id=operation_id,
        started_at=started_at,
        ended_at=ended_at,
        elapsed=time.perf_counter() - start_tick,
        peak_memory=peak,
        witnesses=(),
        artifact_count=len(review_files),
        artifact_bytes=sum(path.stat().st_size for path in review_files),
    )
    repository = find_repository_root(Path.cwd())
    operation_provisional = LiteralOperationRecord(
        operation_id=operation_id,
        operation_kind="build_literal_review",
        candidate_version=composite.candidate_version,
        purpose=composite.purpose,
        engineering_only=loaded.source_manifest.engineering_only,
        git=capture_git_state(repository),
        codex_spec_sha256=composite.codex_spec_sha256,
        resolved_configuration={
            "candidate_version": composite.candidate_version,
            "device": "cpu",
            "network_access": False,
            "model_access": False,
            "gpu_access": False,
        },
        input_hashes={
            "literal_candidate_root_sha256": composite.literal_candidate_root_sha256,
            "review_content_bundle_sha256": expected_content_hash,
        },
        output_hashes={"review_manifest_sha256": manifest.review_manifest_sha256},
        item_count=composite.source_item_count,
        semantic_group_count=composite.semantic_group_count,
        schema_counts=report.schema_counts,
        level_counts=report.level_counts,
        family_counts=report.family_counts,
        status="COMPLETED",
        failure_reason=None,
        package_versions=collect_package_versions(),
        platform=collect_platform_information(),
        started_at=started_at,
        ended_at=ended_at,
        artifacts=make_artifact_records(output, review_files),
        resource_budget=budget,
        operation_sha256="0" * 64,
    )
    operation = operation_provisional.model_copy(
        update={"operation_sha256": operation_hash(operation_provisional)}
    )
    write_canonical_json(literal_root / REVIEW_OPERATION_FILE, operation)
    validate_literal_review(review_root=output, source_root=loaded.root)
    return LiteralOperationResult(
        operation_id=operation_id,
        dry_run=False,
        candidate_version=composite.candidate_version,
        purpose=composite.purpose,
        source_path=str(loaded.root),
        review_path=str(output),
        semantic_group_count=composite.semantic_group_count,
        source_item_count=composite.source_item_count,
        partition_plan_sha256=composite.partition_plan_sha256,
        template_registry_sha256=composite.template_registry_sha256,
        witness_bundle_sha256=composite.witness_bundle_sha256,
        literal_validation_report_sha256=composite.literal_validation_report_sha256,
        literal_candidate_root_sha256=composite.literal_candidate_root_sha256,
        review_manifest_sha256=manifest.review_manifest_sha256,
    )


def validate_literal_review(*, review_root: Path, source_root: Path) -> LiteralReviewManifest:
    """Read back every review artifact and reconstruct its source-bound identity."""

    root = review_root.resolve()
    loaded = load_literal_source(source_root)
    validate_loaded_literal_source(loaded)
    manifest = read_canonical_model(root / REVIEW_MANIFEST_FILE, LiteralReviewManifest)
    expected_paths = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name != REVIEW_MANIFEST_FILE
    }
    verify_artifact_records(root, manifest.artifacts, expected_paths=expected_paths)
    if review_manifest_hash(manifest) != manifest.review_manifest_sha256:
        raise ValueError("Literal review-manifest hash does not reconstruct")
    composite = read_canonical_model(
        loaded.root / LITERAL_DIRECTORY / COMPOSITE_CANDIDATE_FILE,
        LiteralCandidateManifest,
    )
    if composite.literal_candidate_root_sha256 != manifest.literal_candidate_root_sha256:
        raise ValueError("Review manifest binds a different literal candidate")
    content_hash = review_content_bundle_hash(review_content_records(loaded))
    if content_hash != manifest.review_content_bundle_sha256:
        raise ValueError("Review content does not match the private literal source")
    observed_items = read_jsonl_models(
        root / REVIEW_ITEMS_FILE,
        LiteralReviewItem,
        require_canonical=True,
    )
    if observed_items != _review_items(loaded):
        raise ValueError("Review item file does not reconstruct from private source")
    pending = read_canonical_model(root / "pending_owner_review.json", LiteralPendingOwnerReview)
    if pending != pending_owner_review(manifest.candidate_version):
        raise ValueError("Pending owner-review record does not reconstruct")
    operation = read_canonical_model(
        loaded.root / LITERAL_DIRECTORY / REVIEW_OPERATION_FILE,
        LiteralOperationRecord,
    )
    if operation_hash(operation) != operation.operation_sha256:
        raise ValueError("Literal review-operation hash does not reconstruct")
    if operation.output_hashes != {"review_manifest_sha256": manifest.review_manifest_sha256}:
        raise ValueError("Literal review-operation output hash is stale")
    verify_artifact_records(
        root,
        operation.artifacts,
        expected_paths={*expected_paths, REVIEW_MANIFEST_FILE},
    )
    return manifest


def inspect_literal_item(
    *,
    source_root: Path,
    item_id: str,
    render_path: Path | None = None,
) -> dict[str, Any]:
    """Explicitly inspect one private item, optionally writing an after-state render."""

    loaded = load_literal_source(source_root)
    validate_loaded_literal_source(loaded)
    item = next((candidate for candidate in loaded.items if candidate.item_id == item_id), None)
    if item is None:
        raise ValueError(f"Unknown private literal item ID: {item_id}")
    binding = next(
        candidate for candidate in loaded.item_bindings.bindings if item_id in candidate.item_ids
    )
    witness = next(
        candidate
        for candidate in loaded.witness_bundle.witnesses
        if candidate.semantic_group_id == binding.semantic_group_id
    )
    summary: dict[str, Any] = {
        "item": item.model_dump(mode="json"),
        "binding": binding.model_dump(mode="json"),
        "witness": witness.model_dump(mode="json"),
    }
    if render_path is not None:
        pixels, pixel_hash = render_raw_pixels(witness.actual_final_state)
        save_png(render_path, pixels, width=128, height=128)
        summary["render_path"] = str(render_path.resolve())
        summary["render_pixel_sha256"] = pixel_hash
    return summary
