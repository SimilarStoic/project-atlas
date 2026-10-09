from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from project_atlas.media import FfmpegRuntime, LocalMediaStorage, MediaRuntimeError, MediaService
from project_atlas.persistence import AtlasRepository
from project_atlas.scene_media import compositor_contract, load_persistent_scene_frame
from project_atlas.scene_model import (
    Affine,
    DomainBindings,
    Operation,
    TransitionIntent,
    base_state,
    bind_world_definition,
    build_fixture_world,
)
from tests.reference_approvals import approve_reference_images
from tests.test_media import _ready_visual_plan, _runtime_or_skip
from tests.test_scene_persistence import (
    AUTHORITY,
    CHARACTER,
    REFERENCE,
    STYLE,
    _managed_asset,
)

WORLD_ID = "persistent-media-world"
SCENES = ("persistent-media-scene-1", "persistent-media-scene-2", "persistent-media-scene-3")
SPECS = ("persistent-media-spec-wall", "persistent-media-spec-actor", "persistent-media-spec-prop")


def _persistent_world(tmp_path):
    repository = AtlasRepository(tmp_path / "scene.sqlite", tmp_path / "assets")
    plan, script = _ready_visual_plan(repository, "persistent-media")
    for sequence, scene_id in enumerate(SCENES, 1):
        repository.create_scene_under_visual_plan_authorization(
            scene_id, plan.id, sequence, f"Excerpt {sequence}", f"Intent {sequence}"
        )
    for spec_id, scene_id in zip(SPECS, SCENES, strict=True):
        repository.create_asset_spec_under_scene_authorization(
            spec_id, scene_id, "graphic", "persistent proof", "fixture", "local fixture"
        )
    source = build_fixture_world()
    variants = tuple(
        replace(item, character_authority_id=CHARACTER) if item.entity_key == "actor" else item
        for item in source.variants
    )
    world = bind_world_definition(
        replace(
            source,
            variants=variants,
            style_profile_id=STYLE,
            bindings=DomainBindings(plan.id, SCENES, SPECS, CHARACTER, REFERENCE, AUTHORITY, STYLE),
        )
    )
    versions = {spec: 0 for spec in SPECS}
    for index, asset in enumerate(world.assets):
        spec_id = SPECS[1] if asset.asset_id.startswith("asset-actor") else SPECS[index % 3]
        versions[spec_id] += 1
        assert asset.rgba is not None
        _managed_asset(
            repository,
            asset.asset_id,
            asset.rgba,
            asset.expected_digest,
            spec_id,
            versions[spec_id],
        )
    for mask in world.masks:
        versions[SPECS[1]] += 1
        assert mask.alpha is not None
        _managed_asset(
            repository,
            mask.mask_id,
            mask.alpha,
            mask.expected_digest,
            SPECS[1],
            versions[SPECS[1]],
        )
    with repository.connection:
        repository.connection.execute(
            "INSERT INTO character_reference_sets VALUES (?, ?, ?, ?)",
            (REFERENCE, CHARACTER, 1, "2026-09-29T00:00:00+00:00"),
        )
        repository.connection.execute(
            "INSERT INTO character_reference_set_members VALUES (?, ?, ?, ?)",
            (REFERENCE, "asset-actor-a", 1, "2026-09-29T00:00:00+00:00"),
        )
    approve_reference_images(repository, "asset-wall")
    repository.create_visual_reference_authority(
        AUTHORITY,
        "persistent-media-proof",
        "global_illustration_style",
        "Persistent media proof",
        "Synthetic exact proof authority.",
        [("asset-wall", "style")],
    )
    base = base_state(world, SCENES[0])
    repository.create_persistent_scene_world(
        WORLD_ID,
        world,
        base,
        base_intent_id="persistent-media-base-intent",
        base_catalog_id="persistent-media-base-catalog",
        authorization_actor="test",
        authorization_reference="media-proof",
    )
    return repository, world, base, script


def _states(repository, base):
    first = repository.resolve_and_persist_scene_state(
        WORLD_ID,
        base.state_id,
        TransitionIntent(
            "media-intent-1",
            base.state_digest,
            SCENES[1],
            (
                Operation("set_variant", "actor", "actor-b"),
                Operation("set_visible", "report", True),
                Operation("attach", "report", ("actor", Affine.translate(1, 1.5))),
                Operation("set_variant", "laptop", "laptop-on"),
            ),
            (),
            "persistent media proof state one",
        ),
        "media-state-1",
        authorization_actor="test",
        authorization_reference="media-proof",
    )
    second = repository.resolve_and_persist_scene_state(
        WORLD_ID,
        first.state_id,
        TransitionIntent(
            "media-intent-2",
            first.state_digest,
            SCENES[2],
            (
                Operation("set_variant", "actor", "actor-c"),
                Operation("attach", "report", ("table", Affine.translate(4, -1))),
                Operation("set_state", "report", "reviewed"),
                Operation("set_transform", "occluder", Affine.translate(17.5, 7.5)),
            ),
            (),
            "persistent media proof state two",
        ),
        "media-state-2",
        authorization_actor="test",
        authorization_reference="media-proof",
    )
    return base, first, second


def _audio(runtime: FfmpegRuntime, path: Path, duration_ms: int) -> bytes:
    runtime._run(
        [
            runtime.ffmpeg_path,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=440:sample_rate=48000:duration={duration_ms / 1000:.3f}",
            "-c:a",
            "pcm_s16le",
            str(path),
        ]
    )
    return path.read_bytes()


def _proof(tmp_path, runtime: FfmpegRuntime | None = None):
    repository, world, base, script = _persistent_world(tmp_path)
    states = _states(repository, base)
    active_runtime = runtime or _runtime_or_skip()
    service = MediaService(repository, active_runtime, LocalMediaStorage(tmp_path / "media"))
    narration = service.import_narration(
        "persistent-media-narration",
        script.id,
        _audio(active_runtime, tmp_path / "proof.wav", 1500),
        "audio/wav",
    )
    inputs = [
        {
            "scene_id": scene_id,
            "resolved_state_id": state.state_id,
            "duration_ms": 500,
            "motion": "static",
            "transition_to_next": "cut" if index < 2 else None,
        }
        for index, (scene_id, state) in enumerate(zip(SCENES, states, strict=True))
    ]
    snapshot = service.create_persistent_scene_snapshot(
        "persistent-media-snapshot", world.bindings.visual_plan_id, narration.id, inputs
    )
    return repository, service, world, states, snapshot


def test_v2_snapshot_freezes_exact_states_and_deterministic_frames(tmp_path) -> None:
    repository, service, world, states, snapshot = _proof(tmp_path)
    try:
        assert snapshot.snapshot_schema_version == "v2"
        assert [item["resolved_state_id"] for item in snapshot.scene_inputs] == [
            state.state_id for state in states
        ]
        assert all(item["motion"] == "static" for item in snapshot.scene_inputs)
        assert all("asset_selection_id" not in item for item in snapshot.scene_inputs)
        for item in snapshot.scene_inputs:
            first = service._persistent_scene_frame(item)
            second = service._persistent_scene_frame(item)
            assert first == second
            assert sha256(first).hexdigest() == item["encoded_frame_digest"]
            assert item["world_definition_digest"] == world.definition_digest
            assert item["compositor"] == compositor_contract()
    finally:
        repository.close()


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("world_definition_digest", "0" * 64, "identity or digest"),
        ("complete_state_digest", "1" * 64, "identity or digest"),
        ("admission_catalog_id", "wrong-catalog", "identity or digest"),
        ("scene_id", SCENES[1], "Scene"),
        ("compositor_digest", "2" * 64, "identity or digest"),
        ("composited_frame_digest", "3" * 64, "identity or digest"),
    ],
)
def test_v2_render_blocks_frozen_binding_substitution(tmp_path, field, value, message) -> None:
    repository, service, _, _, snapshot = _proof(tmp_path)
    try:
        item = deepcopy(snapshot.scene_inputs[0])
        item[field] = value
        with pytest.raises(MediaRuntimeError, match=message):
            service._persistent_scene_frame(item)
    finally:
        repository.close()


def test_v2_creation_rejects_missing_duplicate_wrong_scene_and_cross_plan(tmp_path) -> None:
    repository, service, world, states, snapshot = _proof(tmp_path)
    try:
        base_inputs = [
            {
                "scene_id": scene_id,
                "resolved_state_id": state.state_id,
                "duration_ms": 500,
                "motion": "static",
                "transition_to_next": "cut" if index < 2 else None,
            }
            for index, (scene_id, state) in enumerate(zip(SCENES, states, strict=True))
        ]
        with pytest.raises(ValueError, match="Every current"):
            service.create_persistent_scene_snapshot(
                "missing",
                world.bindings.visual_plan_id,
                snapshot.narration_asset_id,
                base_inputs[:2],
            )
        duplicate = deepcopy(base_inputs)
        duplicate[1]["resolved_state_id"] = duplicate[0]["resolved_state_id"]
        with pytest.raises(ValueError, match="unique exact"):
            service.create_persistent_scene_snapshot(
                "duplicate", world.bindings.visual_plan_id, snapshot.narration_asset_id, duplicate
            )
        wrong_scene = deepcopy(base_inputs)
        wrong_scene[1]["resolved_state_id"] = states[2].state_id
        with pytest.raises(ValueError, match="another editorial Scene"):
            service.create_persistent_scene_snapshot(
                "wrong-scene",
                world.bindings.visual_plan_id,
                snapshot.narration_asset_id,
                wrong_scene,
            )
        foreign_plan, foreign_script = _ready_visual_plan(repository, "persistent-media-foreign")
        foreign_inputs = deepcopy(base_inputs)
        for sequence, item in enumerate(foreign_inputs, 1):
            foreign_scene = repository.create_scene_under_visual_plan_authorization(
                f"persistent-media-foreign-scene-{sequence}",
                foreign_plan.id,
                sequence,
                f"Foreign excerpt {sequence}",
                f"Foreign intent {sequence}",
            )
            item["scene_id"] = foreign_scene.id
        foreign_narration = service.import_narration(
            "persistent-media-foreign-narration",
            foreign_script.id,
            service.narration_content(snapshot.narration_asset_id),
            "audio/wav",
        )
        with pytest.raises(ValueError, match="another VisualPlan"):
            service.create_persistent_scene_snapshot(
                "cross-plan", foreign_plan.id, foreign_narration.id, foreign_inputs
            )
    finally:
        repository.close()


def test_v2_render_blocks_selected_source_byte_tamper(tmp_path) -> None:
    repository, service, _, _, snapshot = _proof(tmp_path)
    try:
        asset_id = snapshot.scene_inputs[0]["source_assets"][0]["asset_id"]
        path = repository.managed_asset_path(asset_id)
        original = path.read_bytes()
        path.write_bytes(original + b"tamper")
        with pytest.raises(ValueError, match="bytes do not match"):
            service._persistent_scene_frame(snapshot.scene_inputs[0])
    finally:
        repository.close()


def test_v2_render_blocks_state_payload_asset_and_compositor_substitution(tmp_path) -> None:
    repository, service, _, _, snapshot = _proof(tmp_path)
    try:
        original = snapshot.scene_inputs[0]
        substituted = deepcopy(original)
        substituted["resolved_state_id"] = "media-state-1"
        with pytest.raises(MediaRuntimeError, match="identity or digest"):
            service._persistent_scene_frame(substituted)

        payload_changed = deepcopy(original)
        payload_changed["scene_model_snapshot"]["complete_state_digest"] = "0" * 64
        with pytest.raises(MediaRuntimeError, match="payload differs"):
            service._persistent_scene_frame(payload_changed)

        assets_changed = deepcopy(original)
        assets_changed["source_assets"] = []
        with pytest.raises(MediaRuntimeError, match="source Asset set"):
            service._persistent_scene_frame(assets_changed)

        compositor_changed = deepcopy(original)
        compositor_changed["compositor"]["identity"] = "mutable-latest-compositor"
        with pytest.raises(MediaRuntimeError, match="compositor contract"):
            service._persistent_scene_frame(compositor_changed)

        unknown = deepcopy(original)
        unknown["latest_state"] = True
        with pytest.raises(MediaRuntimeError, match="unknown or missing"):
            service._persistent_scene_frame(unknown)
    finally:
        repository.close()


def test_unrelated_later_state_does_not_change_frozen_render(tmp_path) -> None:
    repository, service, _, states, snapshot = _proof(tmp_path)
    try:
        before = service._persistent_scene_frame(snapshot.scene_inputs[0])
        repository.resolve_and_persist_scene_state(
            WORLD_ID,
            states[0].state_id,
            TransitionIntent(
                "media-sibling-intent",
                states[0].state_digest,
                SCENES[1],
                (Operation("set_visible", "spark", True),),
                (),
                "unrelated sibling",
            ),
            "media-sibling-state",
            authorization_actor="test",
            authorization_reference="sibling-proof",
        )
        assert service._persistent_scene_frame(snapshot.scene_inputs[0]) == before
    finally:
        repository.close()


def test_three_state_v2_final_media_render(tmp_path) -> None:
    runtime = _runtime_or_skip()
    repository, service, _, states, snapshot = _proof(tmp_path, runtime)
    try:
        artifact = service.render(
            "persistent-media-execution", "persistent-media-artifact", snapshot.id
        )
        probe = runtime.probe(service.storage.path(artifact.storage_path))
        assert (probe.width, probe.height, probe.video_codec, probe.audio_codec) == (
            1080,
            1920,
            "h264",
            "aac",
        )
        assert probe.duration_ms == 1500
        assert artifact.duration_ms == 1500
        assert len(states) == 3
        assert repository.get_render_execution("persistent-media-execution").outcome == "succeeded"
    finally:
        repository.close()


def test_png_encoder_rejects_invalid_frame_size(tmp_path) -> None:
    repository, _, _, states, _ = _proof(tmp_path)
    try:
        frame = load_persistent_scene_frame(repository, states[0].state_id)
        assert frame.png.startswith(b"\x89PNG\r\n\x1a\n")
        assert sha256(frame.png).hexdigest() == frame.png_digest
    finally:
        repository.close()
