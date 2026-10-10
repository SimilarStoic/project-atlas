"""The opt-in alpha render policy, typed mask assets, soft-matte extraction and resampling."""

from __future__ import annotations

from hashlib import sha256

import pytest

from project_atlas.scene_model import (
    RENDER_POLICY,
    RENDER_POLICY_ALPHA,
    Affine,
    Camera,
    ContactShadow,
    DomainBindings,
    EntityDefinition,
    EntityVariant,
    GeometryContract,
    Operation,
    PersistenceClass,
    PersistentWorld,
    Plane,
    RasterAsset,
    RasterMask,
    RenderSlice,
    SceneModelError,
    TransitionIntent,
    base_state,
    bind_world_definition,
    build_fixture_states,
    build_fixture_world,
    digest,
    render,
    resolve,
    snapshot_payload,
    validate_world,
    world_definition_digest,
)
from project_atlas.scene_raster import DOWNSCALE_ADAPTER, downscale_premultiplied_area
from project_atlas.static_character import (
    _decode_rgba_png,
    _encode_rgba_png,
    extract_soft_matte_character,
    verify_soft_matte_extraction,
)
from tests.test_scene_persistence import (
    AUTHORITY,
    CHARACTER,
    PLAN,
    REFERENCE,
    SCENES,
    SPECS,
    STYLE,
    WORLD_ID,
    _prepared,
)

ROOM_RGB = (200, 190, 180)
W, H = 8, 6

# Digests recorded from the legacy renderer before the alpha policy existed.
LEGACY_FIXTURE = {
    "world": "37a65ebf243995aa63f4bf3c157cd58babbbac172ca33d694e463eff778dd751",
    "state-base": (
        "04663ffe73f886dc4d7123533b56ec4289dde84e2eb2a408ced16f2c4eac64ff",
        "a178aa991374381b4c81c80de1cbdb91ee10f183f529359f4816e56394ab3dc1",
        "6c63457dc5e019e85b2a9944a097126588657961344e51652df8ffe5e28383e7",
    ),
    "state-1": (
        "feba62386528f52e15fc7e57ef29d008d3bcaf62dc4f79201878038a6e50e3e3",
        "ea6da9f034236ed2ef5b214b74dd4b17aa6bec964e5472b82138004c70a1d96f",
        "720c6112c31e4354d65b653ade80cf492d7192f2292f5048231e9982a0666726",
    ),
    "state-2": (
        "dd2363c33cbe14449cf491e3338621555feda93e6127b219f59af4185e6de5a1",
        "115a2c27ed1563e9566520bd28e8f4f3ab746170f2fe0e43bf4229c5be42f7d7",
        "c5e7753c624071ccd87a28062a44ae7b33d1c1346162ef88c3345a9851669616",
    ),
    "state-3": (
        "39ecbec55c64b82118805e66e51f7d21537f2317d77d105667f0642e783a6612",
        "9022602c82bbb5999fc2c6d163e979364bc246ed041123a0c25a5d065e96a103",
        "35c463176b15b573609c73b8bffc006bc018d4d3c7cae4db97fde2c1dac74973",
    ),
}


def test_legacy_worlds_render_byte_identically() -> None:
    world = build_fixture_world()
    assert world.render_policy == RENDER_POLICY
    assert world_definition_digest(world) == LEGACY_FIXTURE["world"]
    for state in build_fixture_states(world):
        expected = LEGACY_FIXTURE[state.state_id]
        assert (
            state.state_digest,
            digest(snapshot_payload(world, state)),
            render(world, state).composite_digest,
        ) == expected


ROOM = RasterAsset.create("asset-alpha-room", W, H, bytes((*ROOM_RGB, 255)) * (W * H))
# Opaque black, half-transparent red, fully transparent (colour ignored), opaque blue.
ACTOR = RasterAsset.create(
    "asset-alpha-actor",
    2,
    2,
    bytes((0, 0, 0, 255, 255, 0, 0, 128, 10, 20, 30, 0, 0, 0, 255, 255)),
)
PROP = RasterAsset.create("asset-alpha-prop", 1, 1, bytes((0, 200, 0, 255)))
# The occluder covers column 6 only, cut from the same room raster.
DESK_MASK = RasterMask.create(
    "asset-alpha-desk-mask", W, H, bytes(255 if x == 6 else 0 for _ in range(H) for x in range(W))
)
SHADOW = ContactShadow("feet", 1.5, 0.75, 0.75, (40, 30, 20), 160)
PROP_SHADOW = ContactShadow("base", 1.5, 0.75, 0.75, (40, 30, 20), 160)


def _alpha_world(policy: str = RENDER_POLICY_ALPHA, actor_shadow=None) -> PersistentWorld:
    variants = (
        EntityVariant(
            "room-v1", "room", (W, H), "frame", (RenderSlice("room.main", ROOM.asset_id, None),)
        ),
        EntityVariant(
            "actor-v1",
            "actor",
            (2, 2),
            "hamster",
            (RenderSlice("actor.main", ACTOR.asset_id, None, Affine(), ("room.main",)),),
            anchors=(("feet", (1.0, 2.0)),),
            character_authority_id=CHARACTER,
            contact_shadow=actor_shadow,
        ),
        EntityVariant(
            "prop-v1",
            "prop",
            (1, 1),
            "prop",
            (RenderSlice("prop.main", PROP.asset_id, None, Affine(), ("room.main", "actor.main")),),
            anchors=(("base", (0.5, 1.0)),),
            contact_shadow=PROP_SHADOW if policy == RENDER_POLICY_ALPHA else None,
        ),
        EntityVariant(
            "desk-v1",
            "desk",
            (W, H),
            "frame",
            (
                RenderSlice(
                    "desk.main",
                    ROOM.asset_id,
                    DESK_MASK.mask_id,
                    Affine(),
                    ("room.main", "actor.main", "prop.main"),
                ),
            ),
        ),
    )
    entities = (
        EntityDefinition(
            "room",
            "background",
            PersistenceClass.LOCKED_STATIC,
            "main",
            "room-v1",
            Affine(),
            approved_variants=("room-v1",),
            purpose="location",
        ),
        EntityDefinition(
            "actor",
            "actor",
            PersistenceClass.ACTOR,
            "main",
            "actor-v1",
            Affine.translate(5, 2),
            approved_variants=("actor-v1",),
            purpose="action",
            depth=2,
        ),
        EntityDefinition(
            "prop",
            "prop",
            PersistenceClass.MOVABLE_PROP,
            "main",
            "prop-v1",
            Affine.translate(1, 4),
            approved_variants=("prop-v1",),
            purpose="action",
            depth=2,
        ),
        EntityDefinition(
            "desk",
            "table",
            PersistenceClass.LOCKED_STATIC,
            "main",
            "desk-v1",
            Affine(),
            approved_variants=("desk-v1",),
            purpose="occlusion",
            depth=3,
        ),
    )
    return bind_world_definition(
        PersistentWorld(
            "alpha-proof-world",
            1,
            GeometryContract("WU", 6, (Plane("main", Affine()),), Camera("cam", W, H, Affine())),
            entities,
            variants,
            (ACTOR, PROP, ROOM),
            (DESK_MASK,),
            STYLE,
            "palette",
            "wall",
            "light",
            DomainBindings(PLAN, SCENES, SPECS[:1], CHARACTER, REFERENCE, AUTHORITY, STYLE),
            "",
            policy,
        )
    )


def _pixel(rgba: bytes, x: int, y: int) -> tuple[int, ...]:
    offset = (y * W + x) * 4
    return tuple(rgba[offset : offset + 4])


def test_premultiplied_over_is_exact_and_occluders_keep_room_bytes() -> None:
    world = _alpha_world()
    result = render(world, base_state(world))
    # Actor at (5, 2): opaque black, then 128-alpha red over the room, transparent skipped.
    assert _pixel(result.rgba, 5, 2) == (0, 0, 0, 255)
    red = (
        (255 * 128 + 127) // 255 + (ROOM_RGB[0] * 127 + 127) // 255,
        (ROOM_RGB[1] * 127 + 127) // 255,
        (ROOM_RGB[2] * 127 + 127) // 255,
        255,
    )
    assert _pixel(result.rgba, 6, 2) != red  # the desk occluder covers column 6
    assert _pixel(result.rgba, 6, 2) == (*ROOM_RGB, 255)
    assert result.owner_map[2 * W + 6] == "desk"
    assert _pixel(result.rgba, 5, 3) == (*ROOM_RGB, 255)
    assert result.owner_map[3 * W + 5] == "room"
    # Move the actor one pixel left: the half-transparent red now lands on open room.
    moved = resolve(
        world,
        base_state(world),
        TransitionIntent(
            "move",
            base_state(world).state_digest,
            SCENES[1],
            (Operation("set_transform", "actor", Affine.translate(4, 2)),),
        ),
        "moved",
    )
    assert _pixel(render(world, moved).rgba, 5, 2) == red
    # Every pixel the occluder owns is the room raster's exact pixel.
    for index, owner in enumerate(render(world, moved).owner_map):
        if owner == "desk":
            assert render(world, moved).rgba[index * 4 : index * 4 + 4] == bytes((*ROOM_RGB, 255))


def test_contact_shadow_is_drawn_on_the_floor_and_not_for_held_objects() -> None:
    world = _alpha_world()
    base = base_state(world)
    owners = render(world, base).owner_map
    assert "prop.shadow" in owners
    held = resolve(
        world,
        base,
        TransitionIntent(
            "hold",
            base.state_digest,
            SCENES[1],
            (Operation("attach", "prop", ("actor", Affine.translate(1, 0))),),
            ("prop",),
        ),
        "held",
    )
    assert "prop.shadow" not in render(world, held).owner_map
    shaded = render(world, base).rgba
    shadow_pixel = owners.index("prop.shadow")
    assert shaded[shadow_pixel * 4 : shadow_pixel * 4 + 3] != bytes(ROOM_RGB)


def test_alpha_policy_places_layers_one_to_one_at_integer_pixels() -> None:
    world = _alpha_world()
    base = base_state(world)
    off_grid = resolve(
        world,
        base,
        TransitionIntent(
            "nudge",
            base.state_digest,
            SCENES[1],
            (Operation("set_transform", "actor", Affine.translate(4.5, 2)),),
        ),
        "nudged",
    )
    with pytest.raises(SceneModelError, match="integer pixels"):
        render(world, off_grid)


def test_contact_shadows_and_unknown_policies_are_refused_for_legacy_worlds() -> None:
    legacy = _alpha_world(RENDER_POLICY, actor_shadow=SHADOW)
    with pytest.raises(SceneModelError, match="alpha render policy"):
        validate_world(legacy)
    with pytest.raises(SceneModelError, match="unknown render policy"):
        validate_world(_alpha_world("scene-made-up-v9"))


def _source_image(repo) -> str:
    """One managed PNG in the plan that the typed derived scene assets descend from."""

    png = _encode_rgba_png(2, 2, bytes((*ROOM_RGB, 255)) * 4)
    path = repo.asset_storage_root / "alpha" / "source.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)
    version = repo.connection.execute(
        "SELECT COALESCE(MAX(version), 0) + 1 FROM assets WHERE asset_spec_id=?", (SPECS[0],)
    ).fetchone()[0]
    repo.create_asset(
        "asset-alpha-source",
        SPECS[0],
        version,
        "alpha/source.png",
        "image/png",
        "imported",
        content_digest=sha256(png).hexdigest(),
    )
    return "asset-alpha-source"


def _store_world_assets(repo) -> None:
    source = _source_image(repo)
    for raster in (ROOM, ACTOR, PROP):
        repo.create_derived_scene_asset(
            raster.asset_id,
            source,
            "application/x-rgba",
            raster.rgba,
            raster.width,
            raster.height,
            DOWNSCALE_ADAPTER,
        )
    repo.create_derived_scene_asset(
        DESK_MASK.mask_id,
        source,
        "application/x-alpha8",
        DESK_MASK.alpha,
        W,
        H,
        "plate-occluder-mask-v1",
    )


def test_alpha_world_persists_reloads_and_renders_identically(tmp_path) -> None:
    repo, legacy_world, _legacy_base, _versions = _prepared(tmp_path)
    try:
        _store_world_assets(repo)
        world = _alpha_world(actor_shadow=SHADOW)
        base = base_state(world, SCENES[0], "alpha-state-base")
        repo.create_persistent_scene_world(
            "alpha-world",
            world,
            base,
            base_intent_id="alpha-intent",
            base_catalog_id="alpha-cat",
            authorization_actor="test",
            authorization_reference="alpha policy test",
        )
        loaded = repo.get_persistent_scene_world("alpha-world")
        assert loaded.render_policy == RENDER_POLICY_ALPHA
        assert loaded.definition_digest == world.definition_digest
        assert loaded.variant("actor-v1").contact_shadow == SHADOW
        state = repo.get_persistent_scene_state("alpha-state-base")
        assert render(loaded, state).rgba == render(world, base).rgba
        treatments = dict(
            repo.connection.execute(
                "SELECT id, treatment_json FROM persistent_scene_world_revisions"
            ).fetchall()
        )
        assert '"render_policy"' in treatments["alpha-world"]
        assert '"render_policy"' not in treatments[WORLD_ID]
        reloaded_legacy = repo.get_persistent_scene_world(WORLD_ID)
        assert reloaded_legacy.render_policy == RENDER_POLICY
        assert reloaded_legacy.definition_digest == legacy_world.definition_digest
    finally:
        repo.close()


def test_mask_assets_are_typed_and_length_checked(tmp_path) -> None:
    repo, *_ = _prepared(tmp_path)
    try:
        source = _source_image(repo)
        with pytest.raises(ValueError, match="dimensions"):
            repo.create_derived_scene_asset(
                "asset-short-mask",
                source,
                "application/x-alpha8",
                b"\xff" * 5,
                W,
                H,
                "plate-occluder-mask-v1",
            )
        with pytest.raises(ValueError, match="not registered"):
            repo.create_derived_scene_asset(
                "asset-wrong-adapter",
                source,
                "application/x-alpha8",
                DESK_MASK.alpha,
                W,
                H,
                DOWNSCALE_ADAPTER,
            )
        mask = repo.create_derived_scene_asset(
            "asset-good-mask",
            source,
            "application/x-alpha8",
            DESK_MASK.alpha,
            W,
            H,
            "plate-occluder-mask-v1",
        )
        assert mask.media_type == "application/x-alpha8"
        path = repo.managed_scene_asset_path(mask.id)
        assert path.read_bytes() == DESK_MASK.alpha
        path.write_bytes(DESK_MASK.alpha[:-1])
        with pytest.raises(ValueError, match="declared dimensions"):
            repo.managed_scene_asset_path(mask.id)
    finally:
        repo.close()


def _synthetic_drawing() -> bytes:
    """Paper, a dark ring with an anti-aliased grey outer edge, a white interior and a speck."""

    size, paper = 40, (250, 248, 240)
    pixels = bytearray()
    for y in range(size):
        for x in range(size):
            radius = ((x - 20) ** 2 + (y - 20) ** 2) ** 0.5
            if (x, y) == (2, 2):
                rgb = (30, 30, 30)
            elif radius < 9:
                rgb = (255, 255, 255)
            elif radius < 11:
                rgb = (20, 20, 20)
            elif radius < 12:
                rgb = (140, 140, 140)
            else:
                rgb = paper
            pixels.extend((*rgb, 255))
    return _encode_rgba_png(size, size, bytes(pixels))


def test_soft_matte_extraction_is_reproducible_with_no_residue_or_fringe() -> None:
    source = _synthetic_drawing()
    extraction = extract_soft_matte_character(source)
    verify_soft_matte_extraction(source, extraction)
    assert extract_soft_matte_character(source) == extraction
    width, _height, pixels = _decode_rgba_png(extraction.content)

    def at(x, y):
        offset = (y * width + x) * 4
        return tuple(pixels[offset : offset + 4])

    assert at(2, 2) == (0, 0, 0, 0)  # the stray speck is dropped
    assert extraction.dropped_components == 1
    assert at(20, 20) == (255, 255, 255, 255)  # the interior keeps its exact pixels
    assert at(0, 39) == (0, 0, 0, 0)  # paper is transparent with no colour residue
    grey = at(20, 31)  # the anti-aliased edge: partial alpha, colour unblended toward the ink
    assert 0 < grey[3] < 255 and max(grey[:3]) < 140
    assert extraction.partial_alpha_pixels > 0


def test_downscale_is_deterministic_premultiplied_and_never_upscales() -> None:
    rgba = bytes((255, 0, 0, 255)) + bytes(12)
    once = downscale_premultiplied_area(rgba, 2, 2, 1, 1)
    assert once == downscale_premultiplied_area(rgba, 2, 2, 1, 1)
    assert once == bytes((255, 0, 0, 64))  # colour stays red: transparent pixels add no fringe
    with pytest.raises(ValueError, match="only downscales"):
        downscale_premultiplied_area(rgba, 2, 2, 3, 3)
