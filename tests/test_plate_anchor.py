"""Plate-anchored acquisition: the approved room plate is the immutable output canvas."""

from __future__ import annotations

from hashlib import sha256

import pytest

from project_atlas import plate_anchor as anchoring
from project_atlas.generation import (
    DEFAULT_GLOBAL_VISUAL_AUTHORITY_ID,
    GeneratedArtifact,
    GenerationService,
    LocalAssetStorage,
    OpenAIImageGenerator,
)
from project_atlas.persistence import AtlasRepository
from tests.reference_approvals import approve_reference_images
from tests.test_persistence import ensure_character_reference_set

SCENE = "scene-isa-deadline-video-v1-01"
PROFILE = "character-profile-similarstoic-hamster-core-v1"
DESK = "visual-reference-authority-anchor-desk-v1"
REGION = {"x": 8, "y": 20, "width": 20, "height": 30}
PLATE_SIZE = (40, 64)


def _plate_raster() -> anchoring.Raster:
    width, height = PLATE_SIZE
    pixels = bytes(
        value
        for y in range(height)
        for x in range(width)
        for value in ((x * 6) % 256, (y * 4) % 256, (x * y) % 256)
    )
    return anchoring.Raster(width, height, 3, pixels)


def _solid_png(width: int, height: int, colour: tuple[int, int, int]) -> bytes:
    return anchoring.encode_png(anchoring.Raster(width, height, 3, bytes(colour) * width * height))


class ProviderOutput:
    """A fake provider whose output differs in size from the plate."""

    generator_key = "fake-anchor"
    max_reference_images = 16

    def __init__(self, content: bytes | None = None) -> None:
        self.content = content or _solid_png(80, 128, (200, 10, 10))
        self.inputs = []

    def supports(self, asset_type: str) -> bool:
        return True

    def generate(self, generation_input):
        self.inputs.append(generation_input)
        return GeneratedArtifact(self.content, "image/png", provider_key="offline-fake")


def _import(repository, root, key: str, content: bytes) -> str:
    spec = repository.create_asset_spec(
        f"asset-spec-anchor-{key}", SCENE, "environment", "Anchor test.", "Anchor test.", "Import."
    )
    storage = LocalAssetStorage(root)
    asset_id = f"asset-anchor-{key}"
    stored = storage.write(spec.id, asset_id, content, "image/png")
    repository.create_asset(
        asset_id,
        spec.id,
        1,
        storage.relative_path(stored),
        "image/png",
        "imported",
        content_digest=sha256(content).hexdigest(),
    )
    approve_reference_images(repository, asset_id)
    return asset_id


@pytest.fixture
def world(tmp_path):
    root = tmp_path / "assets"
    repository = AtlasRepository(tmp_path / "anchor.db", root)
    ensure_character_reference_set(repository, root, PROFILE)
    style = _import(repository, root, "style", _solid_png(4, 4, (250, 248, 240)))
    repository.create_visual_reference_authority(
        DEFAULT_GLOBAL_VISUAL_AUTHORITY_ID,
        "anchor-global",
        "global_illustration_style",
        "Global",
        "Global illustration guidance.",
        [(style, "style")],
    )
    plate_bytes = anchoring.encode_png(_plate_raster())
    plate = _import(repository, root, "desk-plate", plate_bytes)
    repository.create_visual_reference_authority(
        DESK,
        "anchor-desk",
        "environment_family",
        "Desk",
        "Environment identity reference.",
        [(plate, "viewpoint:front")],
        parent_authority_id=DEFAULT_GLOBAL_VISUAL_AUTHORITY_ID,
        metadata={
            "environment_family": "anchor-desk",
            "fixtures": [{"key": "desk", "identity": "small wooden desk"}],
        },
    )
    yield repository, root, plate, plate_bytes
    repository.close()


def _spec(repository, key: str, anchored: bool = True) -> str:
    metadata = (
        {
            "plate_anchor": {
                "authority_id": DESK,
                "viewpoint": "front",
                "action_region": REGION,
                "feather_px": 2,
            }
        }
        if anchored
        else {"environment_family": "anchor-desk", "environment_viewpoint": "front"}
    )
    return repository.create_asset_spec(
        f"asset-spec-anchor-beat-{key}",
        SCENE,
        "character",
        "Calibration beat.",
        "Calibration beat.",
        "The hamster drops a coin into a jar.",
        "anchor-test",
        PROFILE,
        metadata,
    ).id


def test_the_plate_is_sent_first_with_a_plate_sized_mask(world) -> None:
    repository, root, plate, plate_bytes = world
    generator = ProviderOutput()
    GenerationService(repository, generator, LocalAssetStorage(root)).generate_asset_spec(
        _spec(repository, "first")
    )
    [sent] = generator.inputs
    assert sent.reference_images[0].asset_id == plate
    assert sent.reference_images[0].content == plate_bytes
    assert [image.position for image in sent.reference_images] == list(
        range(1, len(sent.reference_images) + 1)
    )
    assert sum(image.asset_id == plate for image in sent.reference_images) == 1
    mask = anchoring.decode_png(sent.mask)
    assert (mask.width, mask.height, mask.channels) == (*PLATE_SIZE, 4)
    assert len(sent.mask) < anchoring.MAX_MASK_BYTES
    for y in range(mask.height):
        for x in range(mask.width):
            inside = REGION["x"] <= x < REGION["x"] + REGION["width"] and (
                REGION["y"] <= y < REGION["y"] + REGION["height"]
            )
            assert mask.pixels[(y * mask.width + x) * 4 + 3] == (0 if inside else 255)
    # The OpenAI transport sends the plate as the first image and the mask beside it.
    body, _ = OpenAIImageGenerator(api_key="test")._reference_edit_payload(sent)
    assert body.index(plate_bytes) < body.index(sent.reference_images[1].content)
    assert b'name="mask"; filename="mask.png"' in body and sent.mask in body


def test_no_pixel_outside_the_action_region_changes(world) -> None:
    repository, root, plate, plate_bytes = world
    result = GenerationService(
        repository, ProviderOutput(), LocalAssetStorage(root)
    ).generate_asset_spec(_spec(repository, "pixels"))
    stored = repository.managed_asset_path(result.asset.id).read_bytes()
    output = anchoring.decode_png(stored)
    plate_raster = anchoring.decode_png(plate_bytes)
    region = anchoring.action_region(REGION, *PLATE_SIZE)
    assert (output.width, output.height) == PLATE_SIZE
    assert anchoring.changed_pixels_outside(plate_raster, output, region) == 0
    centre = ((REGION["y"] + 15) * output.width + REGION["x"] + 10) * 3
    assert output.pixels[centre : centre + 3] == bytes((200, 10, 10))
    frozen = result.execution.generation_input["plate_anchor"]
    assert frozen["plate_sha256"] == sha256(plate_bytes).hexdigest()
    assert frozen["action_region"] == REGION and frozen["method"] == anchoring.METHOD
    assert frozen["plate_approval"]["basis"] == "founder_decision"
    composite = result.execution.response_metadata["plate_anchor_composite"]
    assert composite["resized_to_plate"] is True and composite["provider_output_size"] == [80, 128]
    assert composite["changed_pixels_outside_region"] == 0


def test_unanchored_specs_behave_exactly_as_before(world) -> None:
    repository, root, plate, _plate_bytes = world
    generator = ProviderOutput(b"provider bytes, stored untouched")
    result = GenerationService(repository, generator, LocalAssetStorage(root)).generate_asset_spec(
        _spec(repository, "plain", anchored=False)
    )
    [sent] = generator.inputs
    assert sent.mask is None and sent.plate_anchor is None
    assert "plate_anchor" not in result.execution.generation_input
    assert "PLATE_ANCHOR" not in sent.prompt and "Plate anchor:" not in sent.prompt
    assert "plate_anchor_composite" not in result.execution.response_metadata
    assert result.asset.content_digest == sha256(b"provider bytes, stored untouched").hexdigest()
    # Unpinned family resolution keeps its historical order: character references first.
    assert sent.reference_images[0].asset_id != plate
    body, _ = OpenAIImageGenerator(api_key="test")._reference_edit_payload(sent)
    assert b'name="mask"' not in body


@pytest.mark.parametrize("approval", ["withdrawn", "missing"])
def test_an_ineligible_plate_fails_closed_before_any_provider_call(
    world, monkeypatch, approval
) -> None:
    repository, root, plate, _plate_bytes = world
    spec_id = _spec(repository, approval)
    if approval == "withdrawn":
        repository.record_visual_plate_decision(
            "anchor-plate-withdrawn", plate, "withdrawn", "founder", "founder withdrew the plate"
        )
    else:
        original = repository.list_plate_approvals
        monkeypatch.setattr(
            repository,
            "list_plate_approvals",
            lambda asset_id=None: [] if asset_id == plate else original(asset_id),
        )
    generator = ProviderOutput()
    with pytest.raises(ValueError, match="without an eligible founder approval"):
        GenerationService(repository, generator, LocalAssetStorage(root)).generate_asset_spec(
            spec_id
        )
    assert generator.inputs == []
    assert repository.list_generation_executions_for_asset_spec(spec_id) == []


def test_anchor_selection_and_region_are_validated_before_any_provider_call(world) -> None:
    repository, root, _plate, _plate_bytes = world
    generator = ProviderOutput()
    service = GenerationService(repository, generator, LocalAssetStorage(root))
    for index, (anchor, match) in enumerate(
        (
            ({"authority_id": DESK, "viewpoint": "side", "action_region": REGION}, "exactly one"),
            (
                {"authority_id": DESK, "viewpoint": "front", "action_region": REGION | {"x": 30}},
                "outside the plate",
            ),
            (
                {
                    "authority_id": DESK,
                    "viewpoint": "front",
                    "action_region": {"x": 0, "y": 0, "width": 40, "height": 64},
                },
                "whole plate",
            ),
            ({"authority_id": DESK, "viewpoint": "front"}, "requires"),
        )
    ):
        spec_id = repository.create_asset_spec(
            f"asset-spec-anchor-invalid-{index}",
            SCENE,
            "character",
            "Calibration beat.",
            "Calibration beat.",
            "The hamster.",
            "anchor-test",
            PROFILE,
            {"plate_anchor": anchor},
        ).id
        with pytest.raises(ValueError, match=match):
            service.generate_asset_spec(spec_id)
    assert generator.inputs == []


def test_composite_feathers_only_inside_the_region() -> None:
    plate = _plate_raster()
    region = anchoring.action_region(REGION, *PLATE_SIZE)
    generated = anchoring.Raster(*PLATE_SIZE, 3, bytes((0, 0, 0)) * PLATE_SIZE[0] * PLATE_SIZE[1])
    result = anchoring.composite(plate, generated, region, 4)
    assert anchoring.changed_pixels_outside(plate, result, region) == 0
    edge = (REGION["y"] * PLATE_SIZE[0] + REGION["x"] + 10) * 3
    assert result.pixels[edge : edge + 3] != plate.pixels[edge : edge + 3]
    assert result.pixels[edge : edge + 3] != bytes(3)
