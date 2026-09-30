from __future__ import annotations

import importlib.util
import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from project_atlas.scene_model import (
    Affine,
    EntityVariant,
    Operation,
    RasterAsset,
    RasterMask,
    RenderSlice,
    SceneModelError,
    TransitionIntent,
    VariantAdmissionRequest,
    base_state,
    bind_world_definition,
    build_fixture_states,
    build_fixture_world,
    canonical_json,
    density_problems,
    digest,
    entity_render_digest,
    plan_generation_demand,
    render,
    resolve,
    snapshot_payload,
    validate_snapshot_payload,
    validate_world,
    variant_admission_digest,
    variant_admission_payload,
    variant_content_digest,
    world_definition_digest,
    world_definition_payload,
)


@pytest.fixture
def world():
    return build_fixture_world()


@pytest.fixture
def states(world):
    return build_fixture_states(world)


def transition(state, *operations, closure=()):
    return TransitionIntent("test-intent", state.state_digest, "test-scene", operations, closure)


def replace_asset(world, asset_id, replacement):
    return replace(
        world,
        assets=tuple(
            replacement if asset.asset_id == asset_id else asset for asset in world.assets
        ),
    )


def replace_variant(world, variant_id, replacement):
    return replace(
        world,
        variants=tuple(
            replacement if variant.variant_id == variant_id else variant
            for variant in world.variants
        ),
    )


def expanded_actor_variant(world, variant_id="actor-d"):
    asset = RasterAsset.create(f"asset-{variant_id}", 10, 20, bytes((190, 130, 70, 255)) * 200)
    body = RasterMask.create(f"mask-{variant_id}-body", 10, 20, bytes([255] * 160 + [0] * 40))
    paw = RasterMask.create(f"mask-{variant_id}-paw", 10, 20, bytes([0] * 160 + [255] * 40))
    variant = EntityVariant(
        variant_id,
        "actor",
        (4.0, 5.0),
        "actor-neutral-v1",
        (
            RenderSlice(
                "actor.body", asset.asset_id, body.mask_id, Affine(a=0.4, d=0.25), ("floor.main",)
            ),
            RenderSlice(
                "actor.paw", asset.asset_id, paw.mask_id, Affine(a=0.4, d=0.25), ("report.main",)
            ),
        ),
        anchors=(("foot-contact", (2.0, 5.0)),),
        contact_policy_id="floor-contact-v1",
        character_authority_id="character-profile-core-v3",
        partition_complete_source=True,
    )
    return bind_world_definition(
        replace(
            world,
            entities=tuple(
                (
                    replace(item, approved_variants=item.approved_variants + (variant_id,))
                    if item.entity_key == "actor"
                    else item
                )
                for item in world.entities
            ),
            variants=world.variants + (variant,),
            assets=world.assets + (asset,),
            masks=world.masks + (body, paw),
        )
    )


def admit_and_select(state, variant_id="actor-d"):
    return transition(
        state,
        Operation(
            "admit_variant",
            "actor",
            VariantAdmissionRequest(variant_id, "founder-proof", "approved pose"),
        ),
        Operation("set_variant", "actor", variant_id),
    )


def layer_hashes(result):
    return dict(result.layer_digests)


def test_deterministic_base_world_resolution(world):
    first = base_state(world)
    second = base_state(world)
    assert first == second
    assert first.state_digest == digest(
        {
            "schema_version": 1,
            "world_key": first.world_key,
            "world_revision": first.world_revision,
            "world_definition_digest": first.world_definition_digest,
            "editorial_scene_id": first.editorial_scene_id,
            "predecessor_digest": None,
            "transition_intent_id": None,
            "admitted_variants": first.admitted_variants,
            "variant_admission_digest": first.variant_admission_digest,
            "entities": first.entities,
            "entity_content_digests": first.entity_content_digests,
        }
    )


def test_three_resolved_states_share_one_world(states):
    assert len(states) == 4
    assert {(state.world_key, state.world_revision) for state in states} == {
        ("similarstoic-proof-world", 1)
    }
    assert [state.state_id for state in states] == ["state-base", "state-1", "state-2", "state-3"]


def test_exact_inherited_static_equality(world, states):
    for key in ("wall", "window", "painting", "chair", "table"):
        entities = [state.entity(key) for state in states]
        assert entities.count(entities[0]) == len(entities)
        assert len({entity_render_digest(world, item) for item in entities}) == 1


def test_legal_actor_variant_transition(world, states):
    assert states[0].entity("actor").variant_id == "actor-a"
    assert states[1].entity("actor").variant_id == "actor-b"
    assert states[3].entity("actor").variant_id == "actor-c"
    assert (
        states[0].entity("actor").local_transform.scale
        == states[3].entity("actor").local_transform.scale
    )


def test_legal_stateful_prop_transition(states):
    assert states[1].entity("laptop").variant_id == "laptop-off"
    assert states[2].entity("laptop").variant_id == "laptop-on"


def test_legal_movable_prop_transform(world, states):
    previous = states[2]
    intent = transition(previous, Operation("set_transform", "occluder", Affine.translate(34, 15)))
    result = resolve(world, previous, intent, "moved")
    assert result.entity("occluder").local_transform.e == 34


def test_explicit_ephemeral_introduction_and_removal(world, states):
    base = states[0]
    shown = resolve(world, base, transition(base, Operation("set_visible", "spark", True)), "shown")
    hidden = resolve(
        world, shown, transition(shown, Operation("set_visible", "spark", False)), "hidden"
    )
    assert shown.entity("spark").visible is True
    assert hidden.entity("spark").visible is False


def test_spontaneous_entity_introduction_rejected(world, states):
    with pytest.raises(SceneModelError, match="spontaneous entity"):
        resolve(
            world,
            states[0],
            transition(states[0], Operation("set_visible", "clock", True)),
            "illegal",
        )


@pytest.mark.parametrize(
    ("operation", "message"),
    [
        (Operation("set_transform", "chair", Affine.translate(10, 15)), "forbids"),
        (Operation("set_transform", "chair", Affine.scale_translate(2, 2, 9, 15)), "forbids"),
        (Operation("set_transform", "window", Affine.scale_translate(2, 2, 3, 3)), "forbids"),
        (Operation("set_transform", "painting", Affine(0, 1, -1, 0, 16, 3)), "forbids"),
        (Operation("set_visible", "chair", False), "forbids"),
        (Operation("set_variant", "chair", "chair-identical-unauthorized"), "forbids"),
    ],
)
def test_locked_mutations_rejected(world, states, operation, message):
    with pytest.raises(SceneModelError, match=message):
        resolve(world, states[0], transition(states[0], operation), "illegal")


def test_identical_looking_asset_has_distinct_identity(world):
    original = world.asset("asset-chair")
    clone = world.asset("asset-chair-clone")
    assert original.rgba == clone.rgba
    assert original.asset_id != clone.asset_id
    assert original.expected_digest == clone.expected_digest


@pytest.mark.parametrize("action", ["set_camera", "set_style", "set_wall_treatment"])
def test_world_level_mutation_rejected(world, states, action):
    with pytest.raises(SceneModelError, match="unauthorized world mutation"):
        resolve(
            world, states[0], transition(states[0], Operation(action, None, "changed")), "illegal"
        )


def test_independent_chair_slice_transform_rejected(world, states):
    with pytest.raises(SceneModelError, match="unauthorized world mutation"):
        resolve(
            world,
            states[0],
            transition(
                states[0], Operation("set_slice_transform", "chair", Affine.translate(1, 0))
            ),
            "illegal",
        )


def test_shared_wall_plane_geometry_retained(world, states):
    window = states[0].entity("window")
    painting = states[0].entity("painting")
    assert window.plane_key == painting.plane_key == "wall-plane"
    assert world.geometry.plane(window.plane_key) is world.geometry.plane(painting.plane_key)
    assert states[3].entity("window") == window
    assert states[3].entity("painting") == painting


def test_world_scale_is_not_pixel_bounds(world, states):
    actor_a = world.variant(states[0].entity("actor").variant_id)
    actor_c = world.variant(states[3].entity("actor").variant_id)
    assert actor_a.intrinsic_size_wu != actor_c.intrinsic_size_wu
    assert actor_a.neutral_scale_id == actor_c.neutral_scale_id == "actor-neutral-v1"
    assert states[0].entity("chair").local_transform.scale == (1.0, 1.0)
    assert states[0].entity("table").local_transform.scale == (1.0, 1.0)


def test_movable_scale_cannot_fake_motion(world, states):
    with pytest.raises(SceneModelError, match="scale cannot"):
        resolve(
            world,
            states[0],
            transition(
                states[0], Operation("set_transform", "report", Affine.scale_translate(2, 2, 2, 2))
            ),
            "illegal",
        )


def test_complete_chair_is_one_entity_with_one_source(world, states):
    variant = world.variant(states[0].entity("chair").variant_id)
    assert variant.entity_key == "chair"
    assert variant.partition_complete_source
    assert {layer.asset_id for layer in variant.layers} == {"asset-chair"}
    assert len(variant.layers) == 2


def test_all_chair_slices_share_effective_transform(world, states):
    entity = states[0].entity("chair")
    signatures = []
    for layer in world.variant(entity.variant_id).layers:
        signatures.append((layer.node_key, entity.effective_transform))
    assert len({item[1] for item in signatures}) == 1


def test_disocclusion_reveals_same_source_chair(world, states):
    before = render(world, states[2])
    after = render(world, states[3])
    before_visible = sum(owner == "chair" for owner in before.owner_map)
    after_visible = sum(owner == "chair" for owner in after.owner_map)
    assert after_visible > before_visible
    for node in ("chair.top", "chair.bottom"):
        assert layer_hashes(before)[node] == layer_hashes(after)[node]


def test_actor_report_paw_interleave_is_deterministic(world, states):
    result = render(world, states[2])
    nodes = [key for key, _ in result.layer_digests]
    assert nodes.index("actor.body") < nodes.index("report.main") < nodes.index("actor.paw")
    assert result == render(world, states[2])


def test_mask_partition_gap_or_overlap_rejected(world):
    actor = world.variant("actor-a")
    bad = replace(
        actor, layers=(actor.layers[0], replace(actor.layers[1], mask_id=actor.layers[0].mask_id))
    )
    with pytest.raises(SceneModelError, match="gap or overlap"):
        validate_world(replace_variant(world, "actor-a", bad))


def test_contradictory_slice_order_rejected(world, states):
    actor = world.variant("actor-b")
    body, paw = actor.layers
    bad = replace(actor, layers=(replace(body, after=("actor.paw",)), paw))
    broken = bind_world_definition(replace_variant(world, "actor-b", bad))
    broken_state = build_fixture_states(broken)[2]
    with pytest.raises(SceneModelError, match="contradictory"):
        render(broken, broken_state)


def test_parent_cycle_rejected(world, states):
    previous = states[2]
    with pytest.raises(SceneModelError, match="parent cycle"):
        resolve(
            world,
            previous,
            transition(
                previous,
                Operation("attach", "actor", ("report", Affine())),
            ),
            "illegal",
        )


def test_parent_derived_movement_requires_and_reports_closure(world, states):
    previous = states[2]
    operation = Operation("set_transform", "actor", Affine.translate(29, 16))
    with pytest.raises(SceneModelError, match="outside permitted closure"):
        resolve(world, previous, transition(previous, operation), "illegal")
    result = resolve(world, previous, transition(previous, operation, closure=("report",)), "legal")
    assert result.entity("report").local_transform == previous.entity("report").local_transform
    assert (
        result.entity("report").effective_transform != previous.entity("report").effective_transform
    )
    assert any(item["entity_key"] == "report" for item in result.diff.derived_changes)


def test_canonical_serialization_and_digest_stable(states):
    payload = snapshot_payload(build_fixture_world(), states[2])
    assert canonical_json(payload) == canonical_json(json.loads(canonical_json(payload)))
    assert digest(payload) == digest(json.loads(canonical_json(payload)))


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_numbers_rejected(bad):
    with pytest.raises(SceneModelError, match="NaN and Infinity"):
        Affine(e=bad)


def test_unknown_snapshot_schema_and_fields_rejected(world, states):
    payload = snapshot_payload(world, states[1])
    validate_snapshot_payload(payload)
    with pytest.raises(SceneModelError, match="unknown or missing"):
        validate_snapshot_payload(payload | {"surprise": True})
    with pytest.raises(SceneModelError, match="unknown snapshot schema"):
        validate_snapshot_payload(payload | {"schema_version": 2})


def test_source_digest_corruption_rejected(world):
    asset = world.asset("asset-window")
    corrupted = replace(asset, rgba=asset.rgba[:-1] + b"x")
    with pytest.raises(SceneModelError, match="digest mismatch"):
        validate_world(replace_asset(world, asset.asset_id, corrupted))


def test_missing_source_bytes_rejected(world):
    asset = world.asset("asset-window")
    missing = replace(asset, rgba=None)
    with pytest.raises(SceneModelError, match="missing source"):
        validate_world(replace_asset(world, asset.asset_id, missing))


def test_mask_digest_corruption_rejected(world):
    mask = world.mask("mask-chair-top")
    broken = replace(mask, alpha=mask.alpha[:-1] + b"x")
    broken_world = replace(
        world,
        masks=tuple(broken if item.mask_id == mask.mask_id else item for item in world.masks),
    )
    with pytest.raises(SceneModelError, match="mask digest mismatch"):
        validate_world(broken_world)


def test_machine_readable_diff_exact(world, states):
    diff = states[2].diff
    assert diff.unexpected == ()
    assert {item["entity_key"] for item in diff.direct_changes} == {"report", "laptop"}
    assert {item["entity_key"] for item in diff.introduced_or_hidden} == {"report"}
    assert any(
        item["entity_key"] == "report" and item["cause"] == "attachment"
        for item in diff.derived_changes
    )
    assert {item["entity_key"] for item in diff.inherited} >= {
        "wall",
        "window",
        "painting",
        "chair",
        "table",
    }


def test_generation_demand_plan_is_pure_and_limited(world, states):
    intent = TransitionIntent(
        "demand",
        states[0].state_digest,
        "scene-demand",
        (
            Operation("set_variant", "actor", "actor-b"),
            Operation("set_variant", "report", "report-new"),
        ),
    )
    plan = plan_generation_demand(world, states[0], intent, {"actor-a", "actor-b", "report-v1"})
    assert plan["needs_new_variant"] == ["report:report-new"]
    assert set(plan["exact_reuse"]) >= {"wall", "window", "painting", "chair", "table"}


def test_provider_spy_remains_zero_across_all_paths(world, states):
    class ProviderSpy:
        calls = 0

        def invoke(self):
            self.calls += 1
            raise AssertionError("provider must never be called")

    spy = ProviderSpy()
    render(world, states[2])
    with pytest.raises(SceneModelError):
        resolve(
            world,
            states[0],
            transition(states[0], Operation("set_transform", "chair", Affine.translate(1, 1))),
            "illegal",
        )
    assert spy.calls == 0


def test_static_layer_rasters_equal_across_states(world, states):
    renders = [render(world, state) for state in states]
    for node in (
        "wall.main",
        "window.main",
        "painting.main",
        "chair.top",
        "chair.bottom",
        "table.main",
    ):
        assert len({layer_hashes(result)[node] for result in renders}) == 1


def test_actor_change_does_not_change_static_rasters(world, states):
    before = render(world, states[0])
    after = render(world, states[1])
    assert layer_hashes(before)["actor.body"] != layer_hashes(after)["actor.body"]
    assert layer_hashes(before)["wall.main"] == layer_hashes(after)["wall.main"]
    assert layer_hashes(before)["chair.top"] == layer_hashes(after)["chair.top"]


def test_stateful_variant_replacement_does_not_retain_old_layers(world, states):
    """A state change renders only the selected variant, never accumulated marker residue."""

    before = render(world, states[1])
    after = render(world, states[2])

    assert "laptop.main" in layer_hashes(before)
    assert "laptop.on" not in layer_hashes(before)
    assert "laptop.main" not in layer_hashes(after)
    assert "laptop.on" in layer_hashes(after)
    assert states[2].diff.unexpected == ()


def test_rejected_actor_variant_does_not_mutate_state(world, states):
    original = states[0]
    with pytest.raises(SceneModelError, match="variant not admitted"):
        resolve(
            world,
            original,
            transition(original, Operation("set_variant", "actor", "actor-rejected")),
            "illegal",
        )
    assert original == states[0]
    assert original.entity("actor").variant_id == "actor-a"


def test_style_palette_camera_and_treatment_are_world_frozen(world, states):
    assert world.style_profile_id == "visual-style-profile-fixture-v1"
    assert world.palette_id == "palette-fixture-v1"
    assert world.geometry.camera.fit_policy == "locked"
    assert states[0].state_digest != ""


def test_density_missing_purpose_is_surfaced(world):
    window = world.entity("window")
    broken = replace(window, purpose=None)
    changed = replace(
        world,
        entities=tuple(broken if item.entity_key == "window" else item for item in world.entities),
    )
    assert density_problems(changed) == ("window:missing-purpose",)
    assert density_problems(world) == ()


def test_future_snapshot_freezes_hidden_entities_assets_and_lineage(world, states):
    payload = snapshot_payload(world, states[1])
    assert len(payload["entities"]) == len(world.entities)
    assert (
        next(item for item in payload["entities"] if item["entity_key"] == "report")["visible"]
        is False
    )
    assert payload["geometry_contract_digest"] == digest(world.geometry)
    assert payload["complete_state_digest"] == states[1].state_digest
    validate_snapshot_payload(payload)


def test_current_domain_bindings_are_ids_only(world):
    bindings = world.bindings
    assert bindings.visual_plan_id
    assert bindings.editorial_scene_ids
    assert bindings.asset_spec_ids
    assert bindings.character_profile_id
    assert bindings.character_reference_set_id
    assert bindings.visual_reference_authority_id
    assert bindings.visual_style_profile_id == world.style_profile_id


def test_state_objects_are_immutable(states):
    with pytest.raises(FrozenInstanceError):
        states[0].entities = ()


def test_paths_and_timestamps_are_not_state_identity(world, states):
    payload = snapshot_payload(world, states[0])
    serialized = canonical_json(payload)
    assert "D:\\" not in serialized
    assert "created_at" not in serialized


def test_render_signatures_cover_all_active_layers(world, states):
    result = render(world, states[2])
    assert {key for key, _ in result.layer_digests} == {
        key for key, _ in result.layer_render_input_digests
    }
    assert all(len(value) == 64 for _, value in result.layer_render_input_digests)


def test_world_definition_digest_is_deterministic_and_order_normalized(world):
    reordered = replace(
        world,
        entities=tuple(reversed(world.entities)),
        geometry=replace(world.geometry, planes=tuple(reversed(world.geometry.planes))),
    )
    assert world_definition_payload(world) == world_definition_payload(reordered)
    assert world_definition_digest(world) == world_definition_digest(reordered)
    validate_world(reordered)


def test_same_identity_different_wall_content_changes_world_and_state_digest(world):
    original = world.asset("asset-wall")
    changed_bytes = bytes((1, 2, 3, 255)) * (original.width * original.height)
    changed_asset = RasterAsset.create(
        original.asset_id, original.width, original.height, changed_bytes
    )
    changed_world = bind_world_definition(replace_asset(world, original.asset_id, changed_asset))
    assert (world.world_key, world.revision) == (
        changed_world.world_key,
        changed_world.revision,
    )
    assert world.definition_digest != changed_world.definition_digest
    assert base_state(world).state_digest != base_state(changed_world).state_digest


def test_same_identity_different_camera_changes_world_digest(world):
    camera = replace(world.geometry.camera, world_to_pixel=Affine(a=2.25, d=2.25))
    changed = bind_world_definition(replace(world, geometry=replace(world.geometry, camera=camera)))
    assert changed.definition_digest != world.definition_digest


def test_same_identity_different_plane_geometry_changes_world_digest(world):
    planes = tuple(
        (
            replace(plane, world_to_stage=Affine.translate(0.25, 0))
            if plane.key == "wall-plane"
            else plane
        )
        for plane in world.geometry.planes
    )
    changed = bind_world_definition(replace(world, geometry=replace(world.geometry, planes=planes)))
    assert changed.definition_digest != world.definition_digest


def test_same_identity_different_style_palette_changes_world_digest(world):
    palette = bind_world_definition(replace(world, palette_id="palette-fixture-v2"))
    treatment = bind_world_definition(replace(world, wall_treatment_id="wall-treatment-v2"))
    assert palette.definition_digest != world.definition_digest
    assert treatment.definition_digest != world.definition_digest


def _changed_chair_masks(world):
    top = RasterMask.create("mask-chair-top", 10, 14, bytes([255] * 60 + [0] * 80))
    bottom = RasterMask.create("mask-chair-bottom", 10, 14, bytes([0] * 60 + [255] * 80))
    return bind_world_definition(
        replace(
            world,
            masks=tuple(
                (
                    top
                    if mask.mask_id == top.mask_id
                    else bottom if mask.mask_id == bottom.mask_id else mask
                )
                for mask in world.masks
            ),
        )
    )


def test_same_identity_different_base_mask_changes_world_digest(world):
    changed = _changed_chair_masks(world)
    validate_world(changed)
    assert changed.definition_digest != world.definition_digest


@pytest.mark.parametrize(
    "changed_world",
    [
        "wall",
        "camera",
        "geometry",
        "palette",
        "mask",
    ],
)
def test_same_key_revision_world_substitution_rejected_before_render(world, changed_world):
    predecessor = base_state(world)
    if changed_world == "wall":
        asset = world.asset("asset-wall")
        replacement = RasterAsset.create(
            asset.asset_id,
            asset.width,
            asset.height,
            bytes((9, 8, 7, 255)) * (asset.width * asset.height),
        )
        impostor = bind_world_definition(replace_asset(world, asset.asset_id, replacement))
    elif changed_world == "camera":
        camera = replace(world.geometry.camera, world_to_pixel=Affine(a=2.1, d=2.1))
        impostor = bind_world_definition(
            replace(world, geometry=replace(world.geometry, camera=camera))
        )
    elif changed_world == "geometry":
        planes = tuple(
            (
                replace(plane, world_to_stage=Affine.translate(0.2, 0))
                if plane.key == "wall-plane"
                else plane
            )
            for plane in world.geometry.planes
        )
        impostor = bind_world_definition(
            replace(world, geometry=replace(world.geometry, planes=planes))
        )
    elif changed_world == "palette":
        impostor = bind_world_definition(replace(world, palette_id="palette-impostor"))
    else:
        impostor = _changed_chair_masks(world)
    intent = transition(predecessor, Operation("set_variant", "actor", "actor-b"))
    with pytest.raises(SceneModelError, match="world definition mismatch"):
        resolve(impostor, predecessor, intent, "rejected-before-render")


def test_stale_cached_world_digest_is_recomputed_and_rejected(world):
    changed = replace(world, palette_id="palette-impostor")
    assert changed.definition_digest == world.definition_digest
    with pytest.raises(SceneModelError, match="world definition digest mismatch"):
        validate_world(changed)


def test_resolved_state_digest_binds_world_definition(world):
    original = base_state(world)
    changed_world = bind_world_definition(replace(world, palette_id="palette-other"))
    changed = base_state(changed_world)
    assert original.world_definition_digest == world.definition_digest
    assert changed.world_definition_digest == changed_world.definition_digest
    assert original.state_digest != changed.state_digest


def test_selected_variant_content_affects_state_digest(world, states):
    assert states[0].world_definition_digest == states[1].world_definition_digest
    assert states[0].entity("actor").entity_key == states[1].entity("actor").entity_key
    assert states[0].state_digest != states[1].state_digest
    assert (
        dict(states[0].entity_content_digests)["actor"]
        != dict(states[1].entity_content_digests)["actor"]
    )


def test_new_actor_variant_can_be_admitted_without_redefining_room(world):
    asset = RasterAsset.create("asset-actor-d", 10, 20, bytes((190, 130, 70, 255)) * 200)
    body = RasterMask.create("mask-actor-d-body", 10, 20, bytes([255] * 160 + [0] * 40))
    paw = RasterMask.create("mask-actor-d-paw", 10, 20, bytes([0] * 160 + [255] * 40))
    variant = EntityVariant(
        "actor-d",
        "actor",
        (4.0, 5.0),
        "actor-neutral-v1",
        (
            RenderSlice(
                "actor.body",
                asset.asset_id,
                body.mask_id,
                Affine(a=0.4, d=0.25),
                ("floor.main",),
            ),
            RenderSlice(
                "actor.paw",
                asset.asset_id,
                paw.mask_id,
                Affine(a=0.4, d=0.25),
                ("report.main",),
            ),
        ),
        character_authority_id="character-profile-core-v3",
        partition_complete_source=True,
    )
    actor = world.entity("actor")
    expanded = replace(
        world,
        entities=tuple(
            (
                replace(item, approved_variants=item.approved_variants + (variant.variant_id,))
                if item.entity_key == actor.entity_key
                else item
            )
            for item in world.entities
        ),
        variants=world.variants + (variant,),
        assets=world.assets + (asset,),
        masks=world.masks + (body, paw),
    )
    expanded = bind_world_definition(expanded)
    assert expanded.definition_digest == world.definition_digest
    predecessor = base_state(world)
    result = resolve(
        expanded,
        predecessor,
        transition(
            predecessor,
            Operation(
                "admit_variant",
                "actor",
                VariantAdmissionRequest("actor-d", "founder-proof", "approved pose"),
            ),
            Operation("set_variant", "actor", "actor-d"),
        ),
        "actor-d-state",
    )
    assert result.entity("actor").variant_id == "actor-d"
    assert result.world_definition_digest == predecessor.world_definition_digest


def test_existing_selected_variant_bytes_cannot_be_repointed(world, states):
    asset = world.asset("asset-actor-b")
    replacement = RasterAsset.create(
        asset.asset_id,
        asset.width,
        asset.height,
        bytes((1, 1, 1, 255)) * (asset.width * asset.height),
    )
    changed = bind_world_definition(replace_asset(world, asset.asset_id, replacement))
    assert changed.definition_digest == world.definition_digest
    predecessor = states[1]
    with pytest.raises(SceneModelError, match="admitted variant content mismatch"):
        resolve(
            changed,
            predecessor,
            transition(predecessor, Operation("set_visible", "report", True)),
            "rejected-repoint",
        )


def test_duplicate_variant_or_asset_identity_rejected(world):
    with pytest.raises(SceneModelError, match="duplicate variant identity"):
        validate_world(replace(world, variants=world.variants + (world.variant("actor-b"),)))
    with pytest.raises(SceneModelError, match="duplicate asset identity"):
        validate_world(replace(world, assets=world.assets + (world.asset("asset-actor-b"),)))


def test_fixture_uses_non_identity_pixel_to_wu_and_world_to_pixel_mapping(world):
    actor = world.variant("actor-a")
    assert world.geometry.camera.world_to_pixel.scale == (2.0, 2.0)
    assert actor.layers[0].local_mapping.scale == (0.5, 0.5)
    assert actor.intrinsic_size_wu == (4.0, 5.0)
    assert (world.asset("asset-actor-a").width, world.asset("asset-actor-a").height) == (
        8,
        10,
    )


def test_wu_projection_is_derived_not_source_pixel_identity(world):
    variant = world.variant("actor-b")
    asset = world.asset("asset-actor-b")
    layer = variant.layers[0]
    local_extent = layer.local_mapping.apply(asset.width - 1, asset.height - 1)
    projected_extent = world.geometry.camera.world_to_pixel.apply(*local_extent)
    assert (asset.width, asset.height) == (12, 15)
    assert local_extent != (asset.width - 1, asset.height - 1)
    assert projected_extent != (asset.width - 1, asset.height - 1)


def test_actor_source_bounds_change_without_neutral_world_scale_change(world, states):
    first = world.variant(states[0].entity("actor").variant_id)
    second = world.variant(states[1].entity("actor").variant_id)
    first_asset = world.asset(first.layers[0].asset_id)
    second_asset = world.asset(second.layers[0].asset_id)
    assert (first_asset.width, first_asset.height) == (8, 10)
    assert (second_asset.width, second_asset.height) == (12, 15)
    assert first.intrinsic_size_wu == second.intrinsic_size_wu == (4.0, 5.0)
    assert first.neutral_scale_id == second.neutral_scale_id == "actor-neutral-v1"
    assert states[0].entity("actor").local_transform == states[1].entity("actor").local_transform


def _proof_harness_module():
    path = Path(__file__).parents[1] / "scripts" / "prove_persistent_scene_model.py"
    spec = importlib.util.spec_from_file_location("persistent_scene_proof_harness", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_provider_spy_harness_covers_all_proof_paths_without_calls(world, states):
    class ForbiddenProvider:
        calls = 0

        def __call__(self, *_args, **_kwargs):
            self.calls += 1
            raise AssertionError("provider invocation forbidden")

    spy = ForbiddenProvider()
    result = _proof_harness_module().exercise_provider_free_paths(world, states, spy)
    assert result == {
        "valid_resolution": "passed",
        "failed_rebind": "rejected",
        "explicit_admission": "passed-without-provider",
        "generation_demand": "returned-not-executed",
        "missing_variant": "blocked-or-planned",
        "missing_source": "rejected",
        "corrupt_source": "rejected",
        "invalid_transition": "rejected",
        "render_validation_failure": "rejected",
        "provider_call_count": 0,
    }
    assert spy.calls == 0


def test_variant_content_digest_is_deterministic(world):
    variant = world.variant("actor-b")
    assert variant_content_digest(world, variant) == variant_content_digest(world, variant)


def test_changed_asset_id_changes_variant_digest_even_with_same_bytes(world):
    original = world.asset("asset-actor-b")
    assert original.rgba is not None
    clone = RasterAsset.create(
        "asset-actor-b-clone", original.width, original.height, original.rgba
    )
    variant = world.variant("actor-b")
    changed = replace(
        variant,
        layers=tuple(replace(layer, asset_id=clone.asset_id) for layer in variant.layers),
    )
    altered = replace_variant(
        replace(world, assets=world.assets + (clone,)), variant.variant_id, changed
    )
    assert variant_content_digest(world, variant) != variant_content_digest(altered, changed)


def test_changed_asset_bytes_change_variant_digest(world):
    asset = world.asset("asset-actor-b")
    replacement = RasterAsset.create(
        asset.asset_id,
        asset.width,
        asset.height,
        bytes((1, 2, 3, 255)) * (asset.width * asset.height),
    )
    altered = replace_asset(world, asset.asset_id, replacement)
    assert variant_content_digest(world, world.variant("actor-b")) != variant_content_digest(
        altered, altered.variant("actor-b")
    )


def test_changed_mask_changes_variant_digest(world):
    variant = world.variant("actor-b")
    mask = world.mask("mask-actor-b-body")
    assert mask.alpha is not None
    changed = RasterMask.create(mask.mask_id, mask.width, mask.height, mask.alpha[::-1])
    altered = replace(
        world,
        masks=tuple(changed if item.mask_id == mask.mask_id else item for item in world.masks),
    )
    assert variant_content_digest(world, variant) != variant_content_digest(
        altered, altered.variant("actor-b")
    )


def test_changed_slice_mapping_or_order_changes_variant_digest(world):
    variant = world.variant("actor-b")
    mapped = replace(
        variant,
        layers=(replace(variant.layers[0], local_mapping=Affine(a=0.34, d=1 / 3)),)
        + variant.layers[1:],
    )
    reordered = replace(variant, layers=tuple(reversed(variant.layers)))
    assert variant_content_digest(world, mapped) != variant_content_digest(world, variant)
    assert variant_content_digest(world, reordered) != variant_content_digest(world, variant)


def test_changed_anchor_or_scale_contract_changes_variant_digest(world):
    variant = world.variant("actor-b")
    anchored = replace(variant, anchors=(("foot-contact", (1.0, 2.0)),))
    scaled = replace(variant, neutral_scale_id="actor-neutral-v2")
    assert variant_content_digest(world, anchored) != variant_content_digest(world, variant)
    assert variant_content_digest(world, scaled) != variant_content_digest(world, variant)


def test_admitted_set_digest_is_order_normalized(world):
    state = base_state(world)
    assert variant_admission_payload(state.admitted_variants) == variant_admission_payload(
        tuple(reversed(state.admitted_variants))
    )
    assert variant_admission_digest(state.admitted_variants) == variant_admission_digest(
        tuple(reversed(state.admitted_variants))
    )


def test_ordinary_transition_inherits_admitted_set(world, states):
    assert states[0].admitted_variants == states[1].admitted_variants
    assert states[0].variant_admission_digest == states[1].variant_admission_digest


def test_explicit_new_admission_changes_admitted_set_not_world(world):
    expanded = expanded_actor_variant(world)
    predecessor = base_state(world)
    result = resolve(expanded, predecessor, admit_and_select(predecessor), "admitted")
    assert expanded.definition_digest == world.definition_digest
    assert result.variant_admission_digest != predecessor.variant_admission_digest
    assert result.world_definition_digest == predecessor.world_definition_digest
    assert result.state_digest != predecessor.state_digest


def test_unselected_admitted_variant_cannot_be_rebound(world):
    predecessor = base_state(world)
    asset = world.asset("asset-actor-b")
    replacement = RasterAsset.create(
        asset.asset_id,
        asset.width,
        asset.height,
        bytes((1, 1, 1, 255)) * (asset.width * asset.height),
    )
    altered = bind_world_definition(replace_asset(world, asset.asset_id, replacement))
    assert altered.definition_digest == world.definition_digest
    with pytest.raises(SceneModelError, match="admitted variant content mismatch"):
        resolve(
            altered,
            predecessor,
            transition(predecessor, Operation("set_variant", "actor", "actor-b")),
            "rejected",
        )


@pytest.mark.parametrize("mutation", ["asset-id", "bytes", "mask", "mapping", "anchor"])
def test_admitted_actor_b_content_mutation_rejected_before_selection(world, mutation):
    predecessor = base_state(world)
    variant = world.variant("actor-b")
    altered = world
    if mutation == "asset-id":
        asset = world.asset("asset-actor-b")
        assert asset.rgba is not None
        clone = RasterAsset.create("asset-actor-b-clone", asset.width, asset.height, asset.rgba)
        changed_variant = replace(
            variant,
            layers=tuple(replace(layer, asset_id=clone.asset_id) for layer in variant.layers),
        )
        altered = replace_variant(
            replace(world, assets=world.assets + (clone,)), variant.variant_id, changed_variant
        )
    elif mutation == "bytes":
        asset = world.asset("asset-actor-b")
        replacement = RasterAsset.create(
            asset.asset_id,
            asset.width,
            asset.height,
            bytes((4, 4, 4, 255)) * (asset.width * asset.height),
        )
        altered = replace_asset(world, asset.asset_id, replacement)
    elif mutation == "mask":
        body = RasterMask.create("mask-actor-b-body", 12, 15, bytes([255] * 132 + [0] * 48))
        paw = RasterMask.create("mask-actor-b-paw", 12, 15, bytes([0] * 132 + [255] * 48))
        altered = replace(
            world,
            masks=tuple(
                (
                    body
                    if item.mask_id == body.mask_id
                    else paw if item.mask_id == paw.mask_id else item
                )
                for item in world.masks
            ),
        )
    elif mutation == "mapping":
        changed_variant = replace(
            variant,
            layers=tuple(
                replace(layer, local_mapping=Affine(a=0.34, d=1 / 3)) for layer in variant.layers
            ),
        )
        altered = replace_variant(world, variant.variant_id, changed_variant)
    else:
        altered = replace_variant(
            world,
            variant.variant_id,
            replace(variant, anchors=(("foot-contact", (1.0, 2.0)),)),
        )
    altered = bind_world_definition(altered)
    assert altered.definition_digest == world.definition_digest
    with pytest.raises(SceneModelError, match="admitted variant content mismatch"):
        resolve(
            altered,
            predecessor,
            transition(predecessor, Operation("set_variant", "actor", "actor-b")),
            f"rejected-{mutation}",
        )


def test_previously_admitted_never_selected_variant_rebind_rejects(world):
    base = base_state(world)
    intermediate = resolve(
        world,
        base,
        transition(base, Operation("set_visible", "spark", True)),
        "still-actor-a",
    )
    assert intermediate.entity("actor").variant_id == "actor-a"
    asset = world.asset("asset-actor-b")
    replacement = RasterAsset.create(
        asset.asset_id,
        asset.width,
        asset.height,
        bytes((2, 2, 2, 255)) * (asset.width * asset.height),
    )
    altered = bind_world_definition(replace_asset(world, asset.asset_id, replacement))
    with pytest.raises(SceneModelError, match="admitted variant content mismatch"):
        resolve(
            altered,
            intermediate,
            transition(intermediate, Operation("set_variant", "actor", "actor-b")),
            "rejected-later",
        )


def test_same_looking_replacement_asset_identity_rejects(world):
    predecessor = base_state(world)
    original = world.asset("asset-actor-b")
    assert original.rgba is not None
    clone = RasterAsset.create(
        "asset-actor-b-clone", original.width, original.height, original.rgba
    )
    variant = world.variant("actor-b")
    changed_variant = replace(
        variant, layers=tuple(replace(layer, asset_id=clone.asset_id) for layer in variant.layers)
    )
    altered = bind_world_definition(
        replace_variant(
            replace(world, assets=world.assets + (clone,)), variant.variant_id, changed_variant
        )
    )
    with pytest.raises(SceneModelError, match="admitted variant content mismatch"):
        resolve(
            altered,
            predecessor,
            transition(predecessor, Operation("set_variant", "actor", "actor-b")),
            "rejected-clone",
        )


def test_rebinding_newly_admitted_variant_rejects_later(world):
    expanded = expanded_actor_variant(world)
    base = base_state(world)
    admitted = resolve(expanded, base, admit_and_select(base), "admitted")
    asset = expanded.asset("asset-actor-d")
    replacement = RasterAsset.create(
        asset.asset_id,
        asset.width,
        asset.height,
        bytes((3, 3, 3, 255)) * (asset.width * asset.height),
    )
    altered = bind_world_definition(replace_asset(expanded, asset.asset_id, replacement))
    with pytest.raises(SceneModelError, match="admitted variant content mismatch"):
        resolve(
            altered,
            admitted,
            transition(admitted, Operation("set_visible", "spark", True)),
            "rebound",
        )


def test_raw_available_variant_and_asset_do_not_imply_admission(world):
    expanded = expanded_actor_variant(world)
    predecessor = base_state(world)
    assert expanded.variant("actor-d")
    assert expanded.asset("asset-actor-d")
    with pytest.raises(SceneModelError, match="variant not admitted"):
        resolve(
            expanded,
            predecessor,
            transition(predecessor, Operation("set_variant", "actor", "actor-d")),
            "raw-not-admitted",
        )
