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
            "alpha": "binary; retained pixels preserve source RGBA exactly",
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
    """Decode the explicit 8-bit non-interlaced RGBA PNG form used by the anchor."""

    if not content.startswith(PNG_SIGNATURE):
        raise ValueError("Static character source must be a PNG.")
    cursor = len(PNG_SIGNATURE)
    width = height = None
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
                != (
                    8,
                    6,
                    0,
                    0,
                    0,
                )
            ):
                raise ValueError(
                    "Static character source must be an 8-bit non-interlaced RGBA PNG."
                )
        elif kind == b"IDAT":
            compressed.extend(data)
        elif kind == b"IEND":
            break
        cursor = end + 4
    if width is None or height is None or not compressed:
        raise ValueError("PNG requires IHDR and IDAT data.")
    raw = zlib.decompress(compressed)
    stride = width * 4
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
            left = current[column - 4] if column >= 4 else 0
            above = previous[column]
            upper_left = previous[column - 4] if column >= 4 else 0
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
    return width, height, bytes(decoded)


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


@dataclass(frozen=True)
class SoftMatteExtraction:
    """One anti-aliased, colour-decontaminated character matte and its technical facts."""

    content: bytes
    source_digest: str
    output_digest: str
    width: int
    height: int
    paper_rgb: tuple[int, int, int]
    ink_luminance: int
    retained_pixels: int
    partial_alpha_pixels: int
    dropped_components: int
    dropped_pixels: int
    isolated_edge_pixels: int
    background_min_channel: int
    background_max_channel_spread: int
    band_radius: int
    alpha_floor: int

    def provenance(self) -> dict[str, object]:
        """Return the exact, serializable derivation record for a managed Asset."""

        return {
            "derivation": "deterministic-soft-matte-extraction",
            "method_version": "v3",
            "source_sha256": self.source_digest,
            "output_sha256": self.output_digest,
            "dimensions": {"width": self.width, "height": self.height},
            "background_rule": {
                "connected_to_image_boundary": True,
                "minimum_rgb_channel": self.background_min_channel,
                "maximum_rgb_channel_spread": self.background_max_channel_spread,
            },
            "matte": {
                "paper_rgb": list(self.paper_rgb),
                "ink_luminance": self.ink_luminance,
                "band_radius": self.band_radius,
                "alpha_floor": self.alpha_floor,
                "partial_alpha_pixels": self.partial_alpha_pixels,
            },
            "residue": {
                "kept": "largest four-connected component only",
                "dropped_components": self.dropped_components,
                "dropped_pixels": self.dropped_pixels,
                "isolated_edge_pixels": self.isolated_edge_pixels,
            },
            "alpha": "8-bit straight alpha; interior pixels preserve source RGBA exactly; edge "
            "colours are unblended from the measured paper colour",
        }


def _luminance(red: int, green: int, blue: int) -> int:
    return (299 * red + 587 * green + 114 * blue) // 1000


def extract_soft_matte_character(
    source_png: bytes,
    *,
    background_min_channel: int = 240,
    background_max_channel_spread: int = 20,
    band_radius: int = 2,
    alpha_floor: int = 8,
) -> SoftMatteExtraction:
    """Cut one character from light paper with the drawing's own anti-aliased outline.

    Exterior paper is found exactly as in v2 (boundary-connected bright neutral pixels). Only the
    largest connected drawing component is kept, so stray specks never survive. Neutral pixels in
    a thin band across the outline get alpha from their luminance between the measured paper and
    ink, and their colour is unblended from the paper so no light fringe remains. Every pixel
    deeper inside the drawing keeps its exact source RGBA.
    """

    if not 0 <= background_min_channel <= 255 or not 0 <= background_max_channel_spread <= 255:
        raise ValueError("Background thresholds must be between 0 and 255.")
    if not isinstance(band_radius, int) or not 1 <= band_radius <= 4:
        raise ValueError("band_radius must be an integer between 1 and 4.")
    if not isinstance(alpha_floor, int) or not 0 <= alpha_floor <= 64:
        raise ValueError("alpha_floor must be an integer between 0 and 64.")
    width, height, pixels = _decode_rgba_png(source_png)
    size = width * height
    exterior = _boundary_connected_background(
        pixels, width, height, background_min_channel, background_max_channel_spread
    )
    if not any(exterior) or all(exterior):
        raise ValueError("Extraction must find both exterior paper and a drawing.")

    def neighbours(index: int):
        x = index % width
        if x:
            yield index - 1
        if x + 1 < width:
            yield index + 1
        if index >= width:
            yield index - width
        if index + width < size:
            yield index + width

    component = [0] * size
    sizes = [0]
    for start in range(size):
        if exterior[start] or component[start]:
            continue
        sizes.append(0)
        label = len(sizes) - 1
        component[start] = label
        queue = deque([start])
        while queue:
            index = queue.popleft()
            sizes[label] += 1
            for neighbour in neighbours(index):
                if not exterior[neighbour] and not component[neighbour]:
                    component[neighbour] = label
                    queue.append(neighbour)
    keep = max(range(1, len(sizes)), key=lambda label: (sizes[label], -label))
    paper = [0, 0, 0]
    paper_count = 0
    for index in range(size):
        if exterior[index]:
            offset = index * 4
            paper[0] += pixels[offset]
            paper[1] += pixels[offset + 1]
            paper[2] += pixels[offset + 2]
            paper_count += 1
    paper_rgb = (paper[0] // paper_count, paper[1] // paper_count, paper[2] // paper_count)
    paper_luminance = _luminance(*paper_rgb)
    dropped_pixels = 0
    for index in range(size):
        if component[index] not in (0, keep):
            exterior[index] = 1
            dropped_pixels += 1

    edge = [
        index
        for index in range(size)
        if not exterior[index] and any(exterior[n] for n in neighbours(index))
    ]
    # Ink is the darkest linework of the kept drawing (its darkest 1% of neutral pixels).
    drawing_luminance = sorted(
        _luminance(*pixels[i * 4 : i * 4 + 3])
        for i in range(size)
        if component[i] == keep
        and max(pixels[i * 4 : i * 4 + 3]) - min(pixels[i * 4 : i * 4 + 3]) <= 40
    )
    ink_luminance = drawing_luminance[len(drawing_luminance) // 100]
    if paper_luminance - ink_luminance < 32:
        raise ValueError("Outline is not distinguishable from the paper colour.")

    distance = [0] * size
    queue = deque()
    for index in edge:
        for neighbour in neighbours(index):
            if exterior[neighbour] and not distance[neighbour]:
                distance[neighbour] = 1
                queue.append(neighbour)
    while queue:
        index = queue.popleft()
        if distance[index] >= band_radius:
            continue
        for neighbour in neighbours(index):
            if exterior[neighbour] and not distance[neighbour]:
                distance[neighbour] = distance[index] + 1
                queue.append(neighbour)

    output = bytearray(size * 4)
    span = paper_luminance - ink_luminance
    partial = retained = 0
    edge_set = set(edge)
    for index in range(size):
        offset = index * 4
        red, green, blue, _alpha = pixels[offset : offset + 4]
        neutral = max(red, green, blue) - min(red, green, blue) <= 40
        on_edge = index in edge_set
        if not exterior[index] and not (on_edge and neutral):
            output[offset : offset + 4] = pixels[offset : offset + 4]
            retained += 1
            continue
        if not neutral or not (on_edge or distance[index]):
            continue
        matte = ((paper_luminance - _luminance(red, green, blue)) * 255 + span // 2) // span
        matte = max(0, min(255, matte))
        if matte < alpha_floor:
            continue
        if matte == 255:
            output[offset : offset + 4] = bytes((red, green, blue, 255))
        else:
            for channel, value in enumerate((red, green, blue)):
                unblended = (value * 255 - (255 - matte) * paper_rgb[channel] + matte // 2) // matte
                output[offset + channel] = max(0, min(255, unblended))
            output[offset + 3] = matte
            partial += 1
        retained += 1
    # Edge-band pixels count only where they connect to the kept drawing; isolated faint pixels
    # (beyond an invisible band pixel or beside a dropped speck) are residue.
    connected = bytearray(size)
    queue = deque(
        index for index in range(size) if component[index] == keep and output[index * 4 + 3]
    )
    for index in queue:
        connected[index] = 1
    while queue:
        index = queue.popleft()
        for neighbour in neighbours(index):
            if output[neighbour * 4 + 3] and not connected[neighbour]:
                connected[neighbour] = 1
                queue.append(neighbour)
    isolated = 0
    for index in range(size):
        if output[index * 4 + 3] and not connected[index]:
            partial -= output[index * 4 + 3] < 255
            output[index * 4 : index * 4 + 4] = bytes(4)
            isolated += 1
            retained -= 1
    _validate_soft_matte(pixels, bytes(output), component, keep, width, height)
    content = _encode_rgba_png(width, height, bytes(output))
    return SoftMatteExtraction(
        content=content,
        source_digest=sha256(source_png).hexdigest(),
        output_digest=sha256(content).hexdigest(),
        width=width,
        height=height,
        paper_rgb=paper_rgb,
        ink_luminance=ink_luminance,
        retained_pixels=retained,
        partial_alpha_pixels=partial,
        dropped_components=len(sizes) - 2,
        dropped_pixels=dropped_pixels,
        isolated_edge_pixels=isolated,
        background_min_channel=background_min_channel,
        background_max_channel_spread=background_max_channel_spread,
        band_radius=band_radius,
        alpha_floor=alpha_floor,
    )


def _validate_soft_matte(
    source: bytes,
    output: bytes,
    component: list[int],
    keep: int,
    width: int,
    height: int,
) -> None:
    """Enforce intact dark linework, no colour residue and no pixel outside one drawing."""

    size = width * height
    for index in range(size):
        offset = index * 4
        alpha = output[offset + 3]
        if alpha == 0 and output[offset : offset + 3] != b"\x00\x00\x00":
            raise ValueError("A transparent pixel kept colour residue.")
        if component[index] == keep and min(source[offset : offset + 3]) <= 80 and alpha < 128:
            raise ValueError("A dark line/detail pixel was removed during extraction.")
    start = next(i for i in range(size) if component[i] == keep)
    seen = bytearray(size)
    seen[start] = 1
    queue = deque([start])
    while queue:
        index = queue.popleft()
        x = index % width
        for neighbour in (
            index - 1 if x else None,
            index + 1 if x + 1 < width else None,
            index - width if index >= width else None,
            index + width if index + width < size else None,
        ):
            if neighbour is not None and output[neighbour * 4 + 3] and not seen[neighbour]:
                seen[neighbour] = 1
                queue.append(neighbour)
    if any(output[index * 4 + 3] and not seen[index] for index in range(size)):
        raise ValueError("Extraction left a stray pixel outside the drawing.")


def verify_soft_matte_extraction(source_png: bytes, extraction: SoftMatteExtraction) -> None:
    """Recompute a stored soft-matte extraction and require an exact match."""

    repeated = extract_soft_matte_character(
        source_png,
        background_min_channel=extraction.background_min_channel,
        background_max_channel_spread=extraction.background_max_channel_spread,
        band_radius=extraction.band_radius,
        alpha_floor=extraction.alpha_floor,
    )
    if repeated != extraction:
        raise ValueError("Soft-matte extraction does not reproduce exactly.")
