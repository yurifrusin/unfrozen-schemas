"""End-to-end offline M1 generation, validation, replay, and inspection."""

from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest
from typer.testing import CliRunner

from unfrozen_schemas.cli import app
from unfrozen_schemas.data.core_models import CoreRunManifest
from unfrozen_schemas.data.core_runner import CORE_MANIFEST_FILENAME, validate_core_manifest


def _deny_network(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("SchemaWorld Core attempted a network call")


def test_core_cli_generation_replay_and_render_are_offline_and_complete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(socket, "create_connection", _deny_network)
    monkeypatch.setattr(socket.socket, "connect", _deny_network)
    runner = CliRunner()
    generated = runner.invoke(
        app,
        [
            "generate-core",
            "--config",
            "configs/experiment/milestone1_core_smoke.yaml",
            "--output-root",
            str(tmp_path),
        ],
    )
    assert generated.exit_code == 0, generated.output
    manifests = list(tmp_path.glob(f"*/{CORE_MANIFEST_FILENAME}"))
    assert len(manifests) == 1
    source_path = manifests[0]
    source = validate_core_manifest(source_path)
    assert source.status == "COMPLETED"
    assert {item.schema_name for item in source.episodes} == {"CONTAINMENT", "SUPPORT"}
    assert {item.seed for item in source.episodes} == {101, 202}

    validated = runner.invoke(app, ["validate-core", "--manifest", str(source_path)])
    assert validated.exit_code == 0, validated.output
    assert "12 episodes; 6 pairs" in validated.output

    replayed = runner.invoke(app, ["replay-core", "--manifest", str(source_path)])
    assert replayed.exit_code == 0, replayed.output
    manifests = sorted(tmp_path.glob(f"*/{CORE_MANIFEST_FILENAME}"))
    assert len(manifests) == 2
    replay_path = next(path for path in manifests if path != source_path)
    replay = validate_core_manifest(replay_path)
    assert replay.run_kind == "replay_core"
    assert replay.episodes == source.episodes
    assert replay.resource_budget.environment_steps == source.resource_budget.environment_steps
    assert replay.source_manifest_sha256 is not None

    episode_id = source.episodes[0].episode_id
    png = tmp_path / "representative.png"
    inspected = runner.invoke(
        app,
        [
            "inspect-episode",
            "--episode-id",
            episode_id,
            "--manifest",
            str(source_path),
            "--render",
            "--output",
            str(png),
        ],
    )
    assert inspected.exit_code == 0, inspected.output
    summary = json.loads(inspected.output)
    assert summary["episode_id"] == episode_id
    assert summary["rendered"] is True
    assert summary["render_hash"] == source.episodes[0].render_hash
    assert png.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


def test_core_manifest_json_round_trip_is_strict(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "generate-core",
            "--config",
            "configs/experiment/milestone1_core_smoke.yaml",
            "--output-root",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    manifest_path = next(tmp_path.glob(f"*/{CORE_MANIFEST_FILENAME}"))
    manifest = CoreRunManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    assert CoreRunManifest.model_validate_json(manifest.model_dump_json()) == manifest
