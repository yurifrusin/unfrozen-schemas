"""Structured action family and Phase I legality checks."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final, Literal

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

ActionParameter = Literal["actor_id", "target_id", "delta_x", "delta_y", "magnitude"]


@dataclass(frozen=True, slots=True)
class ActionParameterRule:
    """Canonical non-default parameter shape for one action kind."""

    allowed: frozenset[ActionParameter]
    required: frozenset[ActionParameter]
    exactly_one_axis: bool = False
    positive_magnitude: bool = False


_NONE = ActionParameterRule(frozenset(), frozenset())
_TARGET_ONLY = ActionParameterRule(frozenset({"target_id"}), frozenset({"target_id"}))
_MOVEMENT = ActionParameterRule(
    frozenset({"target_id", "delta_x", "delta_y"}),
    frozenset({"target_id"}),
    exactly_one_axis=True,
)
_TARGET_MAGNITUDE = ActionParameterRule(
    frozenset({"target_id", "magnitude"}),
    frozenset({"target_id", "magnitude"}),
    positive_magnitude=True,
)
_ACTOR_TARGET = ActionParameterRule(
    frozenset({"actor_id", "target_id"}),
    frozenset({"actor_id", "target_id"}),
)
_ACTOR_TARGET_MAGNITUDE = ActionParameterRule(
    frozenset({"actor_id", "target_id", "magnitude"}),
    frozenset({"actor_id", "target_id", "magnitude"}),
    positive_magnitude=True,
)

ACTION_PARAMETER_MATRIX: Final[dict[ActionKind, ActionParameterRule]] = {
    ActionKind.MOVE: _MOVEMENT,
    ActionKind.ROTATE: _TARGET_MAGNITUDE,
    ActionKind.GRASP: _ACTOR_TARGET,
    ActionKind.RELEASE: _ACTOR_TARGET,
    ActionKind.PUSH: _ACTOR_TARGET_MAGNITUDE,
    ActionKind.PULL: _ACTOR_TARGET_MAGNITUDE,
    ActionKind.LIFT: _ACTOR_TARGET_MAGNITUDE,
    ActionKind.LOWER: _ACTOR_TARGET_MAGNITUDE,
    ActionKind.OPEN: _TARGET_ONLY,
    ActionKind.CLOSE: _TARGET_ONLY,
    ActionKind.ATTACH: _ACTOR_TARGET,
    ActionKind.DETACH: _TARGET_ONLY,
    ActionKind.CUT_OR_BREAK: _TARGET_ONLY,
    ActionKind.WAIT: _NONE,
    ActionKind.PROBE_FORCE: _ACTOR_TARGET_MAGNITUDE,
    ActionKind.NOOP: _NONE,
    ActionKind.ENTER: _MOVEMENT,
    ActionKind.EXIT: _MOVEMENT,
    ActionKind.OPEN_GATE: _TARGET_ONLY,
    ActionKind.CLOSE_GATE: _TARGET_ONLY,
    ActionKind.REMOVE_SUPPORT: _TARGET_ONLY,
}


class Action(FrozenModel):
    """One versioned structured action; later-phase semantics remain explicit but unsupported."""

    schema_version: str = Field(default="1", pattern=r"^1$")
    kind: ActionKind
    actor_id: str | None = Field(default=None, pattern=r"^e[0-9]{4}$")
    target_id: str | None = Field(default=None, min_length=1)
    delta_x: int = 0
    delta_y: int = 0
    magnitude: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_structure(self) -> Action:
        rule = ACTION_PARAMETER_MATRIX[self.kind]
        present: set[ActionParameter] = set()
        if self.actor_id is not None:
            present.add("actor_id")
        if self.target_id is not None:
            present.add("target_id")
        if self.delta_x != 0:
            present.add("delta_x")
        if self.delta_y != 0:
            present.add("delta_y")
        if self.magnitude is not None:
            present.add("magnitude")
        unused = present - rule.allowed
        if unused:
            raise ValueError(f"{self.kind.value} rejects unused action fields: {sorted(unused)}")
        missing = rule.required - present
        if missing:
            raise ValueError(f"{self.kind.value} requires action fields: {sorted(missing)}")
        if rule.exactly_one_axis and (self.delta_x == 0) == (self.delta_y == 0):
            raise ValueError(f"{self.kind.value} requires exactly one non-zero axis delta")
        if rule.positive_magnitude and (self.magnitude is None or self.magnitude <= 0):
            raise ValueError(f"{self.kind.value} requires a positive magnitude")
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
