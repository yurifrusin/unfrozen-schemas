"""Reversible schema-neutral discrete codec for canonical logical records."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Final, Literal

from pydantic import Field, model_validator

from unfrozen_schemas.config import FrozenModel
from unfrozen_schemas.envs.schema_world.rng import DeterministicGenerator
from unfrozen_schemas.envs.schema_world.serialization import (
    FORBIDDEN_RELATION_LABELS,
    canonical_record_bytes,
)

CODEC_VERSION: Final = "opaque-byte-v1"
_SYMBOL_PATTERN: Final = re.compile(r"^u[0-9]{4}$")
_PERMUTATION_SEED: Final = 0x554E46524F5A454E


def _symbol_table() -> tuple[str, ...]:
    """Map byte values to a pinned deterministic permutation of meaningless IDs."""

    symbols = [f"u{index:04d}" for index in range(256)]
    rng = DeterministicGenerator(_PERMUTATION_SEED)
    for index in range(len(symbols) - 1, 0, -1):
        swap = rng.randbelow(index + 1)
        symbols[index], symbols[swap] = symbols[swap], symbols[index]
    return tuple(symbols)


SYMBOL_TABLE: Final[tuple[str, ...]] = _symbol_table()
DECODE_TABLE: Final[dict[str, int]] = {
    symbol: byte_value for byte_value, symbol in enumerate(SYMBOL_TABLE)
}


class EncodedRecord(FrozenModel):
    schema_version: Literal["1"] = "1"
    codec_version: Literal["opaque-byte-v1"] = CODEC_VERSION
    record_kind: Literal["observation", "action"]
    symbols: tuple[str, ...]
    logical_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_symbols(self) -> EncodedRecord:
        unknown = [symbol for symbol in self.symbols if symbol not in DECODE_TABLE]
        if unknown:
            raise ValueError(f"Unknown opaque symbols: {unknown[:3]}")
        return self


class OpaqueDiscreteCodec:
    """Byte-exact codec with a versioned, non-lexical 256-symbol table."""

    version: Literal["opaque-byte-v1"] = CODEC_VERSION

    @property
    def symbol_table(self) -> tuple[str, ...]:
        return SYMBOL_TABLE

    def encode(self, value: Any, *, record_kind: Literal["observation", "action"]) -> EncodedRecord:
        logical = canonical_record_bytes(value)
        record = EncodedRecord(
            record_kind=record_kind,
            symbols=tuple(SYMBOL_TABLE[byte] for byte in logical),
            logical_sha256=hashlib.sha256(logical).hexdigest(),
        )
        self.assert_semantically_opaque(record)
        return record

    def decode_bytes(self, record: EncodedRecord) -> bytes:
        decoded = bytes(DECODE_TABLE[symbol] for symbol in record.symbols)
        observed = hashlib.sha256(decoded).hexdigest()
        if observed != record.logical_sha256:
            raise ValueError(
                f"Opaque decode hash mismatch: expected {record.logical_sha256}, "
                f"observed {observed}"
            )
        return decoded

    def decode(self, record: EncodedRecord) -> dict[str, Any] | list[Any]:
        value: Any = json.loads(self.decode_bytes(record))
        if not isinstance(value, (dict, list)):
            raise ValueError("Opaque records must decode to a declared mapping or sequence")
        return value

    def assert_semantically_opaque(self, record: EncodedRecord) -> None:
        if any(not _SYMBOL_PATTERN.fullmatch(symbol) for symbol in record.symbols):
            raise ValueError("Opaque symbols must match the stable uNNNN identifier contract")
        stream = " ".join(record.symbols).upper()
        leaked = sorted(label for label in FORBIDDEN_RELATION_LABELS if label in stream)
        if leaked:
            raise ValueError(f"Opaque symbol stream leaked relation wording: {leaked}")
