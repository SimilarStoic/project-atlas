"""Deterministic admission-time resampling of scene layers (the alpha render policy places 1:1)."""

from __future__ import annotations

import math
from typing import Any

DOWNSCALE_ADAPTER = "premultiplied-area-downscale-v1"


def _weights(source: int, target: int) -> list[list[tuple[int, float]]]:
    scale = source / target
    spans = []
    for index in range(target):
        start, end = index * scale, (index + 1) * scale
        spans.append(
            [
                (pixel, min(end, pixel + 1) - max(start, pixel))
                for pixel in range(math.floor(start), min(source, math.ceil(end)))
                if min(end, pixel + 1) > max(start, pixel)
            ]
        )
    return spans


def downscale_premultiplied_area(
    rgba: bytes, width: int, height: int, target_width: int, target_height: int
) -> bytes:
    """Exact area average of premultiplied RGBA, straight 8-bit RGBA out; never upscales.

    Averaging premultiplied colour means transparent pixels contribute no colour, so edges keep
    the drawing's own colour instead of picking up a dark or light fringe.
    """

    if len(rgba) != width * height * 4:
        raise ValueError("RGBA bytes do not match their dimensions.")
    if not 0 < target_width <= width or not 0 < target_height <= height:
        raise ValueError("Admission resampling only downscales.")
    columns, rows = _weights(width, target_width), _weights(height, target_height)
    area = (width / target_width) * (height / target_height)
    output = bytearray(target_width * target_height * 4)
    out = 0
    for row_weights in rows:
        for column_weights in columns:
            red = green = blue = alpha = 0.0
            for y, weight_y in row_weights:
                base = y * width
                for x, weight_x in column_weights:
                    offset = (base + x) * 4
                    weight = weight_x * weight_y * rgba[offset + 3]
                    if weight:
                        red += rgba[offset] * weight
                        green += rgba[offset + 1] * weight
                        blue += rgba[offset + 2] * weight
                        alpha += weight
            value = int(alpha / area + 0.5)
            if value:
                output[out] = min(255, int(red / alpha + 0.5))
                output[out + 1] = min(255, int(green / alpha + 0.5))
                output[out + 2] = min(255, int(blue / alpha + 0.5))
                output[out + 3] = min(255, value)
            out += 4
    return bytes(output)


def downscale_provenance(
    width: int, height: int, target_width: int, target_height: int
) -> dict[str, Any]:
    """The admission record a downscaled scene layer carries in its Asset metadata."""

    return {
        "method": "exact area average of premultiplied 8-bit RGBA, straight alpha out",
        "source_dimensions": [width, height],
        "target_dimensions": [target_width, target_height],
    }
