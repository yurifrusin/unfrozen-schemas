"""Closed narrative, intervention, and structural-signature contracts for M2.2."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from typing import Any

from unfrozen_schemas.envs.schema_world.actions import Action, ActionKind
from unfrozen_schemas.envs.schema_world.serialization import primary_observation
from unfrozen_schemas.envs.schema_world.state import BoundarySide, EntityRole, WorldState
from unfrozen_schemas.evaluation.literal_hashing import structural_signature_hash, template_hash
from unfrozen_schemas.evaluation.literal_models import (
    ContainmentScenarioCase,
    LiteralCausalFactor,
    LiteralDirection,
    LiteralInterventionContract,
    LiteralInterventionKind,
    LiteralMechanismKind,
    LiteralNarrativeFacts,
    LiteralOutcomeCode,
    LiteralScenarioSpec,
    LiteralSchema,
    LiteralStructuralSignatures,
    LiteralTaskFamily,
    LiteralTemplate,
    LiteralWitnessRecord,
    SupportScenarioCase,
)

_CONTRACTS: dict[ContainmentScenarioCase | SupportScenarioCase, LiteralInterventionContract] = {
    ContainmentScenarioCase.FITTING_OPENING: LiteralInterventionContract(
        scenario_case=ContainmentScenarioCase.FITTING_OPENING,
        intervention_kind=LiteralInterventionKind.OPENING_ENABLED_STATE,
        occurs_in="initial_state",
        allowed_initial_difference_paths=("openings.0.enabled",),
        allowed_action_difference_paths=(),
        required_equal_scopes=(
            "action_plan",
            "horizon",
            "initial_state_except_opening_enabled",
        ),
        causal_factor=LiteralCausalFactor.APERTURE_AVAILABILITY,
        expected_actual_outcome=LiteralOutcomeCode.MOVEMENT_SUCCEEDS,
        expected_counterfactual_outcome=LiteralOutcomeCode.MOVEMENT_BLOCKED,
    ),
    ContainmentScenarioCase.CLOSED_BOUNDARY: LiteralInterventionContract(
        scenario_case=ContainmentScenarioCase.CLOSED_BOUNDARY,
        intervention_kind=LiteralInterventionKind.OPENING_ENABLED_STATE,
        occurs_in="initial_state",
        allowed_initial_difference_paths=("openings.0.enabled",),
        allowed_action_difference_paths=(),
        required_equal_scopes=(
            "action_plan",
            "horizon",
            "initial_state_except_opening_enabled",
        ),
        causal_factor=LiteralCausalFactor.APERTURE_AVAILABILITY,
        expected_actual_outcome=LiteralOutcomeCode.MOVEMENT_BLOCKED,
        expected_counterfactual_outcome=LiteralOutcomeCode.MOVEMENT_SUCCEEDS,
    ),
    ContainmentScenarioCase.UNDERSIZED_OPENING: LiteralInterventionContract(
        scenario_case=ContainmentScenarioCase.UNDERSIZED_OPENING,
        intervention_kind=LiteralInterventionKind.OPENING_SPAN,
        occurs_in="initial_state",
        allowed_initial_difference_paths=("openings.0.span_end", "openings.0.span_start"),
        allowed_action_difference_paths=(),
        required_equal_scopes=("action_plan", "horizon", "initial_state_except_opening_span"),
        causal_factor=LiteralCausalFactor.APERTURE_SIZE,
        expected_actual_outcome=LiteralOutcomeCode.MOVEMENT_BLOCKED,
        expected_counterfactual_outcome=LiteralOutcomeCode.MOVEMENT_SUCCEEDS,
    ),
    ContainmentScenarioCase.MISALIGNED_OPENING: LiteralInterventionContract(
        scenario_case=ContainmentScenarioCase.MISALIGNED_OPENING,
        intervention_kind=LiteralInterventionKind.OPENING_ALIGNMENT,
        occurs_in="initial_state",
        allowed_initial_difference_paths=("openings.0.span_end", "openings.0.span_start"),
        allowed_action_difference_paths=(),
        required_equal_scopes=(
            "action_plan",
            "horizon",
            "initial_state_except_opening_alignment",
        ),
        causal_factor=LiteralCausalFactor.APERTURE_ALIGNMENT,
        expected_actual_outcome=LiteralOutcomeCode.MOVEMENT_BLOCKED,
        expected_counterfactual_outcome=LiteralOutcomeCode.MOVEMENT_SUCCEEDS,
    ),
    ContainmentScenarioCase.FULLY_OPEN_BOUNDARY: LiteralInterventionContract(
        scenario_case=ContainmentScenarioCase.FULLY_OPEN_BOUNDARY,
        intervention_kind=LiteralInterventionKind.BOUNDARY_CLOSURE,
        occurs_in="initial_state",
        allowed_initial_difference_paths=("boundaries.0.closed",),
        allowed_action_difference_paths=(),
        required_equal_scopes=(
            "action_plan",
            "horizon",
            "initial_state_except_boundary_closure",
        ),
        causal_factor=LiteralCausalFactor.PERIMETER_CLOSURE,
        expected_actual_outcome=LiteralOutcomeCode.MOVEMENT_SUCCEEDS,
        expected_counterfactual_outcome=LiteralOutcomeCode.MOVEMENT_BLOCKED,
    ),
    SupportScenarioCase.LOWER_SUPPORT_REMOVAL: LiteralInterventionContract(
        scenario_case=SupportScenarioCase.LOWER_SUPPORT_REMOVAL,
        intervention_kind=LiteralInterventionKind.LOWER_SUPPORT_ACTION,
        occurs_in="action",
        allowed_initial_difference_paths=(),
        allowed_action_difference_paths=("0.kind", "0.target_id"),
        required_equal_scopes=("initial_state", "horizon", "action_except_kind_and_target"),
        causal_factor=LiteralCausalFactor.LOWER_CONTACT_REMOVAL,
        expected_actual_outcome=LiteralOutcomeCode.OBJECT_FALLS,
        expected_counterfactual_outcome=LiteralOutcomeCode.OBJECT_STAYS,
    ),
    SupportScenarioCase.LOWER_SUPPORT_NOOP: LiteralInterventionContract(
        scenario_case=SupportScenarioCase.LOWER_SUPPORT_NOOP,
        intervention_kind=LiteralInterventionKind.LOWER_SUPPORT_ACTION,
        occurs_in="action",
        allowed_initial_difference_paths=(),
        allowed_action_difference_paths=("0.kind", "0.target_id"),
        required_equal_scopes=("initial_state", "horizon", "action_except_kind_and_target"),
        causal_factor=LiteralCausalFactor.LOWER_CONTACT_REMOVAL,
        expected_actual_outcome=LiteralOutcomeCode.OBJECT_STAYS,
        expected_counterfactual_outcome=LiteralOutcomeCode.OBJECT_FALLS,
    ),
    SupportScenarioCase.SIDE_CONTACT: LiteralInterventionContract(
        scenario_case=SupportScenarioCase.SIDE_CONTACT,
        intervention_kind=LiteralInterventionKind.SUPPORT_CONTACT_GEOMETRY,
        occurs_in="initial_state",
        allowed_initial_difference_paths=("entities.1.x", "entities.1.y"),
        allowed_action_difference_paths=(),
        required_equal_scopes=("action_plan", "horizon", "initial_state_except_support_pose"),
        causal_factor=LiteralCausalFactor.LOWER_CONTACT_GEOMETRY,
        expected_actual_outcome=LiteralOutcomeCode.OBJECT_FALLS,
        expected_counterfactual_outcome=LiteralOutcomeCode.OBJECT_STAYS,
    ),
    SupportScenarioCase.TETHER_CUT: LiteralInterventionContract(
        scenario_case=SupportScenarioCase.TETHER_CUT,
        intervention_kind=LiteralInterventionKind.TETHER_CUT_ACTION,
        occurs_in="action",
        allowed_initial_difference_paths=(),
        allowed_action_difference_paths=("0.kind", "0.target_id"),
        required_equal_scopes=("initial_state", "horizon", "action_except_kind_and_target"),
        causal_factor=LiteralCausalFactor.TETHER_CONTINUITY,
        expected_actual_outcome=LiteralOutcomeCode.OBJECT_FALLS,
        expected_counterfactual_outcome=LiteralOutcomeCode.OBJECT_STAYS,
    ),
    SupportScenarioCase.TETHERED_PLATFORM_REMOVAL: LiteralInterventionContract(
        scenario_case=SupportScenarioCase.TETHERED_PLATFORM_REMOVAL,
        intervention_kind=LiteralInterventionKind.TETHER_ACTION_CHOICE,
        occurs_in="action",
        allowed_initial_difference_paths=(),
        allowed_action_difference_paths=("0.kind", "0.target_id"),
        required_equal_scopes=("initial_state", "horizon", "action_except_kind_and_target"),
        causal_factor=LiteralCausalFactor.LOAD_BEARING_MECHANISM,
        expected_actual_outcome=LiteralOutcomeCode.OBJECT_STAYS,
        expected_counterfactual_outcome=LiteralOutcomeCode.OBJECT_FALLS,
    ),
    SupportScenarioCase.NONBEARING_TETHER: LiteralInterventionContract(
        scenario_case=SupportScenarioCase.NONBEARING_TETHER,
        intervention_kind=LiteralInterventionKind.TETHER_LOAD_BEARING,
        occurs_in="initial_state",
        allowed_initial_difference_paths=("tethers.0.load_bearing",),
        allowed_action_difference_paths=(),
        required_equal_scopes=(
            "action_plan",
            "horizon",
            "initial_state_except_tether_load_bearing",
        ),
        causal_factor=LiteralCausalFactor.TETHER_LOAD_BEARING,
        expected_actual_outcome=LiteralOutcomeCode.OBJECT_FALLS,
        expected_counterfactual_outcome=LiteralOutcomeCode.OBJECT_STAYS,
    ),
}


_MECHANISMS: dict[ContainmentScenarioCase | SupportScenarioCase, LiteralMechanismKind] = {
    ContainmentScenarioCase.FITTING_OPENING: LiteralMechanismKind.FITTING_APERTURE,
    ContainmentScenarioCase.CLOSED_BOUNDARY: LiteralMechanismKind.DISABLED_APERTURE,
    ContainmentScenarioCase.UNDERSIZED_OPENING: LiteralMechanismKind.UNDERSIZED_APERTURE,
    ContainmentScenarioCase.MISALIGNED_OPENING: LiteralMechanismKind.MISALIGNED_APERTURE,
    ContainmentScenarioCase.FULLY_OPEN_BOUNDARY: LiteralMechanismKind.OPEN_PERIMETER,
    SupportScenarioCase.LOWER_SUPPORT_REMOVAL: LiteralMechanismKind.LOWER_CONTACT,
    SupportScenarioCase.LOWER_SUPPORT_NOOP: LiteralMechanismKind.LOWER_CONTACT,
    SupportScenarioCase.SIDE_CONTACT: LiteralMechanismKind.SIDE_CONTACT,
    SupportScenarioCase.TETHER_CUT: LiteralMechanismKind.LOAD_BEARING_TETHER,
    SupportScenarioCase.TETHERED_PLATFORM_REMOVAL: LiteralMechanismKind.LOAD_BEARING_TETHER,
    SupportScenarioCase.NONBEARING_TETHER: LiteralMechanismKind.NONBEARING_TETHER,
}


def intervention_contract(
    case: ContainmentScenarioCase | SupportScenarioCase,
) -> LiteralInterventionContract:
    return _CONTRACTS[case]


def target_mechanism(
    case: ContainmentScenarioCase | SupportScenarioCase,
) -> LiteralMechanismKind:
    return _MECHANISMS[case]


def _opening_quality(state: WorldState, side: BoundarySide) -> str:
    boundary = state.boundaries[0]
    if not boundary.closed:
        return "fully-open-perimeter"
    opening = next((item for item in state.openings if item.side is side), None)
    if opening is None:
        return "closed-perimeter"
    if not opening.enabled:
        return "disabled-opening"
    obj = next(item for item in state.entities if item.role is EntityRole.OBJECT)
    if side in {BoundarySide.LEFT, BoundarySide.RIGHT}:
        object_start, object_end = obj.y, obj.y + obj.height
    else:
        object_start, object_end = obj.x, obj.x + obj.width
    if opening.span_start <= object_start and opening.span_end >= object_end:
        return "fitting-opening"
    if opening.span_end - opening.span_start < object_end - object_start:
        return "undersized-opening"
    return "misaligned-opening"


def _support_geometry(state: WorldState) -> str:
    obj = next(item for item in state.entities if item.role is EntityRole.OBJECT)
    support = next(item for item in state.entities if item.role is EntityRole.SUPPORT)
    horizontal_overlap = min(obj.x + obj.width, support.x + support.width) > max(obj.x, support.x)
    if obj.y == support.y + support.height and horizontal_overlap:
        return "lower-contact"
    return "side-contact"


def _scene_clause(
    schema: LiteralSchema,
    state: WorldState,
    side: BoundarySide | None,
    direction: LiteralDirection | None,
) -> str:
    if schema is LiteralSchema.CONTAINMENT:
        assert side is not None and direction is not None
        location = "inside" if direction is LiteralDirection.EXIT else "outside"
        quality = _opening_quality(state, side)
        descriptions = {
            "fully-open-perimeter": "the relevant perimeter is fully open",
            "closed-perimeter": "the relevant perimeter is closed and has no opening",
            "disabled-opening": "the perimeter is closed and its opening is disabled",
            "fitting-opening": (
                "the perimeter has an enabled opening aligned with and wide enough for the object"
            ),
            "undersized-opening": (
                "the perimeter has an enabled opening that is too small for the object"
            ),
            "misaligned-opening": (
                "the perimeter has an enabled opening that is not aligned with the object"
            ),
        }
        return (
            f"the object begins {location} the container and {descriptions[quality]} "
            f"on its {side.value} side"
        )
    geometry = _support_geometry(state)
    tether = state.tethers[0] if state.tethers else None
    if tether is None:
        extra = "there is no tether"
    elif tether.load_bearing:
        extra = "a taut load-bearing tether connects the object to an upper anchor"
    else:
        extra = "a visible tether is present but is not load-bearing"
    contact = (
        "a platform is in lower contact with the object"
        if geometry == "lower-contact"
        else "a platform touches the object's side without lower contact"
    )
    return f"{contact} and {extra}"


def _target_type(state: WorldState, target_id: str | None) -> str:
    if target_id is None:
        return "none"
    try:
        return state.entity(target_id).role.value
    except KeyError:
        pass
    if any(item.opening_id == target_id for item in state.openings):
        return "opening"
    if any(item.tether_id == target_id for item in state.tethers):
        return "tether"
    if any(item.attachment_id == target_id for item in state.attachments):
        return "attachment"
    return "unknown"


def action_summary(
    action: Action,
    state: WorldState,
    *,
    side: BoundarySide | None,
) -> str:
    if action.kind is ActionKind.ENTER:
        assert side is not None
        return f"the object moves inward through the {side.value} side"
    if action.kind is ActionKind.EXIT:
        assert side is not None
        return f"the object moves outward through the {side.value} side"
    if action.kind in {ActionKind.NOOP, ActionKind.WAIT}:
        return "the setup is observed without removing or changing anything"
    if action.kind is ActionKind.REMOVE_SUPPORT:
        return (
            "the lower platform is removed"
            if _support_geometry(state) == "lower-contact"
            else "the side-touching platform is removed"
        )
    if action.kind is ActionKind.CUT_OR_BREAK:
        return "the tether is cut"
    if action.kind is ActionKind.DETACH:
        return "the load-bearing tether is detached"
    raise ValueError(f"No literal action summary is registered for {action.kind.value}")


def _mechanism_summary(value: LiteralMechanismKind) -> str:
    return {
        LiteralMechanismKind.FITTING_APERTURE: (
            "passage depends on an aligned opening that fits the object"
        ),
        LiteralMechanismKind.DISABLED_APERTURE: "passage depends on whether the opening is enabled",
        LiteralMechanismKind.UNDERSIZED_APERTURE: (
            "passage depends on whether the opening is large enough"
        ),
        LiteralMechanismKind.MISALIGNED_APERTURE: "passage depends on aperture alignment",
        LiteralMechanismKind.OPEN_PERIMETER: (
            "passage depends on whether the whole perimeter is open"
        ),
        LiteralMechanismKind.CLOSED_PERIMETER: "passage is prevented by a closed perimeter",
        LiteralMechanismKind.LOWER_CONTACT: "elevation depends on lower contact",
        LiteralMechanismKind.SIDE_CONTACT: "side contact alone does not maintain elevation",
        LiteralMechanismKind.LOAD_BEARING_TETHER: (
            "elevation depends on tension from a load-bearing tether"
        ),
        LiteralMechanismKind.NONBEARING_TETHER: (
            "a non-load-bearing tether does not maintain elevation"
        ),
    }[value]


def _task_question(family: LiteralTaskFamily) -> str:
    return {
        LiteralTaskFamily.DIRECT_OUTCOME: "Which direct outcome follows?",
        LiteralTaskFamily.INTERVENTION_CONSEQUENCE: (
            "Which consequence is caused by the intervention?"
        ),
        LiteralTaskFamily.MATCHED_COUNTERFACTUAL: (
            "Which outcome occurs in the actual setup rather than the matched alternative?"
        ),
        LiteralTaskFamily.NOVEL_TEMPLATE: ("What is the object's outcome?"),
        LiteralTaskFamily.NOVEL_CONFIGURATION: ("What happens to the object?"),
        LiteralTaskFamily.PHYSICAL_ANALOGY: ("What happens to the object?"),
    }[family]


def _outcome_clause(outcome: LiteralOutcomeCode) -> str:
    return {
        LiteralOutcomeCode.MOVEMENT_SUCCEEDS: "the object completes the attempted movement",
        LiteralOutcomeCode.MOVEMENT_BLOCKED: "the object remains blocked",
        LiteralOutcomeCode.OBJECT_FALLS: "the object moves downward",
        LiteralOutcomeCode.OBJECT_STAYS: "the object remains elevated",
    }[outcome]


def narrative_facts(
    spec: LiteralScenarioSpec,
    actual_state: WorldState,
    counterfactual_state: WorldState,
    actual_actions: Sequence[Action],
    counterfactual_actions: Sequence[Action],
    *,
    analogy_source: LiteralWitnessRecord | None = None,
) -> LiteralNarrativeFacts:
    if len(actual_actions) != 1 or len(counterfactual_actions) != 1:
        raise ValueError("Literal narrative renderer supports the prospectively allowed horizon")
    target = target_mechanism(spec.scenario_case)
    if spec.task_family is LiteralTaskFamily.PHYSICAL_ANALOGY:
        if analogy_source is None:
            raise ValueError("Physical analogy narrative requires its declared L1 source witness")
        source = analogy_source.target_mechanism
        source_mapping_clause = (
            f"{analogy_source.narrative_facts.actual_scene_clause}; when "
            f"{analogy_source.narrative_facts.actual_action_summary}, "
            f"{_outcome_clause(analogy_source.actual_outcome_code)}"
        )
    else:
        if analogy_source is not None:
            raise ValueError("Only physical analogies may receive a source witness")
        source = target
        source_mapping_clause = None
    return LiteralNarrativeFacts(
        schema_identity=spec.schema_identity,
        transfer_level=spec.transfer_level,
        task_family=spec.task_family,
        scenario_case=spec.scenario_case,
        side=spec.side,
        direction=spec.direction,
        intervention_kind=spec.intervention_kind,
        source_mechanism=source,
        target_mechanism=target,
        actual_scene_clause=_scene_clause(
            spec.schema_identity, actual_state, spec.side, spec.direction
        ),
        counterfactual_scene_clause=_scene_clause(
            spec.schema_identity, counterfactual_state, spec.side, spec.direction
        ),
        actual_action_summary=action_summary(actual_actions[0], actual_state, side=spec.side),
        counterfactual_action_summary=action_summary(
            counterfactual_actions[0], counterfactual_state, side=spec.side
        ),
        source_mapping_clause=source_mapping_clause,
        task_family_question=_task_question(spec.task_family),
        instructions="Choose exactly one literal outcome.",
    )


def render_literal_prompt(template: LiteralTemplate, facts: LiteralNarrativeFacts) -> str:
    """Render a prompt from typed facts only; free causal prose is never accepted."""

    if not isinstance(facts, LiteralNarrativeFacts):
        raise TypeError("Literal prompt templates accept only LiteralNarrativeFacts")
    if (
        template.task_family is not facts.task_family
        or template.transfer_level is not facts.transfer_level
    ):
        raise ValueError("Template and narrative-fact classifications disagree")
    if template.vocabulary_mode == "engineering_fixture":
        condition = {
            ContainmentScenarioCase.FITTING_OPENING: "the route is available",
            ContainmentScenarioCase.CLOSED_BOUNDARY: "the route is unavailable",
            ContainmentScenarioCase.UNDERSIZED_OPENING: "the route is too narrow",
            ContainmentScenarioCase.MISALIGNED_OPENING: "the route is offset",
            ContainmentScenarioCase.FULLY_OPEN_BOUNDARY: "the route is clear",
            SupportScenarioCase.LOWER_SUPPORT_REMOVAL: "the lower base is removed",
            SupportScenarioCase.LOWER_SUPPORT_NOOP: "the lower base is unchanged",
            SupportScenarioCase.SIDE_CONTACT: "contact occurs only at the side",
            SupportScenarioCase.TETHER_CUT: "the upper link is cut",
            SupportScenarioCase.TETHERED_PLATFORM_REMOVAL: "the lower base is removed",
            SupportScenarioCase.NONBEARING_TETHER: "the upper link carries no load",
        }[facts.scenario_case]
        return (
            f"Consider the following physical setup. The object begins at the designated start, "
            f"and {condition}. Apply the stated single step. {facts.task_family_question}"
        )
    if facts.task_family is LiteralTaskFamily.DIRECT_OUTCOME:
        prompt = (
            f"Consider the following physical setup. {facts.actual_scene_clause.capitalize()}. "
            f"Then {facts.actual_action_summary}. {facts.task_family_question}"
        )
    elif facts.task_family is LiteralTaskFamily.INTERVENTION_CONSEQUENCE:
        prompt = (
            f"Consider the following physical setup. {facts.actual_scene_clause.capitalize()}. "
            f"Now {facts.actual_action_summary}. "
            f"{facts.task_family_question}"
        )
    elif facts.task_family is LiteralTaskFamily.MATCHED_COUNTERFACTUAL:
        prompt = (
            "Consider two otherwise matched physical setups. In the actual setup, "
            f"{facts.actual_scene_clause}; {facts.actual_action_summary}. "
            "In the alternative setup, "
            f"{facts.counterfactual_scene_clause}; {facts.counterfactual_action_summary}. "
            f"{facts.task_family_question}"
        )
    elif facts.task_family is LiteralTaskFamily.NOVEL_TEMPLATE:
        prompt = (
            f"A physical setup is described as follows: {facts.actual_scene_clause}. Next, "
            f"{facts.actual_action_summary}. {facts.task_family_question}"
        )
    elif facts.task_family is LiteralTaskFamily.NOVEL_CONFIGURATION:
        prompt = (
            f"Consider the following physical setup. {facts.actual_scene_clause.capitalize()}. "
            f"After {facts.actual_action_summary}, {facts.task_family_question[0].lower()}"
            f"{facts.task_family_question[1:]}"
        )
    else:
        if facts.source_mapping_clause is None:
            raise ValueError("Physical analogy facts lack an operational source mapping")
        prompt = (
            f"In a reference setup, {facts.source_mapping_clause}. Apply the same causal pattern "
            f"to another setup: {facts.actual_scene_clause}; then {facts.actual_action_summary}. "
            f"{facts.task_family_question}"
        )
    canonical = " ".join(prompt.split())
    if canonical != prompt:
        raise ValueError("Typed literal renderer produced non-canonical whitespace")
    return canonical


def _state_topology(state: WorldState) -> dict[str, Any]:
    return {
        "entity_roles": dict(sorted(Counter(item.role.value for item in state.entities).items())),
        "boundaries": tuple(sorted(item.closed for item in state.boundaries)),
        "openings": tuple(
            sorted(
                (item.side.value, item.enabled, item.gate_id is not None) for item in state.openings
            )
        ),
        "attachments": tuple(
            sorted((item.active, item.load_bearing) for item in state.attachments)
        ),
        "tethers": tuple(sorted((item.active, item.load_bearing) for item in state.tethers)),
        "delayed_event_kinds": tuple(sorted(item.kind.value for item in state.delayed_events)),
    }


def _qualitative_geometry(
    schema: LiteralSchema,
    state: WorldState,
    side: BoundarySide | None,
    direction: LiteralDirection | None,
) -> dict[str, Any]:
    if schema is LiteralSchema.CONTAINMENT:
        assert side is not None and direction is not None
        return {
            "schema": schema.value,
            "side": side.value,
            "direction": direction.value,
            "opening_quality": _opening_quality(state, side),
            "distractor_present": any(
                item.role is EntityRole.DISTRACTOR for item in state.entities
            ),
        }
    tether = state.tethers[0] if state.tethers else None
    return {
        "schema": schema.value,
        "support_geometry": _support_geometry(state),
        "tether_present": tether is not None,
        "tether_active": None if tether is None else tether.active,
        "tether_load_bearing": None if tether is None else tether.load_bearing,
        "distractor_present": any(item.role is EntityRole.DISTRACTOR for item in state.entities),
    }


def _action_structure(state: WorldState, actions: Sequence[Action]) -> tuple[dict[str, Any], ...]:
    result: list[dict[str, Any]] = []
    for action in actions:
        axis = "x" if action.delta_x else "y" if action.delta_y else "none"
        delta = action.delta_x or action.delta_y
        result.append(
            {
                "kind": action.kind.value,
                "target_type": _target_type(state, action.target_id),
                "axis": axis,
                "direction": 0 if delta == 0 else 1 if delta > 0 else -1,
                "has_magnitude": action.magnitude is not None,
            }
        )
    return tuple(result)


def _observation_structure(state: WorldState) -> dict[str, Any]:
    observation = primary_observation(state)
    return {
        "entity_kind_counts": dict(
            sorted(Counter(item.kind_code for item in observation.entities).items())
        ),
        "boundary_closed": tuple(sorted(item.closed for item in observation.boundaries)),
        "apertures": tuple(
            sorted((item.side_code, item.enabled) for item in observation.apertures)
        ),
        "edges": tuple(sorted((item.mechanism_code, item.active) for item in observation.edges)),
    }


def structural_signatures(
    spec: LiteralScenarioSpec,
    template: LiteralTemplate,
    actual_state: WorldState,
    counterfactual_state: WorldState,
    actual_actions: Sequence[Action],
    counterfactual_actions: Sequence[Action],
    actual_outcome: LiteralOutcomeCode,
    counterfactual_outcome: LiteralOutcomeCode,
    *,
    analogy_source: LiteralWitnessRecord | None = None,
) -> LiteralStructuralSignatures:
    """Create seed-, ID-, and filesystem-independent prospective signatures."""

    contract = intervention_contract(spec.scenario_case)
    topology_payload = {
        "actual": _state_topology(actual_state),
        "counterfactual": _state_topology(counterfactual_state),
    }
    geometry_payload = {
        "actual": _qualitative_geometry(
            spec.schema_identity, actual_state, spec.side, spec.direction
        ),
        "counterfactual": _qualitative_geometry(
            spec.schema_identity, counterfactual_state, spec.side, spec.direction
        ),
    }
    action_payload = {
        "actual": _action_structure(actual_state, actual_actions),
        "counterfactual": _action_structure(counterfactual_state, counterfactual_actions),
    }
    counterfactual_payload = {
        "kind": contract.intervention_kind.value,
        "occurs_in": contract.occurs_in,
        "initial_paths": contract.allowed_initial_difference_paths,
        "action_paths": contract.allowed_action_difference_paths,
    }
    mechanism_payload = {
        "schema": spec.schema_identity.value,
        "mechanism": target_mechanism(spec.scenario_case).value,
        "actual_action": action_payload["actual"],
        "counterfactual_action": action_payload["counterfactual"],
        "actual_outcome": actual_outcome.value,
        "counterfactual_outcome": counterfactual_outcome.value,
    }
    observation_payload = {
        "actual": _observation_structure(actual_state),
        "counterfactual": _observation_structure(counterfactual_state),
    }
    world_hash = structural_signature_hash("world-topology", topology_payload)
    geometry_hash = structural_signature_hash("qualitative-geometry", geometry_payload)
    action_hash = structural_signature_hash("action-plan", action_payload)
    counterfactual_hash = structural_signature_hash(
        "counterfactual-intervention", counterfactual_payload
    )
    target_mechanism_hash = structural_signature_hash("mechanism-identity", mechanism_payload)
    if spec.task_family is LiteralTaskFamily.PHYSICAL_ANALOGY:
        if analogy_source is None:
            raise ValueError("Physical analogy signatures require the declared L1 source witness")
        source_mechanism_hash = analogy_source.structural_signatures.target_mechanism_sha256
    else:
        if analogy_source is not None:
            raise ValueError("Only physical analogies may receive a source witness")
        source_mechanism_hash = target_mechanism_hash
    template_identity = structural_signature_hash(
        "prompt-template",
        {"template_id": template.template_id, "template_sha256": template_hash(template)},
    )
    observation_hash = structural_signature_hash("observation-structure", observation_payload)
    configuration_hash = structural_signature_hash(
        "configuration",
        {
            "world": world_hash,
            "geometry": geometry_hash,
            "action": action_hash,
            "counterfactual": counterfactual_hash,
            "target_mechanism": target_mechanism_hash,
            "observation": observation_hash,
        },
    )
    causal_scenario_hash = structural_signature_hash(
        "causal-scenario", {"configuration": configuration_hash}
    )
    episode_hashes = tuple(
        sorted(
            (
                structural_signature_hash(
                    "structural-stratum-episode",
                    {
                        "topology": topology_payload[role],
                        "geometry": geometry_payload[role],
                        "action": action_payload[role],
                        "observation": observation_payload[role],
                        "outcome": outcome.value,
                    },
                )
                for role, outcome in (
                    ("actual", actual_outcome),
                    ("counterfactual", counterfactual_outcome),
                )
            )
        )
    )
    structural_stratum_hash = structural_signature_hash(
        "structural-stratum",
        {
            "schema": spec.schema_identity.value,
            "causal_factor": contract.causal_factor.value,
            "episodes": episode_hashes,
        },
    )
    witness_configuration_hash = structural_signature_hash(
        "witness-configuration",
        {
            "causal_scenario": causal_scenario_hash,
            "source_mechanism": source_mechanism_hash,
            "template": template_identity,
        },
    )
    return LiteralStructuralSignatures(
        world_topology_sha256=world_hash,
        qualitative_geometry_sha256=geometry_hash,
        action_plan_sha256=action_hash,
        counterfactual_intervention_sha256=counterfactual_hash,
        source_mechanism_sha256=source_mechanism_hash,
        target_mechanism_sha256=target_mechanism_hash,
        prompt_template_sha256=template_identity,
        observation_structure_sha256=observation_hash,
        configuration_sha256=configuration_hash,
        causal_scenario_sha256=causal_scenario_hash,
        structural_stratum_sha256=structural_stratum_hash,
        witness_configuration_sha256=witness_configuration_hash,
    )
