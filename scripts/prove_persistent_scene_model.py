"""Write private zero-spend evidence for the isolated persistent-scene prototype."""

from __future__ import annotations

import argparse
import hashlib
from dataclasses import asdict, replace
from pathlib import Path

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
    plan_generation_demand,
    render,
    resolve,
    snapshot_payload,
    validate_world,
    variant_admission_payload,
    variant_content_digest,
    world_definition_payload,
)


def write_text(path: Path, value: object) -> None:
    path.write_text(canonical_json(value) + "\n", encoding="utf-8", newline="\n")


def write_ppm(path: Path, width: int, height: int, rgba: bytes) -> None:
    rgb = bytes(channel for index, channel in enumerate(rgba) if index % 4 != 3)
    path.write_bytes(f"P6\n{width} {height}\n255\n".encode() + rgb)


def admission_fixture(world):
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
                    replace(
                        entity, approved_variants=entity.approved_variants + (variant.variant_id,)
                    )
                    if entity.entity_key == "actor"
                    else entity
                )
                for entity in world.entities
            ),
            variants=world.variants + (variant,),
            assets=world.assets + (asset,),
            masks=world.masks + (body, paw),
        )
    )


def exercise_provider_free_paths(world, states, forbidden_generation) -> dict[str, object]:
    """Proof harness: return demand or fail closed, never execute generation."""

    results: dict[str, object] = {}
    base = states[0]
    valid = TransitionIntent(
        "provider-proof-valid",
        base.state_digest,
        "provider-proof-scene",
        (Operation("set_variant", "actor", "actor-b"),),
    )
    resolve(world, base, valid, "provider-proof-valid-state")
    results["valid_resolution"] = "passed"

    actor_b = world.asset("asset-actor-b")
    rebound_asset = RasterAsset.create(
        actor_b.asset_id,
        actor_b.width,
        actor_b.height,
        bytes((1, 1, 1, 255)) * (actor_b.width * actor_b.height),
    )
    rebound_world = bind_world_definition(
        replace(
            world,
            assets=tuple(
                rebound_asset if asset.asset_id == actor_b.asset_id else asset
                for asset in world.assets
            ),
        )
    )
    try:
        resolve(rebound_world, base, valid, "provider-proof-rebind")
    except SceneModelError:
        results["failed_rebind"] = "rejected"
    else:
        raise AssertionError("admitted variant rebind unexpectedly resolved")

    expanded = admission_fixture(world)
    admission = TransitionIntent(
        "provider-proof-admission",
        base.state_digest,
        "provider-proof-scene",
        (
            Operation(
                "admit_variant",
                "actor",
                VariantAdmissionRequest("actor-d", "proof-approval", "reviewed fixture"),
            ),
            Operation("set_variant", "actor", "actor-d"),
        ),
    )
    resolve(expanded, base, admission, "provider-proof-admitted-state")
    results["explicit_admission"] = "passed-without-provider"

    missing_variant = TransitionIntent(
        "provider-proof-demand",
        base.state_digest,
        "provider-proof-scene",
        (Operation("set_variant", "actor", "actor-not-present"),),
    )
    demand = plan_generation_demand(
        world,
        base,
        missing_variant,
        {variant.variant_id for variant in world.variants},
    )
    assert demand["needs_new_variant"] == ["actor:actor-not-present"]
    results["generation_demand"] = "returned-not-executed"
    try:
        resolve(world, base, missing_variant, "provider-proof-missing-variant")
    except SceneModelError:
        results["missing_variant"] = "blocked-or-planned"
    else:
        raise AssertionError("missing variant unexpectedly resolved")

    source = world.asset("asset-wall")
    missing_source = replace(source, rgba=None)
    missing_world = replace(
        world,
        assets=tuple(
            missing_source if asset.asset_id == source.asset_id else asset for asset in world.assets
        ),
    )
    try:
        validate_world(missing_world)
    except SceneModelError:
        results["missing_source"] = "rejected"
    else:
        raise AssertionError("missing source unexpectedly validated")

    assert source.rgba is not None
    corrupt_source = replace(source, rgba=source.rgba[:-1] + b"x")
    corrupt_world = replace(
        world,
        assets=tuple(
            corrupt_source if asset.asset_id == source.asset_id else asset for asset in world.assets
        ),
    )
    try:
        validate_world(corrupt_world)
    except SceneModelError:
        results["corrupt_source"] = "rejected"
    else:
        raise AssertionError("corrupt source unexpectedly validated")

    illegal = TransitionIntent(
        "provider-proof-illegal",
        base.state_digest,
        "provider-proof-scene",
        (Operation("set_transform", "chair", Affine.translate(1, 1)),),
    )
    try:
        resolve(world, base, illegal, "provider-proof-illegal-state")
    except SceneModelError:
        results["invalid_transition"] = "rejected"
    else:
        raise AssertionError("illegal transition unexpectedly resolved")

    invalid_state = replace(states[2], state_digest="0" * 64)
    try:
        render(world, invalid_state)
    except SceneModelError:
        results["render_validation_failure"] = "rejected"
    else:
        raise AssertionError("invalid state unexpectedly rendered")

    # Deliberately retain the injected forbidden callable without invoking it.
    results["provider_call_count"] = getattr(forbidden_generation, "calls", 0)
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty proof directory: {output}")
    output.mkdir(parents=True, exist_ok=True)

    world = build_fixture_world()
    states = build_fixture_states(world)

    class ForbiddenGeneration:
        calls = 0

        def __call__(self, *_args, **_kwargs):
            self.calls += 1
            raise AssertionError("provider invocation forbidden")

    provider_spy = ForbiddenGeneration()
    provider_evidence = exercise_provider_free_paths(world, states, provider_spy)
    expanded_world = admission_fixture(world)
    admission_intent = TransitionIntent(
        "intent-admit-actor-d",
        states[0].state_digest,
        "scene-admission-proof",
        (
            Operation(
                "admit_variant",
                "actor",
                VariantAdmissionRequest(
                    "actor-d", "founder-proof-approval", "reviewed fixture pose"
                ),
            ),
            Operation("set_variant", "actor", "actor-d"),
        ),
    )
    admitted_state = resolve(expanded_world, states[0], admission_intent, "state-admitted-actor-d")
    intents = (
        TransitionIntent(
            "intent-1",
            states[0].state_digest,
            "scene-1",
            (Operation("set_variant", "actor", "actor-b"),),
        ),
        TransitionIntent(
            "intent-2",
            states[1].state_digest,
            "scene-2",
            (
                Operation("set_visible", "report", True),
                Operation("attach", "report", ("actor", Affine.translate(1, 1.5))),
                Operation("set_variant", "laptop", "laptop-on"),
            ),
        ),
        TransitionIntent(
            "intent-3",
            states[2].state_digest,
            "scene-3",
            (
                Operation("set_variant", "actor", "actor-c"),
                Operation("attach", "report", ("table", Affine.translate(4, -1))),
                Operation("set_state", "report", "reviewed"),
                Operation("set_transform", "occluder", Affine.translate(17.5, 7.5)),
            ),
        ),
    )
    write_text(
        output / "fixture-description.json",
        {
            "purpose": "mechanical structural proof only",
            "world_key": world.world_key,
            "world_revision": world.revision,
            "entity_inventory": [entity.entity_key for entity in world.entities],
            "geometry": asdict(world.geometry),
            "provider_capability": "absent",
        },
    )
    write_text(output / "base-world.json", snapshot_payload(world, states[0]))
    write_text(output / "world-definition.json", world_definition_payload(world))
    write_text(output / "provider-isolation.json", provider_evidence)
    write_text(
        output / "base-variant-admissions.json",
        variant_admission_payload(states[0].admitted_variants),
    )
    write_text(
        output / "variant-admission-retest.json",
        {
            "world_definition_digest_stable": (
                expanded_world.definition_digest == world.definition_digest
            ),
            "base_admission_digest": states[0].variant_admission_digest,
            "expanded_admission_digest": admitted_state.variant_admission_digest,
            "admission_digest_changed": (
                admitted_state.variant_admission_digest != states[0].variant_admission_digest
            ),
            "new_variant_content_digest": variant_content_digest(
                expanded_world, expanded_world.variant("actor-d")
            ),
            "selected_variant": admitted_state.entity("actor").variant_id,
            "resolved_state_digest": admitted_state.state_digest,
            "explicit_authorization": "founder-proof-approval",
            "raw_asset_does_not_imply_admission": True,
            "provider_invocation_count": provider_spy.calls,
        },
    )
    write_text(
        output / "expanded-variant-admissions.json",
        variant_admission_payload(admitted_state.admitted_variants),
    )
    write_text(
        output / "resolved-state-admitted-actor-d.json",
        snapshot_payload(expanded_world, admitted_state),
    )

    original_wall = world.asset("asset-wall")
    changed_wall = RasterAsset.create(
        original_wall.asset_id,
        original_wall.width,
        original_wall.height,
        bytes((1, 2, 3, 255)) * (original_wall.width * original_wall.height),
    )
    impostor = bind_world_definition(
        replace(
            world,
            assets=tuple(
                changed_wall if asset.asset_id == original_wall.asset_id else asset
                for asset in world.assets
            ),
        )
    )
    substitution_result = "not-exercised"
    try:
        resolve(
            impostor,
            states[0],
            TransitionIntent(
                "world-substitution",
                states[0].state_digest,
                "scene-substitution",
                (Operation("set_variant", "actor", "actor-b"),),
            ),
            "world-substitution-state",
        )
    except SceneModelError as exc:
        substitution_result = str(exc)
    else:
        raise AssertionError("same-key/revision world substitution unexpectedly resolved")
    write_text(
        output / "world-binding-retest.json",
        {
            "same_nominal_identity": (world.world_key, world.revision)
            == (impostor.world_key, impostor.revision),
            "original_world_definition_digest": world.definition_digest,
            "impostor_world_definition_digest": impostor.definition_digest,
            "world_digests_differ": world.definition_digest != impostor.definition_digest,
            "base_state_digests_differ": states[0].state_digest
            != base_state(impostor).state_digest,
            "substitution_rejected_before_render": substitution_result,
            "failed_review_reproduction": {
                "previous_behavior": "same digest and accepted",
                "source": "2026-09-28 exact commit review",
            },
        },
    )
    actor_a = world.variant("actor-a")
    actor_b = world.variant("actor-b")
    actor_a_asset = world.asset(actor_a.layers[0].asset_id)
    actor_b_asset = world.asset(actor_b.layers[0].asset_id)
    write_text(
        output / "world-unit-evidence.json",
        {
            "unit": world.geometry.unit,
            "camera_world_to_pixel": world.geometry.camera.world_to_pixel,
            "actor_a": {
                "source_pixels": [actor_a_asset.width, actor_a_asset.height],
                "intrinsic_size_wu": actor_a.intrinsic_size_wu,
                "pixel_to_wu": actor_a.layers[0].local_mapping,
                "neutral_scale_id": actor_a.neutral_scale_id,
            },
            "actor_b": {
                "source_pixels": [actor_b_asset.width, actor_b_asset.height],
                "intrinsic_size_wu": actor_b.intrinsic_size_wu,
                "pixel_to_wu": actor_b.layers[0].local_mapping,
                "neutral_scale_id": actor_b.neutral_scale_id,
            },
            "source_bounds_differ": (actor_a_asset.width, actor_a_asset.height)
            != (actor_b_asset.width, actor_b_asset.height),
            "neutral_world_contract_equal": actor_a.neutral_scale_id == actor_b.neutral_scale_id,
        },
    )
    for index, (state, intent) in enumerate(zip(states[1:], intents, strict=True), start=1):
        write_text(output / f"resolved-state-{index}.json", snapshot_payload(world, state))
        write_text(output / f"transition-intent-{index}.json", asdict(intent))
        write_text(output / f"adjacent-diff-{index}.json", asdict(state.diff))

    render_evidence = {}
    for index, state in enumerate(states):
        result = render(world, state)
        write_ppm(
            output / f"proof-composite-{index}.ppm",
            world.geometry.camera.width,
            world.geometry.camera.height,
            result.rgba,
        )
        render_evidence[state.state_id] = {
            "composite_digest": result.composite_digest,
            "layer_raster_digests": dict(result.layer_digests),
            "render_input_signatures": dict(result.layer_render_input_digests),
            "visible_owner_counts": {
                key: result.owner_map.count(key)
                for key in sorted({key for key in result.owner_map if key is not None})
            },
        }
    write_text(output / "render-evidence.json", render_evidence)

    demand_intent = TransitionIntent(
        "demand-evidence",
        states[0].state_digest,
        "scene-demand",
        (
            Operation("set_variant", "actor", "actor-b"),
            Operation("set_variant", "report", "report-new"),
        ),
    )
    write_text(
        output / "generation-demand-plan.json",
        plan_generation_demand(world, states[0], demand_intent, {"actor-a", "actor-b", "report-v1"})
        | {"provider_invocation_count": 0},
    )

    illegal_cases = {
        "undeclared-entity": Operation("set_visible", "clock", True),
        "locked-chair-move": Operation("set_transform", "chair", Affine.translate(1, 1)),
        "locked-chair-scale": Operation(
            "set_transform", "chair", Affine.scale_translate(2, 2, 9, 15)
        ),
        "painting-rotation": Operation("set_transform", "painting", Affine(0, 1, -1, 0)),
        "camera-mutation": Operation("set_camera", None, "other-camera"),
        "wall-treatment": Operation("set_wall_treatment", None, "other-treatment"),
        "independent-chair-slice": Operation(
            "set_slice_transform", "chair", Affine.translate(1, 0)
        ),
        "identical-looking-asset-substitution": Operation(
            "set_variant", "chair", "chair-identical-unauthorized"
        ),
    }
    failures = {}
    for name, operation in illegal_cases.items():
        try:
            resolve(
                world,
                states[0],
                TransitionIntent(
                    f"illegal-{name}", states[0].state_digest, "scene-illegal", (operation,)
                ),
                f"illegal-{name}",
            )
        except SceneModelError as exc:
            failures[name] = {"rejected_before_render": True, "error": str(exc)}
        else:
            raise AssertionError(f"illegal case unexpectedly resolved: {name}")
    write_text(output / "illegal-mutation-evidence.json", failures)

    review = {
        "persistent_scene_models": "clearly required",
        "scene_entities": "clearly required",
        "scene_entity_variants": (
            "clearly required as immutable queryable accepted content; identity, content, "
            "admission/acceptance, and state selection remain distinct"
        ),
        "scene_entity_variant_layers": "clearly required for restrictive slice lineage",
        "scene_transition_intents": "clearly required and distinct from resolved state",
        "resolved_scene_states": "clearly required",
        "resolved_scene_entities": "clearly required; full normalized membership proved",
        "scene_model_visual_authorities": "probably required but not mechanically proven",
        "final_media_scene_states": "deferrable from first persisted milestone",
        "typed_documents": "geometry and density can remain immutable typed documents",
    }
    write_text(output / "persistence-minimality-review.json", review)
    (output / "limitations.md").write_text(
        "# Mechanical proof limitations\n\n"
        "- Affine static-camera mechanics only; no true perspective, camera motion, 3D, "
        "physics, or rigging.\n"
        "- Binary-alpha nearest-neighbour fixture compositor, not production rendering.\n"
        "- Structural actor identity is proven; visual/anatomical quality still requires "
        "human gates.\n"
        "- No production persistence, snapshot, generation, media, or provider path is activated.\n"
        "- Density purpose is surfaced as a planning problem, not an aesthetic score.\n",
        encoding="utf-8",
        newline="\n",
    )

    records = []
    for path in sorted(output.iterdir()):
        if path.name == "evidence-manifest.json":
            continue
        records.append(
            {
                "path": path.name,
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    manifest = {
        "schema_version": 1,
        "world_key": world.world_key,
        "world_revision": world.revision,
        "state_digests": [state.state_digest for state in states],
        "provider_invocation_count": 0,
        "spend_usd": 0,
        "files": records,
    }
    write_text(output / "evidence-manifest.json", manifest)
    print(canonical_json(manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
