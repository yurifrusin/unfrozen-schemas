"""Independent validation for private candidates, public metadata, and frozen versions."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel

from unfrozen_schemas.config import sha256_file
from unfrozen_schemas.evaluation.benchmark_hashing import (
    bundle_hashes,
    canonical_logical_bytes,
    derive_built_records,
    freeze_approval_hash,
    frozen_manifest_hash,
    public_metadata_bundle_hash,
    source_snapshot_hash,
)
from unfrozen_schemas.evaluation.benchmark_models import (
    ENGINEERING_VERSION,
    PRODUCTION_VERSION,
    SELECTION_VERSION,
    AdjudicationStatus,
    BenchmarkOperationRecord,
    BenchmarkPurpose,
    BuiltBenchmarkItem,
    CandidateManifest,
    CoverageSummary,
    FreezeApproval,
    FrozenManifest,
    GovernanceStatus,
    HumanValidationStatus,
    ImmutableReceipt,
    LifecycleState,
    OriginClassification,
    PrivateAnswerRecord,
    PublicManifest,
    ResolvedBenchmarkConfig,
    RightsStatus,
    SourceItemRecord,
    SourceManifest,
    SourceSnapshot,
    SourceSnapshotHeader,
    ValidationReport,
)
from unfrozen_schemas.evaluation.benchmark_persistence import (
    read_canonical_model,
    read_jsonl_models,
    resolve_safe_relative_path,
    verify_artifact_records,
)

CANDIDATE_MANIFEST_FILENAME = "candidate_manifest.json"
FROZEN_MANIFEST_FILENAME = "frozen_manifest.json"
CANDIDATE_ARTIFACT_PATHS: set[str] = {
    "coverage_summary.json",
    "items.jsonl",
    "operation_record.json",
    "private_answers.jsonl",
    "public_manifest.json",
    "resolved_benchmark_config.json",
    "resource_budget.json",
    "source_snapshot.json",
    "validation_report.json",
}
FROZEN_EXTRA_ARTIFACT_PATHS: set[str] = {
    CANDIDATE_MANIFEST_FILENAME,
    "freeze_approval.json",
    "freeze_operation.json",
    "freeze_resource_budget.json",
    "immutable_receipt.json",
}
CANDIDATE_BUDGET_PATHS: set[str] = {
    "coverage_summary.json",
    "items.jsonl",
    "private_answers.jsonl",
    "public_manifest.json",
    "resolved_benchmark_config.json",
    "resource_budget.json",
    "source_snapshot.json",
    "validation_report.json",
}
FROZEN_BUDGET_PATHS: set[str] = (
    CANDIDATE_ARTIFACT_PATHS
    | {CANDIDATE_MANIFEST_FILENAME, "freeze_approval.json", "immutable_receipt.json"}
    | {"freeze_resource_budget.json"}
)
VALIDATION_CHECKS: tuple[str, ...] = (
    "canonical_encoding",
    "schema_versions",
    "lifecycle_state",
    "purpose_quarantine",
    "reserved_versions",
    "stable_item_and_revision_identity",
    "unique_item_and_option_ids",
    "answer_reference_integrity",
    "reverse_pair_integrity",
    "logical_hash_reconstruction",
    "artifact_hashes_and_safe_paths",
    "mandatory_artifact_set",
    "public_private_partition",
    "recursive_answer_leakage",
    "rights_human_validation_and_ethics_fields",
    "resource_budget_v2",
    "operation_provenance",
)

_FORBIDDEN_PUBLIC_KEYS = {
    "correctoptionid",
    "answerindex",
    "expectedanswer",
    "schemaconsistentoptionid",
    "goldlabel",
    "answerrationale",
    "rationale",
    "privatevalidationnotes",
    "privateanswerrecordsha256",
    "completeprivateitemrecordsha256",
}
_ENGINEERING_PROHIBITED_WORDS = re.compile(
    r"\b(containment|container|support|inside|outside|boundary|metaphor|source[ -]?path[ -]?goal|"
    r"schema|force|blockage|tether|trajectory)\b",
    flags=re.IGNORECASE,
)


def ensure_lifecycle_transition(before: LifecycleState, after: LifecycleState) -> None:
    allowed = {
        (LifecycleState.SOURCE, LifecycleState.PRIVATE),
        (LifecycleState.PRIVATE, LifecycleState.FROZEN),
    }
    if (before, after) not in allowed:
        raise ValueError(f"Illegal benchmark lifecycle transition: {before.value} -> {after.value}")


def _normalised_key(key: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(key).casefold())


def _walk_public(value: Any, *, context: str = "$") -> Iterable[tuple[str, Any]]:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_context = f"{context}.{key}"
            yield key_context, (key, item)
            yield from _walk_public(item, context=key_context)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            yield from _walk_public(item, context=f"{context}[{index}]")


def assert_public_answer_isolation(
    public_values: Sequence[BaseModel | Mapping[str, Any]],
    answers: Sequence[PrivateAnswerRecord],
    items: Sequence[BuiltBenchmarkItem],
) -> None:
    secrets: set[str] = set()
    for answer in answers:
        secrets.add(answer.correct_option_id)
        for value in (
            answer.answer_rationale,
            answer.simulator_verification_reference,
            answer.adjudication_reference,
            answer.private_answer_record_sha256,
        ):
            if value:
                secrets.add(value)
    for item in items:
        secrets.add(item.complete_private_item_record_sha256)
        secrets.add(item.model_visible.prompt)
        if item.model_visible.instructions:
            secrets.add(item.model_visible.instructions)
        secrets.update(option.text for option in item.model_visible.ordered_options)
    for public in public_values:
        for context, pair in _walk_public(public):
            key, value = cast(tuple[object, Any], pair)
            if _normalised_key(key) in _FORBIDDEN_PUBLIC_KEYS:
                raise ValueError(f"Public metadata contains answer-equivalent field at {context}")
            if isinstance(value, str) and value in secrets:
                raise ValueError(
                    f"Public metadata contains a private answer or item value at {context}"
                )


def validate_reverse_pairs(items: Sequence[SourceItemRecord | BuiltBenchmarkItem]) -> None:
    groups: dict[str, list[SourceItemRecord | BuiltBenchmarkItem]] = defaultdict(list)
    for item in items:
        pair_id = item.model_visible.reverse_pair_id
        if pair_id is not None:
            groups[pair_id].append(item)
    for pair_id, members in groups.items():
        if len(members) != 2:
            raise ValueError(f"Reverse pair {pair_id!r} must contain exactly two variants")
        left, right = sorted(members, key=lambda item: item.item_id)
        if left.item_id == right.item_id:
            raise ValueError(f"Reverse pair {pair_id!r} requires distinct item IDs")
        if left.model_visible.variant_id == right.model_visible.variant_id:
            raise ValueError(f"Reverse pair {pair_id!r} requires distinct variant IDs")
        left_ids = left.model_visible.option_permutation
        right_ids = right.model_visible.option_permutation
        if set(left_ids) != set(right_ids) or right_ids != tuple(reversed(left_ids)):
            raise ValueError(f"Reverse pair {pair_id!r} has an invalid option permutation")


def _validate_common_items(
    items: Sequence[SourceItemRecord | BuiltBenchmarkItem],
    *,
    purpose: BenchmarkPurpose,
    engineering_only: bool,
) -> None:
    item_ids = [item.item_id for item in items]
    if len(item_ids) != len(set(item_ids)):
        raise ValueError("Duplicate stable item IDs are prohibited within one benchmark version")
    if any(item.purpose is not purpose or item.identity_purpose is not purpose for item in items):
        raise ValueError("Every item purpose and identity purpose must match its bundle")
    for item in items:
        if item.engineering_only != engineering_only:
            raise ValueError("Item engineering status must match its bundle")
        if engineering_only:
            visible_text = canonical_logical_bytes(item.model_visible).decode("utf-8")
            if _ENGINEERING_PROHIBITED_WORDS.search(visible_text):
                raise ValueError(
                    f"Engineering fixture item {item.item_id} uses prohibited scientific vocabulary"
                )
    validate_reverse_pairs(items)


def load_source_directory(
    source_directory: Path, *, benchmark_version: str, purpose: BenchmarkPurpose
) -> tuple[SourceManifest, SourceSnapshot]:
    source_root = source_directory.resolve()
    manifest_path = source_root / "source_manifest.json"
    if not manifest_path.is_file():
        raise ValueError("Source directory requires source_manifest.json")
    source_manifest = SourceManifest.model_validate_json(manifest_path.read_bytes())
    if source_manifest.benchmark_version != benchmark_version:
        raise ValueError("CLI benchmark version does not match source manifest")
    if source_manifest.purpose is not purpose:
        raise ValueError("CLI benchmark purpose does not match immutable source purpose")
    items_path = resolve_safe_relative_path(source_root, source_manifest.items_file)
    items = read_jsonl_models(items_path, SourceItemRecord, require_canonical=False)
    if len(items) != source_manifest.expected_item_count:
        raise ValueError("Source item count does not match source manifest")
    _validate_common_items(
        items, purpose=source_manifest.purpose, engineering_only=source_manifest.engineering_only
    )
    header = SourceSnapshotHeader(
        benchmark_version=source_manifest.benchmark_version,
        purpose=source_manifest.purpose,
        engineering_only=source_manifest.engineering_only,
        scientific_eligible=source_manifest.scientific_eligible,
        promotable=source_manifest.promotable,
        item_count=len(items),
        rights_determination_reference=source_manifest.rights_determination_reference,
        human_validation_reference=source_manifest.human_validation_reference,
        ethics_determination_reference=source_manifest.ethics_determination_reference,
        production_prerequisites=source_manifest.production_prerequisites,
    )
    from unfrozen_schemas.evaluation.benchmark_hashing import make_source_snapshot

    snapshot = make_source_snapshot(header, items)
    return source_manifest, snapshot


def coverage_summary(
    *,
    version: str,
    purpose: BenchmarkPurpose,
    items: Sequence[BuiltBenchmarkItem],
    engineering_only: bool,
    scientific_eligible: bool,
) -> CoverageSummary:
    def counts(values: Iterable[str]) -> dict[str, int]:
        return dict(sorted(Counter(values).items()))

    return CoverageSummary(
        benchmark_version=version,
        purpose=purpose,
        item_count=len(items),
        task_family_counts=counts(item.task_family_slug for item in items),
        schema_designation_counts=counts(item.schema_designation.value for item in items),
        partition_counts=counts(item.partition_id for item in items),
        transfer_level_counts=counts(
            "not_applicable" if item.transfer_level is None else f"L{item.transfer_level}"
            for item in items
        ),
        target_domain_family_counts=counts(item.target_domain_family for item in items),
        source_mechanism_family_counts=counts(item.source_mechanism_family for item in items),
        trained_schema_role_counts=counts(
            item.scientific_annotations.trained_schema_role.value for item in items
        ),
        reverse_pair_count=len(
            {
                item.model_visible.reverse_pair_id
                for item in items
                if item.model_visible.reverse_pair_id
            }
        ),
        closed_book_eligible_count=sum(item.model_visible.closed_book_eligible for item in items),
        open_book_eligible_count=sum(item.model_visible.open_book_eligible for item in items),
        engineering_only=engineering_only,
        scientific_eligible=scientific_eligible,
    )


def public_manifest(
    *,
    version: str,
    purpose: BenchmarkPurpose,
    items: Sequence[BuiltBenchmarkItem],
    engineering_only: bool,
    scientific_eligible: bool,
    promotable: bool,
    source_snapshot_sha256: str,
    hashes: Mapping[str, str],
) -> PublicManifest:
    def counts(values: Iterable[str]) -> dict[str, int]:
        return dict(sorted(Counter(values).items()))

    return PublicManifest(
        benchmark_version=version,
        purpose=purpose,
        engineering_only=engineering_only,
        scientific_eligible=scientific_eligible,
        promotable=promotable,
        item_count=len(items),
        origin_classification_counts=counts(
            item.provenance.origin_classification.value for item in items
        ),
        rights_status_counts=counts(item.provenance.rights_status.value for item in items),
        human_validation_status_counts=counts(
            item.human_validation.validation_status.value for item in items
        ),
        ethics_status_counts=counts(item.provenance.ethics_status.value for item in items),
        source_snapshot_sha256=source_snapshot_sha256,
        **dict(hashes),
    )


def validate_cross_purpose_records(
    groups: Mapping[BenchmarkPurpose, Sequence[BuiltBenchmarkItem]],
) -> None:
    seen_ids: dict[str, BenchmarkPurpose] = {}
    seen_hashes: dict[str, BenchmarkPurpose] = {}
    seen_content: dict[str, BenchmarkPurpose] = {}
    for purpose, items in groups.items():
        for item in items:
            previous = seen_ids.get(item.item_id)
            if previous is not None and previous is not purpose:
                raise ValueError(
                    f"Item ID {item.item_id!r} appears across prohibited purposes: "
                    f"{previous.value}, {purpose.value}"
                )
            seen_ids[item.item_id] = purpose
            previous_hash = seen_hashes.get(item.model_visible_sha256)
            if previous_hash is not None and previous_hash is not purpose:
                raise ValueError(
                    "Model-visible content hash appears across prohibited benchmark purposes: "
                    f"{previous_hash.value}, {purpose.value}"
                )
            seen_hashes[item.model_visible_sha256] = purpose
            content_fingerprint = hashlib.sha256(
                canonical_logical_bytes(item.model_visible)
            ).hexdigest()
            previous_content = seen_content.get(content_fingerprint)
            if previous_content is not None and previous_content is not purpose:
                raise ValueError(
                    "Equivalent model-visible content appears across prohibited benchmark "
                    "purposes: "
                    f"{previous_content.value}, {purpose.value}"
                )
            seen_content[content_fingerprint] = purpose


def _verify_resource_budget(
    root: Path, operation: BenchmarkOperationRecord, paths: set[str]
) -> None:
    budget = operation.resource_budget
    observed_count = len(paths)
    observed_bytes = sum(resolve_safe_relative_path(root, path).stat().st_size for path in paths)
    if budget.stored_artifact_count != observed_count:
        raise ValueError("ResourceBudget stored_artifact_count does not match retained files")
    if budget.stored_artifact_bytes != observed_bytes:
        raise ValueError("ResourceBudget stored_artifact_bytes does not match retained files")
    zero_fields = (
        "external_language_tokens",
        "self_generated_language_tokens",
        "sensor_observations",
        "sensor_bytes",
        "environment_steps",
        "optimisation_steps",
        "forward_passes",
        "backward_passes",
    )
    if any(getattr(budget, field) != 0 for field in zero_fields):
        raise ValueError(
            "M2.1 benchmark operations must report unused scientific resources as zero"
        )


def _load_candidate_payload(
    manifest_path: Path,
) -> tuple[CandidateManifest, tuple[BuiltBenchmarkItem, ...], tuple[PrivateAnswerRecord, ...]]:
    manifest = read_canonical_model(manifest_path, CandidateManifest)
    root = manifest_path.parent.resolve()
    verify_artifact_records(root, manifest.artifacts, expected_paths=CANDIDATE_ARTIFACT_PATHS)
    snapshot = read_canonical_model(root / manifest.source_snapshot_path, SourceSnapshot)
    if tuple(sorted(snapshot.items, key=lambda item: item.item_id)) != snapshot.items:
        raise ValueError("Source snapshot items must use canonical item_id ordering")
    observed_snapshot_hash = source_snapshot_hash(snapshot.header, snapshot.items)
    if observed_snapshot_hash != snapshot.source_snapshot_sha256:
        raise ValueError("Source snapshot logical hash mismatch")
    if manifest.source_snapshot_sha256 != observed_snapshot_hash:
        raise ValueError("Candidate manifest source snapshot hash mismatch")
    if snapshot.header.item_count != len(snapshot.items):
        raise ValueError("Source snapshot item count mismatch")
    items = read_jsonl_models(
        root / manifest.items_path, BuiltBenchmarkItem, require_canonical=True
    )
    answers = read_jsonl_models(
        root / manifest.private_answers_path, PrivateAnswerRecord, require_canonical=True
    )
    if tuple(sorted(items, key=lambda item: item.item_id)) != items:
        raise ValueError("Built items must use canonical item_id ordering")
    if tuple(sorted(answers, key=lambda item: item.item_id)) != answers:
        raise ValueError("Private answers must use canonical item_id ordering")
    expected = tuple(derive_built_records(source_item) for source_item in snapshot.items)
    if items != tuple(pair[0] for pair in expected):
        raise ValueError("Built item records do not reconstruct from the private source snapshot")
    if answers != tuple(pair[1] for pair in expected):
        raise ValueError("Private answers do not reconstruct from the private source snapshot")
    if len(items) != len(answers) or len(items) != manifest.item_count:
        raise ValueError("Source, item, answer, and manifest counts must agree")
    if tuple(item.item_id for item in items) != tuple(answer.item_id for answer in answers):
        raise ValueError("Private answers must correspond one-to-one with built items")
    _validate_common_items(
        items, purpose=manifest.purpose, engineering_only=manifest.engineering_only
    )
    for item, answer in zip(items, answers, strict=True):
        option_ids = {option.option_id for option in item.model_visible.ordered_options}
        if answer.correct_option_id not in option_ids:
            raise ValueError(f"Private answer for {item.item_id} references an invalid option")
    observed_bundles = bundle_hashes(
        benchmark_version=manifest.benchmark_version,
        purpose=manifest.purpose.value,
        source_snapshot_sha256=manifest.source_snapshot_sha256,
        items=items,
        answers=answers,
    )
    for field, observed in observed_bundles.items():
        if getattr(manifest, field) != observed:
            raise ValueError(f"Candidate logical hash mismatch: {field}")
    config = read_canonical_model(
        root / manifest.resolved_configuration_path, ResolvedBenchmarkConfig
    )
    if (
        config.benchmark_version != manifest.benchmark_version
        or config.purpose is not manifest.purpose
    ):
        raise ValueError("Resolved benchmark configuration does not match candidate manifest")
    coverage = read_canonical_model(root / manifest.coverage_summary_path, CoverageSummary)
    expected_coverage = coverage_summary(
        version=manifest.benchmark_version,
        purpose=manifest.purpose,
        items=items,
        engineering_only=manifest.engineering_only,
        scientific_eligible=manifest.scientific_eligible,
    )
    if coverage != expected_coverage:
        raise ValueError("Coverage summary does not reconstruct from candidate items")
    public = read_canonical_model(root / manifest.public_manifest_path, PublicManifest)
    public_expected = public_manifest(
        version=manifest.benchmark_version,
        purpose=manifest.purpose,
        items=items,
        engineering_only=manifest.engineering_only,
        scientific_eligible=manifest.scientific_eligible,
        promotable=manifest.promotable,
        source_snapshot_sha256=manifest.source_snapshot_sha256,
        hashes={
            "model_visible_bundle_sha256": manifest.model_visible_bundle_sha256,
            "annotation_metadata_bundle_sha256": manifest.annotation_metadata_bundle_sha256,
            "candidate_bundle_root_sha256": manifest.candidate_bundle_root_sha256,
            "private_answer_bundle_sha256": manifest.private_answer_bundle_sha256,
        },
    )
    if public != public_expected:
        raise ValueError("Public manifest does not reconstruct from private candidate identity")
    observed_public_hash = public_metadata_bundle_hash(public, coverage)
    if manifest.public_metadata_bundle_sha256 != observed_public_hash:
        raise ValueError("Public metadata bundle logical hash mismatch")
    assert_public_answer_isolation((public, coverage), answers, items)
    report = read_canonical_model(root / manifest.validation_report_path, ValidationReport)
    if (
        report.benchmark_version != manifest.benchmark_version
        or report.lifecycle_state is not LifecycleState.PRIVATE
        or report.purpose is not manifest.purpose
        or report.item_count != manifest.item_count
        or report.checks != VALIDATION_CHECKS
    ):
        raise ValueError("Persisted validation report does not describe this candidate")
    operation = read_canonical_model(
        root / manifest.operation_record_path, BenchmarkOperationRecord
    )
    if (
        operation.operation_kind != "build_benchmark"
        or operation.status != "COMPLETED"
        or operation.lifecycle_state_before is not LifecycleState.SOURCE
        or operation.lifecycle_state_after is not LifecycleState.PRIVATE
        or operation.benchmark_version != manifest.benchmark_version
        or operation.purpose is not manifest.purpose
        or operation.item_count != manifest.item_count
        or operation.git != manifest.git
        or operation.codex_spec_sha256 != manifest.codex_spec_sha256
        or operation.resolved_configuration != config
    ):
        raise ValueError("Build operation provenance does not match candidate manifest")
    persisted_budget = json.loads(
        (root / manifest.resource_budget_path).read_text(encoding="utf-8")
    )
    if persisted_budget != operation.resource_budget.model_dump(mode="json"):
        raise ValueError("resource_budget.json does not equal the build operation ResourceBudget")
    verify_artifact_records(root, operation.artifacts, expected_paths=CANDIDATE_BUDGET_PATHS)
    _verify_resource_budget(root, operation, CANDIDATE_BUDGET_PATHS)
    return manifest, items, answers


def _validate_freeze_eligibility(
    candidate: CandidateManifest,
    items: Sequence[BuiltBenchmarkItem],
    approval: FreezeApproval,
) -> None:
    if candidate.git.dirty:
        raise ValueError("Freeze requires a PRIVATE candidate built from an exact clean Git commit")
    if approval.decision != "APPROVED":
        raise ValueError("Freeze approval decision must be affirmative")
    if candidate.engineering_only:
        if candidate.benchmark_version != ENGINEERING_VERSION:
            raise ValueError(
                "Only the declared engineering fixture version may use engineering freeze"
            )
        if approval.approval_class != "engineering_fixture":
            raise ValueError("Engineering candidate requires an engineering-only approval")
        for item in items:
            if (
                item.scientific_eligible
                or item.promotable
                or item.provenance.origin_classification
                is not OriginClassification.ENGINEERING_FIXTURE
                or item.provenance.rights_status is not RightsStatus.NOT_APPLICABLE_ENGINEERING
                or item.provenance.ethics_status is not GovernanceStatus.NOT_APPLICABLE_ENGINEERING
                or item.human_validation.validation_status
                is not HumanValidationStatus.NOT_APPLICABLE_ENGINEERING
                or item.human_validation.adjudication_status
                is not AdjudicationStatus.NOT_APPLICABLE_ENGINEERING
            ):
                raise ValueError("Engineering freeze item is not unmistakably non-scientific")
        return
    for item in items:
        if item.provenance.rights_status not in {RightsStatus.CLEARED, RightsStatus.LICENSED}:
            raise ValueError("Production freeze requires resolved rights/licensing for every item")
        if not item.provenance.licence_reference:
            raise ValueError("Production freeze requires an item-level licence/rights reference")
        if item.provenance.ethics_status is not GovernanceStatus.APPROVED:
            raise ValueError(
                "Production freeze requires an approved ethics/governance determination"
            )
        if not item.provenance.ethics_reference:
            raise ValueError("Production freeze requires an item-level ethics reference")
        if item.human_validation.validation_status is not HumanValidationStatus.PASSED:
            raise ValueError("Production freeze requires passed human validation")
    if candidate.production_prerequisites is None or approval.production_prerequisites is None:
        raise ValueError("Production freeze requires explicit M2.2-M2.5 prerequisite hashes")
    if candidate.production_prerequisites != approval.production_prerequisites:
        raise ValueError("Candidate and approval production prerequisite hashes disagree")
    if (
        approval.model_selection_approval_sha256
        != candidate.production_prerequisites.model_selection_approval_sha256
    ):
        raise ValueError("Model-selection approval hash does not match production prerequisites")
    if candidate.benchmark_version == PRODUCTION_VERSION:
        raise ValueError(
            "v1_core production freezing is not enabled in M2.1; explicit M2.2-M2.5 artifacts "
            "must be implemented and reviewed before M2.6"
        )
    if candidate.benchmark_version == SELECTION_VERSION:
        raise ValueError("selection_probe_v1 remains reserved for separately reviewed M2.5 work")


def verify_freeze_approval(
    candidate_manifest_path: Path,
    candidate: CandidateManifest,
    items: Sequence[BuiltBenchmarkItem],
    approval: FreezeApproval,
) -> None:
    if freeze_approval_hash(approval) != approval.approval_sha256:
        raise ValueError("Freeze approval logical hash mismatch")
    expected: dict[str, object] = {
        "benchmark_version": candidate.benchmark_version,
        "benchmark_purpose": candidate.purpose,
        "engineering_only": candidate.engineering_only,
        "candidate_manifest_sha256": sha256_file(candidate_manifest_path),
        "candidate_bundle_root_sha256": candidate.candidate_bundle_root_sha256,
        "private_answer_bundle_sha256": candidate.private_answer_bundle_sha256,
        "public_metadata_bundle_sha256": candidate.public_metadata_bundle_sha256,
        "codex_spec_sha256": candidate.codex_spec_sha256,
        "git_commit": candidate.git.commit,
        "rights_determination_reference": candidate.rights_determination_reference,
        "human_validation_reference": candidate.human_validation_reference,
        "ethics_determination_reference": candidate.ethics_determination_reference,
    }
    for field, value in expected.items():
        if getattr(approval, field) != value:
            raise ValueError(f"Freeze approval mismatch: {field}")
    _validate_freeze_eligibility(candidate, items, approval)


def _load_frozen_payload(manifest_path: Path) -> FrozenManifest:
    manifest = read_canonical_model(manifest_path, FrozenManifest)
    root = manifest_path.parent.resolve()
    verify_artifact_records(
        root,
        manifest.artifacts,
        expected_paths=CANDIDATE_ARTIFACT_PATHS | FROZEN_EXTRA_ARTIFACT_PATHS,
    )
    if frozen_manifest_hash(manifest) != manifest.frozen_manifest_sha256:
        raise ValueError("Frozen manifest logical hash mismatch")
    candidate_path = root / manifest.candidate_manifest_path
    candidate, items, _ = _load_candidate_payload(candidate_path)
    approval = read_canonical_model(root / manifest.freeze_approval_path, FreezeApproval)
    verify_freeze_approval(candidate_path, candidate, items, approval)
    receipt = read_canonical_model(root / manifest.immutable_receipt_path, ImmutableReceipt)
    expected_receipt = ImmutableReceipt(
        benchmark_version=candidate.benchmark_version,
        purpose=candidate.purpose,
        candidate_manifest_sha256=sha256_file(candidate_path),
        candidate_bundle_root_sha256=candidate.candidate_bundle_root_sha256,
        freeze_approval_sha256=approval.approval_sha256,
    )
    if receipt != expected_receipt:
        raise ValueError("Immutable receipt does not match candidate and approval")
    operation = read_canonical_model(
        root / manifest.operation_record_path, BenchmarkOperationRecord
    )
    if (
        operation.operation_kind != "freeze_benchmark"
        or operation.status != "COMPLETED"
        or operation.lifecycle_state_before is not LifecycleState.PRIVATE
        or operation.lifecycle_state_after is not LifecycleState.FROZEN
        or operation.benchmark_version != candidate.benchmark_version
        or operation.purpose is not candidate.purpose
        or operation.item_count != candidate.item_count
    ):
        raise ValueError("Freeze operation provenance does not match frozen manifest")
    persisted_budget = json.loads(
        (root / manifest.resource_budget_path).read_text(encoding="utf-8")
    )
    if persisted_budget != operation.resource_budget.model_dump(mode="json"):
        raise ValueError("freeze_resource_budget.json does not equal freeze operation budget")
    verify_artifact_records(root, operation.artifacts, expected_paths=FROZEN_BUDGET_PATHS)
    _verify_resource_budget(root, operation, FROZEN_BUDGET_PATHS)
    expected_manifest_fields: dict[str, object] = {
        "benchmark_version": candidate.benchmark_version,
        "purpose": candidate.purpose,
        "engineering_only": candidate.engineering_only,
        "scientific_eligible": candidate.scientific_eligible,
        "promotable": candidate.promotable,
        "item_count": candidate.item_count,
        "candidate_manifest_sha256": sha256_file(candidate_path),
        "candidate_bundle_root_sha256": candidate.candidate_bundle_root_sha256,
        "private_answer_bundle_sha256": candidate.private_answer_bundle_sha256,
        "public_metadata_bundle_sha256": candidate.public_metadata_bundle_sha256,
        "freeze_approval_sha256": approval.approval_sha256,
        "codex_spec_sha256": candidate.codex_spec_sha256,
        "git_commit": candidate.git.commit,
    }
    for field, value in expected_manifest_fields.items():
        if getattr(manifest, field) != value:
            raise ValueError(f"Frozen manifest mismatch: {field}")
    return manifest


def validate_benchmark_manifest(
    manifest_path: Path, *, against_manifests: Sequence[Path] = ()
) -> CandidateManifest | FrozenManifest:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    kind = payload.get("manifest_kind")
    current_items: tuple[BuiltBenchmarkItem, ...]
    result: CandidateManifest | FrozenManifest
    if kind == "benchmark_private_candidate":
        candidate_result, current_items, _ = _load_candidate_payload(manifest_path)
        result = candidate_result
    elif kind == "benchmark_frozen":
        frozen_result = _load_frozen_payload(manifest_path)
        result = frozen_result
        _, current_items, _ = _load_candidate_payload(
            manifest_path.parent / frozen_result.candidate_manifest_path
        )
    else:
        raise ValueError(f"Unsupported benchmark manifest kind: {kind!r}")
    groups: dict[BenchmarkPurpose, list[BuiltBenchmarkItem]] = defaultdict(list)
    groups[result.purpose].extend(current_items)
    for other_path in against_manifests:
        other_payload = json.loads(other_path.read_text(encoding="utf-8"))
        if other_payload.get("manifest_kind") == "benchmark_private_candidate":
            other_candidate, other_items, _ = _load_candidate_payload(other_path)
            other_purpose = other_candidate.purpose
        elif other_payload.get("manifest_kind") == "benchmark_frozen":
            other_frozen = _load_frozen_payload(other_path)
            other_purpose = other_frozen.purpose
            _, other_items, _ = _load_candidate_payload(
                other_path.parent / other_frozen.candidate_manifest_path
            )
        else:
            raise ValueError(f"Unsupported quarantine manifest: {other_path}")
        groups[other_purpose].extend(other_items)
    validate_cross_purpose_records(groups)
    return result


def audit_tracked_benchmark_paths(repository_root: Path) -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "ls-files", "-z", "--", "benchmarks"],
        cwd=repository_root,
        check=True,
        capture_output=True,
    )
    tracked = tuple(sorted(path for path in completed.stdout.decode("utf-8").split("\0") if path))
    prohibited_names = {
        "candidate_manifest.json",
        "items.jsonl",
        "private_answers.jsonl",
        "source_manifest.json",
        "source_snapshot.json",
    }
    for declared in tracked:
        path = Path(declared)
        if path.name in prohibited_names:
            raise ValueError(
                f"Tracked production benchmark path is answer-bearing/private: {declared}"
            )
        if (
            any(part in {PRODUCTION_VERSION, SELECTION_VERSION} for part in path.parts)
            and path.name != "README.md"
        ):
            raise ValueError(f"M2.1 must not track reserved benchmark content: {declared}")
    return tracked
