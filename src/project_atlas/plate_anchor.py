"""Plate-anchored acquisition: an approved room plate is the immutable output canvas.

The provider receives the plate as its first image with a mask that opens only the action
region. Whatever it returns, Atlas keeps every plate pixel outside that region exactly and
blends the provider's drawing in only inside it. Dependency-free 8-bit PNG handling only.
"""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass
from typing import Any

METHOD = "plate-anchor-mask-composite-v1"
DEFAULT_FEATHER_PX = 16
MAX_MASK_BYTES = 4 * 1024 * 1024
ANCHOR_KEYS = frozenset({"authority_id", "viewpoint", "action_region", "feather_px"})
_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_CHANNELS = {0: 1, 2: 3, 4: 2, 6: 4}


@dataclass(frozen=True)
class Raster:
    """Exact 8-bit pixels: 3 (RGB) or 4 (RGBA) channels, rows top to bottom."""

    width: int
    height: int
    channels: int
    pixels: bytes

    @property
    def stride(self) -> int:
        return self.width * self.channels


@dataclass(frozen=True)
class ActionRegion:
    """One rectangle, in plate pixels, that the provider may redraw."""

    x: int
    y: int
    width: int
    height: int

    def payload(self) -> dict[str, int]:
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}


def validate_anchor_spec(value: Any) -> dict[str, Any]:
    """Validate one AssetSpec plate_anchor object without resolving anything."""

    if not isinstance(value, dict) or not {"authority_id", "viewpoint", "action_region"} <= set(
        value
    ):
        raise ValueError("plate_anchor requires authority_id, viewpoint and action_region.")
    if set(value) - ANCHOR_KEYS:
        raise ValueError("plate_anchor has unsupported keys.")
    for key in ("authority_id", "viewpoint"):
        if not isinstance(value[key], str) or not value[key].strip():
            raise ValueError(f"plate_anchor {key} must be non-empty text.")
    feather = value.get("feather_px", DEFAULT_FEATHER_PX)
    if type(feather) is not int or feather < 0:
        raise ValueError("plate_anchor feather_px must be a non-negative integer.")
    return value


def action_region(value: Any, width: int, height: int) -> ActionRegion:
    """Validate a rectangle that lies inside, and is smaller than, the plate."""

    if not isinstance(value, dict) or set(value) != {"x", "y", "width", "height"}:
        raise ValueError("plate_anchor action_region requires exactly x, y, width and height.")
    if not all(type(value[key]) is int for key in value):
        raise ValueError("plate_anchor action_region values must be integers.")
    region = ActionRegion(value["x"], value["y"], value["width"], value["height"])
    if region.x < 0 or region.y < 0 or region.width <= 0 or region.height <= 0:
        raise ValueError("plate_anchor action_region must be a positive rectangle.")
    if region.x + region.width > width or region.y + region.height > height:
        raise ValueError("plate_anchor action_region lies outside the plate.")
    if region.width == width and region.height == height:
        raise ValueError("plate_anchor action_region cannot open the whole plate.")
    return region


def _chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))


def encode_png(raster: Raster) -> bytes:
    """Encode exact pixels losslessly (filter 0, deterministic deflate)."""

    if raster.channels not in (3, 4) or len(raster.pixels) != raster.stride * raster.height:
        raise ValueError("Raster dimensions do not match its pixel content.")
    stride = raster.stride
    scanlines = b"".join(
        b"\x00" + raster.pixels[offset : offset + stride]
        for offset in range(0, len(raster.pixels), stride)
    )
    colour_type = 2 if raster.channels == 3 else 6
    header = struct.pack(">IIBBBBB", raster.width, raster.height, 8, colour_type, 0, 0, 0)
    return (
        _SIGNATURE
        + _chunk(b"IHDR", header)
        + _chunk(b"IDAT", zlib.compress(scanlines, 9))
        + _chunk(b"IEND", b"")
    )


def _paeth(left: int, up: int, upper_left: int) -> int:
    estimate = left + up - upper_left
    distance_left, distance_up = abs(estimate - left), abs(estimate - up)
    distance_upper_left = abs(estimate - upper_left)
    if distance_left <= distance_up and distance_left <= distance_upper_left:
        return left
    return up if distance_up <= distance_upper_left else upper_left


def decode_png(content: bytes) -> Raster:
    """Decode a non-interlaced 8-bit grey, grey-alpha, RGB or RGBA PNG to RGB or RGBA."""

    if not content.startswith(_SIGNATURE):
        raise ValueError("Image is not a PNG.")
    offset, header, data = len(_SIGNATURE), None, bytearray()
    while offset + 8 <= len(content):
        (length,) = struct.unpack(">I", content[offset : offset + 4])
        kind = content[offset + 4 : offset + 8]
        payload = content[offset + 8 : offset + 8 + length]
        if len(payload) != length:
            raise ValueError("PNG chunk is truncated.")
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", payload)
        elif kind == b"IDAT":
            data.extend(payload)
        elif kind == b"IEND":
            break
        offset += 12 + length
    if header is None or not data:
        raise ValueError("PNG has no header or image data.")
    width, height, depth, colour_type, _compression, _filter, interlace = header
    if depth != 8 or colour_type not in _CHANNELS or interlace != 0:
        raise ValueError("Only non-interlaced 8-bit grey, RGB or RGBA PNGs are supported.")
    channels = _CHANNELS[colour_type]
    stride = width * channels
    raw = zlib.decompress(bytes(data))
    if len(raw) != (stride + 1) * height:
        raise ValueError("PNG image data does not match its header.")
    rows: list[bytes] = []
    previous = bytes(stride)
    for row_index in range(height):
        start = row_index * (stride + 1)
        kind, row = raw[start], bytearray(raw[start + 1 : start + 1 + stride])
        if kind == 1:
            for i in range(channels, stride):
                row[i] = (row[i] + row[i - channels]) & 0xFF
        elif kind == 2:
            row = bytearray((a + b) & 0xFF for a, b in zip(row, previous, strict=True))
        elif kind == 3:
            for i in range(stride):
                left = row[i - channels] if i >= channels else 0
                row[i] = (row[i] + ((left + previous[i]) >> 1)) & 0xFF
        elif kind == 4:
            for i in range(stride):
                if i >= channels:
                    left, upper_left = row[i - channels], previous[i - channels]
                else:
                    left = upper_left = 0
                row[i] = (row[i] + _paeth(left, previous[i], upper_left)) & 0xFF
        elif kind != 0:
            raise ValueError("PNG uses an unknown row filter.")
        previous = bytes(row)
        rows.append(previous)
    pixels = b"".join(rows)
    if channels == 1:
        return Raster(width, height, 3, bytes(v for v in pixels for _ in range(3)))
    if channels == 2:
        expanded = bytearray()
        for i in range(0, len(pixels), 2):
            expanded.extend((pixels[i], pixels[i], pixels[i], pixels[i + 1]))
        return Raster(width, height, 4, bytes(expanded))
    return Raster(width, height, channels, pixels)


def with_channels(raster: Raster, channels: int) -> Raster:
    """Match the plate's channel count: add opaque alpha, or drop alpha."""

    if raster.channels == channels:
        return raster
    if channels == 4:
        source, expanded = raster.pixels, bytearray()
        for i in range(0, len(source), 3):
            expanded.extend(source[i : i + 3])
            expanded.append(255)
        return Raster(raster.width, raster.height, 4, bytes(expanded))
    source = raster.pixels
    dropped = bytearray()
    for i in range(0, len(source), 4):
        dropped.extend(source[i : i + 3])
    return Raster(raster.width, raster.height, 3, bytes(dropped))


def resize_bilinear(raster: Raster, width: int, height: int) -> Raster:
    """Resample a provider output (never the plate) to the plate's exact dimensions."""

    if (raster.width, raster.height) == (width, height):
        return raster
    channels, source, stride = raster.channels, raster.pixels, raster.stride

    def axis(target: int, size: int) -> list[tuple[int, int, float]]:
        scale = size / target
        samples = []
        for index in range(target):
            position = min(max((index + 0.5) * scale - 0.5, 0.0), size - 1)
            low = int(position)
            samples.append((low, min(low + 1, size - 1), position - low))
        return samples

    columns, rows = axis(width, raster.width), axis(height, raster.height)
    output = bytearray(width * height * channels)
    out = 0
    for top, bottom, fy in rows:
        top_row, bottom_row = top * stride, bottom * stride
        for left, right, fx in columns:
            a, b = top_row + left * channels, top_row + right * channels
            c, d = bottom_row + left * channels, bottom_row + right * channels
            for k in range(channels):
                upper = source[a + k] + (source[b + k] - source[a + k]) * fx
                lower = source[c + k] + (source[d + k] - source[c + k]) * fx
                output[out] = int(upper + (lower - upper) * fy + 0.5)
                out += 1
    return Raster(width, height, channels, bytes(output))


def mask_png(width: int, height: int, region: ActionRegion) -> bytes:
    """An RGBA mask the plate's size: transparent (editable) only inside the region."""

    opaque, clear = b"\x00\x00\x00\xff", b"\x00\x00\x00\x00"
    outside_row = opaque * width
    inside_row = (
        opaque * region.x + clear * region.width + opaque * (width - region.x - region.width)
    )
    pixels = b"".join(
        inside_row if region.y <= y < region.y + region.height else outside_row
        for y in range(height)
    )
    encoded = encode_png(Raster(width, height, 4, pixels))
    if len(encoded) >= MAX_MASK_BYTES:
        raise ValueError("The plate mask PNG is not under 4 MB.")
    return encoded


def composite(plate: Raster, generated: Raster, region: ActionRegion, feather: int) -> Raster:
    """Keep every plate pixel outside the region; blend wholly inside it.

    A region edge that is also a plate edge needs no blend, so only interior edges feather.
    """

    if (generated.width, generated.height, generated.channels) != (
        plate.width,
        plate.height,
        plate.channels,
    ):
        raise ValueError("Generated pixels must already match the plate's size and channels.")
    channels, stride = plate.channels, plate.stride
    output = bytearray(plate.pixels)
    right, bottom = region.x + region.width, region.y + region.height
    open_left, open_top = region.x > 0, region.y > 0
    open_right, open_bottom = right < plate.width, bottom < plate.height
    for y in range(region.y, bottom):
        vertical = min(
            (y - region.y + 1) if open_top else 1 << 30,
            (bottom - y) if open_bottom else 1 << 30,
        )
        row = y * stride
        for x in range(region.x, right):
            distance = min(
                vertical,
                (x - region.x + 1) if open_left else 1 << 30,
                (right - x) if open_right else 1 << 30,
            )
            weight = 1.0 if feather == 0 or distance >= feather else distance / feather
            at = row + x * channels
            if weight == 1.0:
                output[at : at + channels] = generated.pixels[at : at + channels]
                continue
            for k in range(channels):
                base = plate.pixels[at + k]
                output[at + k] = int(base + (generated.pixels[at + k] - base) * weight + 0.5)
    return Raster(plate.width, plate.height, channels, bytes(output))


def changed_pixels_outside(plate: Raster, result: Raster, region: ActionRegion) -> int:
    """Count pixels outside the region that differ from the plate (must be zero)."""

    if (plate.width, plate.height, plate.channels) != (
        result.width,
        result.height,
        result.channels,
    ):
        raise ValueError("Compared rasters differ in size or channels.")
    channels, stride, changed = plate.channels, plate.stride, 0
    left, right = region.x * channels, (region.x + region.width) * channels
    for y in range(plate.height):
        row = y * stride
        a, b = plate.pixels[row : row + stride], result.pixels[row : row + stride]
        segments = (
            [(0, left), (right, stride)]
            if region.y <= y < region.y + region.height
            else [(0, stride)]
        )
        for start, end in segments:
            if a[start:end] != b[start:end]:
                changed += sum(
                    a[i : i + channels] != b[i : i + channels] for i in range(start, end, channels)
                )
    return changed
