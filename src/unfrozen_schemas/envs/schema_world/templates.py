"""Deterministic matched counterfactual templates for the M1 core mechanisms."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum
from typing import Any, Literal

from pydantic import Field, model_validator

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
    environment_version: Literal["schemaworld-core-v1"]
    seed: int = Field(ge=0, le=4_294_967_295)
    noise_seed: int = Field(ge=0, le=4_294_967_295)
    audited_target_factor: str
    declared_difference_paths: tuple[str, ...]
    initial_state: WorldState
    actions: tuple[Action, ...] = Field(min_length=1)
    initial_state_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    initial_observation_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    action_sequence_hash: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_embedded_identity(self) -> EpisodePlan:
        if self.environment_version != self.initial_state.environment_version:
            raise ValueError("Episode environment version must match its initial state")
        if self.seed != self.initial_state.seed or self.noise_seed != self.initial_state.noise_seed:
            raise ValueError("Episode seeds must match its initial state")
        if self.initial_state.step_index + len(self.actions) > self.initial_state.max_steps:
            raise ValueError("Episode actions exceed the initial state's remaining horizon")
        if self.initial_state_hash != canonical_hash(self.initial_state):
            raise ValueError("Episode initial_state_hash does not match its initial state")
        if self.initial_observation_hash != canonical_hash(primary_observation(self.initial_state)):
            raise ValueError(
                "Episode initial_observation_hash does not match its initial observation"
            )
        if self.action_sequence_hash != canonical_hash(self.actions):
            raise ValueError("Episode action_sequence_hash does not match its actions")
        return self


class PairIdentity(FrozenModel):
    """Canonical pre-ID payload containing every causally relevant matched-pair input."""

    environment_version: Literal["schemaworld-core-v1"] = "schemaworld-core-v1"
    template_family: TemplateFamily
    seed: int = Field(ge=0, le=4_294_967_295)
    noise_seed: int = Field(ge=0, le=4_294_967_295)
    gravity_per_step: int = Field(le=0)
    max_steps: int = Field(gt=0)
    initial_states: tuple[WorldState, WorldState]
    actions: tuple[tuple[Action, ...], tuple[Action, ...]]
    target_factor: str = Field(min_length=1)
    declared_difference_paths: tuple[str, ...]


class MatchedPair(FrozenModel):
    pair_id: str = Field(pattern=r"^pair-[a-f0-9]{16}$")
    target_factor: str
    declared_difference_paths: tuple[str, ...]
    episodes: tuple[EpisodePlan, EpisodePlan]


def _stable_id(prefix: str, value: Mapping[str, Any]) -> str:
    return f"{prefix}-{canonical_hash(value)[:16]}"


def derive_pair_id(identity: PairIdentity) -> str:
    """Derive a pair ID without including pair or episode IDs in the hashed payload."""

    return _stable_id("pair", identity.model_dump(mode="json"))


def derive_episode_id(identity: PairIdentity, condition_index: int) -> str:
    """Derive a stable condition-specific episode ID from the same pre-ID identity."""

    return (
        f"{_stable_id('ep', {'pair_identity': identity, 'condition_index': condition_index})}"
        f"-{condition_index}"
    )


def _plan(
    *,
    identity: PairIdentity,
    condition_index: int,
    schema_name: SchemaName,
) -> EpisodePlan:
    pair_id = derive_pair_id(identity)
    initial_state = identity.initial_states[condition_index]
    actions = identity.actions[condition_index]
    return EpisodePlan(
        episode_id=derive_episode_id(identity, condition_index),
        parent_pair_id=pair_id,
        condition_index=condition_index,
        template_id=identity.template_family,
        schema_name=schema_name,
        environment_version=ENVIRONMENT_VERSION,
        seed=identity.seed,
        noise_seed=identity.noise_seed,
        audited_target_factor=identity.target_factor,
        declared_difference_paths=identity.declared_difference_paths,
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
    if (left.condition_index, right.condition_index) != (0, 1):
        raise PairParityError(f"Matched pair {pair.pair_id} must use condition order 0, 1")
    common_fields = (
        left.template_id == right.template_id
        and left.schema_name == right.schema_name
        and left.environment_version == right.environment_version
        and left.seed == right.seed
        and left.noise_seed == right.noise_seed
        and left.audited_target_factor == right.audited_target_factor == pair.target_factor
        and left.declared_difference_paths
        == right.declared_difference_paths
        == pair.declared_difference_paths
        and left.parent_pair_id == right.parent_pair_id == pair.pair_id
    )
    if not common_fields:
        raise PairParityError(f"Matched pair {pair.pair_id} has inconsistent identity metadata")
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
    identity = PairIdentity(
        template_family=left.template_id,
        seed=left.seed,
        noise_seed=left.noise_seed,
        gravity_per_step=left.initial_state.gravity_per_step,
        max_steps=left.initial_state.max_steps,
        initial_states=(left.initial_state, right.initial_state),
        actions=(left.actions, right.actions),
        target_factor=pair.target_factor,
        declared_difference_paths=pair.declared_difference_paths,
    )
    expected_pair_id = derive_pair_id(identity)
    if pair.pair_id != expected_pair_id:
        raise PairParityError(
            f"Matched pair ID mismatch: expected {expected_pair_id}, observed {pair.pair_id}"
        )
    expected_episode_ids = (
        derive_episode_id(identity, 0),
        derive_episode_id(identity, 1),
    )
    observed_episode_ids = (left.episode_id, right.episode_id)
    if observed_episode_ids != expected_episode_ids:
        raise PairParityError(
            "Matched episode ID mismatch: "
            f"expected={expected_episode_ids}, observed={observed_episode_ids}"
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
    identity = PairIdentity(
        template_family=TemplateFamily.CONTAINMENT_GATE,
        seed=seed,
        noise_seed=noise_seed,
        gravity_per_step=gravity,
        max_steps=max_steps,
        initial_states=(closed_state, open_state),
        actions=(actions, actions),
        target_factor=target_factor,
        declared_difference_paths=differences,
    )
    pair_id = derive_pair_id(identity)
    pair = MatchedPair(
        pair_id=pair_id,
        target_factor=target_factor,
        declared_difference_paths=differences,
        episodes=(
            _plan(
                identity=identity,
                condition_index=0,
                schema_name=SchemaName.CONTAINMENT,
            ),
            _plan(
                identity=identity,
                condition_index=1,
                schema_name=SchemaName.CONTAINMENT,
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
    identity = PairIdentity(
        template_family=template_id,
        seed=seed,
        noise_seed=noise_seed,
        gravity_per_step=gravity,
        max_steps=max_steps,
        initial_states=(state, state),
        actions=((left_action,), (right_action,)),
        target_factor=target_factor,
        declared_difference_paths=differences,
    )
    pair_id = derive_pair_id(identity)
    pair = MatchedPair(
        pair_id=pair_id,
        target_factor=target_factor,
        declared_difference_paths=differences,
        episodes=(
            _plan(
                identity=identity,
                condition_index=0,
                schema_name=SchemaName.SUPPORT,
            ),
            _plan(
                identity=identity,
                condition_index=1,
                schema_name=SchemaName.SUPPORT,
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
                length=350,
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
