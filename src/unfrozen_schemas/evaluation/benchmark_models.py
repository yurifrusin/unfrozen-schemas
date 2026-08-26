"""Strict, versioned records for the M2.1 benchmark lifecycle."""

from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from unfrozen_schemas.budgets import ResourceBudget
from unfrozen_schemas.config import FrozenModel
from unfrozen_schemas.provenance import ArtifactRecord, GitState, PlatformInformation

SHA256_PATTERN = r"^[a-f0-9]{64}$"
SLUG_PATTERN = r"^[a-z0-9][a-z0-9._-]*$"
ENGINEERING_VERSION = "engineering-benchmark-lifecycle-v1"
PRODUCTION_VERSION = "v1_core"
SELECTION_VERSION = "selection_probe_v1"
CANONICAL_QUARANTINE_ROOTS: tuple[str, ...] = (
    "benchmarks/frozen",
    "benchmarks/private",
    "benchmarks/selection",
)


class BenchmarkPurpose(StrEnum):
    """Mutually quarantined uses for benchmark material."""

    OUTCOME = "outcome"
    SELECTION = "selection"
    ENGINEERING = "engineering"
    RETENTION = "retention"


class LifecycleState(StrEnum):
    SOURCE = "SOURCE"
    PRIVATE = "PRIVATE"
    FROZEN = "FROZEN"


class SchemaDesignation(StrEnum):
    ITEM_SCHEMA = "item_schema"
    CONTROL_SCHEMA = "control_schema"
    NOT_APPLICABLE = "not_applicable"


class TrainedSchemaRole(StrEnum):
    TRAINED = "trained"
    UNTRAINED = "untrained"
    NOT_APPLICABLE = "not_applicable"


class OriginClassification(StrEnum):
    SIMULATOR_DERIVED = "simulator_derived"
    HUMAN_AUTHORED = "human_authored"
    EXTERNAL_LICENSED = "external_licensed"
    ENGINEERING_FIXTURE = "engineering_fixture"


class RightsStatus(StrEnum):
    UNRESOLVED = "unresolved"
    CLEARED = "cleared"
    LICENSED = "licensed"
    NOT_APPLICABLE_ENGINEERING = "not_applicable_engineering"


class GovernanceStatus(StrEnum):
    UNRESOLVED = "unresolved"
    APPROVED = "approved"
    NOT_APPLICABLE_ENGINEERING = "not_applicable_engineering"


class HumanValidationStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    NOT_APPLICABLE_ENGINEERING = "not_applicable_engineering"


class AdjudicationStatus(StrEnum):
    NOT_STARTED = "not_started"
    UNRESOLVED = "unresolved"
    RESOLVED = "resolved"
    NOT_APPLICABLE_ENGINEERING = "not_applicable_engineering"


class AnswerProvenance(StrEnum):
    INDEPENDENT_HUMAN = "independent_human"
    INDEPENDENT_SIMULATOR = "independent_simulator"
    ENGINEERING_FIXTURE = "engineering_fixture"


class QuarantineScopeMode(StrEnum):
    """The only supported mandatory purpose-quarantine scope modes."""

    CANONICAL_ROOT_SCAN = "canonical_root_scan"
    ENGINEERING_EMPTY = "engineering_empty"


class QuarantineScopeDeclaration(FrozenModel):
    schema_version: Literal["1"] = "1"
    mode: QuarantineScopeMode
    canonical_roots: tuple[str, ...]

    @model_validator(mode="after")
    def validate_scope_shape(self) -> QuarantineScopeDeclaration:
        if tuple(sorted(self.canonical_roots)) != self.canonical_roots:
            raise ValueError("Quarantine roots must use canonical sorted ordering")
        if len(self.canonical_roots) != len(set(self.canonical_roots)):
            raise ValueError("Quarantine roots must be unique")
        if self.mode is QuarantineScopeMode.ENGINEERING_EMPTY:
            if self.canonical_roots:
                raise ValueError("An engineering-empty quarantine scope cannot declare roots")
        elif self.canonical_roots != CANONICAL_QUARANTINE_ROOTS:
            raise ValueError(
                "A non-engineering quarantine scan must cover every canonical benchmark root"
            )
        return self


class QuarantineManifestReference(FrozenModel):
    path: str = Field(min_length=1)
    file_sha256: str = Field(pattern=SHA256_PATTERN)
    manifest_kind: Literal["benchmark_private_candidate", "benchmark_frozen"]
    lifecycle_state: Literal[LifecycleState.PRIVATE, LifecycleState.FROZEN]
    benchmark_version: str = Field(min_length=1, pattern=SLUG_PATTERN)
    purpose: BenchmarkPurpose
    candidate_bundle_root_sha256: str = Field(pattern=SHA256_PATTERN)
    item_ids: tuple[str, ...]
    exact_displayed_input_fingerprints: tuple[str, ...]
    order_neutral_item_content_fingerprints: tuple[str, ...]

    @model_validator(mode="after")
    def validate_canonical_reference(self) -> QuarantineManifestReference:
        for field_name in (
            "item_ids",
            "exact_displayed_input_fingerprints",
            "order_neutral_item_content_fingerprints",
        ):
            values = getattr(self, field_name)
            if tuple(sorted(values)) != values or len(values) != len(set(values)):
                raise ValueError(f"{field_name} must be sorted and unique")
        for fingerprint in (
            *self.exact_displayed_input_fingerprints,
            *self.order_neutral_item_content_fingerprints,
        ):
            if not re.fullmatch(SHA256_PATTERN, fingerprint):
                raise ValueError("Quarantine content fingerprints must be SHA-256 values")
        return self


class QuarantineScope(FrozenModel):
    schema_version: Literal["1"] = "1"
    scope_kind: Literal["benchmark_purpose_quarantine_scope"] = "benchmark_purpose_quarantine_scope"
    mode: QuarantineScopeMode
    canonical_roots: tuple[str, ...]
    manifests: tuple[QuarantineManifestReference, ...]
    quarantine_scope_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_canonical_scope(self) -> QuarantineScope:
        declaration = QuarantineScopeDeclaration(
            mode=self.mode,
            canonical_roots=self.canonical_roots,
        )
        if declaration.mode is QuarantineScopeMode.ENGINEERING_EMPTY and self.manifests:
            raise ValueError("Engineering-empty quarantine scope cannot contain manifests")
        paths = tuple(reference.path for reference in self.manifests)
        if tuple(sorted(paths)) != paths or len(paths) != len(set(paths)):
            raise ValueError("Quarantine manifest references must use unique sorted paths")
        return self


class AnswerOption(FrozenModel):
    option_id: str = Field(min_length=1, pattern=SLUG_PATTERN)
    text: str = Field(min_length=1)


class ModelVisibleContent(FrozenModel):
    prompt: str = Field(min_length=1)
    ordered_options: tuple[AnswerOption, ...] = Field(min_length=2)
    instructions: str | None = None
    reverse_pair_id: str | None = Field(default=None, pattern=SLUG_PATTERN)
    variant_id: str = Field(min_length=1, pattern=SLUG_PATTERN)
    option_permutation: tuple[str, ...] = Field(min_length=2)
    closed_book_eligible: bool
    open_book_eligible: bool

    @model_validator(mode="after")
    def validate_options(self) -> ModelVisibleContent:
        option_ids = tuple(option.option_id for option in self.ordered_options)
        if len(option_ids) != len(set(option_ids)):
            raise ValueError("Model-visible option IDs must be unique")
        normalised_text = tuple(
            " ".join(option.text.split()).casefold() for option in self.ordered_options
        )
        if len(normalised_text) != len(set(normalised_text)):
            raise ValueError("Model-visible option text must be unambiguous and unique")
        if self.option_permutation != option_ids:
            raise ValueError("option_permutation must exactly match ordered option IDs")
        return self


class ScientificAnnotations(FrozenModel):
    required_causal_factors: tuple[str, ...]
    composition_depth: int = Field(ge=0)
    lexical_cue_annotations: tuple[str, ...]
    source_mechanism_family: str = Field(min_length=1, pattern=SLUG_PATTERN)
    conventionality_estimate: float | None = Field(default=None, ge=0.0, le=1.0)
    external_language_overlap_flags: tuple[str, ...]
    target_domain_family: str = Field(min_length=1, pattern=SLUG_PATTERN)
    trained_schema_role: TrainedSchemaRole

    @model_validator(mode="after")
    def validate_unique_annotations(self) -> ScientificAnnotations:
        for name in (
            "required_causal_factors",
            "lexical_cue_annotations",
            "external_language_overlap_flags",
        ):
            values = getattr(self, name)
            if len(values) != len(set(values)):
                raise ValueError(f"{name} must not contain duplicates")
        return self


class ProvenanceRights(FrozenModel):
    authorship_origin: str = Field(min_length=1)
    source_reference: str = Field(min_length=1)
    origin_classification: OriginClassification
    rights_status: RightsStatus
    licence_reference: str | None = None
    transformation_history: tuple[str, ...]
    reviewer_references: tuple[str, ...]
    ethics_status: GovernanceStatus
    ethics_reference: str | None = None
    created_from_source_record: str = Field(min_length=1, pattern=SLUG_PATTERN)
    created_from_source_revision: int = Field(ge=1)


class HumanValidationMetadata(FrozenModel):
    validation_status: HumanValidationStatus
    protocol_version: str | None = None
    validator_count: int | None = Field(default=None, ge=0)
    agreement_metric: str | None = None
    agreement_value: float | None = Field(default=None, ge=0.0)
    adjudication_status: AdjudicationStatus
    ambiguity_findings: tuple[str, ...]
    validator_population_description: str | None = None
    ethics_determination_reference: str | None = None

    @model_validator(mode="after")
    def validate_passed_record(self) -> HumanValidationMetadata:
        if self.validation_status is HumanValidationStatus.PASSED:
            required = {
                "protocol_version": self.protocol_version,
                "validator_count": self.validator_count,
                "agreement_metric": self.agreement_metric,
                "agreement_value": self.agreement_value,
                "validator_population_description": self.validator_population_description,
                "ethics_determination_reference": self.ethics_determination_reference,
            }
            missing = [name for name, value in required.items() if value is None or value == ""]
            if missing:
                raise ValueError(f"Passed human validation is incomplete: {missing}")
            if self.validator_count == 0:
                raise ValueError("Passed human validation requires at least one validator")
            if self.adjudication_status is not AdjudicationStatus.RESOLVED:
                raise ValueError("Passed human validation requires resolved adjudication")
        return self


class SourcePrivateAnswer(FrozenModel):
    correct_option_id: str = Field(min_length=1, pattern=SLUG_PATTERN)
    answer_rationale: str | None = None
    simulator_verification_reference: str | None = None
    answer_provenance: AnswerProvenance
    adjudication_reference: str | None = None

    @model_validator(mode="after")
    def validate_evidence(self) -> SourcePrivateAnswer:
        if not self.answer_rationale and not self.simulator_verification_reference:
            raise ValueError("A private answer requires a rationale or simulator reference")
        return self


class SourceItemRecord(FrozenModel):
    schema_version: Literal["1"] = "1"
    item_id: str = Field(min_length=3, pattern=SLUG_PATTERN)
    item_revision: int = Field(ge=1)
    purpose: BenchmarkPurpose
    identity_purpose: BenchmarkPurpose
    task_family_slug: str = Field(min_length=1, pattern=SLUG_PATTERN)
    transfer_level: int | None = Field(default=None, ge=0, le=4)
    schema_designation: SchemaDesignation
    target_domain_family: str = Field(min_length=1, pattern=SLUG_PATTERN)
    source_mechanism_family: str = Field(min_length=1, pattern=SLUG_PATTERN)
    prompt_template_id: str = Field(min_length=1, pattern=SLUG_PATTERN)
    partition_id: str = Field(min_length=1, pattern=SLUG_PATTERN)
    release_status: Literal["source_private"] = "source_private"
    engineering_only: bool
    scientific_eligible: bool
    promotable: bool
    model_visible: ModelVisibleContent
    scientific_annotations: ScientificAnnotations
    provenance: ProvenanceRights
    human_validation: HumanValidationMetadata
    private_answer: SourcePrivateAnswer

    @model_validator(mode="after")
    def validate_identity_and_classification(self) -> SourceItemRecord:
        if self.purpose is not self.identity_purpose:
            raise ValueError("Benchmark purpose is immutable for an existing item identity")
        if self.source_mechanism_family != self.scientific_annotations.source_mechanism_family:
            raise ValueError("Source-mechanism classification and annotation must agree")
        if self.target_domain_family != self.scientific_annotations.target_domain_family:
            raise ValueError("Target-domain classification and annotation must agree")
        if self.provenance.created_from_source_record != self.item_id:
            raise ValueError("created_from_source_record must equal the stable item_id")
        if self.provenance.created_from_source_revision != self.item_revision:
            raise ValueError("created_from_source_revision must equal item_revision")
        option_ids = {option.option_id for option in self.model_visible.ordered_options}
        if self.private_answer.correct_option_id not in option_ids:
            raise ValueError("The correct option must reference a model-visible option ID")
        if self.purpose is BenchmarkPurpose.ENGINEERING:
            if not self.engineering_only or self.scientific_eligible or self.promotable:
                raise ValueError(
                    "Engineering items must be engineering-only, non-scientific, and not promotable"
                )
            if (
                self.provenance.origin_classification
                is not OriginClassification.ENGINEERING_FIXTURE
            ):
                raise ValueError("Engineering items require engineering-fixture provenance")
            if self.private_answer.answer_provenance is not AnswerProvenance.ENGINEERING_FIXTURE:
                raise ValueError("Engineering answers require engineering-fixture provenance")
            if (
                self.provenance.rights_status is not RightsStatus.NOT_APPLICABLE_ENGINEERING
                or self.provenance.ethics_status is not GovernanceStatus.NOT_APPLICABLE_ENGINEERING
                or self.human_validation.validation_status
                is not HumanValidationStatus.NOT_APPLICABLE_ENGINEERING
                or self.human_validation.adjudication_status
                is not AdjudicationStatus.NOT_APPLICABLE_ENGINEERING
            ):
                raise ValueError(
                    "Engineering items require not-applicable engineering governance records"
                )
        else:
            if self.engineering_only:
                raise ValueError("Non-engineering purposes cannot be marked engineering-only")
            if (
                self.provenance.origin_classification is OriginClassification.ENGINEERING_FIXTURE
                or self.private_answer.answer_provenance is AnswerProvenance.ENGINEERING_FIXTURE
            ):
                raise ValueError("Non-engineering items cannot use engineering-fixture provenance")
            if (
                self.provenance.rights_status is RightsStatus.NOT_APPLICABLE_ENGINEERING
                or self.provenance.ethics_status is GovernanceStatus.NOT_APPLICABLE_ENGINEERING
                or self.human_validation.validation_status
                is HumanValidationStatus.NOT_APPLICABLE_ENGINEERING
                or self.human_validation.adjudication_status
                is AdjudicationStatus.NOT_APPLICABLE_ENGINEERING
            ):
                raise ValueError(
                    "Non-engineering items cannot use engineering-only governance classifications"
                )
        return self


class ProductionPrerequisites(FrozenModel):
    literal_items_approval_sha256: str = Field(pattern=SHA256_PATTERN)
    transfer_items_validation_sha256: str = Field(pattern=SHA256_PATTERN)
    scoring_leakage_retention_approval_sha256: str = Field(pattern=SHA256_PATTERN)
    hardware_qualification_sha256: str = Field(pattern=SHA256_PATTERN)
    model_selection_approval_sha256: str = Field(pattern=SHA256_PATTERN)
    owner_freeze_authorisation_sha256: str = Field(pattern=SHA256_PATTERN)


class SourceManifest(FrozenModel):
    schema_version: Literal["1"] = "1"
    manifest_kind: Literal["benchmark_source"] = "benchmark_source"
    lifecycle_state: Literal[LifecycleState.SOURCE] = LifecycleState.SOURCE
    source_format: Literal["canonical-jsonl-v1"] = "canonical-jsonl-v1"
    benchmark_version: str = Field(min_length=1, pattern=SLUG_PATTERN)
    purpose: BenchmarkPurpose
    engineering_only: bool
    scientific_eligible: bool
    promotable: bool
    items_file: Literal["items.jsonl"] = "items.jsonl"
    expected_item_count: int = Field(ge=1)
    rights_determination_reference: str = Field(min_length=1)
    human_validation_reference: str = Field(min_length=1)
    ethics_determination_reference: str = Field(min_length=1)
    production_prerequisites: ProductionPrerequisites | None = None
    quarantine_scope: QuarantineScopeDeclaration

    @model_validator(mode="after")
    def validate_reserved_version_and_purpose(self) -> SourceManifest:
        if self.purpose is BenchmarkPurpose.ENGINEERING:
            if self.benchmark_version in {PRODUCTION_VERSION, SELECTION_VERSION}:
                raise ValueError("Engineering sources cannot use reserved benchmark versions")
            if not self.engineering_only or self.scientific_eligible or self.promotable:
                raise ValueError(
                    "Engineering sources must be engineering-only, non-scientific, "
                    "and not promotable"
                )
            if self.quarantine_scope.mode is not QuarantineScopeMode.ENGINEERING_EMPTY:
                raise ValueError("Engineering sources require an explicit empty quarantine scope")
        else:
            if self.engineering_only:
                raise ValueError("Non-engineering sources cannot be marked engineering-only")
            if self.quarantine_scope.mode is not QuarantineScopeMode.CANONICAL_ROOT_SCAN:
                raise ValueError(
                    "Non-engineering sources require the mandatory canonical quarantine scan"
                )
        if (
            self.benchmark_version == PRODUCTION_VERSION
            and self.purpose is not BenchmarkPurpose.OUTCOME
        ):
            raise ValueError("v1_core is reserved exclusively for outcome benchmarks")
        if (
            self.benchmark_version == SELECTION_VERSION
            and self.purpose is not BenchmarkPurpose.SELECTION
        ):
            raise ValueError("selection_probe_v1 is reserved exclusively for selection")
        if self.purpose is BenchmarkPurpose.OUTCOME and self.benchmark_version == SELECTION_VERSION:
            raise ValueError("Outcome data cannot reuse selection_probe_v1")
        return self


class SourceSnapshotHeader(FrozenModel):
    schema_version: Literal["1"] = "1"
    source_format: Literal["canonical-jsonl-v1"] = "canonical-jsonl-v1"
    benchmark_version: str = Field(min_length=1, pattern=SLUG_PATTERN)
    purpose: BenchmarkPurpose
    engineering_only: bool
    scientific_eligible: bool
    promotable: bool
    item_count: int
    rights_determination_reference: str
    human_validation_reference: str
    ethics_determination_reference: str
    production_prerequisites: ProductionPrerequisites | None
    quarantine_scope: QuarantineScopeDeclaration


class SourceSnapshot(FrozenModel):
    schema_version: Literal["1"] = "1"
    snapshot_kind: Literal["private_answer_bearing_source_snapshot"] = (
        "private_answer_bearing_source_snapshot"
    )
    header: SourceSnapshotHeader
    items: tuple[SourceItemRecord, ...]
    source_snapshot_sha256: str = Field(pattern=SHA256_PATTERN)


class PrivateAnswerRecord(FrozenModel):
    schema_version: Literal["1"] = "1"
    item_id: str = Field(pattern=SLUG_PATTERN)
    item_revision: int = Field(ge=1)
    purpose: BenchmarkPurpose
    correct_option_id: str = Field(pattern=SLUG_PATTERN)
    answer_rationale: str | None
    simulator_verification_reference: str | None
    answer_provenance: AnswerProvenance
    adjudication_reference: str | None
    private_answer_record_sha256: str = Field(pattern=SHA256_PATTERN)


class BuiltBenchmarkItem(FrozenModel):
    schema_version: Literal["1"] = "1"
    item_id: str = Field(pattern=SLUG_PATTERN)
    item_revision: int = Field(ge=1)
    purpose: BenchmarkPurpose
    identity_purpose: BenchmarkPurpose
    task_family_slug: str = Field(min_length=1, pattern=SLUG_PATTERN)
    transfer_level: int | None
    schema_designation: SchemaDesignation
    target_domain_family: str = Field(min_length=1, pattern=SLUG_PATTERN)
    source_mechanism_family: str = Field(min_length=1, pattern=SLUG_PATTERN)
    prompt_template_id: str = Field(min_length=1, pattern=SLUG_PATTERN)
    partition_id: str = Field(min_length=1, pattern=SLUG_PATTERN)
    release_status: Literal["private_candidate"] = "private_candidate"
    engineering_only: bool
    scientific_eligible: bool
    promotable: bool
    model_visible: ModelVisibleContent
    scientific_annotations: ScientificAnnotations
    provenance: ProvenanceRights
    human_validation: HumanValidationMetadata
    model_visible_sha256: str = Field(pattern=SHA256_PATTERN)
    exact_displayed_input_fingerprint_sha256: str = Field(pattern=SHA256_PATTERN)
    order_neutral_item_content_fingerprint_sha256: str = Field(pattern=SHA256_PATTERN)
    annotation_metadata_sha256: str = Field(pattern=SHA256_PATTERN)
    complete_private_item_record_sha256: str = Field(pattern=SHA256_PATTERN)


class ResolvedBenchmarkConfig(FrozenModel):
    schema_version: Literal["1"] = "1"
    source_format: Literal["canonical-jsonl-v1"] = "canonical-jsonl-v1"
    built_item_format: Literal["canonical-jsonl-v1"] = "canonical-jsonl-v1"
    benchmark_version: str = Field(min_length=1, pattern=SLUG_PATTERN)
    purpose: BenchmarkPurpose
    quarantine_scope_sha256: str | None = Field(default=None, pattern=SHA256_PATTERN)
    source_manifest_filename: Literal["source_manifest.json"] = "source_manifest.json"
    source_items_filename: Literal["items.jsonl"] = "items.jsonl"
    candidate_items_filename: Literal["items.jsonl"] = "items.jsonl"
    private_answers_filename: Literal["private_answers.jsonl"] = "private_answers.jsonl"
    device: Literal["cpu"] = "cpu"
    network_access: Literal[False] = False
    model_access: Literal[False] = False
    gpu_access: Literal[False] = False


class CoverageSummary(FrozenModel):
    schema_version: Literal["1"] = "1"
    benchmark_version: str = Field(min_length=1, pattern=SLUG_PATTERN)
    purpose: BenchmarkPurpose
    item_count: int
    task_family_counts: dict[str, int]
    schema_designation_counts: dict[str, int]
    partition_counts: dict[str, int]
    transfer_level_counts: dict[str, int]
    target_domain_family_counts: dict[str, int]
    source_mechanism_family_counts: dict[str, int]
    trained_schema_role_counts: dict[str, int]
    reverse_pair_count: int
    closed_book_eligible_count: int
    open_book_eligible_count: int
    engineering_only: bool
    scientific_eligible: bool


class PublicManifest(FrozenModel):
    schema_version: Literal["1"] = "1"
    manifest_kind: Literal["benchmark_public_metadata"] = "benchmark_public_metadata"
    lifecycle_state: Literal[LifecycleState.PRIVATE] = LifecycleState.PRIVATE
    benchmark_version: str = Field(min_length=1, pattern=SLUG_PATTERN)
    purpose: BenchmarkPurpose
    engineering_only: bool
    scientific_eligible: bool
    promotable: bool
    item_count: int
    origin_classification_counts: dict[str, int]
    rights_status_counts: dict[str, int]
    human_validation_status_counts: dict[str, int]
    ethics_status_counts: dict[str, int]
    source_snapshot_sha256: str = Field(pattern=SHA256_PATTERN)
    model_visible_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    annotation_metadata_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    candidate_bundle_root_sha256: str = Field(pattern=SHA256_PATTERN)
    private_answer_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    quarantine_scope_sha256: str = Field(pattern=SHA256_PATTERN)
    coverage_summary_path: Literal["coverage_summary.json"] = "coverage_summary.json"
    benchmark_card_path: Literal["docs/benchmark-card.md"] = "docs/benchmark-card.md"
    contains_prompts_or_options: Literal[False] = False
    contains_per_item_answer_hashes: Literal[False] = False
    contains_answers_or_rationales: Literal[False] = False


class ValidationReport(FrozenModel):
    schema_version: Literal["1"] = "1"
    report_kind: Literal["benchmark_validation"] = "benchmark_validation"
    benchmark_version: str = Field(min_length=1, pattern=SLUG_PATTERN)
    lifecycle_state: LifecycleState
    purpose: BenchmarkPurpose
    status: Literal["PASS"] = "PASS"
    item_count: int
    checks: tuple[str, ...]


class BenchmarkOperationRecord(FrozenModel):
    schema_version: Literal["1"] = "1"
    record_kind: Literal["benchmark_operation"] = "benchmark_operation"
    operation_id: str = Field(min_length=1)
    operation_kind: Literal["build_benchmark", "freeze_benchmark"]
    engineering_only: bool
    scientific_result: Literal[False] = False
    git: GitState
    codex_spec_sha256: str = Field(pattern=SHA256_PATTERN)
    quarantine_scope_sha256: str | None = Field(default=None, pattern=SHA256_PATTERN)
    resolved_configuration: ResolvedBenchmarkConfig
    input_hashes: dict[str, str]
    lifecycle_state_before: LifecycleState
    lifecycle_state_after: LifecycleState | None
    benchmark_version: str = Field(min_length=1, pattern=SLUG_PATTERN)
    purpose: BenchmarkPurpose
    item_count: int
    artifacts: tuple[ArtifactRecord, ...]
    package_versions: dict[str, str]
    platform: PlatformInformation
    started_at: datetime
    ended_at: datetime
    status: Literal["COMPLETED", "FAILED"]
    failure_reason: str | None
    resource_budget: ResourceBudget

    @model_validator(mode="after")
    def validate_operation(self) -> BenchmarkOperationRecord:
        if self.ended_at < self.started_at:
            raise ValueError("Benchmark operation ended before it started")
        if self.resource_budget.schema_version != "2":
            raise ValueError("Benchmark operations must reuse ResourceBudget schema version 2")
        if self.resource_budget.run_id != self.operation_id:
            raise ValueError("Benchmark operation and resource-budget IDs must match")
        if self.resource_budget.interval_start != self.started_at:
            raise ValueError("Benchmark operation and resource budget must start together")
        if self.resource_budget.interval_end != self.ended_at:
            raise ValueError("Benchmark operation and resource budget must end together")
        if self.status == "FAILED" and not self.failure_reason:
            raise ValueError("Failed benchmark operations require the original failure reason")
        if self.status == "COMPLETED" and self.failure_reason is not None:
            raise ValueError("Completed benchmark operations cannot contain a failure reason")
        if self.status == "COMPLETED" and self.quarantine_scope_sha256 is None:
            raise ValueError("Completed benchmark operations require a quarantine-scope identity")
        return self


class CandidateManifest(FrozenModel):
    schema_version: Literal["1"] = "1"
    manifest_kind: Literal["benchmark_private_candidate"] = "benchmark_private_candidate"
    lifecycle_state: Literal[LifecycleState.PRIVATE] = LifecycleState.PRIVATE
    benchmark_version: str = Field(min_length=1, pattern=SLUG_PATTERN)
    purpose: BenchmarkPurpose
    engineering_only: bool
    scientific_eligible: bool
    promotable: bool
    source_snapshot_sha256: str = Field(pattern=SHA256_PATTERN)
    model_visible_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    annotation_metadata_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    private_answer_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    candidate_bundle_root_sha256: str = Field(pattern=SHA256_PATTERN)
    public_metadata_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    quarantine_scope_sha256: str = Field(pattern=SHA256_PATTERN)
    codex_spec_sha256: str = Field(pattern=SHA256_PATTERN)
    git: GitState
    item_count: int = Field(ge=1)
    item_ids: tuple[str, ...]
    source_snapshot_path: Literal["source_snapshot.json"] = "source_snapshot.json"
    items_path: Literal["items.jsonl"] = "items.jsonl"
    private_answers_path: Literal["private_answers.jsonl"] = "private_answers.jsonl"
    public_manifest_path: Literal["public_manifest.json"] = "public_manifest.json"
    coverage_summary_path: Literal["coverage_summary.json"] = "coverage_summary.json"
    resolved_configuration_path: Literal["resolved_benchmark_config.json"] = (
        "resolved_benchmark_config.json"
    )
    validation_report_path: Literal["validation_report.json"] = "validation_report.json"
    resource_budget_path: Literal["resource_budget.json"] = "resource_budget.json"
    operation_record_path: Literal["operation_record.json"] = "operation_record.json"
    quarantine_scope_path: Literal["quarantine_scope.json"] = "quarantine_scope.json"
    production_prerequisites: ProductionPrerequisites | None
    rights_determination_reference: str
    human_validation_reference: str
    ethics_determination_reference: str
    artifacts: tuple[ArtifactRecord, ...]

    @model_validator(mode="after")
    def validate_item_identity_list(self) -> CandidateManifest:
        if tuple(sorted(self.item_ids)) != self.item_ids:
            raise ValueError("Candidate item IDs must use canonical ordering")
        if len(self.item_ids) != len(set(self.item_ids)):
            raise ValueError("Candidate item IDs must be unique")
        if len(self.item_ids) != self.item_count:
            raise ValueError("Candidate item count does not match item IDs")
        return self


class FreezeApproval(FrozenModel):
    schema_version: Literal["1"] = "1"
    artifact_kind: Literal["benchmark_freeze_approval"] = "benchmark_freeze_approval"
    approval_class: Literal["engineering_fixture", "production"]
    benchmark_version: str = Field(min_length=1, pattern=SLUG_PATTERN)
    benchmark_purpose: BenchmarkPurpose
    engineering_only: bool
    candidate_manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    candidate_bundle_root_sha256: str = Field(pattern=SHA256_PATTERN)
    private_answer_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    public_metadata_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    quarantine_scope_sha256: str = Field(pattern=SHA256_PATTERN)
    codex_spec_sha256: str = Field(pattern=SHA256_PATTERN)
    git_commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    git_dirty: Literal[False] = False
    transition_from: Literal[LifecycleState.PRIVATE] = LifecycleState.PRIVATE
    transition_to: Literal[LifecycleState.FROZEN] = LifecycleState.FROZEN
    rights_determination_reference: str = Field(min_length=1)
    human_validation_reference: str = Field(min_length=1)
    ethics_determination_reference: str = Field(min_length=1)
    model_selection_approval_sha256: str | None = Field(default=None, pattern=SHA256_PATTERN)
    production_prerequisites: ProductionPrerequisites | None = None
    decision: Literal["APPROVED", "REJECTED"]
    signer: str = Field(min_length=1)
    timestamp: datetime
    rationale: str = Field(min_length=1)
    approval_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_approval_class(self) -> FreezeApproval:
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("Freeze approval timestamp must be timezone-aware")
        if self.approval_class == "engineering_fixture":
            if (
                not self.engineering_only
                or self.benchmark_purpose is not BenchmarkPurpose.ENGINEERING
            ):
                raise ValueError("Engineering approval cannot authorise scientific benchmark data")
            if self.model_selection_approval_sha256 is not None:
                raise ValueError("Engineering approval cannot impersonate model-selection approval")
            if self.production_prerequisites is not None:
                raise ValueError("Engineering approval cannot contain production prerequisites")
        else:
            if self.engineering_only:
                raise ValueError("Production approval cannot be engineering-only")
            if self.production_prerequisites is None:
                raise ValueError("Production approval requires explicit M2.2-M2.5 prerequisites")
            if self.model_selection_approval_sha256 is None:
                raise ValueError("Production approval requires model-selection approval")
        return self


class ImmutableReceipt(FrozenModel):
    schema_version: Literal["1"] = "1"
    receipt_kind: Literal["benchmark_write_once_receipt"] = "benchmark_write_once_receipt"
    benchmark_version: str = Field(min_length=1, pattern=SLUG_PATTERN)
    purpose: BenchmarkPurpose
    lifecycle_state: Literal[LifecycleState.FROZEN] = LifecycleState.FROZEN
    candidate_manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    candidate_bundle_root_sha256: str = Field(pattern=SHA256_PATTERN)
    freeze_approval_sha256: str = Field(pattern=SHA256_PATTERN)
    quarantine_scope_sha256: str = Field(pattern=SHA256_PATTERN)
    write_once: Literal[True] = True
    filesystem_read_only_is_advisory: Literal[True] = True


class FrozenManifest(FrozenModel):
    schema_version: Literal["1"] = "1"
    manifest_kind: Literal["benchmark_frozen"] = "benchmark_frozen"
    lifecycle_state: Literal[LifecycleState.FROZEN] = LifecycleState.FROZEN
    benchmark_version: str = Field(min_length=1, pattern=SLUG_PATTERN)
    purpose: BenchmarkPurpose
    engineering_only: bool
    scientific_eligible: bool
    promotable: bool
    item_count: int = Field(ge=1)
    candidate_manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    candidate_bundle_root_sha256: str = Field(pattern=SHA256_PATTERN)
    private_answer_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    public_metadata_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    quarantine_scope_sha256: str = Field(pattern=SHA256_PATTERN)
    freeze_approval_sha256: str = Field(pattern=SHA256_PATTERN)
    codex_spec_sha256: str = Field(pattern=SHA256_PATTERN)
    git_commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    candidate_manifest_path: Literal["candidate_manifest.json"] = "candidate_manifest.json"
    freeze_approval_path: Literal["freeze_approval.json"] = "freeze_approval.json"
    immutable_receipt_path: Literal["immutable_receipt.json"] = "immutable_receipt.json"
    resource_budget_path: Literal["freeze_resource_budget.json"] = "freeze_resource_budget.json"
    operation_record_path: Literal["freeze_operation.json"] = "freeze_operation.json"
    artifacts: tuple[ArtifactRecord, ...]
    frozen_manifest_sha256: str = Field(pattern=SHA256_PATTERN)


class BenchmarkOperationResult(FrozenModel):
    operation_id: str
    dry_run: bool
    benchmark_version: str = Field(min_length=1, pattern=SLUG_PATTERN)
    purpose: BenchmarkPurpose
    manifest_path: str | None
    candidate_bundle_root_sha256: str
    private_answer_bundle_sha256: str
    public_metadata_bundle_sha256: str


class BenchmarkOperationError(RuntimeError):
    """Operation failure retaining the strongest governed failure record possible."""

    def __init__(self, message: str, *, failure_record_path: str | None) -> None:
        super().__init__(message)
        self.failure_record_path = failure_record_path
