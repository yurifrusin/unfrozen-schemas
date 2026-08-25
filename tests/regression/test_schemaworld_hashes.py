"""Cross-platform M1 canonical logical and raw-pixel regression identities."""

from __future__ import annotations

import pytest

from unfrozen_schemas.codecs.opaque_tokens import OpaqueDiscreteCodec
from unfrozen_schemas.envs.schema_world.dynamics import transition
from unfrozen_schemas.envs.schema_world.renderer import render_raw_pixels
from unfrozen_schemas.envs.schema_world.serialization import canonical_hash, primary_observation
from unfrozen_schemas.envs.schema_world.templates import TemplateFamily, generate_matched_pair


@pytest.mark.parametrize(
    ("template_id", "expected_hash"),
    [
        (
            TemplateFamily.CONTAINMENT_GATE,
            "a3e594eb812fd4da4129f61802fb0a52f2d963341a9b73657df38c00741474d5",
        ),
        (
            TemplateFamily.SUPPORT_PLATFORM,
            "945c715a4e6dace0999de60ec0c4ce0f72f9cf725f7426cdd5678b8310cf22c0",
        ),
        (
            TemplateFamily.SUPPORT_TENSION,
            "279939eacddc980dc5d713d05ffe0c667e886ebd3680fc6b923e657503517eb6",
        ),
    ],
)
def test_matched_pair_regression_hash(template_id: TemplateFamily, expected_hash: str) -> None:
    pair = generate_matched_pair(template_id, seed=101, noise_seed=100_101)
    assert canonical_hash(pair) == expected_hash


def test_opaque_encoding_regression_hash() -> None:
    pair = generate_matched_pair(TemplateFamily.CONTAINMENT_GATE, seed=101, noise_seed=100_101)
    encoded = OpaqueDiscreteCodec().encode(
        primary_observation(pair.episodes[0].initial_state), record_kind="observation"
    )
    assert canonical_hash(encoded) == (
        "692787a3aeb85692cff5a71317cc6133ba81017cc2e09eef7405d6ae755f1c63"
    )


def test_raw_pixel_render_regression_hash() -> None:
    plan = generate_matched_pair(
        TemplateFamily.SUPPORT_TENSION, seed=101, noise_seed=100_101
    ).episodes[1]
    final_state = transition(plan.initial_state, plan.actions[0]).state
    _, render_hash = render_raw_pixels(final_state, width=128, height=128)
    assert render_hash == "73865a3936270878554b10b0b2549fa262819f711b11d4ab88c21c79f78a8448"
