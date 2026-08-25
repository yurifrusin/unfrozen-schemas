"""Immutable integer scientific state for SchemaWorld Core."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from unfrozen_schemas.config import FrozenModel
from unfrozen_schemas.envs.schema_world.events import DelayedEvent, event_sort_key

ENVIRONMENT_VERSION = "schemaworld-core-v1"
COORDINATE_UNIT = "microunit"
COORDINATE_MIN = 0
COORDINATE_MAX = 10_000


class EntityRole(StrEnum):
    AGENT = "agent"
    OBJECT = "object"
    CONTAINER = "container"
    GATE = "gate"
    SUPPORT = "support"
    ANCHOR = "anchor"
    DISTRACTOR = "distractor"


class BoundarySide(StrEnum):
    LEFT = "left"
    RIGHT = "right"
    BOTTOM = "bottom"
    TOP = "top"


class Entity(FrozenModel):
    """Axis-aligned body with exact lower-left position and dimensions."""

    entity_id: str = Field(pattern=r"^e[0-9]{4}$")
    role: EntityRole
    x: int = Field(ge=COORDINATE_MIN, le=COORDINATE_MAX)
    y: int = Field(ge=COORDINATE_MIN, le=COORDINATE_MAX)
    width: int = Field(gt=0, le=COORDINATE_MAX)
    height: int = Field(gt=0, le=COORDINATE_MAX)
    velocity_x: int = 0
    velocity_y: int = 0
    active: bool = True
    movable: bool = False
    affected_by_gravity: bool = False

    @model_validator(mode="after")
    def validate_extent(self) -> Entity:
        if self.x + self.width > COORDINATE_MAX or self.y + self.height > COORDINATE_MAX:
            raise ValueError("Entity extent must remain inside the global coordinate bounds")
        if self.affected_by_gravity and not self.movable:
            raise ValueError("Only movable entities may be affected by gravity")
        return self


class Boundary(FrozenModel):
    """Closed or open perimeter belonging to one container entity."""

    boundary_id: str = Field(pattern=r"^b[0-9]{4}$")
    container_id: str = Field(pattern=r"^e[0-9]{4}$")
    thickness: int = Field(gt=0)
    closed: bool = True


class Opening(FrozenModel):
    """A bounded aperture in one boundary side, optionally controlled by a gate body."""

    opening_id: str = Field(pattern=r"^o[0-9]{4}$")
    boundary_id: str = Field(pattern=r"^b[0-9]{4}$")
    side: BoundarySide
    span_start: int = Field(ge=COORDINATE_MIN, le=COORDINATE_MAX)
    span_end: int = Field(ge=COORDINATE_MIN, le=COORDINATE_MAX)
    enabled: bool = False
    gate_id: str | None = Field(default=None, pattern=r"^e[0-9]{4}$")

    @model_validator(mode="after")
    def validate_span(self) -> Opening:
        if self.span_end <= self.span_start:
            raise ValueError("Opening span_end must be greater than span_start")
        return self


class Attachment(FrozenModel):
    """Direct mechanical attachment between an object and an anchor entity."""

    attachment_id: str = Field(pattern=r"^a[0-9]{4}$")
    object_id: str = Field(pattern=r"^e[0-9]{4}$")
    anchor_id: str = Field(pattern=r"^e[0-9]{4}$")
    active: bool = True
    load_bearing: bool = True


class Tether(FrozenModel):
    """Tension-capable connection with an exact maximum centre-to-centre length."""

    tether_id: str = Field(pattern=r"^t[0-9]{4}$")
    object_id: str = Field(pattern=r"^e[0-9]{4}$")
    anchor_id: str = Field(pattern=r"^e[0-9]{4}$")
    max_length: int = Field(gt=0)
    active: bool = True
    load_bearing: bool = True


class WorldState(FrozenModel):
    """Complete privileged scientific state; ordinary observations are derived separately."""

    schema_version: Literal["1"] = "1"
    environment_version: Literal["schemaworld-core-v1"] = "schemaworld-core-v1"
    coordinate_unit: Literal["microunit"] = "microunit"
    fixed_point_scale: Literal[1] = 1
    coordinate_min: Literal[0] = 0
    coordinate_max: Literal[10_000] = 10_000
    gravity_per_step: int = Field(le=0)
    seed: int = Field(ge=0, le=4_294_967_295)
    noise_seed: int = Field(ge=0, le=4_294_967_295)
    step_index: int = Field(ge=0)
    max_steps: int = Field(gt=0)
    terminated: bool = False
    entities: tuple[Entity, ...]
    boundaries: tuple[Boundary, ...] = ()
    openings: tuple[Opening, ...] = ()
    attachments: tuple[Attachment, ...] = ()
    tethers: tuple[Tether, ...] = ()
    delayed_events: tuple[DelayedEvent, ...] = ()

    @model_validator(mode="after")
    def validate_graph_and_ordering(self) -> WorldState:
        identifiers = [entity.entity_id for entity in self.entities]
        identifiers += [boundary.boundary_id for boundary in self.boundaries]
        identifiers += [opening.opening_id for opening in self.openings]
        identifiers += [attachment.attachment_id for attachment in self.attachments]
        identifiers += [tether.tether_id for tether in self.tethers]
        identifiers += [event.event_id for event in self.delayed_events]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("All state identifiers must be globally unique")
        if tuple(sorted(self.entities, key=lambda item: item.entity_id)) != self.entities:
            raise ValueError("Entities must use stable entity_id ordering")
        if tuple(sorted(self.boundaries, key=lambda item: item.boundary_id)) != self.boundaries:
            raise ValueError("Boundaries must use stable boundary_id ordering")
        if tuple(sorted(self.openings, key=lambda item: item.opening_id)) != self.openings:
            raise ValueError("Openings must use stable opening_id ordering")
        if tuple(sorted(self.attachments, key=lambda item: item.attachment_id)) != self.attachments:
            raise ValueError("Attachments must use stable attachment_id ordering")
        if tuple(sorted(self.tethers, key=lambda item: item.tether_id)) != self.tethers:
            raise ValueError("Tethers must use stable tether_id ordering")
        if tuple(sorted(self.delayed_events, key=event_sort_key)) != self.delayed_events:
            raise ValueError("Delayed events must use canonical queue ordering")

        entities = {entity.entity_id: entity for entity in self.entities}
        boundaries = {boundary.boundary_id: boundary for boundary in self.boundaries}
        for boundary in self.boundaries:
            container = entities.get(boundary.container_id)
            if container is None or container.role is not EntityRole.CONTAINER:
                raise ValueError("Every boundary must reference a container entity")
            if 2 * boundary.thickness >= min(container.width, container.height):
                raise ValueError("Boundary thickness leaves no positive container interior")
        for opening in self.openings:
            if opening.boundary_id not in boundaries:
                raise ValueError("Every opening must reference an existing boundary")
            if opening.gate_id is not None:
                gate = entities.get(opening.gate_id)
                if gate is None or gate.role is not EntityRole.GATE:
                    raise ValueError("Opening gate_id must reference a gate entity")
        for attachment in self.attachments:
            if attachment.object_id not in entities or attachment.anchor_id not in entities:
                raise ValueError("Every attachment and tether endpoint must exist")
            if attachment.object_id == attachment.anchor_id:
                raise ValueError("A connection cannot attach an entity to itself")
        for tether in self.tethers:
            if tether.object_id not in entities or tether.anchor_id not in entities:
                raise ValueError("Every attachment and tether endpoint must exist")
            if tether.object_id == tether.anchor_id:
                raise ValueError("A connection cannot attach an entity to itself")
        if self.step_index > self.max_steps:
            raise ValueError("step_index cannot exceed max_steps")
        if self.terminated != (self.step_index >= self.max_steps):
            raise ValueError("terminated must exactly reflect the max-step condition")
        return self

    def entity(self, entity_id: str) -> Entity:
        for entity in self.entities:
            if entity.entity_id == entity_id:
                return entity
        raise KeyError(entity_id)
