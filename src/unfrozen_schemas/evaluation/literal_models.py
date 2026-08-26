"""Strict M2.2 literal-benchmark records layered over the M2.1 lifecycle."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import Field, model_validator

from unfrozen_schemas.budgets import ResourceBudget
from unfrozen_schemas.config import FrozenModel
from unfrozen_schemas.envs.schema_world.actions import Action
from unfrozen_schemas.envs.schema_world.dynamics import TransitionTrace
from unfrozen_schemas.envs.schema_world.relations import RelationRecord
from unfrozen_schemas.envs.schema_world.state import BoundarySide, WorldState
from unfrozen_schemas.evaluation.benchmark_models import (
    HumanValidationMetadata,
    ProvenanceRights,
)
from unfrozen_schemas.provenance import ArtifactRecord, GitState, PlatformInformation

SHA256_PATTERN = r"^[a-f0-9]{64}$"
SLUG_PATTERN = r"^[a-z0-9][a-z0-9._-]*$"
LITERAL_CANDIDATE_VERSION = "m2-2-literal-candidate-v1"
LITERAL_GENERATOR_VERSION = "literal-generator-v1"
LITERAL_PARTITION_PLAN_VERSION = "literal-partition-plan-v1"


class LiteralSchema(StrEnum):
    CONTAINMENT = "CONTAINMENT"
    SUPPORT = "SUPPORT"


class LiteralTransferLevel(StrEnum):
    L1 = "L1"
    L2 = "L2"


class LiteralTaskFamily(StrEnum):
    DIRECT_OUTCOME = "direct-literal-outcome"
    INTERVENTION_CONSEQUENCE = "literal-intervention-consequence"
    MATCHED_COUNTERFACTUAL = "matched-counterfactual-reasoning"
    NOVEL_TEMPLATE = "novel-literal-template"
    NOVEL_CONFIGURATION = "novel-literal-configuration"
    PHYSICAL_ANALOGY = "literal-physical-mechanism-analogy"


class LiteralPartition(StrEnum):
    L1_HELD_OUT = "l1-held-out-literal"
    L2_NOVEL_TEMPLATE = "l2-novel-template"
    L2_NOVEL_CONFIGURATION = "l2-novel-configuration"
    L2_MECHANISM_TRANSFER = "l2-mechanism-transfer"


class ContainmentScenarioCase(StrEnum):
    FITTING_OPENING = "fitting-opening"
    CLOSED_BOUNDARY = "closed-boundary"
    UNDERSIZED_OPENING = "undersized-opening"
    MISALIGNED_OPENING = "misaligned-opening"
    FULLY_OPEN_BOUNDARY = "fully-open-boundary"


class SupportScenarioCase(StrEnum):
    LOWER_SUPPORT_REMOVAL = "lower-support-removal"
    LOWER_SUPPORT_NOOP = "lower-support-noop"
    SIDE_CONTACT = "side-contact"
    TETHER_CUT = "tether-cut"
    TETHERED_PLATFORM_REMOVAL = "tethered-platform-removal"
    NONBEARING_TETHER = "nonbearing-tether"


class LiteralDirection(StrEnum):
    ENTRY = "entry"
    EXIT = "exit"


class LiteralTemplate(FrozenModel):
    template_id: str = Field(pattern=SLUG_PATTERN)
    task_family: LiteralTaskFamily
    transfer_level: LiteralTransferLevel
    prompt_format: str = Field(min_length=1)
    instructions: str = Field(min_length=1)


class LiteralScenarioSpec(FrozenModel):
    semantic_group_id: str = Field(pattern=SLUG_PATTERN)
    schema_identity: LiteralSchema
    transfer_level: LiteralTransferLevel
    task_family: LiteralTaskFamily
    partition: LiteralPartition
    source_mechanism_family: str = Field(pattern=SLUG_PATTERN)
    prompt_template_id: str = Field(pattern=SLUG_PATTERN)
    scenario_case: ContainmentScenarioCase | SupportScenarioCase
    side: BoundarySide | None = None
    direction: LiteralDirection | None = None
    seed: int = Field(ge=0, le=4_294_967_295)
    noise_seed: int = Field(ge=0, le=4_294_967_295)
    include_distractor: bool = False
    scene_description: str = Field(min_length=1)
    actual_action_description: str = Field(min_length=1)
    counterfactual_action_description: str = Field(min_length=1)
    positive_option_text: str = Field(min_length=1)
    negative_option_text: str = Field(min_length=1)
    action_word: str = Field(min_length=1, pattern=r"^[a-z][a-z-]*$")
    declared_causal_factor: str = Field(min_length=1)
    declared_non_target_equality_fields: tuple[str, ...] = Field(min_length=1)
    structural_novelty_dimensions: tuple[str, ...]
    lexical_cue_annotations: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_schema_case_and_level(self) -> LiteralScenarioSpec:
        if self.schema_identity is LiteralSchema.CONTAINMENT:
            if not isinstance(self.scenario_case, ContainmentScenarioCase):
                raise ValueError("CONTAINMENT scenarios require a containment scenario case")
            if self.side is None or self.direction is None:
                raise ValueError("CONTAINMENT scenarios require side and entry/exit direction")
        else:
            if not isinstance(self.scenario_case, SupportScenarioCase):
                raise ValueError("SUPPORT scenarios require a support scenario case")
            if self.side is not None or self.direction is not None:
                raise ValueError("SUPPORT scenarios cannot declare containment geometry fields")
        if self.transfer_level is LiteralTransferLevel.L1:
            if self.partition is not LiteralPartition.L1_HELD_OUT:
                raise ValueError("L1 literal groups must use the held-out literal partition")
        elif self.partition is LiteralPartition.L1_HELD_OUT:
            raise ValueError("L2 literal groups cannot use the L1 partition")
        if self.transfer_level is LiteralTransferLevel.L2:
            if not self.structural_novelty_dimensions:
                raise ValueError("L2 groups require structural novelty beyond a new seed")
            if set(self.structural_novelty_dimensions) <= {"entity-name-only", "new-seed-only"}:
                raise ValueError("A new name or seed alone cannot establish L2 transfer")
        if len(self.lexical_cue_annotations) != len(set(self.lexical_cue_annotations)):
            raise ValueError("Lexical-cue annotations must be unique")
        return self


class LiteralAuthoringManifest(FrozenModel):
    schema_version: Literal["1"] = "1"
    authoring_kind: Literal["private_literal_authoring"] = "private_literal_authoring"
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    purpose: Literal["outcome", "engineering"]
    environment_version: Literal["schemaworld-core-v1"] = "schemaworld-core-v1"
    generator_version: Literal["literal-generator-v1"] = "literal-generator-v1"
    partition_plan_version: Literal["literal-partition-plan-v1"] = "literal-partition-plan-v1"
    engineering_only: bool
    scientific_eligible: bool
    promotable: bool
    templates: tuple[LiteralTemplate, ...] = Field(min_length=1)
    scenarios: tuple[LiteralScenarioSpec, ...] = Field(min_length=1)
    prospective_adaptation_strata: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_authoring_identity(self) -> LiteralAuthoringManifest:
        if self.purpose == "engineering":
            if not self.engineering_only or self.scientific_eligible or self.promotable:
                raise ValueError("Engineering literal authoring must be non-scientific")
        elif self.engineering_only:
            raise ValueError("Outcome authoring cannot be marked engineering-only")
        template_ids = tuple(item.template_id for item in self.templates)
        group_ids = tuple(item.semantic_group_id for item in self.scenarios)
        if len(template_ids) != len(set(template_ids)):
            raise ValueError("Literal prompt-template IDs must be unique")
        if len(group_ids) != len(set(group_ids)):
            raise ValueError("Literal semantic-group IDs must be unique")
        template_by_id = {item.template_id: item for item in self.templates}
        for scenario in self.scenarios:
            template = template_by_id.get(scenario.prompt_template_id)
            if template is None:
                raise ValueError(
                    f"Scenario references an unknown prompt template: {scenario.prompt_template_id}"
                )
            if (
                template.task_family is not scenario.task_family
                or template.transfer_level is not scenario.transfer_level
            ):
                raise ValueError("Scenario and prompt-template classifications must agree")
        return self


class LiteralPartitionPlan(FrozenModel):
    schema_version: Literal["1"] = "1"
    plan_kind: Literal["literal_partition_plan"] = "literal_partition_plan"
    plan_version: Literal["literal-partition-plan-v1"] = "literal-partition-plan-v1"
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    prospective_adaptation_strata: tuple[str, ...]
    l1_held_out_group_ids: tuple[str, ...]
    l2_novel_template_group_ids: tuple[str, ...]
    l2_novel_configuration_group_ids: tuple[str, ...]
    l2_mechanism_transfer_group_ids: tuple[str, ...]
    benchmark_reserved_prompt_template_ids: tuple[str, ...]
    benchmark_reserved_semantic_group_ids: tuple[str, ...]
    future_treatment_overlap_status: Literal["not_assessed_m2_2"] = "not_assessed_m2_2"
    partition_plan_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_partition_sets(self) -> LiteralPartitionPlan:
        group_sets = (
            set(self.l1_held_out_group_ids),
            set(self.l2_novel_template_group_ids),
            set(self.l2_novel_configuration_group_ids),
            set(self.l2_mechanism_transfer_group_ids),
        )
        combined: set[str] = set()
        for values in group_sets:
            if combined & values:
                raise ValueError("Literal partition group memberships must be disjoint")
            combined |= values
        if combined != set(self.benchmark_reserved_semantic_group_ids):
            raise ValueError("Reserved semantic-group IDs must equal all evaluation groups")
        adaptation = set(self.prospective_adaptation_strata)
        if adaptation & set(self.benchmark_reserved_semantic_group_ids):
            raise ValueError("Prospective adaptation and benchmark group IDs must be disjoint")
        if adaptation & set(self.benchmark_reserved_prompt_template_ids):
            raise ValueError("Prospective adaptation and prompt-template IDs must be disjoint")
        for field_name in (
            "prospective_adaptation_strata",
            "l1_held_out_group_ids",
            "l2_novel_template_group_ids",
            "l2_novel_configuration_group_ids",
            "l2_mechanism_transfer_group_ids",
            "benchmark_reserved_prompt_template_ids",
            "benchmark_reserved_semantic_group_ids",
        ):
            values = getattr(self, field_name)
            if tuple(sorted(values)) != values or len(values) != len(set(values)):
                raise ValueError(f"{field_name} must be sorted and unique")
        return self


class LiteralTemplateRegistryManifest(FrozenModel):
    schema_version: Literal["1"] = "1"
    registry_kind: Literal["private_literal_template_registry"] = (
        "private_literal_template_registry"
    )
    registry_version: Literal["literal-template-registry-v1"] = "literal-template-registry-v1"
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    template_ids: tuple[str, ...]
    template_content_hashes: dict[str, str]
    template_registry_sha256: str = Field(pattern=SHA256_PATTERN)


class LiteralWitnessRecord(FrozenModel):
    schema_version: Literal["1"] = "1"
    semantic_group_id: str = Field(pattern=SLUG_PATTERN)
    item_ids: tuple[str, str]
    schema_identity: LiteralSchema
    transfer_level: LiteralTransferLevel
    task_family: LiteralTaskFamily
    source_mechanism_family: str = Field(pattern=SLUG_PATTERN)
    prompt_template_id: str = Field(pattern=SLUG_PATTERN)
    partition: LiteralPartition
    environment_version: Literal["schemaworld-core-v1"] = "schemaworld-core-v1"
    generator_version: Literal["literal-generator-v1"] = "literal-generator-v1"
    seed: int
    noise_seed: int
    initial_privileged_state: WorldState
    counterfactual_initial_privileged_state: WorldState
    initial_state_hash: str = Field(pattern=SHA256_PATTERN)
    counterfactual_initial_state_hash: str = Field(pattern=SHA256_PATTERN)
    initial_observation_hash: str = Field(pattern=SHA256_PATTERN)
    counterfactual_initial_observation_hash: str = Field(pattern=SHA256_PATTERN)
    actual_actions: tuple[Action, ...] = Field(min_length=1)
    counterfactual_actions: tuple[Action, ...] = Field(min_length=1)
    action_sequence_hash: str = Field(pattern=SHA256_PATTERN)
    counterfactual_action_sequence_hash: str = Field(pattern=SHA256_PATTERN)
    actual_final_state: WorldState
    counterfactual_final_state: WorldState
    actual_transition_traces: tuple[TransitionTrace, ...]
    counterfactual_transition_traces: tuple[TransitionTrace, ...]
    actual_transition_hashes: tuple[str, ...]
    counterfactual_transition_hashes: tuple[str, ...]
    actual_relations: tuple[RelationRecord, ...]
    counterfactual_relations: tuple[RelationRecord, ...]
    declared_causal_factor: str
    declared_non_target_equality_fields: tuple[str, ...]
    declared_initial_difference_paths: tuple[str, ...]
    declared_action_difference_paths: tuple[str, ...]
    actual_outcome_code: str = Field(pattern=SLUG_PATTERN)
    counterfactual_outcome_code: str = Field(pattern=SLUG_PATTERN)
    stable_correct_option_id: str = Field(pattern=SLUG_PATTERN)
    witness_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_counterfactual_shape(self) -> LiteralWitnessRecord:
        if len(self.actual_actions) != len(self.counterfactual_actions):
            raise ValueError("Actual and counterfactual plans require equal horizons")
        if self.actual_outcome_code == self.counterfactual_outcome_code:
            raise ValueError("A counterfactual witness must change the declared outcome")
        if tuple(sorted(self.item_ids)) != self.item_ids or len(set(self.item_ids)) != 2:
            raise ValueError("Witness item IDs must be two unique sorted reverse variants")
        return self


class LiteralWitnessBundle(FrozenModel):
    schema_version: Literal["1"] = "1"
    bundle_kind: Literal["literal_witness_bundle"] = "literal_witness_bundle"
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    witnesses: tuple[LiteralWitnessRecord, ...]
    witness_bundle_sha256: str = Field(pattern=SHA256_PATTERN)


class LiteralItemBinding(FrozenModel):
    schema_version: Literal["1"] = "1"
    semantic_group_id: str = Field(pattern=SLUG_PATTERN)
    item_ids: tuple[str, str]
    variant_ids: tuple[str, str]
    option_permutations: tuple[tuple[str, ...], tuple[str, ...]]
    schema_identity: LiteralSchema
    transfer_level: LiteralTransferLevel
    task_family: LiteralTaskFamily
    source_mechanism_family: str = Field(pattern=SLUG_PATTERN)
    prompt_template_id: str = Field(pattern=SLUG_PATTERN)
    partition: LiteralPartition
    scenario_case: str = Field(pattern=SLUG_PATTERN)
    action_word: str = Field(pattern=r"^[a-z][a-z-]*$")
    counterfactual_group_id: str = Field(pattern=SLUG_PATTERN)
    structural_novelty_dimensions: tuple[str, ...]
    stable_correct_option_id: str = Field(pattern=SLUG_PATTERN)
    witness_sha256: str = Field(pattern=SHA256_PATTERN)
    reversal_transformation: Literal["reversed option presentation"] = (
        "reversed option presentation"
    )
    item_binding_sha256: str = Field(pattern=SHA256_PATTERN)


class LiteralItemBindingBundle(FrozenModel):
    schema_version: Literal["1"] = "1"
    bundle_kind: Literal["literal_item_binding_bundle"] = "literal_item_binding_bundle"
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    bindings: tuple[LiteralItemBinding, ...]
    item_binding_bundle_sha256: str = Field(pattern=SHA256_PATTERN)


class LiteralLexicalFinding(FrozenModel):
    finding_kind: str = Field(pattern=SLUG_PATTERN)
    scope: str = Field(min_length=1)
    value: str = Field(min_length=1)
    disposition: Literal["pass", "reviewed-causal", "fail"]


class LiteralLexicalAudit(FrozenModel):
    schema_version: Literal["1"] = "1"
    audit_kind: Literal["literal_lexical_cue_audit"] = "literal_lexical_cue_audit"
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    semantic_group_count: int
    source_item_count: int
    answer_position_counts: dict[str, int]
    template_answer_counts: dict[str, dict[str, int]]
    action_word_answer_counts: dict[str, dict[str, int]]
    source_mechanism_answer_counts: dict[str, dict[str, int]]
    exact_duplicate_group_count: int
    near_duplicate_group_pairs: tuple[tuple[str, str], ...]
    findings: tuple[LiteralLexicalFinding, ...]
    external_language_overlap_status: Literal["not_assessed_m2_2"] = "not_assessed_m2_2"
    status: Literal["PASS"] = "PASS"
    lexical_audit_sha256: str = Field(pattern=SHA256_PATTERN)


class LiteralSplitAudit(FrozenModel):
    schema_version: Literal["1"] = "1"
    audit_kind: Literal["literal_split_audit"] = "literal_split_audit"
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    semantic_group_count: int
    l1_group_count: int
    l2_group_count: int
    unique_state_hash_count: int
    unique_action_hash_count: int
    unique_witness_hash_count: int
    l2_structural_novelty_dimensions: dict[str, tuple[str, ...]]
    exact_prompt_duplicate_count: int
    future_treatment_overlap_status: Literal["not_assessed_m2_2"] = "not_assessed_m2_2"
    status: Literal["PASS"] = "PASS"
    split_audit_sha256: str = Field(pattern=SHA256_PATTERN)


class LiteralValidationReport(FrozenModel):
    schema_version: Literal["1"] = "1"
    report_kind: Literal["literal_validation_report"] = "literal_validation_report"
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    purpose: Literal["outcome", "engineering"]
    semantic_group_count: int
    source_item_count: int
    schema_counts: dict[str, int]
    level_counts: dict[str, int]
    family_counts: dict[str, int]
    mechanism_counts: dict[str, int]
    simulator_correctness: Literal["PASS"] = "PASS"
    counterfactual_parity: Literal["PASS"] = "PASS"
    split_integrity: Literal["PASS"] = "PASS"
    reverse_equivalence: Literal["PASS"] = "PASS"
    lexical_cue_audit: Literal["PASS"] = "PASS"
    prompt_option_balance: Literal["PASS"] = "PASS"
    provenance_integrity: Literal["PASS"] = "PASS"
    m2_1_lifecycle_validation: Literal["PASS", "not_evaluated_source_stage"]
    future_treatment_overlap_status: Literal["not_assessed_m2_2"] = "not_assessed_m2_2"
    human_validation_status: Literal["not_started", "not_applicable_engineering"] = "not_started"
    rights_status: Literal["unresolved", "not_applicable_engineering"] = "unresolved"
    ethics_governance_status: Literal["unresolved", "not_applicable_engineering"] = "unresolved"
    freeze_eligibility: Literal[False] = False
    overall_status: Literal["CANDIDATE_VALIDATED_OWNER_REVIEW_PENDING"] = (
        "CANDIDATE_VALIDATED_OWNER_REVIEW_PENDING"
    )
    literal_validation_report_sha256: str = Field(pattern=SHA256_PATTERN)


class LiteralSourceBundleManifest(FrozenModel):
    schema_version: Literal["1"] = "1"
    manifest_kind: Literal["literal_source_bundle"] = "literal_source_bundle"
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    purpose: Literal["outcome", "engineering"]
    authoring_manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    m2_1_source_manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    m2_1_items_file_sha256: str = Field(pattern=SHA256_PATTERN)
    partition_plan_sha256: str = Field(pattern=SHA256_PATTERN)
    template_registry_sha256: str = Field(pattern=SHA256_PATTERN)
    item_binding_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    witness_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    split_audit_sha256: str = Field(pattern=SHA256_PATTERN)
    lexical_audit_sha256: str = Field(pattern=SHA256_PATTERN)
    literal_validation_report_sha256: str = Field(pattern=SHA256_PATTERN)
    generation_operation_sha256: str = Field(pattern=SHA256_PATTERN)
    artifacts: tuple[ArtifactRecord, ...]
    literal_source_bundle_sha256: str = Field(pattern=SHA256_PATTERN)


class LiteralCandidateManifest(FrozenModel):
    schema_version: Literal["1"] = "1"
    manifest_kind: Literal["literal_private_candidate"] = "literal_private_candidate"
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    purpose: Literal["outcome", "engineering"]
    git: GitState
    codex_spec_sha256: str = Field(pattern=SHA256_PATTERN)
    m2_1_candidate_manifest_file_sha256: str = Field(pattern=SHA256_PATTERN)
    m2_1_candidate_bundle_root_sha256: str = Field(pattern=SHA256_PATTERN)
    m2_1_source_snapshot_sha256: str = Field(pattern=SHA256_PATTERN)
    m2_1_private_answer_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    m2_1_public_metadata_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    m2_1_quarantine_scope_sha256: str = Field(pattern=SHA256_PATTERN)
    literal_source_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    partition_plan_sha256: str = Field(pattern=SHA256_PATTERN)
    template_registry_sha256: str = Field(pattern=SHA256_PATTERN)
    item_binding_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    witness_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    split_audit_sha256: str = Field(pattern=SHA256_PATTERN)
    lexical_audit_sha256: str = Field(pattern=SHA256_PATTERN)
    literal_validation_report_sha256: str = Field(pattern=SHA256_PATTERN)
    review_content_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    semantic_group_count: int
    source_item_count: int
    literal_candidate_root_sha256: str = Field(pattern=SHA256_PATTERN)


class LiteralReviewItem(FrozenModel):
    schema_version: Literal["1"] = "1"
    semantic_group_id: str = Field(pattern=SLUG_PATTERN)
    item_ids: tuple[str, str]
    schema_identity: LiteralSchema
    transfer_level: LiteralTransferLevel
    task_family: LiteralTaskFamily
    prompt: str
    option_forms: tuple[tuple[dict[str, str], ...], tuple[dict[str, str], ...]]
    stable_correct_option_id: str
    simulator_rationale: str
    actual_outcome_code: str
    counterfactual_outcome_code: str
    causal_factor: str
    lexical_cue_annotations: tuple[str, ...]
    provenance: ProvenanceRights
    human_validation: HumanValidationMetadata
    human_validation_status: Literal["not_started", "not_applicable_engineering"] = "not_started"
    before_render_path: str
    after_render_path: str
    witness_sha256: str = Field(pattern=SHA256_PATTERN)
    item_binding_sha256: str = Field(pattern=SHA256_PATTERN)


class LiteralPendingOwnerReview(FrozenModel):
    schema_version: Literal["1"] = "1"
    record_kind: Literal["literal_pending_owner_review"] = "literal_pending_owner_review"
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    status: Literal["PENDING"] = "PENDING"
    owner_decision_recorded: Literal[False] = False
    substitutes_for_human_validation: Literal[False] = False
    required_owner_bindings: tuple[
        Literal[
            "pull_request_number",
            "pull_request_head_sha",
            "m2_1_candidate_manifest_file_sha256",
            "m2_1_candidate_bundle_root_sha256",
            "literal_candidate_root_sha256",
            "m2_1_source_snapshot_sha256",
            "witness_bundle_sha256",
            "literal_validation_report_sha256",
            "review_manifest_sha256",
        ],
        ...,
    ]

    @model_validator(mode="after")
    def validate_binding_set(self) -> LiteralPendingOwnerReview:
        if tuple(sorted(self.required_owner_bindings)) != self.required_owner_bindings:
            raise ValueError("Pending owner-review bindings must use sorted ordering")
        if len(self.required_owner_bindings) != len(set(self.required_owner_bindings)):
            raise ValueError("Pending owner-review bindings must be unique")
        return self


class LiteralReviewManifest(FrozenModel):
    schema_version: Literal["1"] = "1"
    manifest_kind: Literal["literal_private_review_bundle"] = "literal_private_review_bundle"
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    literal_candidate_root_sha256: str = Field(pattern=SHA256_PATTERN)
    witness_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    literal_validation_report_sha256: str = Field(pattern=SHA256_PATTERN)
    review_content_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    artifacts: tuple[ArtifactRecord, ...]
    review_manifest_sha256: str = Field(pattern=SHA256_PATTERN)


class LiteralOperationRecord(FrozenModel):
    schema_version: Literal["1"] = "1"
    record_kind: Literal["literal_operation"] = "literal_operation"
    operation_id: str
    operation_kind: Literal[
        "generate_literal_source", "validate_literal_source", "build_literal_review"
    ]
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    purpose: Literal["outcome", "engineering"]
    engineering_only: bool
    scientific_result: Literal[False] = False
    git: GitState
    codex_spec_sha256: str = Field(pattern=SHA256_PATTERN)
    environment_version: Literal["schemaworld-core-v1"] = "schemaworld-core-v1"
    generator_version: Literal["literal-generator-v1"] = "literal-generator-v1"
    resolved_configuration: dict[str, Any]
    input_hashes: dict[str, str]
    output_hashes: dict[str, str]
    item_count: int
    semantic_group_count: int
    schema_counts: dict[str, int]
    level_counts: dict[str, int]
    family_counts: dict[str, int]
    status: Literal["COMPLETED", "FAILED"]
    failure_reason: str | None
    package_versions: dict[str, str]
    platform: PlatformInformation
    started_at: datetime
    ended_at: datetime
    artifacts: tuple[ArtifactRecord, ...]
    resource_budget: ResourceBudget
    operation_sha256: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_operation(self) -> LiteralOperationRecord:
        if self.ended_at < self.started_at:
            raise ValueError("Literal operation end precedes its start")
        if self.resource_budget.run_id != self.operation_id:
            raise ValueError("Literal operation and ResourceBudget IDs must match")
        if self.resource_budget.interval_start != self.started_at:
            raise ValueError("Literal operation and ResourceBudget must start together")
        if self.resource_budget.interval_end != self.ended_at:
            raise ValueError("Literal operation and ResourceBudget must end together")
        if self.status == "FAILED" and not self.failure_reason:
            raise ValueError("Failed literal operations require the original failure reason")
        if self.status == "COMPLETED" and self.failure_reason is not None:
            raise ValueError("Completed literal operations cannot contain a failure reason")
        return self


class LiteralOperationResult(FrozenModel):
    operation_id: str
    dry_run: bool
    candidate_version: str
    purpose: Literal["outcome", "engineering"]
    source_path: str | None
    review_path: str | None = None
    semantic_group_count: int
    source_item_count: int
    partition_plan_sha256: str = Field(pattern=SHA256_PATTERN)
    template_registry_sha256: str = Field(pattern=SHA256_PATTERN)
    witness_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    literal_validation_report_sha256: str = Field(pattern=SHA256_PATTERN)
    literal_candidate_root_sha256: str | None = Field(default=None, pattern=SHA256_PATTERN)
    review_manifest_sha256: str | None = Field(default=None, pattern=SHA256_PATTERN)


class LiteralOperationError(RuntimeError):
    """Failure preserving the original cause and best available local artifact."""

    def __init__(self, message: str, *, failure_record_path: str | None = None) -> None:
        super().__init__(message)
        self.failure_record_path = failure_record_path
