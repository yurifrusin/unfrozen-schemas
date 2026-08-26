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
    LiteralOutcomeCode,
    LiteralPartition,
    LiteralPartitionPlan,
    LiteralScenarioSpec,
    LiteralSchema,
    LiteralTemplate,
    LiteralTransferLevel,
    SupportScenarioCase,
)
from unfrozen_schemas.evaluation.literal_scenarios import (
    build_witness,
    difference_paths,
)
from unfrozen_schemas.evaluation.literal_validation import (
    LoadedLiteralSource,
    build_lexical_audit,
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


def test_generated_items_are_m2_1_snapshot_normalised(
    literal_authoring: LiteralAuthoringManifest,
) -> None:
    first = literal_authoring.scenarios[0].model_copy(
        update={"lexical_cue_annotations": ("z-cue", "a-cue")}
    )
    authoring = literal_authoring.model_copy(
        update={"scenarios": (first, *literal_authoring.scenarios[1:])}
    )
    templates = {item.template_id: item for item in authoring.templates}
    witnesses = tuple(
        build_witness(spec, templates[spec.prompt_template_id])
        for spec in sorted(authoring.scenarios, key=lambda item: item.semantic_group_id)
    )

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
    for scenario in literal_authoring.scenarios:
        template = _template(literal_authoring, scenario)
        witness = build_witness(scenario, template)
        verify_witness(witness, scenario, template)
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
    witness = build_witness(scenario, template)
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
        verify_witness(corrupted, scenario, template)


def test_snapshot_scene_drift_is_rejected_after_refreshing_snapshot_root(
    literal_pipeline_source: LoadedLiteralSource,
) -> None:
    loaded = literal_pipeline_source
    scenarios = list(loaded.authoring_snapshot.scenarios)
    scenarios[0] = scenarios[0].model_copy(update={"scene_name": "Changed Fixture Scene"})
    snapshot = loaded.authoring_snapshot.model_copy(update={"scenarios": tuple(scenarios)})
    source_bundle = loaded.source_bundle.model_copy(
        update={"authoring_snapshot_sha256": authoring_snapshot_hash(snapshot)}
    )
    corrupted = replace(
        loaded,
        authoring_snapshot=snapshot,
        source_bundle=source_bundle,
    )
    with pytest.raises(ValueError, match="Typed narrative facts do not reconstruct"):
        validate_loaded_literal_source(corrupted)


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
    assert audit.option_style_by_answer_class

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
