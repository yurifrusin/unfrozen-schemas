"""Unit coverage for strict M2.2 literal contracts and independent replay."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from pydantic import ValidationError

from unfrozen_schemas.evaluation.literal_generation import render_literal_prompt
from unfrozen_schemas.evaluation.literal_hashing import (
    partition_plan_hash,
    template_hash,
    witness_hash,
)
from unfrozen_schemas.evaluation.literal_models import (
    LiteralAuthoringManifest,
    LiteralPartitionPlan,
    LiteralScenarioSpec,
    LiteralTransferLevel,
)
from unfrozen_schemas.evaluation.literal_scenarios import build_witness
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


def test_strict_models_reject_unknown_fields_and_illegal_l2_claim(
    literal_authoring: LiteralAuthoringManifest,
) -> None:
    payload = literal_authoring.scenarios[0].model_dump(mode="json")
    payload["unknown_field"] = True
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        LiteralScenarioSpec.model_validate(payload)

    l2 = literal_authoring.scenarios[2].model_dump(mode="json")
    l2["structural_novelty_dimensions"] = ["new-seed-only"]
    with pytest.raises(ValidationError, match="new name or seed alone"):
        LiteralScenarioSpec.model_validate(l2)

    l2["transfer_level"] = "L3"
    with pytest.raises(ValidationError):
        LiteralScenarioSpec.model_validate(l2)


def test_template_rendering_and_hashes_are_deterministic(
    literal_authoring: LiteralAuthoringManifest,
) -> None:
    scenario = literal_authoring.scenarios[0]
    template = next(
        item
        for item in literal_authoring.templates
        if item.template_id == scenario.prompt_template_id
    )
    assert render_literal_prompt(template, scenario) == render_literal_prompt(template, scenario)
    assert template_hash(template) == template_hash(template)
    invalid = template.model_copy(update={"prompt_format": "Fixture {secret_answer}."})
    with pytest.raises(ValueError, match="Unknown private literal-template field"):
        render_literal_prompt(invalid, scenario)


def test_partition_plan_disjointness_and_hashing() -> None:
    plan = LiteralPartitionPlan(
        candidate_version="fixture-v1",
        prospective_adaptation_strata=("adaptation-a",),
        l1_held_out_group_ids=("group-a",),
        l2_novel_template_group_ids=("group-b",),
        l2_novel_configuration_group_ids=(),
        l2_mechanism_transfer_group_ids=(),
        benchmark_reserved_prompt_template_ids=("template-a",),
        benchmark_reserved_semantic_group_ids=("group-a", "group-b"),
        partition_plan_sha256="0" * 64,
    )
    assert partition_plan_hash(plan) == partition_plan_hash(plan)
    payload = plan.model_dump(mode="json")
    payload["l2_novel_template_group_ids"] = ["group-a"]
    payload["benchmark_reserved_semantic_group_ids"] = ["group-a"]
    with pytest.raises(ValidationError, match="disjoint"):
        LiteralPartitionPlan.model_validate(payload)


def test_every_fixture_witness_replays_and_changes_outcome(
    literal_authoring: LiteralAuthoringManifest,
) -> None:
    for scenario in literal_authoring.scenarios:
        witness = build_witness(scenario)
        verify_witness(witness)
        assert witness.actual_outcome_code != witness.counterfactual_outcome_code
        assert witness.witness_sha256 == witness_hash(witness)
        if scenario.transfer_level is LiteralTransferLevel.L2:
            assert scenario.structural_novelty_dimensions


@pytest.mark.parametrize(
    "field,value",
    [
        ("declared_causal_factor", "corrupted-factor"),
        ("declared_non_target_equality_fields", ("corrupted-parity",)),
        ("witness_sha256", "f" * 64),
        ("actual_outcome_code", "corrupted-outcome"),
        ("stable_correct_option_id", "corrupted-option"),
        ("actual_relations", ()),
    ],
)
def test_independent_witness_verifier_rejects_mutations(
    literal_authoring: LiteralAuthoringManifest,
    field: str,
    value: object,
) -> None:
    witness = build_witness(literal_authoring.scenarios[0])
    if field == "actual_relations" and not witness.actual_relations:
        witness = build_witness(literal_authoring.scenarios[4])
    corrupted = witness.model_copy(update={field: value})
    with pytest.raises(ValueError):
        verify_witness(corrupted)


def test_witness_verifier_rejects_state_action_and_final_state_mutations(
    literal_authoring: LiteralAuthoringManifest,
) -> None:
    witness = build_witness(literal_authoring.scenarios[0])
    first_entity = witness.initial_privileged_state.entities[0]
    initial = witness.initial_privileged_state.model_copy(
        update={
            "entities": (
                first_entity.model_copy(update={"x": first_entity.x + 1}),
                *witness.initial_privileged_state.entities[1:],
            )
        }
    )
    final_entity = witness.actual_final_state.entities[0]
    final_state = witness.actual_final_state.model_copy(
        update={
            "entities": (
                final_entity.model_copy(update={"x": final_entity.x + 1}),
                *witness.actual_final_state.entities[1:],
            )
        }
    )
    changed_actual_action = witness.actual_actions[0].model_copy(
        update={"delta_x": witness.actual_actions[0].delta_x + 1}
    )
    changed_counterfactual_action = witness.counterfactual_actions[0].model_copy(
        update={"delta_x": witness.counterfactual_actions[0].delta_x + 1}
    )
    mutations = (
        witness.model_copy(update={"initial_privileged_state": initial}),
        witness.model_copy(update={"actual_actions": (changed_actual_action,)}),
        witness.model_copy(update={"counterfactual_actions": (changed_counterfactual_action,)}),
        witness.model_copy(update={"actual_final_state": final_state}),
    )
    for corrupted in mutations:
        with pytest.raises(ValueError):
            verify_witness(corrupted)


def test_raw_identifier_and_perfect_structural_cue_are_rejected(
    literal_pipeline_source: LoadedLiteralSource,
) -> None:
    loaded = literal_pipeline_source
    first, second = loaded.items[:2]
    visible_first = first.model_visible.model_copy(
        update={"prompt": f"{first.model_visible.prompt} e0001"}
    )
    visible_second = second.model_visible.model_copy(
        update={"prompt": f"{second.model_visible.prompt} e0001"}
    )
    corrupted_items = (
        first.model_copy(update={"model_visible": visible_first}),
        second.model_copy(update={"model_visible": visible_second}),
        *loaded.items[2:],
    )
    with pytest.raises(ValueError, match="raw-entity-id"):
        build_lexical_audit(
            candidate_version=loaded.source_manifest.benchmark_version,
            items=corrupted_items,
            bindings=loaded.item_bindings.bindings,
        )

    binding = loaded.item_bindings.bindings[0]
    cue_binding = binding.model_copy(update={"action_word": "oneoff"})
    with pytest.raises(ValueError, match="action-word-single-answer-class"):
        build_lexical_audit(
            candidate_version=loaded.source_manifest.benchmark_version,
            items=loaded.items,
            bindings=(cue_binding, *loaded.item_bindings.bindings[1:]),
        )


def test_wrong_simulator_reference_is_rejected(
    literal_pipeline_source: LoadedLiteralSource,
) -> None:
    loaded = literal_pipeline_source
    first, second = loaded.items[:2]
    answer = first.private_answer.model_copy(
        update={"simulator_verification_reference": "literal-witness-sha256:" + "0" * 64}
    )
    second_answer = second.private_answer.model_copy(
        update={"simulator_verification_reference": "literal-witness-sha256:" + "0" * 64}
    )
    corrupted = replace(
        loaded,
        items=(
            first.model_copy(update={"private_answer": answer}),
            second.model_copy(update={"private_answer": second_answer}),
            *loaded.items[2:],
        ),
    )
    with pytest.raises(ValueError, match="Simulator verification reference mismatch"):
        validate_loaded_literal_source(corrupted)
