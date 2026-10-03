"""Canonical v2 production lifecycle integration tests; every provider is fake."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from project_atlas.generation import GeneratedArtifact, GenerationFailure
from project_atlas.media import MediaService, NarrationSynthesis
from project_atlas.production import (
    DERIVED_RASTER_NAMESPACE,
    SCENE_ADAPTER_VERSION,
    ManagedAssetSceneAdapter,
    ProductionLifecycleService,
)
from project_atlas.scene_media import load_persistent_scene_frame, unwritten_alpha_pixels
from project_atlas.scene_model import Affine
from project_atlas.web import create_server
from tests.test_web import (
    MEDIA_PNG,
    create_authorized_visual_plan,
    ensure_character_reference_set,
    media_runtime_or_skip,
    post_json,
)

# The dimensions gpt-image-2 returned for the approved SimilarStoic beats.
REALISTIC_SOURCE_SIZE = (941, 1672)
HAMSTER_PROFILE = "character-profile-similarstoic-hamster-core-v1"


def realistic_source_png(runtime, tmp_path: Path) -> bytes:
    """Render one deterministic, detailed 941x1672 PNG with the local FFmpeg only."""

    path = tmp_path / "realistic-source.png"
    width, height = REALISTIC_SOURCE_SIZE
    runtime._run(
        [
            runtime.ffmpeg_path,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"testsrc2=size={width + 1}x{height}:rate=1,crop={width}:{height}:0:0,format=rgb24",
            "-frames:v",
            "1",
            str(path),
        ]
    )
    return path.read_bytes()


class ValidFakeImageGenerator:
    """Return one decodable image and retain exact provider-free call count."""

    generator_key = "fake-v2-image"

    def __init__(
        self,
        failure: GenerationFailure | None = None,
        content: bytes = MEDIA_PNG,
        fail_on_calls: frozenset[int] = frozenset(),
    ) -> None:
        self.failure = failure
        self.content = content
        self.fail_on_calls = fail_on_calls
        self.inputs = []

    def supports(self, asset_type: str) -> bool:
        return asset_type in {"environment", "character", "graphic", "prop"}

    def generate(self, generation_input):
        self.inputs.append(generation_input)
        if self.failure:
            raise self.failure
        if len(self.inputs) in self.fail_on_calls:
            raise GenerationFailure("offline scheduled failure")
        return GeneratedArtifact(self.content, "image/png", provider_key="offline-fake")


def _server(tmp_path: Path, generator: ValidFakeImageGenerator, runtime=None):
    return create_server(
        port=0,
        database_path=tmp_path / "lifecycle.db",
        generator=generator,
        asset_storage_root=tmp_path / "assets",
        media_runtime=runtime or media_runtime_or_skip(),
        media_storage_root=tmp_path / "media",
    )


def _request(
    server,
    tmp_path: Path,
    prefix: str,
    *,
    image_calls: int = 2,
    narration_authorized: bool = True,
    character_profile_id: str | None = HAMSTER_PROFILE,
    intrinsic_size_wu: tuple[int, int] = (1080, 1920),
) -> tuple[dict, list[tuple[str, str, str]]]:
    repository = server.repository
    plan = create_authorized_visual_plan(server, prefix)
    variants = []
    review_keys = []
    scene_ids = []
    for sequence, variant_key in enumerate(("start", "finish"), 1):
        scene = repository.create_scene_under_visual_plan_authorization(
            f"{prefix}-scene-{sequence}",
            plan.id,
            sequence,
            f"Narration {sequence}",
            f"Visual intent {sequence}",
        )
        scene_ids.append(scene.id)
        spec = repository.create_asset_spec_under_scene_authorization(
            f"{prefix}-spec-{sequence}",
            scene.id,
            "character" if character_profile_id else "graphic",
            "Explain the current narration beat.",
            f"Canonical world state {sequence}",
            f"Draw state {sequence} without text.",
            character_profile_id=character_profile_id,
        )
        variants.append(
            {
                "key": variant_key,
                "asset_spec_id": spec.id,
                "intrinsic_size_wu": list(intrinsic_size_wu),
            }
        )
        review_keys.append(("main-world", "explanation", variant_key))
    reference_set_id = ensure_character_reference_set(server, tmp_path / "assets")
    repository.create_visual_reference_authority(
        "visual-reference-authority-similarstoic-global-illustration-v1",
        "similarstoic-global-illustration",
        "global_illustration_style",
        "Offline lifecycle authority",
        "Use the managed fixture only as an offline style authority.",
        [("asset-http-reference-basis-v1", "style")],
    )
    return (
        {
            "id": prefix,
            "visual_plan_id": plan.id,
            "authority": {
                "character_profile_id": "character-profile-similarstoic-hamster-core-v1",
                "character_reference_set_id": reference_set_id,
                "visual_reference_authority_id": (
                    "visual-reference-authority-similarstoic-global-illustration-v1"
                ),
                "visual_style_profile_id": "visual-style-profile-similarstoic-core-v3",
            },
            "worlds": [
                {
                    "key": "main-world",
                    "scene_ids": scene_ids,
                    "visual_treatment": {
                        "style_profile_id": "visual-style-profile-similarstoic-core-v3",
                        "palette_id": "similarstoic-core-v3",
                        "wall_treatment_id": "off-white-negative-space-v1",
                        "lighting_policy_id": "flat-soft-light-v1",
                    },
                    "entities": [
                        {
                            "key": "explanation",
                            "semantic_role": "graphic",
                            "persistence_class": "STATEFUL_STATIC",
                            "purpose": "Carry the explanation across both scenes.",
                            "neutral_scale_id": "full-frame-v1",
                            "initial_variant_key": "start",
                            "initial_transform": {},
                            "variants": variants,
                        }
                    ],
                    "transitions": [
                        {
                            "scene_id": scene_ids[1],
                            "reason": "Advance the explanation to its concluding state.",
                            "operations": [
                                {
                                    "action": "set_variant",
                                    "entity_key": "explanation",
                                    "value": "finish",
                                }
                            ],
                        }
                    ],
                }
            ],
            "timeline": [
                {
                    "scene_id": scene_ids[0],
                    "duration_weight": 1,
                    "transition_to_next": "crossfade",
                },
                {
                    "scene_id": scene_ids[1],
                    "duration_weight": 1,
                    "transition_to_next": None,
                },
            ],
            "forecast": {
                "image_calls": image_calls,
                "narration_calls": 1,
                "real_provider_calls": 0,
            },
            "narration_authorized": narration_authorized,
        },
        review_keys,
    )


def _post_error(server, path: str, payload: dict) -> tuple[dict, int]:
    request = Request(
        f"http://{server.server_address[0]}:{server.server_address[1]}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    import threading

    thread = threading.Thread(target=server.handle_request)
    thread.start()
    try:
        urlopen(request)
    except HTTPError as error:
        result = json.loads(error.read())
        status = error.code
    else:
        raise AssertionError("Expected lifecycle failure")
    thread.join(timeout=2)
    return result, status


def _passing_reviews(review_keys) -> dict:
    return {
        "reviews": [
            {
                "world_key": world,
                "entity_key": entity,
                "variant_key": variant,
                "outcome": "passed",
                "evidence": {"source_quality": "passed", "semantic_support": "passed"},
            }
            for world, entity, variant in review_keys
        ]
    }


def _fake_narration(monkeypatch, wav_path: Path, calls: list[str] | None = None) -> None:
    def synthesize(engine, text):
        if calls is not None:
            calls.append(text)
        assert engine.execution_authorized
        assert text == "Narration."
        return NarrationSynthesis(
            wav_path.read_bytes(),
            "audio/wav",
            engine.engine_kind,
            engine.engine_identity,
            engine.voice_identity,
            engine.locale,
            engine.settings,
        )

    monkeypatch.setattr(
        "project_atlas.narration.InworldNarrationSynthesizer.synthesize", synthesize
    )


def _sine_wav(runtime, tmp_path: Path) -> Path:
    wav_path = tmp_path / "narration.wav"
    runtime._run(
        [
            runtime.ffmpeg_path,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=48000:duration=1",
            "-c:a",
            "pcm_s16le",
            str(wav_path),
        ]
    )
    return wav_path


def test_canonical_v2_http_lifecycle_is_resumable_and_founder_distinct(
    tmp_path, monkeypatch
) -> None:
    runtime = media_runtime_or_skip()
    generator = ValidFakeImageGenerator(content=realistic_source_png(runtime, tmp_path))
    server = _server(tmp_path, generator, runtime)
    _fake_narration(monkeypatch, _sine_wav(runtime, tmp_path))
    try:
        request, review_keys = _request(server, tmp_path, "canonical-v2-proof")
        started, status = post_json(server, "/api/v2/productions", request)
        assert status == 201
        assert started["production"]["status"] == "acquisition_review_pending"
        assert len(generator.inputs) == 2

        duplicate, status = post_json(server, "/api/v2/productions", request)
        assert status == 201
        assert duplicate["production"]["request_digest"] == started["production"]["request_digest"]
        assert len(generator.inputs) == 2

        try:
            reviewed, status = post_json(
                server,
                "/api/v2/productions/canonical-v2-proof/acquisition-review",
                _passing_reviews(review_keys),
            )
        except HTTPError as error:
            raise AssertionError(error.read().decode()) from error
        assert status == 200
        production = reviewed["production"]
        assert production["status"] == "qa_review_pending"
        evidence_types = {item["type"] for item in production["evidence"]}
        assert {
            "acquisition",
            "world",
            "scene_state",
            "narration",
            "snapshot",
            "render",
        } <= evidence_types
        snapshot_id = next(
            item["references"]["final_media_input_snapshot_id"]
            for item in production["evidence"]
            if item["type"] == "snapshot"
        )
        snapshot = server.repository.get_final_media_input_snapshot(snapshot_id)
        assert snapshot.snapshot_schema_version == "v2"
        assert all(
            item["render_source_kind"] == "persistent_scene_state" for item in snapshot.scene_inputs
        )
        # New canonical v2 snapshots freeze the explicit v3 encode profile.
        assert snapshot.render_settings["profile"] == "similarstoic-vertical-v3"
        assert snapshot.render_settings["encode"] == MediaService.PERSISTENT_ENCODE_PROFILE

        # Realistic 941x1672 sources are resampled once to exact frame pixels by a versioned
        # adapter, and every composited frame is fully covered (the old path left a grid).
        for item in snapshot.scene_inputs:
            frame = load_persistent_scene_frame(server.repository, item["resolved_state_id"])
            assert (frame.width, frame.height) == (1080, 1920)
            assert unwritten_alpha_pixels(frame.rgba) == 0
            for source in item["source_assets"]:
                derived = server.repository.get_asset(source["asset_id"])
                assert f":{DERIVED_RASTER_NAMESPACE}:" in derived.id
                assert derived.metadata["adapter"] == SCENE_ADAPTER_VERSION
                assert derived.metadata["scale_method"] == "ffmpeg-lanczos-bitexact"
                assert (derived.metadata["source_width"], derived.metadata["source_height"]) == (
                    REALISTIC_SOURCE_SIZE
                )
                assert (derived.metadata["width"], derived.metadata["height"]) == (1080, 1920)

        artifact_id = next(
            item["references"]["final_media_artifact_id"]
            for item in production["evidence"]
            if item["type"] == "render"
        )
        artifact = server.repository.get_final_media_artifact(artifact_id)
        content = (tmp_path / "media" / artifact.storage_path).read_bytes()
        assert b"crf=18.0" in content
        audio = next(
            stream
            for stream in runtime.probe(tmp_path / "media" / artifact.storage_path).raw["streams"]
            if stream["codec_type"] == "audio"
        )
        assert (audio["sample_rate"], audio["channels"]) == ("48000", 1)

        assert (
            server.repository.get_narration_generation_execution(
                f"{request['id']}:narration-execution:1"
            ).voice_identity
            == "Daniel"
        )
        cell_reviews = [
            review
            for review in server.repository.list_production_qa_reviews(request["id"])
            if review.scope == "cell"
        ]
        assert len(cell_reviews) == 1
        assert cell_reviews[0].outcome == "passed"
        assert cell_reviews[0].profile == MediaService.AUTOMATED_CELL_QA_PROFILE
        assert "source_composite_encode_edge_proof" not in json.dumps(cell_reviews[0].profile)
        coverage = cell_reviews[0].evidence[MediaService.COMPOSITOR_COVERAGE_POLICY]
        assert set(coverage["unwritten_alpha_pixels_by_scene"].values()) == {0}
        assert production["founder_review"] is None

        ready, status = post_json(
            server,
            "/api/v2/productions/canonical-v2-proof/qa",
            {
                "outcome": "passed",
                "evidence": {"normal_speed": "passed", "phone_scale": "passed"},
            },
        )
        assert status == 200
        assert ready["production"]["status"] == "private_founder_review_ready"
        assert ready["production"]["founder_review"] is None

        rejected, status = post_json(
            server,
            "/api/v2/productions/canonical-v2-proof/founder-review",
            {
                "outcome": "rejected",
                "founder_actor": "founder",
                "decision_reference": "private-review-1",
                "notes": "Creative rejection remains distinct from technical completion.",
            },
        )
        assert status == 200
        assert rejected["production"]["status"] == "founder_rejected"
        assert rejected["production"]["founder_review"]["outcome"] == "rejected"
        assert server.repository.connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert (
            server.repository.connection.execute(
                "SELECT MAX(version) FROM schema_migrations"
            ).fetchone()[0]
            == 28
        )
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            server.repository.connection.execute(
                "UPDATE production_runs SET visual_plan_id=visual_plan_id WHERE id=?",
                (request["id"],),
            )
        server.repository.connection.rollback()
    finally:
        server.server_close()


def test_canonical_v2_acquisition_failure_is_persisted_and_fail_closed(tmp_path) -> None:
    generator = ValidFakeImageGenerator(GenerationFailure("offline controlled failure"))
    server = _server(tmp_path, generator)
    try:
        request, _review_keys = _request(server, tmp_path, "canonical-v2-failure", image_calls=3)
        failed, status = _post_error(server, "/api/v2/productions", request)
        assert status == 422
        assert failed["stage"] == "acquisition"
        assert failed["production"]["status"] == "failed"
        assert failed["production"]["error"]["code"] == "RuntimeError"
        assert server.repository.list_production_evidence(request["id"], "world") == []
        assert server.repository.list_production_evidence(request["id"], "narration") == []
        generator.failure = None
        resumed, status = post_json(server, "/api/v2/productions/canonical-v2-failure/resume", {})
        assert status == 200
        assert resumed["production"]["status"] == "acquisition_review_pending"
        assert len(generator.inputs) == 3
        successful = [
            item
            for item in server.repository.list_production_evidence(request["id"], "acquisition")
            if item.asset_id is not None
        ]
        assert len(successful) == 2
    finally:
        server.server_close()


def test_full_frame_guard_rejects_the_historical_grid_mapping() -> None:
    """The exact pre-fix 941x1672 -> 1080x1920 upscale can no longer reach the compositor."""

    width, height = REALISTIC_SOURCE_SIZE
    historical = Affine(a=1080 / width, d=1920 / height)
    with pytest.raises(ValueError, match="upscale"):
        ProductionLifecycleService._guard_layer_mapping(historical, True)
    with pytest.raises(ValueError, match="upscale"):
        ProductionLifecycleService._guard_layer_mapping(historical, False)
    with pytest.raises(ValueError, match="exact 1:1"):
        ProductionLifecycleService._guard_layer_mapping(Affine(a=0.5, d=0.5), True)
    # Downscaled, non-full-frame layers stay legitimate.
    ProductionLifecycleService._guard_layer_mapping(Affine(a=0.5, d=0.5), False)
    ProductionLifecycleService._guard_layer_mapping(Affine(), True)


def test_unwritten_alpha_pixels_counts_only_zero_alpha() -> None:
    assert unwritten_alpha_pixels(bytes([1, 2, 3, 255, 0, 0, 0, 0, 9, 9, 9, 1])) == 1
    assert unwritten_alpha_pixels(bytes([0, 0, 0, 255] * 4)) == 0
    with pytest.raises(ValueError):
        unwritten_alpha_pixels(b"\x00\x00\x00")


def test_pre_fix_derived_rasters_are_never_reused(tmp_path) -> None:
    runtime = media_runtime_or_skip()
    generator = ValidFakeImageGenerator(content=realistic_source_png(runtime, tmp_path))
    server = _server(tmp_path, generator, runtime)
    try:
        request, _keys = _request(server, tmp_path, "stale-raster")
        post_json(server, "/api/v2/productions", request)
        repository = server.repository
        source = repository.get_asset(
            repository.list_production_evidence(request["id"], "acquisition")[0].asset_id
        )
        repository.create_asset(
            "stale-raster:raster:1:1:1",
            source.asset_spec_id,
            99,
            "persistent-derived/stale-raster/legacy.rgba",
            "application/x-rgba",
            "derived",
            {"adapter": "managed-image-to-rgba-v1", "source_asset_id": source.id},
            "0" * 64,
        )
        adapter = ManagedAssetSceneAdapter(repository, runtime)
        with pytest.raises(ValueError, match="another adapter version"):
            adapter.adapt("stale-raster", source.id, "stale-raster:raster:1:1:1", (1080, 1920))
    finally:
        server.server_close()


@pytest.mark.parametrize("mismatch", ["style", "global"])
def test_authority_mismatch_blocks_generation_before_any_provider_call(tmp_path, mismatch) -> None:
    generator = ValidFakeImageGenerator()
    server = _server(tmp_path, generator)
    try:
        request, _keys = _request(server, tmp_path, f"authority-{mismatch}")
        if mismatch == "style":
            request["authority"][
                "visual_style_profile_id"
            ] = "visual-style-profile-similarstoic-core-v2"
        else:
            server.repository.create_visual_reference_authority(
                "visual-reference-authority-offline-other-global-v1",
                "offline-other-global",
                "global_illustration_style",
                "Other offline authority",
                "A different global authority.",
                [("asset-http-reference-basis-v1", "style")],
            )
            request["authority"][
                "visual_reference_authority_id"
            ] = "visual-reference-authority-offline-other-global-v1"
        failed, status = _post_error(server, "/api/v2/productions", request)
        assert status == 422
        assert failed["stage"] == "acquisition"
        assert "differs from the production authority" in failed["error"]
        assert generator.inputs == []
    finally:
        server.server_close()


def test_execution_provenance_mismatch_after_generation_is_not_admitted(
    tmp_path, monkeypatch
) -> None:
    generator = ValidFakeImageGenerator()
    server = _server(tmp_path, generator)
    try:
        request, _keys = _request(server, tmp_path, "execution-mismatch")
        other = server.repository.get_visual_style_profile(
            "visual-style-profile-similarstoic-core-v2"
        )
        monkeypatch.setattr(
            server.generation_service, "_active_visual_style_profile", lambda: other
        )
        failed, status = _post_error(server, "/api/v2/productions", request)
        assert status == 422
        assert "different visual style profile" in failed["error"]
        assert len(generator.inputs) == 1
        evidence = server.repository.list_production_evidence(request["id"], "acquisition")
        assert len(evidence) == 1
        assert evidence[0].generation_execution_id is not None
        assert evidence[0].asset_id is None
        assert "authority_mismatch" in evidence[0].payload
    finally:
        server.server_close()


def test_forecast_ceiling_below_variant_count_is_rejected_at_creation(tmp_path) -> None:
    generator = ValidFakeImageGenerator()
    server = _server(tmp_path, generator)
    try:
        request, _keys = _request(server, tmp_path, "forecast-small", image_calls=1)
        failed, status = _post_error(server, "/api/v2/productions", request)
        assert status == 400
        assert "image_calls" in failed["error"]
        assert generator.inputs == []
        with pytest.raises(KeyError):
            server.repository.get_production_run(request["id"])
        for forecast in ({"image_calls": 2}, {"image_calls": 2, "narration_calls": 2}):
            request["forecast"] = forecast
            _failed, status = _post_error(server, "/api/v2/productions", request)
            assert status == 400
    finally:
        server.server_close()


def test_failed_calls_count_toward_ceiling_and_block_the_next_provider_call(tmp_path) -> None:
    generator = ValidFakeImageGenerator(fail_on_calls=frozenset({1}))
    server = _server(tmp_path, generator)
    try:
        request, _keys = _request(server, tmp_path, "ceiling", image_calls=2)
        failed, status = _post_error(server, "/api/v2/productions", request)
        assert status == 422
        assert len(generator.inputs) == 1
        blocked, status = _post_error(server, "/api/v2/productions/ceiling/resume", {})
        assert status == 422
        assert "ceiling of 2 would be exceeded" in blocked["error"]
        # Call 1 failed and counted; call 2 acquired the first variant; call 3 never happened.
        assert len(generator.inputs) == 2
        acquired = [
            item
            for item in server.repository.list_production_evidence(request["id"], "acquisition")
            if item.asset_id is not None
        ]
        assert len(acquired) == 1
    finally:
        server.server_close()


def test_resume_neither_reacquires_nor_revalidates_forecast_against_remaining(
    tmp_path, monkeypatch
) -> None:
    generator = ValidFakeImageGenerator(fail_on_calls=frozenset({2}))
    server = _server(tmp_path, generator)
    try:
        request, _keys = _request(server, tmp_path, "resume-ceiling", image_calls=3)
        _failed, status = _post_error(server, "/api/v2/productions", request)
        assert status == 422
        assert len(generator.inputs) == 2

        def forbidden(*_args, **_kwargs):
            raise AssertionError("resume must not re-validate the frozen request")

        monkeypatch.setattr(ProductionLifecycleService, "_validate_request", forbidden)
        resumed, status = post_json(server, "/api/v2/productions/resume-ceiling/resume", {})
        assert status == 200
        assert resumed["production"]["status"] == "acquisition_review_pending"
        assert len(generator.inputs) == 3
        acquired = [
            (item.payload["variant_key"], item.asset_id)
            for item in server.repository.list_production_evidence(request["id"], "acquisition")
            if item.asset_id is not None
        ]
        assert sorted(key for key, _asset in acquired) == ["finish", "start"]
        again, status = post_json(server, "/api/v2/productions/resume-ceiling/resume", {})
        assert status == 200
        assert again["production"]["status"] == "acquisition_review_pending"
        assert len(generator.inputs) == 3
    finally:
        server.server_close()


def test_narration_requires_explicit_frozen_authorization(tmp_path, monkeypatch) -> None:
    runtime = media_runtime_or_skip()
    generator = ValidFakeImageGenerator(content=realistic_source_png(runtime, tmp_path))
    server = _server(tmp_path, generator, runtime)
    calls: list[str] = []
    _fake_narration(monkeypatch, _sine_wav(runtime, tmp_path), calls)
    try:
        request, review_keys = _request(
            server, tmp_path, "narration-blocked", narration_authorized=False
        )
        missing = {key: value for key, value in request.items() if key != "narration_authorized"}
        _failed, status = _post_error(server, "/api/v2/productions", missing)
        assert status == 400

        started, status = post_json(server, "/api/v2/productions", request)
        assert status == 201
        blocked, status = _post_error(
            server,
            "/api/v2/productions/narration-blocked/acquisition-review",
            _passing_reviews(review_keys),
        )
        assert status == 422
        assert blocked["stage"] == "narration"
        assert "not authorized" in blocked["error"]
        assert calls == []
        with pytest.raises(KeyError):
            server.repository.get_narration_generation_execution(
                "narration-blocked:narration-execution:1"
            )
    finally:
        server.server_close()


@pytest.mark.parametrize("profile", [None, "character-profile-offline-other-v1"])
def test_full_frame_beats_require_the_authority_character_before_any_call(
    tmp_path, profile
) -> None:
    generator = ValidFakeImageGenerator()
    server = _server(tmp_path, generator)
    try:
        if profile is not None:
            server.repository.create_character_profile(
                profile, "offline-other", 1, "Other", "Another character.", "Offline only."
            )
        request, _keys = _request(
            server, tmp_path, "full-frame-character", character_profile_id=profile
        )
        failed, status = _post_error(server, "/api/v2/productions", request)
        assert status == 422
        assert failed["stage"] == "acquisition"
        assert "Full-frame AssetSpec character profile" in failed["error"]
        assert generator.inputs == []
    finally:
        server.server_close()


def test_non_full_frame_characterless_variants_remain_allowed(tmp_path) -> None:
    generator = ValidFakeImageGenerator()
    server = _server(tmp_path, generator)
    try:
        request, _keys = _request(
            server,
            tmp_path,
            "partial-characterless",
            character_profile_id=None,
            intrinsic_size_wu=(540, 960),
        )
        started, status = post_json(server, "/api/v2/productions", request)
        assert status == 201
        assert started["production"]["status"] == "acquisition_review_pending"
        assert len(generator.inputs) == 2
    finally:
        server.server_close()


def test_character_spec_execution_without_character_provenance_is_not_admitted(
    tmp_path, monkeypatch
) -> None:
    generator = ValidFakeImageGenerator()
    server = _server(tmp_path, generator)
    try:
        request, _keys = _request(server, tmp_path, "missing-character-provenance")
        monkeypatch.setattr(server.generation_service, "_character_profile_for", lambda _spec: None)
        failed, status = _post_error(server, "/api/v2/productions", request)
        assert status == 422
        assert "different character authority" in failed["error"]
        assert len(generator.inputs) == 1
        evidence = server.repository.list_production_evidence(request["id"], "acquisition")
        assert len(evidence) == 1
        assert evidence[0].generation_execution_id is not None
        assert evidence[0].asset_id is None
        assert "authority_mismatch" in evidence[0].payload
    finally:
        server.server_close()


def test_characterless_spec_rejects_unexpected_character_provenance(tmp_path, monkeypatch) -> None:
    generator = ValidFakeImageGenerator()
    server = _server(tmp_path, generator)
    try:
        request, _keys = _request(
            server,
            tmp_path,
            "unexpected-character-provenance",
            character_profile_id=None,
            intrinsic_size_wu=(540, 960),
        )
        hamster = server.repository.get_character_profile(HAMSTER_PROFILE)
        monkeypatch.setattr(
            server.generation_service, "_character_profile_for", lambda _spec: hamster
        )
        failed, status = _post_error(server, "/api/v2/productions", request)
        assert status == 422
        assert "characterless spec" in failed["error"]
        assert len(generator.inputs) == 1
        evidence = server.repository.list_production_evidence(request["id"], "acquisition")
        assert len(evidence) == 1
        assert evidence[0].generation_execution_id is not None
        assert evidence[0].asset_id is None
    finally:
        server.server_close()
