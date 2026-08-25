"""Deterministic matched counterfactual templates for the M1 core mechanisms."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum
from typing import Any

from pydantic import Field

from unfrozen_schemas.config import FrozenModel
from unfrozen_schemas.envs.schema_world.actions import Action, ActionKind
from unfrozen_schemas.envs.schema_world.rng import DeterministicGenerator
from unfrozen_schemas.envs.schema_world.serialization import (
    canonical_hash,
    primary_observation,
)
from unfrozen_schemas.envs.schema_world.state import (
    ENVIRONMENT_VERSION,
    Boundary,
    BoundarySide,
    Entity,
    EntityRole,
    Opening,
    Tether,
    WorldState,
)


class SchemaName(StrEnum):
    CONTAINMENT = "CONTAINMENT"
    SUPPORT = "SUPPORT"


class TemplateFamily(StrEnum):
    CONTAINMENT_GATE = "containment_gate_v1"
    SUPPORT_PLATFORM = "support_platform_v1"
    SUPPORT_TENSION = "support_tension_v1"


class PairParityError(ValueError):
    """Raised when a claimed pair differs outside its declared target factor."""


class EpisodePlan(FrozenModel):
    """One immutable counterfactual member before dynamics are executed."""

    episode_id: str = Field(pattern=r"^ep-[a-f0-9]{16}-[01]$")
    parent_pair_id: str = Field(pattern=r"^pair-[a-f0-9]{16}$")
    condition_index: int = Field(ge=0, le=1)
    template_id: TemplateFamily
    schema_name: SchemaName
    environment_version: str
    seed: int = Field(ge=0, le=4_294_967_295)
    noise_seed: int = Field(ge=0, le=4_294_967_295)
    audited_target_factor: str
    declared_difference_paths: tuple[str, ...]
    initial_state: WorldState
    actions: tuple[Action, ...]
    initial_state_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    initial_observation_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    action_sequence_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


class MatchedPair(FrozenModel):
    pair_id: str = Field(pattern=r"^pair-[a-f0-9]{16}$")
    target_factor: str
    declared_difference_paths: tuple[str, ...]
    episodes: tuple[EpisodePlan, EpisodePlan]


def _stable_id(prefix: str, value: Mapping[str, Any]) -> str:
    return f"{prefix}-{canonical_hash(value)[:16]}"


def _plan(
    *,
    pair_id: str,
    condition_index: int,
    template_id: TemplateFamily,
    schema_name: SchemaName,
    seed: int,
    noise_seed: int,
    target_factor: str,
    difference_paths: tuple[str, ...],
    initial_state: WorldState,
    actions: tuple[Action, ...],
) -> EpisodePlan:
    identity = {
        "pair_id": pair_id,
        "condition_index": condition_index,
        "initial_state": initial_state,
        "actions": actions,
    }
    return EpisodePlan(
        episode_id=f"{_stable_id('ep', identity)}-{condition_index}",
        parent_pair_id=pair_id,
        condition_index=condition_index,
        template_id=template_id,
        schema_name=schema_name,
        environment_version=ENVIRONMENT_VERSION,
        seed=seed,
        noise_seed=noise_seed,
        audited_target_factor=target_factor,
        declared_difference_paths=difference_paths,
        initial_state=initial_state,
        actions=actions,
        initial_state_hash=canonical_hash(initial_state),
        initial_observation_hash=canonical_hash(primary_observation(initial_state)),
        action_sequence_hash=canonical_hash(actions),
    )


def _flatten(value: Any, path: str = "") -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    if isinstance(value, Mapping):
        flattened: dict[str, Any] = {}
        for key in sorted(value):
            child = f"{path}.{key}" if path else str(key)
            flattened.update(_flatten(value[key], child))
        return flattened
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        flattened = {}
        for index, item in enumerate(value):
            child = f"{path}.{index}" if path else str(index)
            flattened.update(_flatten(item, child))
        if not value:
            flattened[path] = []
        return flattened
    return {path: value}


def audit_matched_pair(pair: MatchedPair) -> tuple[str, ...]:
    """Require the exact declared leaf differences and no others."""

    left, right = pair.episodes
    left_payload = _flatten({"initial_state": left.initial_state, "actions": left.actions})
    right_payload = _flatten({"initial_state": right.initial_state, "actions": right.actions})
    all_paths = set(left_payload) | set(right_payload)
    observed = tuple(
        sorted(path for path in all_paths if left_payload.get(path) != right_payload.get(path))
    )
    declared = tuple(sorted(pair.declared_difference_paths))
    if observed != declared:
        raise PairParityError(
            f"Matched pair {pair.pair_id} differs outside its declaration: "
            f"declared={declared}, observed={observed}"
        )
    return observed


def _containment_pair(seed: int, noise_seed: int, gravity: int, max_steps: int) -> MatchedPair:
    rng = DeterministicGenerator(seed)
    y = 350 + 25 * rng.randbelow(5)
    entities = (
        Entity(
            entity_id="e0001",
            role=EntityRole.OBJECT,
            x=700,
            y=y,
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
            y=300,
            width=20,
            height=400,
        ),
    )
    boundary = Boundary(boundary_id="b0001", container_id="e0002", thickness=20)
    opening = Opening(
        opening_id="o0001",
        boundary_id="b0001",
        side=BoundarySide.RIGHT,
        span_start=300,
        span_end=700,
        enabled=False,
        gate_id="e0003",
    )
    closed_state = WorldState(
        gravity_per_step=gravity,
        seed=seed,
        noise_seed=noise_seed,
        step_index=0,
        max_steps=max_steps,
        entities=entities,
        boundaries=(boundary,),
        openings=(opening,),
    )
    open_state = closed_state.model_copy(
        update={"openings": (opening.model_copy(update={"enabled": True}),)}
    )
    actions = (Action(kind=ActionKind.EXIT, target_id="e0001", delta_x=300),)
    target_factor = "right aperture enabled before identical planned exit"
    differences = ("initial_state.openings.0.enabled",)
    pair_id = _stable_id(
        "pair", {"template": TemplateFamily.CONTAINMENT_GATE, "seed": seed, "noise": noise_seed}
    )
    pair = MatchedPair(
        pair_id=pair_id,
        target_factor=target_factor,
        declared_difference_paths=differences,
        episodes=(
            _plan(
                pair_id=pair_id,
                condition_index=0,
                template_id=TemplateFamily.CONTAINMENT_GATE,
                schema_name=SchemaName.CONTAINMENT,
                seed=seed,
                noise_seed=noise_seed,
                target_factor=target_factor,
                difference_paths=differences,
                initial_state=closed_state,
                actions=actions,
            ),
            _plan(
                pair_id=pair_id,
                condition_index=1,
                template_id=TemplateFamily.CONTAINMENT_GATE,
                schema_name=SchemaName.CONTAINMENT,
                seed=seed,
                noise_seed=noise_seed,
                target_factor=target_factor,
                difference_paths=differences,
                initial_state=open_state,
                actions=actions,
            ),
        ),
    )
    audit_matched_pair(pair)
    return pair


def _support_entities(y: int, *, side_platform: bool = False) -> tuple[Entity, ...]:
    platform_x = 600 if side_platform else 400
    platform_y = y if side_platform else y - 100
    return (
        Entity(
            entity_id="e0001",
            role=EntityRole.OBJECT,
            x=400,
            y=y,
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
        ),
        Entity(
            entity_id="e0003",
            role=EntityRole.ANCHOR,
            x=450,
            y=900,
            width=100,
            height=100,
        ),
    )


def _action_pair(
    *,
    template_id: TemplateFamily,
    seed: int,
    noise_seed: int,
    gravity: int,
    max_steps: int,
    state: WorldState,
    left_action: Action,
    right_action: Action,
    target_factor: str,
) -> MatchedPair:
    differences = ("actions.0.kind", "actions.0.target_id")
    pair_id = _stable_id("pair", {"template": template_id, "seed": seed, "noise": noise_seed})
    del gravity, max_steps
    pair = MatchedPair(
        pair_id=pair_id,
        target_factor=target_factor,
        declared_difference_paths=differences,
        episodes=(
            _plan(
                pair_id=pair_id,
                condition_index=0,
                template_id=template_id,
                schema_name=SchemaName.SUPPORT,
                seed=seed,
                noise_seed=noise_seed,
                target_factor=target_factor,
                difference_paths=differences,
                initial_state=state,
                actions=(left_action,),
            ),
            _plan(
                pair_id=pair_id,
                condition_index=1,
                template_id=template_id,
                schema_name=SchemaName.SUPPORT,
                seed=seed,
                noise_seed=noise_seed,
                target_factor=target_factor,
                difference_paths=differences,
                initial_state=state,
                actions=(right_action,),
            ),
        ),
    )
    audit_matched_pair(pair)
    return pair


def _platform_pair(seed: int, noise_seed: int, gravity: int, max_steps: int) -> MatchedPair:
    rng = DeterministicGenerator(seed)
    y = 500 + 20 * rng.randbelow(4)
    state = WorldState(
        gravity_per_step=gravity,
        seed=seed,
        noise_seed=noise_seed,
        step_index=0,
        max_steps=max_steps,
        entities=_support_entities(y),
    )
    return _action_pair(
        template_id=TemplateFamily.SUPPORT_PLATFORM,
        seed=seed,
        noise_seed=noise_seed,
        gravity=gravity,
        max_steps=max_steps,
        state=state,
        left_action=Action(kind=ActionKind.REMOVE_SUPPORT, target_id="e0002"),
        right_action=Action(kind=ActionKind.NOOP),
        target_factor="removal of the actual lower support",
    )


def _tension_pair(seed: int, noise_seed: int, gravity: int, max_steps: int) -> MatchedPair:
    state = WorldState(
        gravity_per_step=gravity,
        seed=seed,
        noise_seed=noise_seed,
        step_index=0,
        max_steps=max_steps,
        entities=_support_entities(500, side_platform=True),
        tethers=(
            Tether(
                tether_id="t0001",
                object_id="e0001",
                anchor_id="e0003",
                max_length=400,
            ),
        ),
    )
    return _action_pair(
        template_id=TemplateFamily.SUPPORT_TENSION,
        seed=seed,
        noise_seed=noise_seed,
        gravity=gravity,
        max_steps=max_steps,
        state=state,
        left_action=Action(kind=ActionKind.REMOVE_SUPPORT, target_id="e0002"),
        right_action=Action(kind=ActionKind.DETACH, target_id="t0001"),
        target_factor="removal of visible side contact versus removal of load-bearing tension",
    )


def generate_matched_pair(
    template_id: TemplateFamily,
    *,
    seed: int,
    noise_seed: int,
    gravity: int = -100,
    max_steps: int = 4,
) -> MatchedPair:
    """Generate and immediately parity-audit one deterministic matched pair."""

    if template_id is TemplateFamily.CONTAINMENT_GATE:
        return _containment_pair(seed, noise_seed, gravity, max_steps)
    if template_id is TemplateFamily.SUPPORT_PLATFORM:
        return _platform_pair(seed, noise_seed, gravity, max_steps)
    return _tension_pair(seed, noise_seed, gravity, max_steps)
