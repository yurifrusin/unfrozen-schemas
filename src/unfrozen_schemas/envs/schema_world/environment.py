"""Small Gymnasium-style wrapper around the pure SchemaWorld transition functions."""

from __future__ import annotations

from unfrozen_schemas.envs.schema_world.actions import Action
from unfrozen_schemas.envs.schema_world.dynamics import TransitionResult, transition
from unfrozen_schemas.envs.schema_world.protocol import ResetResult, StepResult
from unfrozen_schemas.envs.schema_world.serialization import canonical_hash, primary_observation
from unfrozen_schemas.envs.schema_world.state import WorldState
from unfrozen_schemas.envs.schema_world.templates import TemplateFamily, generate_matched_pair


class SchemaWorld:
    """Stateful protocol adapter; scientific dynamics remain in the pure ``transition`` function."""

    def __init__(
        self,
        template_id: TemplateFamily,
        *,
        condition_index: int = 0,
        gravity_per_step: int = -100,
        max_steps: int = 4,
    ) -> None:
        if condition_index not in {0, 1}:
            raise ValueError("condition_index must be 0 or 1")
        self.template_id = template_id
        self.condition_index = condition_index
        self.gravity_per_step = gravity_per_step
        self.max_steps = max_steps
        self._state: WorldState | None = None
        self._last_transition: TransitionResult | None = None

    @property
    def privileged_state(self) -> WorldState:
        if self._state is None:
            raise RuntimeError("SchemaWorld must be reset before state access")
        return self._state

    @property
    def last_transition(self) -> TransitionResult | None:
        return self._last_transition

    def reset(self, *, seed: int, noise_seed: int) -> ResetResult:
        pair = generate_matched_pair(
            self.template_id,
            seed=seed,
            noise_seed=noise_seed,
            gravity=self.gravity_per_step,
            max_steps=self.max_steps,
        )
        plan = pair.episodes[self.condition_index]
        self._state = plan.initial_state
        self._last_transition = None
        return ResetResult(
            observation=primary_observation(self._state),
            privileged_state=self._state,
            info={
                "episode_id": plan.episode_id,
                "pair_id": plan.parent_pair_id,
                "template_id": plan.template_id.value,
                "environment_version": plan.environment_version,
                "seed": seed,
                "noise_seed": noise_seed,
            },
        )

    def step(self, action: Action) -> StepResult:
        before = self.privileged_state
        result = transition(before, action)
        self._state = result.state
        self._last_transition = result
        observation = primary_observation(result.state)
        return StepResult(
            observation=observation,
            privileged_state=result.state,
            reward=0,
            terminated=False,
            truncated=result.state.terminated,
            info={
                "environment_version": result.state.environment_version,
                "step_index": result.state.step_index,
                "stage_order": result.trace.stage_order,
                "trace_hash": canonical_hash(result.trace),
            },
            transition_hash=result.transition_hash,
        )
