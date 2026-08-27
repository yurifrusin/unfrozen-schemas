"""M2.2 composite identity, materialization, and private review operations."""

from __future__ import annotations

import hashlib
import os
import shutil
import time
import tracemalloc
import uuid
from pathlib import Path
from typing import Any

from PIL import Image

from unfrozen_schemas.config import find_repository_root, sha256_file
from unfrozen_schemas.envs.schema_world.renderer import BACKGROUND, render_raw_pixels, save_png
from unfrozen_schemas.envs.schema_world.state import Attachment, EntityRole, Tether, WorldState
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
from unfrozen_schemas.evaluation.literal_generation import (
    _publish_source,
    _quarantine_publication,
    _resource_budget,
    _safe_remove_tree,
    _write_literal_failure_record,
)
from unfrozen_schemas.evaluation.literal_hashing import (
    literal_candidate_root_hash,
    operation_hash,
    review_content_bundle_hash,
    review_manifest_hash,
    validation_report_hash,
)
from unfrozen_schemas.evaluation.literal_models import (
    LiteralAuditStatus,
    LiteralCandidateManifest,
    LiteralCueDispositionRecord,
    LiteralOperationError,
    LiteralOperationRecord,
    LiteralOperationResult,
    LiteralPendingOwnerReview,
    LiteralRenderRecord,
    LiteralReviewItem,
    LiteralReviewManifest,
    LiteralValidationReport,
)
from unfrozen_schemas.evaluation.literal_validation import (
    CANDIDATE_MATERIALIZATION_OPERATION_FILE,
    CANDIDATE_VALIDATION_REPORT_FILE,
    COMPOSITE_CANDIDATE_FILE,
    LITERAL_DIRECTORY,
    LoadedLiteralSource,
    _validate_loaded_literal_source_content,
    canonical_record_sha256,
    load_literal_source,
    pending_owner_review,
    review_content_records,
    validate_literal_root_location,
    validate_loaded_literal_source,
)
from unfrozen_schemas.literal_config import reject_literal_path_aliases
from unfrozen_schemas.provenance import (
    capture_git_state,
    collect_package_versions,
    collect_platform_information,
    create_run_id,
    utc_now,
)

REVIEW_MANIFEST_FILE = "review_manifest.json"
REVIEW_ITEMS_FILE = "item_review.jsonl"
REVIEW_OPERATION_FILE = "review_operation_record.json"
CUE_DISPOSITION_FILE = "cue_disposition_pending.json"


def _candidate_report(
    loaded: LoadedLiteralSource,
    *,
    enforce_source_location: bool = True,
    observed_source_root: Path | None = None,
) -> LiteralValidationReport:
    source_report = (
        validate_loaded_literal_source(loaded, observed_root=observed_source_root)
        if enforce_source_location
        else _validate_loaded_literal_source_content(loaded)
    )
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
    provisional = LiteralCandidateManifest(
        candidate_version=candidate.benchmark_version,
        purpose=candidate.purpose.value,
        git=candidate.git,
        codex_spec_sha256=candidate.codex_spec_sha256,
        authoring_snapshot_sha256=source.authoring_snapshot_sha256,
        authoring_snapshot_file_sha256=source.authoring_snapshot_file_sha256,
        source_generation_operation_sha256=source.source_generation_operation_sha256,
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
        review_content_bundle_sha256=review_content_bundle_hash(review_content_records(loaded)),
        semantic_group_count=report.semantic_group_count,
        source_item_count=report.source_item_count,
        literal_candidate_root_sha256="0" * 64,
    )
    return provisional.model_copy(
        update={"literal_candidate_root_sha256": literal_candidate_root_hash(provisional)}
    )


def _candidate_input_hashes(
    loaded: LoadedLiteralSource,
    candidate: CandidateManifest,
    candidate_manifest_path: Path,
) -> dict[str, str]:
    source = loaded.source_bundle
    return {
        "authoring_snapshot_file_sha256": source.authoring_snapshot_file_sha256,
        "authoring_snapshot_sha256": source.authoring_snapshot_sha256,
        "literal_source_bundle_sha256": source.literal_source_bundle_sha256,
        "m2_1_candidate_bundle_root_sha256": candidate.candidate_bundle_root_sha256,
        "m2_1_candidate_manifest_file_sha256": sha256_file(candidate_manifest_path),
        "m2_1_source_snapshot_sha256": candidate.source_snapshot_sha256,
        "source_generation_operation_sha256": source.source_generation_operation_sha256,
    }


def _materialized_paths(root: Path) -> tuple[Path, Path, Path]:
    literal_root = root / LITERAL_DIRECTORY
    return (
        literal_root / CANDIDATE_VALIDATION_REPORT_FILE,
        literal_root / COMPOSITE_CANDIDATE_FILE,
        literal_root / CANDIDATE_MATERIALIZATION_OPERATION_FILE,
    )


def _verify_materialization_operation(
    *,
    loaded: LoadedLiteralSource,
    candidate: CandidateManifest,
    candidate_manifest_path: Path,
    composite: LiteralCandidateManifest,
    report: LiteralValidationReport,
    current_git: object,
) -> LiteralOperationRecord:
    report_path, composite_path, operation_path = _materialized_paths(loaded.root)
    operation = read_canonical_model(operation_path, LiteralOperationRecord)
    if operation_hash(operation) != operation.operation_sha256:
        raise ValueError("Candidate-materialization operation hash does not reconstruct")
    if (
        operation.operation_kind != "materialize_literal_candidate"
        or operation.status != "COMPLETED"
        or operation.scientific_result is not False
        or operation.engineering_only != candidate.engineering_only
        or operation.git != current_git
        or operation.codex_spec_sha256 != composite.codex_spec_sha256
        or operation.resolved_configuration != loaded.source_bundle.resolved_configuration
        or operation.input_hashes
        != _candidate_input_hashes(loaded, candidate, candidate_manifest_path)
        or operation.output_hashes
        != {
            "literal_candidate_root_sha256": composite.literal_candidate_root_sha256,
            "literal_validation_report_sha256": report.literal_validation_report_sha256,
        }
        or operation.item_count != composite.source_item_count
        or operation.semantic_group_count != composite.semantic_group_count
        or operation.schema_counts != report.schema_counts
        or operation.level_counts != report.level_counts
        or operation.family_counts != report.family_counts
        or operation.package_versions != collect_package_versions()
        or operation.platform != collect_platform_information()
    ):
        raise ValueError("Candidate-materialization operation provenance is inconsistent")
    verify_artifact_records(
        loaded.root,
        operation.artifacts,
        expected_paths={
            f"{LITERAL_DIRECTORY}/{CANDIDATE_VALIDATION_REPORT_FILE}",
            f"{LITERAL_DIRECTORY}/{COMPOSITE_CANDIDATE_FILE}",
        },
    )
    expected_budget = _resource_budget(
        operation_id=operation.operation_id,
        started_at=operation.started_at,
        ended_at=operation.ended_at,
        elapsed=operation.resource_budget.elapsed_compute_seconds or 0.0,
        peak_memory=operation.resource_budget.peak_memory_bytes,
        witnesses=loaded.witness_bundle.witnesses,
        artifact_count=2,
        artifact_bytes=report_path.stat().st_size + composite_path.stat().st_size,
    )
    if operation.resource_budget != expected_budget:
        raise ValueError("Candidate-materialization ResourceBudget does not reconstruct")
    return operation


def _validate_literal_benchmark(
    *,
    source_root: Path,
    candidate_manifest_path: Path,
    repository_root: Path | None = None,
    enforce_source_location: bool,
) -> LiteralCandidateManifest:
    """Read-only validation of an already materialized M2.2 composite candidate."""

    repository = (
        find_repository_root(Path.cwd()) if repository_root is None else repository_root.resolve()
    )
    reject_literal_path_aliases(source_root, label="source_root")
    loaded = load_literal_source(source_root)
    report = _candidate_report(
        loaded,
        enforce_source_location=enforce_source_location,
        observed_source_root=source_root,
    )
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
    if sha256_file(repository / "CODEX_SPEC.md") != candidate.codex_spec_sha256:
        raise ValueError("Literal candidate CODEX_SPEC identity is stale")
    if not candidate.engineering_only:
        if candidate.git.dirty or current_git.dirty:
            raise ValueError("Outcome literal candidate requires clean Git state")
        if candidate.git.commit != current_git.commit:
            raise ValueError("Outcome literal candidate does not match the current branch head")
    composite = _composite_candidate(
        loaded=loaded,
        candidate=candidate,
        candidate_manifest_path=candidate_manifest_path,
        report=report,
    )
    report_path, composite_path, operation_path = _materialized_paths(loaded.root)
    if not all(path.is_file() for path in (report_path, composite_path, operation_path)):
        raise ValueError("Literal candidate has not been atomically materialized")
    if read_canonical_model(report_path, LiteralValidationReport) != report:
        raise ValueError("Materialized candidate literal-validation report is stale")
    if read_canonical_model(composite_path, LiteralCandidateManifest) != composite:
        raise ValueError("Materialized literal composite candidate is stale")
    _verify_materialization_operation(
        loaded=loaded,
        candidate=candidate,
        candidate_manifest_path=candidate_manifest_path,
        composite=composite,
        report=report,
        current_git=current_git,
    )
    return composite


def validate_literal_benchmark(
    *,
    source_root: Path,
    candidate_manifest_path: Path,
    repository_root: Path | None = None,
) -> LiteralCandidateManifest:
    """Read-only validation at the configured outcome-source location."""

    return _validate_literal_benchmark(
        source_root=source_root,
        candidate_manifest_path=candidate_manifest_path,
        repository_root=repository_root,
        enforce_source_location=True,
    )


def _after_literal_candidate_publication(_output: Path) -> None:
    """Injection seam for the first instruction after candidate publication."""


def materialize_literal_candidate(
    *,
    source_root: Path,
    candidate_manifest_path: Path,
    repository_root: Path | None = None,
) -> LiteralCandidateManifest:
    """Atomically publish M2.2 composite records after staged validation."""

    repository = (
        find_repository_root(Path.cwd()) if repository_root is None else repository_root.resolve()
    )
    reject_literal_path_aliases(source_root, label="source_root")
    loaded = load_literal_source(source_root)
    validate_loaded_literal_source(loaded, observed_root=source_root)
    source = loaded.root
    if any(path.exists() for path in _materialized_paths(source)):
        raise FileExistsError("Literal candidate materialization is write-once")
    validated = validate_benchmark_manifest(candidate_manifest_path, repository_root=repository)
    candidate = read_canonical_model(candidate_manifest_path, CandidateManifest)
    if validated.benchmark_version != loaded.source_manifest.benchmark_version:
        raise ValueError("M2.1 candidate and literal source versions differ")
    if validated.purpose is not loaded.source_manifest.purpose:
        raise ValueError("M2.1 candidate and literal source purposes differ")
    current_git = capture_git_state(repository)
    if not candidate.engineering_only and (
        candidate.git.dirty
        or current_git.dirty
        or candidate.git.commit != current_git.commit
        or loaded.source_bundle.git.commit != current_git.commit
        or loaded.source_bundle.git.dirty
    ):
        raise ValueError("Outcome materialization requires one clean exact Git commit")
    operation_id = create_run_id("literal-candidate-materialization")
    staging = source.parent / f".{source.name}.staging-{uuid.uuid4().hex}"
    backup: Path | None = None
    published = False
    started_at = utc_now()
    start_tick = time.perf_counter()
    tracing_was_active = tracemalloc.is_tracing()
    if not tracing_was_active:
        tracemalloc.start()
    try:
        shutil.copytree(source, staging)
        staged = load_literal_source(staging)
        _validate_loaded_literal_source_content(staged)
        report = _candidate_report(staged, enforce_source_location=False)
        composite = _composite_candidate(
            loaded=staged,
            candidate=candidate,
            candidate_manifest_path=candidate_manifest_path,
            report=report,
        )
        report_path, composite_path, operation_path = _materialized_paths(staging)
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
            witnesses=staged.witness_bundle.witnesses,
            artifact_count=len(retained),
            artifact_bytes=sum(path.stat().st_size for path in retained),
        )
        provisional = LiteralOperationRecord(
            operation_id=operation_id,
            operation_kind="materialize_literal_candidate",
            candidate_version=composite.candidate_version,
            purpose=composite.purpose,
            engineering_only=candidate.engineering_only,
            git=current_git,
            codex_spec_sha256=composite.codex_spec_sha256,
            resolved_configuration=staged.source_bundle.resolved_configuration,
            input_hashes=_candidate_input_hashes(staged, candidate, candidate_manifest_path),
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
            artifacts=make_artifact_records(staging, retained),
            resource_budget=budget,
            operation_sha256="0" * 64,
        )
        operation = provisional.model_copy(update={"operation_sha256": operation_hash(provisional)})
        write_canonical_json(operation_path, operation)
        _validate_literal_benchmark(
            source_root=staging,
            candidate_manifest_path=candidate_manifest_path,
            repository_root=repository,
            enforce_source_location=False,
        )
        backup = _publish_source(staging, source, operation_id)
        published = True
        _after_literal_candidate_publication(source)
        result = validate_literal_benchmark(
            source_root=source,
            candidate_manifest_path=candidate_manifest_path,
            repository_root=repository,
        )
        if backup is not None:
            _safe_remove_tree(backup, source.parent, marker=".authoring-backup-")
        return result
    except Exception as exc:
        peak = tracemalloc.get_traced_memory()[1] if tracemalloc.is_tracing() else None
        if not tracing_was_active and tracemalloc.is_tracing():
            tracemalloc.stop()
        notes: list[str] = []
        if published and source.exists():
            try:
                quarantined = _quarantine_publication(source, operation_id)
                if quarantined is not None:
                    notes.append(f"invalid publication quarantined at {quarantined.name}")
            except Exception as cleanup_exc:
                notes.append(f"publication cleanup failed: {cleanup_exc}")
        if backup is not None and backup.exists() and not source.exists():
            try:
                os.replace(backup, source)
            except Exception as restore_exc:
                notes.append(f"source restoration failed: {restore_exc}")
        try:
            _safe_remove_tree(staging, source.parent, marker=".staging-")
        except Exception as cleanup_exc:
            notes.append(f"staging cleanup failed: {cleanup_exc}")
        reason = f"{type(exc).__name__}: {exc}"
        if notes:
            reason += "; " + "; ".join(notes)
        failure_path: Path | None = None
        try:
            source_report = _candidate_report(loaded)
            failure_path = _write_literal_failure_record(
                output=source,
                operation_id=operation_id,
                operation_kind="materialize_literal_candidate",
                candidate_version=candidate.benchmark_version,
                purpose="engineering" if candidate.engineering_only else "outcome",
                engineering_only=candidate.engineering_only,
                repository_root=repository,
                resolved_configuration=loaded.source_bundle.resolved_configuration,
                input_hashes=_candidate_input_hashes(loaded, candidate, candidate_manifest_path),
                item_count=len(loaded.items),
                semantic_group_count=len(loaded.item_bindings.bindings),
                schema_counts=source_report.schema_counts,
                level_counts=source_report.level_counts,
                family_counts=source_report.family_counts,
                witnesses=loaded.witness_bundle.witnesses,
                started_at=started_at,
                elapsed=time.perf_counter() - start_tick,
                peak_memory=peak,
                failure_reason=reason,
            )
        except Exception as record_exc:
            reason += f"; failure-record write failed: {record_exc}"
        raise LiteralOperationError(
            reason,
            failure_record_path=None if failure_path is None else str(failure_path),
        ) from exc


def _load_materialized_source(
    source_root: Path,
) -> tuple[
    LoadedLiteralSource,
    LiteralCandidateManifest,
    LiteralValidationReport,
    LiteralOperationRecord,
]:
    reject_literal_path_aliases(source_root, label="source_root")
    loaded = load_literal_source(source_root)
    validate_loaded_literal_source(loaded, observed_root=source_root)
    report_path, composite_path, operation_path = _materialized_paths(loaded.root)
    if not all(path.is_file() for path in (report_path, composite_path, operation_path)):
        raise ValueError("Literal candidate has not been atomically materialized")
    report = read_canonical_model(report_path, LiteralValidationReport)
    if report != _candidate_report(loaded):
        raise ValueError("Materialized literal validation report does not reconstruct")
    composite = read_canonical_model(composite_path, LiteralCandidateManifest)
    if literal_candidate_root_hash(composite) != composite.literal_candidate_root_sha256:
        raise ValueError("Literal candidate root does not reconstruct")
    source = loaded.source_bundle
    if (
        composite.authoring_snapshot_sha256 != source.authoring_snapshot_sha256
        or composite.authoring_snapshot_file_sha256 != source.authoring_snapshot_file_sha256
        or composite.source_generation_operation_sha256 != source.source_generation_operation_sha256
        or composite.literal_source_bundle_sha256 != source.literal_source_bundle_sha256
        or composite.partition_plan_sha256 != source.partition_plan_sha256
        or composite.template_registry_sha256 != source.template_registry_sha256
        or composite.item_binding_bundle_sha256 != source.item_binding_bundle_sha256
        or composite.witness_bundle_sha256 != source.witness_bundle_sha256
        or composite.split_audit_sha256 != source.split_audit_sha256
        or composite.lexical_audit_sha256 != source.lexical_audit_sha256
    ):
        raise ValueError("Materialized literal candidate source bindings are stale")
    if (
        composite.literal_validation_report_sha256 != report.literal_validation_report_sha256
        or composite.review_content_bundle_sha256
        != review_content_bundle_hash(review_content_records(loaded))
        or composite.semantic_group_count != report.semantic_group_count
        or composite.source_item_count != report.source_item_count
    ):
        raise ValueError("Materialized literal candidate content bindings are stale")
    operation = read_canonical_model(operation_path, LiteralOperationRecord)
    if operation_hash(operation) != operation.operation_sha256:
        raise ValueError("Candidate-materialization operation hash does not reconstruct")
    if (
        operation.operation_kind != "materialize_literal_candidate"
        or operation.status != "COMPLETED"
    ):
        raise ValueError("Candidate-materialization operation kind/status is invalid")
    expected_inputs = {
        "authoring_snapshot_file_sha256": composite.authoring_snapshot_file_sha256,
        "authoring_snapshot_sha256": composite.authoring_snapshot_sha256,
        "literal_source_bundle_sha256": composite.literal_source_bundle_sha256,
        "m2_1_candidate_bundle_root_sha256": (composite.m2_1_candidate_bundle_root_sha256),
        "m2_1_candidate_manifest_file_sha256": (composite.m2_1_candidate_manifest_file_sha256),
        "m2_1_source_snapshot_sha256": composite.m2_1_source_snapshot_sha256,
        "source_generation_operation_sha256": (composite.source_generation_operation_sha256),
    }
    if operation.output_hashes != {
        "literal_candidate_root_sha256": composite.literal_candidate_root_sha256,
        "literal_validation_report_sha256": report.literal_validation_report_sha256,
    }:
        raise ValueError("Candidate-materialization outputs are stale")
    if (
        operation.scientific_result is not False
        or operation.engineering_only != loaded.source_manifest.engineering_only
        or operation.codex_spec_sha256 != composite.codex_spec_sha256
        or operation.resolved_configuration != source.resolved_configuration
        or operation.input_hashes != expected_inputs
        or operation.item_count != composite.source_item_count
        or operation.semantic_group_count != composite.semantic_group_count
        or operation.schema_counts != report.schema_counts
        or operation.level_counts != report.level_counts
        or operation.family_counts != report.family_counts
        or operation.package_versions != collect_package_versions()
        or operation.platform != collect_platform_information()
    ):
        raise ValueError("Candidate-materialization operation provenance is inconsistent")
    verify_artifact_records(
        loaded.root,
        operation.artifacts,
        expected_paths={
            f"{LITERAL_DIRECTORY}/{CANDIDATE_VALIDATION_REPORT_FILE}",
            f"{LITERAL_DIRECTORY}/{COMPOSITE_CANDIDATE_FILE}",
        },
    )
    expected_budget = _resource_budget(
        operation_id=operation.operation_id,
        started_at=operation.started_at,
        ended_at=operation.ended_at,
        elapsed=operation.resource_budget.elapsed_compute_seconds or 0.0,
        peak_memory=operation.resource_budget.peak_memory_bytes,
        witnesses=loaded.witness_bundle.witnesses,
        artifact_count=2,
        artifact_bytes=report_path.stat().st_size + composite_path.stat().st_size,
    )
    if operation.resource_budget != expected_budget:
        raise ValueError("Candidate-materialization ResourceBudget does not reconstruct")
    if not loaded.source_manifest.engineering_only:
        repository = find_repository_root(Path.cwd())
        current_git = capture_git_state(repository)
        if (
            current_git.dirty
            or current_git.commit != composite.git.commit
            or operation.git != composite.git
            or sha256_file(repository / "CODEX_SPEC.md") != composite.codex_spec_sha256
        ):
            raise ValueError("Outcome literal candidate does not match the current clean head")
    return loaded, composite, report, operation


def _review_items(
    loaded: LoadedLiteralSource,
    composite: LiteralCandidateManifest,
) -> tuple[LiteralReviewItem, ...]:
    items = {item.item_id: item for item in loaded.items}
    witnesses = {item.semantic_group_id: item for item in loaded.witness_bundle.witnesses}
    result: list[LiteralReviewItem] = []
    for binding in loaded.item_bindings.bindings:
        witness = witnesses[binding.semantic_group_id]
        left, right = (items[item_id] for item_id in binding.item_ids)
        full_frame_render_paths = tuple(
            f"renders/{binding.semantic_group_id}-{suffix}.png"
            for suffix in (
                "actual-before",
                "actual-after",
                "counterfactual-before",
                "counterfactual-after",
            )
        )
        review_zoom_render_paths = tuple(
            path.replace(".png", "-zoom.png") for path in full_frame_render_paths
        )
        cue_findings = tuple(
            finding
            for finding in loaded.lexical_audit.findings
            if binding.semantic_group_id in finding.semantic_group_ids
            or bool(set(binding.item_ids) & set(finding.item_ids))
        )
        result.append(
            LiteralReviewItem(
                semantic_group_id=binding.semantic_group_id,
                item_ids=binding.item_ids,
                schema_identity=binding.schema_identity,
                transfer_level=binding.transfer_level,
                partition=binding.partition,
                task_family=binding.task_family,
                scenario_case=binding.scenario_case,
                source_mechanism=binding.source_mechanism,
                target_mechanism=binding.target_mechanism,
                structural_novelty_dimensions=binding.structural_novelty_dimensions,
                structural_signatures=binding.structural_signatures,
                prompt=left.model_visible.prompt,
                instructions=left.model_visible.instructions or "",
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
                typed_actual_action_summary=witness.narrative_facts.actual_action_summary,
                typed_counterfactual_action_summary=(
                    witness.narrative_facts.counterfactual_action_summary
                ),
                actual_outcome_code=witness.actual_outcome_code,
                counterfactual_outcome_code=witness.counterfactual_outcome_code,
                allowed_initial_difference_paths=(
                    witness.intervention_contract.allowed_initial_difference_paths
                ),
                observed_initial_difference_paths=witness.observed_initial_difference_paths,
                allowed_action_difference_paths=(
                    witness.intervention_contract.allowed_action_difference_paths
                ),
                observed_action_difference_paths=witness.observed_action_difference_paths,
                declared_equal_fields=witness.intervention_contract.required_equal_scopes,
                simulator_rationale=(
                    f"Independent {binding.scenario_case.value} replay applied the "
                    f"{witness.intervention_contract.causal_factor.value} contract and "
                    "reproduced both typed outcomes."
                ),
                cue_findings=cue_findings,
                lexical_cue_annotations=left.scientific_annotations.lexical_cue_annotations,
                provenance=left.provenance,
                human_validation=left.human_validation,
                governance_status=(
                    "engineering_only"
                    if loaded.source_manifest.engineering_only
                    else "owner_review_pending"
                ),
                full_frame_render_paths=full_frame_render_paths,
                review_zoom_render_paths=review_zoom_render_paths,
                authoring_snapshot_sha256=composite.authoring_snapshot_sha256,
                literal_candidate_root_sha256=composite.literal_candidate_root_sha256,
                witness_bundle_sha256=composite.witness_bundle_sha256,
                literal_validation_report_sha256=composite.literal_validation_report_sha256,
                witness_sha256=witness.witness_sha256,
                item_binding_sha256=binding.item_binding_sha256,
            )
        )
    return tuple(result)


def _write_markdown(path: Path, *, title: str, lines: list[str]) -> None:
    path.write_text(
        "\n".join((f"# {title}", "", *lines, "")),
        encoding="utf-8",
        newline="\n",
    )


def _review_render_states(loaded: LoadedLiteralSource) -> tuple[tuple[str, Any], ...]:
    records: list[tuple[str, Any]] = []
    for witness in loaded.witness_bundle.witnesses:
        group = witness.semantic_group_id
        records.extend(
            (
                (f"renders/{group}-actual-before.png", witness.initial_privileged_state),
                (f"renders/{group}-actual-after.png", witness.actual_final_state),
                (
                    f"renders/{group}-counterfactual-before.png",
                    witness.counterfactual_initial_privileged_state,
                ),
                (
                    f"renders/{group}-counterfactual-after.png",
                    witness.counterfactual_final_state,
                ),
            )
        )
    return tuple(records)


def _set_pixel(
    pixels: bytearray,
    *,
    width: int,
    height: int,
    x: int,
    y: int,
    colour: tuple[int, int, int],
) -> None:
    if 0 <= x < width and 0 <= y < height:
        offset = 3 * (y * width + x)
        pixels[offset : offset + 3] = bytes(colour)


def _draw_line(
    pixels: bytearray,
    *,
    width: int,
    height: int,
    start: tuple[int, int],
    end: tuple[int, int],
    colour: tuple[int, int, int],
) -> None:
    x0, y0 = start
    x1, y1 = end
    delta_x = abs(x1 - x0)
    step_x = 1 if x0 < x1 else -1
    delta_y = -abs(y1 - y0)
    step_y = 1 if y0 < y1 else -1
    error = delta_x + delta_y
    while True:
        for offset_x, offset_y in ((0, 0), (1, 0), (0, 1)):
            _set_pixel(
                pixels,
                width=width,
                height=height,
                x=x0 + offset_x,
                y=y0 + offset_y,
                colour=colour,
            )
        if (x0, y0) == (x1, y1):
            break
        doubled = 2 * error
        if doubled >= delta_y:
            error += delta_y
            x0 += step_x
        if doubled <= delta_x:
            error += delta_x
            y0 += step_y


def _entity_centre(state: WorldState, entity_id: str, *, size: int) -> tuple[int, int]:
    entity = state.entity(entity_id)
    x = (2 * entity.x + entity.width) * size // (2 * state.coordinate_max)
    y = size - (2 * entity.y + entity.height) * size // (2 * state.coordinate_max)
    return x, y


def _review_zoom_pixels(state: WorldState, full_pixels: bytes) -> tuple[bytes, str]:
    """Create a deterministic review-only detail view while preserving the full render."""

    size = 128
    overlaid = bytearray(full_pixels)
    connections: tuple[Attachment | Tether, ...] = (*state.attachments, *state.tethers)
    for connection in connections:
        _draw_line(
            overlaid,
            width=size,
            height=size,
            start=_entity_centre(state, connection.object_id, size=size),
            end=_entity_centre(state, connection.anchor_id, size=size),
            colour=(43, 47, 54) if connection.active else (174, 179, 188),
        )
    relevant_roles = {
        EntityRole.OBJECT,
        EntityRole.SUPPORT,
        EntityRole.ANCHOR,
        EntityRole.CONTAINER,
        EntityRole.GATE,
    }
    relevant = [entity for entity in state.entities if entity.role in relevant_roles]
    if not relevant:
        raise ValueError("Review zoom has no inspectable physical entities")
    left = min(entity.x for entity in relevant) * size // state.coordinate_max
    right = max(entity.x + entity.width for entity in relevant) * size // state.coordinate_max
    top = size - max(entity.y + entity.height for entity in relevant) * size // state.coordinate_max
    bottom = size - min(entity.y for entity in relevant) * size // state.coordinate_max
    padding = 4
    left = max(0, left - padding)
    right = min(size, max(left + 1, right + padding))
    top = max(0, top - padding)
    bottom = min(size, max(top + 1, bottom + padding))
    crop_width = right - left
    crop_height = bottom - top
    scale = min((size - 8) / crop_width, (size - 8) / crop_height)
    output_width = max(1, int(crop_width * scale))
    output_height = max(1, int(crop_height * scale))
    offset_x = (size - output_width) // 2
    offset_y = (size - output_height) // 2
    source_image = Image.frombytes("RGB", (size, size), bytes(overlaid))
    crop = source_image.crop((left, top, right, bottom)).resize(
        (output_width, output_height), resample=Image.Resampling.NEAREST
    )
    zoom = Image.new("RGB", (size, size), BACKGROUND)
    zoom.paste(crop, (offset_x, offset_y))
    raw = zoom.tobytes()
    logical = canonical_record_sha256(
        {
            "view_kind": "literal-review-zoom-v1",
            "source_full_frame_raw_pixel_sha256": hashlib.sha256(full_pixels).hexdigest(),
            "raw_pixel_sha256": hashlib.sha256(raw).hexdigest(),
            "width": size,
            "height": size,
            "mode": "RGB",
        }
    )
    return raw, logical


def _cue_disposition(
    loaded: LoadedLiteralSource, composite: LiteralCandidateManifest
) -> LiteralCueDispositionRecord:
    required = {
        summary.category: summary.category_membership_sha256
        for summary in loaded.lexical_audit.category_summaries
        if summary.owner_disposition_required
    }
    consequential = tuple(
        finding.finding_id
        for finding in loaded.lexical_audit.findings
        if finding.disposition is not LiteralAuditStatus.PASS
    )
    return LiteralCueDispositionRecord(
        candidate_version=composite.candidate_version,
        lexical_audit_sha256=composite.lexical_audit_sha256,
        candidate_root_sha256=composite.literal_candidate_root_sha256,
        required_category_membership_hashes=dict(sorted(required.items())),
        consequential_finding_ids=consequential,
    )


def _render_bundle_hash(records: tuple[LiteralRenderRecord, ...]) -> str:
    return canonical_record_sha256(
        {"render_records": [record.model_dump(mode="json") for record in records]}
    )


def _after_literal_review_publication(_output: Path) -> None:
    """Injection seam for the first instruction after review publication."""


def _cleanup_failed_review_publication(output: Path, operation_id: str) -> tuple[str, ...]:
    """Best-effort quarantine cascade that never replaces the primary failure."""

    notes: list[str] = []
    if not output.exists():
        return ()
    quarantine = output.parent / f".{output.name}.invalid-review-{operation_id}"
    if quarantine.exists():
        notes.append(f"review quarantine destination already exists: {quarantine.name}")
    else:
        try:
            os.replace(output, quarantine)
            return (f"invalid review quarantined by replace at {quarantine.name}",)
        except Exception as cleanup_exc:
            notes.append(
                f"review quarantine replace failed: {type(cleanup_exc).__name__}: {cleanup_exc}"
            )
        try:
            shutil.move(str(output), str(quarantine))
            notes.append(f"invalid review quarantined by move at {quarantine.name}")
            return tuple(notes)
        except Exception as cleanup_exc:
            notes.append(
                f"review quarantine move failed: {type(cleanup_exc).__name__}: {cleanup_exc}"
            )
    try:
        shutil.rmtree(output)
        notes.append("invalid review removed after quarantine failures")
        return tuple(notes)
    except Exception as cleanup_exc:
        notes.append(f"review removal failed: {type(cleanup_exc).__name__}: {cleanup_exc}")
    if not output.exists():
        notes.append("invalid review is absent after partial removal")
        return tuple(notes)
    manifest = output / REVIEW_MANIFEST_FILE
    if not manifest.exists():
        notes.append("invalid review manifest is absent after partial removal")
        return tuple(notes)
    try:
        manifest.unlink()
        notes.append("invalid review manifest removed to prevent validation")
        return tuple(notes)
    except Exception as cleanup_exc:
        notes.append(
            "review manifest unlink invalidation failed: "
            f"{type(cleanup_exc).__name__}: {cleanup_exc}"
        )
    invalidated = output / f".{REVIEW_MANIFEST_FILE}.invalidated-{operation_id}"
    try:
        os.replace(manifest, invalidated)
        notes.append("invalid review manifest renamed to prevent validation")
        return tuple(notes)
    except Exception as cleanup_exc:
        notes.append(
            "review manifest rename invalidation failed: "
            f"{type(cleanup_exc).__name__}: {cleanup_exc}"
        )
    try:
        manifest.write_bytes(b'{"invalidated":true}\n')
        notes.append("invalid review manifest overwritten to prevent validation")
    except Exception as cleanup_exc:
        notes.append(
            "review manifest overwrite invalidation failed: "
            f"{type(cleanup_exc).__name__}: {cleanup_exc}"
        )
    return tuple(notes)


def _valid_failure_record(path: Path, operation_id: str) -> bool:
    try:
        record = read_canonical_model(path, LiteralOperationRecord)
    except Exception:
        return False
    return (
        record.operation_id == operation_id
        and record.status == "FAILED"
        and operation_hash(record) == record.operation_sha256
    )


def _recover_review_failure_record(
    output: Path,
    operation_id: str,
) -> tuple[Path | None, tuple[str, ...]]:
    """Retain the strongest valid failure record after publication itself fails."""

    notes: list[str] = []
    final = output.parent / f".{output.name}.failure-{operation_id}.json"
    if final.is_file() and _valid_failure_record(final, operation_id):
        return final, ()
    staged = sorted(output.parent.glob(f"..{output.name}.failure-{operation_id}.json.staging-*"))
    valid_staged = next(
        (path for path in staged if path.is_file() and _valid_failure_record(path, operation_id)),
        None,
    )
    if valid_staged is None:
        return None, ()
    if not final.exists():
        try:
            shutil.move(str(valid_staged), str(final))
            if _valid_failure_record(final, operation_id):
                notes.append("governed failure record preserved by move fallback")
                return final, tuple(notes)
        except Exception as preserve_exc:
            notes.append(
                "failure-record move fallback failed: "
                f"{type(preserve_exc).__name__}: {preserve_exc}"
            )
    notes.append(f"governed staged failure record retained at {valid_staged.name}")
    return valid_staged, tuple(notes)


def build_literal_review(*, source_root: Path, output_root: Path) -> LiteralOperationResult:
    """Atomically build a private review bundle with full and zoomed renders."""

    loaded, composite, report, materialization = _load_materialized_source(source_root)
    reject_literal_path_aliases(output_root, label="review_root")
    validate_literal_root_location(
        loaded,
        observed_root=output_root,
        root_kind="review",
        must_exist=False,
    )
    output = output_root.resolve()
    if output.exists():
        raise FileExistsError(f"Literal review destination already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    operation_id = create_run_id("literal-review-build")
    staging = output.parent / f".{output.name}.staging-{uuid.uuid4().hex}"
    started_at = utc_now()
    start_tick = time.perf_counter()
    tracing_was_active = tracemalloc.is_tracing()
    if not tracing_was_active:
        tracemalloc.start()
    published = False
    try:
        staging.mkdir(parents=False, exist_ok=False)
        review_items = _review_items(loaded, composite)
        write_canonical_jsonl(staging / REVIEW_ITEMS_FILE, list(review_items))
        write_canonical_json(staging / "split_audit.json", loaded.split_audit)
        write_canonical_json(staging / "lexical_audit.json", loaded.lexical_audit)
        write_canonical_json(staging / "literal_validation_report.json", report)
        write_canonical_json(staging / "witness_bundle.json", loaded.witness_bundle)
        write_canonical_json(
            staging / "pending_owner_review.json",
            pending_owner_review(composite.candidate_version),
        )
        cue_disposition = _cue_disposition(loaded, composite)
        write_canonical_json(staging / CUE_DISPOSITION_FILE, cue_disposition)
        _write_markdown(
            staging / "aggregate_summary.md",
            title="M2.2 private literal candidate review summary",
            lines=[
                f"Candidate version: `{composite.candidate_version}`",
                f"Purpose: `{composite.purpose}`",
                f"Semantic groups: {composite.semantic_group_count}",
                f"Question groups: {report.question_group_count}",
                f"Causal scenarios: {report.causal_scenario_count}",
                (f"Independent structural strata: {report.independent_structural_stratum_count}"),
                f"Cross-family matched variants: {report.matched_variant_count}",
                f"Cosmetic variants (not unique coverage): {report.cosmetic_variant_count}",
                f"Source records: {composite.source_item_count}",
                f"Lexical status: `{loaded.lexical_audit.status.value}`",
                "Status: `CANDIDATE_VALIDATED_OWNER_REVIEW_PENDING`",
                "Human validation, rights, ethics, freezing, and evaluation remain pending.",
            ],
        )
        _write_markdown(
            staging / "reviewer_checklist.md",
            title="M2.2 owner review decision template",
            lines=[
                "- [ ] Narrative facts exactly match the retained authoring snapshot and replay.",
                "- [ ] Reverse variants preserve semantics and the stable answer.",
                "- [ ] Structural novelty evidence supports every declared L2 classification.",
                "- [ ] Actual/counterfactual pairs obey prospective intervention contracts.",
                "- [ ] Every owner-review-required lexical finding is dispositioned by its exact "
                "subcategory membership hash or exact finding ID.",
                "- [ ] The decision binds the exact PR, head, operations, and manifests.",
                "",
                "Decision: PENDING",
            ],
        )
        render_records: list[LiteralRenderRecord] = []
        for relative, state in _review_render_states(loaded):
            pixels, scientific_hash = render_raw_pixels(state, width=128, height=128)
            save_png(staging / relative, pixels, width=128, height=128)
            full_raw_hash = hashlib.sha256(pixels).hexdigest()
            render_records.append(
                LiteralRenderRecord(
                    path=relative,
                    view_kind="scientific-full-frame",
                    raw_pixel_sha256=full_raw_hash,
                    logical_render_sha256=scientific_hash,
                    scientific_render_sha256=scientific_hash,
                )
            )
            zoom_relative = relative.replace(".png", "-zoom.png")
            zoom_pixels, zoom_hash = _review_zoom_pixels(state, pixels)
            save_png(staging / zoom_relative, zoom_pixels, width=128, height=128)
            render_records.append(
                LiteralRenderRecord(
                    path=zoom_relative,
                    view_kind="review-zoom",
                    raw_pixel_sha256=hashlib.sha256(zoom_pixels).hexdigest(),
                    logical_render_sha256=zoom_hash,
                    source_full_frame_raw_pixel_sha256=full_raw_hash,
                )
            )
        render_tuple = tuple(sorted(render_records, key=lambda item: item.path))
        content_files = sorted(
            (path for path in staging.rglob("*") if path.is_file()),
            key=lambda path: path.relative_to(staging).as_posix(),
        )
        ended_at = utc_now()
        peak = tracemalloc.get_traced_memory()[1] if tracemalloc.is_tracing() else None
        if not tracing_was_active and tracemalloc.is_tracing():
            tracemalloc.stop()
        budget = _resource_budget(
            operation_id=operation_id,
            started_at=started_at,
            ended_at=ended_at,
            elapsed=time.perf_counter() - start_tick,
            peak_memory=peak,
            witnesses=(),
            artifact_count=len(content_files),
            artifact_bytes=sum(path.stat().st_size for path in content_files),
        )
        repository = find_repository_root(Path.cwd())
        current_git = capture_git_state(repository)
        if not loaded.source_manifest.engineering_only and (
            current_git.dirty or current_git.commit != composite.git.commit
        ):
            raise ValueError("Outcome review requires the clean candidate commit")
        content_hash = composite.review_content_bundle_sha256
        render_hash = _render_bundle_hash(render_tuple)
        operation_provisional = LiteralOperationRecord(
            operation_id=operation_id,
            operation_kind="build_literal_review",
            candidate_version=composite.candidate_version,
            purpose=composite.purpose,
            engineering_only=loaded.source_manifest.engineering_only,
            git=current_git,
            codex_spec_sha256=composite.codex_spec_sha256,
            resolved_configuration=loaded.source_bundle.resolved_configuration,
            input_hashes={
                "authoring_snapshot_file_sha256": composite.authoring_snapshot_file_sha256,
                "authoring_snapshot_sha256": composite.authoring_snapshot_sha256,
                "candidate_materialization_operation_sha256": materialization.operation_sha256,
                "literal_candidate_root_sha256": composite.literal_candidate_root_sha256,
                "review_content_bundle_sha256": content_hash,
                "source_generation_operation_sha256": (
                    composite.source_generation_operation_sha256
                ),
            },
            output_hashes={
                "render_bundle_sha256": render_hash,
                "review_content_bundle_sha256": content_hash,
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
            artifacts=make_artifact_records(staging, content_files),
            resource_budget=budget,
            operation_sha256="0" * 64,
        )
        operation = operation_provisional.model_copy(
            update={"operation_sha256": operation_hash(operation_provisional)}
        )
        write_canonical_json(staging / REVIEW_OPERATION_FILE, operation)
        manifest_artifacts = make_artifact_records(
            staging,
            sorted(
                (path for path in staging.rglob("*") if path.is_file()),
                key=lambda path: path.relative_to(staging).as_posix(),
            ),
        )
        manifest_provisional = LiteralReviewManifest(
            candidate_version=composite.candidate_version,
            git=current_git,
            codex_spec_sha256=composite.codex_spec_sha256,
            authoring_snapshot_sha256=composite.authoring_snapshot_sha256,
            authoring_snapshot_file_sha256=composite.authoring_snapshot_file_sha256,
            source_generation_operation_sha256=(composite.source_generation_operation_sha256),
            candidate_materialization_operation_sha256=materialization.operation_sha256,
            review_operation_sha256=operation.operation_sha256,
            literal_candidate_root_sha256=composite.literal_candidate_root_sha256,
            witness_bundle_sha256=composite.witness_bundle_sha256,
            literal_validation_report_sha256=composite.literal_validation_report_sha256,
            review_content_bundle_sha256=content_hash,
            render_records=render_tuple,
            artifacts=manifest_artifacts,
            review_manifest_sha256="0" * 64,
        )
        manifest = manifest_provisional.model_copy(
            update={"review_manifest_sha256": review_manifest_hash(manifest_provisional)}
        )
        write_canonical_json(staging / REVIEW_MANIFEST_FILE, manifest)
        _validate_literal_review_content(
            root=staging,
            loaded=loaded,
            composite=composite,
            report=report,
            materialization=materialization,
        )
        os.replace(staging, output)
        published = True
        _after_literal_review_publication(output)
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
    except Exception as exc:
        peak = tracemalloc.get_traced_memory()[1] if tracemalloc.is_tracing() else None
        if not tracing_was_active and tracemalloc.is_tracing():
            tracemalloc.stop()
        notes: list[str] = []
        if published and output.exists():
            try:
                notes.extend(_cleanup_failed_review_publication(output, operation_id))
            except Exception as cleanup_exc:
                notes.append(
                    "review publication cleanup cascade failed unexpectedly: "
                    f"{type(cleanup_exc).__name__}: {cleanup_exc}"
                )
        try:
            _safe_remove_tree(staging, output.parent, marker=".staging-")
        except Exception as cleanup_exc:
            notes.append(f"review staging cleanup failed: {cleanup_exc}")
        reason = f"{type(exc).__name__}: {exc}"
        if notes:
            reason += "; " + "; ".join(notes)
        failure_path: Path | None = None
        try:
            failure_path = _write_literal_failure_record(
                output=output,
                operation_id=operation_id,
                operation_kind="build_literal_review",
                candidate_version=composite.candidate_version,
                purpose=composite.purpose,
                engineering_only=loaded.source_manifest.engineering_only,
                repository_root=find_repository_root(Path.cwd()),
                resolved_configuration=loaded.source_bundle.resolved_configuration,
                input_hashes={
                    "authoring_snapshot_file_sha256": (composite.authoring_snapshot_file_sha256),
                    "authoring_snapshot_sha256": composite.authoring_snapshot_sha256,
                    "candidate_materialization_operation_sha256": (
                        materialization.operation_sha256
                    ),
                    "literal_candidate_root_sha256": (composite.literal_candidate_root_sha256),
                    "review_content_bundle_sha256": (composite.review_content_bundle_sha256),
                    "source_generation_operation_sha256": (
                        composite.source_generation_operation_sha256
                    ),
                },
                item_count=composite.source_item_count,
                semantic_group_count=composite.semantic_group_count,
                schema_counts=report.schema_counts,
                level_counts=report.level_counts,
                family_counts=report.family_counts,
                witnesses=(),
                started_at=started_at,
                elapsed=time.perf_counter() - start_tick,
                peak_memory=peak,
                failure_reason=reason,
            )
        except Exception as record_exc:
            record_notes = [
                f"failure-record write failed: {type(record_exc).__name__}: {record_exc}"
            ]
            failure_path, recovery_notes = _recover_review_failure_record(output, operation_id)
            record_notes.extend(recovery_notes)
            reason += "; " + "; ".join(record_notes)
        raise LiteralOperationError(
            reason,
            failure_record_path=None if failure_path is None else str(failure_path),
        ) from exc


def _validate_literal_review_content(
    *,
    root: Path,
    loaded: LoadedLiteralSource,
    composite: LiteralCandidateManifest,
    report: LiteralValidationReport,
    materialization: LiteralOperationRecord,
) -> LiteralReviewManifest:
    """Reconstruct review content at a caller-authorised publication location."""

    manifest = read_canonical_model(root / REVIEW_MANIFEST_FILE, LiteralReviewManifest)
    expected_manifest_paths = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name != REVIEW_MANIFEST_FILE
    }
    verify_artifact_records(root, manifest.artifacts, expected_paths=expected_manifest_paths)
    if review_manifest_hash(manifest) != manifest.review_manifest_sha256:
        raise ValueError("Literal review-manifest hash does not reconstruct")
    if (
        (not loaded.source_manifest.engineering_only and manifest.git != composite.git)
        or manifest.codex_spec_sha256 != composite.codex_spec_sha256
        or manifest.authoring_snapshot_sha256 != composite.authoring_snapshot_sha256
        or manifest.authoring_snapshot_file_sha256 != composite.authoring_snapshot_file_sha256
        or manifest.source_generation_operation_sha256
        != composite.source_generation_operation_sha256
        or manifest.candidate_materialization_operation_sha256 != materialization.operation_sha256
        or manifest.literal_candidate_root_sha256 != composite.literal_candidate_root_sha256
        or manifest.witness_bundle_sha256 != composite.witness_bundle_sha256
        or manifest.literal_validation_report_sha256 != composite.literal_validation_report_sha256
        or manifest.review_content_bundle_sha256 != composite.review_content_bundle_sha256
    ):
        raise ValueError("Review manifest candidate/provenance bindings are stale")
    expected_render_records: list[LiteralRenderRecord] = []
    for relative, state in _review_render_states(loaded):
        expected_pixels, scientific_hash = render_raw_pixels(state, width=128, height=128)
        path = root / relative
        with Image.open(path) as image:
            image.load()
            if image.format != "PNG" or image.mode != "RGB" or image.size != (128, 128):
                raise ValueError(f"Review render format/mode/dimensions invalid: {relative}")
            decoded = image.tobytes()
        if decoded != expected_pixels:
            raise ValueError(f"Review render decoded pixels differ from replay: {relative}")
        expected_render_records.append(
            LiteralRenderRecord(
                path=relative,
                view_kind="scientific-full-frame",
                raw_pixel_sha256=hashlib.sha256(decoded).hexdigest(),
                logical_render_sha256=scientific_hash,
                scientific_render_sha256=scientific_hash,
            )
        )
        zoom_relative = relative.replace(".png", "-zoom.png")
        expected_zoom, zoom_hash = _review_zoom_pixels(state, expected_pixels)
        zoom_path = root / zoom_relative
        with Image.open(zoom_path) as image:
            image.load()
            if image.format != "PNG" or image.mode != "RGB" or image.size != (128, 128):
                raise ValueError(f"Review zoom format/mode/dimensions invalid: {zoom_relative}")
            decoded_zoom = image.tobytes()
        if decoded_zoom != expected_zoom:
            raise ValueError(f"Review zoom decoded pixels differ from replay: {zoom_relative}")
        expected_render_records.append(
            LiteralRenderRecord(
                path=zoom_relative,
                view_kind="review-zoom",
                raw_pixel_sha256=hashlib.sha256(decoded_zoom).hexdigest(),
                logical_render_sha256=zoom_hash,
                source_full_frame_raw_pixel_sha256=hashlib.sha256(decoded).hexdigest(),
            )
        )
    render_records = tuple(sorted(expected_render_records, key=lambda item: item.path))
    if manifest.render_records != render_records:
        raise ValueError("Review render records do not reconstruct")
    observed_items = read_jsonl_models(
        root / REVIEW_ITEMS_FILE,
        LiteralReviewItem,
        require_canonical=True,
    )
    if observed_items != _review_items(loaded, composite):
        raise ValueError("Review item file does not reconstruct from private source")
    pending = read_canonical_model(root / "pending_owner_review.json", LiteralPendingOwnerReview)
    if pending != pending_owner_review(manifest.candidate_version):
        raise ValueError("Pending owner-review record does not reconstruct")
    cue = read_canonical_model(root / CUE_DISPOSITION_FILE, LiteralCueDispositionRecord)
    expected_cue = _cue_disposition(loaded, composite)
    if cue != expected_cue:
        raise ValueError("Cue-disposition template does not reconstruct")
    operation = read_canonical_model(root / REVIEW_OPERATION_FILE, LiteralOperationRecord)
    if operation_hash(operation) != operation.operation_sha256:
        raise ValueError("Literal review-operation hash does not reconstruct")
    if operation.operation_sha256 != manifest.review_operation_sha256:
        raise ValueError("Review manifest binds a different review operation")
    expected_inputs = {
        "authoring_snapshot_file_sha256": composite.authoring_snapshot_file_sha256,
        "authoring_snapshot_sha256": composite.authoring_snapshot_sha256,
        "candidate_materialization_operation_sha256": materialization.operation_sha256,
        "literal_candidate_root_sha256": composite.literal_candidate_root_sha256,
        "review_content_bundle_sha256": composite.review_content_bundle_sha256,
        "source_generation_operation_sha256": composite.source_generation_operation_sha256,
    }
    expected_outputs = {
        "render_bundle_sha256": _render_bundle_hash(render_records),
        "review_content_bundle_sha256": composite.review_content_bundle_sha256,
    }
    content_paths = expected_manifest_paths - {REVIEW_OPERATION_FILE}
    if (
        operation.operation_kind != "build_literal_review"
        or operation.status != "COMPLETED"
        or operation.scientific_result is not False
        or operation.git != manifest.git
        or operation.codex_spec_sha256 != manifest.codex_spec_sha256
        or operation.resolved_configuration != loaded.source_bundle.resolved_configuration
        or operation.input_hashes != expected_inputs
        or operation.output_hashes != expected_outputs
        or operation.item_count != composite.source_item_count
        or operation.semantic_group_count != composite.semantic_group_count
        or operation.schema_counts != report.schema_counts
        or operation.level_counts != report.level_counts
        or operation.family_counts != report.family_counts
        or operation.package_versions != collect_package_versions()
        or operation.platform != collect_platform_information()
    ):
        raise ValueError("Literal review-operation provenance is inconsistent")
    verify_artifact_records(root, operation.artifacts, expected_paths=content_paths)
    expected_budget = _resource_budget(
        operation_id=operation.operation_id,
        started_at=operation.started_at,
        ended_at=operation.ended_at,
        elapsed=operation.resource_budget.elapsed_compute_seconds or 0.0,
        peak_memory=operation.resource_budget.peak_memory_bytes,
        witnesses=(),
        artifact_count=len(content_paths),
        artifact_bytes=sum((root / relative).stat().st_size for relative in content_paths),
    )
    if operation.resource_budget != expected_budget:
        raise ValueError("Literal review ResourceBudget does not reconstruct")
    return manifest


def validate_literal_review(*, review_root: Path, source_root: Path) -> LiteralReviewManifest:
    """Read back a review bundle only at configured non-engineering roots."""

    reject_literal_path_aliases(review_root, label="review_root")
    loaded, composite, report, materialization = _load_materialized_source(source_root)
    validate_literal_root_location(
        loaded,
        observed_root=review_root,
        root_kind="review",
    )
    root = review_root.resolve()
    return _validate_literal_review_content(
        root=root,
        loaded=loaded,
        composite=composite,
        report=report,
        materialization=materialization,
    )


def inspect_literal_item(
    *,
    source_root: Path,
    item_id: str,
    render_path: Path | None = None,
) -> dict[str, Any]:
    """Explicitly inspect one private item, optionally writing an after-state render."""

    reject_literal_path_aliases(source_root, label="source_root")
    loaded = load_literal_source(source_root)
    validate_loaded_literal_source(loaded, observed_root=source_root)
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
