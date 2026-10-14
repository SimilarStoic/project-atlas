"""Production progressions: character-free frames, extracted objects and the on-screen text hook."""

from __future__ import annotations

import pytest

from project_atlas.media import MediaService
from project_atlas.production import (
    FRAME_SIZE,
    ProductionLifecycleError,
    ProductionRequestError,
)
from project_atlas.scene_media import encode_rgba_png, load_persistent_scene_frame
from project_atlas.scene_model import RENDER_POLICY, RENDER_POLICY_ALPHA
from tests.test_production_lifecycle import (
    _LEGACY_NARRATOR,
    FIXTURE_EXCERPTS,
    FIXTURE_SCRIPT,
    HAMSTER_PROFILE,
    REALISTIC_SOURCE_SIZE,
    ValidFakeImageGenerator,
    _fake_narration,
    _passing_reviews,
    _server,
    _sine_wav,
    realistic_source_png,
    transcription,  # noqa: F401  (autouse: no test reaches the real recognizer)
)
from tests.test_web import (
    create_authorized_visual_plan,
    ensure_character_reference_set,
    media_runtime_or_skip,
    post_json,
)

HOOK = "WHY INVESTING FEELS POINTLESS AT FIRST"
OBJECT_CENTER = [700, 1300]


def _object_canvas() -> bytes:
    """A plain off-white 941x1672 canvas with one closed black-outlined coin-coloured square."""

    width, height = REALISTIC_SOURCE_SIZE
    paper, ink, fill = (250, 248, 240, 255), (20, 20, 20, 255), (214, 170, 60, 255)
    pixels = bytearray(bytes(paper) * (width * height))
    for y in range(400, 470):
        for x in range(300, 380):
            edge = y < 406 or y >= 464 or x < 306 or x >= 374
            offset = (y * width + x) * 4
            pixels[offset : offset + 4] = bytes(ink if edge else fill)
    return encode_rgba_png(width, height, bytes(pixels))


def _progression_request(server, tmp_path, prefix: str, *, base_character: bool = True):
    repository = server.repository
    plan = create_authorized_visual_plan(server, prefix, FIXTURE_SCRIPT)
    scenes = [
        repository.create_scene_under_visual_plan_authorization(
            f"{prefix}-scene-{index}",
            plan.id,
            index,
            FIXTURE_EXCERPTS[index - 1],
            f"Visual intent {index}",
            on_screen_text=HOOK if index == 1 else None,
        )
        for index in (1, 2)
    ]
    base = repository.create_asset_spec_under_scene_authorization(
        f"{prefix}-base",
        scenes[0].id,
        "character" if base_character else "environment",
        "A frozen full-frame base for both states.",
        "Base",
        "Draw the base without text.",
        character_profile_id=HAMSTER_PROFILE if base_character else None,
        metadata=None if base_character else {"character_free": True},
    )
    coin = repository.create_asset_spec_under_scene_authorization(
        f"{prefix}-coin",
        scenes[1].id,
        "prop",
        "An object added on the second state.",
        "Coin",
        "Draw one coin alone on a plain flat off-white background with a closed black outline.",
        metadata={"character_free": True},
    )
    reference_set_id = ensure_character_reference_set(server, tmp_path / "assets")
    repository.create_visual_reference_authority(
        "visual-reference-authority-similarstoic-global-illustration-v1",
        "similarstoic-global-illustration",
        "global_illustration_style",
        "Offline lifecycle authority",
        "Use the managed fixture only as an offline style authority.",
        [("asset-http-reference-basis-v1", "style")],
    )
    scene_ids = [scene.id for scene in scenes]
    request = {
        "id": prefix,
        "visual_plan_id": plan.id,
        "authority": {
            "character_profile_id": HAMSTER_PROFILE,
            "character_reference_set_id": reference_set_id,
            "visual_reference_authority_id": (
                "visual-reference-authority-similarstoic-global-illustration-v1"
            ),
            "visual_style_profile_id": "visual-style-profile-similarstoic-core-v4",
        },
        "worlds": [
            {
                "key": "run",
                "scene_ids": scene_ids,
                "visual_treatment": {
                    "style_profile_id": "visual-style-profile-similarstoic-core-v3",
                    "palette_id": "similarstoic-core-v3",
                    "wall_treatment_id": "off-white-negative-space-v1",
                    "lighting_policy_id": "flat-soft-light-v1",
                },
                "entities": [
                    {
                        "key": "base",
                        "semantic_role": "full-scene-illustration",
                        "persistence_class": "LOCKED_STATIC",
                        "purpose": "The frozen base of the run.",
                        "neutral_scale_id": "full-frame-v1",
                        "initial_variant_key": "base",
                        "initial_transform": {},
                        "variants": [
                            {
                                "key": "base",
                                "asset_spec_id": base.id,
                                "intrinsic_size_wu": list(FRAME_SIZE),
                            }
                        ],
                    },
                    {
                        "key": "coin",
                        "semantic_role": "added-object",
                        "persistence_class": "MOVABLE_PROP",
                        "purpose": "Appears on the second state and stays.",
                        "neutral_scale_id": "object-v1",
                        "initial_variant_key": "coin",
                        "initial_transform": {},
                        "initial_visible": False,
                        "depth": 1,
                        "variants": [
                            {
                                "key": "coin",
                                "asset_spec_id": coin.id,
                                "intrinsic_size_wu": list(FRAME_SIZE),
                                "object_center": OBJECT_CENTER,
                            }
                        ],
                    },
                ],
                "transitions": [
                    {
                        "scene_id": scene_ids[1],
                        "reason": "The coin appears.",
                        "operations": [
                            {"action": "set_visible", "entity_key": "coin", "value": True}
                        ],
                    }
                ],
            }
        ],
        "timeline": [
            {"scene_id": scene_ids[0], "duration_weight": 1, "transition_to_next": "cut"},
            {"scene_id": scene_ids[1], "duration_weight": 1, "transition_to_next": None},
        ],
        "forecast": {"image_calls": 2, "narration_calls": 1, "verification_calls": 1},
        "narration_authorized": True,
        "narrator": _LEGACY_NARRATOR,
        "render_policy": RENDER_POLICY_ALPHA,
        "on_screen_text_overlay": True,
    }
    keys = [("run", "base", "base"), ("run", "coin", "coin")]
    return request, keys


def _frame(server, run_id: str, scene_id: str):
    return load_persistent_scene_frame(server.repository, f"{run_id}:state:{scene_id}")


@pytest.mark.parametrize("base_character", [True, False])
def test_progression_admits_an_object_onto_a_frozen_base_and_renders_the_hook(
    tmp_path, monkeypatch, base_character
) -> None:
    runtime = media_runtime_or_skip()
    generator = ValidFakeImageGenerator(
        sequence=[realistic_source_png(runtime, tmp_path), _object_canvas()]
    )
    server = _server(tmp_path, generator, runtime)
    _fake_narration(monkeypatch, _sine_wav(runtime, tmp_path))
    prefix = "progression-char" if base_character else "progression-free"
    request, keys = _progression_request(server, tmp_path, prefix, base_character=base_character)
    try:
        created, status = post_json(server, "/api/v2/productions", request)
        assert status == 201, created
        # The character-free base was generated without any character reference.
        assert generator.inputs[0].character_references is None if not base_character else True
        reviewed, status = post_json(
            server,
            f"/api/v2/productions/{prefix}/acquisition-review",
            _passing_reviews(keys, server, prefix),
        )
        assert status == 200 and reviewed["production"]["status"] == "qa_review_pending", reviewed
        assert len(generator.inputs) == 2  # nothing regenerated
        scene_ids = request["timeline"]
        first = _frame(server, prefix, scene_ids[0]["scene_id"])
        second = _frame(server, prefix, scene_ids[1]["scene_id"])
        evidence = server.repository.list_production_evidence(prefix, "world")[0].payload
        [admission] = evidence["object_admissions"]
        left, top = admission["placed_at"]
        width, height = admission["size_px"]
        assert admission["size_px"] == [
            admission["crop_box"][2] - admission["crop_box"][0],
            admission["crop_box"][3] - admission["crop_box"][1],
        ]
        assert admission["outline_px"] and admission["base_outline_px"]
        changed = [
            index
            for index in range(FRAME_SIZE[0] * FRAME_SIZE[1])
            if first.rgba[index * 4 : index * 4 + 4] != second.rgba[index * 4 : index * 4 + 4]
        ]
        assert changed, "the object must appear on the second state"
        for index in changed:  # the base is frozen: only the object's own box changes
            x, y = index % FRAME_SIZE[0], index // FRAME_SIZE[0]
            assert left <= x < left + width and top <= y < top + height
        snapshot = server.repository.get_final_media_input_snapshot(
            server.repository.list_production_evidence(prefix, "snapshot")[
                0
            ].final_media_input_snapshot_id
        )
        settings = snapshot.render_settings
        assert settings["persistent_scene_compositor"]["render_policy"] == RENDER_POLICY_ALPHA
        assert all(
            item["compositor"]["render_policy"] == RENDER_POLICY_ALPHA
            for item in snapshot.scene_inputs
        )
        [hook] = settings["on_screen_text_overlay"]["texts"]
        assert hook["text"] == HOOK and hook["start_ms"] == 0
        assert hook["end_ms"] == snapshot.scene_inputs[0]["duration_ms"]
    finally:
        server.server_close()


def test_opt_in_fields_are_validated_before_any_provider_call(tmp_path) -> None:
    runtime = media_runtime_or_skip()
    generator = ValidFakeImageGenerator(content=realistic_source_png(runtime, tmp_path))
    server = _server(tmp_path, generator, runtime)
    service = server.production_service
    try:
        request, _keys = _progression_request(server, tmp_path, "validation")
        with pytest.raises(ProductionRequestError, match="may only opt in"):
            service._validate_request(request | {"render_policy": RENDER_POLICY})
        without_policy = {key: value for key, value in request.items() if key != "render_policy"}
        with pytest.raises(ProductionRequestError, match="Extracted objects require"):
            service._validate_request(without_policy)
        with pytest.raises(ProductionRequestError, match="on_screen_text_overlay must be true"):
            service._validate_request(request | {"on_screen_text_overlay": False})
        assert generator.inputs == []
    finally:
        server.server_close()


def test_on_screen_text_is_timed_to_its_scene_and_requires_one() -> None:
    inputs = [
        {"scene_id": "a", "duration_ms": 1500, "on_screen_text": HOOK},
        {"scene_id": "b", "duration_ms": 2000, "on_screen_text": None},
    ]
    assert MediaService.on_screen_text_overlays(inputs) == [
        {"scene_id": "a", "text": HOOK, "start_ms": 0, "end_ms": 1500}
    ]
    with pytest.raises(ValueError, match="requires a Scene"):
        MediaService.on_screen_text_overlays([inputs[1]])
    with pytest.raises(ValueError, match="1-60 plain characters"):
        MediaService.on_screen_text_overlays([{**inputs[0], "on_screen_text": "x" * 61}])


def _at_review_run(tmp_path, monkeypatch, prefix: str):
    runtime = media_runtime_or_skip()
    generator = ValidFakeImageGenerator(
        sequence=[realistic_source_png(runtime, tmp_path), _object_canvas()]
    )
    server = _server(tmp_path, generator, runtime)
    _fake_narration(monkeypatch, _sine_wav(runtime, tmp_path))
    request, keys = _progression_request(server, tmp_path, prefix)
    coin = request["worlds"][0]["entities"][1]["variants"][0]
    coin["object_center"] = "at_review"
    created, status = post_json(server, "/api/v2/productions", request)
    assert status == 201, created
    return server, generator, request, keys


def _reviews_with_center(server, keys, prefix, center=None, on=("run", "coin", "coin")):
    reviews = _passing_reviews(keys, server, prefix)
    for review in reviews["reviews"]:
        if center is not None and (
            review["world_key"],
            review["entity_key"],
            review["variant_key"],
        ) == tuple(on):
            review["evidence"]["object_center"] = center
    return reviews


def test_object_centre_set_at_review_is_recorded_and_used(tmp_path, monkeypatch) -> None:
    server, generator, request, keys = _at_review_run(tmp_path, monkeypatch, "at-review")
    try:
        reviewed, status = post_json(
            server,
            "/api/v2/productions/at-review/acquisition-review",
            _reviews_with_center(server, keys, "at-review", [520, 1500]),
        )
        assert status == 200 and reviewed["production"]["status"] == "qa_review_pending", reviewed
        [admission] = server.repository.list_production_evidence("at-review", "world")[0].payload[
            "object_admissions"
        ]
        assert admission["object_center"] == [520, 1500]
        width, height = admission["size_px"]
        assert admission["placed_at"] == [520 - width // 2, 1500 - height // 2]
        recorded = [
            review.evidence.get("object_center")
            for review in server.repository.list_production_qa_reviews("at-review")
        ]
        assert [520, 1500] in recorded
        assert len(generator.inputs) == 2
    finally:
        server.server_close()


def test_world_building_refuses_an_object_without_a_review_centre(tmp_path, monkeypatch) -> None:
    server, _generator, _request, keys = _at_review_run(tmp_path, monkeypatch, "no-centre")
    try:
        service = server.production_service
        with pytest.raises(ProductionLifecycleError, match="no founder-approved centre"):
            service.review_acquisition(
                "no-centre", _passing_reviews(keys, server, "no-centre")["reviews"]
            )
        status = service.status("no-centre")
        assert status["status"] == "failed"
        assert "no founder-approved centre" in status["error"]["message"]
        assert server.repository.list_production_evidence("no-centre", "world") == []
    finally:
        server.server_close()


def test_review_centres_are_refused_where_they_do_not_belong(tmp_path, monkeypatch) -> None:
    server, _generator, _request, keys = _at_review_run(tmp_path, monkeypatch, "misplaced")
    service = server.production_service
    try:
        for reviews in (
            _reviews_with_center(server, keys, "misplaced", [10, 10], on=("run", "base", "base")),
            _reviews_with_center(server, keys, "misplaced", [5000, 10]),
        ):
            with pytest.raises(ProductionRequestError, match="object_center is accepted only"):
                service.review_acquisition("misplaced", reviews["reviews"])
        failing = _reviews_with_center(server, keys, "misplaced", [100, 100])
        for review in failing["reviews"]:
            review["outcome"] = "failed"
        with pytest.raises(ProductionRequestError, match="object_center is accepted only"):
            service.review_acquisition("misplaced", failing["reviews"])
        assert server.repository.list_production_qa_reviews("misplaced") == []
    finally:
        server.server_close()
