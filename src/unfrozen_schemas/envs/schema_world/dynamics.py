"""Pure exact transitions for Milestone 1 CONTAINMENT and SUPPORT dynamics."""

from __future__ import annotations

from enum import StrEnum
from typing import Final, Literal

from pydantic import Field, ValidationError

from unfrozen_schemas.config import FrozenModel
from unfrozen_schemas.envs.schema_world.actions import Action, ActionKind, validate_action
from unfrozen_schemas.envs.schema_world.events import DelayedEvent, DelayedEventKind, event_sort_key
from unfrozen_schemas.envs.schema_world.protocol import IllegalActionError
from unfrozen_schemas.envs.schema_world.serialization import canonical_hash
from unfrozen_schemas.envs.schema_world.state import (
    Attachment,
    Boundary,
    BoundarySide,
    Entity,
    EntityRole,
    Opening,
    Tether,
    WorldState,
    tether_is_exactly_taut,
)

TRANSITION_STAGE_ORDER: Final[tuple[str, ...]] = (
    "action_application",
    "contact_resolution",
    "support_evaluation",
    "gravity",
    "collision_resolution",
    "delayed_events",
    "relation_derivation",
)


class ContactKind(StrEnum):
    LOWER_SURFACE = "lower_surface"
    SIDE = "side"
    OVERLAP = "overlap"


class SupportKind(StrEnum):
    LOWER_SURFACE = "lower_surface"
    ATTACHMENT = "attachment"
    TENSION = "tension"


class ContactRecord(FrozenModel):
    object_id: str = Field(pattern=r"^e[0-9]{4}$")
    other_id: str = Field(pattern=r"^e[0-9]{4}$")
    kind: ContactKind


class SupportRecord(FrozenModel):
    object_id: str = Field(pattern=r"^e[0-9]{4}$")
    mechanism_id: str
    kind: SupportKind


class TransitionTrace(FrozenModel):
    """Privileged audit trace; it is never included in a primary observation."""

    schema_version: Literal["1"] = "1"
    action: Action
    stage_order: tuple[str, ...] = TRANSITION_STAGE_ORDER
    contacts: tuple[ContactRecord, ...]
    functional_supports: tuple[SupportRecord, ...]
    blocked_by: tuple[str, ...]
    moved_entities: tuple[str, ...]
    falling_entities: tuple[str, ...]
    collision_entities: tuple[str, ...]
    processed_event_ids: tuple[str, ...]
    notes: tuple[str, ...]


class TransitionResult(FrozenModel):
    state: WorldState
    trace: TransitionTrace
    transition_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


def _horizontal_overlap(left: Entity, right: Entity) -> int:
    return max(0, min(left.x + left.width, right.x + right.width) - max(left.x, right.x))


def _vertical_overlap(left: Entity, right: Entity) -> int:
    return max(0, min(left.y + left.height, right.y + right.height) - max(left.y, right.y))


def _replace_entity(entities: tuple[Entity, ...], replacement: Entity) -> tuple[Entity, ...]:
    return tuple(
        replacement if item.entity_id == replacement.entity_id else item for item in entities
    )


def _replace_opening(openings: tuple[Opening, ...], replacement: Opening) -> tuple[Opening, ...]:
    return tuple(
        replacement if item.opening_id == replacement.opening_id else item for item in openings
    )


def _replace_attachment(
    attachments: tuple[Attachment, ...], replacement: Attachment
) -> tuple[Attachment, ...]:
    return tuple(
        replacement if item.attachment_id == replacement.attachment_id else item
        for item in attachments
    )


def _replace_tether(tethers: tuple[Tether, ...], replacement: Tether) -> tuple[Tether, ...]:
    return tuple(
        replacement if item.tether_id == replacement.tether_id else item for item in tethers
    )


def _interior(container: Entity, boundary: Boundary) -> tuple[int, int, int, int]:
    return (
        container.x + boundary.thickness,
        container.x + container.width - boundary.thickness,
        container.y + boundary.thickness,
        container.y + container.height - boundary.thickness,
    )


def _crossed_sides(
    before: Entity,
    proposed: Entity,
    container: Entity,
    bounds: tuple[int, int, int, int],
) -> tuple[BoundarySide, ...]:
    """Return every finite wall segment intersected by the open swept rectangle extent."""

    left, right, bottom, top = bounds
    sides: list[BoundarySide] = []
    if before.x != proposed.x and _vertical_overlap(before, container) > 0:
        swept_left = min(before.x, proposed.x)
        swept_right = max(before.x + before.width, proposed.x + proposed.width)
        if swept_left < left < swept_right:
            sides.append(BoundarySide.LEFT)
        if swept_left < right < swept_right:
            sides.append(BoundarySide.RIGHT)
    if before.y != proposed.y and _horizontal_overlap(before, container) > 0:
        swept_bottom = min(before.y, proposed.y)
        swept_top = max(before.y + before.height, proposed.y + proposed.height)
        if swept_bottom < bottom < swept_top:
            sides.append(BoundarySide.BOTTOM)
        if swept_bottom < top < swept_top:
            sides.append(BoundarySide.TOP)
    return tuple(sides)


def _fits_opening(entity: Entity, side: BoundarySide, opening: Opening) -> bool:
    if not opening.enabled or opening.side is not side:
        return False
    if side in {BoundarySide.LEFT, BoundarySide.RIGHT}:
        return entity.y >= opening.span_start and entity.y + entity.height <= opening.span_end
    return entity.x >= opening.span_start and entity.x + entity.width <= opening.span_end


def _movement_blockers(state: WorldState, before: Entity, proposed: Entity) -> tuple[str, ...]:
    blockers: list[str] = []
    entities = {entity.entity_id: entity for entity in state.entities}
    for boundary in state.boundaries:
        if not boundary.closed:
            continue
        container = entities[boundary.container_id]
        bounds = _interior(container, boundary)
        crossed = _crossed_sides(before, proposed, container, bounds)
        if not crossed:
            continue
        boundary_openings = tuple(
            opening for opening in state.openings if opening.boundary_id == boundary.boundary_id
        )
        if any(
            not any(_fits_opening(before, side, opening) for opening in boundary_openings)
            for side in crossed
        ):
            blockers.append(boundary.boundary_id)
    return tuple(sorted(set(blockers)))


def _validated_action_state(candidate: WorldState, action: Action) -> WorldState:
    try:
        return WorldState.model_validate(candidate.model_dump(mode="python"))
    except ValidationError as exc:
        raise IllegalActionError(
            f"{action.kind.value} would violate SchemaWorld state invariants: "
            f"{exc.errors()[0]['msg']}"
        ) from exc


def _apply_action(
    state: WorldState, action: Action
) -> tuple[WorldState, tuple[str, ...], tuple[str, ...]]:
    blocked_by: tuple[str, ...] = ()
    moved: tuple[str, ...] = ()
    if action.kind in {ActionKind.MOVE, ActionKind.ENTER, ActionKind.EXIT}:
        assert action.target_id is not None
        before = state.entity(action.target_id)
        proposed = before.model_copy(
            update={"x": before.x + action.delta_x, "y": before.y + action.delta_y}
        )
        if (
            proposed.x < state.coordinate_min
            or proposed.y < state.coordinate_min
            or proposed.x + proposed.width > state.coordinate_max
            or proposed.y + proposed.height > state.coordinate_max
        ):
            blocked_by = ("world_bounds",)
        else:
            blocked_by = _movement_blockers(state, before, proposed)
        if not blocked_by:
            state = _validated_action_state(
                state.model_copy(update={"entities": _replace_entity(state.entities, proposed)}),
                action,
            )
            moved = (before.entity_id,)
    elif action.kind in {ActionKind.OPEN, ActionKind.OPEN_GATE}:
        assert action.target_id is not None
        opening = next(item for item in state.openings if item.opening_id == action.target_id)
        state = _validated_action_state(
            state.model_copy(
                update={
                    "openings": _replace_opening(
                        state.openings, opening.model_copy(update={"enabled": True})
                    )
                }
            ),
            action,
        )
    elif action.kind in {ActionKind.CLOSE, ActionKind.CLOSE_GATE}:
        assert action.target_id is not None
        opening = next(item for item in state.openings if item.opening_id == action.target_id)
        state = _validated_action_state(
            state.model_copy(
                update={
                    "openings": _replace_opening(
                        state.openings, opening.model_copy(update={"enabled": False})
                    )
                }
            ),
            action,
        )
    elif action.kind is ActionKind.REMOVE_SUPPORT:
        assert action.target_id is not None
        target = state.entity(action.target_id)
        state = _validated_action_state(
            state.model_copy(
                update={
                    "entities": _replace_entity(
                        state.entities, target.model_copy(update={"active": False})
                    )
                }
            ),
            action,
        )
    elif action.kind in {ActionKind.DETACH, ActionKind.CUT_OR_BREAK}:
        assert action.target_id is not None
        attachment = next(
            (item for item in state.attachments if item.attachment_id == action.target_id), None
        )
        if attachment is not None:
            state = _validated_action_state(
                state.model_copy(
                    update={
                        "attachments": _replace_attachment(
                            state.attachments, attachment.model_copy(update={"active": False})
                        )
                    }
                ),
                action,
            )
        else:
            tether = next(item for item in state.tethers if item.tether_id == action.target_id)
            state = _validated_action_state(
                state.model_copy(
                    update={
                        "tethers": _replace_tether(
                            state.tethers, tether.model_copy(update={"active": False})
                        )
                    }
                ),
                action,
            )
    return state, blocked_by, moved


def derive_contacts(state: WorldState) -> tuple[ContactRecord, ...]:
    contacts: list[ContactRecord] = []
    objects = (
        entity
        for entity in state.entities
        if entity.active and entity.movable and entity.affected_by_gravity
    )
    others = tuple(entity for entity in state.entities if entity.active)
    for obj in objects:
        for other in others:
            if obj.entity_id == other.entity_id:
                continue
            if obj.y == other.y + other.height and _horizontal_overlap(obj, other) > 0:
                kind = ContactKind.LOWER_SURFACE
            elif (
                obj.x == other.x + other.width or obj.x + obj.width == other.x
            ) and _vertical_overlap(obj, other) > 0:
                kind = ContactKind.SIDE
            elif _horizontal_overlap(obj, other) > 0 and _vertical_overlap(obj, other) > 0:
                kind = ContactKind.OVERLAP
            else:
                continue
            contacts.append(
                ContactRecord(object_id=obj.entity_id, other_id=other.entity_id, kind=kind)
            )
    return tuple(
        sorted(contacts, key=lambda item: (item.object_id, item.other_id, item.kind.value))
    )


def _tether_is_taut(state: WorldState, tether: Tether) -> bool:
    if not tether.active or not tether.load_bearing:
        return False
    obj = state.entity(tether.object_id)
    anchor = state.entity(tether.anchor_id)
    if not obj.active or not anchor.active:
        return False
    return tether_is_exactly_taut(tether, obj, anchor)


def derive_functional_supports(
    state: WorldState, contacts: tuple[ContactRecord, ...]
) -> tuple[SupportRecord, ...]:
    records: list[SupportRecord] = []
    entities = {entity.entity_id: entity for entity in state.entities}
    for contact in contacts:
        other = entities[contact.other_id]
        if contact.kind is ContactKind.LOWER_SURFACE and other.role is EntityRole.SUPPORT:
            records.append(
                SupportRecord(
                    object_id=contact.object_id,
                    mechanism_id=other.entity_id,
                    kind=SupportKind.LOWER_SURFACE,
                )
            )
    for attachment in state.attachments:
        if (
            attachment.active
            and attachment.load_bearing
            and entities[attachment.object_id].active
            and entities[attachment.anchor_id].active
        ):
            records.append(
                SupportRecord(
                    object_id=attachment.object_id,
                    mechanism_id=attachment.attachment_id,
                    kind=SupportKind.ATTACHMENT,
                )
            )
    for tether in state.tethers:
        if _tether_is_taut(state, tether):
            records.append(
                SupportRecord(
                    object_id=tether.object_id,
                    mechanism_id=tether.tether_id,
                    kind=SupportKind.TENSION,
                )
            )
    return tuple(
        sorted(records, key=lambda item: (item.object_id, item.kind.value, item.mechanism_id))
    )


def _apply_gravity(
    state: WorldState, supports: tuple[SupportRecord, ...]
) -> tuple[WorldState, tuple[str, ...], dict[str, int]]:
    supported_ids = {record.object_id for record in supports}
    falling: list[str] = []
    previous_y: dict[str, int] = {}
    entities = state.entities
    for entity in state.entities:
        if not entity.active or not entity.movable or not entity.affected_by_gravity:
            continue
        previous_y[entity.entity_id] = entity.y
        if entity.entity_id in supported_ids:
            replacement = entity.model_copy(update={"velocity_y": 0})
        else:
            velocity_y = entity.velocity_y + state.gravity_per_step
            proposed_y = max(state.coordinate_min, entity.y + velocity_y)
            replacement = entity.model_copy(update={"y": proposed_y, "velocity_y": velocity_y})
            if proposed_y < entity.y:
                falling.append(entity.entity_id)
        entities = _replace_entity(entities, replacement)
    return state.model_copy(update={"entities": entities}), tuple(sorted(falling)), previous_y


def _resolve_collisions(
    state: WorldState, previous_y: dict[str, int]
) -> tuple[WorldState, tuple[str, ...]]:
    collisions: list[str] = []
    entities = state.entities
    platforms = tuple(
        entity for entity in state.entities if entity.active and entity.role is EntityRole.SUPPORT
    )
    for entity in state.entities:
        if entity.entity_id not in previous_y or not entity.active:
            continue
        candidates = [
            platform
            for platform in platforms
            if previous_y[entity.entity_id] >= platform.y + platform.height
            and entity.y <= platform.y + platform.height
            and _horizontal_overlap(entity, platform) > 0
        ]
        if candidates:
            platform = sorted(
                candidates, key=lambda item: (-(item.y + item.height), item.entity_id)
            )[0]
            replacement = entity.model_copy(
                update={"y": platform.y + platform.height, "velocity_y": 0}
            )
            entities = _replace_entity(entities, replacement)
            collisions.append(entity.entity_id)
        elif entity.y == state.coordinate_min and entity.velocity_y < 0:
            entities = _replace_entity(entities, entity.model_copy(update={"velocity_y": 0}))
            collisions.append(entity.entity_id)
    return state.model_copy(update={"entities": entities}), tuple(sorted(collisions))


def _apply_one_event(state: WorldState, event: DelayedEvent) -> WorldState:
    if event.kind is DelayedEventKind.DISABLE_ENTITY:
        entity_target = state.entity(event.target_id)
        return state.model_copy(
            update={
                "entities": _replace_entity(
                    state.entities, entity_target.model_copy(update={"active": False})
                ),
                "attachments": tuple(
                    item.model_copy(update={"active": False})
                    if item.active and event.target_id in {item.object_id, item.anchor_id}
                    else item
                    for item in state.attachments
                ),
                "tethers": tuple(
                    item.model_copy(update={"active": False})
                    if item.active and event.target_id in {item.object_id, item.anchor_id}
                    else item
                    for item in state.tethers
                ),
            }
        )
    if event.kind is DelayedEventKind.ENABLE_OPENING:
        opening_target = next(item for item in state.openings if item.opening_id == event.target_id)
        return state.model_copy(
            update={
                "openings": _replace_opening(
                    state.openings, opening_target.model_copy(update={"enabled": True})
                )
            }
        )
    if event.kind is DelayedEventKind.DISABLE_ATTACHMENT:
        attachment_target = next(
            item for item in state.attachments if item.attachment_id == event.target_id
        )
        return state.model_copy(
            update={
                "attachments": _replace_attachment(
                    state.attachments, attachment_target.model_copy(update={"active": False})
                )
            }
        )
    tether_target = next(item for item in state.tethers if item.tether_id == event.target_id)
    return state.model_copy(
        update={
            "tethers": _replace_tether(
                state.tethers, tether_target.model_copy(update={"active": False})
            )
        }
    )


def _process_delayed_events(
    state: WorldState, next_step: int
) -> tuple[WorldState, tuple[str, ...]]:
    due = tuple(
        sorted(
            (event for event in state.delayed_events if event.due_step <= next_step),
            key=event_sort_key,
        )
    )
    future = tuple(event for event in state.delayed_events if event.due_step > next_step)
    for event in due:
        state = _apply_one_event(state, event)
    return state.model_copy(update={"delayed_events": future}), tuple(
        event.event_id for event in due
    )


def transition(state: WorldState, action: Action) -> TransitionResult:
    """Apply one accepted action using the frozen seven-stage M1 transition order."""

    validate_action(state, action)
    action_state, blocked_by, moved = _apply_action(state, action)
    contacts = derive_contacts(action_state)
    supports = derive_functional_supports(action_state, contacts)
    gravity_state, falling, previous_y = _apply_gravity(action_state, supports)
    collision_state, collisions = _resolve_collisions(gravity_state, previous_y)
    next_step = state.step_index + 1
    event_state, processed_events = _process_delayed_events(collision_state, next_step)
    final_state = event_state.model_copy(
        update={"step_index": next_step, "terminated": next_step >= state.max_steps}
    )
    try:
        final_state = WorldState.model_validate(final_state.model_dump(mode="python"))
    except ValidationError as exc:
        raise IllegalActionError(
            f"Transition would violate SchemaWorld state invariants: {exc.errors()[0]['msg']}"
        ) from exc
    notes = (
        "Delayed events execute after collision resolution; "
        "their physical effects begin next step.",
    )
    trace = TransitionTrace(
        action=action,
        contacts=contacts,
        functional_supports=supports,
        blocked_by=blocked_by,
        moved_entities=moved,
        falling_entities=falling,
        collision_entities=collisions,
        processed_event_ids=processed_events,
        notes=notes,
    )
    return TransitionResult(
        state=final_state,
        trace=trace,
        transition_hash=canonical_hash(
            {"before": state, "action": action, "after": final_state, "trace": trace}
        ),
    )
