"""Object-mode soft matte on real generated P11 objects (several intended parts, noise dropped)."""

from __future__ import annotations

from collections import deque
from pathlib import Path

import pytest

from project_atlas.static_character import (
    OBJECT_NOISE_THRESHOLD_PX,
    _decode_rgba_png,
    extract_soft_matte_character,
    extract_soft_matte_object,
)

FIXTURES = Path(__file__).parent / "fixtures" / "p11-objects"


def _visible_components(pixels: bytes, width: int, height: int) -> list[int]:
    size = width * height
    seen = bytearray(size)
    sizes = []
    for start in range(size):
        if seen[start] or not pixels[start * 4 + 3]:
            continue
        seen[start] = 1
        queue, count = deque([start]), 0
        while queue:
            index = queue.popleft()
            count += 1
            x = index % width
            for neighbour in (
                index - 1 if x else None,
                index + 1 if x + 1 < width else None,
                index - width if index >= width else None,
                index + width if index + width < size else None,
            ):
                if neighbour is not None and pixels[neighbour * 4 + 3] and not seen[neighbour]:
                    seen[neighbour] = 1
                    queue.append(neighbour)
        sizes.append(count)
    return sizes


@pytest.mark.parametrize("name", ["phone_arrows", "bet_half", "bet_two_thirds"])
def test_object_mode_keeps_every_intended_part_and_drops_only_noise(name) -> None:
    source = (FIXTURES / f"{name}.png").read_bytes()
    extraction = extract_soft_matte_object(source)
    assert extraction == extract_soft_matte_object(source)  # deterministic
    width, height, pixels = _decode_rgba_png(extraction.content)
    components = _visible_components(pixels, width, height)
    assert min(components) >= OBJECT_NOISE_THRESHOLD_PX == 50
    assert len(components) == len(extraction.kept_component_sizes)
    dropped = extraction.dropped_before_matte + extraction.dropped_after_matte
    assert dropped and max(dropped) < OBJECT_NOISE_THRESHOLD_PX
    provenance = extraction.provenance()["components"]
    assert provenance["noise_threshold_px"] == 50
    assert provenance["dropped_after_matte"] == list(extraction.dropped_after_matte)


def test_the_phone_keeps_all_three_red_arrows_opaque() -> None:
    source = (FIXTURES / "phone_arrows.png").read_bytes()
    width, height, original = _decode_rgba_png(source)
    _w, _h, pixels = _decode_rgba_png(extract_soft_matte_object(source).content)
    red = [
        index
        for index in range(width * height)
        if original[index * 4] > 180
        and original[index * 4 + 1] < 90
        and original[index * 4 + 2] < 90
    ]
    assert len(red) > 5000
    assert all(pixels[index * 4 + 3] == 255 for index in red)


@pytest.mark.parametrize("name", ["phone_arrows", "bet_half"])
def test_the_character_path_is_unchanged_and_still_refuses_these_islands(name) -> None:
    with pytest.raises(ValueError, match="stray pixel outside the drawing"):
        extract_soft_matte_character((FIXTURES / f"{name}.png").read_bytes())
