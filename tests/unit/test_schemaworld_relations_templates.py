"""M1.3 verifier relations and strict matched-pair audits."""

from __future__ import annotations

import pytest

from unfrozen_schemas.envs.schema_world.dynamics import transition
from unfrozen_schemas.envs.schema_world.relations import RelationKind, derive_relations
from unfrozen_schemas.envs.schema_world.serialization import (
    FORBIDDEN_RELATION_LABELS,
    canonical_record_bytes,
    primary_observation,
)
from unfrozen_schemas.envs.schema_world.templates import (
    MatchedPair,
    PairParityError,
    TemplateFamily,
    audit_matched_pair,
    generate_matched_pair,
)


@pytest.mark.parametrize("template_id", list(TemplateFamily))
def test_matched_pair_has_stable_identity_hashes_and_exact_declared_difference(
    template_id: TemplateFamily,
) -> None:
    first = generate_matched_pair(template_id, seed=101, noise_seed=201)
    second = generate_matched_pair(template_id, seed=101, noise_seed=201)
    assert first == second
    assert first.pair_id.startswith("pair-")
    assert len({episode.episode_id for episode in first.episodes}) == 2
    assert audit_matched_pair(first) == tuple(sorted(first.declared_difference_paths))
    assert all(episode.initial_state_hash for episode in first.episodes)
    assert all(episode.initial_observation_hash for episode in first.episodes)
    assert all(episode.action_sequence_hash for episode in first.episodes)


def test_undeclared_pair_difference_is_rejected() -> None:
    pair = generate_matched_pair(TemplateFamily.CONTAINMENT_GATE, seed=7, noise_seed=8)
    right = pair.episodes[1]
    changed_entity = right.initial_state.entities[0].model_copy(update={"x": 650})
    changed_state = right.initial_state.model_copy(
        update={"entities": (changed_entity, *right.initial_state.entities[1:])}
    )
    changed_right = right.model_copy(update={"initial_state": changed_state})
    changed_pair = MatchedPair(
        pair_id=pair.pair_id,
        target_factor=pair.target_factor,
        declared_difference_paths=pair.declared_difference_paths,
        episodes=(pair.episodes[0], changed_right),
    )
    with pytest.raises(PairParityError, match="outside its declaration"):
        audit_matched_pair(changed_pair)


def test_containment_relation_truth_table_and_blockage_are_derived() -> None:
    pair = generate_matched_pair(TemplateFamily.CONTAINMENT_GATE, seed=9, noise_seed=10)
    closed, opened = pair.episodes
    before_relations = derive_relations(closed.initial_state)
    assert any(record.relation is RelationKind.INTERIOR for record in before_relations)

    blocked = transition(closed.initial_state, closed.actions[0])
    blocked_relations = derive_relations(blocked.state, blocked.trace)
    assert any(record.relation is RelationKind.BLOCKAGE for record in blocked_relations)
    assert any(record.relation is RelationKind.INTERIOR for record in blocked_relations)

    passed = transition(opened.initial_state, opened.actions[0])
    passed_relations = derive_relations(passed.state, passed.trace)
    assert any(record.relation is RelationKind.EXTERIOR for record in passed_relations)
    assert any(record.relation is RelationKind.MOVEMENT for record in passed_relations)
    assert not any(record.relation is RelationKind.BLOCKAGE for record in passed_relations)


def test_functional_support_is_not_contact_and_tension_relations_are_mechanical() -> None:
    pair = generate_matched_pair(TemplateFamily.SUPPORT_TENSION, seed=12, noise_seed=13)
    remove_visible, remove_true = pair.episodes
    held = transition(remove_visible.initial_state, remove_visible.actions[0])
    held_relations = derive_relations(held.state, held.trace)
    assert any(record.relation is RelationKind.CONNECTION for record in held_relations)
    assert any(record.relation is RelationKind.FUNCTIONAL_SUPPORT for record in held_relations)
    assert not any(record.relation is RelationKind.FALLING for record in held_relations)

    falling = transition(remove_true.initial_state, remove_true.actions[0])
    falling_relations = derive_relations(falling.state, falling.trace)
    assert any(record.relation is RelationKind.FALLING for record in falling_relations)
    assert not any(
        record.relation is RelationKind.FUNCTIONAL_SUPPORT for record in falling_relations
    )


def test_verifier_relations_never_enter_primary_observations() -> None:
    pair = generate_matched_pair(TemplateFamily.CONTAINMENT_GATE, seed=21, noise_seed=22)
    observation = primary_observation(pair.episodes[0].initial_state)
    payload = canonical_record_bytes(observation).decode("utf-8").upper()
    assert not any(label in payload for label in FORBIDDEN_RELATION_LABELS)
