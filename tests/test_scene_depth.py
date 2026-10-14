"""The opt-in depth render policy: frozen floor-depth rule, supports, held props, occlusion."""

from __future__ import annotations

from dataclasses import replace

import pytest

from project_atlas.scene_model import (
    RENDER_POLICY_ALPHA,
    RENDER_POLICY_DEPTH,
    Affine,
    Camera,
    DepthDerivative,
    DepthKnot,
    DirectionalContactShadow,
    DomainBindings,
    EntityDefinition,
    EntityVariant,
    FloorDepthRule,
    GeometryContract,
    OccluderDepth,
    Operation,
    PersistenceClass,
    PersistentWorld,
    Plane,
    RasterAsset,
    RasterMask,
    RenderSlice,
    SceneModelError,
    SupportSurface,
    TransitionIntent,
    base_state,
    bind_world_definition,
    depth_placements,
    digest,
    render,
    resolve,
    snapshot_payload,
    validate_world,
)
from project_atlas.scene_raster import DOWNSCALE_ADAPTER
from tests.test_scene_alpha import SHADOW, _alpha_world, _source_image
from tests.test_scene_persistence import (
    AUTHORITY,
    CHARACTER,
    PLAN,
    REFERENCE,
    SCENES,
    SPECS,
    STYLE,
    _prepared,
)

N = 40
ROOM_RGB = (200, 190, 180)
SOURCE_SHA = "a" * 64
RULE = FloorDepthRule(
    (
        DepthKnot(10, 0.5, "assumed: far wall"),
        DepthKnot(30, 1.0, "measured: front reference"),
    )
)
ROOM = RasterAsset.create("asset-depth-room", N, N, bytes((*ROOM_RGB, 255)) * (N * N))
DESK_MASK = RasterMask.create(
    "asset-depth-desk-mask",
    N,
    N,
    bytes(255 if 10 <= x <= 20 and 15 <= y <= 29 else 0 for y in range(N) for x in range(N)),
)
SHADOW_2B = DirectionalContactShadow("feet", 6.0, 2.0, 1.0, -6.0, -0.5, (60, 50, 40), 200)


def _solid(asset_id: str, size: int, rgb: tuple[int, int, int]) -> RasterAsset:
    return RasterAsset.create(asset_id, size, size, bytes((*rgb, 255)) * (size * size))


ACTOR_RASTERS = {
    scale: _solid(f"asset-depth-actor-{size}", size, (0, 0, 0))
    for scale, size in ((1.0, 8), (0.875, 7), (0.75, 6))
}
PROP_RASTERS = {scale: _solid(f"asset-depth-prop-{scale}", 2, (0, 0, 255)) for scale in (1.0, 0.75)}


def _actor_variant(scale: float, shadow=SHADOW_2B) -> EntityVariant:
    raster = ACTOR_RASTERS[scale]
    return EntityVariant(
        f"actor-k{scale}",
        "actor",
        (8, 8),
        "hamster",
        (RenderSlice(f"actor.k{scale}", raster.asset_id, None, Affine(), ("room.main",)),),
        anchors=(("feet", (4.0, 8.0)),),
        character_authority_id=CHARACTER,
        contact_shadow=shadow,
        depth_derivative=DepthDerivative("asset-source", SOURCE_SHA, scale, "feet"),
    )


def _prop_variant(scale: float) -> EntityVariant:
    raster = PROP_RASTERS[scale]
    return EntityVariant(
        f"prop-k{scale}",
        "prop",
        (2, 2),
        "prop",
        (RenderSlice(f"prop.k{scale}", raster.asset_id, None, Affine(), ("room.main",)),),
        anchors=(("grip", (1.0, 1.0)),),
        depth_derivative=DepthDerivative("asset-prop-source", SOURCE_SHA, scale, "grip"),
    )


def _world(policy: str = RENDER_POLICY_DEPTH, rule=RULE, actor_initial=(15, 30)) -> PersistentWorld:
    actor_variants = tuple(_actor_variant(scale) for scale in ACTOR_RASTERS)
    prop_variants = tuple(_prop_variant(scale) for scale in PROP_RASTERS)
    desk = EntityVariant(
        "desk-v1",
        "desk",
        (N, N),
        "frame",
        (RenderSlice("desk.main", ROOM.asset_id, DESK_MASK.mask_id, Affine(), ("room.main",)),),
        support=SupportSurface("desk", 25),
        occluder=OccluderDepth("desk", ((10, 25), (20, 25))),
    )
    variants = (
        EntityVariant(
            "room-v1", "room", (N, N), "frame", (RenderSlice("room.main", ROOM.asset_id, None),)
        ),
        desk,
        *actor_variants,
        *prop_variants,
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
            "desk",
            "table",
            PersistenceClass.LOCKED_STATIC,
            "main",
            "desk-v1",
            Affine(),
            approved_variants=("desk-v1",),
            purpose="occlusion and support",
        ),
        EntityDefinition(
            "actor",
            "actor",
            PersistenceClass.ACTOR,
            "main",
            "actor-k1.0",
            Affine.translate(*actor_initial),
            approved_variants=tuple(item.variant_id for item in actor_variants),
            purpose="action",
        ),
        EntityDefinition(
            "prop",
            "prop",
            PersistenceClass.MOVABLE_PROP,
            "main",
            "prop-k1.0",
            Affine.translate(30, 30),
            approved_variants=tuple(item.variant_id for item in prop_variants),
            purpose="held object",
        ),
    )
    return bind_world_definition(
        PersistentWorld(
            "depth-proof-world",
            1,
            GeometryContract("WU", 6, (Plane("main", Affine()),), Camera("cam", N, N, Affine())),
            entities,
            variants,
            (ROOM, *ACTOR_RASTERS.values(), *PROP_RASTERS.values()),
            (DESK_MASK,),
            STYLE,
            "palette",
            "wall",
            "light",
            DomainBindings(PLAN, SCENES, SPECS[:1], CHARACTER, REFERENCE, AUTHORITY, STYLE),
            "",
            policy,
            rule if policy == RENDER_POLICY_DEPTH else None,
        )
    )


def _move(world, state, operations, name, derived=()):
    intent = TransitionIntent(
        name, state.state_digest, SCENES[1], tuple(operations), tuple(derived)
    )
    return resolve(world, state, intent, name)


def _owner(result, x, y):
    return result.owner_map[y * N + x]


def test_rule_interpolates_and_refuses_placements_outside_its_range() -> None:
    assert RULE.scale_at(10) == 0.5 and RULE.scale_at(30) == 1.0 and RULE.scale_at(20) == 0.75
    for outside in (9.99, 30.01):
        with pytest.raises(SceneModelError, match="outside the accepted depth range"):
            RULE.scale_at(outside)
    with pytest.raises(SceneModelError, match="increasing floor_y"):
        FloorDepthRule((DepthKnot(30, 1, "x"), DepthKnot(10, 0.5, "y")))
    with pytest.raises(SceneModelError, match="basis"):
        DepthKnot(10, 0.5, " ")


def test_apparent_size_comes_only_from_the_frozen_rule() -> None:
    world = _world()
    base = base_state(world)
    placement = depth_placements(world, base)["actor"]
    assert (placement.scale, placement.offset, placement.support) == (1.0, (11, 22), "floor")
    # Moving back without the matching derivative is refused; with it, it is accepted.
    with pytest.raises(SceneModelError, match="requires 0.75"):
        _move(world, base, [Operation("set_transform", "actor", Affine.translate(15, 20))], "bad")
    back = _move(
        world,
        base,
        [
            Operation("set_transform", "actor", Affine.translate(15, 20)),
            Operation("set_variant", "actor", "actor-k0.75"),
        ],
        "back",
    )
    assert depth_placements(world, back)["actor"].offset == (12, 14)
    with pytest.raises(SceneModelError, match="outside the accepted depth range"):
        _move(world, base, [Operation("set_transform", "actor", Affine.translate(15, 35))], "out")
    # The legacy guard still forbids scaling an actor through its transform.
    with pytest.raises(SceneModelError, match="scale cannot be used"):
        _move(
            world,
            base,
            [Operation("set_transform", "actor", Affine(a=0.75, d=0.75, e=15, f=20))],
            "s",
        )


def test_occlusion_depends_on_position_and_keeps_room_pixels() -> None:
    world = _world()
    front = base_state(world)  # floor y 30, nearer than the desk line at y 25
    behind = _move(
        world,
        front,
        [
            Operation("set_transform", "actor", Affine.translate(15, 20)),
            Operation("set_variant", "actor", "actor-k0.75"),
        ],
        "behind",
    )
    in_front = render(world, front)
    occluded = render(world, behind)
    assert _owner(in_front, 15, 25) == "actor"  # the actor covers the desk piece
    assert _owner(occluded, 14, 17) == "desk"  # the desk piece covers the actor
    for result in (in_front, occluded):
        for index, owner in enumerate(result.owner_map):
            if owner in ("desk", "room"):
                assert result.rgba[index * 4 : index * 4 + 4] == bytes((*ROOM_RGB, 255))


def test_standing_on_a_support_takes_its_scale_and_is_never_covered_by_it() -> None:
    world = _world()
    on_desk = _move(
        world,
        base_state(world),
        [
            Operation("attach", "actor", ("desk", Affine.translate(15, 16))),
            Operation("set_variant", "actor", "actor-k0.875"),
        ],
        "on-desk",
    )
    placement = depth_placements(world, on_desk)["actor"]
    assert (placement.scale, placement.support, placement.floor_y) == (0.875, "support:desk", 25)
    result = render(world, on_desk)
    assert _owner(result, 14, 15) == "actor"  # inside the desk piece, yet drawn over it
    assert "actor.shadow" not in result.owner_map  # no floor shadow while supported


def test_held_props_follow_the_parent_placement_and_scale_without_a_shadow() -> None:
    world = _world()
    base = base_state(world)
    held = _move(
        world,
        base,
        [
            Operation("set_transform", "actor", Affine.translate(15, 20)),
            Operation("set_variant", "actor", "actor-k0.75"),
            Operation("attach", "prop", ("actor", Affine.translate(2, -4))),
            Operation("set_variant", "prop", "prop-k0.75"),
        ],
        "held",
    )
    prop = depth_placements(world, held)["prop"]
    assert prop.contact == (16.5, 17.0) and prop.scale == 0.75 and prop.support == "held:actor"
    result = render(world, held)
    assert "prop.shadow" not in result.owner_map and "actor.shadow" in result.owner_map
    with pytest.raises(SceneModelError, match="requires 0.75"):
        _move(
            world,
            base,
            [
                Operation("set_transform", "actor", Affine.translate(15, 20)),
                Operation("set_variant", "actor", "actor-k0.75"),
                Operation("attach", "prop", ("actor", Affine.translate(2, -4))),
            ],
            "mismatched",
        )


def test_directional_shadow_is_offset_and_scaled_with_apparent_size() -> None:
    world = _world()
    result = render(world, base_state(world))
    shadow = [i for i, owner in enumerate(result.owner_map) if owner == "actor.shadow"]
    xs, ys = [i % N for i in shadow], [i // N for i in shadow]
    # Contact (15, 30) plus offset (-6, -0.5) at scale 1: centred left of and behind the feet.
    assert min(xs) < 9 < max(xs) and max(ys) <= 31


def test_depth_fields_are_refused_outside_the_depth_policy() -> None:
    with pytest.raises(SceneModelError, match="belongs to, and is required by"):
        validate_world(replace(_world(), depth_rule=None))
    with pytest.raises(SceneModelError, match="require the depth render policy"):
        validate_world(_world(policy=RENDER_POLICY_ALPHA))
    alpha_with_directional = _alpha_world(actor_shadow=SHADOW_2B)
    with pytest.raises(SceneModelError, match="does not match the render policy"):
        validate_world(alpha_with_directional)


# Round 2A alpha-world digests recorded before the depth policy existed.
ALPHA_PINNED = (
    "5f914613d9797ba5ec5100d5ccbef4af8a2c1d4766626ece185e6bb58039bd68",
    "9cf3ab23fc00c06355d98e9006df63801f955227217618474516799d1b89246a",
    "95af7c314e5414b1df1147743944ae4ef5112ebb106c049ea3c51ba1f286d858",
    "84e10322e750d7b56e02df0130d7b9307740dc27aeca63981d4ec17b46e58b22",
)


def test_alpha_worlds_keep_their_identity_and_bytes() -> None:
    world = _alpha_world(actor_shadow=SHADOW)
    state = base_state(world)
    assert (
        world.definition_digest,
        state.state_digest,
        digest(snapshot_payload(world, state)),
        render(world, state).composite_digest,
    ) == ALPHA_PINNED


def test_depth_world_persists_reloads_and_renders_identically(tmp_path) -> None:
    repo, *_ = _prepared(tmp_path)
    try:
        source = _source_image(repo)
        for raster in (ROOM, *ACTOR_RASTERS.values(), *PROP_RASTERS.values()):
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
            N,
            N,
            "plate-occluder-mask-v1",
        )
        world = _world()
        base = base_state(world, SCENES[0], "depth-base")
        repo.create_persistent_scene_world(
            "depth-world",
            world,
            base,
            base_intent_id="depth-intent",
            base_catalog_id="depth-cat",
            authorization_actor="test",
            authorization_reference="depth policy test",
        )
        moved = repo.resolve_and_persist_scene_state(
            "depth-world",
            "depth-base",
            TransitionIntent(
                "depth-move",
                base.state_digest,
                SCENES[1],
                (
                    Operation("set_transform", "actor", Affine.translate(15, 20)),
                    Operation("set_variant", "actor", "actor-k0.75"),
                ),
            ),
            "depth-moved",
            authorization_actor="test",
            authorization_reference="depth move",
        )
        loaded = repo.get_persistent_scene_world("depth-world")
        assert loaded.render_policy == RENDER_POLICY_DEPTH and loaded.depth_rule == RULE
        assert loaded.definition_digest == world.definition_digest
        assert loaded.variant("desk-v1").occluder == world.variant("desk-v1").occluder
        assert loaded.variant("actor-k0.75").contact_shadow == SHADOW_2B
        reloaded_state = repo.get_persistent_scene_state("depth-moved")
        assert render(loaded, reloaded_state).rgba == render(world, moved).rgba
        treatment = repo.connection.execute(
            "SELECT treatment_json FROM persistent_scene_world_revisions WHERE id='depth-world'"
        ).fetchone()[0]
        assert '"depth_rule"' in treatment and '"measured: front reference"' in treatment
    finally:
        repo.close()
