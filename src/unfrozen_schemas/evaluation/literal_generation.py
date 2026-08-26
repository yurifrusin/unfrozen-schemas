"""Deterministic private M2.2 literal-source generation."""

from __future__ import annotations

import string
import time
import tracemalloc
from collections import Counter
from collections.abc import Iterable, Sequence
from typing import Literal

from unfrozen_schemas.budgets import (
    RESOURCE_FIELDS,
    ResourceBudget,
    ResourceField,
    ResourceMeasurementBasis,
)
from unfrozen_schemas.config import sha256_file
from unfrozen_schemas.envs.schema_world.serialization import primary_observation
from unfrozen_schemas.evaluation.benchmark_hashing import canonical_logical_bytes
from unfrozen_schemas.evaluation.benchmark_models import (
    CANONICAL_QUARANTINE_ROOTS,
    AdjudicationStatus,
    AnswerOption,
    AnswerProvenance,
    BenchmarkPurpose,
    GovernanceStatus,
    HumanValidationMetadata,
    HumanValidationStatus,
    ModelVisibleContent,
    OriginClassification,
    ProvenanceRights,
    QuarantineScopeDeclaration,
    QuarantineScopeMode,
    RightsStatus,
    SchemaDesignation,
    ScientificAnnotations,
    SourceItemRecord,
    SourceManifest,
    SourcePrivateAnswer,
    TrainedSchemaRole,
)
from unfrozen_schemas.evaluation.benchmark_persistence import (
    make_artifact_records,
    write_canonical_json,
    write_canonical_jsonl,
)
from unfrozen_schemas.evaluation.literal_hashing import (
    item_binding_bundle_hash,
    item_binding_hash,
    operation_hash,
    partition_plan_hash,
    source_bundle_hash,
    template_hash,
    template_registry_hash,
    validation_report_hash,
    witness_bundle_hash,
)
from unfrozen_schemas.evaluation.literal_models import (
    LiteralAuthoringManifest,
    LiteralItemBinding,
    LiteralItemBindingBundle,
    LiteralOperationError,
    LiteralOperationRecord,
    LiteralOperationResult,
    LiteralPartition,
    LiteralPartitionPlan,
    LiteralScenarioSpec,
    LiteralSchema,
    LiteralSourceBundleManifest,
    LiteralTemplate,
    LiteralTemplateRegistryManifest,
    LiteralTransferLevel,
    LiteralValidationReport,
    LiteralWitnessBundle,
    LiteralWitnessRecord,
)
from unfrozen_schemas.evaluation.literal_scenarios import build_witness, literal_item_ids
from unfrozen_schemas.evaluation.literal_validation import (
    GENERATION_OPERATION_FILE,
    ITEM_BINDINGS_FILE,
    LEXICAL_AUDIT_FILE,
    LITERAL_DIRECTORY,
    PARTITION_PLAN_FILE,
    SOURCE_BUNDLE_FILE,
    SPLIT_AUDIT_FILE,
    TEMPLATE_REGISTRY_FILE,
    VALIDATION_REPORT_FILE,
    WITNESS_BUNDLE_FILE,
    build_lexical_audit,
    build_split_audit,
)
from unfrozen_schemas.literal_config import LoadedLiteralConfig
from unfrozen_schemas.provenance import (
    capture_git_state,
    collect_package_versions,
    collect_platform_information,
    create_run_id,
    utc_now,
)

_ALLOWED_TEMPLATE_FIELDS = frozenset(
    {
        "scene_description",
        "actual_action_description",
        "counterfactual_action_description",
    }
)


def _counts(values: Iterable[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def render_literal_prompt(template: LiteralTemplate, scenario: object) -> str:
    """Render only declared typed scenario facts through a closed placeholder set."""

    values = {name: str(getattr(scenario, name)) for name in sorted(_ALLOWED_TEMPLATE_FIELDS)}
    formatter = string.Formatter()
    fields = []
    for _literal, field_name, format_spec, conversion in formatter.parse(template.prompt_format):
        if field_name is None:
            continue
        if field_name not in _ALLOWED_TEMPLATE_FIELDS:
            raise ValueError(f"Unknown private literal-template field: {field_name}")
        if format_spec or conversion:
            raise ValueError("Literal templates prohibit conversions and format specifications")
        fields.append(field_name)
    if not fields:
        raise ValueError("Literal prompt templates must render at least one typed scenario fact")
    rendered = template.prompt_format.format_map(values)
    if rendered != " ".join(rendered.split()):
        raise ValueError("Rendered literal prompts must use canonical single whitespace")
    return rendered


def _option_mapping(spec: LiteralScenarioSpec, witness: LiteralWitnessRecord) -> dict[str, str]:
    positive = spec.positive_option_text
    negative = spec.negative_option_text
    if witness.schema_identity is LiteralSchema.CONTAINMENT:
        return {"movement-succeeds": positive, "movement-blocked": negative}
    return {"object-falls": positive, "object-stays": negative}


def _governance(
    *, engineering_only: bool
) -> tuple[ProvenanceRights, HumanValidationMetadata, AnswerProvenance]:
    if engineering_only:
        provenance = ProvenanceRights(
            authorship_origin="repository engineering fixture",
            source_reference="tracked non-scientific M2.2 engineering fixture",
            origin_classification=OriginClassification.ENGINEERING_FIXTURE,
            rights_status=RightsStatus.NOT_APPLICABLE_ENGINEERING,
            transformation_history=("deterministic typed fixture rendering",),
            reviewer_references=(),
            ethics_status=GovernanceStatus.NOT_APPLICABLE_ENGINEERING,
            created_from_source_record="placeholder",
            created_from_source_revision=1,
        )
        validation = HumanValidationMetadata(
            validation_status=HumanValidationStatus.NOT_APPLICABLE_ENGINEERING,
            validator_count=0,
            adjudication_status=AdjudicationStatus.NOT_APPLICABLE_ENGINEERING,
            ambiguity_findings=(),
        )
        return provenance, validation, AnswerProvenance.ENGINEERING_FIXTURE
    provenance = ProvenanceRights(
        authorship_origin="repository-authored clean-room simulator-derived content",
        source_reference="private M2.2 typed authoring manifest",
        origin_classification=OriginClassification.SIMULATOR_DERIVED,
        rights_status=RightsStatus.UNRESOLVED,
        licence_reference=None,
        transformation_history=("deterministic typed literal rendering",),
        reviewer_references=(),
        ethics_status=GovernanceStatus.UNRESOLVED,
        ethics_reference=None,
        created_from_source_record="placeholder",
        created_from_source_revision=1,
    )
    validation = HumanValidationMetadata(
        validation_status=HumanValidationStatus.NOT_STARTED,
        validator_count=0,
        adjudication_status=AdjudicationStatus.NOT_STARTED,
        ambiguity_findings=(),
    )
    return provenance, validation, AnswerProvenance.INDEPENDENT_SIMULATOR


def _source_items(
    authoring: LiteralAuthoringManifest,
    witnesses: Sequence[LiteralWitnessRecord],
) -> tuple[tuple[SourceItemRecord, ...], tuple[LiteralItemBinding, ...]]:
    template_by_id = {item.template_id: item for item in authoring.templates}
    witness_by_group = {item.semantic_group_id: item for item in witnesses}
    items: list[SourceItemRecord] = []
    bindings: list[LiteralItemBinding] = []
    engineering = authoring.engineering_only
    purpose = BenchmarkPurpose.ENGINEERING if engineering else BenchmarkPurpose.OUTCOME
    for spec in sorted(authoring.scenarios, key=lambda item: item.semantic_group_id):
        witness = witness_by_group[spec.semantic_group_id]
        template = template_by_id[spec.prompt_template_id]
        prompt = render_literal_prompt(template, spec)
        option_mapping = _option_mapping(spec, witness)
        normal_order = tuple(sorted(option_mapping))
        reverse_order = tuple(reversed(normal_order))
        item_ids = literal_item_ids(spec.semantic_group_id)
        for index, (item_id, order) in enumerate(
            zip(item_ids, (normal_order, reverse_order), strict=True)
        ):
            base_provenance, human_validation, answer_provenance = _governance(
                engineering_only=engineering
            )
            history = base_provenance.transformation_history
            if index == 1:
                history = (*history, "reversed option presentation")
            provenance = base_provenance.model_copy(
                update={
                    "created_from_source_record": item_id,
                    "transformation_history": history,
                }
            )
            items.append(
                SourceItemRecord(
                    item_id=item_id,
                    item_revision=1,
                    purpose=purpose,
                    identity_purpose=purpose,
                    task_family_slug=spec.task_family.value,
                    transfer_level=1 if spec.transfer_level is LiteralTransferLevel.L1 else 2,
                    schema_designation=SchemaDesignation.ITEM_SCHEMA,
                    target_domain_family="literal-physical",
                    source_mechanism_family=spec.source_mechanism_family,
                    prompt_template_id=spec.prompt_template_id,
                    partition_id=spec.partition.value,
                    engineering_only=engineering,
                    scientific_eligible=authoring.scientific_eligible,
                    promotable=authoring.promotable,
                    model_visible=ModelVisibleContent(
                        prompt=prompt,
                        instructions=template.instructions,
                        ordered_options=tuple(
                            AnswerOption(option_id=option_id, text=option_mapping[option_id])
                            for option_id in order
                        ),
                        reverse_pair_id=spec.semantic_group_id,
                        variant_id="normal" if index == 0 else "reversed",
                        option_permutation=order,
                        closed_book_eligible=True,
                        open_book_eligible=True,
                    ),
                    scientific_annotations=ScientificAnnotations(
                        required_causal_factors=(spec.declared_causal_factor,),
                        composition_depth=1
                        if spec.transfer_level is LiteralTransferLevel.L1
                        else 2,
                        lexical_cue_annotations=spec.lexical_cue_annotations,
                        source_mechanism_family=spec.source_mechanism_family,
                        conventionality_estimate=None,
                        external_language_overlap_flags=("not_assessed_m2_2",),
                        target_domain_family="literal-physical",
                        trained_schema_role=TrainedSchemaRole.NOT_APPLICABLE,
                    ),
                    provenance=provenance,
                    human_validation=human_validation,
                    private_answer=SourcePrivateAnswer(
                        correct_option_id=witness.stable_correct_option_id,
                        answer_rationale=(
                            "Engineering verifier outcome."
                            if engineering
                            else "The released deterministic simulator replay derives this outcome."
                        ),
                        simulator_verification_reference=(
                            f"literal-witness-sha256:{witness.witness_sha256}"
                        ),
                        answer_provenance=answer_provenance,
                    ),
                )
            )
        provisional = LiteralItemBinding(
            semantic_group_id=spec.semantic_group_id,
            item_ids=item_ids,
            variant_ids=("normal", "reversed"),
            option_permutations=(normal_order, reverse_order),
            schema_identity=spec.schema_identity,
            transfer_level=spec.transfer_level,
            task_family=spec.task_family,
            source_mechanism_family=spec.source_mechanism_family,
            prompt_template_id=spec.prompt_template_id,
            partition=spec.partition,
            scenario_case=spec.scenario_case.value,
            action_word=spec.action_word,
            counterfactual_group_id=f"{spec.semantic_group_id}-counterfactual",
            structural_novelty_dimensions=spec.structural_novelty_dimensions,
            stable_correct_option_id=witness.stable_correct_option_id,
            witness_sha256=witness.witness_sha256,
            item_binding_sha256="0" * 64,
        )
        bindings.append(
            provisional.model_copy(update={"item_binding_sha256": item_binding_hash(provisional)})
        )
    return tuple(sorted(items, key=lambda item: item.item_id)), tuple(bindings)


def _partition_plan(authoring: LiteralAuthoringManifest) -> LiteralPartitionPlan:
    groups = {
        partition: tuple(
            sorted(
                scenario.semantic_group_id
                for scenario in authoring.scenarios
                if scenario.partition is partition
            )
        )
        for partition in LiteralPartition
    }
    provisional = LiteralPartitionPlan(
        candidate_version=authoring.candidate_version,
        prospective_adaptation_strata=tuple(sorted(authoring.prospective_adaptation_strata)),
        l1_held_out_group_ids=groups[LiteralPartition.L1_HELD_OUT],
        l2_novel_template_group_ids=groups[LiteralPartition.L2_NOVEL_TEMPLATE],
        l2_novel_configuration_group_ids=groups[LiteralPartition.L2_NOVEL_CONFIGURATION],
        l2_mechanism_transfer_group_ids=groups[LiteralPartition.L2_MECHANISM_TRANSFER],
        benchmark_reserved_prompt_template_ids=tuple(
            sorted(template.template_id for template in authoring.templates)
        ),
        benchmark_reserved_semantic_group_ids=tuple(
            sorted(scenario.semantic_group_id for scenario in authoring.scenarios)
        ),
        partition_plan_sha256="0" * 64,
    )
    return provisional.model_copy(
        update={"partition_plan_sha256": partition_plan_hash(provisional)}
    )


def _template_registry(authoring: LiteralAuthoringManifest) -> LiteralTemplateRegistryManifest:
    hashes = {
        template.template_id: template_hash(template)
        for template in sorted(authoring.templates, key=lambda item: item.template_id)
    }
    provisional = LiteralTemplateRegistryManifest(
        candidate_version=authoring.candidate_version,
        template_ids=tuple(sorted(hashes)),
        template_content_hashes=dict(sorted(hashes.items())),
        template_registry_sha256="0" * 64,
    )
    return provisional.model_copy(
        update={"template_registry_sha256": template_registry_hash(provisional)}
    )


def _coverage(config: LoadedLiteralConfig, bindings: Sequence[LiteralItemBinding]) -> None:
    coverage = config.resolved.coverage
    if len(bindings) < coverage.minimum_semantic_groups:
        raise ValueError("Literal semantic-group coverage floor is not met")
    schemas = Counter(binding.schema_identity for binding in bindings)
    levels = Counter(binding.transfer_level for binding in bindings)
    families = {binding.task_family for binding in bindings}
    if not set(coverage.required_schemas) <= set(schemas):
        raise ValueError("Literal source is missing a required schema")
    if not set(coverage.required_levels) <= set(levels):
        raise ValueError("Literal source is missing a required transfer level")
    if not set(coverage.required_task_families) <= families:
        raise ValueError("Literal source is missing a required task family")
    for schema in coverage.required_schemas:
        if schemas[schema] < coverage.minimum_groups_per_schema:
            raise ValueError(f"Literal source has too few {schema.value} groups")
        for level in coverage.required_levels:
            cell = sum(
                binding.schema_identity is schema and binding.transfer_level is level
                for binding in bindings
            )
            if cell < coverage.minimum_groups_per_schema_level:
                raise ValueError(
                    f"Literal source has too few {schema.value} x {level.value} groups"
                )
    if config.resolved.purpose == "outcome":
        containment_cases = {
            binding.scenario_case
            for binding in bindings
            if binding.schema_identity is LiteralSchema.CONTAINMENT
        }
        support_cases = {
            binding.scenario_case
            for binding in bindings
            if binding.schema_identity is LiteralSchema.SUPPORT
        }
        required_containment = {
            "fitting-opening",
            "closed-boundary",
            "undersized-opening",
            "misaligned-opening",
            "fully-open-boundary",
        }
        required_support = {
            "lower-support-removal",
            "lower-support-noop",
            "side-contact",
            "tether-cut",
            "tethered-platform-removal",
            "nonbearing-tether",
        }
        if not required_containment <= containment_cases:
            raise ValueError("Outcome literal source lacks required containment contrasts")
        if not required_support <= support_cases:
            raise ValueError("Outcome literal source lacks required support contrasts")


def _basis(
    status: Literal["measured", "derived", "observed_zero", "unavailable"],
    method: str,
    reason: str | None = None,
) -> ResourceMeasurementBasis:
    return ResourceMeasurementBasis(status=status, method=method, reason=reason)


def _resource_budget(
    *,
    operation_id: str,
    started_at: object,
    ended_at: object,
    elapsed: float,
    peak_memory: int | None,
    witnesses: Sequence[LiteralWitnessRecord],
    artifact_count: int,
    artifact_bytes: int,
) -> ResourceBudget:
    from datetime import datetime

    assert isinstance(started_at, datetime) and isinstance(ended_at, datetime)
    basis: dict[ResourceField, ResourceMeasurementBasis] = {}
    for field in RESOURCE_FIELDS:
        if field in {
            "external_language_tokens",
            "self_generated_language_tokens",
            "optimisation_steps",
            "forward_passes",
            "backward_passes",
        }:
            basis[field] = _basis(
                "observed_zero", "M2.2 offline deterministic code-path observation"
            )
        elif field in {"sensor_observations", "sensor_bytes", "environment_steps"}:
            basis[field] = _basis("measured", "M2.2 literal witness construction counters")
        elif field in {"stored_artifact_count", "stored_artifact_bytes"}:
            basis[field] = _basis(
                "derived", "retained hash-stable source files excluding provenance"
            )
        elif field == "elapsed_compute_seconds":
            basis[field] = _basis("measured", "time.perf_counter monotonic elapsed time")
        elif field == "peak_memory_bytes":
            basis[field] = (
                _basis("measured", "tracemalloc peak traced Python allocations")
                if peak_memory is not None
                else _basis("unavailable", "tracemalloc", "tracemalloc was unavailable")
            )
    sensor_bytes = sum(
        len(canonical_logical_bytes(primary_observation(state)))
        for witness in witnesses
        for state in (
            witness.initial_privileged_state,
            witness.counterfactual_initial_privileged_state,
        )
    )
    return ResourceBudget(
        run_id=operation_id,
        interval_kind="run",
        interval_start=started_at,
        interval_end=ended_at,
        external_language_tokens=0,
        self_generated_language_tokens=0,
        sensor_observations=2 * len(witnesses),
        sensor_bytes=sensor_bytes,
        environment_steps=sum(
            len(witness.actual_actions) + len(witness.counterfactual_actions)
            for witness in witnesses
        ),
        optimisation_steps=0,
        forward_passes=0,
        backward_passes=0,
        elapsed_compute_seconds=elapsed,
        peak_memory_bytes=peak_memory,
        stored_artifact_count=artifact_count,
        stored_artifact_bytes=artifact_bytes,
        measurement_basis=basis,
    )


def _source_manifest(authoring: LiteralAuthoringManifest, item_count: int) -> SourceManifest:
    purpose = (
        BenchmarkPurpose.ENGINEERING if authoring.engineering_only else BenchmarkPurpose.OUTCOME
    )
    engineering = authoring.engineering_only
    return SourceManifest(
        benchmark_version=authoring.candidate_version,
        purpose=purpose,
        engineering_only=engineering,
        scientific_eligible=authoring.scientific_eligible,
        promotable=authoring.promotable,
        expected_item_count=item_count,
        rights_determination_reference=(
            "not-applicable-engineering-fixture" if engineering else "pending-m2.2-owner-review"
        ),
        human_validation_reference=(
            "not-applicable-engineering-fixture" if engineering else "not-started-m2.2"
        ),
        ethics_determination_reference=(
            "not-applicable-engineering-fixture" if engineering else "unresolved-m2.2"
        ),
        quarantine_scope=QuarantineScopeDeclaration(
            mode=(
                QuarantineScopeMode.ENGINEERING_EMPTY
                if engineering
                else QuarantineScopeMode.CANONICAL_ROOT_SCAN
            ),
            canonical_roots=() if engineering else CANONICAL_QUARANTINE_ROOTS,
        ),
    )


def _read_authoring(config: LoadedLiteralConfig) -> LiteralAuthoringManifest:
    authoring = LiteralAuthoringManifest.model_validate_json(config.authoring_manifest.read_bytes())
    resolved = config.resolved
    if (
        authoring.candidate_version != resolved.candidate_version
        or authoring.purpose != resolved.purpose
        or authoring.engineering_only != resolved.engineering_only
        or authoring.scientific_eligible != resolved.scientific_eligible
        or authoring.promotable != resolved.promotable
    ):
        raise ValueError("Literal authoring manifest and tracked configuration disagree")
    scenario_seeds = tuple(sorted(item.seed for item in authoring.scenarios))
    if scenario_seeds != tuple(sorted(config.resolved.generation_seeds)):
        raise ValueError(
            "Literal authoring scenario seeds must exactly match the tracked generation seeds"
        )
    return authoring


def generate_literal_source(
    config: LoadedLiteralConfig, *, dry_run: bool = False
) -> LiteralOperationResult:
    """Generate one write-once M2.1-compatible source with hash-bound M2.2 sidecars."""

    operation_id = create_run_id("literal-source-generation")
    started_at = utc_now()
    start_tick = time.perf_counter()
    tracing_was_active = tracemalloc.is_tracing()
    if not tracing_was_active:
        tracemalloc.start()
    root = config.source_root.resolve()
    output_paths = (
        root / "source_manifest.json",
        root / "items.jsonl",
        *(
            root / LITERAL_DIRECTORY / name
            for name in (
                PARTITION_PLAN_FILE,
                TEMPLATE_REGISTRY_FILE,
                ITEM_BINDINGS_FILE,
                WITNESS_BUNDLE_FILE,
                LEXICAL_AUDIT_FILE,
                SPLIT_AUDIT_FILE,
                VALIDATION_REPORT_FILE,
                GENERATION_OPERATION_FILE,
                SOURCE_BUNDLE_FILE,
            )
        ),
    )
    try:
        if any(path.exists() for path in output_paths):
            raise FileExistsError(f"Literal source destination contains generated files: {root}")
        if root.exists():
            allowed = (
                {config.authoring_manifest.resolve()}
                if config.authoring_manifest.parent == root
                else set()
            )
            observed = {path.resolve() for path in root.iterdir()}
            if observed - allowed:
                raise FileExistsError(
                    f"Literal source destination is not an authoring-only directory: {root}"
                )
        authoring = _read_authoring(config)
        witnesses = tuple(
            build_witness(spec)
            for spec in sorted(authoring.scenarios, key=lambda item: item.semantic_group_id)
        )
        items, bindings = _source_items(authoring, witnesses)
        _coverage(config, bindings)
        partition = _partition_plan(authoring)
        template_registry = _template_registry(authoring)
        binding_provisional = LiteralItemBindingBundle(
            candidate_version=authoring.candidate_version,
            bindings=bindings,
            item_binding_bundle_sha256="0" * 64,
        )
        binding_bundle = binding_provisional.model_copy(
            update={"item_binding_bundle_sha256": item_binding_bundle_hash(binding_provisional)}
        )
        witness_provisional = LiteralWitnessBundle(
            candidate_version=authoring.candidate_version,
            witnesses=witnesses,
            witness_bundle_sha256="0" * 64,
        )
        witness_bundle = witness_provisional.model_copy(
            update={"witness_bundle_sha256": witness_bundle_hash(witness_provisional)}
        )
        lexical = build_lexical_audit(
            candidate_version=authoring.candidate_version,
            items=items,
            bindings=bindings,
        )
        split = build_split_audit(
            candidate_version=authoring.candidate_version,
            items=items,
            bindings=bindings,
            witnesses=witnesses,
        )
        schema_counts = _counts(item.schema_identity.value for item in bindings)
        level_counts = _counts(item.transfer_level.value for item in bindings)
        family_counts = _counts(item.task_family.value for item in bindings)
        mechanism_counts = _counts(item.source_mechanism_family for item in bindings)
        validation_provisional = LiteralValidationReport(
            candidate_version=authoring.candidate_version,
            purpose=authoring.purpose,
            semantic_group_count=len(bindings),
            source_item_count=len(items),
            schema_counts=schema_counts,
            level_counts=level_counts,
            family_counts=family_counts,
            mechanism_counts=mechanism_counts,
            m2_1_lifecycle_validation="not_evaluated_source_stage",
            human_validation_status=(
                "not_applicable_engineering" if authoring.engineering_only else "not_started"
            ),
            rights_status=(
                "not_applicable_engineering" if authoring.engineering_only else "unresolved"
            ),
            ethics_governance_status=(
                "not_applicable_engineering" if authoring.engineering_only else "unresolved"
            ),
            literal_validation_report_sha256="0" * 64,
        )
        validation = validation_provisional.model_copy(
            update={
                "literal_validation_report_sha256": validation_report_hash(validation_provisional)
            }
        )
        if dry_run:
            if not tracing_was_active:
                tracemalloc.stop()
            return LiteralOperationResult(
                operation_id=operation_id,
                dry_run=True,
                candidate_version=authoring.candidate_version,
                purpose=authoring.purpose,
                source_path=None,
                semantic_group_count=len(bindings),
                source_item_count=len(items),
                partition_plan_sha256=partition.partition_plan_sha256,
                template_registry_sha256=template_registry.template_registry_sha256,
                witness_bundle_sha256=witness_bundle.witness_bundle_sha256,
                literal_validation_report_sha256=validation.literal_validation_report_sha256,
            )
        root.mkdir(parents=True, exist_ok=True)
        literal_root = root / LITERAL_DIRECTORY
        literal_root.mkdir(parents=False, exist_ok=False)
        manifest = _source_manifest(authoring, len(items))
        write_canonical_json(root / "source_manifest.json", manifest)
        write_canonical_jsonl(root / "items.jsonl", list(items))
        write_canonical_json(literal_root / PARTITION_PLAN_FILE, partition)
        write_canonical_json(literal_root / TEMPLATE_REGISTRY_FILE, template_registry)
        write_canonical_json(literal_root / ITEM_BINDINGS_FILE, binding_bundle)
        write_canonical_json(literal_root / WITNESS_BUNDLE_FILE, witness_bundle)
        write_canonical_json(literal_root / LEXICAL_AUDIT_FILE, lexical)
        write_canonical_json(literal_root / SPLIT_AUDIT_FILE, split)
        write_canonical_json(literal_root / VALIDATION_REPORT_FILE, validation)
        base_paths = [
            root / "source_manifest.json",
            root / "items.jsonl",
            literal_root / PARTITION_PLAN_FILE,
            literal_root / TEMPLATE_REGISTRY_FILE,
            literal_root / ITEM_BINDINGS_FILE,
            literal_root / WITNESS_BUNDLE_FILE,
            literal_root / LEXICAL_AUDIT_FILE,
            literal_root / SPLIT_AUDIT_FILE,
            literal_root / VALIDATION_REPORT_FILE,
        ]
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
            witnesses=witnesses,
            artifact_count=len(base_paths),
            artifact_bytes=sum(path.stat().st_size for path in base_paths),
        )
        source_placeholder = LiteralSourceBundleManifest(
            candidate_version=authoring.candidate_version,
            purpose=authoring.purpose,
            authoring_manifest_sha256=sha256_file(config.authoring_manifest),
            m2_1_source_manifest_sha256=sha256_file(root / "source_manifest.json"),
            m2_1_items_file_sha256=sha256_file(root / "items.jsonl"),
            partition_plan_sha256=partition.partition_plan_sha256,
            template_registry_sha256=template_registry.template_registry_sha256,
            item_binding_bundle_sha256=binding_bundle.item_binding_bundle_sha256,
            witness_bundle_sha256=witness_bundle.witness_bundle_sha256,
            split_audit_sha256=split.split_audit_sha256,
            lexical_audit_sha256=lexical.lexical_audit_sha256,
            literal_validation_report_sha256=validation.literal_validation_report_sha256,
            generation_operation_sha256="0" * 64,
            artifacts=make_artifact_records(root, base_paths),
            literal_source_bundle_sha256="0" * 64,
        )
        logical_source_hash = source_bundle_hash(source_placeholder)
        operation_provisional = LiteralOperationRecord(
            operation_id=operation_id,
            operation_kind="generate_literal_source",
            candidate_version=authoring.candidate_version,
            purpose=authoring.purpose,
            engineering_only=authoring.engineering_only,
            git=capture_git_state(config.repository_root),
            codex_spec_sha256=sha256_file(config.repository_root / "CODEX_SPEC.md"),
            resolved_configuration=config.resolved.model_dump(mode="json"),
            input_hashes={"authoring_manifest_sha256": sha256_file(config.authoring_manifest)},
            output_hashes={"literal_source_bundle_sha256": logical_source_hash},
            item_count=len(items),
            semantic_group_count=len(bindings),
            schema_counts=schema_counts,
            level_counts=level_counts,
            family_counts=family_counts,
            status="COMPLETED",
            failure_reason=None,
            package_versions=collect_package_versions(),
            platform=collect_platform_information(),
            started_at=started_at,
            ended_at=ended_at,
            artifacts=make_artifact_records(root, base_paths),
            resource_budget=budget,
            operation_sha256="0" * 64,
        )
        operation = operation_provisional.model_copy(
            update={"operation_sha256": operation_hash(operation_provisional)}
        )
        write_canonical_json(literal_root / GENERATION_OPERATION_FILE, operation)
        source_bundle = source_placeholder.model_copy(
            update={
                "generation_operation_sha256": operation.operation_sha256,
                "literal_source_bundle_sha256": logical_source_hash,
            }
        )
        write_canonical_json(literal_root / SOURCE_BUNDLE_FILE, source_bundle)
        return LiteralOperationResult(
            operation_id=operation_id,
            dry_run=False,
            candidate_version=authoring.candidate_version,
            purpose=authoring.purpose,
            source_path=str(root),
            semantic_group_count=len(bindings),
            source_item_count=len(items),
            partition_plan_sha256=partition.partition_plan_sha256,
            template_registry_sha256=template_registry.template_registry_sha256,
            witness_bundle_sha256=witness_bundle.witness_bundle_sha256,
            literal_validation_report_sha256=validation.literal_validation_report_sha256,
        )
    except Exception as exc:
        if not tracing_was_active and tracemalloc.is_tracing():
            tracemalloc.stop()
        raise LiteralOperationError(
            f"{type(exc).__name__}: {exc}", failure_record_path=None
        ) from exc
