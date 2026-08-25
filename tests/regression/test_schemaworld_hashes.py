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
            "09bd2fb9ee22cc6fe21af537518e9f57c59022d64f3ac80e4b476b89314949a0",
        ),
        (
            TemplateFamily.SUPPORT_PLATFORM,
            "d8191a727e0f0c24ed11780a506c76f60157c79aed9f265825c5735ae2031a5f",
        ),
        (
            TemplateFamily.SUPPORT_TENSION,
            "1dbcc1d9368e4baf68349ff6f0edeb832c52406c2ecdc6d4a3eed77bf193ef37",
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
