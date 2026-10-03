"""Deterministic adapter from sealed persistent scene state to a local raster frame."""

from __future__ import annotations

import hashlib
import json
import struct
import zlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from project_atlas.scene_model import (
    RENDER_POLICY,
    canonical_json,
    digest,
    render,
    snapshot_payload,
    validate_snapshot_payload,
)

if TYPE_CHECKING:
    from project_atlas.persistence import AtlasRepository

SNAPSHOT_SCHEMA_VERSION = "v2"
COMPOSITOR_IDENTITY = "persistent-scene-rgba-v1"
FRAME_ENCODING = "png-filter0-deflate-store-v1"


@dataclass(frozen=True)
class PersistentSceneFrame:
    """One independently revalidated deterministic frame and its frozen lineage."""

    width: int
    height: int
    rgba: bytes
    rgba_digest: str
    png: bytes
    png_digest: str
    scene_model_snapshot: dict[str, Any]
    scene_model_snapshot_digest: str
    world_id: str
    admission_catalog_id: str
    transition_intent_id: str


def _chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))


def _zlib_store(payload: bytes) -> bytes:
    """Return one canonical zlib stream using only explicit stored DEFLATE blocks."""

    encoded = bytearray(b"\x78\x01")
    for offset in range(0, len(payload), 65535):
        block = payload[offset : offset + 65535]
        final = offset + len(block) == len(payload)
        encoded.append(1 if final else 0)
        encoded.extend(struct.pack("<H", len(block)))
        encoded.extend(struct.pack("<H", 0xFFFF - len(block)))
        encoded.extend(block)
    encoded.extend(struct.pack(">I", zlib.adler32(payload)))
    return bytes(encoded)


def encode_rgba_png(width: int, height: int, rgba: bytes) -> bytes:
    """Encode exact RGBA pixels as a deterministic dependency-free PNG."""

    if width <= 0 or height <= 0 or len(rgba) != width * height * 4:
        raise ValueError("RGBA frame dimensions do not match its byte content.")
    stride = width * 4
    scanlines = b"".join(
        b"\x00" + rgba[offset : offset + stride] for offset in range(0, len(rgba), stride)
    )
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", header)
        + _chunk(b"IDAT", _zlib_store(scanlines))
        + _chunk(b"IEND", b"")
    )


def load_persistent_scene_frame(repository: AtlasRepository, state_id: str) -> PersistentSceneFrame:
    """Reload, validate and render one exact sealed state without mutable inference."""

    context = repository.get_persistent_scene_media_context(state_id)
    payload = snapshot_payload(context.world, context.state)
    validate_snapshot_payload(payload)
    frozen_payload = json.loads(canonical_json(payload))
    result = render(context.world, context.state)
    camera = context.world.geometry.camera
    png = encode_rgba_png(camera.width, camera.height, result.rgba)
    return PersistentSceneFrame(
        camera.width,
        camera.height,
        result.rgba,
        result.composite_digest,
        png,
        hashlib.sha256(png).hexdigest(),
        frozen_payload,
        digest(frozen_payload),
        context.world_id,
        context.admission_catalog_id,
        context.transition_intent_id,
    )


def unwritten_alpha_pixels(rgba: bytes) -> int:
    """Count composited pixels whose alpha was never written (exactly zero)."""

    if len(rgba) % 4:
        raise ValueError("RGBA frame byte length must be a multiple of four.")
    return rgba[3::4].count(0)


def compositor_contract() -> dict[str, Any]:
    return {
        "identity": COMPOSITOR_IDENTITY,
        "render_policy": RENDER_POLICY,
        "frame_encoding": FRAME_ENCODING,
        "schema_version": 1,
    }
