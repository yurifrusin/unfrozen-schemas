"""Versioned delayed-event records and deterministic priority policy."""

from __future__ import annotations

from enum import StrEnum
from typing import Final

from pydantic import Field, model_validator

from unfrozen_schemas.config import FrozenModel

EVENT_PRIORITY: Final[dict[str, int]] = {
    "disable_attachment": 10,
    "disable_tether": 20,
    "disable_entity": 30,
    "enable_opening": 40,
}


class DelayedEventKind(StrEnum):
    DISABLE_ATTACHMENT = "disable_attachment"
    DISABLE_TETHER = "disable_tether"
    DISABLE_ENTITY = "disable_entity"
    ENABLE_OPENING = "enable_opening"


class DelayedEvent(FrozenModel):
    """One queued event, ordered by due step, priority, then insertion order."""

    event_id: str = Field(pattern=r"^v[0-9]{4}$")
    due_step: int = Field(ge=1)
    priority: int = Field(ge=0)
    insertion_order: int = Field(ge=0)
    kind: DelayedEventKind
    target_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_declared_priority(self) -> DelayedEvent:
        expected = EVENT_PRIORITY[self.kind.value]
        if self.priority != expected:
            raise ValueError(
                f"Event priority for {self.kind.value} must be {expected}, observed {self.priority}"
            )
        return self


def event_sort_key(event: DelayedEvent) -> tuple[int, int, int, str]:
    """Stable total ordering for delayed events."""

    return (event.due_step, event.priority, event.insertion_order, event.event_id)
