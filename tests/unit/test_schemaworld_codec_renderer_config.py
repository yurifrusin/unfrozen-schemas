"""M1.4 codec, renderer, and strict configuration contracts."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

import unfrozen_schemas.core_config as core_config_module
from unfrozen_schemas.codecs.opaque_tokens import OpaqueDiscreteCodec
from unfrozen_schemas.config import ConfigLoadError
from unfrozen_schemas.core_config import load_core_config
from unfrozen_schemas.envs.schema_world.renderer import render_raw_pixels, save_png
from unfrozen_schemas.envs.schema_world.serialization import (
    FORBIDDEN_RELATION_LABELS,
    canonical_record_bytes,
    primary_observation,
)
from unfrozen_schemas.envs.schema_world.templates import TemplateFamily, generate_matched_pair


def test_opaque_codec_is_reversible_versioned_and_semantically_meaningless() -> None:
    plan = generate_matched_pair(
        TemplateFamily.CONTAINMENT_GATE, seed=101, noise_seed=100_101
    ).episodes[0]
    observation = primary_observation(plan.initial_state)
    codec = OpaqueDiscreteCodec()
    encoded = codec.encode(observation, record_kind="observation")
    assert encoded.codec_version == "opaque-byte-v1"
    assert all(symbol.startswith("u") and len(symbol) == 5 for symbol in encoded.symbols)
    assert not any(
        label in " ".join(encoded.symbols).upper() for label in FORBIDDEN_RELATION_LABELS
    )
    assert codec.decode_bytes(encoded) == canonical_record_bytes(observation)
    assert codec.decode(encoded) == observation.model_dump(mode="json")


def test_codec_is_identical_for_equal_records_across_matched_conditions() -> None:
    pair = generate_matched_pair(TemplateFamily.SUPPORT_PLATFORM, seed=5, noise_seed=6)
    codec = OpaqueDiscreteCodec()
    left = codec.encode(
        primary_observation(pair.episodes[0].initial_state), record_kind="observation"
    )
    right = codec.encode(
        primary_observation(pair.episodes[1].initial_state), record_kind="observation"
    )
    assert left == right


def test_renderer_is_headless_deterministic_and_hashes_raw_pixels(tmp_path: Path) -> None:
    state = (
        generate_matched_pair(TemplateFamily.SUPPORT_TENSION, seed=9, noise_seed=10)
        .episodes[0]
        .initial_state
    )
    first_pixels, first_hash = render_raw_pixels(state, width=64, height=64)
    second_pixels, second_hash = render_raw_pixels(state, width=64, height=64)
    assert first_pixels == second_pixels
    assert first_hash == second_hash
    assert len(first_pixels) == 64 * 64 * 3
    output = tmp_path / "inspect.png"
    save_png(output, first_pixels, width=64, height=64)
    assert output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert first_hash != __import__("hashlib").sha256(output.read_bytes()).hexdigest()


def test_core_config_is_strict_relative_cpu_offline_and_ordered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    loaded = load_core_config(
        Path("configs/experiment/milestone1_core_smoke.yaml"),
        output_root_override=tmp_path,
    )
    assert loaded.output_root == tmp_path.resolve()
    assert loaded.resolved.run.engineering_only is True
    assert loaded.resolved.run.device == "cpu"
    assert loaded.resolved.generator.seeds == (101, 202)

    source = Path("configs/experiment/milestone1_core_smoke.yaml")
    raw = yaml.safe_load(source.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    raw["environment"]["transition_stage_order"][0] = "relation_derivation"
    monkeypatch.setattr(core_config_module, "_load_yaml", lambda _path: raw)
    with pytest.raises(ConfigLoadError, match="transition_stage_order"):
        load_core_config(source, output_root_override=tmp_path)
