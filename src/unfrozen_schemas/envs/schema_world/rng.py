"""Explicit cross-platform deterministic generator for SchemaWorld Core."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

GENERATOR_ALGORITHM: Final = "splitmix64"
GENERATOR_VERSION: Final = "1"
_MASK_64: Final = (1 << 64) - 1
_GAMMA: Final = 0x9E3779B97F4A7C15


@dataclass(slots=True)
class DeterministicGenerator:
    """A tiny pinned SplitMix64 implementation that never uses global random state."""

    state: int

    def __post_init__(self) -> None:
        if not 0 <= self.state <= _MASK_64:
            raise ValueError("Generator seed must fit an unsigned 64-bit integer")

    @property
    def identity(self) -> str:
        return f"{GENERATOR_ALGORITHM}-v{GENERATOR_VERSION}"

    def next_u64(self) -> int:
        self.state = (self.state + _GAMMA) & _MASK_64
        value = self.state
        value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & _MASK_64
        value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & _MASK_64
        return (value ^ (value >> 31)) & _MASK_64

    def randbelow(self, upper_bound: int) -> int:
        """Return an unbiased integer in ``range(upper_bound)`` using rejection sampling."""

        if upper_bound <= 0 or upper_bound > 1 << 64:
            raise ValueError("upper_bound must be between 1 and 2**64")
        limit = (1 << 64) - ((1 << 64) % upper_bound)
        while True:
            candidate = self.next_u64()
            if candidate < limit:
                return candidate % upper_bound

    def randint(self, lower: int, upper: int) -> int:
        if upper < lower:
            raise ValueError("upper must be greater than or equal to lower")
        return lower + self.randbelow(upper - lower + 1)
