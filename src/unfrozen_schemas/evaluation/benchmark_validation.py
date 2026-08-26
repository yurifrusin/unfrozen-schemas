"""Independent validation for private candidates, public metadata, and frozen versions."""

from __future__ import annotations

import json
import re
import subprocess
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from unfrozen_schemas.budgets import ResourceBudget
from unfrozen_schemas.config import sha256_file
from unfrozen_schemas.evaluation.benchmark_hashing import (
    bundle_hashes,
    canonical_logical_bytes,
    derive_built_records,
    exact_displayed_input_fingerprint,
    freeze_approval_hash,
    frozen_manifest_hash,
    hash_domain,
    normalise_equivalent_text,
    order_neutral_item_content_fingerprint,
    public_metadata_bundle_hash,
    quarantine_scope_hash,
    source_snapshot_hash,
)
from unfrozen_schemas.evaluation.benchmark_models import (
    CANONICAL_QUARANTINE_ROOTS,
    ENGINEERING_VERSION,
    PRODUCTION_VERSION,
    SELECTION_VERSION,
    AdjudicationStatus,
    AnswerProvenance,
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
    QuarantineManifestReference,
    QuarantineScope,
    QuarantineScopeDeclaration,
    QuarantineScopeMode,
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
    resolve_candidate_version_path,
    resolve_frozen_version_path,
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
    "quarantine_scope.json",
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
    "quarantine_scope.json",
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
    "mandatory_hash_bound_quarantine_scope",
    "purpose_neutral_content_fingerprints",
    "reserved_versions",
    "stable_item_and_revision_identity",
    "unique_item_and_option_ids",
    "answer_reference_integrity",
    "reverse_pair_integrity",
    "reverse_pair_equivalence_contract",
    "logical_hash_reconstruction",
    "artifact_hashes_and_safe_paths",
    "mandatory_artifact_set",
    "public_private_partition",
    "recursive_answer_leakage",
    "cross_record_consistency",
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
    "solution",
    "correctchoice",
    "correctchoiceid",
    "targetoption",
    "targetoptionid",
    "truthlabel",
}
_PERMITTED_ANSWER_AGGREGATE_KEYS = {
    "privateanswerbundlesha256",
    "containsperitemanswerhashes",
    "containsanswersorrationales",
}
_REVERSE_TRANSFORMATION_RECORD = "reversed option presentation"
_SAFE_TRACKED_BENCHMARK_PATHS: frozenset[str] = frozenset(
    {
        "benchmarks/README.md",
        "benchmarks/frozen/README.md",
        "benchmarks/private/README.md",
        "benchmarks/selection/README.md",
        "benchmarks/source/README.md",
    }
)
_ENGINEERING_PROHIBITED_WORDS = re.compile(
    r"\b(containment|container|support|inside|outside|boundary|metaphor|source[ -]?path[ -]?goal|"
    r"schema|force|blockage|tether|trajectory)\b",
    flags=re.IGNORECASE,
)


def _require_canonical_candidate_location(
    manifest_path: Path,
    candidate: CandidateManifest,
    repository_root: Path | None,
    *,
    allow_canonical_frozen_copy: bool,
) -> None:
    """Reject every non-engineering candidate outside its exact canonical location."""

    if candidate.engineering_only:
        return
    if repository_root is None:
        raise ValueError(
            "Non-engineering candidate validation requires the canonical repository root"
        )
    repository = repository_root.resolve()
    expected = (
        resolve_candidate_version_path(
            repository,
            candidate.benchmark_version,
            candidate.purpose,
        )
        / CANDIDATE_MANIFEST_FILENAME
    )
    actual = manifest_path.resolve(strict=True)
    if actual == expected:
        return
    if allow_canonical_frozen_copy and candidate.purpose in {
        BenchmarkPurpose.OUTCOME,
        BenchmarkPurpose.RETENTION,
    }:
        frozen_copy = (
            resolve_frozen_version_path(
                repository,
                candidate.benchmark_version,
                candidate.purpose,
            )
            / CANDIDATE_MANIFEST_FILENAME
        )
        if actual == frozen_copy:
            return
    raise ValueError(
        "Non-engineering candidate manifest is outside its canonical purpose-specific "
        f"location: expected {expected}"
    )


def _require_canonical_frozen_location(
    manifest_path: Path,
    manifest: FrozenManifest,
    repository_root: Path | None,
) -> None:
    """Reject every non-engineering frozen manifest outside its exact version directory."""

    if manifest.engineering_only:
        return
    if repository_root is None:
        raise ValueError("Non-engineering frozen validation requires the canonical repository root")
    expected = (
        resolve_frozen_version_path(
            repository_root.resolve(),
            manifest.benchmark_version,
            manifest.purpose,
        )
        / FROZEN_MANIFEST_FILENAME
    )
    if manifest_path.resolve(strict=True) != expected:
        raise ValueError(
            "Non-engineering frozen manifest is outside its canonical location: "
            f"expected {expected}"
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


def _is_forbidden_public_key(key: object) -> bool:
    normalised = _normalised_key(key)
    if normalised in _PERMITTED_ANSWER_AGGREGATE_KEYS:
        return False
    if normalised in _FORBIDDEN_PUBLIC_KEYS:
        return True
    answer_terms = ("answer", "correct", "gold", "solution", "target", "truth")
    identity_terms = ("option", "choice", "label", "index", "id", "rationale", "evidence")
    return any(term in normalised for term in answer_terms) and any(
        term in normalised for term in identity_terms
    )


def _walk_public_scalars(value: Any, *, context: str = "$") -> Iterable[tuple[str, Any]]:
    """Yield every mapping key and every scalar leaf, including sequence members."""

    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_context = f"{context}.{key}"
            yield f"{key_context}<key>", key
            yield from _walk_public_scalars(item, context=key_context)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            yield from _walk_public_scalars(item, context=f"{context}[{index}]")
    else:
        yield context, value


def _normalise_leakage_scalar(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    line_normalised = value.replace("\r\n", "\n").replace("\r", "\n")
    unicode_normalised = unicodedata.normalize("NFC", line_normalised)
    return " ".join(unicode_normalised.split()).casefold()


def _contains_private_value(public_value: str, secret: str) -> bool:
    if not secret:
        return False
    if public_value == secret:
        return True
    if len(secret) >= 4:
        return secret in public_value
    escaped = re.escape(secret)
    return re.search(rf"(?<![\w]){escaped}(?![\w])", public_value) is not None


def assert_public_answer_isolation(
    public_values: Sequence[BaseModel | Mapping[str, Any]],
    answers: Sequence[PrivateAnswerRecord],
    items: Sequence[BuiltBenchmarkItem],
) -> None:
    raw_secrets: set[str] = set()
    for answer in answers:
        raw_secrets.add(answer.correct_option_id)
        for value in (
            answer.answer_rationale,
            answer.simulator_verification_reference,
            answer.adjudication_reference,
            answer.private_answer_record_sha256,
        ):
            if value:
                raw_secrets.add(value)
    for item in items:
        raw_secrets.update(
            {
                item.complete_private_item_record_sha256,
                item.model_visible_sha256,
                item.annotation_metadata_sha256,
                item.exact_displayed_input_fingerprint_sha256,
                item.order_neutral_item_content_fingerprint_sha256,
                item.model_visible.prompt,
                item.model_visible.variant_id,
            }
        )
        if item.model_visible.instructions:
            raw_secrets.add(item.model_visible.instructions)
        if item.model_visible.reverse_pair_id:
            raw_secrets.add(item.model_visible.reverse_pair_id)
        raw_secrets.update(option.option_id for option in item.model_visible.ordered_options)
        raw_secrets.update(option.text for option in item.model_visible.ordered_options)
        raw_secrets.update(item.model_visible.option_permutation)
    secrets = {
        normalised for value in raw_secrets if (normalised := _normalise_leakage_scalar(value))
    }
    for public in public_values:
        for context, value in _walk_public_scalars(public):
            if context.endswith("<key>") and _is_forbidden_public_key(value):
                raise ValueError(f"Public metadata contains answer-equivalent field at {context}")
            normalised_value = _normalise_leakage_scalar(value)
            if normalised_value is not None and any(
                _contains_private_value(normalised_value, secret) for secret in secrets
            ):
                raise ValueError(
                    f"Public metadata contains a private answer or item value at {context}"
                )


def _pair_text(value: str | None) -> str | None:
    if value is None:
        return None
    return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))


def _pair_answer_payload(
    item: SourceItemRecord | BuiltBenchmarkItem,
    answer_by_id: Mapping[str, PrivateAnswerRecord],
) -> dict[str, Any]:
    if isinstance(item, SourceItemRecord):
        return item.private_answer.model_dump(mode="json")
    try:
        answer = answer_by_id[item.item_id]
    except KeyError as exc:
        raise ValueError(f"Reverse-pair item {item.item_id} is missing its private answer") from exc
    return answer.model_dump(
        mode="json",
        exclude={"item_id", "item_revision", "purpose", "private_answer_record_sha256"},
    )


def _reverse_pair_common_payload(
    item: SourceItemRecord | BuiltBenchmarkItem,
    answer_by_id: Mapping[str, PrivateAnswerRecord],
) -> dict[str, Any]:
    item_payload = item.model_dump(
        mode="json",
        exclude={
            "item_id",
            "model_visible",
            "provenance",
            "private_answer",
            "model_visible_sha256",
            "exact_displayed_input_fingerprint_sha256",
            "order_neutral_item_content_fingerprint_sha256",
            "annotation_metadata_sha256",
            "complete_private_item_record_sha256",
        },
    )
    provenance = item.provenance.model_dump(
        mode="json",
        exclude={"created_from_source_record", "transformation_history"},
    )
    option_mapping = sorted(
        (
            option.option_id,
            normalise_equivalent_text(option.text),
        )
        for option in item.model_visible.ordered_options
    )
    return {
        "benchmark_classification": item_payload,
        "prompt": _pair_text(item.model_visible.prompt),
        "instructions": _pair_text(item.model_visible.instructions),
        "reverse_pair_id": item.model_visible.reverse_pair_id,
        "stable_option_id_to_normalised_text": option_mapping,
        "closed_book_eligible": item.model_visible.closed_book_eligible,
        "open_book_eligible": item.model_visible.open_book_eligible,
        "provenance_except_source_record_and_reversal_history": provenance,
        "private_answer_evidence": _pair_answer_payload(item, answer_by_id),
    }


def reverse_pair_identity_hash(
    members: Sequence[SourceItemRecord | BuiltBenchmarkItem],
    *,
    answers: Sequence[PrivateAnswerRecord] = (),
) -> str:
    """Validate and hash the exact reverse-pair equivalence contract."""

    if len(members) != 2:
        raise ValueError("A canonical reverse pair must contain exactly two variants")
    left, right = sorted(members, key=lambda item: item.item_id)
    pair_id = left.model_visible.reverse_pair_id
    if pair_id is None or right.model_visible.reverse_pair_id != pair_id:
        raise ValueError("Canonical reverse-pair members must share one pair identity")
    if left.item_id == right.item_id:
        raise ValueError(f"Reverse pair {pair_id!r} requires distinct item IDs")
    if left.provenance.created_from_source_record == right.provenance.created_from_source_record:
        raise ValueError(f"Reverse pair {pair_id!r} requires distinct source-record IDs")
    if left.model_visible.variant_id == right.model_visible.variant_id:
        raise ValueError(f"Reverse pair {pair_id!r} requires distinct variant IDs")
    left_ids = left.model_visible.option_permutation
    right_ids = right.model_visible.option_permutation
    if set(left_ids) != set(right_ids) or right_ids != tuple(reversed(left_ids)):
        raise ValueError(f"Reverse pair {pair_id!r} has an invalid option permutation")
    answer_by_id = {answer.item_id: answer for answer in answers}
    left_common = _reverse_pair_common_payload(left, answer_by_id)
    right_common = _reverse_pair_common_payload(right, answer_by_id)
    if canonical_logical_bytes(left_common) != canonical_logical_bytes(right_common):
        raise ValueError(
            f"Reverse pair {pair_id!r} differs outside the declared variant-specific fields"
        )
    histories = (
        left.provenance.transformation_history,
        right.provenance.transformation_history,
    )
    stripped_histories: list[tuple[str, ...]] = []
    reversal_counts: list[int] = []
    for history in histories:
        reversal_count = history.count(_REVERSE_TRANSFORMATION_RECORD)
        if reversal_count > 1:
            raise ValueError(f"Reverse pair {pair_id!r} repeats its reversal transformation")
        reversal_counts.append(reversal_count)
        stripped_histories.append(
            tuple(value for value in history if value != _REVERSE_TRANSFORMATION_RECORD)
        )
    if sorted(reversal_counts) != [0, 1] or stripped_histories[0] != stripped_histories[1]:
        raise ValueError(
            f"Reverse pair {pair_id!r} must differ only by the declared reversal transformation"
        )
    return hash_domain(
        "unfrozen-schemas/benchmark/reverse-pair-identity/v1",
        {"pair_id": pair_id, "common": left_common},
    )


def validate_reverse_pairs(
    items: Sequence[SourceItemRecord | BuiltBenchmarkItem],
    *,
    answers: Sequence[PrivateAnswerRecord] = (),
) -> None:
    groups: dict[str, list[SourceItemRecord | BuiltBenchmarkItem]] = defaultdict(list)
    for item in items:
        pair_id = item.model_visible.reverse_pair_id
        if pair_id is not None:
            groups[pair_id].append(item)
    for pair_id, members in groups.items():
        if len(members) != 2:
            raise ValueError(f"Reverse pair {pair_id!r} must contain exactly two variants")
        reverse_pair_identity_hash(members, answers=answers)


def _validate_common_items(
    items: Sequence[SourceItemRecord | BuiltBenchmarkItem],
    *,
    purpose: BenchmarkPurpose,
    engineering_only: bool,
    scientific_eligible: bool,
    promotable: bool,
    answers: Sequence[PrivateAnswerRecord] = (),
) -> None:
    item_ids = [item.item_id for item in items]
    if len(item_ids) != len(set(item_ids)):
        raise ValueError("Duplicate stable item IDs are prohibited within one benchmark version")
    if any(item.purpose is not purpose or item.identity_purpose is not purpose for item in items):
        raise ValueError("Every item purpose and identity purpose must match its bundle")
    answer_by_id = {answer.item_id: answer for answer in answers}
    for item in items:
        if (
            item.engineering_only != engineering_only
            or item.scientific_eligible != scientific_eligible
            or item.promotable != promotable
        ):
            raise ValueError("Every candidate-level classification flag must match every item")
        if engineering_only:
            if (
                item.provenance.origin_classification
                is not OriginClassification.ENGINEERING_FIXTURE
                or item.provenance.rights_status is not RightsStatus.NOT_APPLICABLE_ENGINEERING
                or item.provenance.ethics_status is not GovernanceStatus.NOT_APPLICABLE_ENGINEERING
                or item.human_validation.validation_status
                is not HumanValidationStatus.NOT_APPLICABLE_ENGINEERING
                or item.human_validation.adjudication_status
                is not AdjudicationStatus.NOT_APPLICABLE_ENGINEERING
            ):
                raise ValueError(
                    "Engineering items require exact engineering origin and governance classes"
                )
            if (
                item.item_id in answer_by_id
                and answer_by_id[item.item_id].answer_provenance
                is not AnswerProvenance.ENGINEERING_FIXTURE
            ):
                raise ValueError("Engineering private answers require engineering provenance")
            visible_text = canonical_logical_bytes(item.model_visible).decode("utf-8")
            if _ENGINEERING_PROHIBITED_WORDS.search(visible_text):
                raise ValueError(
                    f"Engineering fixture item {item.item_id} uses prohibited scientific vocabulary"
                )
        else:
            answer_provenance = (
                item.private_answer.answer_provenance
                if isinstance(item, SourceItemRecord)
                else answer_by_id[item.item_id].answer_provenance
            )
            if (
                item.provenance.origin_classification is OriginClassification.ENGINEERING_FIXTURE
                or answer_provenance is AnswerProvenance.ENGINEERING_FIXTURE
            ):
                raise ValueError(
                    "Non-engineering items cannot use engineering-fixture classification"
                )
    validate_reverse_pairs(items, answers=answers)


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
        items,
        purpose=source_manifest.purpose,
        engineering_only=source_manifest.engineering_only,
        scientific_eligible=source_manifest.scientific_eligible,
        promotable=source_manifest.promotable,
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
        quarantine_scope=source_manifest.quarantine_scope,
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
    quarantine_scope_sha256: str,
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
        quarantine_scope_sha256=quarantine_scope_sha256,
        **dict(hashes),
    )


def _quarantine_manifest_identity(
    manifest_path: Path,
    repository_root: Path,
) -> tuple[
    CandidateManifest | FrozenManifest,
    tuple[BuiltBenchmarkItem, ...],
]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    kind = payload.get("manifest_kind")
    if kind == "benchmark_private_candidate":
        allow_frozen_copy = (manifest_path.parent / FROZEN_MANIFEST_FILENAME).is_file()
        candidate_manifest, items, _ = _load_candidate_payload(
            manifest_path,
            repository_root=repository_root,
            revalidate_quarantine=False,
            allow_canonical_frozen_copy=allow_frozen_copy,
        )
        return candidate_manifest, items
    if kind == "benchmark_frozen":
        frozen_manifest = _load_frozen_payload(
            manifest_path,
            repository_root=repository_root,
            revalidate_quarantine=False,
        )
        _, items, _ = _load_candidate_payload(
            manifest_path.parent / frozen_manifest.candidate_manifest_path,
            repository_root=repository_root,
            revalidate_quarantine=False,
            allow_canonical_frozen_copy=True,
        )
        return frozen_manifest, items
    raise ValueError(f"Unsupported manifest in mandatory quarantine scope: {manifest_path}")


def _is_current_candidate_lineage(
    manifest_path: Path,
    *,
    repository_root: Path,
    candidate_bundle_root_sha256: str | None,
    benchmark_version: str | None,
    purpose: BenchmarkPurpose | None,
) -> bool:
    if (
        candidate_bundle_root_sha256 is None
        or benchmark_version is None
        or purpose is None
        or purpose is BenchmarkPurpose.ENGINEERING
    ):
        return False
    canonical_paths = {
        (
            resolve_candidate_version_path(repository_root, benchmark_version, purpose)
            / CANDIDATE_MANIFEST_FILENAME
        ).resolve()
    }
    if purpose in {BenchmarkPurpose.OUTCOME, BenchmarkPurpose.RETENTION}:
        frozen_root = resolve_frozen_version_path(repository_root, benchmark_version, purpose)
        canonical_paths.update(
            {
                (frozen_root / CANDIDATE_MANIFEST_FILENAME).resolve(),
                (frozen_root / FROZEN_MANIFEST_FILENAME).resolve(),
            }
        )
    if manifest_path.resolve(strict=True) not in canonical_paths:
        return False
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return bool(
        payload.get("candidate_bundle_root_sha256") == candidate_bundle_root_sha256
        and payload.get("benchmark_version") == benchmark_version
        and payload.get("purpose") == (purpose.value if purpose is not None else None)
    )


def create_quarantine_scope(
    declaration: QuarantineScopeDeclaration,
    repository_root: Path,
    *,
    current_candidate_bundle_root_sha256: str | None = None,
    current_benchmark_version: str | None = None,
    current_purpose: BenchmarkPurpose | None = None,
    transient_staging_roots: Sequence[Path] = (),
) -> QuarantineScope:
    """Scan every mandatory canonical root and bind all external manifest identities."""

    repository = repository_root.resolve()
    if declaration.mode is QuarantineScopeMode.ENGINEERING_EMPTY:
        provisional = QuarantineScope(
            mode=declaration.mode,
            canonical_roots=declaration.canonical_roots,
            manifests=(),
            quarantine_scope_sha256="0" * 64,
        )
        return provisional.model_copy(
            update={"quarantine_scope_sha256": quarantine_scope_hash(provisional)}
        )
    if declaration.canonical_roots != CANONICAL_QUARANTINE_ROOTS:
        raise ValueError("Mandatory quarantine scope omits one or more canonical roots")
    resolved_transient_roots: tuple[Path, ...] = tuple(
        staging.resolve(strict=True) for staging in transient_staging_roots
    )
    canonical_root_paths = tuple(
        (repository / declared_root).resolve() for declared_root in declaration.canonical_roots
    )
    for staging in resolved_transient_roots:
        if (
            not staging.is_dir()
            or ".staging-" not in staging.name
            or staging.parent not in canonical_root_paths
        ):
            raise ValueError(f"Invalid transient quarantine-scan staging root: {staging}")
    manifest_paths: set[Path] = set()
    for declared_root in declaration.canonical_roots:
        try:
            root = resolve_safe_relative_path(repository, declared_root)
        except (FileNotFoundError, OSError, ValueError) as exc:
            raise ValueError(
                f"Quarantine root is missing, unreadable, or non-canonical: {declared_root}"
            ) from exc
        if not root.is_dir() or root.is_symlink():
            raise ValueError(
                f"Quarantine root is missing, unreadable, or non-canonical: {declared_root}"
            )
        for filename in (CANDIDATE_MANIFEST_FILENAME, FROZEN_MANIFEST_FILENAME):
            for manifest_path in root.rglob(filename):
                resolved = manifest_path.resolve(strict=True)
                if not resolved.is_relative_to(root):
                    raise ValueError(f"Quarantine manifest escapes its root: {manifest_path}")
                if any(resolved.is_relative_to(staging) for staging in resolved_transient_roots):
                    continue
                manifest_paths.add(resolved)
    references: list[QuarantineManifestReference] = []
    for manifest_path in sorted(manifest_paths, key=lambda path: path.as_posix()):
        if _is_current_candidate_lineage(
            manifest_path,
            repository_root=repository,
            candidate_bundle_root_sha256=current_candidate_bundle_root_sha256,
            benchmark_version=current_benchmark_version,
            purpose=current_purpose,
        ):
            continue
        manifest, items = _quarantine_manifest_identity(manifest_path, repository)
        relative = manifest_path.relative_to(repository).as_posix()
        references.append(
            QuarantineManifestReference(
                path=relative,
                file_sha256=sha256_file(manifest_path),
                manifest_kind=manifest.manifest_kind,
                lifecycle_state=manifest.lifecycle_state,
                benchmark_version=manifest.benchmark_version,
                purpose=manifest.purpose,
                candidate_bundle_root_sha256=manifest.candidate_bundle_root_sha256,
                item_ids=tuple(sorted(item.item_id for item in items)),
                exact_displayed_input_fingerprints=tuple(
                    sorted({item.exact_displayed_input_fingerprint_sha256 for item in items})
                ),
                order_neutral_item_content_fingerprints=tuple(
                    sorted({item.order_neutral_item_content_fingerprint_sha256 for item in items})
                ),
            )
        )
    provisional = QuarantineScope(
        mode=declaration.mode,
        canonical_roots=declaration.canonical_roots,
        manifests=tuple(sorted(references, key=lambda reference: reference.path)),
        quarantine_scope_sha256="0" * 64,
    )
    return provisional.model_copy(
        update={"quarantine_scope_sha256": quarantine_scope_hash(provisional)}
    )


def validate_quarantine_scope_content(
    purpose: BenchmarkPurpose,
    items: Sequence[BuiltBenchmarkItem],
    scope: QuarantineScope,
) -> None:
    seen_ids: dict[str, BenchmarkPurpose] = {item.item_id: purpose for item in items}
    seen_exact: dict[str, BenchmarkPurpose] = {
        item.exact_displayed_input_fingerprint_sha256: purpose for item in items
    }
    seen_order_neutral: dict[str, BenchmarkPurpose] = {
        item.order_neutral_item_content_fingerprint_sha256: purpose for item in items
    }
    for reference in scope.manifests:
        for item_id in reference.item_ids:
            previous = seen_ids.get(item_id)
            if previous is not None and previous is not reference.purpose:
                raise ValueError(
                    f"Item ID {item_id!r} appears across prohibited purposes: "
                    f"{previous.value}, {reference.purpose.value}"
                )
            seen_ids[item_id] = reference.purpose
        for fingerprint in reference.exact_displayed_input_fingerprints:
            previous = seen_exact.get(fingerprint)
            if previous is not None and previous is not reference.purpose:
                raise ValueError(
                    "Exact displayed model input appears across prohibited benchmark purposes: "
                    f"{previous.value}, {reference.purpose.value}"
                )
            seen_exact[fingerprint] = reference.purpose
        for fingerprint in reference.order_neutral_item_content_fingerprints:
            previous = seen_order_neutral.get(fingerprint)
            if previous is not None and previous is not reference.purpose:
                raise ValueError(
                    "Order-neutral item content appears across prohibited benchmark purposes: "
                    f"{previous.value}, {reference.purpose.value}"
                )
            seen_order_neutral[fingerprint] = reference.purpose


def verify_quarantine_scope(
    *,
    scope: QuarantineScope,
    declaration: QuarantineScopeDeclaration,
    repository_root: Path | None,
    candidate: CandidateManifest,
    items: Sequence[BuiltBenchmarkItem],
    transient_staging_roots: Sequence[Path] = (),
) -> None:
    if quarantine_scope_hash(scope) != scope.quarantine_scope_sha256:
        raise ValueError("Quarantine scope logical hash mismatch")
    if scope.quarantine_scope_sha256 != candidate.quarantine_scope_sha256:
        raise ValueError("Candidate quarantine-scope identity mismatch")
    if scope.mode is not declaration.mode or scope.canonical_roots != declaration.canonical_roots:
        raise ValueError("Source declaration and candidate quarantine scope disagree")
    if scope.mode is QuarantineScopeMode.ENGINEERING_EMPTY:
        if not candidate.engineering_only or scope.manifests:
            raise ValueError("Only engineering candidates may use an explicitly empty scope")
    else:
        if repository_root is None:
            raise ValueError("Non-engineering quarantine validation requires the repository root")
        observed = create_quarantine_scope(
            declaration,
            repository_root,
            current_candidate_bundle_root_sha256=candidate.candidate_bundle_root_sha256,
            current_benchmark_version=candidate.benchmark_version,
            current_purpose=candidate.purpose,
            transient_staging_roots=transient_staging_roots,
        )
        if observed != scope:
            raise ValueError(
                "Mandatory quarantine scope is stale, incomplete, unreadable, or hash-mismatched"
            )
    validate_quarantine_scope_content(candidate.purpose, items, scope)


def validate_cross_purpose_records(
    groups: Mapping[BenchmarkPurpose, Sequence[BuiltBenchmarkItem]],
) -> None:
    seen_ids: dict[str, BenchmarkPurpose] = {}
    seen_exact_displayed: dict[str, BenchmarkPurpose] = {}
    seen_order_neutral: dict[str, BenchmarkPurpose] = {}
    for purpose, items in groups.items():
        for item in items:
            previous = seen_ids.get(item.item_id)
            if previous is not None and previous is not purpose:
                raise ValueError(
                    f"Item ID {item.item_id!r} appears across prohibited purposes: "
                    f"{previous.value}, {purpose.value}"
                )
            seen_ids[item.item_id] = purpose
            exact_fingerprint = exact_displayed_input_fingerprint(item.model_visible)
            if exact_fingerprint != item.exact_displayed_input_fingerprint_sha256:
                raise ValueError("Stored exact displayed-input fingerprint is inconsistent")
            previous_exact = seen_exact_displayed.get(exact_fingerprint)
            if previous_exact is not None and previous_exact is not purpose:
                raise ValueError(
                    "Exact displayed model input appears across prohibited benchmark purposes: "
                    f"{previous_exact.value}, {purpose.value}"
                )
            seen_exact_displayed[exact_fingerprint] = purpose
            order_neutral = order_neutral_item_content_fingerprint(item.model_visible)
            if order_neutral != item.order_neutral_item_content_fingerprint_sha256:
                raise ValueError("Stored order-neutral item-content fingerprint is inconsistent")
            previous_content = seen_order_neutral.get(order_neutral)
            if previous_content is not None and previous_content is not purpose:
                raise ValueError(
                    "Order-neutral item content appears across prohibited benchmark purposes: "
                    f"{previous_content.value}, {purpose.value}"
                )
            seen_order_neutral[order_neutral] = purpose


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
    *,
    repository_root: Path | None = None,
    revalidate_quarantine: bool = True,
    enforce_storage_location: bool = True,
    allow_canonical_frozen_copy: bool = False,
    transient_staging_roots: Sequence[Path] = (),
) -> tuple[CandidateManifest, tuple[BuiltBenchmarkItem, ...], tuple[PrivateAnswerRecord, ...]]:
    manifest = read_canonical_model(manifest_path, CandidateManifest)
    if enforce_storage_location:
        _require_canonical_candidate_location(
            manifest_path,
            manifest,
            repository_root,
            allow_canonical_frozen_copy=allow_canonical_frozen_copy,
        )
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
    expected_header: dict[str, object] = {
        "benchmark_version": manifest.benchmark_version,
        "purpose": manifest.purpose,
        "engineering_only": manifest.engineering_only,
        "scientific_eligible": manifest.scientific_eligible,
        "promotable": manifest.promotable,
        "item_count": manifest.item_count,
        "rights_determination_reference": manifest.rights_determination_reference,
        "human_validation_reference": manifest.human_validation_reference,
        "ethics_determination_reference": manifest.ethics_determination_reference,
        "production_prerequisites": manifest.production_prerequisites,
    }
    for field, expected_value in expected_header.items():
        if getattr(snapshot.header, field) != expected_value:
            raise ValueError(f"Source snapshot header and candidate manifest mismatch: {field}")
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
        items,
        purpose=manifest.purpose,
        engineering_only=manifest.engineering_only,
        scientific_eligible=manifest.scientific_eligible,
        promotable=manifest.promotable,
        answers=answers,
    )
    for item, answer in zip(items, answers, strict=True):
        option_ids = {option.option_id for option in item.model_visible.ordered_options}
        if answer.correct_option_id not in option_ids:
            raise ValueError(f"Private answer for {item.item_id} references an invalid option")
    observed_bundles = bundle_hashes(
        benchmark_version=manifest.benchmark_version,
        purpose=manifest.purpose.value,
        source_snapshot_sha256=manifest.source_snapshot_sha256,
        quarantine_scope_sha256=manifest.quarantine_scope_sha256,
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
        or config.quarantine_scope_sha256 != manifest.quarantine_scope_sha256
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
        quarantine_scope_sha256=manifest.quarantine_scope_sha256,
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
    scope = read_canonical_model(root / manifest.quarantine_scope_path, QuarantineScope)
    if revalidate_quarantine:
        verify_quarantine_scope(
            scope=scope,
            declaration=snapshot.header.quarantine_scope,
            repository_root=repository_root,
            candidate=manifest,
            items=items,
            transient_staging_roots=transient_staging_roots,
        )
    else:
        if quarantine_scope_hash(scope) != scope.quarantine_scope_sha256:
            raise ValueError("Quarantine scope logical hash mismatch")
        if scope.quarantine_scope_sha256 != manifest.quarantine_scope_sha256:
            raise ValueError("Candidate quarantine-scope identity mismatch")
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
    expected_build_input_hashes = {
        "quarantine_scope_sha256": manifest.quarantine_scope_sha256,
        "source_snapshot_sha256": manifest.source_snapshot_sha256,
    }
    if (
        operation.operation_kind != "build_benchmark"
        or operation.status != "COMPLETED"
        or operation.engineering_only != manifest.engineering_only
        or operation.scientific_result is not False
        or operation.lifecycle_state_before is not LifecycleState.SOURCE
        or operation.lifecycle_state_after is not LifecycleState.PRIVATE
        or operation.benchmark_version != manifest.benchmark_version
        or operation.purpose is not manifest.purpose
        or operation.item_count != manifest.item_count
        or operation.git != manifest.git
        or operation.codex_spec_sha256 != manifest.codex_spec_sha256
        or operation.quarantine_scope_sha256 != manifest.quarantine_scope_sha256
        or operation.resolved_configuration != config
        or operation.input_hashes != expected_build_input_hashes
    ):
        raise ValueError("Build operation provenance does not match candidate manifest")
    persisted_budget = read_canonical_model(root / manifest.resource_budget_path, ResourceBudget)
    if persisted_budget != operation.resource_budget:
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
    if candidate.purpose is BenchmarkPurpose.SELECTION:
        raise ValueError("SELECTION-purpose freezing is refused throughout M2.1")
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
        "quarantine_scope_sha256": candidate.quarantine_scope_sha256,
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


def _load_frozen_payload(
    manifest_path: Path,
    *,
    repository_root: Path | None = None,
    revalidate_quarantine: bool = True,
    enforce_storage_location: bool = True,
) -> FrozenManifest:
    manifest = read_canonical_model(manifest_path, FrozenManifest)
    if enforce_storage_location:
        _require_canonical_frozen_location(manifest_path, manifest, repository_root)
    root = manifest_path.parent.resolve()
    verify_artifact_records(
        root,
        manifest.artifacts,
        expected_paths=CANDIDATE_ARTIFACT_PATHS | FROZEN_EXTRA_ARTIFACT_PATHS,
    )
    if frozen_manifest_hash(manifest) != manifest.frozen_manifest_sha256:
        raise ValueError("Frozen manifest logical hash mismatch")
    candidate_path = root / manifest.candidate_manifest_path
    candidate, items, _ = _load_candidate_payload(
        candidate_path,
        repository_root=repository_root,
        revalidate_quarantine=revalidate_quarantine,
        enforce_storage_location=enforce_storage_location,
        allow_canonical_frozen_copy=True,
    )
    approval = read_canonical_model(root / manifest.freeze_approval_path, FreezeApproval)
    verify_freeze_approval(candidate_path, candidate, items, approval)
    receipt = read_canonical_model(root / manifest.immutable_receipt_path, ImmutableReceipt)
    expected_receipt = ImmutableReceipt(
        benchmark_version=candidate.benchmark_version,
        purpose=candidate.purpose,
        candidate_manifest_sha256=sha256_file(candidate_path),
        candidate_bundle_root_sha256=candidate.candidate_bundle_root_sha256,
        freeze_approval_sha256=approval.approval_sha256,
        quarantine_scope_sha256=candidate.quarantine_scope_sha256,
    )
    if receipt != expected_receipt:
        raise ValueError("Immutable receipt does not match candidate and approval")
    operation = read_canonical_model(
        root / manifest.operation_record_path, BenchmarkOperationRecord
    )
    expected_freeze_input_hashes = {
        "candidate_bundle_root_sha256": candidate.candidate_bundle_root_sha256,
        "candidate_manifest_sha256": sha256_file(candidate_path),
        "freeze_approval_sha256": approval.approval_sha256,
        "quarantine_scope_sha256": candidate.quarantine_scope_sha256,
    }
    expected_freeze_config = ResolvedBenchmarkConfig(
        benchmark_version=candidate.benchmark_version,
        purpose=candidate.purpose,
        quarantine_scope_sha256=candidate.quarantine_scope_sha256,
    )
    if (
        operation.operation_kind != "freeze_benchmark"
        or operation.status != "COMPLETED"
        or operation.engineering_only != candidate.engineering_only
        or operation.scientific_result is not False
        or operation.lifecycle_state_before is not LifecycleState.PRIVATE
        or operation.lifecycle_state_after is not LifecycleState.FROZEN
        or operation.benchmark_version != candidate.benchmark_version
        or operation.purpose is not candidate.purpose
        or operation.item_count != candidate.item_count
        or operation.git != candidate.git
        or operation.codex_spec_sha256 != candidate.codex_spec_sha256
        or operation.quarantine_scope_sha256 != candidate.quarantine_scope_sha256
        or operation.resolved_configuration != expected_freeze_config
        or operation.input_hashes != expected_freeze_input_hashes
    ):
        raise ValueError("Freeze operation provenance does not match frozen manifest")
    persisted_budget = read_canonical_model(root / manifest.resource_budget_path, ResourceBudget)
    if persisted_budget != operation.resource_budget:
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
        "quarantine_scope_sha256": candidate.quarantine_scope_sha256,
        "freeze_approval_sha256": approval.approval_sha256,
        "codex_spec_sha256": candidate.codex_spec_sha256,
        "git_commit": candidate.git.commit,
    }
    for field, value in expected_manifest_fields.items():
        if getattr(manifest, field) != value:
            raise ValueError(f"Frozen manifest mismatch: {field}")
    return manifest


def validate_benchmark_manifest(
    manifest_path: Path,
    *,
    against_manifests: Sequence[Path] = (),
    repository_root: Path | None = None,
) -> CandidateManifest | FrozenManifest:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    kind = payload.get("manifest_kind")
    current_items: tuple[BuiltBenchmarkItem, ...]
    result: CandidateManifest | FrozenManifest
    if kind == "benchmark_private_candidate":
        candidate_result, current_items, _ = _load_candidate_payload(
            manifest_path, repository_root=repository_root
        )
        result = candidate_result
    elif kind == "benchmark_frozen":
        frozen_result = _load_frozen_payload(manifest_path, repository_root=repository_root)
        result = frozen_result
        _, current_items, _ = _load_candidate_payload(
            manifest_path.parent / frozen_result.candidate_manifest_path,
            repository_root=repository_root,
            allow_canonical_frozen_copy=True,
        )
    else:
        raise ValueError(f"Unsupported benchmark manifest kind: {kind!r}")
    groups: dict[BenchmarkPurpose, list[BuiltBenchmarkItem]] = defaultdict(list)
    groups[result.purpose].extend(current_items)
    for other_path in against_manifests:
        other_payload = json.loads(other_path.read_text(encoding="utf-8"))
        if other_payload.get("manifest_kind") == "benchmark_private_candidate":
            other_candidate, other_items, _ = _load_candidate_payload(
                other_path, repository_root=repository_root
            )
            other_purpose = other_candidate.purpose
        elif other_payload.get("manifest_kind") == "benchmark_frozen":
            other_frozen = _load_frozen_payload(other_path, repository_root=repository_root)
            other_purpose = other_frozen.purpose
            _, other_items, _ = _load_candidate_payload(
                other_path.parent / other_frozen.candidate_manifest_path,
                repository_root=repository_root,
                allow_canonical_frozen_copy=True,
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
    unexpected = sorted(set(tracked) - _SAFE_TRACKED_BENCHMARK_PATHS)
    missing = sorted(_SAFE_TRACKED_BENCHMARK_PATHS - set(tracked))
    if unexpected or missing:
        raise ValueError(
            "Tracked benchmark paths must equal the reviewed M2.1 README allowlist; "
            f"missing={missing}, unexpected={unexpected}"
        )
    return tracked
