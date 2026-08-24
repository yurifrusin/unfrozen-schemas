"""Configuration validation and repository-relative resolution tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from unfrozen_schemas.config import ConfigLoadError, SmokeConfig, load_smoke_config


def _write_fake_repository(tmp_path: Path, *, expected_hash: str | None = None) -> Path:
    repository = tmp_path / "repository"
    (repository / ".git").mkdir(parents=True)
    (repository / "configs/experiment").mkdir(parents=True)
    (repository / "configs/model").mkdir(parents=True)
    (repository / "tests/fixtures").mkdir(parents=True)
    (repository / "CODEX_SPEC_Unfrozen_Schemas_v4.md").write_text("test spec\n", encoding="utf-8")

    fixture_data: dict[str, Any] = {
        "schema_version": "1",
        "model_type": "tiny_linear",
        "seed": 7,
        "input_size": 1,
        "output_size": 1,
        "weights": [[0.5]],
        "bias": [0.0],
    }
    fixture_bytes = (json.dumps(fixture_data, sort_keys=True) + "\n").encode()
    fixture_path = repository / "tests/fixtures/tiny.json"
    fixture_path.write_bytes(fixture_bytes)
    fixture_hash = hashlib.sha256(fixture_bytes).hexdigest()

    model_data = {
        "schema_version": "1",
        "model_type": "tiny_linear_fixture",
        "fixture_path": "tests/fixtures/tiny.json",
        "expected_sha256": fixture_hash if expected_hash is None else expected_hash,
    }
    (repository / "configs/model/tiny.yaml").write_text(
        yaml.safe_dump(model_data, sort_keys=False), encoding="utf-8"
    )
    experiment_data = {
        "schema_version": "1",
        "run": {
            "name": "smoke-test",
            "output_root": "runs",
            "seed": 11,
            "device": "cpu",
            "offline": True,
            "requires_secret": False,
            "engineering_only": True,
        },
        "model_config": "configs/model/tiny.yaml",
        "logging": {"level": "INFO"},
    }
    experiment_path = repository / "configs/experiment/smoke.yaml"
    experiment_path.write_text(yaml.safe_dump(experiment_data, sort_keys=False), encoding="utf-8")
    return experiment_path


def test_valid_configuration_resolves_repository_paths(tmp_path: Path) -> None:
    path = _write_fake_repository(tmp_path)

    resolved = load_smoke_config(path)

    assert resolved.run.output_root == (path.parents[2] / "runs").resolve()
    assert resolved.model.fixture_path.is_absolute()
    assert resolved.run.device == "cpu"
    assert resolved.run.offline is True
    assert resolved.run.engineering_only is True


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("device", "cuda"),
        ("offline", False),
        ("requires_secret", True),
        ("engineering_only", False),
        ("seed", -1),
    ],
)
def test_smoke_configuration_rejects_unsupported_execution(field: str, value: object) -> None:
    run: dict[str, object] = {
        "name": "smoke-test",
        "output_root": "runs",
        "seed": 1,
        "device": "cpu",
        "offline": True,
        "requires_secret": False,
        "engineering_only": True,
    }
    run[field] = value
    data: dict[str, object] = {
        "schema_version": "1",
        "run": run,
        "model_config": "configs/model/tiny.yaml",
        "logging": {"level": "INFO"},
    }

    with pytest.raises(ValidationError):
        SmokeConfig.model_validate(data)


def test_configuration_rejects_unknown_fields() -> None:
    data: dict[str, object] = {
        "schema_version": "1",
        "run": {
            "name": "smoke-test",
            "output_root": "runs",
            "seed": 1,
            "device": "cpu",
            "offline": True,
            "requires_secret": False,
            "engineering_only": True,
            "surprise": "not allowed",
        },
        "model_config": "configs/model/tiny.yaml",
    }

    with pytest.raises(ValidationError):
        SmokeConfig.model_validate(data)


def test_configuration_rejects_fixture_hash_mismatch(tmp_path: Path) -> None:
    path = _write_fake_repository(tmp_path, expected_hash="0" * 64)

    with pytest.raises(ConfigLoadError, match="hash mismatch"):
        load_smoke_config(path)


def test_configuration_allows_isolated_output_and_seed_overrides(tmp_path: Path) -> None:
    path = _write_fake_repository(tmp_path)
    isolated_output = tmp_path / "isolated-runs"

    resolved = load_smoke_config(path, output_root_override=isolated_output, seed_override=99)

    assert resolved.run.output_root == isolated_output.resolve()
    assert resolved.run.seed == 99
