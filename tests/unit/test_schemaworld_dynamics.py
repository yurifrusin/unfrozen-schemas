"""M1.2 exact containment and support transitions."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from unfrozen_schemas.envs.schema_world.actions import Action, ActionKind
from unfrozen_schemas.envs.schema_world.dynamics import (
    TRANSITION_STAGE_ORDER,
    ContactKind,
    SupportKind,
    derive_contacts,
    derive_functional_supports,
    transition,
)
from unfrozen_schemas.envs.schema_world.events import (
    EVENT_PRIORITY,
    DelayedEvent,
    DelayedEventKind,
)
from unfrozen_schemas.envs.schema_world.protocol import IllegalActionError
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


def _containment_state(*, enabled: bool = False, closed: bool = True) -> WorldState:
    return WorldState(
        gravity_per_step=-100,
        seed=1,
        noise_seed=2,
        step_index=0,
        max_steps=5,
        entities=(
            Entity(
                entity_id="e0001",
                role=EntityRole.OBJECT,
                x=700,
                y=400,
                width=100,
                height=100,
                movable=True,
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
        boundaries=(
            Boundary(
                boundary_id="b0001",
                container_id="e0002",
                thickness=20,
                closed=closed,
            ),
        ),
        openings=(
            Opening(
                opening_id="o0001",
                boundary_id="b0001",
                side=BoundarySide.RIGHT,
                span_start=350,
                span_end=650,
                enabled=enabled,
                gate_id="e0003",
            ),
        ),
    )


def _support_state(
    *,
    side_contact: bool = False,
    tether: bool = False,
    platform_active: bool = True,
    events: tuple[DelayedEvent, ...] = (),
) -> WorldState:
    platform_x = 600 if side_contact else 400
    platform_y = 500 if side_contact else 400
    return WorldState(
        gravity_per_step=-100,
        seed=3,
        noise_seed=4,
        step_index=0,
        max_steps=6,
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
                role=EntityRole.SUPPORT,
                x=platform_x,
                y=platform_y,
                width=300,
                height=100,
                active=platform_active,
            ),
            Entity(
                entity_id="e0003",
                role=EntityRole.ANCHOR,
                x=450,
                y=900,
                width=100,
                height=100,
            ),
        ),
        tethers=(
            Tether(
                tether_id="t0001",
                object_id="e0001",
                anchor_id="e0003",
                length=350,
            ),
        )
        if tether
        else (),
        delayed_events=events,
    )


def test_closed_boundary_impedes_exit_and_enabled_opening_allows_it() -> None:
    action = Action(kind=ActionKind.EXIT, target_id="e0001", delta_x=300)
    blocked = transition(_containment_state(), action)
    assert blocked.state.entity("e0001").x == 700
    assert blocked.trace.blocked_by == ("b0001",)
    assert blocked.trace.moved_entities == ()

    passed = transition(_containment_state(enabled=True), action)
    assert passed.state.entity("e0001").x == 1000
    assert passed.trace.blocked_by == ()
    assert passed.trace.moved_entities == ("e0001",)


def test_open_boundary_allows_exit_without_an_enabled_aperture() -> None:
    result = transition(
        _containment_state(closed=False),
        Action(kind=ActionKind.EXIT, target_id="e0001", delta_x=300),
    )
    assert result.state.entity("e0001").x == 1000


def _tunnelling_state(
    *, left_enabled: bool, right_enabled: bool, closed: bool = True, start_x: int = 100
) -> WorldState:
    return WorldState(
        gravity_per_step=-100,
        seed=1,
        noise_seed=2,
        step_index=0,
        max_steps=5,
        entities=(
            Entity(
                entity_id="e0001",
                role=EntityRole.OBJECT,
                x=start_x,
                y=500,
                width=100,
                height=100,
                movable=True,
            ),
            Entity(
                entity_id="e0002",
                role=EntityRole.CONTAINER,
                x=300,
                y=100,
                width=800,
                height=800,
            ),
        ),
        boundaries=(
            Boundary(
                boundary_id="b0001",
                container_id="e0002",
                thickness=20,
                closed=closed,
            ),
        ),
        openings=(
            Opening(
                opening_id="o0001",
                boundary_id="b0001",
                side=BoundarySide.LEFT,
                span_start=400,
                span_end=700,
                enabled=left_enabled,
            ),
            Opening(
                opening_id="o0002",
                boundary_id="b0001",
                side=BoundarySide.RIGHT,
                span_start=400,
                span_end=700,
                enabled=right_enabled,
            ),
        ),
    )


def test_swept_boundary_blocks_forward_and_reverse_outside_to_outside_tunnelling() -> None:
    forward = transition(
        _tunnelling_state(left_enabled=True, right_enabled=False),
        Action(kind=ActionKind.MOVE, target_id="e0001", delta_x=1100),
    )
    assert forward.state.entity("e0001").x == 100
    assert forward.trace.blocked_by == ("b0001",)

    reverse = transition(
        _tunnelling_state(
            left_enabled=False,
            right_enabled=True,
            start_x=1200,
        ),
        Action(kind=ActionKind.MOVE, target_id="e0001", delta_x=-1100),
    )
    assert reverse.state.entity("e0001").x == 1200
    assert reverse.trace.blocked_by == ("b0001",)


def test_large_sweep_requires_an_opening_at_every_crossed_plane() -> None:
    passed = transition(
        _tunnelling_state(left_enabled=True, right_enabled=True),
        Action(kind=ActionKind.MOVE, target_id="e0001", delta_x=1100),
    )
    assert passed.state.entity("e0001").x == 1200
    assert passed.trace.blocked_by == ()

    whole_boundary_open = transition(
        _tunnelling_state(left_enabled=False, right_enabled=False, closed=False),
        Action(kind=ActionKind.MOVE, target_id="e0001", delta_x=1100),
    )
    assert whole_boundary_open.state.entity("e0001").x == 1200


def test_partial_boundary_start_is_fail_closed_without_a_fitting_opening() -> None:
    base = _containment_state()
    partial = base.entities[0].model_copy(update={"x": 850})
    partial_state = WorldState.model_validate(
        {**base.model_dump(), "entities": (partial, *base.entities[1:])}
    )
    blocked = transition(
        partial_state,
        Action(kind=ActionKind.MOVE, target_id="e0001", delta_x=100),
    )
    assert blocked.state.entity("e0001").x == 850
    assert blocked.trace.blocked_by == ("b0001",)

    enabled = WorldState.model_validate(
        {
            **partial_state.model_dump(),
            "openings": (partial_state.openings[0].model_copy(update={"enabled": True}),),
        }
    )
    passed = transition(
        enabled,
        Action(kind=ActionKind.MOVE, target_id="e0001", delta_x=100),
    )
    assert passed.state.entity("e0001").x == 950


def test_aperture_fit_uses_exact_span_and_orthogonal_crossing_alignment() -> None:
    base = _containment_state(enabled=True)
    too_small = Opening(
        opening_id="o0001",
        boundary_id="b0001",
        side=BoundarySide.RIGHT,
        span_start=425,
        span_end=475,
        enabled=True,
    )
    too_small_state = WorldState.model_validate({**base.model_dump(), "openings": (too_small,)})
    blocked_small = transition(
        too_small_state,
        Action(kind=ActionKind.EXIT, target_id="e0001", delta_x=300),
    )
    assert blocked_small.trace.blocked_by == ("b0001",)

    misaligned_object = base.entities[0].model_copy(update={"y": 700})
    misaligned = WorldState.model_validate(
        {**base.model_dump(), "entities": (misaligned_object, *base.entities[1:])}
    )
    blocked_alignment = transition(
        misaligned,
        Action(kind=ActionKind.EXIT, target_id="e0001", delta_x=300),
    )
    assert blocked_alignment.trace.blocked_by == ("b0001",)

    aligned = transition(
        base,
        Action(kind=ActionKind.EXIT, target_id="e0001", delta_x=300),
    )
    assert aligned.trace.blocked_by == ()


def test_entry_and_open_action_use_the_same_exact_aperture_contract() -> None:
    base = _containment_state()
    outside = base.entities[0].model_copy(update={"x": 1000})
    outside_state = base.model_copy(update={"entities": (outside, *base.entities[1:])})
    entry = Action(kind=ActionKind.ENTER, target_id="e0001", delta_x=-300)
    blocked = transition(outside_state, entry)
    assert blocked.state.entity("e0001").x == 1000
    assert blocked.trace.blocked_by == ("b0001",)

    opened = transition(base, Action(kind=ActionKind.OPEN_GATE, target_id="o0001"))
    exited = transition(
        opened.state,
        Action(kind=ActionKind.EXIT, target_id="e0001", delta_x=300),
    )
    assert exited.state.entity("e0001").x == 1000

    enabled_outside = outside_state.model_copy(
        update={"openings": (outside_state.openings[0].model_copy(update={"enabled": True}),)}
    )
    entered = transition(enabled_outside, entry)
    assert entered.state.entity("e0001").x == 700


def test_lower_surface_is_functional_but_side_contact_does_not_prevent_falling() -> None:
    stable = transition(_support_state(), Action(kind=ActionKind.NOOP))
    assert stable.state.entity("e0001").y == 500
    assert stable.trace.contacts[0].kind is ContactKind.LOWER_SURFACE
    assert stable.trace.functional_supports[0].kind is SupportKind.LOWER_SURFACE
    assert stable.trace.falling_entities == ()

    side = transition(_support_state(side_contact=True), Action(kind=ActionKind.NOOP))
    assert side.trace.contacts[0].kind is ContactKind.SIDE
    assert side.trace.functional_supports == ()
    assert side.state.entity("e0001").y == 400
    assert side.trace.falling_entities == ("e0001",)


def test_support_removal_causes_exact_fall() -> None:
    result = transition(_support_state(), Action(kind=ActionKind.REMOVE_SUPPORT, target_id="e0002"))
    assert result.state.entity("e0002").active is False
    assert result.state.entity("e0001").y == 400
    assert result.state.entity("e0001").velocity_y == -100
    assert result.trace.stage_order == TRANSITION_STAGE_ORDER


def test_tension_support_survives_platform_removal_then_detach_causes_fall() -> None:
    held = transition(
        _support_state(tether=True),
        Action(kind=ActionKind.REMOVE_SUPPORT, target_id="e0002"),
    )
    assert held.state.entity("e0001").y == 500
    assert held.trace.functional_supports[0].kind is SupportKind.TENSION

    detached = transition(held.state, Action(kind=ActionKind.DETACH, target_id="t0001"))
    assert detached.state.entity("e0001").y == 400
    assert detached.trace.falling_entities == ("e0001",)


def test_taut_tether_support_uses_exact_squared_integer_equality() -> None:
    state = _support_state(tether=True, platform_active=False)
    supports = derive_functional_supports(state, derive_contacts(state))
    assert [(item.kind, item.mechanism_id) for item in supports] == [(SupportKind.TENSION, "t0001")]


@pytest.mark.parametrize(
    ("length", "anchor_y"),
    [
        (400, 900),  # underlength/slack: distance 350 is below the declaration
        (300, 900),  # overlength: distance 350 exceeds the declaration
        (250, 300),  # exact distance but anchor is below the object
    ],
)
def test_active_load_bearing_tether_rejects_slack_overlength_and_anchor_not_above(
    length: int, anchor_y: int
) -> None:
    base = _support_state(platform_active=False)
    anchor = base.entity("e0003").model_copy(update={"y": anchor_y})
    with pytest.raises(ValidationError, match="exact declared length"):
        WorldState(
            **{
                **base.model_dump(),
                "entities": (base.entities[0], base.entities[1], anchor),
                "tethers": (
                    Tether(
                        tether_id="t0001",
                        object_id="e0001",
                        anchor_id="e0003",
                        length=length,
                    ),
                ),
            }
        )


@pytest.mark.parametrize(
    ("active", "load_bearing"),
    [(False, True), (True, False)],
)
def test_inactive_or_non_load_bearing_tether_is_not_functional_support(
    active: bool, load_bearing: bool
) -> None:
    base = _support_state(platform_active=False)
    state = WorldState(
        **{
            **base.model_dump(),
            "tethers": (
                Tether(
                    tether_id="t0001",
                    object_id="e0001",
                    anchor_id="e0003",
                    length=400,
                    active=active,
                    load_bearing=load_bearing,
                ),
            ),
        }
    )
    assert derive_functional_supports(state, derive_contacts(state)) == ()


def test_action_that_would_break_tether_invariant_is_rejected() -> None:
    with pytest.raises(IllegalActionError, match="state invariants"):
        transition(
            _support_state(tether=True),
            Action(kind=ActionKind.MOVE, target_id="e0001", delta_x=1),
        )


@pytest.mark.parametrize("kind", [ActionKind.DETACH, ActionKind.CUT_OR_BREAK])
def test_detach_and_cut_cause_fall_in_the_same_accepted_step(kind: ActionKind) -> None:
    result = transition(
        _support_state(tether=True, platform_active=False),
        Action(kind=kind, target_id="t0001"),
    )
    assert result.state.entity("e0001").y == 400
    assert result.state.entity("e0001").velocity_y == -100
    assert result.trace.falling_entities == ("e0001",)


def test_direct_attachment_is_functional_support_until_detached() -> None:
    base = _support_state(platform_active=False)
    state = base.model_copy(
        update={
            "attachments": (
                Attachment(
                    attachment_id="a0001",
                    object_id="e0001",
                    anchor_id="e0003",
                ),
            )
        }
    )
    held = transition(state, Action(kind=ActionKind.NOOP))
    assert held.state.entity("e0001").y == 500
    assert held.trace.functional_supports[0].kind is SupportKind.ATTACHMENT
    fallen = transition(held.state, Action(kind=ActionKind.DETACH, target_id="a0001"))
    assert fallen.state.entity("e0001").y == 400


def test_superficially_similar_exterior_parallel_motion_is_not_blocked() -> None:
    base = _containment_state()
    outside = base.entities[0].model_copy(update={"x": 1000})
    state = base.model_copy(update={"entities": (outside, *base.entities[1:])})
    result = transition(
        state,
        Action(kind=ActionKind.MOVE, target_id="e0001", delta_y=100),
    )
    assert result.state.entity("e0001").y == 500
    assert result.trace.blocked_by == ()


def test_delayed_event_priority_is_stable_and_effect_begins_next_step() -> None:
    events = (
        DelayedEvent(
            event_id="v0001",
            due_step=1,
            priority=EVENT_PRIORITY["disable_tether"],
            insertion_order=1,
            kind=DelayedEventKind.DISABLE_TETHER,
            target_id="t0001",
        ),
        DelayedEvent(
            event_id="v0002",
            due_step=1,
            priority=EVENT_PRIORITY["disable_entity"],
            insertion_order=0,
            kind=DelayedEventKind.DISABLE_ENTITY,
            target_id="e0002",
        ),
    )
    first = transition(_support_state(tether=True, events=events), Action(kind=ActionKind.NOOP))
    assert first.trace.processed_event_ids == ("v0001", "v0002")
    assert first.state.entity("e0001").y == 500
    assert first.state.tethers[0].active is False
    assert first.state.entity("e0002").active is False

    second = transition(first.state, Action(kind=ActionKind.WAIT))
    assert second.state.entity("e0001").y == 400


def test_collision_tie_breaks_by_highest_surface_then_stable_id() -> None:
    base = _support_state(platform_active=False)
    state = base.model_copy(
        update={
            "entities": (
                base.entities[0].model_copy(update={"y": 650, "velocity_y": -200}),
                base.entities[1].model_copy(
                    update={"entity_id": "e0002", "active": True, "y": 400}
                ),
                base.entities[2],
                Entity(
                    entity_id="e0004",
                    role=EntityRole.SUPPORT,
                    x=400,
                    y=450,
                    width=300,
                    height=100,
                ),
            )
        }
    )
    result = transition(state, Action(kind=ActionKind.NOOP))
    assert result.state.entity("e0001").y == 550
    assert result.trace.collision_entities == ("e0001",)
