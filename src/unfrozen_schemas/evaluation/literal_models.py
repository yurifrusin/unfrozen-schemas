"""Strict M2.2 literal-benchmark records layered over the M2.1 lifecycle."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import Field, model_validator

from unfrozen_schemas.budgets import ResourceBudget
from unfrozen_schemas.config import FrozenModel
from unfrozen_schemas.envs.schema_world.actions import Action, ActionKind
from unfrozen_schemas.envs.schema_world.dynamics import TransitionTrace
from unfrozen_schemas.envs.schema_world.relations import RelationRecord
from unfrozen_schemas.envs.schema_world.state import BoundarySide, WorldState
from unfrozen_schemas.evaluation.benchmark_models import HumanValidationMetadata, ProvenanceRights
from unfrozen_schemas.provenance import ArtifactRecord, GitState, PlatformInformation

SHA256_PATTERN = r"^[a-f0-9]{64}$"
SLUG_PATTERN = r"^[a-z0-9][a-z0-9._-]*$"
DISPLAY_NAME_PATTERN = r"^[A-Za-z][A-Za-z '-]{0,39}$"
LITERAL_CANDIDATE_VERSION = "m2-2-literal-candidate-v1"
LITERAL_GENERATOR_VERSION = "literal-generator-v3"
LITERAL_PARTITION_PLAN_VERSION = "literal-partition-plan-v3"
LITERAL_OUTCOME_TEXT_REGISTRY_VERSION = "literal-outcome-text-registry-v2"
LITERAL_STRUCTURAL_SIGNATURE_VERSION = "literal-structural-signatures-v3"
LITERAL_MECHANISM_KIND_VERSION = "literal-mechanism-kind-v1"
LITERAL_INTERVENTION_CONTRACT_VERSION = "literal-intervention-contract-v1"
LITERAL_CAUSAL_ALLOWLIST_VERSION = "literal-causal-term-allowlist-v2"
LITERAL_LEXICAL_CATEGORY_VERSION = "literal-lexical-category-v2"


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


LiteralScenarioCase = ContainmentScenarioCase | SupportScenarioCase


class LiteralDirection(StrEnum):
    ENTRY = "entry"
    EXIT = "exit"


class LiteralOutcomeCode(StrEnum):
    MOVEMENT_SUCCEEDS = "movement-succeeds"
    MOVEMENT_BLOCKED = "movement-blocked"
    OBJECT_FALLS = "object-falls"
    OBJECT_STAYS = "object-stays"


class LiteralInterventionKind(StrEnum):
    OPENING_ENABLED_STATE = "opening-enabled-state"
    OPENING_SPAN = "opening-span"
    OPENING_ALIGNMENT = "opening-alignment"
    BOUNDARY_CLOSURE = "boundary-closure"
    LOWER_SUPPORT_ACTION = "lower-support-action"
    SUPPORT_CONTACT_GEOMETRY = "support-contact-geometry"
    TETHER_CUT_ACTION = "tether-cut-action"
    TETHER_ACTION_CHOICE = "tether-action-choice"
    TETHER_LOAD_BEARING = "tether-load-bearing"


class LiteralCausalFactor(StrEnum):
    APERTURE_AVAILABILITY = "aperture-availability"
    APERTURE_SIZE = "aperture-size"
    APERTURE_ALIGNMENT = "aperture-alignment"
    PERIMETER_CLOSURE = "perimeter-closure"
    LOWER_CONTACT_REMOVAL = "lower-contact-removal"
    LOWER_CONTACT_GEOMETRY = "lower-contact-geometry"
    TETHER_CONTINUITY = "tether-continuity"
    LOAD_BEARING_MECHANISM = "load-bearing-mechanism"
    TETHER_LOAD_BEARING = "tether-load-bearing"


class LiteralMechanismKind(StrEnum):
    FITTING_APERTURE = "fitting-aperture"
    DISABLED_APERTURE = "disabled-aperture"
    UNDERSIZED_APERTURE = "undersized-aperture"
    MISALIGNED_APERTURE = "misaligned-aperture"
    OPEN_PERIMETER = "open-perimeter"
    CLOSED_PERIMETER = "closed-perimeter"
    LOWER_CONTACT = "lower-contact"
    SIDE_CONTACT = "side-contact"
    LOAD_BEARING_TETHER = "load-bearing-tether"
    NONBEARING_TETHER = "nonbearing-tether"


class StructuralNoveltyDimension(StrEnum):
    WORLD_TOPOLOGY = "world-topology"
    QUALITATIVE_GEOMETRY = "qualitative-geometry"
    ACTION_PLAN = "action-plan"
    COUNTERFACTUAL_INTERVENTION = "counterfactual-intervention"
    SOURCE_MECHANISM = "source-mechanism"
    PROMPT_TEMPLATE = "prompt-template"
    OBSERVATION_STRUCTURE = "observation-structure"


class LiteralAuditStatus(StrEnum):
    PASS = "PASS"
    OWNER_REVIEW_REQUIRED = "OWNER_REVIEW_REQUIRED"
    FAIL = "FAIL"


class LiteralLexicalCategory(StrEnum):
    NECESSARY_CAUSAL_CONDITION_VOCABULARY = "necessary-causal-condition-vocabulary"
    PHYSICAL_MECHANISM_CORRELATION = "physical-mechanism-correlation"
    NUISANCE_DIRECTION_ORIENTATION_VOCABULARY = "nuisance-direction-orientation-vocabulary"
    RENDERER_GRAMMATICAL_CONSTRUCTION_CUE = "renderer-grammatical-construction-cue"
    AUDIT_BOUNDARY_ARTIFACT = "audit-boundary-artifact"
    TASK_META_VOCABULARY = "task-meta-vocabulary"
    NUISANCE_IDENTIFIER_VOCABULARY = "nuisance-identifier-vocabulary"
    DUPLICATE_MATCHED_WORDING = "duplicate-or-matched-wording"


class LiteralTemplate(FrozenModel):
    template_id: str = Field(pattern=SLUG_PATTERN)
    task_family: LiteralTaskFamily
    transfer_level: LiteralTransferLevel
    renderer_version: Literal["literal-typed-narrative-renderer-v3"] = (
        "literal-typed-narrative-renderer-v3"
    )
    instruction_kind: Literal["choose-one-literal-outcome"] = "choose-one-literal-outcome"
    vocabulary_mode: Literal["literal_physics", "engineering_fixture"] = "literal_physics"


class LiteralOutcomeText(FrozenModel):
    text_id: str = Field(pattern=SLUG_PATTERN)
    outcome_code: LiteralOutcomeCode
    text: str = Field(min_length=1)


class LiteralScenarioSpec(FrozenModel):
    semantic_group_id: str = Field(pattern=SLUG_PATTERN)
    schema_identity: LiteralSchema
    transfer_level: LiteralTransferLevel
    task_family: LiteralTaskFamily
    partition: LiteralPartition
    prompt_template_id: str = Field(pattern=SLUG_PATTERN)
    scenario_case: LiteralScenarioCase
    side: BoundarySide | None = None
    direction: LiteralDirection | None = None
    intervention_kind: LiteralInterventionKind
    seed: int = Field(ge=0, le=4_294_967_295)
    noise_seed: int = Field(ge=0, le=4_294_967_295)
    include_distractor: bool = False
    scene_name: str = Field(pattern=DISPLAY_NAME_PATTERN)
    outcome_text_record_ids: tuple[str, str]
    structural_novelty_dimensions: tuple[StructuralNoveltyDimension, ...]
    matched_stratum_id: str | None = Field(default=None, pattern=SLUG_PATTERN)
    analogy_reference_group_id: str | None = Field(default=None, pattern=SLUG_PATTERN)
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
            if self.structural_novelty_dimensions:
                raise ValueError("L1 groups cannot claim L2 structural novelty")
        elif self.partition is LiteralPartition.L1_HELD_OUT:
            raise ValueError("L2 literal groups cannot use the L1 partition")
        if self.transfer_level is LiteralTransferLevel.L2:
            if not self.structural_novelty_dimensions:
                raise ValueError("L2 groups require typed structural novelty evidence")
            if self.partition is LiteralPartition.L2_NOVEL_TEMPLATE and set(
                self.structural_novelty_dimensions
            ) != {StructuralNoveltyDimension.PROMPT_TEMPLATE}:
                raise ValueError("Novel-template L2 groups must use prompt-template novelty")
            if self.partition is LiteralPartition.L2_NOVEL_CONFIGURATION and not set(
                self.structural_novelty_dimensions
            ) & {
                StructuralNoveltyDimension.WORLD_TOPOLOGY,
                StructuralNoveltyDimension.QUALITATIVE_GEOMETRY,
                StructuralNoveltyDimension.OBSERVATION_STRUCTURE,
            }:
                raise ValueError("Novel-configuration L2 groups require structural geometry")
            if self.partition is LiteralPartition.L2_MECHANISM_TRANSFER and (
                StructuralNoveltyDimension.SOURCE_MECHANISM
                not in self.structural_novelty_dimensions
            ):
                raise ValueError("Mechanism-transfer L2 groups require source-mechanism novelty")
            expected_family = {
                LiteralPartition.L2_NOVEL_TEMPLATE: LiteralTaskFamily.NOVEL_TEMPLATE,
                LiteralPartition.L2_NOVEL_CONFIGURATION: LiteralTaskFamily.NOVEL_CONFIGURATION,
                LiteralPartition.L2_MECHANISM_TRANSFER: LiteralTaskFamily.PHYSICAL_ANALOGY,
            }[self.partition]
            if self.task_family is not expected_family:
                raise ValueError("Each L2 partition requires its matching scientific task family")
        if len(self.outcome_text_record_ids) != len(set(self.outcome_text_record_ids)):
            raise ValueError("Scenario outcome-text records must be distinct")
        if len(self.structural_novelty_dimensions) != len(set(self.structural_novelty_dimensions)):
            raise ValueError("Structural novelty dimensions must be unique")
        if len(self.lexical_cue_annotations) != len(set(self.lexical_cue_annotations)):
            raise ValueError("Lexical-cue annotations must be unique")
        if (self.task_family is LiteralTaskFamily.PHYSICAL_ANALOGY) != (
            self.analogy_reference_group_id is not None
        ):
            raise ValueError("Only physical-analogy groups require one L1 reference group")
        return self


class LiteralAuthoringManifest(FrozenModel):
    schema_version: Literal["4"] = "4"
    authoring_kind: Literal["private_literal_authoring"] = "private_literal_authoring"
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    purpose: Literal["outcome", "engineering"]
    environment_version: Literal["schemaworld-core-v1"] = "schemaworld-core-v1"
    generator_version: Literal["literal-generator-v3"] = "literal-generator-v3"
    partition_plan_version: Literal["literal-partition-plan-v3"] = "literal-partition-plan-v3"
    outcome_text_registry_version: Literal["literal-outcome-text-registry-v2"] = (
        "literal-outcome-text-registry-v2"
    )
    engineering_only: bool
    scientific_eligible: bool
    promotable: bool
    templates: tuple[LiteralTemplate, ...] = Field(min_length=1)
    outcome_text_registry: tuple[LiteralOutcomeText, ...] = Field(min_length=4)
    scenarios: tuple[LiteralScenarioSpec, ...] = Field(min_length=1)
    prospective_adaptation_strata: tuple[str, ...] = Field(min_length=1)
    prospective_adaptation_source_mechanism_signatures: tuple[str, ...] = Field(min_length=1)
    prospective_adaptation_source_mechanism_kind_signatures: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_authoring_identity(self) -> LiteralAuthoringManifest:
        if self.purpose == "engineering":
            if not self.engineering_only or self.scientific_eligible or self.promotable:
                raise ValueError("Engineering literal authoring must be non-scientific")
        elif self.engineering_only:
            raise ValueError("Outcome authoring cannot be marked engineering-only")
        template_ids = tuple(item.template_id for item in self.templates)
        group_ids = tuple(item.semantic_group_id for item in self.scenarios)
        text_ids = tuple(item.text_id for item in self.outcome_text_registry)
        if len(template_ids) != len(set(template_ids)):
            raise ValueError("Literal prompt-template IDs must be unique")
        if len(group_ids) != len(set(group_ids)):
            raise ValueError("Literal semantic-group IDs must be unique")
        if len(text_ids) != len(set(text_ids)):
            raise ValueError("Literal outcome-text IDs must be unique")
        for field_name in (
            "prospective_adaptation_source_mechanism_signatures",
            "prospective_adaptation_source_mechanism_kind_signatures",
        ):
            prospective_signatures = getattr(self, field_name)
            if tuple(sorted(prospective_signatures)) != prospective_signatures or len(
                prospective_signatures
            ) != len(set(prospective_signatures)):
                raise ValueError(f"{field_name} must be sorted and unique")
        normalised_texts: set[str] = set()
        for record in self.outcome_text_registry:
            text = " ".join(record.text.split()).casefold()
            if text in normalised_texts:
                raise ValueError("Literal outcome wording records must have unique text")
            normalised_texts.add(text)
        if set(record.outcome_code for record in self.outcome_text_registry) != set(
            LiteralOutcomeCode
        ):
            raise ValueError("Outcome-text registry must cover all four literal outcomes")
        template_by_id = {item.template_id: item for item in self.templates}
        text_by_id = {item.text_id: item for item in self.outcome_text_registry}
        scene_names: set[str] = set()
        referenced_template_ids: set[str] = set()
        referenced_text_ids: set[str] = set()
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
            referenced_template_ids.add(scenario.prompt_template_id)
            referenced_text_ids.update(scenario.outcome_text_record_ids)
            try:
                selected = tuple(text_by_id[item] for item in scenario.outcome_text_record_ids)
            except KeyError as exc:
                raise ValueError("Scenario references an unknown outcome-text record") from exc
            expected_codes = (
                {LiteralOutcomeCode.MOVEMENT_SUCCEEDS, LiteralOutcomeCode.MOVEMENT_BLOCKED}
                if scenario.schema_identity is LiteralSchema.CONTAINMENT
                else {LiteralOutcomeCode.OBJECT_FALLS, LiteralOutcomeCode.OBJECT_STAYS}
            )
            if {item.outcome_code for item in selected} != expected_codes:
                raise ValueError("Scenario outcome wording does not cover its two typed outcomes")
            scene_key = " ".join(scenario.scene_name.split()).casefold()
            if scene_key in scene_names:
                raise ValueError("Cosmetic scene names must be unique")
            scene_names.add(scene_key)
            if scenario.analogy_reference_group_id is not None:
                reference = next(
                    (
                        item
                        for item in self.scenarios
                        if item.semantic_group_id == scenario.analogy_reference_group_id
                    ),
                    None,
                )
                if (
                    reference is None
                    or reference.transfer_level is not LiteralTransferLevel.L1
                    or reference.schema_identity is not scenario.schema_identity
                ):
                    raise ValueError(
                        "Physical analogy must reference an L1 group of the same schema"
                    )
        if referenced_template_ids != set(template_ids):
            raise ValueError("Literal authoring cannot retain orphaned prompt templates")
        if referenced_text_ids != set(text_ids):
            raise ValueError("Literal authoring cannot retain orphaned outcome-text records")
        return self


class LiteralStructuralSignatures(FrozenModel):
    schema_version: Literal["3"] = "3"
    signature_version: Literal["literal-structural-signatures-v3"] = (
        "literal-structural-signatures-v3"
    )
    mechanism_kind_version: Literal["literal-mechanism-kind-v1"] = "literal-mechanism-kind-v1"
    world_topology_sha256: str = Field(pattern=SHA256_PATTERN)
    qualitative_geometry_sha256: str = Field(pattern=SHA256_PATTERN)
    action_plan_sha256: str = Field(pattern=SHA256_PATTERN)
    counterfactual_intervention_sha256: str = Field(pattern=SHA256_PATTERN)
    source_mechanism_sha256: str = Field(pattern=SHA256_PATTERN)
    target_mechanism_sha256: str = Field(pattern=SHA256_PATTERN)
    source_mechanism_kind_sha256: str = Field(pattern=SHA256_PATTERN)
    target_mechanism_kind_sha256: str = Field(pattern=SHA256_PATTERN)
    prompt_template_sha256: str = Field(pattern=SHA256_PATTERN)
    observation_structure_sha256: str = Field(pattern=SHA256_PATTERN)
    configuration_sha256: str = Field(pattern=SHA256_PATTERN)
    causal_scenario_sha256: str = Field(pattern=SHA256_PATTERN)
    structural_stratum_sha256: str = Field(pattern=SHA256_PATTERN)
    witness_configuration_sha256: str = Field(pattern=SHA256_PATTERN)


class LiteralInterventionContract(FrozenModel):
    schema_version: Literal["1"] = "1"
    contract_version: Literal["literal-intervention-contract-v1"] = (
        "literal-intervention-contract-v1"
    )
    scenario_case: LiteralScenarioCase
    intervention_kind: LiteralInterventionKind
    occurs_in: Literal["initial_state", "action"]
    allowed_initial_difference_paths: tuple[str, ...]
    allowed_action_difference_paths: tuple[str, ...]
    required_equal_scopes: tuple[str, ...]
    allowed_horizon: Literal[1] = 1
    causal_factor: LiteralCausalFactor
    expected_actual_outcome: LiteralOutcomeCode
    expected_counterfactual_outcome: LiteralOutcomeCode


class LiteralNarrativeFacts(FrozenModel):
    schema_version: Literal["3"] = "3"
    facts_kind: Literal["literal_narrative_facts"] = "literal_narrative_facts"
    schema_identity: LiteralSchema
    transfer_level: LiteralTransferLevel
    task_family: LiteralTaskFamily
    scenario_case: LiteralScenarioCase
    side: BoundarySide | None
    direction: LiteralDirection | None
    intervention_kind: LiteralInterventionKind
    source_mechanism: LiteralMechanismKind
    target_mechanism: LiteralMechanismKind
    actual_action_kind: ActionKind
    counterfactual_action_kind: ActionKind
    actual_scene_clause: str = Field(min_length=1)
    counterfactual_scene_clause: str = Field(min_length=1)
    actual_action_summary: str = Field(min_length=1)
    counterfactual_action_summary: str = Field(min_length=1)
    source_mapping_clause: str | None = None
    task_family_question: str = Field(min_length=1)
    instructions: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_control_question(self) -> LiteralNarrativeFacts:
        if self.task_family is not LiteralTaskFamily.INTERVENTION_CONSEQUENCE:
            return self
        control = self.actual_action_kind in {ActionKind.NOOP, ActionKind.WAIT}
        normalised = " ".join(self.task_family_question.casefold().split())
        if control:
            if normalised != "which outcome is observed under this unchanged control?":
                raise ValueError("NOOP/WAIT requires the unchanged-control question")
            if "intervention" in normalised or "caused" in normalised:
                raise ValueError("NOOP/WAIT cannot use intervention-causation wording")
        elif normalised != "which consequence is caused by the intervention?":
            raise ValueError("A real intervention requires the intervention-consequence question")
        return self


class LiteralPartitionPlan(FrozenModel):
    schema_version: Literal["4"] = "4"
    plan_kind: Literal["literal_partition_plan"] = "literal_partition_plan"
    plan_version: Literal["literal-partition-plan-v3"] = "literal-partition-plan-v3"
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    prospective_adaptation_strata: tuple[str, ...]
    l1_held_out_group_ids: tuple[str, ...]
    l2_novel_template_group_ids: tuple[str, ...]
    l2_novel_configuration_group_ids: tuple[str, ...]
    l2_mechanism_transfer_group_ids: tuple[str, ...]
    benchmark_reserved_prompt_template_ids: tuple[str, ...]
    benchmark_reserved_semantic_group_ids: tuple[str, ...]
    reserved_world_topology_signatures: tuple[str, ...]
    reserved_qualitative_geometry_signatures: tuple[str, ...]
    reserved_action_signatures: tuple[str, ...]
    reserved_counterfactual_signatures: tuple[str, ...]
    reserved_source_mechanism_signatures: tuple[str, ...]
    reserved_target_mechanism_signatures: tuple[str, ...]
    reserved_source_mechanism_kind_signatures: tuple[str, ...]
    reserved_target_mechanism_kind_signatures: tuple[str, ...]
    prohibited_l1_source_mechanism_signatures: tuple[str, ...]
    prospective_adaptation_source_mechanism_signatures: tuple[str, ...]
    prohibited_mechanism_transfer_target_signatures: tuple[str, ...]
    prohibited_l1_source_mechanism_kind_signatures: tuple[str, ...]
    prospective_adaptation_source_mechanism_kind_signatures: tuple[str, ...]
    prohibited_mechanism_transfer_target_kind_signatures: tuple[str, ...]
    reserved_observation_structure_signatures: tuple[str, ...]
    reserved_configuration_signatures: tuple[str, ...]
    reserved_causal_scenario_signatures: tuple[str, ...]
    reserved_structural_stratum_signatures: tuple[str, ...]
    reserved_witness_configuration_signatures: tuple[str, ...]
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
        prohibited = set(self.prohibited_l1_source_mechanism_signatures) | set(
            self.prospective_adaptation_source_mechanism_signatures
        )
        if prohibited != set(self.prohibited_mechanism_transfer_target_signatures):
            raise ValueError(
                "Prohibited transfer targets must equal complete L1 and adaptation-source sets"
            )
        prohibited_kinds = set(self.prohibited_l1_source_mechanism_kind_signatures) | set(
            self.prospective_adaptation_source_mechanism_kind_signatures
        )
        if prohibited_kinds != set(self.prohibited_mechanism_transfer_target_kind_signatures):
            raise ValueError(
                "Prohibited transfer target kinds must equal complete L1 and "
                "adaptation-source kind sets"
            )
        for field_name in (
            "prospective_adaptation_strata",
            "l1_held_out_group_ids",
            "l2_novel_template_group_ids",
            "l2_novel_configuration_group_ids",
            "l2_mechanism_transfer_group_ids",
            "benchmark_reserved_prompt_template_ids",
            "benchmark_reserved_semantic_group_ids",
            "reserved_world_topology_signatures",
            "reserved_qualitative_geometry_signatures",
            "reserved_action_signatures",
            "reserved_counterfactual_signatures",
            "reserved_source_mechanism_signatures",
            "reserved_target_mechanism_signatures",
            "reserved_source_mechanism_kind_signatures",
            "reserved_target_mechanism_kind_signatures",
            "prohibited_l1_source_mechanism_signatures",
            "prospective_adaptation_source_mechanism_signatures",
            "prohibited_mechanism_transfer_target_signatures",
            "prohibited_l1_source_mechanism_kind_signatures",
            "prospective_adaptation_source_mechanism_kind_signatures",
            "prohibited_mechanism_transfer_target_kind_signatures",
            "reserved_observation_structure_signatures",
            "reserved_configuration_signatures",
            "reserved_causal_scenario_signatures",
            "reserved_structural_stratum_signatures",
            "reserved_witness_configuration_signatures",
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
    schema_version: Literal["4"] = "4"
    semantic_group_id: str = Field(pattern=SLUG_PATTERN)
    item_ids: tuple[str, str]
    schema_identity: LiteralSchema
    transfer_level: LiteralTransferLevel
    task_family: LiteralTaskFamily
    source_mechanism: LiteralMechanismKind
    target_mechanism: LiteralMechanismKind
    prompt_template_id: str = Field(pattern=SLUG_PATTERN)
    partition: LiteralPartition
    scenario_case: LiteralScenarioCase
    intervention_kind: LiteralInterventionKind
    structural_novelty_dimensions: tuple[StructuralNoveltyDimension, ...]
    matched_stratum_id: str | None
    analogy_reference_group_id: str | None
    environment_version: Literal["schemaworld-core-v1"] = "schemaworld-core-v1"
    generator_version: Literal["literal-generator-v3"] = "literal-generator-v3"
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
    intervention_contract: LiteralInterventionContract
    observed_initial_difference_paths: tuple[str, ...]
    observed_action_difference_paths: tuple[str, ...]
    actual_outcome_code: LiteralOutcomeCode
    counterfactual_outcome_code: LiteralOutcomeCode
    stable_correct_option_id: str = Field(pattern=SLUG_PATTERN)
    structural_signatures: LiteralStructuralSignatures
    narrative_facts: LiteralNarrativeFacts
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
    schema_version: Literal["3"] = "3"
    bundle_kind: Literal["literal_witness_bundle"] = "literal_witness_bundle"
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    witnesses: tuple[LiteralWitnessRecord, ...]
    witness_bundle_sha256: str = Field(pattern=SHA256_PATTERN)


class LiteralItemBinding(FrozenModel):
    schema_version: Literal["4"] = "4"
    semantic_group_id: str = Field(pattern=SLUG_PATTERN)
    item_ids: tuple[str, str]
    variant_ids: tuple[str, str]
    option_permutations: tuple[tuple[str, ...], tuple[str, ...]]
    outcome_text_record_ids: tuple[str, str]
    schema_identity: LiteralSchema
    transfer_level: LiteralTransferLevel
    task_family: LiteralTaskFamily
    source_mechanism: LiteralMechanismKind
    target_mechanism: LiteralMechanismKind
    prompt_template_id: str = Field(pattern=SLUG_PATTERN)
    partition: LiteralPartition
    scenario_case: LiteralScenarioCase
    intervention_kind: LiteralInterventionKind
    action_word: str = Field(pattern=r"^[a-z][a-z-]*$")
    counterfactual_group_id: str = Field(pattern=SLUG_PATTERN)
    structural_novelty_dimensions: tuple[StructuralNoveltyDimension, ...]
    structural_signatures: LiteralStructuralSignatures
    matched_stratum_id: str | None
    analogy_reference_group_id: str | None
    stable_correct_option_id: str = Field(pattern=SLUG_PATTERN)
    witness_sha256: str = Field(pattern=SHA256_PATTERN)
    reversal_transformation: Literal["reversed option presentation"] = (
        "reversed option presentation"
    )
    item_binding_sha256: str = Field(pattern=SHA256_PATTERN)


class LiteralItemBindingBundle(FrozenModel):
    schema_version: Literal["3"] = "3"
    bundle_kind: Literal["literal_item_binding_bundle"] = "literal_item_binding_bundle"
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    bindings: tuple[LiteralItemBinding, ...]
    item_binding_bundle_sha256: str = Field(pattern=SHA256_PATTERN)


class LiteralLexicalFinding(FrozenModel):
    schema_version: Literal["3"] = "3"
    category_version: Literal["literal-lexical-category-v2"] = "literal-lexical-category-v2"
    finding_id: str = Field(pattern=r"^cue-[a-f0-9]{24}$")
    category: LiteralLexicalCategory
    finding_kind: str = Field(pattern=SLUG_PATTERN)
    scope: str = Field(min_length=1)
    value: str = Field(min_length=1)
    occurrence_support: int = Field(ge=1)
    semantic_group_support: int = Field(ge=1)
    answer_class_counts: dict[str, int]
    semantic_group_ids: tuple[str, ...]
    item_ids: tuple[str, ...]
    membership_sha256: str = Field(pattern=SHA256_PATTERN)
    disposition: LiteralAuditStatus

    @model_validator(mode="after")
    def validate_membership(self) -> LiteralLexicalFinding:
        for field_name in ("semantic_group_ids", "item_ids"):
            values = getattr(self, field_name)
            if tuple(sorted(values)) != values or len(values) != len(set(values)):
                raise ValueError(f"{field_name} must be sorted and unique")
        if self.semantic_group_support != len(self.semantic_group_ids):
            raise ValueError("Lexical finding support must match enumerated semantic groups")
        if sum(self.answer_class_counts.values()) > self.occurrence_support:
            raise ValueError("Lexical answer counts cannot exceed occurrence support")
        return self


class LiteralLexicalCategorySummary(FrozenModel):
    category_version: Literal["literal-lexical-category-v2"] = "literal-lexical-category-v2"
    category: LiteralLexicalCategory
    finding_ids: tuple[str, ...]
    finding_count: int = Field(ge=0)
    owner_disposition_required: bool
    category_membership_sha256: str = Field(pattern=SHA256_PATTERN)


class LiteralLexicalAudit(FrozenModel):
    schema_version: Literal["4"] = "4"
    audit_kind: Literal["literal_lexical_cue_audit"] = "literal_lexical_cue_audit"
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    causal_term_allowlist_version: Literal["literal-causal-term-allowlist-v2"] = (
        "literal-causal-term-allowlist-v2"
    )
    causal_term_allowlist: tuple[str, ...]
    semantic_group_count: int
    source_item_count: int
    answer_position_counts: dict[str, int]
    template_answer_counts: dict[str, dict[str, int]]
    action_word_answer_counts: dict[str, dict[str, int]]
    source_mechanism_answer_counts: dict[str, dict[str, int]]
    target_mechanism_answer_counts: dict[str, dict[str, int]]
    prompt_length_by_answer_class: dict[str, dict[str, int]]
    option_length_by_answer_class: dict[str, dict[str, int]]
    distractor_option_length_by_answer_class: dict[str, dict[str, int]]
    option_style_by_answer_class: dict[str, dict[str, int]]
    option_pair_length_difference_counts: dict[str, int]
    tokenizer_specific_length_check_status: Literal["pending_m2_4"] = "pending_m2_4"
    exact_duplicate_group_count: int
    near_duplicate_group_pairs: tuple[tuple[str, str], ...]
    findings: tuple[LiteralLexicalFinding, ...]
    category_summaries: tuple[LiteralLexicalCategorySummary, ...]
    unresolved_owner_review_finding_count: int
    external_language_overlap_status: Literal["not_assessed_m2_2"] = "not_assessed_m2_2"
    status: LiteralAuditStatus
    lexical_audit_sha256: str = Field(pattern=SHA256_PATTERN)


class LiteralSplitAudit(FrozenModel):
    schema_version: Literal["3"] = "3"
    audit_kind: Literal["literal_split_audit"] = "literal_split_audit"
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    semantic_group_count: int
    question_group_count: int
    causal_scenario_count: int
    independent_structural_stratum_count: int
    matched_variant_count: int
    cosmetic_variant_count: int
    l1_group_count: int
    l2_group_count: int
    unique_state_hash_count: int
    unique_observation_hash_count: int
    unique_action_hash_count: int
    unique_group_count: int
    unique_witness_hash_count: int
    l2_structural_novelty_dimensions: dict[str, tuple[StructuralNoveltyDimension, ...]]
    causal_scenario_groups: dict[str, tuple[str, ...]]
    structural_signature_strata: dict[str, tuple[str, ...]]
    exact_prompt_duplicate_count: int
    future_treatment_overlap_status: Literal["not_assessed_m2_2"] = "not_assessed_m2_2"
    status: Literal["PASS"] = "PASS"
    split_audit_sha256: str = Field(pattern=SHA256_PATTERN)


class LiteralValidationReport(FrozenModel):
    schema_version: Literal["4"] = "4"
    report_kind: Literal["literal_validation_report"] = "literal_validation_report"
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    purpose: Literal["outcome", "engineering"]
    semantic_group_count: int
    question_group_count: int
    causal_scenario_count: int
    independent_structural_stratum_count: int
    matched_variant_count: int
    cosmetic_variant_count: int
    source_item_count: int
    schema_counts: dict[str, int]
    level_counts: dict[str, int]
    family_counts: dict[str, int]
    source_mechanism_counts: dict[str, int]
    target_mechanism_counts: dict[str, int]
    simulator_correctness: Literal["PASS"] = "PASS"
    typed_narrative_integrity: Literal["PASS"] = "PASS"
    counterfactual_parity: Literal["PASS"] = "PASS"
    cross_record_consistency: Literal["PASS"] = "PASS"
    split_integrity: Literal["PASS"] = "PASS"
    reverse_equivalence: Literal["PASS"] = "PASS"
    lexical_cue_audit: Literal["PASS", "OWNER_REVIEW_REQUIRED"]
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
    schema_version: Literal["4"] = "4"
    manifest_kind: Literal["literal_source_bundle"] = "literal_source_bundle"
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    purpose: Literal["outcome", "engineering"]
    git: GitState
    codex_spec_sha256: str = Field(pattern=SHA256_PATTERN)
    resolved_configuration: dict[str, Any]
    tracked_configuration_file_sha256: str = Field(pattern=SHA256_PATTERN)
    authoring_input_file_sha256: str = Field(pattern=SHA256_PATTERN)
    authoring_snapshot_sha256: str = Field(pattern=SHA256_PATTERN)
    authoring_snapshot_file_sha256: str = Field(pattern=SHA256_PATTERN)
    m2_1_source_manifest_sha256: str = Field(pattern=SHA256_PATTERN)
    m2_1_items_file_sha256: str = Field(pattern=SHA256_PATTERN)
    partition_plan_sha256: str = Field(pattern=SHA256_PATTERN)
    template_registry_sha256: str = Field(pattern=SHA256_PATTERN)
    item_binding_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    witness_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    split_audit_sha256: str = Field(pattern=SHA256_PATTERN)
    lexical_audit_sha256: str = Field(pattern=SHA256_PATTERN)
    literal_validation_report_sha256: str = Field(pattern=SHA256_PATTERN)
    source_generation_operation_sha256: str = Field(pattern=SHA256_PATTERN)
    artifacts: tuple[ArtifactRecord, ...]
    literal_source_bundle_sha256: str = Field(pattern=SHA256_PATTERN)


class LiteralCandidateManifest(FrozenModel):
    schema_version: Literal["4"] = "4"
    manifest_kind: Literal["literal_private_candidate"] = "literal_private_candidate"
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    purpose: Literal["outcome", "engineering"]
    git: GitState
    codex_spec_sha256: str = Field(pattern=SHA256_PATTERN)
    authoring_snapshot_sha256: str = Field(pattern=SHA256_PATTERN)
    authoring_snapshot_file_sha256: str = Field(pattern=SHA256_PATTERN)
    source_generation_operation_sha256: str = Field(pattern=SHA256_PATTERN)
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
    schema_version: Literal["4"] = "4"
    semantic_group_id: str = Field(pattern=SLUG_PATTERN)
    item_ids: tuple[str, str]
    schema_identity: LiteralSchema
    transfer_level: LiteralTransferLevel
    partition: LiteralPartition
    task_family: LiteralTaskFamily
    scenario_case: LiteralScenarioCase
    source_mechanism: LiteralMechanismKind
    target_mechanism: LiteralMechanismKind
    structural_novelty_dimensions: tuple[StructuralNoveltyDimension, ...]
    structural_signatures: LiteralStructuralSignatures
    prompt: str
    instructions: str
    option_forms: tuple[tuple[dict[str, str], ...], tuple[dict[str, str], ...]]
    stable_correct_option_id: str
    typed_actual_action_summary: str
    typed_counterfactual_action_summary: str
    actual_outcome_code: LiteralOutcomeCode
    counterfactual_outcome_code: LiteralOutcomeCode
    allowed_initial_difference_paths: tuple[str, ...]
    observed_initial_difference_paths: tuple[str, ...]
    allowed_action_difference_paths: tuple[str, ...]
    observed_action_difference_paths: tuple[str, ...]
    declared_equal_fields: tuple[str, ...]
    simulator_rationale: str
    cue_findings: tuple[LiteralLexicalFinding, ...]
    lexical_cue_annotations: tuple[str, ...]
    provenance: ProvenanceRights
    human_validation: HumanValidationMetadata
    governance_status: Literal["owner_review_pending", "engineering_only"]
    full_frame_render_paths: tuple[str, str, str, str]
    review_zoom_render_paths: tuple[str, str, str, str]
    authoring_snapshot_sha256: str = Field(pattern=SHA256_PATTERN)
    literal_candidate_root_sha256: str = Field(pattern=SHA256_PATTERN)
    witness_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    literal_validation_report_sha256: str = Field(pattern=SHA256_PATTERN)
    witness_sha256: str = Field(pattern=SHA256_PATTERN)
    item_binding_sha256: str = Field(pattern=SHA256_PATTERN)


class LiteralCueDispositionRecord(FrozenModel):
    schema_version: Literal["3"] = "3"
    record_kind: Literal["literal_cue_owner_disposition"] = "literal_cue_owner_disposition"
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    lexical_audit_sha256: str = Field(pattern=SHA256_PATTERN)
    candidate_root_sha256: str = Field(pattern=SHA256_PATTERN)
    status: Literal["PENDING"] = "PENDING"
    required_category_membership_hashes: dict[LiteralLexicalCategory, str]
    accepted_category_membership_hashes: tuple[str, ...] = ()
    rejected_category_membership_hashes: tuple[str, ...] = ()
    consequential_finding_ids: tuple[str, ...]
    accepted_finding_ids: tuple[str, ...] = ()
    rejected_finding_ids: tuple[str, ...] = ()
    owner_decision_recorded: Literal[False] = False

    @model_validator(mode="after")
    def validate_pending_disposition(self) -> LiteralCueDispositionRecord:
        if tuple(sorted(self.consequential_finding_ids)) != self.consequential_finding_ids:
            raise ValueError("Consequential cue finding IDs must be sorted")
        if len(self.consequential_finding_ids) != len(set(self.consequential_finding_ids)):
            raise ValueError("Consequential cue finding IDs must be unique")
        if set(self.accepted_category_membership_hashes) & set(
            self.rejected_category_membership_hashes
        ):
            raise ValueError("Cue categories cannot be both accepted and rejected")
        if set(self.accepted_finding_ids) & set(self.rejected_finding_ids):
            raise ValueError("Cue findings cannot be both accepted and rejected")
        allowed_category_hashes = set(self.required_category_membership_hashes.values())
        if (
            not set(self.accepted_category_membership_hashes) <= allowed_category_hashes
            or not set(self.rejected_category_membership_hashes) <= allowed_category_hashes
        ):
            raise ValueError("Cue disposition references an unbound category membership hash")
        allowed_finding_ids = set(self.consequential_finding_ids)
        if (
            not set(self.accepted_finding_ids) <= allowed_finding_ids
            or not set(self.rejected_finding_ids) <= allowed_finding_ids
        ):
            raise ValueError("Cue disposition references an unbound finding ID")
        for field_name in (
            "accepted_category_membership_hashes",
            "rejected_category_membership_hashes",
            "accepted_finding_ids",
            "rejected_finding_ids",
        ):
            values = getattr(self, field_name)
            if tuple(sorted(values)) != values or len(values) != len(set(values)):
                raise ValueError(f"{field_name} must be sorted and unique")
        return self


class LiteralPendingOwnerReview(FrozenModel):
    schema_version: Literal["3"] = "3"
    record_kind: Literal["literal_pending_owner_review"] = "literal_pending_owner_review"
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    status: Literal["PENDING"] = "PENDING"
    owner_decision_recorded: Literal[False] = False
    substitutes_for_human_validation: Literal[False] = False
    required_owner_bindings: tuple[str, ...]

    @model_validator(mode="after")
    def validate_binding_set(self) -> LiteralPendingOwnerReview:
        expected = {
            "authoring_snapshot_file_sha256",
            "authoring_snapshot_sha256",
            "candidate_materialization_operation_sha256",
            "literal_candidate_root_sha256",
            "literal_validation_report_sha256",
            "m2_1_candidate_bundle_root_sha256",
            "m2_1_candidate_manifest_file_sha256",
            "m2_1_source_snapshot_sha256",
            "pull_request_head_sha",
            "pull_request_number",
            "review_manifest_file_sha256",
            "review_manifest_sha256",
            "review_operation_sha256",
            "source_generation_operation_sha256",
            "witness_bundle_sha256",
        }
        if set(self.required_owner_bindings) != expected:
            raise ValueError("Pending owner-review binding set is incomplete or unexpected")
        if tuple(sorted(self.required_owner_bindings)) != self.required_owner_bindings:
            raise ValueError("Pending owner-review bindings must use sorted ordering")
        return self


class LiteralRenderRecord(FrozenModel):
    schema_version: Literal["2"] = "2"
    path: str = Field(min_length=1)
    view_kind: Literal["scientific-full-frame", "review-zoom"]
    width: Literal[128] = 128
    height: Literal[128] = 128
    mode: Literal["RGB"] = "RGB"
    raw_pixel_sha256: str = Field(pattern=SHA256_PATTERN)
    logical_render_sha256: str = Field(pattern=SHA256_PATTERN)
    scientific_render_sha256: str | None = Field(default=None, pattern=SHA256_PATTERN)
    source_full_frame_raw_pixel_sha256: str | None = Field(default=None, pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_view_identity(self) -> LiteralRenderRecord:
        if self.view_kind == "scientific-full-frame":
            if (
                self.scientific_render_sha256 is None
                or self.source_full_frame_raw_pixel_sha256 is not None
                or self.logical_render_sha256 != self.scientific_render_sha256
            ):
                raise ValueError("Full-frame render identity is inconsistent")
        elif (
            self.scientific_render_sha256 is not None
            or self.source_full_frame_raw_pixel_sha256 is None
        ):
            raise ValueError("Review-zoom render identity is inconsistent")
        return self


class LiteralReviewManifest(FrozenModel):
    schema_version: Literal["4"] = "4"
    manifest_kind: Literal["literal_private_review_bundle"] = "literal_private_review_bundle"
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    git: GitState
    codex_spec_sha256: str = Field(pattern=SHA256_PATTERN)
    authoring_snapshot_sha256: str = Field(pattern=SHA256_PATTERN)
    authoring_snapshot_file_sha256: str = Field(pattern=SHA256_PATTERN)
    source_generation_operation_sha256: str = Field(pattern=SHA256_PATTERN)
    candidate_materialization_operation_sha256: str = Field(pattern=SHA256_PATTERN)
    review_operation_sha256: str = Field(pattern=SHA256_PATTERN)
    literal_candidate_root_sha256: str = Field(pattern=SHA256_PATTERN)
    witness_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    literal_validation_report_sha256: str = Field(pattern=SHA256_PATTERN)
    review_content_bundle_sha256: str = Field(pattern=SHA256_PATTERN)
    render_records: tuple[LiteralRenderRecord, ...]
    artifacts: tuple[ArtifactRecord, ...]
    review_manifest_sha256: str = Field(pattern=SHA256_PATTERN)


class LiteralOperationRecord(FrozenModel):
    schema_version: Literal["4"] = "4"
    record_kind: Literal["literal_operation"] = "literal_operation"
    operation_id: str
    operation_kind: Literal[
        "generate_literal_source",
        "validate_literal_source",
        "materialize_literal_candidate",
        "validate_literal_benchmark",
        "build_literal_review",
        "validate_literal_review",
    ]
    candidate_version: str = Field(pattern=SLUG_PATTERN)
    purpose: Literal["outcome", "engineering"]
    engineering_only: bool
    scientific_result: Literal[False] = False
    git: GitState
    codex_spec_sha256: str = Field(pattern=SHA256_PATTERN)
    environment_version: Literal["schemaworld-core-v1"] = "schemaworld-core-v1"
    generator_version: Literal["literal-generator-v3"] = "literal-generator-v3"
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
