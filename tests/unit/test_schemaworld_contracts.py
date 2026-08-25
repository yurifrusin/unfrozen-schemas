"""M1.1 state, action, generator, observation, and serialization contracts."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from unfrozen_schemas.envs.schema_world.actions import Action, ActionKind, validate_action
from unfrozen_schemas.envs.schema_world.events import DelayedEvent, DelayedEventKind
from unfrozen_schemas.envs.schema_world.protocol import IllegalActionError, UnsupportedActionError
from unfrozen_schemas.envs.schema_world.rng import DeterministicGenerator
from unfrozen_schemas.envs.schema_world.serialization import (
    FORBIDDEN_RELATION_LABELS,
    canonical_hash,
    canonical_record_bytes,
    primary_observation,
)
from unfrozen_schemas.envs.schema_world.state import (
    Boundary,
    BoundarySide,
    Entity,
    EntityRole,
    Opening,
    WorldState,
)


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
                x=900,
                y=400,
                width=20,
                height=200,
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


def test_actions_distinguish_illegal_and_unsupported_from_noop() -> None:
    state = _state()
    validate_action(state, Action(kind=ActionKind.NOOP))
    with pytest.raises(UnsupportedActionError, match="prospectively"):
        validate_action(state, Action(kind=ActionKind.GRASP))
    with pytest.raises(IllegalActionError, match="Unknown movement target"):
        validate_action(
            state,
            Action(kind=ActionKind.MOVE, target_id="e9999", delta_x=100),
        )
    with pytest.raises(ValidationError, match="non-zero integer delta"):
        Action(kind=ActionKind.EXIT, target_id="e0001")


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


def test_canonical_hash_ignores_mapping_insertion_order() -> None:
    left = {"b": [2, 3], "a": 1}
    right = {"a": 1, "b": [2, 3]}
    assert canonical_record_bytes(left) == b'{"a":1,"b":[2,3]}\n'
    assert canonical_hash(left) == canonical_hash(right)
