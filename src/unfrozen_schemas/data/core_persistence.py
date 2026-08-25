"""Explicit PyArrow/Parquet schemas for canonical SchemaWorld episode and step records."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Final, cast

import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]

EPISODE_SCHEMA_VERSION: Final = "1"
STEP_SCHEMA_VERSION: Final = "1"

EPISODE_SCHEMA: Final = pa.schema(
    [
        pa.field("episode_id", pa.string(), nullable=False),
        pa.field("parent_pair_id", pa.string(), nullable=False),
        pa.field("condition_index", pa.int8(), nullable=False),
        pa.field("template_id", pa.string(), nullable=False),
        pa.field("schema_name", pa.string(), nullable=False),
        pa.field("environment_version", pa.string(), nullable=False),
        pa.field("seed", pa.uint32(), nullable=False),
        pa.field("noise_seed", pa.uint32(), nullable=False),
        pa.field("audited_target_factor", pa.string(), nullable=False),
        pa.field(
            "declared_difference_paths",
            pa.list_(pa.field("element", pa.string())),
            nullable=False,
        ),
        pa.field("initial_state_hash", pa.string(), nullable=False),
        pa.field("initial_observation_hash", pa.string(), nullable=False),
        pa.field("state_hash", pa.string(), nullable=False),
        pa.field("observation_hash", pa.string(), nullable=False),
        pa.field("trajectory_hash", pa.string(), nullable=False),
        pa.field("action_sequence_hash", pa.string(), nullable=False),
        pa.field("render_hash", pa.string(), nullable=False),
        pa.field("codec_version", pa.string(), nullable=False),
        pa.field("renderer_version", pa.string(), nullable=False),
        pa.field("plan_json", pa.binary(), nullable=False),
        pa.field("final_state_json", pa.binary(), nullable=False),
    ],
    metadata={b"unfrozen_schema": b"schemaworld_episodes", b"schema_version": b"1"},
)

STEP_SCHEMA: Final = pa.schema(
    [
        pa.field("episode_id", pa.string(), nullable=False),
        pa.field("step_index", pa.int32(), nullable=False),
        pa.field("state_before_json", pa.binary(), nullable=False),
        pa.field("observation_before_json", pa.binary(), nullable=False),
        pa.field("opaque_observation_before_json", pa.binary(), nullable=False),
        pa.field("action_json", pa.binary(), nullable=False),
        pa.field("opaque_action_json", pa.binary(), nullable=False),
        pa.field("state_after_json", pa.binary(), nullable=False),
        pa.field("observation_after_json", pa.binary(), nullable=False),
        pa.field("opaque_observation_after_json", pa.binary(), nullable=False),
        pa.field("trace_json", pa.binary(), nullable=False),
        pa.field("relations_after_json", pa.binary(), nullable=False),
        pa.field("state_before_hash", pa.string(), nullable=False),
        pa.field("observation_before_hash", pa.string(), nullable=False),
        pa.field("state_after_hash", pa.string(), nullable=False),
        pa.field("observation_after_hash", pa.string(), nullable=False),
        pa.field("transition_hash", pa.string(), nullable=False),
    ],
    metadata={b"unfrozen_schema": b"schemaworld_steps", b"schema_version": b"1"},
)


def _write(path: Path, rows: list[dict[str, Any]], schema: pa.Schema) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(rows, schema=schema)
    pq.write_table(
        table,
        path,
        compression="NONE",
        use_dictionary=False,
        write_statistics=False,
        data_page_version="1.0",
        version="2.6",
        store_schema=True,
    )


def write_episode_table(path: Path, rows: list[dict[str, Any]]) -> None:
    _write(path, rows, EPISODE_SCHEMA)


def write_step_table(path: Path, rows: list[dict[str, Any]]) -> None:
    _write(path, rows, STEP_SCHEMA)


def _read(path: Path, schema: pa.Schema) -> list[dict[str, Any]]:
    if not path.is_file():
        raise ValueError(f"Required Parquet file does not exist: {path}")
    table = pq.read_table(path)
    if not table.schema.equals(schema, check_metadata=True):
        raise ValueError(f"Parquet schema mismatch for {path.name}: {table.schema}")
    return cast(list[dict[str, Any]], table.to_pylist())


def read_episode_table(path: Path) -> list[dict[str, Any]]:
    return _read(path, EPISODE_SCHEMA)


def read_step_table(path: Path) -> list[dict[str, Any]]:
    return _read(path, STEP_SCHEMA)
