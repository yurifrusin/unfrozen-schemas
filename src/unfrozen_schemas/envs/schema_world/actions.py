"""Structured action family and Phase I legality checks."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, model_validator

from unfrozen_schemas.config import FrozenModel
from unfrozen_schemas.envs.schema_world.protocol import IllegalActionError, UnsupportedActionError
from unfrozen_schemas.envs.schema_world.state import EntityRole, WorldState


class ActionKind(StrEnum):
    MOVE = "MOVE"
    ROTATE = "ROTATE"
    GRASP = "GRASP"
    RELEASE = "RELEASE"
    PUSH = "PUSH"
    PULL = "PULL"
    LIFT = "LIFT"
    LOWER = "LOWER"
    OPEN = "OPEN"
    CLOSE = "CLOSE"
    ATTACH = "ATTACH"
    DETACH = "DETACH"
    CUT_OR_BREAK = "CUT_OR_BREAK"
    WAIT = "WAIT"
    PROBE_FORCE = "PROBE_FORCE"
    NOOP = "NOOP"
    ENTER = "ENTER"
    EXIT = "EXIT"
    OPEN_GATE = "OPEN_GATE"
    CLOSE_GATE = "CLOSE_GATE"
    REMOVE_SUPPORT = "REMOVE_SUPPORT"


SUPPORTED_PHASE1_ACTIONS = frozenset(
    {
        ActionKind.MOVE,
        ActionKind.OPEN,
        ActionKind.CLOSE,
        ActionKind.DETACH,
        ActionKind.CUT_OR_BREAK,
        ActionKind.WAIT,
        ActionKind.NOOP,
        ActionKind.ENTER,
        ActionKind.EXIT,
        ActionKind.OPEN_GATE,
        ActionKind.CLOSE_GATE,
        ActionKind.REMOVE_SUPPORT,
    }
)


class Action(FrozenModel):
    """One versioned structured action; later-phase semantics remain explicit but unsupported."""

    schema_version: str = Field(default="1", pattern=r"^1$")
    kind: ActionKind
    actor_id: str | None = Field(default=None, pattern=r"^e[0-9]{4}$")
    target_id: str | None = None
    delta_x: int = 0
    delta_y: int = 0
    magnitude: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_structure(self) -> Action:
        movement = {ActionKind.MOVE, ActionKind.ENTER, ActionKind.EXIT}
        target_actions = {
            ActionKind.OPEN,
            ActionKind.CLOSE,
            ActionKind.OPEN_GATE,
            ActionKind.CLOSE_GATE,
            ActionKind.DETACH,
            ActionKind.CUT_OR_BREAK,
            ActionKind.REMOVE_SUPPORT,
        }
        if self.kind in movement:
            if self.target_id is None or not (self.delta_x or self.delta_y):
                raise ValueError("Movement actions require a target and a non-zero integer delta")
        elif self.kind in target_actions and self.target_id is None:
            raise ValueError(f"{self.kind.value} requires target_id")
        elif self.kind in {ActionKind.WAIT, ActionKind.NOOP} and (
            self.target_id is not None or self.delta_x or self.delta_y or self.magnitude is not None
        ):
            raise ValueError(f"{self.kind.value} accepts no target or numeric parameters")
        return self


def validate_action(state: WorldState, action: Action) -> None:
    """Fail explicitly for unsupported actions and illegal implemented actions."""

    if state.terminated:
        raise IllegalActionError("Cannot step a terminated SchemaWorld state")
    if action.kind not in SUPPORTED_PHASE1_ACTIONS:
        raise UnsupportedActionError(
            f"{action.kind.value} is declared prospectively but unsupported in "
            f"{state.environment_version}"
        )
    if action.kind in {ActionKind.WAIT, ActionKind.NOOP}:
        return
    assert action.target_id is not None
    if action.kind in {ActionKind.MOVE, ActionKind.ENTER, ActionKind.EXIT}:
        try:
            target = state.entity(action.target_id)
        except KeyError as exc:
            raise IllegalActionError(f"Unknown movement target: {action.target_id}") from exc
        if not target.active or not target.movable:
            raise IllegalActionError(
                f"Movement target is not active and movable: {action.target_id}"
            )
        return
    if action.kind in {
        ActionKind.OPEN,
        ActionKind.OPEN_GATE,
        ActionKind.CLOSE,
        ActionKind.CLOSE_GATE,
    }:
        opening = next(
            (item for item in state.openings if item.opening_id == action.target_id), None
        )
        if opening is None:
            raise IllegalActionError(f"Unknown opening target: {action.target_id}")
        enabling = action.kind in {ActionKind.OPEN, ActionKind.OPEN_GATE}
        if opening.enabled == enabling:
            raise IllegalActionError(
                f"Opening {action.target_id} is already {'enabled' if enabling else 'disabled'}"
            )
        return
    if action.kind is ActionKind.REMOVE_SUPPORT:
        try:
            support = state.entity(action.target_id)
        except KeyError as exc:
            raise IllegalActionError(f"Unknown support target: {action.target_id}") from exc
        if support.role is not EntityRole.SUPPORT or not support.active:
            raise IllegalActionError(f"Target is not an active support entity: {action.target_id}")
        return
    attachment = next(
        (item for item in state.attachments if item.attachment_id == action.target_id),
        None,
    )
    tether = next((item for item in state.tethers if item.tether_id == action.target_id), None)
    if (attachment is None or not attachment.active) and (tether is None or not tether.active):
        raise IllegalActionError(f"Target is not an active connection: {action.target_id}")
