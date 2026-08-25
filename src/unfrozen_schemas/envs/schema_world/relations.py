"""Privileged relation derivation from geometry, mechanics, and transition traces."""

from __future__ import annotations

from pydantic import Field

from unfrozen_schemas.config import FrozenModel
from unfrozen_schemas.envs.schema_world.dynamics import (
    TransitionTrace,
    derive_contacts,
    derive_functional_supports,
)
from unfrozen_schemas.envs.schema_world.relation_kinds import RelationKind as RelationKind
from unfrozen_schemas.envs.schema_world.state import Entity, WorldState


class RelationRecord(FrozenModel):
    """One derived verifier fact with a compact auditable evidence reference."""

    relation: RelationKind
    subject_id: str = Field(min_length=1)
    object_id: str | None = None
    evidence_ids: tuple[str, ...] = ()


def _inside(entity: Entity, container: Entity, thickness: int) -> bool:
    return (
        entity.x >= container.x + thickness
        and entity.x + entity.width <= container.x + container.width - thickness
        and entity.y >= container.y + thickness
        and entity.y + entity.height <= container.y + container.height - thickness
    )


def derive_relations(
    state: WorldState, trace: TransitionTrace | None = None
) -> tuple[RelationRecord, ...]:
    """Derive all M1 verifier relations without reading an authoritative target flag."""

    records: list[RelationRecord] = []
    entities = {entity.entity_id: entity for entity in state.entities}
    movable = tuple(entity for entity in state.entities if entity.active and entity.movable)
    for boundary in state.boundaries:
        container = entities[boundary.container_id]
        for entity in movable:
            relation = (
                RelationKind.INTERIOR
                if _inside(entity, container, boundary.thickness)
                else RelationKind.EXTERIOR
            )
            records.append(
                RelationRecord(
                    relation=relation,
                    subject_id=entity.entity_id,
                    object_id=container.entity_id,
                    evidence_ids=(boundary.boundary_id,),
                )
            )

    supports = derive_functional_supports(state, derive_contacts(state))
    for support in supports:
        records.append(
            RelationRecord(
                relation=RelationKind.FUNCTIONAL_SUPPORT,
                subject_id=support.object_id,
                object_id=support.mechanism_id,
                evidence_ids=(support.kind.value,),
            )
        )
    for attachment in state.attachments:
        if attachment.active:
            records.append(
                RelationRecord(
                    relation=RelationKind.CONNECTION,
                    subject_id=attachment.object_id,
                    object_id=attachment.anchor_id,
                    evidence_ids=(attachment.attachment_id,),
                )
            )
    for tether in state.tethers:
        if tether.active:
            records.append(
                RelationRecord(
                    relation=RelationKind.CONNECTION,
                    subject_id=tether.object_id,
                    object_id=tether.anchor_id,
                    evidence_ids=(tether.tether_id,),
                )
            )
    if trace is not None:
        for blocker in trace.blocked_by:
            records.append(
                RelationRecord(
                    relation=RelationKind.BLOCKAGE,
                    subject_id=trace.action.target_id or trace.action.actor_id or "world",
                    object_id=blocker,
                    evidence_ids=(trace.action.kind.value,),
                )
            )
        for entity_id in trace.moved_entities:
            records.append(
                RelationRecord(
                    relation=RelationKind.MOVEMENT,
                    subject_id=entity_id,
                    evidence_ids=(trace.action.kind.value,),
                )
            )
        for entity_id in trace.falling_entities:
            records.append(
                RelationRecord(
                    relation=RelationKind.FALLING,
                    subject_id=entity_id,
                    evidence_ids=(trace.action.kind.value,),
                )
            )
    return tuple(
        sorted(
            records,
            key=lambda item: (
                item.relation.value,
                item.subject_id,
                item.object_id or "",
                item.evidence_ids,
            ),
        )
    )
