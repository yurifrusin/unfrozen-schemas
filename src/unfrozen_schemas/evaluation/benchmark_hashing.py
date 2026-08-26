"""Canonical, purpose-bound SHA-256 domains for benchmark records."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from collections.abc import Mapping, Sequence
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel

from unfrozen_schemas.evaluation.benchmark_models import (
    BuiltBenchmarkItem,
    CoverageSummary,
    FreezeApproval,
    FrozenManifest,
    ModelVisibleContent,
    PrivateAnswerRecord,
    PublicManifest,
    QuarantineScope,
    SourceItemRecord,
    SourceSnapshot,
    SourceSnapshotHeader,
)

HASH_DOMAINS: tuple[str, ...] = (
    "unfrozen-schemas/benchmark/source-snapshot/v1",
    "unfrozen-schemas/benchmark/model-visible-item/v1",
    "unfrozen-schemas/benchmark/private-answer-record/v1",
    "unfrozen-schemas/benchmark/complete-private-item/v1",
    "unfrozen-schemas/benchmark/annotation-metadata/v1",
    "unfrozen-schemas/benchmark/model-visible-bundle/v1",
    "unfrozen-schemas/benchmark/private-answer-bundle/v1",
    "unfrozen-schemas/benchmark/annotation-metadata-bundle/v1",
    "unfrozen-schemas/benchmark/candidate-bundle-root/v1",
    "unfrozen-schemas/benchmark/public-metadata-bundle/v1",
    "unfrozen-schemas/benchmark/freeze-approval/v1",
    "unfrozen-schemas/benchmark/frozen-manifest/v1",
    "unfrozen-schemas/benchmark/exact-displayed-input-fingerprint/v1",
    "unfrozen-schemas/benchmark/order-neutral-item-content-fingerprint/v1",
    "unfrozen-schemas/benchmark/reverse-pair-identity/v1",
    "unfrozen-schemas/benchmark/quarantine-scope/v1",
)


def _normalise_logical(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _normalise_logical(value.model_dump(mode="json"))
    if isinstance(value, Mapping):
        return {str(key): _normalise_logical(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_normalise_logical(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        line_normalised = value.replace("\r\n", "\n").replace("\r", "\n")
        return unicodedata.normalize("NFC", line_normalised)
    return value


def canonical_logical_bytes(value: Any) -> bytes:
    """Canonical JSON bytes for scientific identity, independent of container metadata."""

    return (
        json.dumps(
            _normalise_logical(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def normalise_equivalent_text(value: str | None) -> str:
    """Normalise text for declared cross-purpose equivalence comparisons."""

    if value is None:
        return ""
    line_normalised = value.replace("\r\n", "\n").replace("\r", "\n")
    unicode_normalised = unicodedata.normalize("NFC", line_normalised)
    return " ".join(unicode_normalised.split()).casefold()


def hash_domain(domain: str, payload: Any) -> str:
    if domain not in HASH_DOMAINS:
        raise ValueError(f"Unknown benchmark hash domain: {domain}")
    framed = {"domain": domain, "payload": _normalise_logical(payload)}
    return hashlib.sha256(canonical_logical_bytes(framed)).hexdigest()


def normalise_source_item(item: SourceItemRecord) -> SourceItemRecord:
    """Normalise logical strings and canonically ordered set-like annotations."""

    data = _normalise_logical(item.model_dump(mode="json"))
    annotations = data["scientific_annotations"]
    for name in (
        "required_causal_factors",
        "lexical_cue_annotations",
        "external_language_overlap_flags",
    ):
        annotations[name] = sorted(annotations[name])
    data["provenance"]["reviewer_references"] = sorted(data["provenance"]["reviewer_references"])
    data["human_validation"]["ambiguity_findings"] = sorted(
        data["human_validation"]["ambiguity_findings"]
    )
    return SourceItemRecord.model_validate(data)


def source_snapshot_hash(header: SourceSnapshotHeader, items: Sequence[SourceItemRecord]) -> str:
    payload = {
        "header": header,
        "items": [item for item in sorted(items, key=lambda value: value.item_id)],
    }
    return hash_domain("unfrozen-schemas/benchmark/source-snapshot/v1", payload)


def make_source_snapshot(
    header: SourceSnapshotHeader, items: Sequence[SourceItemRecord]
) -> SourceSnapshot:
    normalised = tuple(
        sorted((normalise_source_item(item) for item in items), key=lambda x: x.item_id)
    )
    return SourceSnapshot(
        header=header,
        items=normalised,
        source_snapshot_sha256=source_snapshot_hash(header, normalised),
    )


def model_visible_item_hash(item: SourceItemRecord) -> str:
    payload = {
        "item_id": item.item_id,
        "item_revision": item.item_revision,
        "purpose": item.purpose,
        "model_visible": item.model_visible,
    }
    return hash_domain("unfrozen-schemas/benchmark/model-visible-item/v1", payload)


def exact_displayed_input_fingerprint(content: ModelVisibleContent) -> str:
    """Purpose-neutral identity of the exact displayed model input."""

    payload = {
        "prompt": normalise_equivalent_text(content.prompt),
        "instructions": normalise_equivalent_text(content.instructions),
        "displayed_option_texts": [
            normalise_equivalent_text(option.text) for option in content.ordered_options
        ],
        "closed_book_eligible": content.closed_book_eligible,
        "open_book_eligible": content.open_book_eligible,
    }
    return hash_domain("unfrozen-schemas/benchmark/exact-displayed-input-fingerprint/v1", payload)


def order_neutral_item_content_fingerprint(content: ModelVisibleContent) -> str:
    """Purpose-neutral item content identity independent of IDs and option order."""

    payload = {
        "prompt": normalise_equivalent_text(content.prompt),
        "instructions": normalise_equivalent_text(content.instructions),
        "option_text_multiset": sorted(
            normalise_equivalent_text(option.text) for option in content.ordered_options
        ),
    }
    return hash_domain(
        "unfrozen-schemas/benchmark/order-neutral-item-content-fingerprint/v1", payload
    )


def private_answer_record_hash(item: SourceItemRecord) -> str:
    payload = {
        "item_id": item.item_id,
        "item_revision": item.item_revision,
        "purpose": item.purpose,
        "private_answer": item.private_answer,
    }
    return hash_domain("unfrozen-schemas/benchmark/private-answer-record/v1", payload)


def annotation_metadata_hash(item: SourceItemRecord) -> str:
    data = item.model_dump(mode="json", exclude={"model_visible", "private_answer"})
    return hash_domain("unfrozen-schemas/benchmark/annotation-metadata/v1", data)


def derive_built_records(item: SourceItemRecord) -> tuple[BuiltBenchmarkItem, PrivateAnswerRecord]:
    item = normalise_source_item(item)
    answer = PrivateAnswerRecord(
        item_id=item.item_id,
        item_revision=item.item_revision,
        purpose=item.purpose,
        correct_option_id=item.private_answer.correct_option_id,
        answer_rationale=item.private_answer.answer_rationale,
        simulator_verification_reference=item.private_answer.simulator_verification_reference,
        answer_provenance=item.private_answer.answer_provenance,
        adjudication_reference=item.private_answer.adjudication_reference,
        private_answer_record_sha256=private_answer_record_hash(item),
    )
    provisional = BuiltBenchmarkItem(
        item_id=item.item_id,
        item_revision=item.item_revision,
        purpose=item.purpose,
        identity_purpose=item.identity_purpose,
        task_family_slug=item.task_family_slug,
        transfer_level=item.transfer_level,
        schema_designation=item.schema_designation,
        target_domain_family=item.target_domain_family,
        source_mechanism_family=item.source_mechanism_family,
        prompt_template_id=item.prompt_template_id,
        partition_id=item.partition_id,
        engineering_only=item.engineering_only,
        scientific_eligible=item.scientific_eligible,
        promotable=item.promotable,
        model_visible=item.model_visible,
        scientific_annotations=item.scientific_annotations,
        provenance=item.provenance,
        human_validation=item.human_validation,
        model_visible_sha256=model_visible_item_hash(item),
        exact_displayed_input_fingerprint_sha256=exact_displayed_input_fingerprint(
            item.model_visible
        ),
        order_neutral_item_content_fingerprint_sha256=(
            order_neutral_item_content_fingerprint(item.model_visible)
        ),
        annotation_metadata_sha256=annotation_metadata_hash(item),
        complete_private_item_record_sha256="0" * 64,
    )
    complete_payload = {
        "built_item": provisional.model_dump(
            mode="json", exclude={"complete_private_item_record_sha256"}
        ),
        "private_answer": answer.model_dump(mode="json", exclude={"private_answer_record_sha256"}),
    }
    complete_hash = hash_domain(
        "unfrozen-schemas/benchmark/complete-private-item/v1", complete_payload
    )
    return provisional.model_copy(
        update={"complete_private_item_record_sha256": complete_hash}
    ), answer


def bundle_hashes(
    *,
    benchmark_version: str,
    purpose: str,
    source_snapshot_sha256: str,
    quarantine_scope_sha256: str,
    items: Sequence[BuiltBenchmarkItem],
    answers: Sequence[PrivateAnswerRecord],
) -> dict[str, str]:
    sorted_items = sorted(items, key=lambda item: item.item_id)
    sorted_answers = sorted(answers, key=lambda item: item.item_id)
    model_visible = hash_domain(
        "unfrozen-schemas/benchmark/model-visible-bundle/v1",
        {
            "benchmark_version": benchmark_version,
            "purpose": purpose,
            "records": [
                {"item_id": item.item_id, "sha256": item.model_visible_sha256}
                for item in sorted_items
            ],
        },
    )
    annotations = hash_domain(
        "unfrozen-schemas/benchmark/annotation-metadata-bundle/v1",
        {
            "benchmark_version": benchmark_version,
            "purpose": purpose,
            "records": [
                {"item_id": item.item_id, "sha256": item.annotation_metadata_sha256}
                for item in sorted_items
            ],
        },
    )
    private_answers = hash_domain(
        "unfrozen-schemas/benchmark/private-answer-bundle/v1",
        {
            "benchmark_version": benchmark_version,
            "purpose": purpose,
            "records": [
                {"item_id": item.item_id, "sha256": item.private_answer_record_sha256}
                for item in sorted_answers
            ],
        },
    )
    candidate = hash_domain(
        "unfrozen-schemas/benchmark/candidate-bundle-root/v1",
        {
            "benchmark_version": benchmark_version,
            "purpose": purpose,
            "source_snapshot_sha256": source_snapshot_sha256,
            "quarantine_scope_sha256": quarantine_scope_sha256,
            "model_visible_bundle_sha256": model_visible,
            "annotation_metadata_bundle_sha256": annotations,
            "private_answer_bundle_sha256": private_answers,
            "complete_private_records": [
                {"item_id": item.item_id, "sha256": item.complete_private_item_record_sha256}
                for item in sorted_items
            ],
        },
    )
    return {
        "model_visible_bundle_sha256": model_visible,
        "annotation_metadata_bundle_sha256": annotations,
        "private_answer_bundle_sha256": private_answers,
        "candidate_bundle_root_sha256": candidate,
    }


def public_metadata_bundle_hash(public: PublicManifest, coverage: CoverageSummary) -> str:
    return hash_domain(
        "unfrozen-schemas/benchmark/public-metadata-bundle/v1",
        {"public_manifest": public, "coverage_summary": coverage},
    )


def freeze_approval_hash(approval: FreezeApproval) -> str:
    payload = approval.model_dump(mode="json", exclude={"approval_sha256"})
    return hash_domain("unfrozen-schemas/benchmark/freeze-approval/v1", payload)


def frozen_manifest_hash(manifest: FrozenManifest) -> str:
    payload = manifest.model_dump(mode="json", exclude={"frozen_manifest_sha256"})
    return hash_domain("unfrozen-schemas/benchmark/frozen-manifest/v1", payload)


def quarantine_scope_hash(scope: QuarantineScope) -> str:
    payload = scope.model_dump(mode="json", exclude={"quarantine_scope_sha256"})
    return hash_domain("unfrozen-schemas/benchmark/quarantine-scope/v1", payload)
