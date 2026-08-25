"""CPU-only deterministic inspection rendering with raw-pixel identity."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Final

from PIL import Image

from unfrozen_schemas.envs.schema_world.state import BoundarySide, EntityRole, WorldState

RENDERER_VERSION: Final = "schemaworld-raster-v1"
PIXEL_MODE: Final = "RGB"
BACKGROUND: Final = (245, 247, 250)
COLORS: Final[dict[EntityRole, tuple[int, int, int]]] = {
    EntityRole.AGENT: (76, 110, 245),
    EntityRole.OBJECT: (236, 94, 72),
    EntityRole.CONTAINER: (78, 86, 102),
    EntityRole.GATE: (237, 178, 45),
    EntityRole.SUPPORT: (64, 154, 103),
    EntityRole.ANCHOR: (123, 87, 178),
    EntityRole.DISTRACTOR: (150, 156, 168),
}


def _pixel_hash(pixels: bytes, width: int, height: int) -> str:
    header = f"{RENDERER_VERSION}\0{PIXEL_MODE}\0{width}\0{height}\0".encode()
    return hashlib.sha256(header + pixels).hexdigest()


def _fill(
    pixels: bytearray,
    width: int,
    height: int,
    left: int,
    top: int,
    right: int,
    bottom: int,
    colour: tuple[int, int, int],
) -> None:
    left = max(0, min(width, left))
    right = max(0, min(width, right))
    top = max(0, min(height, top))
    bottom = max(0, min(height, bottom))
    for row in range(top, bottom):
        for column in range(left, right):
            offset = 3 * (row * width + column)
            pixels[offset : offset + 3] = bytes(colour)


def _rect(
    state: WorldState, x: int, y: int, w: int, h: int, width: int, height: int
) -> tuple[int, int, int, int]:
    left = x * width // state.coordinate_max
    right = (x + w) * width // state.coordinate_max
    top = height - (y + h) * height // state.coordinate_max
    bottom = height - y * height // state.coordinate_max
    return left, top, max(left + 1, right), max(top + 1, bottom)


def render_raw_pixels(
    state: WorldState, *, width: int = 128, height: int = 128
) -> tuple[bytes, str]:
    """Render exact RGB bytes without fonts, display servers, timestamps, or metadata."""

    if width <= 0 or height <= 0:
        raise ValueError("Renderer dimensions must be positive")
    pixels = bytearray(bytes(BACKGROUND) * (width * height))
    boundaries = {boundary.container_id: boundary for boundary in state.boundaries}
    for entity in state.entities:
        if not entity.active:
            continue
        left, top, right, bottom = _rect(
            state, entity.x, entity.y, entity.width, entity.height, width, height
        )
        colour = COLORS[entity.role]
        boundary = boundaries.get(entity.entity_id)
        if entity.role is EntityRole.CONTAINER and boundary is not None:
            thickness_x = max(1, boundary.thickness * width // state.coordinate_max)
            thickness_y = max(1, boundary.thickness * height // state.coordinate_max)
            _fill(pixels, width, height, left, top, right, top + thickness_y, colour)
            _fill(pixels, width, height, left, bottom - thickness_y, right, bottom, colour)
            _fill(pixels, width, height, left, top, left + thickness_x, bottom, colour)
            _fill(pixels, width, height, right - thickness_x, top, right, bottom, colour)
        else:
            _fill(pixels, width, height, left, top, right, bottom, colour)

    for opening in state.openings:
        if not opening.enabled:
            continue
        boundary = next(
            item for item in state.boundaries if item.boundary_id == opening.boundary_id
        )
        container = state.entity(boundary.container_id)
        thickness = boundary.thickness
        if opening.side in {BoundarySide.LEFT, BoundarySide.RIGHT}:
            x = (
                container.x
                if opening.side is BoundarySide.LEFT
                else container.x + container.width - thickness
            )
            rect = _rect(
                state,
                x,
                opening.span_start,
                thickness,
                opening.span_end - opening.span_start,
                width,
                height,
            )
        else:
            y = (
                container.y
                if opening.side is BoundarySide.BOTTOM
                else container.y + container.height - thickness
            )
            rect = _rect(
                state,
                opening.span_start,
                y,
                opening.span_end - opening.span_start,
                thickness,
                width,
                height,
            )
        _fill(pixels, width, height, *rect, BACKGROUND)

    raw = bytes(pixels)
    return raw, _pixel_hash(raw, width, height)


def save_png(path: Path, pixels: bytes, *, width: int, height: int) -> None:
    """Save a human inspection PNG; PNG container bytes are not the scientific render identity."""

    expected_size = width * height * 3
    if len(pixels) != expected_size:
        raise ValueError(f"Expected {expected_size} raw RGB bytes, observed {len(pixels)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.frombytes(PIXEL_MODE, (width, height), pixels)
    image.save(path, format="PNG", compress_level=9, optimize=False)
