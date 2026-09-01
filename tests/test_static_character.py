from __future__ import annotations

from project_atlas.static_character import (
    _encode_rgba_png,
    extract_boundary_connected_background,
    verify_static_character_extraction,
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
