"""M1.1 state, action, generator, observation, and serialization contracts."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from unfrozen_schemas.envs.schema_world.actions import (
    ACTION_PARAMETER_MATRIX,
    Action,
    ActionKind,
    validate_action,
)
from unfrozen_schemas.envs.schema_world.environment import SchemaWorld
from unfrozen_schemas.envs.schema_world.events import DelayedEvent, DelayedEventKind
from unfrozen_schemas.envs.schema_world.protocol import IllegalActionError, UnsupportedActionError
from unfrozen_schemas.envs.schema_world.relation_kinds import RelationKind
from unfrozen_schemas.envs.schema_world.rng import DeterministicGenerator
from unfrozen_schemas.envs.schema_world.serialization import (
    BOUNDARY_SIDE_CODES,
    ENTITY_KIND_CODES,
    FORBIDDEN_RELATION_LABELS,
    assert_relation_labels_absent,
    canonical_hash,
    canonical_record_bytes,
    primary_observation,
)
from unfrozen_schemas.envs.schema_world.state import (
    Attachment,
    Boundary,
    BoundarySide,
    Entity,
    EntityRole,
    Opening,
    Tether,
    WorldState,
)
from unfrozen_schemas.envs.schema_world.templates import TemplateFamily


def _state() -> WorldState:
    return WorldState(
        gravity_per_step=-100,
        seed=7,
        noise_seed=11,
        step_index=0,
        max_steps=5,
        entities=(
            Entity(
                entity_id="e0001",
                role=EntityRole.OBJECT,
                x=400,
                y=400,
                width=100,
                height=100,
                movable=True,
                affected_by_gravity=True,
            ),
            Entity(
                entity_id="e0002",
                role=EntityRole.CONTAINER,
                x=100,
                y=100,
                width=800,
                height=800,
            ),
            Entity(
                entity_id="e0003",
                role=EntityRole.GATE,
                x=880,
                y=350,
                width=20,
                height=300,
            ),
        ),
        boundaries=(Boundary(boundary_id="b0001", container_id="e0002", thickness=20),),
        openings=(
            Opening(
                opening_id="o0001",
                boundary_id="b0001",
                side=BoundarySide.RIGHT,
                span_start=350,
                span_end=650,
                gate_id="e0003",
            ),
        ),
    )


def _full_graph_state(*, delayed_events: tuple[DelayedEvent, ...] = ()) -> WorldState:
    return WorldState(
        gravity_per_step=-100,
        seed=7,
        noise_seed=11,
        step_index=0,
        max_steps=5,
        entities=(
            Entity(
                entity_id="e0001",
                role=EntityRole.OBJECT,
                x=400,
                y=500,
                width=200,
                height=200,
                movable=True,
                affected_by_gravity=True,
            ),
            Entity(
                entity_id="e0002",
                role=EntityRole.ANCHOR,
                x=450,
                y=900,
                width=100,
                height=100,
            ),
            Entity(
                entity_id="e0003",
                role=EntityRole.CONTAINER,
                x=1000,
                y=100,
                width=800,
                height=800,
            ),
            Entity(
                entity_id="e0004",
                role=EntityRole.GATE,
                x=1780,
                y=350,
                width=20,
                height=300,
            ),
        ),
        boundaries=(Boundary(boundary_id="b0001", container_id="e0003", thickness=20),),
        openings=(
            Opening(
                opening_id="o0001",
                boundary_id="b0001",
                side=BoundarySide.RIGHT,
                span_start=350,
                span_end=650,
                gate_id="e0004",
            ),
        ),
        attachments=(
            Attachment(
                attachment_id="a0001",
                object_id="e0001",
                anchor_id="e0002",
            ),
        ),
        tethers=(
            Tether(
                tether_id="t0001",
                object_id="e0001",
                anchor_id="e0002",
                length=350,
            ),
        ),
        delayed_events=delayed_events,
    )


def test_world_state_is_immutable_and_validates_bounds_and_stable_ids() -> None:
    state = _state()
    with pytest.raises(ValidationError, match="frozen"):
        state.step_index = 1  # type: ignore[misc]
    with pytest.raises(ValidationError, match="string_pattern_mismatch"):
        Entity(
            entity_id="object",
            role=EntityRole.OBJECT,
            x=0,
            y=0,
            width=1,
            height=1,
        )
    with pytest.raises(ValidationError, match="global coordinate bounds"):
        Entity(
            entity_id="e9999",
            role=EntityRole.OBJECT,
            x=9_999,
            y=0,
            width=2,
            height=1,
        )


def test_state_rejects_unstable_order_duplicate_ids_and_bad_event_priority() -> None:
    state = _state()
    with pytest.raises(ValidationError, match="stable entity_id ordering"):
        WorldState(**{**state.model_dump(), "entities": tuple(reversed(state.entities))})
    with pytest.raises(ValidationError, match="globally unique"):
        WorldState(**{**state.model_dump(), "entities": (*state.entities, state.entities[0])})
    with pytest.raises(ValidationError, match="must be 30"):
        DelayedEvent(
            event_id="v0001",
            due_step=1,
            priority=99,
            insertion_order=0,
            kind=DelayedEventKind.DISABLE_ENTITY,
            target_id="e0001",
        )


def test_state_graph_rejects_bad_opening_geometry_and_delayed_event_target_types() -> None:
    state = _state()
    out_of_side_span = state.openings[0].model_copy(update={"span_start": 110, "gate_id": None})
    with pytest.raises(ValidationError, match="container side"):
        WorldState.model_validate({**state.model_dump(), "openings": (out_of_side_span,)})

    shifted_gate = state.entity("e0003").model_copy(update={"x": 879})
    with pytest.raises(ValidationError, match="gate geometry"):
        WorldState.model_validate(
            {**state.model_dump(), "entities": (*state.entities[:2], shifted_gate)}
        )

    wrong_target_type = DelayedEvent(
        event_id="v0001",
        due_step=1,
        priority=40,
        insertion_order=0,
        kind=DelayedEventKind.ENABLE_OPENING,
        target_id="e0001",
    )
    with pytest.raises(ValidationError, match="existing opening"):
        WorldState.model_validate({**state.model_dump(), "delayed_events": (wrong_target_type,)})


@pytest.mark.parametrize(
    ("kind", "target_id", "wrong_target_id"),
    [
        (DelayedEventKind.DISABLE_ATTACHMENT, "a0001", "e0001"),
        (DelayedEventKind.DISABLE_TETHER, "t0001", "e0001"),
        (DelayedEventKind.DISABLE_ENTITY, "e0001", "o0001"),
        (DelayedEventKind.ENABLE_OPENING, "o0001", "e0001"),
    ],
)
def test_every_delayed_event_kind_requires_its_exact_target_type(
    kind: DelayedEventKind, target_id: str, wrong_target_id: str
) -> None:
    priority = {
        DelayedEventKind.DISABLE_ATTACHMENT: 10,
        DelayedEventKind.DISABLE_TETHER: 20,
        DelayedEventKind.DISABLE_ENTITY: 30,
        DelayedEventKind.ENABLE_OPENING: 40,
    }[kind]
    valid = DelayedEvent(
        event_id="v0001",
        due_step=1,
        priority=priority,
        insertion_order=0,
        kind=kind,
        target_id=target_id,
    )
    assert _full_graph_state(delayed_events=(valid,)).delayed_events == (valid,)

    wrong = valid.model_copy(update={"target_id": wrong_target_id})
    with pytest.raises(ValidationError, match="Delayed event"):
        _full_graph_state(delayed_events=(wrong,))


def test_active_connections_require_active_role_correct_endpoints() -> None:
    state = _full_graph_state()
    inactive_anchor = state.entity("e0002").model_copy(update={"active": False})
    with pytest.raises(ValidationError, match="active attachment requires active endpoints"):
        WorldState.model_validate(
            {
                **state.model_dump(),
                "entities": (state.entities[0], inactive_anchor, *state.entities[2:]),
            }
        )

    with pytest.raises(ValidationError, match="active tether requires active endpoints"):
        WorldState.model_validate(
            {
                **state.model_dump(),
                "entities": (state.entities[0], inactive_anchor, *state.entities[2:]),
                "attachments": (state.attachments[0].model_copy(update={"active": False}),),
            }
        )

    wrong_object = state.attachments[0].model_copy(update={"object_id": "e0004"})
    with pytest.raises(ValidationError, match="object and an anchor"):
        WorldState.model_validate({**state.model_dump(), "attachments": (wrong_object,)})

    wrong_tether_object = state.tethers[0].model_copy(update={"object_id": "e0004"})
    with pytest.raises(ValidationError, match="object and an anchor"):
        WorldState.model_validate({**state.model_dump(), "tethers": (wrong_tether_object,)})


def test_actions_distinguish_illegal_and_unsupported_from_noop() -> None:
    state = _state()
    validate_action(state, Action(kind=ActionKind.NOOP))
    with pytest.raises(UnsupportedActionError, match="prospectively"):
        validate_action(
            state,
            Action(kind=ActionKind.GRASP, actor_id="e0003", target_id="e0001"),
        )
    with pytest.raises(IllegalActionError, match="Unknown movement target"):
        validate_action(
            state,
            Action(kind=ActionKind.MOVE, target_id="e9999", delta_x=100),
        )
    with pytest.raises(ValidationError, match="exactly one non-zero axis"):
        Action(kind=ActionKind.EXIT, target_id="e0001")


_VALID_ACTION_PAYLOADS: dict[ActionKind, dict[str, str | int]] = {
    ActionKind.MOVE: {"target_id": "e0001", "delta_x": 1},
    ActionKind.ROTATE: {"target_id": "e0001", "magnitude": 1},
    ActionKind.GRASP: {"actor_id": "e0003", "target_id": "e0001"},
    ActionKind.RELEASE: {"actor_id": "e0003", "target_id": "e0001"},
    ActionKind.PUSH: {"actor_id": "e0003", "target_id": "e0001", "magnitude": 1},
    ActionKind.PULL: {"actor_id": "e0003", "target_id": "e0001", "magnitude": 1},
    ActionKind.LIFT: {"actor_id": "e0003", "target_id": "e0001", "magnitude": 1},
    ActionKind.LOWER: {"actor_id": "e0003", "target_id": "e0001", "magnitude": 1},
    ActionKind.OPEN: {"target_id": "o0001"},
    ActionKind.CLOSE: {"target_id": "o0001"},
    ActionKind.ATTACH: {"actor_id": "e0003", "target_id": "e0001"},
    ActionKind.DETACH: {"target_id": "t0001"},
    ActionKind.CUT_OR_BREAK: {"target_id": "t0001"},
    ActionKind.WAIT: {},
    ActionKind.PROBE_FORCE: {
        "actor_id": "e0003",
        "target_id": "e0001",
        "magnitude": 1,
    },
    ActionKind.NOOP: {},
    ActionKind.ENTER: {"target_id": "e0001", "delta_x": -1},
    ActionKind.EXIT: {"target_id": "e0001", "delta_x": 1},
    ActionKind.OPEN_GATE: {"target_id": "o0001"},
    ActionKind.CLOSE_GATE: {"target_id": "o0001"},
    ActionKind.REMOVE_SUPPORT: {"target_id": "e0002"},
}


@pytest.mark.parametrize("kind", list(ActionKind))
def test_every_action_kind_has_one_strict_canonical_parameter_shape(kind: ActionKind) -> None:
    assert set(ACTION_PARAMETER_MATRIX) == set(ActionKind)
    valid = _VALID_ACTION_PAYLOADS[kind]
    assert Action(kind=kind, **valid).kind is kind

    for field in ACTION_PARAMETER_MATRIX[kind].required:
        missing_required = dict(valid)
        missing_required.pop(field)
        with pytest.raises(ValidationError):
            Action(kind=kind, **missing_required)

    non_default_values: dict[str, str | int] = {
        "actor_id": "e0003",
        "target_id": "e0001",
        "delta_x": 1,
        "delta_y": 1,
        "magnitude": 1,
    }
    for unused_field in non_default_values.keys() - ACTION_PARAMETER_MATRIX[kind].allowed:
        with pytest.raises(ValidationError, match="rejects unused action fields"):
            Action(
                kind=kind,
                **{**valid, unused_field: non_default_values[unused_field]},
            )


@pytest.mark.parametrize("kind", [ActionKind.MOVE, ActionKind.ENTER, ActionKind.EXIT])
def test_movement_actions_reject_diagonal_deltas(kind: ActionKind) -> None:
    with pytest.raises(ValidationError, match="exactly one non-zero axis"):
        Action(kind=kind, target_id="e0001", delta_x=1, delta_y=1)


@pytest.mark.parametrize(
    "kind",
    [
        ActionKind.ROTATE,
        ActionKind.PUSH,
        ActionKind.PULL,
        ActionKind.LIFT,
        ActionKind.LOWER,
        ActionKind.PROBE_FORCE,
    ],
)
def test_magnitude_bearing_actions_reject_zero(kind: ActionKind) -> None:
    payload = {**_VALID_ACTION_PAYLOADS[kind], "magnitude": 0}
    with pytest.raises(ValidationError, match="positive magnitude"):
        Action(kind=kind, **payload)


def test_splitmix64_is_explicit_isolated_and_repeatable() -> None:
    left = DeterministicGenerator(123)
    right = DeterministicGenerator(123)
    assert left.identity == "splitmix64-v1"
    assert [left.next_u64() for _ in range(5)] == [right.next_u64() for _ in range(5)]
    assert DeterministicGenerator(0).next_u64() == 16_294_208_416_658_607_535
    assert [DeterministicGenerator(seed).randint(2, 9) for seed in range(4)] == [9, 3, 8, 7]


def test_primary_observation_excludes_privileged_roles_and_relation_labels() -> None:
    observation = primary_observation(_state())
    payload = canonical_record_bytes(observation).decode("utf-8")
    for role in EntityRole:
        assert role.value not in payload
    upper = payload.upper()
    assert not any(label in upper for label in FORBIDDEN_RELATION_LABELS)


@pytest.mark.parametrize("relation", list(RelationKind))
def test_every_privileged_relation_name_is_rejected_from_primary_payloads(
    relation: RelationKind,
) -> None:
    with pytest.raises(ValueError, match="forbidden relation labels"):
        assert_relation_labels_absent({"untrusted_sensor_field": relation.value})


def test_observation_numeric_codes_are_explicit_and_canonical() -> None:
    assert ENTITY_KIND_CODES == {
        EntityRole.AGENT: 1,
        EntityRole.OBJECT: 2,
        EntityRole.CONTAINER: 3,
        EntityRole.GATE: 4,
        EntityRole.SUPPORT: 5,
        EntityRole.ANCHOR: 6,
        EntityRole.DISTRACTOR: 7,
    }
    assert BOUNDARY_SIDE_CODES == {
        BoundarySide.LEFT: 1,
        BoundarySide.RIGHT: 2,
        BoundarySide.BOTTOM: 3,
        BoundarySide.TOP: 4,
    }


def test_canonical_hash_ignores_mapping_insertion_order() -> None:
    left = {"b": [2, 3], "a": 1}
    right = {"a": 1, "b": [2, 3]}
    assert canonical_record_bytes(left) == b'{"a":1,"b":[2,3]}\n'
    assert canonical_hash(left) == canonical_hash(right)


def test_gymnasium_style_reset_and_step_are_typed_and_deterministic() -> None:
    environment = SchemaWorld(TemplateFamily.CONTAINMENT_GATE, condition_index=0, max_steps=1)
    left = environment.reset(seed=17, noise_seed=18)
    right = environment.reset(seed=17, noise_seed=18)
    assert left == right
    result = environment.step(Action(kind=ActionKind.NOOP))
    assert result.reward == 0
    assert result.terminated is False
    assert result.truncated is True
    assert result.privileged_state.terminated is True
