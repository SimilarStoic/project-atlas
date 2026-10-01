"""Deterministic, local-only extraction of a static character layer from PNG art."""

from __future__ import annotations

import struct
import zlib
from collections import deque
from dataclasses import dataclass
from hashlib import sha256

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@dataclass(frozen=True)
class StaticCharacterExtraction:
    """One validated, binary-alpha extraction and its durable technical facts."""

    content: bytes
    source_digest: str
    output_digest: str
    width: int
    height: int
    transparent_pixels: int
    retained_pixels: int
    foreground_bbox: tuple[int, int, int, int]
    background_min_channel: int
    background_max_channel_spread: int
    edge_matte_min_channel: int
    edge_matte_max_channel_spread: int
    edge_matte_passes: int

    def provenance(self) -> dict[str, object]:
        """Return the exact, serializable derivation record for a managed Asset."""

        return {
            "derivation": "deterministic-boundary-connected-background-extraction",
            "method_version": "v2",
            "source_sha256": self.source_digest,
            "output_sha256": self.output_digest,
            "source_dimensions": {"width": self.width, "height": self.height},
            "output_dimensions": {"width": self.width, "height": self.height},
            "background_rule": {
                "connected_to_image_boundary": True,
                "minimum_rgb_channel": self.background_min_channel,
                "maximum_rgb_channel_spread": self.background_max_channel_spread,
            },
            "edge_matte_cleanup": {
                "boundary_connected_only": True,
                "minimum_rgb_channel": self.edge_matte_min_channel,
                "maximum_rgb_channel_spread": self.edge_matte_max_channel_spread,
                "passes": self.edge_matte_passes,
            },
            "alpha": "binary; retained source RGB and any existing alpha are preserved exactly",
        }


def extract_boundary_connected_background(
    source_png: bytes,
    *,
    background_min_channel: int = 250,
    background_max_channel_spread: int = 5,
    edge_matte_min_channel: int = 235,
    edge_matte_max_channel_spread: int = 20,
    edge_matte_passes: int = 1,
) -> StaticCharacterExtraction:
    """Turn only bright, neutral exterior background pixels into transparency.

    Candidate background pixels are removed only if a four-connected path to an
    image boundary exists.  White or light character areas enclosed by linework
    are therefore retained with their original RGBA bytes, not color-keyed away.
    """

    if not 0 <= background_min_channel <= 255:
        raise ValueError("background_min_channel must be between 0 and 255.")
    if not 0 <= background_max_channel_spread <= 255:
        raise ValueError("background_max_channel_spread must be between 0 and 255.")
    if not 0 <= edge_matte_min_channel <= 255:
        raise ValueError("edge_matte_min_channel must be between 0 and 255.")
    if not 0 <= edge_matte_max_channel_spread <= 255:
        raise ValueError("edge_matte_max_channel_spread must be between 0 and 255.")
    if not isinstance(edge_matte_passes, int) or not 0 <= edge_matte_passes <= 4:
        raise ValueError("edge_matte_passes must be an integer between 0 and 4.")

    width, height, pixels = _decode_rgba_png(source_png)
    background = _boundary_connected_background(
        pixels,
        width,
        height,
        background_min_channel,
        background_max_channel_spread,
    )
    background = _expand_boundary_matte(
        pixels,
        background,
        width,
        height,
        edge_matte_min_channel,
        edge_matte_max_channel_spread,
        edge_matte_passes,
    )
    output = bytearray(pixels)
    for index, is_background in enumerate(background):
        if is_background:
            output[index * 4 + 3] = 0
    _validate_extraction(pixels, output, background, width, height)
    transparent_pixels = sum(background)
    retained = width * height - transparent_pixels
    bbox = _foreground_bbox(output, width, height)
    content = _encode_rgba_png(width, height, output)
    return StaticCharacterExtraction(
        content=content,
        source_digest=sha256(source_png).hexdigest(),
        output_digest=sha256(content).hexdigest(),
        width=width,
        height=height,
        transparent_pixels=transparent_pixels,
        retained_pixels=retained,
        foreground_bbox=bbox,
        background_min_channel=background_min_channel,
        background_max_channel_spread=background_max_channel_spread,
        edge_matte_min_channel=edge_matte_min_channel,
        edge_matte_max_channel_spread=edge_matte_max_channel_spread,
        edge_matte_passes=edge_matte_passes,
    )


def verify_static_character_extraction(
    source_png: bytes, extraction: StaticCharacterExtraction
) -> None:
    """Recompute and verify a stored extraction without any visual interpretation."""

    repeated = extract_boundary_connected_background(
        source_png,
        background_min_channel=extraction.background_min_channel,
        background_max_channel_spread=extraction.background_max_channel_spread,
        edge_matte_min_channel=extraction.edge_matte_min_channel,
        edge_matte_max_channel_spread=extraction.edge_matte_max_channel_spread,
        edge_matte_passes=extraction.edge_matte_passes,
    )
    if repeated != extraction:
        raise ValueError("Static character extraction does not reproduce exactly.")


def _boundary_connected_background(
    pixels: bytes,
    width: int,
    height: int,
    minimum: int,
    spread: int,
) -> bytearray:
    """Return a byte-per-pixel mask for eligible exterior background only."""

    mask = bytearray(width * height)
    queue: deque[int] = deque()

    def is_candidate(index: int) -> bool:
        offset = index * 4
        red, green, blue, alpha = pixels[offset : offset + 4]
        return (
            alpha == 255
            and min(red, green, blue) >= minimum
            and max(red, green, blue) - min(red, green, blue) <= spread
        )

    def add(index: int) -> None:
        if not mask[index] and is_candidate(index):
            mask[index] = 1
            queue.append(index)

    for x in range(width):
        add(x)
        add((height - 1) * width + x)
    for y in range(1, height - 1):
        add(y * width)
        add(y * width + width - 1)

    while queue:
        index = queue.popleft()
        x = index % width
        if x:
            add(index - 1)
        if x + 1 < width:
            add(index + 1)
        if index >= width:
            add(index - width)
        if index + width < width * height:
            add(index + width)
    return mask


def _expand_boundary_matte(
    pixels: bytes,
    background: bytearray,
    width: int,
    height: int,
    minimum: int,
    spread: int,
    passes: int,
) -> bytearray:
    """Remove only bright neutral fringe touching the already-proven exterior matte."""

    expanded = bytearray(background)
    for _pass in range(passes):
        additions: list[int] = []
        for index, removed in enumerate(expanded):
            if removed:
                continue
            offset = index * 4
            red, green, blue, alpha = pixels[offset : offset + 4]
            if (
                alpha != 255
                or min(red, green, blue) < minimum
                or max(red, green, blue) - min(red, green, blue) > spread
            ):
                continue
            x = index % width
            neighbors = (
                index - 1 if x else None,
                index + 1 if x + 1 < width else None,
                index - width if index >= width else None,
                index + width if index + width < width * height else None,
            )
            if any(neighbor is not None and expanded[neighbor] for neighbor in neighbors):
                additions.append(index)
        for index in additions:
            expanded[index] = 1
    return expanded


def _validate_extraction(
    source: bytes,
    output: bytes,
    background: bytearray,
    width: int,
    height: int,
) -> None:
    """Enforce exact retained pixels and a single exterior transparent component."""

    if not any(background) or all(background):
        raise ValueError("Extraction must retain character pixels and remove exterior background.")
    for index, is_background in enumerate(background):
        offset = index * 4
        if is_background:
            if (
                output[offset : offset + 3] != source[offset : offset + 3]
                or output[offset + 3] != 0
            ):
                raise ValueError(
                    "Background extraction changed RGB or failed to make alpha transparent."
                )
        elif output[offset : offset + 4] != source[offset : offset + 4]:
            raise ValueError("A retained character pixel changed during extraction.")
        if min(source[offset : offset + 3]) <= 80 and output[offset + 3] == 0:
            raise ValueError("A dark line/detail pixel was removed during extraction.")

    reachable = bytearray(width * height)
    queue: deque[int] = deque()
    for x in range(width):
        for index in (x, (height - 1) * width + x):
            if output[index * 4 + 3] == 0 and not reachable[index]:
                reachable[index] = 1
                queue.append(index)
    for y in range(1, height - 1):
        for index in (y * width, y * width + width - 1):
            if output[index * 4 + 3] == 0 and not reachable[index]:
                reachable[index] = 1
                queue.append(index)
    while queue:
        index = queue.popleft()
        x = index % width
        for neighbor in (
            index - 1 if x else None,
            index + 1 if x + 1 < width else None,
            index - width if index >= width else None,
            index + width if index + width < width * height else None,
        ):
            if neighbor is not None and output[neighbor * 4 + 3] == 0 and not reachable[neighbor]:
                reachable[neighbor] = 1
                queue.append(neighbor)
    if any(output[index * 4 + 3] == 0 and not reachable[index] for index in range(width * height)):
        raise ValueError("Extraction produced an unexpected transparent interior hole.")


def _foreground_bbox(pixels: bytes, width: int, height: int) -> tuple[int, int, int, int]:
    foreground = [index for index in range(width * height) if pixels[index * 4 + 3] != 0]
    if not foreground:
        raise ValueError("Extraction removed every pixel.")
    return (
        min(index % width for index in foreground),
        min(index // width for index in foreground),
        max(index % width for index in foreground),
        max(index // width for index in foreground),
    )


def _decode_rgba_png(content: bytes) -> tuple[int, int, bytes]:
    """Decode an 8-bit non-interlaced RGB/RGBA PNG into exact RGBA pixels."""

    if not content.startswith(PNG_SIGNATURE):
        raise ValueError("Static character source must be a PNG.")
    cursor = len(PNG_SIGNATURE)
    width = height = color_type = None
    compressed = bytearray()
    while cursor < len(content):
        if cursor + 12 > len(content):
            raise ValueError("PNG chunk is truncated.")
        length = struct.unpack(">I", content[cursor : cursor + 4])[0]
        kind = content[cursor + 4 : cursor + 8]
        end = cursor + 8 + length
        if end + 4 > len(content):
            raise ValueError("PNG chunk data is truncated.")
        data = content[cursor + 8 : end]
        expected_crc = struct.unpack(">I", content[end : end + 4])[0]
        if zlib.crc32(kind + data) & 0xFFFFFFFF != expected_crc:
            raise ValueError("PNG chunk checksum is invalid.")
        if kind == b"IHDR":
            if length != 13:
                raise ValueError("PNG IHDR is invalid.")
            (
                width,
                height,
                bit_depth,
                color_type,
                compression,
                filter_method,
                interlace,
            ) = struct.unpack(">IIBBBBB", data)
            encoding = (bit_depth, color_type, compression, filter_method, interlace)
            if (
                not width
                or not height
                or encoding
                not in {
                    (8, 2, 0, 0, 0),
                    (8, 6, 0, 0, 0),
                }
            ):
                raise ValueError(
                    "Static character source must be an 8-bit non-interlaced RGB/RGBA PNG."
                )
        elif kind == b"IDAT":
            compressed.extend(data)
        elif kind == b"IEND":
            break
        cursor = end + 4
    if width is None or height is None or not compressed:
        raise ValueError("PNG requires IHDR and IDAT data.")
    raw = zlib.decompress(compressed)
    bytes_per_pixel = 4 if color_type == 6 else 3
    stride = width * bytes_per_pixel
    if len(raw) != height * (stride + 1):
        raise ValueError("PNG image data length is invalid.")
    decoded = bytearray(height * stride)
    previous = bytearray(stride)
    offset = 0
    for row in range(height):
        filter_type = raw[offset]
        encoded = raw[offset + 1 : offset + 1 + stride]
        offset += stride + 1
        current = bytearray(stride)
        for column, value in enumerate(encoded):
            left = current[column - bytes_per_pixel] if column >= bytes_per_pixel else 0
            above = previous[column]
            upper_left = previous[column - bytes_per_pixel] if column >= bytes_per_pixel else 0
            if filter_type == 0:
                current[column] = value
            elif filter_type == 1:
                current[column] = (value + left) & 0xFF
            elif filter_type == 2:
                current[column] = (value + above) & 0xFF
            elif filter_type == 3:
                current[column] = (value + ((left + above) // 2)) & 0xFF
            elif filter_type == 4:
                current[column] = (value + _paeth(left, above, upper_left)) & 0xFF
            else:
                raise ValueError("PNG uses an unsupported filter.")
        start = row * stride
        decoded[start : start + stride] = current
        previous = current
    if color_type == 6:
        return width, height, bytes(decoded)
    rgba = bytearray(width * height * 4)
    for index in range(width * height):
        source = index * 3
        target = index * 4
        rgba[target : target + 3] = decoded[source : source + 3]
        rgba[target + 3] = 255
    return width, height, bytes(rgba)


def _encode_rgba_png(width: int, height: int, pixels: bytes) -> bytes:
    """Encode deterministic 8-bit RGBA PNG bytes with unfiltered scanlines."""

    stride = width * 4
    raw = b"".join(b"\x00" + pixels[row * stride : (row + 1) * stride] for row in range(height))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    return (
        PNG_SIGNATURE
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, level=9))
        + chunk(b"IEND", b"")
    )


def _paeth(left: int, above: int, upper_left: int) -> int:
    predictor = left + above - upper_left
    distances = abs(predictor - left), abs(predictor - above), abs(predictor - upper_left)
    if distances[0] <= distances[1] and distances[0] <= distances[2]:
        return left
    if distances[1] <= distances[2]:
        return above
    return upper_left
