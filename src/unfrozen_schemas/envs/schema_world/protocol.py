"""Typed reset/step protocol and explicit environment errors."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pydantic import Field

from unfrozen_schemas.config import FrozenModel
from unfrozen_schemas.envs.schema_world.serialization import PrimaryObservation
from unfrozen_schemas.envs.schema_world.state import WorldState

if TYPE_CHECKING:
    from unfrozen_schemas.envs.schema_world.actions import Action


class SchemaWorldError(RuntimeError):
    """Base for environment contract failures."""


class IllegalActionError(SchemaWorldError):
    """Raised when an implemented action is invalid in the current state."""


class UnsupportedActionError(SchemaWorldError):
    """Raised when a prospectively declared action has no Milestone 1 dynamics."""


class ResetResult(FrozenModel):
    observation: PrimaryObservation
    privileged_state: WorldState
    info: dict[str, str | int | bool]


class StepResult(FrozenModel):
    observation: PrimaryObservation
    privileged_state: WorldState
    reward: int = 0
    terminated: bool
    truncated: bool
    info: dict[str, str | int | bool | tuple[str, ...]]
    transition_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


class SchemaWorldProtocol(Protocol):
    def reset(self, *, seed: int, noise_seed: int) -> ResetResult: ...

    def step(self, action: Action) -> StepResult: ...
