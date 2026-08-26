"""Canonical SHA-256 domains for the separately versioned M2.2 layer."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from typing import Any

from unfrozen_schemas.evaluation.benchmark_hashing import canonical_logical_bytes
from unfrozen_schemas.evaluation.literal_models import (
    LiteralCandidateManifest,
    LiteralItemBinding,
    LiteralItemBindingBundle,
    LiteralLexicalAudit,
    LiteralOperationRecord,
    LiteralPartitionPlan,
    LiteralReviewManifest,
    LiteralSourceBundleManifest,
    LiteralSplitAudit,
    LiteralTemplate,
    LiteralTemplateRegistryManifest,
    LiteralValidationReport,
    LiteralWitnessBundle,
    LiteralWitnessRecord,
)

LITERAL_HASH_DOMAINS: frozenset[str] = frozenset(
    {
        "unfrozen-schemas/literal/literal-partition-plan/v1",
        "unfrozen-schemas/literal/literal-template/v1",
        "unfrozen-schemas/literal/literal-template-registry/v1",
        "unfrozen-schemas/literal/literal-item-binding/v1",
        "unfrozen-schemas/literal/literal-item-binding-bundle/v1",
        "unfrozen-schemas/literal/literal-witness/v1",
        "unfrozen-schemas/literal/literal-witness-bundle/v1",
        "unfrozen-schemas/literal/literal-lexical-audit/v1",
        "unfrozen-schemas/literal/literal-split-audit/v1",
        "unfrozen-schemas/literal/literal-validation-report/v1",
        "unfrozen-schemas/literal/literal-source-bundle/v1",
        "unfrozen-schemas/literal/literal-review-content-bundle/v1",
        "unfrozen-schemas/literal/literal-review-manifest/v1",
        "unfrozen-schemas/literal/literal-candidate-root/v1",
        "unfrozen-schemas/literal/literal-operation/v1",
    }
)


def literal_hash(domain: str, payload: Any) -> str:
    if domain not in LITERAL_HASH_DOMAINS:
        raise ValueError(f"Unknown literal hash domain: {domain}")
    return hashlib.sha256(
        canonical_logical_bytes({"domain": domain, "payload": payload})
    ).hexdigest()


def partition_plan_hash(value: LiteralPartitionPlan) -> str:
    return literal_hash(
        "unfrozen-schemas/literal/literal-partition-plan/v1",
        value.model_dump(mode="json", exclude={"partition_plan_sha256"}),
    )


def template_hash(value: LiteralTemplate) -> str:
    return literal_hash("unfrozen-schemas/literal/literal-template/v1", value)


def template_registry_hash(value: LiteralTemplateRegistryManifest) -> str:
    return literal_hash(
        "unfrozen-schemas/literal/literal-template-registry/v1",
        value.model_dump(mode="json", exclude={"template_registry_sha256"}),
    )


def witness_hash(value: LiteralWitnessRecord) -> str:
    return literal_hash(
        "unfrozen-schemas/literal/literal-witness/v1",
        value.model_dump(mode="json", exclude={"witness_sha256"}),
    )


def witness_bundle_hash(value: LiteralWitnessBundle) -> str:
    return literal_hash(
        "unfrozen-schemas/literal/literal-witness-bundle/v1",
        value.model_dump(mode="json", exclude={"witness_bundle_sha256"}),
    )


def item_binding_hash(value: LiteralItemBinding) -> str:
    return literal_hash(
        "unfrozen-schemas/literal/literal-item-binding/v1",
        value.model_dump(mode="json", exclude={"item_binding_sha256"}),
    )


def item_binding_bundle_hash(value: LiteralItemBindingBundle) -> str:
    return literal_hash(
        "unfrozen-schemas/literal/literal-item-binding-bundle/v1",
        value.model_dump(mode="json", exclude={"item_binding_bundle_sha256"}),
    )


def lexical_audit_hash(value: LiteralLexicalAudit) -> str:
    return literal_hash(
        "unfrozen-schemas/literal/literal-lexical-audit/v1",
        value.model_dump(mode="json", exclude={"lexical_audit_sha256"}),
    )


def split_audit_hash(value: LiteralSplitAudit) -> str:
    return literal_hash(
        "unfrozen-schemas/literal/literal-split-audit/v1",
        value.model_dump(mode="json", exclude={"split_audit_sha256"}),
    )


def validation_report_hash(value: LiteralValidationReport) -> str:
    return literal_hash(
        "unfrozen-schemas/literal/literal-validation-report/v1",
        value.model_dump(mode="json", exclude={"literal_validation_report_sha256"}),
    )


def source_bundle_hash(value: LiteralSourceBundleManifest) -> str:
    # Operation provenance and physical artifact records contextualise a run, but
    # contain timestamps, platform information, and container bytes. They are
    # deliberately excluded from the logical source identity.
    return literal_hash(
        "unfrozen-schemas/literal/literal-source-bundle/v1",
        value.model_dump(
            mode="json",
            exclude={
                "artifacts",
                "generation_operation_sha256",
                "literal_source_bundle_sha256",
            },
        ),
    )


def review_content_bundle_hash(records: Sequence[dict[str, object]]) -> str:
    return literal_hash(
        "unfrozen-schemas/literal/literal-review-content-bundle/v1",
        sorted(records, key=lambda item: str(item["path"])),
    )


def review_manifest_hash(value: LiteralReviewManifest) -> str:
    payload = value.model_dump(mode="json", exclude={"review_manifest_sha256"})
    # PNG container bytes may differ across operating systems even when the
    # exact raw scientific inspection pixels agree. Exact PNG file hashes stay
    # in the manifest for local read-back; the logical manifest root binds the
    # stable raw-pixel identities and all non-render artifacts.
    payload["artifacts"] = [
        artifact for artifact in payload["artifacts"] if not str(artifact["path"]).endswith(".png")
    ]
    return literal_hash(
        "unfrozen-schemas/literal/literal-review-manifest/v1",
        payload,
    )


def literal_candidate_root_hash(value: LiteralCandidateManifest) -> str:
    # Exact file and Git provenance remain recorded for owner review, while the
    # logical identity binds the platform-independent M2.1 candidate root.
    return literal_hash(
        "unfrozen-schemas/literal/literal-candidate-root/v1",
        value.model_dump(
            mode="json",
            exclude={
                "git",
                "m2_1_candidate_manifest_file_sha256",
                "literal_candidate_root_sha256",
            },
        ),
    )


def operation_hash(value: LiteralOperationRecord) -> str:
    return literal_hash(
        "unfrozen-schemas/literal/literal-operation/v1",
        value.model_dump(mode="json", exclude={"operation_sha256"}),
    )
