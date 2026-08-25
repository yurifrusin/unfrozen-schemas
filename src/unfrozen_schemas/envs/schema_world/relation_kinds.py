"""Privileged relation vocabulary shared without importing dynamics or serialization."""

from __future__ import annotations

from enum import StrEnum
from typing import Final


class RelationKind(StrEnum):
    """Verifier-only relation names that must never enter primary sensor streams."""

    INTERIOR = "INTERIOR"
    EXTERIOR = "EXTERIOR"
    FUNCTIONAL_SUPPORT = "FUNCTIONAL_SUPPORT"
    BLOCKAGE = "BLOCKAGE"
    CONNECTION = "CONNECTION"
    MOVEMENT = "MOVEMENT"
    FALLING = "FALLING"


RELATION_SYNONYMS: Final[frozenset[str]] = frozenset(
    {
        "INSIDE",
        "OUTSIDE",
        "SUPPORTED",
        "UNSUPPORTED",
        "BLOCKED",
        "CONNECTED",
        "CONTAINMENT",
        "SUPPORT",
    }
)
FORBIDDEN_RELATION_LABELS: Final[frozenset[str]] = (
    frozenset({relation.value for relation in RelationKind}) | RELATION_SYNONYMS
)
