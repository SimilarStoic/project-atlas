from __future__ import annotations

import struct
import zlib

from project_atlas.static_character import (
    _decode_rgba_png,
    _encode_rgba_png,
    extract_boundary_connected_background,
    verify_static_character_extraction,
)


def _encode_rgb_png(width: int, height: int, pixels: bytes) -> bytes:
    stride = width * 3
    raw = b"".join(b"\x00" + pixels[row * stride : (row + 1) * stride] for row in range(height))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, level=9))
        + chunk(b"IEND", b"")
    )


def test_boundary_connected_extraction_keeps_enclosed_light_character_pixels_and_lines() -> None:
    """Only eligible exterior pixels become transparent; no visual detail is repainted."""

    # A dark, closed outline protects the light interior from the off-white exterior.
    pixels = bytearray()
    background = (253, 254, 255, 255)
    for y in range(7):
        for x in range(7):
            color = background
            if x in {1, 5} and 1 <= y <= 5 or y in {1, 5} and 1 <= x <= 5:
                color = (10, 10, 10, 255)
            if 2 <= x <= 4 and 2 <= y <= 4:
                color = (255, 255, 255, 255)
            pixels.extend(color)
    source = _encode_rgba_png(7, 7, bytes(pixels))

    extraction = extract_boundary_connected_background(source)

    assert extraction.width == 7
    assert extraction.height == 7
    assert extraction.transparent_pixels == 24
    assert extraction.retained_pixels == 25
    assert extraction.foreground_bbox == (1, 1, 5, 5)
    assert extraction.source_digest != extraction.output_digest
    assert (
        extraction.provenance()["derivation"]
        == "deterministic-boundary-connected-background-extraction"
    )
    verify_static_character_extraction(source, extraction)


def test_extraction_rejects_invalid_png_content() -> None:
    """The deterministic production path never guesses at an unsupported image format."""

    try:
        extract_boundary_connected_background(b"not a png")
    except ValueError as error:
        assert "PNG" in str(error)
    else:
        raise AssertionError("Unsupported source content was accepted.")


def test_boundary_matte_cleanup_removes_only_connected_light_fringe() -> None:
    """One bounded pass removes baked background halo without erasing dark contour pixels."""

    pixels = bytearray()
    for y in range(5):
        for x in range(5):
            if x in {0, 4} or y in {0, 4}:
                color = (254, 254, 254, 255)
            elif x in {1, 3} or y in {1, 3}:
                color = (244, 242, 243, 255)
            else:
                color = (20, 20, 20, 255)
            pixels.extend(color)
    source = _encode_rgba_png(5, 5, bytes(pixels))

    extraction = extract_boundary_connected_background(source)
    width, height, output = _decode_rgba_png(extraction.content)

    assert (width, height) == (5, 5)
    assert extraction.transparent_pixels == 24
    assert extraction.foreground_bbox == (2, 2, 2, 2)
    assert output[(2 * width + 2) * 4 : (2 * width + 2) * 4 + 4] == bytes((20, 20, 20, 255))
    assert extraction.provenance()["edge_matte_cleanup"]["passes"] == 1


def test_rgb_source_extraction_is_reproducible_and_preserves_retained_rgb() -> None:
    pixels = bytearray()
    for y in range(5):
        for x in range(5):
            pixels.extend((240, 238, 232) if x in {0, 4} or y in {0, 4} else (20, 30, 40))
    source = _encode_rgb_png(5, 5, bytes(pixels))

    extraction = extract_boundary_connected_background(
        source,
        background_min_channel=230,
        background_max_channel_spread=12,
    )
    repeated = extract_boundary_connected_background(
        source,
        background_min_channel=230,
        background_max_channel_spread=12,
    )
    width, height, output = _decode_rgba_png(extraction.content)

    assert extraction == repeated
    assert (width, height) == (5, 5)
    assert output[(2 * width + 2) * 4 : (2 * width + 2) * 4 + 4] == bytes((20, 30, 40, 255))
    verify_static_character_extraction(source, extraction)
