"""Typed M2.2 scenario construction using only released SchemaWorld Core dynamics."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from unfrozen_schemas.envs.schema_world.actions import Action, ActionKind
from unfrozen_schemas.envs.schema_world.dynamics import transition
from unfrozen_schemas.envs.schema_world.relations import derive_relations
from unfrozen_schemas.envs.schema_world.serialization import canonical_hash, primary_observation
from unfrozen_schemas.envs.schema_world.state import (
    Boundary,
    BoundarySide,
    Entity,
    EntityRole,
    Opening,
    Tether,
    WorldState,
)
from unfrozen_schemas.evaluation.literal_hashing import witness_hash
from unfrozen_schemas.evaluation.literal_models import (
    ContainmentScenarioCase,
    LiteralDirection,
    LiteralScenarioSpec,
    LiteralSchema,
    LiteralWitnessRecord,
    SupportScenarioCase,
)


def literal_item_ids(semantic_group_id: str) -> tuple[str, str]:
    return (f"{semantic_group_id}-a", f"{semantic_group_id}-b")


def _flatten(value: Any, path: str = "") -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    if isinstance(value, Mapping):
        flattened: dict[str, Any] = {}
        for key in sorted(value):
            child = f"{path}.{key}" if path else str(key)
            flattened.update(_flatten(value[key], child))
        return flattened
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        flattened = {}
        for index, item in enumerate(value):
            child = f"{path}.{index}" if path else str(index)
            flattened.update(_flatten(item, child))
        if not value:
            flattened[path] = []
        return flattened
    return {path: value}


def difference_paths(left: Any, right: Any) -> tuple[str, ...]:
    left_flat = _flatten(left)
    right_flat = _flatten(right)
    return tuple(
        sorted(
            key
            for key in set(left_flat) | set(right_flat)
            if left_flat.get(key) != right_flat.get(key)
        )
    )


def _containment_position(
    side: BoundarySide, direction: LiteralDirection
) -> tuple[int, int, int, int]:
    orthogonal = 4_800
    if side is BoundarySide.RIGHT:
        return (5_700 if direction is LiteralDirection.EXIT else 6_100, orthogonal, 400, 0)
    if side is BoundarySide.LEFT:
        return (4_100 if direction is LiteralDirection.EXIT else 3_700, orthogonal, -400, 0)
    if side is BoundarySide.TOP:
        return (orthogonal, 5_700 if direction is LiteralDirection.EXIT else 6_100, 0, 400)
    return (orthogonal, 4_100 if direction is LiteralDirection.EXIT else 3_700, 0, -400)


def _containment_states(
    spec: LiteralScenarioSpec,
) -> tuple[WorldState, WorldState, tuple[Action, ...], tuple[Action, ...]]:
    assert spec.side is not None and spec.direction is not None
    object_x, object_y, exit_delta_x, exit_delta_y = _containment_position(
        spec.side, spec.direction
    )
    multiplier = 1 if spec.direction is LiteralDirection.EXIT else -1
    delta_x = exit_delta_x * multiplier
    delta_y = exit_delta_y * multiplier
    entities: list[Entity] = [
        Entity(
            entity_id="e0001",
            role=EntityRole.OBJECT,
            x=object_x,
            y=object_y,
            width=200,
            height=200,
            movable=True,
        ),
        Entity(
            entity_id="e0002",
            role=EntityRole.CONTAINER,
            x=4_000,
            y=4_000,
            width=2_000,
            height=2_000,
        ),
    ]
    if spec.include_distractor:
        entities.append(
            Entity(
                entity_id="e0009",
                role=EntityRole.DISTRACTOR,
                x=1_000,
                y=1_000,
                width=250,
                height=250,
            )
        )
    entities_tuple = tuple(sorted(entities, key=lambda item: item.entity_id))
    boundary_actual = Boundary(
        boundary_id="b0001",
        container_id="e0002",
        thickness=100,
        closed=spec.scenario_case is not ContainmentScenarioCase.FULLY_OPEN_BOUNDARY,
    )
    boundary_counterfactual = boundary_actual.model_copy(update={"closed": True})

    actual_openings: tuple[Opening, ...]
    counterfactual_openings: tuple[Opening, ...]
    if spec.scenario_case is ContainmentScenarioCase.FULLY_OPEN_BOUNDARY:
        actual_openings = ()
        counterfactual_openings = ()
    else:
        actual_span = (4_700, 5_100)
        counterfactual_span = (4_700, 5_100)
        actual_enabled = True
        counterfactual_enabled = True
        if spec.scenario_case is ContainmentScenarioCase.FITTING_OPENING:
            counterfactual_enabled = False
        elif spec.scenario_case is ContainmentScenarioCase.CLOSED_BOUNDARY:
            actual_enabled = False
        elif spec.scenario_case is ContainmentScenarioCase.UNDERSIZED_OPENING:
            actual_span = (4_850, 4_950)
        elif spec.scenario_case is ContainmentScenarioCase.MISALIGNED_OPENING:
            actual_span = (5_200, 5_500)
        actual_openings = (
            Opening(
                opening_id="o0001",
                boundary_id="b0001",
                side=spec.side,
                span_start=actual_span[0],
                span_end=actual_span[1],
                enabled=actual_enabled,
            ),
        )
        counterfactual_openings = (
            Opening(
                opening_id="o0001",
                boundary_id="b0001",
                side=spec.side,
                span_start=counterfactual_span[0],
                span_end=counterfactual_span[1],
                enabled=counterfactual_enabled,
            ),
        )
    common = {
        "gravity_per_step": -100,
        "seed": spec.seed,
        "noise_seed": spec.noise_seed,
        "step_index": 0,
        "max_steps": 4,
        "entities": entities_tuple,
    }
    actual_state = WorldState(
        **common,
        boundaries=(boundary_actual,),
        openings=actual_openings,
    )
    counterfactual_state = WorldState(
        **common,
        boundaries=(boundary_counterfactual,),
        openings=counterfactual_openings,
    )
    action_kind = ActionKind.EXIT if spec.direction is LiteralDirection.EXIT else ActionKind.ENTER
    actions = (
        Action(
            kind=action_kind,
            target_id="e0001",
            delta_x=delta_x,
            delta_y=delta_y,
        ),
    )
    return actual_state, counterfactual_state, actions, actions


def _support_entities(*, platform: str, include_distractor: bool) -> tuple[Entity, ...]:
    platform_position = (4_000, 4_800) if platform == "lower" else (4_200, 5_000)
    entities = [
        Entity(
            entity_id="e0001",
            role=EntityRole.OBJECT,
            x=4_000,
            y=5_000,
            width=200,
            height=200,
            movable=True,
            affected_by_gravity=True,
        ),
        Entity(
            entity_id="e0002",
            role=EntityRole.SUPPORT,
            x=platform_position[0],
            y=platform_position[1],
            width=200,
            height=200,
        ),
        Entity(
            entity_id="e0003",
            role=EntityRole.ANCHOR,
            x=4_050,
            y=5_750,
            width=100,
            height=100,
        ),
    ]
    if include_distractor:
        entities.append(
            Entity(
                entity_id="e0009",
                role=EntityRole.DISTRACTOR,
                x=1_500,
                y=1_500,
                width=200,
                height=200,
            )
        )
    return tuple(sorted(entities, key=lambda item: item.entity_id))


def _support_state(
    spec: LiteralScenarioSpec,
    *,
    platform: str,
    tether: bool,
    tether_load_bearing: bool = True,
) -> WorldState:
    return WorldState(
        gravity_per_step=-100,
        seed=spec.seed,
        noise_seed=spec.noise_seed,
        step_index=0,
        max_steps=4,
        entities=_support_entities(platform=platform, include_distractor=spec.include_distractor),
        tethers=(
            Tether(
                tether_id="t0001",
                object_id="e0001",
                anchor_id="e0003",
                length=700,
                load_bearing=tether_load_bearing,
            ),
        )
        if tether
        else (),
    )


def _support_states(
    spec: LiteralScenarioSpec,
) -> tuple[WorldState, WorldState, tuple[Action, ...], tuple[Action, ...]]:
    case = spec.scenario_case
    assert isinstance(case, SupportScenarioCase)
    if case is SupportScenarioCase.LOWER_SUPPORT_REMOVAL:
        state = _support_state(spec, platform="lower", tether=False)
        return (
            state,
            state,
            (Action(kind=ActionKind.REMOVE_SUPPORT, target_id="e0002"),),
            (Action(kind=ActionKind.NOOP),),
        )
    if case is SupportScenarioCase.LOWER_SUPPORT_NOOP:
        state = _support_state(spec, platform="lower", tether=False)
        return (
            state,
            state,
            (Action(kind=ActionKind.NOOP),),
            (Action(kind=ActionKind.REMOVE_SUPPORT, target_id="e0002"),),
        )
    if case is SupportScenarioCase.SIDE_CONTACT:
        return (
            _support_state(spec, platform="side", tether=False),
            _support_state(spec, platform="lower", tether=False),
            (Action(kind=ActionKind.NOOP),),
            (Action(kind=ActionKind.NOOP),),
        )
    if case is SupportScenarioCase.TETHER_CUT:
        state = _support_state(spec, platform="side", tether=True)
        return (
            state,
            state,
            (Action(kind=ActionKind.CUT_OR_BREAK, target_id="t0001"),),
            (Action(kind=ActionKind.NOOP),),
        )
    if case is SupportScenarioCase.TETHERED_PLATFORM_REMOVAL:
        state = _support_state(spec, platform="side", tether=True)
        return (
            state,
            state,
            (Action(kind=ActionKind.REMOVE_SUPPORT, target_id="e0002"),),
            (Action(kind=ActionKind.DETACH, target_id="t0001"),),
        )
    return (
        _support_state(spec, platform="side", tether=True, tether_load_bearing=False),
        _support_state(spec, platform="side", tether=True, tether_load_bearing=True),
        (Action(kind=ActionKind.NOOP),),
        (Action(kind=ActionKind.NOOP),),
    )


def scenario_plans(
    spec: LiteralScenarioSpec,
) -> tuple[WorldState, WorldState, tuple[Action, ...], tuple[Action, ...]]:
    if spec.schema_identity is LiteralSchema.CONTAINMENT:
        return _containment_states(spec)
    return _support_states(spec)


def _replay(
    initial_state: WorldState, actions: tuple[Action, ...]
) -> tuple[WorldState, tuple[Any, ...], tuple[str, ...], tuple[Any, ...]]:
    state = initial_state
    traces = []
    hashes = []
    relations: tuple[Any, ...] = ()
    for action in actions:
        result = transition(state, action)
        state = result.state
        traces.append(result.trace)
        hashes.append(result.transition_hash)
        relations = derive_relations(state, result.trace)
    return state, tuple(traces), tuple(hashes), tuple(relations)


def derive_outcome_code(
    schema: LiteralSchema, initial_state: WorldState, final_state: WorldState
) -> str:
    before = initial_state.entity("e0001")
    after = final_state.entity("e0001")
    if schema is LiteralSchema.CONTAINMENT:
        return (
            "movement-succeeds"
            if (before.x, before.y) != (after.x, after.y)
            else "movement-blocked"
        )
    return "object-falls" if after.y < before.y else "object-stays"


def correct_option_id_for_outcome(outcome_code: str) -> str:
    return outcome_code


def build_witness(spec: LiteralScenarioSpec) -> LiteralWitnessRecord:
    actual_initial, counterfactual_initial, actual_actions, counterfactual_actions = scenario_plans(
        spec
    )
    actual_final, actual_traces, actual_hashes, actual_relations = _replay(
        actual_initial, actual_actions
    )
    counterfactual_final, counterfactual_traces, counterfactual_hashes, cf_relations = _replay(
        counterfactual_initial, counterfactual_actions
    )
    actual_outcome = derive_outcome_code(spec.schema_identity, actual_initial, actual_final)
    counterfactual_outcome = derive_outcome_code(
        spec.schema_identity, counterfactual_initial, counterfactual_final
    )
    provisional = LiteralWitnessRecord(
        semantic_group_id=spec.semantic_group_id,
        item_ids=literal_item_ids(spec.semantic_group_id),
        schema_identity=spec.schema_identity,
        transfer_level=spec.transfer_level,
        task_family=spec.task_family,
        source_mechanism_family=spec.source_mechanism_family,
        prompt_template_id=spec.prompt_template_id,
        partition=spec.partition,
        seed=spec.seed,
        noise_seed=spec.noise_seed,
        initial_privileged_state=actual_initial,
        counterfactual_initial_privileged_state=counterfactual_initial,
        initial_state_hash=canonical_hash(actual_initial),
        counterfactual_initial_state_hash=canonical_hash(counterfactual_initial),
        initial_observation_hash=canonical_hash(primary_observation(actual_initial)),
        counterfactual_initial_observation_hash=canonical_hash(
            primary_observation(counterfactual_initial)
        ),
        actual_actions=actual_actions,
        counterfactual_actions=counterfactual_actions,
        action_sequence_hash=canonical_hash(actual_actions),
        counterfactual_action_sequence_hash=canonical_hash(counterfactual_actions),
        actual_final_state=actual_final,
        counterfactual_final_state=counterfactual_final,
        actual_transition_traces=actual_traces,
        counterfactual_transition_traces=counterfactual_traces,
        actual_transition_hashes=actual_hashes,
        counterfactual_transition_hashes=counterfactual_hashes,
        actual_relations=actual_relations,
        counterfactual_relations=cf_relations,
        declared_causal_factor=spec.declared_causal_factor,
        declared_non_target_equality_fields=spec.declared_non_target_equality_fields,
        declared_initial_difference_paths=difference_paths(actual_initial, counterfactual_initial),
        declared_action_difference_paths=difference_paths(actual_actions, counterfactual_actions),
        actual_outcome_code=actual_outcome,
        counterfactual_outcome_code=counterfactual_outcome,
        stable_correct_option_id=correct_option_id_for_outcome(actual_outcome),
        witness_sha256="0" * 64,
    )
    return provisional.model_copy(update={"witness_sha256": witness_hash(provisional)})
