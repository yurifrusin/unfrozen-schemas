"""Canonical logical serialization and non-privileged observation derivation."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any, Final, Literal

from pydantic import BaseModel, Field

from unfrozen_schemas.config import FrozenModel
from unfrozen_schemas.envs.schema_world.state import EntityRole, WorldState

FORBIDDEN_RELATION_LABELS: Final[frozenset[str]] = frozenset(
    {
        "INSIDE",
        "OUTSIDE",
        "SUPPORTED",
        "UNSUPPORTED",
        "BLOCKED",
        "CONNECTED",
        "CONTAINMENT",
        "SUPPORT",
    }
)
ENTITY_KIND_CODES: Final[dict[EntityRole, int]] = {
    role: index for index, role in enumerate(EntityRole, start=1)
}


class ObservedEntity(FrozenModel):
    entity_id: str
    kind_code: int = Field(ge=1)
    x: int
    y: int
    width: int
    height: int
    velocity_x: int
    velocity_y: int
    active: bool


class ObservedBoundary(FrozenModel):
    boundary_id: str
    body_id: str
    thickness: int
    closed: bool


class ObservedAperture(FrozenModel):
    aperture_id: str
    boundary_id: str
    side_code: int = Field(ge=1, le=4)
    span_start: int
    span_end: int
    enabled: bool


class ObservedEdge(FrozenModel):
    edge_id: str
    endpoint_a: str
    endpoint_b: str
    mechanism_code: Literal[1, 2]
    active: bool
    max_length: int | None


class PrimaryObservation(FrozenModel):
    """Schema-neutral primary observation containing geometry and observable mechanisms only."""

    schema_version: Literal["1"] = "1"
    environment_version: str
    coordinate_unit: str
    step_index: int
    entities: tuple[ObservedEntity, ...]
    boundaries: tuple[ObservedBoundary, ...]
    apertures: tuple[ObservedAperture, ...]
    edges: tuple[ObservedEdge, ...]


def _logical_data(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _logical_data(value.model_dump(mode="json"))
    if isinstance(value, Mapping):
        return {str(key): _logical_data(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_logical_data(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    return value


def canonical_record_bytes(value: BaseModel | Mapping[str, Any] | Sequence[Any]) -> bytes:
    """Return stable logical JSON without paths, timestamps, or writer metadata."""

    data = _logical_data(value)
    return (
        json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def canonical_hash(value: BaseModel | Mapping[str, Any] | Sequence[Any]) -> str:
    return hashlib.sha256(canonical_record_bytes(value)).hexdigest()


def primary_observation(state: WorldState) -> PrimaryObservation:
    side_codes = {"left": 1, "right": 2, "bottom": 3, "top": 4}
    observation = PrimaryObservation(
        environment_version=state.environment_version,
        coordinate_unit=state.coordinate_unit,
        step_index=state.step_index,
        entities=tuple(
            ObservedEntity(
                entity_id=entity.entity_id,
                kind_code=ENTITY_KIND_CODES[entity.role],
                x=entity.x,
                y=entity.y,
                width=entity.width,
                height=entity.height,
                velocity_x=entity.velocity_x,
                velocity_y=entity.velocity_y,
                active=entity.active,
            )
            for entity in state.entities
        ),
        boundaries=tuple(
            ObservedBoundary(
                boundary_id=boundary.boundary_id,
                body_id=boundary.container_id,
                thickness=boundary.thickness,
                closed=boundary.closed,
            )
            for boundary in state.boundaries
        ),
        apertures=tuple(
            ObservedAperture(
                aperture_id=opening.opening_id,
                boundary_id=opening.boundary_id,
                side_code=side_codes[opening.side.value],
                span_start=opening.span_start,
                span_end=opening.span_end,
                enabled=opening.enabled,
            )
            for opening in state.openings
        ),
        edges=tuple(
            [
                ObservedEdge(
                    edge_id=item.attachment_id,
                    endpoint_a=item.object_id,
                    endpoint_b=item.anchor_id,
                    mechanism_code=1,
                    active=item.active,
                    max_length=None,
                )
                for item in state.attachments
            ]
            + [
                ObservedEdge(
                    edge_id=item.tether_id,
                    endpoint_a=item.object_id,
                    endpoint_b=item.anchor_id,
                    mechanism_code=2,
                    active=item.active,
                    max_length=item.max_length,
                )
                for item in state.tethers
            ]
        ),
    )
    assert_relation_labels_absent(observation)
    return observation


def assert_relation_labels_absent(value: BaseModel | Mapping[str, Any] | Sequence[Any]) -> None:
    payload = canonical_record_bytes(value).decode("utf-8").upper()
    leaked = sorted(label for label in FORBIDDEN_RELATION_LABELS if label in payload)
    if leaked:
        raise ValueError(f"Primary observation contains forbidden relation labels: {leaked}")
