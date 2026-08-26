"""Unit coverage for typed M2.2 authoring, replay, novelty, and cue semantics."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from pydantic import ValidationError

from unfrozen_schemas.envs.schema_world.serialization import canonical_hash, primary_observation
from unfrozen_schemas.evaluation.benchmark_hashing import normalise_source_item
from unfrozen_schemas.evaluation.literal_contracts import (
    intervention_contract,
    render_literal_prompt,
)
from unfrozen_schemas.evaluation.literal_generation import _source_items
from unfrozen_schemas.evaluation.literal_hashing import (
    authoring_snapshot_hash,
    partition_plan_hash,
    template_hash,
    witness_hash,
)
from unfrozen_schemas.evaluation.literal_models import (
    ContainmentScenarioCase,
    LiteralAuditStatus,
    LiteralAuthoringManifest,
    LiteralLexicalCategory,
    LiteralOutcomeCode,
    LiteralPartition,
    LiteralPartitionPlan,
    LiteralScenarioSpec,
    LiteralSchema,
    LiteralTaskFamily,
    LiteralTemplate,
    LiteralTransferLevel,
    LiteralWitnessRecord,
    StructuralNoveltyDimension,
    SupportScenarioCase,
)
from unfrozen_schemas.evaluation.literal_scenarios import (
    build_witness,
    difference_paths,
)
from unfrozen_schemas.evaluation.literal_validation import (
    LoadedLiteralSource,
    build_lexical_audit,
    build_split_audit,
    validate_loaded_literal_source,
    verify_witness,
)


@pytest.fixture
def literal_authoring() -> LiteralAuthoringManifest:
    return LiteralAuthoringManifest.model_validate_json(
        Path("tests/fixtures/literal_benchmark/authoring.json").read_bytes()
    )


def _template(
    authoring: LiteralAuthoringManifest, scenario: LiteralScenarioSpec
) -> LiteralTemplate:
    return next(
        item for item in authoring.templates if item.template_id == scenario.prompt_template_id
    )


def _witnesses(
    authoring: LiteralAuthoringManifest,
) -> dict[str, LiteralWitnessRecord]:
    templates = {item.template_id: item for item in authoring.templates}
    ordered = tuple(sorted(authoring.scenarios, key=lambda item: item.semantic_group_id))
    witnesses = {
        spec.semantic_group_id: build_witness(spec, templates[spec.prompt_template_id])
        for spec in ordered
        if spec.task_family is not LiteralTaskFamily.PHYSICAL_ANALOGY
    }
    for spec in ordered:
        if spec.task_family is LiteralTaskFamily.PHYSICAL_ANALOGY:
            assert spec.analogy_reference_group_id is not None
            witnesses[spec.semantic_group_id] = build_witness(
                spec,
                templates[spec.prompt_template_id],
                analogy_source=witnesses[spec.analogy_reference_group_id],
            )
    return witnesses


def test_generated_items_are_m2_1_snapshot_normalised(
    literal_authoring: LiteralAuthoringManifest,
) -> None:
    first = literal_authoring.scenarios[0].model_copy(
        update={"lexical_cue_annotations": ("z-cue", "a-cue")}
    )
    authoring = literal_authoring.model_copy(
        update={"scenarios": (first, *literal_authoring.scenarios[1:])}
    )
    witness_map = _witnesses(authoring)
    witnesses = tuple(witness_map[key] for key in sorted(witness_map))

    items, _bindings = _source_items(authoring, witnesses)

    assert all(item == normalise_source_item(item) for item in items)


def test_authoring_is_typed_and_rejects_free_causal_prose(
    literal_authoring: LiteralAuthoringManifest,
) -> None:
    scenario = literal_authoring.scenarios[0]
    payload = scenario.model_dump(mode="json")
    for prohibited in (
        "scene_description",
        "actual_action_description",
        "counterfactual_action_description",
        "positive_option_text",
        "negative_option_text",
        "declared_causal_factor",
        "source_mechanism_family",
    ):
        payload[prohibited] = "untrusted prose"
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            LiteralScenarioSpec.model_validate(payload)
        payload.pop(prohibited)

    l2 = next(
        item
        for item in literal_authoring.scenarios
        if item.transfer_level is LiteralTransferLevel.L2
    ).model_dump(mode="json")
    l2["structural_novelty_dimensions"] = ["new-seed-only"]
    with pytest.raises(ValidationError):
        LiteralScenarioSpec.model_validate(l2)


def test_renderer_accepts_only_reconstructed_narrative_facts(
    literal_authoring: LiteralAuthoringManifest,
) -> None:
    scenario = literal_authoring.scenarios[0]
    template = _template(literal_authoring, scenario)
    witness = build_witness(scenario, template)
    first = render_literal_prompt(template, witness.narrative_facts)
    assert first == render_literal_prompt(template, witness.narrative_facts)
    assert template_hash(template) == template_hash(template)
    with pytest.raises(TypeError, match="only LiteralNarrativeFacts"):
        render_literal_prompt(template, scenario)  # type: ignore[arg-type]


def test_all_six_task_family_renderers_have_exact_natural_wording(
    literal_authoring: LiteralAuthoringManifest,
) -> None:
    scenarios = {item.semantic_group_id: item for item in literal_authoring.scenarios}
    source_witnesses = _witnesses(literal_authoring)
    cases = (
        (
            LiteralTaskFamily.DIRECT_OUTCOME,
            "fixture-route-l1-pass",
            LiteralTransferLevel.L1,
            LiteralPartition.L1_HELD_OUT,
            (),
        ),
        (
            LiteralTaskFamily.INTERVENTION_CONSEQUENCE,
            "fixture-route-l1-pass",
            LiteralTransferLevel.L1,
            LiteralPartition.L1_HELD_OUT,
            (),
        ),
        (
            LiteralTaskFamily.MATCHED_COUNTERFACTUAL,
            "fixture-pad-l1-shift",
            LiteralTransferLevel.L1,
            LiteralPartition.L1_HELD_OUT,
            (),
        ),
        (
            LiteralTaskFamily.NOVEL_TEMPLATE,
            "fixture-route-l2-pass",
            LiteralTransferLevel.L2,
            LiteralPartition.L2_NOVEL_TEMPLATE,
            (StructuralNoveltyDimension.PROMPT_TEMPLATE,),
        ),
        (
            LiteralTaskFamily.NOVEL_CONFIGURATION,
            "fixture-route-l2-pass",
            LiteralTransferLevel.L2,
            LiteralPartition.L2_NOVEL_CONFIGURATION,
            (StructuralNoveltyDimension.QUALITATIVE_GEOMETRY,),
        ),
    )
    observed: dict[LiteralTaskFamily, str] = {}
    for family, base_id, level, partition, novelty in cases:
        template_id = f"renderer-{family.name.casefold().replace('_', '-')}"
        scenario = scenarios[base_id].model_copy(
            update={
                "semantic_group_id": template_id,
                "task_family": family,
                "transfer_level": level,
                "partition": partition,
                "prompt_template_id": template_id,
                "structural_novelty_dimensions": novelty,
                "analogy_reference_group_id": None,
            }
        )
        template = LiteralTemplate(
            template_id=template_id,
            task_family=family,
            transfer_level=level,
            vocabulary_mode="literal_physics",
        )
        witness = build_witness(scenario, template)
        observed[family] = render_literal_prompt(template, witness.narrative_facts)

    analogy = scenarios["fixture-link-l2-shift"].model_copy(
        update={
            "semantic_group_id": "renderer-physical-analogy",
            "prompt_template_id": "renderer-physical-analogy",
        }
    )
    analogy_template = LiteralTemplate(
        template_id=analogy.prompt_template_id,
        task_family=analogy.task_family,
        transfer_level=analogy.transfer_level,
        vocabulary_mode="literal_physics",
    )
    assert analogy.analogy_reference_group_id is not None
    analogy_witness = build_witness(
        analogy,
        analogy_template,
        analogy_source=source_witnesses[analogy.analogy_reference_group_id],
    )
    observed[LiteralTaskFamily.PHYSICAL_ANALOGY] = render_literal_prompt(
        analogy_template, analogy_witness.narrative_facts
    )

    assert observed == {
        LiteralTaskFamily.DIRECT_OUTCOME: (
            "Consider the following physical setup. The object begins inside the container and "
            "the perimeter has an enabled opening aligned with and wide enough for the object on "
            "its right side. Then the object moves outward through the right side. Which direct "
            "outcome follows?"
        ),
        LiteralTaskFamily.INTERVENTION_CONSEQUENCE: (
            "Consider the following physical setup. The object begins inside the container and "
            "the perimeter has an enabled opening aligned with and wide enough for the object on "
            "its right side. Now the object moves outward through the right side. Which "
            "consequence "
            "is caused by the intervention?"
        ),
        LiteralTaskFamily.MATCHED_COUNTERFACTUAL: (
            "Consider two otherwise matched physical setups. In the actual setup, a platform is "
            "in lower contact with the object and there is no tether; the lower platform is "
            "removed. In the alternative setup, a platform is in lower contact with the object "
            "and there is no tether; the setup is observed without removing or changing anything. "
            "Which outcome occurs in the actual setup rather than the matched alternative?"
        ),
        LiteralTaskFamily.NOVEL_TEMPLATE: (
            "A physical setup is described as follows: the object begins outside the container and "
            "the relevant perimeter is fully open on its left side. Next, the object moves inward "
            "through the left side. What is the object's outcome?"
        ),
        LiteralTaskFamily.NOVEL_CONFIGURATION: (
            "Consider the following physical setup. The object begins outside the container and "
            "the relevant perimeter is fully open on its left side. After the object moves inward "
            "through the left side, what happens to the object?"
        ),
        LiteralTaskFamily.PHYSICAL_ANALOGY: (
            "In a reference setup, a platform is in lower contact with the object and there is no "
            "tether; when the lower platform is removed, the object moves downward. Apply the same "
            "causal pattern to another setup: a platform touches the object's side without lower "
            "contact and a taut load-bearing tether connects the object to an upper anchor; then "
            "the tether is cut. What happens to the object?"
        ),
    }


def test_partition_plan_disjointness_and_hashing(
    literal_pipeline_source: LoadedLiteralSource,
) -> None:
    plan = literal_pipeline_source.partition_plan
    assert partition_plan_hash(plan) == plan.partition_plan_sha256
    payload = plan.model_dump(mode="json")
    duplicate = payload["l1_held_out_group_ids"][0]
    payload["l2_novel_configuration_group_ids"][0] = duplicate
    with pytest.raises(ValidationError, match="disjoint"):
        LiteralPartitionPlan.model_validate(payload)


def test_every_fixture_witness_replays_and_changes_outcome(
    literal_authoring: LiteralAuthoringManifest,
) -> None:
    witness_map = _witnesses(literal_authoring)
    for scenario in literal_authoring.scenarios:
        template = _template(literal_authoring, scenario)
        witness = witness_map[scenario.semantic_group_id]
        source = (
            witness_map[scenario.analogy_reference_group_id]
            if scenario.analogy_reference_group_id is not None
            else None
        )
        verify_witness(witness, scenario, template, analogy_source=source)
        assert witness.actual_outcome_code != witness.counterfactual_outcome_code
        assert witness.witness_sha256 == witness_hash(witness)
        assert witness.intervention_kind is scenario.intervention_kind
        if scenario.transfer_level is LiteralTransferLevel.L2:
            assert scenario.structural_novelty_dimensions


@pytest.mark.parametrize(
    "scenario_case",
    (
        "fitting-opening",
        "closed-boundary",
        "undersized-opening",
        "misaligned-opening",
        "fully-open-boundary",
        "lower-support-removal",
        "lower-support-noop",
        "side-contact",
        "tether-cut",
        "tethered-platform-removal",
        "nonbearing-tether",
    ),
)
def test_every_intervention_family_rejects_extra_seed_difference_with_refreshed_hashes(
    literal_authoring: LiteralAuthoringManifest,
    scenario_case: str,
) -> None:
    existing = next(
        (item for item in literal_authoring.scenarios if item.scenario_case.value == scenario_case),
        None,
    )
    if existing is None:
        case = (
            ContainmentScenarioCase(scenario_case)
            if scenario_case in {item.value for item in ContainmentScenarioCase}
            else SupportScenarioCase(scenario_case)
        )
        base = next(
            item
            for item in literal_authoring.scenarios
            if item.schema_identity
            is (
                LiteralSchema.CONTAINMENT
                if isinstance(case, ContainmentScenarioCase)
                else LiteralSchema.SUPPORT
            )
        )
        scenario = base.model_copy(
            update={
                "semantic_group_id": f"mutation-{scenario_case}",
                "scenario_case": case,
                "intervention_kind": intervention_contract(case).intervention_kind,
                "scene_name": "Mutation Fixture Scene",
            }
        )
    else:
        scenario = existing
    template = _template(literal_authoring, scenario)
    source = None
    if scenario.analogy_reference_group_id is not None:
        source = _witnesses(literal_authoring)[scenario.analogy_reference_group_id]
    witness = build_witness(scenario, template, analogy_source=source)
    changed_state = witness.initial_privileged_state.model_copy(
        update={"noise_seed": witness.initial_privileged_state.noise_seed + 1}
    )
    observed = difference_paths(changed_state, witness.counterfactual_initial_privileged_state)
    provisional = witness.model_copy(
        update={
            "initial_privileged_state": changed_state,
            "initial_state_hash": canonical_hash(changed_state),
            "initial_observation_hash": canonical_hash(primary_observation(changed_state)),
            "observed_initial_difference_paths": observed,
            "witness_sha256": "0" * 64,
        }
    )
    corrupted = provisional.model_copy(update={"witness_sha256": witness_hash(provisional)})
    with pytest.raises(ValueError, match="prospective contract"):
        verify_witness(corrupted, scenario, template, analogy_source=source)


def test_seed_scene_and_option_nouns_do_not_create_a_new_causal_scenario(
    literal_authoring: LiteralAuthoringManifest,
) -> None:
    scenario = literal_authoring.scenarios[0]
    template = _template(literal_authoring, scenario)
    original = build_witness(scenario, template)
    changed_scenario = scenario.model_copy(
        update={
            "seed": scenario.seed + 10_000,
            "noise_seed": scenario.noise_seed + 10_000,
            "scene_name": "Changed Private Scene",
        }
    )
    changed = build_witness(changed_scenario, template)
    assert (
        original.structural_signatures.causal_scenario_sha256
        == changed.structural_signatures.causal_scenario_sha256
    )
    assert (
        original.structural_signatures.structural_stratum_sha256
        == changed.structural_signatures.structural_stratum_sha256
    )
    assert render_literal_prompt(template, original.narrative_facts) == render_literal_prompt(
        template, changed.narrative_facts
    )
    changed_registry = tuple(
        record.model_copy(update={"text": record.text.replace("result", "response")})
        if record.text_id in scenario.outcome_text_record_ids
        else record
        for record in literal_authoring.outcome_text_registry
    )
    changed_authoring = literal_authoring.model_copy(
        update={"outcome_text_registry": changed_registry}
    )
    _, original_bindings = _source_items(
        literal_authoring, tuple(_witnesses(literal_authoring).values())
    )
    _, changed_bindings = _source_items(
        changed_authoring, tuple(_witnesses(changed_authoring).values())
    )
    assert {
        binding.structural_signatures.causal_scenario_sha256 for binding in original_bindings
    } == {binding.structural_signatures.causal_scenario_sha256 for binding in changed_bindings}


def test_option_semantics_drift_is_rejected_after_refreshing_snapshot_root(
    literal_pipeline_source: LoadedLiteralSource,
) -> None:
    loaded = literal_pipeline_source
    first_spec = loaded.authoring_snapshot.scenarios[0]
    selected = set(first_spec.outcome_text_record_ids)
    registry = []
    for record in loaded.authoring_snapshot.outcome_text_registry:
        if record.text_id not in selected:
            registry.append(record)
        elif record.outcome_code is LiteralOutcomeCode.MOVEMENT_SUCCEEDS:
            registry.append(
                record.model_copy(update={"outcome_code": LiteralOutcomeCode.MOVEMENT_BLOCKED})
            )
        else:
            registry.append(
                record.model_copy(update={"outcome_code": LiteralOutcomeCode.MOVEMENT_SUCCEEDS})
            )
    snapshot = loaded.authoring_snapshot.model_copy(
        update={"outcome_text_registry": tuple(registry)}
    )
    source_bundle = loaded.source_bundle.model_copy(
        update={"authoring_snapshot_sha256": authoring_snapshot_hash(snapshot)}
    )
    corrupted = replace(
        loaded,
        authoring_snapshot=snapshot,
        source_bundle=source_bundle,
    )
    with pytest.raises(ValueError, match="Typed narrative/source item mismatch"):
        validate_loaded_literal_source(corrupted)


def test_source_snapshot_binding_witness_reconciliation_rejects_orphans(
    literal_pipeline_source: LoadedLiteralSource,
) -> None:
    loaded = literal_pipeline_source
    corrupted = replace(
        loaded,
        item_bindings=loaded.item_bindings.model_copy(
            update={"bindings": loaded.item_bindings.bindings[1:]}
        ),
    )
    with pytest.raises(ValueError, match="exactly two items and one witness per group"):
        validate_loaded_literal_source(corrupted)


def test_split_has_exact_l1_l2_separation_and_structural_novelty(
    literal_pipeline_source: LoadedLiteralSource,
) -> None:
    loaded = literal_pipeline_source
    bindings = loaded.item_bindings.bindings
    l1 = [item for item in bindings if item.transfer_level is LiteralTransferLevel.L1]
    l2 = [item for item in bindings if item.transfer_level is LiteralTransferLevel.L2]
    assert {item.semantic_group_id for item in l1}.isdisjoint(item.semantic_group_id for item in l2)
    l1_configurations = {item.structural_signatures.configuration_sha256 for item in l1}
    for item in l2:
        if item.partition is LiteralPartition.L2_NOVEL_CONFIGURATION:
            assert item.structural_signatures.configuration_sha256 not in l1_configurations


def test_mechanism_transfer_compares_every_l1_and_prospective_source(
    literal_pipeline_source: LoadedLiteralSource,
) -> None:
    loaded = literal_pipeline_source
    bindings = loaded.item_bindings.bindings
    l1_signatures = {
        binding.structural_signatures.target_mechanism_sha256
        for binding in bindings
        if binding.transfer_level is LiteralTransferLevel.L1
    }
    assert l1_signatures == set(loaded.partition_plan.prohibited_l1_source_mechanism_signatures)
    incomplete = loaded.partition_plan.model_copy(
        update={
            "prohibited_l1_source_mechanism_signatures": tuple(sorted(l1_signatures))[1:],
            "prohibited_mechanism_transfer_target_signatures": tuple(
                sorted(
                    set(tuple(sorted(l1_signatures))[1:])
                    | set(loaded.partition_plan.prospective_adaptation_source_mechanism_signatures)
                )
            ),
        }
    )
    with pytest.raises(ValueError, match="complete L1 mechanism-source set"):
        build_split_audit(
            candidate_version=loaded.source_manifest.benchmark_version,
            items=loaded.items,
            bindings=bindings,
            witnesses=loaded.witness_bundle.witnesses,
            partition_plan=incomplete,
        )

    transfer = next(
        binding for binding in bindings if binding.task_family is LiteralTaskFamily.PHYSICAL_ANALOGY
    )
    prospective = tuple(
        sorted(
            {
                *loaded.partition_plan.prospective_adaptation_source_mechanism_signatures,
                transfer.structural_signatures.target_mechanism_sha256,
            }
        )
    )
    coordinated = loaded.partition_plan.model_copy(
        update={
            "prospective_adaptation_source_mechanism_signatures": prospective,
            "prohibited_mechanism_transfer_target_signatures": tuple(
                sorted(l1_signatures | set(prospective))
            ),
        }
    )
    with pytest.raises(ValueError, match="represented in prohibited source material"):
        build_split_audit(
            candidate_version=loaded.source_manifest.benchmark_version,
            items=loaded.items,
            bindings=bindings,
            witnesses=loaded.witness_bundle.witnesses,
            partition_plan=coordinated,
        )


def test_split_reports_questions_scenarios_strata_and_noncosmetic_variants(
    literal_pipeline_source: LoadedLiteralSource,
) -> None:
    audit = literal_pipeline_source.split_audit
    assert audit.question_group_count == 8
    assert audit.causal_scenario_count == 8
    assert audit.independent_structural_stratum_count == 8
    assert audit.matched_variant_count == 0
    assert audit.cosmetic_variant_count == 0
    assert len(audit.causal_scenario_groups) == audit.causal_scenario_count
    assert len(audit.structural_signature_strata) == (audit.independent_structural_stratum_count)


def test_exact_prompt_duplicates_require_declared_cosmetic_variant_identity(
    literal_pipeline_source: LoadedLiteralSource,
) -> None:
    loaded = literal_pipeline_source
    left = loaded.item_bindings.bindings[0]
    right = next(
        binding
        for binding in loaded.item_bindings.bindings[1:]
        if binding.task_family is left.task_family
    )
    matched_stratum_id = "test-declared-cosmetic-variant"
    updated_bindings = tuple(
        binding.model_copy(
            update={
                "matched_stratum_id": matched_stratum_id,
                "structural_signatures": binding.structural_signatures.model_copy(
                    update={
                        "causal_scenario_sha256": (
                            left.structural_signatures.causal_scenario_sha256
                        )
                    }
                ),
            }
        )
        if binding.semantic_group_id in {left.semantic_group_id, right.semantic_group_id}
        else binding
        for binding in loaded.item_bindings.bindings
    )
    source_prompt = next(
        item.model_visible.prompt for item in loaded.items if item.item_id == left.item_ids[0]
    )
    updated_items = tuple(
        item.model_copy(
            update={
                "model_visible": item.model_visible.model_copy(update={"prompt": source_prompt})
            }
        )
        if item.item_id in right.item_ids
        else item
        for item in loaded.items
    )

    lexical = build_lexical_audit(
        candidate_version=loaded.source_manifest.benchmark_version,
        items=updated_items,
        bindings=updated_bindings,
    )
    exact = [
        finding for finding in lexical.findings if finding.finding_kind == "exact-prompt-duplicate"
    ]
    assert len(exact) == 1
    assert exact[0].disposition is LiteralAuditStatus.OWNER_REVIEW_REQUIRED
    assert exact[0].occurrence_support == 2
    split = build_split_audit(
        candidate_version=loaded.source_manifest.benchmark_version,
        items=updated_items,
        bindings=updated_bindings,
        witnesses=loaded.witness_bundle.witnesses,
        partition_plan=loaded.partition_plan,
    )
    assert split.exact_prompt_duplicate_count == 1
    assert split.cosmetic_variant_count == 1

    with pytest.raises(ValueError, match="declared variants of one causal scenario"):
        build_split_audit(
            candidate_version=loaded.source_manifest.benchmark_version,
            items=updated_items,
            bindings=loaded.item_bindings.bindings,
            witnesses=loaded.witness_bundle.witnesses,
            partition_plan=loaded.partition_plan,
        )


def test_lexical_findings_remain_owner_review_required(
    literal_pipeline_source: LoadedLiteralSource,
) -> None:
    loaded = literal_pipeline_source
    audit = build_lexical_audit(
        candidate_version=loaded.source_manifest.benchmark_version,
        items=loaded.items,
        bindings=loaded.item_bindings.bindings,
    )
    assert audit.status is LiteralAuditStatus.OWNER_REVIEW_REQUIRED
    assert audit.unresolved_owner_review_finding_count > 0
    assert audit.causal_term_allowlist
    assert audit.prompt_length_by_answer_class
    assert audit.option_length_by_answer_class
    assert audit.distractor_option_length_by_answer_class
    assert audit.option_style_by_answer_class
    assert audit.tokenizer_specific_length_check_status == "pending_m2_4"
    assert all(
        finding.occurrence_support >= finding.semantic_group_support for finding in audit.findings
    )
    assert all(finding.answer_class_counts for finding in audit.findings)
    assert all(finding.semantic_group_ids and finding.item_ids for finding in audit.findings)
    assert all(
        finding.disposition is not LiteralAuditStatus.OWNER_REVIEW_REQUIRED
        for finding in audit.findings
        if finding.semantic_group_support == 1
    )
    assert {summary.category for summary in audit.category_summaries} == set(LiteralLexicalCategory)
    assert all(
        summary.finding_count == len(summary.finding_ids) for summary in audit.category_summaries
    )

    first, second = loaded.items[:2]
    corrupted_items = (
        first.model_copy(
            update={
                "model_visible": first.model_visible.model_copy(
                    update={"prompt": f"{first.model_visible.prompt} e0001"}
                )
            }
        ),
        second.model_copy(
            update={
                "model_visible": second.model_visible.model_copy(
                    update={"prompt": f"{second.model_visible.prompt} e0001"}
                )
            }
        ),
        *loaded.items[2:],
    )
    with pytest.raises(ValueError, match="raw-entity-id"):
        build_lexical_audit(
            candidate_version=loaded.source_manifest.benchmark_version,
            items=corrupted_items,
            bindings=loaded.item_bindings.bindings,
        )


def test_option_forms_are_parallel_and_length_is_not_answer_deterministic(
    literal_pipeline_source: LoadedLiteralSource,
) -> None:
    items = {item.item_id: item for item in literal_pipeline_source.items}
    lengths_by_answer: dict[str, set[int]] = {}
    modal = {"may", "might", "must", "will", "would", "could", "should"}
    for binding in literal_pipeline_source.item_bindings.bindings:
        item = items[binding.item_ids[0]]
        options = item.model_visible.ordered_options
        lengths = {option.option_id: len(option.text.split()) for option in options}
        assert max(lengths.values()) - min(lengths.values()) <= 1
        assert all(option.text.startswith("The object ") for option in options)
        assert all(option.text.endswith(".") for option in options)
        assert all(not (set(option.text.casefold().split()) & modal) for option in options)
        assert len({option.text.count(".") for option in options}) == 1
        lengths_by_answer.setdefault(binding.stable_correct_option_id, set()).add(
            lengths[binding.stable_correct_option_id]
        )
    assert lengths_by_answer["movement-succeeds"] & lengths_by_answer["movement-blocked"]
    assert lengths_by_answer["object-falls"] & lengths_by_answer["object-stays"]
