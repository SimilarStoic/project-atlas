"""Canonical v2 production lifecycle integration tests; every provider is fake."""

from __future__ import annotations

import json
import sqlite3
from hashlib import sha256
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from project_atlas.generation import GeneratedArtifact, GenerationFailure
from project_atlas.media import MediaRuntimeError, MediaService, NarrationSynthesis
from project_atlas.production import (
    DERIVED_RASTER_NAMESPACE,
    SCENE_ADAPTER_VERSION,
    ManagedAssetSceneAdapter,
    ProductionLifecycleError,
    ProductionLifecycleService,
    ProductionRequestError,
)
from project_atlas.scene_media import (
    encode_rgba_png,
    load_persistent_scene_frame,
    unwritten_alpha_pixels,
)
from project_atlas.scene_model import Affine
from project_atlas.web import create_server
from tests.test_web import (
    create_authorized_visual_plan,
    ensure_character_reference_set,
    media_runtime_or_skip,
    post_json,
)

# The dimensions gpt-image-2 returned for the approved SimilarStoic beats.
REALISTIC_SOURCE_SIZE = (941, 1672)
HAMSTER_PROFILE = "character-profile-similarstoic-hamster-core-v1"
# A minimal technically admissible full-frame source (exact 9:16) for non-media tests.
NINE_BY_SIXTEEN_PNG = encode_rgba_png(9, 16, bytes([250, 248, 240, 255]) * 9 * 16)


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
        content: bytes = NINE_BY_SIXTEEN_PNG,
        fail_on_calls: frozenset[int] = frozenset(),
        sequence: list[bytes] | None = None,
    ) -> None:
        self.failure = failure
        self.content = content
        self.fail_on_calls = fail_on_calls
        self.sequence = sequence
        self.inputs = []

    def supports(self, asset_type: str) -> bool:
        return asset_type in {"environment", "character", "graphic", "prop"}

    def generate(self, generation_input):
        self.inputs.append(generation_input)
        if self.failure:
            raise self.failure
        if len(self.inputs) in self.fail_on_calls:
            raise GenerationFailure("offline scheduled failure")
        content = self.sequence[len(self.inputs) - 1] if self.sequence else self.content
        return GeneratedArtifact(content, "image/png", provider_key="offline-fake")


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


def _narration_authorization(server, run_id: str) -> list:
    return server.repository.list_production_evidence(run_id, "narration_authorization")


def test_recorded_founder_authorization_permits_exactly_one_narration(
    tmp_path, monkeypatch
) -> None:
    runtime = media_runtime_or_skip()
    generator = ValidFakeImageGenerator(content=realistic_source_png(runtime, tmp_path))
    server = _server(tmp_path, generator, runtime)
    calls: list[str] = []
    _fake_narration(monkeypatch, _sine_wav(runtime, tmp_path), calls)
    try:
        request, review_keys = _request(
            server, tmp_path, "narration-later", narration_authorized=False
        )
        started, status = post_json(server, "/api/v2/productions", request)
        assert status == 201
        assert started["production"]["narration_authorized"] is False
        run_before = server.repository.get_production_run("narration-later")
        image_calls = len(generator.inputs)

        path = "/api/v2/productions/narration-later/narration-authorization"
        _failed, status = _post_error(server, path, {"evidence": {}})
        assert status == 400
        assert _narration_authorization(server, "narration-later") == []

        evidence = {"authorized_by": "founder", "decision_reference": "offline-test"}
        authorized, status = post_json(server, path, {"evidence": evidence})
        assert status == 200
        assert authorized["production"]["narration_authorized"] is True
        # Authorization records evidence only; the lifecycle state is unchanged.
        assert authorized["production"]["status"] == "acquisition_review_pending"
        again, status = post_json(server, path, {"evidence": evidence})
        assert status == 200
        records = _narration_authorization(server, "narration-later")
        assert len(records) == 1 and records[0].payload == evidence
        assert calls == []

        reviewed, status = post_json(
            server,
            "/api/v2/productions/narration-later/acquisition-review",
            _passing_reviews(review_keys),
        )
        assert status == 200
        assert reviewed["production"]["status"] == "qa_review_pending"
        assert len(calls) == 1
        resumed, status = post_json(server, "/api/v2/productions/narration-later/resume", {})
        assert status == 200
        assert len(calls) == 1
        assert len(server.repository.list_production_evidence("narration-later", "narration")) == 1
        assert len(generator.inputs) == image_calls

        run_after = server.repository.get_production_run("narration-later")
        assert run_after.request == run_before.request
        assert run_after.request["narration_authorized"] is False
        assert run_after.request_digest == run_before.request_digest
    finally:
        server.server_close()


def test_authorization_after_a_blocked_narration_resumes_without_reacquisition(
    tmp_path, monkeypatch
) -> None:
    runtime = media_runtime_or_skip()
    generator = ValidFakeImageGenerator(content=realistic_source_png(runtime, tmp_path))
    server = _server(tmp_path, generator, runtime)
    calls: list[str] = []
    _fake_narration(monkeypatch, _sine_wav(runtime, tmp_path), calls)
    try:
        request, review_keys = _request(
            server, tmp_path, "narration-after-block", narration_authorized=False
        )
        _started, status = post_json(server, "/api/v2/productions", request)
        assert status == 201
        image_calls = len(generator.inputs)
        blocked, status = _post_error(
            server,
            "/api/v2/productions/narration-after-block/acquisition-review",
            _passing_reviews(review_keys),
        )
        assert status == 422 and blocked["stage"] == "narration"
        reviews = server.repository.list_production_qa_reviews("narration-after-block")
        assert {item.scope for item in reviews} == {"acquisition"}
        assert calls == []

        post_json(
            server,
            "/api/v2/productions/narration-after-block/narration-authorization",
            {"evidence": {"authorized_by": "founder"}},
        )
        resumed, status = post_json(server, "/api/v2/productions/narration-after-block/resume", {})
        assert status == 200
        assert resumed["production"]["status"] == "qa_review_pending"
        assert len(calls) == 1
        assert len(generator.inputs) == image_calls
        after = server.repository.list_production_qa_reviews("narration-after-block")
        assert [item for item in after if item.scope == "acquisition"] == reviews
    finally:
        server.server_close()


def test_frozen_request_authorization_needs_no_record(tmp_path, monkeypatch) -> None:
    runtime = media_runtime_or_skip()
    generator = ValidFakeImageGenerator(content=realistic_source_png(runtime, tmp_path))
    server = _server(tmp_path, generator, runtime)
    calls: list[str] = []
    _fake_narration(monkeypatch, _sine_wav(runtime, tmp_path), calls)
    try:
        request, review_keys = _request(server, tmp_path, "narration-frozen")
        started, status = post_json(server, "/api/v2/productions", request)
        assert status == 201 and started["production"]["narration_authorized"] is True
        authorized, status = post_json(
            server,
            "/api/v2/productions/narration-frozen/narration-authorization",
            {"evidence": {"authorized_by": "founder"}},
        )
        assert status == 200
        assert _narration_authorization(server, "narration-frozen") == []
        reviewed, status = post_json(
            server,
            "/api/v2/productions/narration-frozen/acquisition-review",
            _passing_reviews(review_keys),
        )
        assert reviewed["production"]["status"] == "qa_review_pending"
        assert len(calls) == 1
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


def sized_png(runtime, tmp_path: Path, width: int, height: int) -> bytes:
    """Render one deterministic PNG of an exact size with the local FFmpeg only."""

    path = tmp_path / f"source-{width}x{height}.png"
    runtime._run(
        [
            runtime.ffmpeg_path,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=white:s={width}x{height}:r=1,format=rgb24",
            "-frames:v",
            "1",
            str(path),
        ]
    )
    return path.read_bytes()


def _spec_of(generation_input) -> str:
    return generation_input.visual_authority_recipe["asset_spec_id"]


def _review(keys, outcome: str) -> list[dict]:
    return [
        {
            "world_key": world,
            "entity_key": entity,
            "variant_key": variant,
            "outcome": outcome,
            "evidence": {"source_quality": outcome},
        }
        for world, entity, variant in keys
    ]


def test_rejected_variant_is_reacquired_alone_and_later_rounds_supersede_it(
    tmp_path, monkeypatch
) -> None:
    runtime = media_runtime_or_skip()
    generator = ValidFakeImageGenerator(content=realistic_source_png(runtime, tmp_path))
    server = _server(tmp_path, generator, runtime)
    calls: list[str] = []
    _fake_narration(monkeypatch, _sine_wav(runtime, tmp_path), calls)
    try:
        request, keys = _request(server, tmp_path, "retry-round", image_calls=3)
        start_key, finish_key = keys
        post_json(server, "/api/v2/productions", request)
        assert [_spec_of(item) for item in generator.inputs] == [
            "retry-round-spec-1",
            "retry-round-spec-2",
        ]
        first_finish = server.production_service._acquisition_map("retry-round")[finish_key][
            "asset_id"
        ]

        rejected, status = post_json(
            server,
            "/api/v2/productions/retry-round/acquisition-review",
            {"reviews": _review([start_key], "passed") + _review([finish_key], "failed")},
        )
        assert status == 200
        assert rejected["production"]["status"] == "failed"
        assert rejected["production"]["stage"] == "acquisition_review"
        assert calls == []  # No narration while any active variant lacks a pass.

        resumed, status = post_json(server, "/api/v2/productions/retry-round/resume", {})
        assert status == 200
        assert resumed["production"]["status"] == "acquisition_review_pending"
        # Only the rejected variant was regenerated; the passed one was not.
        assert [_spec_of(item) for item in generator.inputs] == [
            "retry-round-spec-1",
            "retry-round-spec-2",
            "retry-round-spec-2",
        ]
        active = server.production_service._acquisition_map("retry-round")
        assert active[finish_key]["asset_id"] != first_finish

        # The second round must cover only the retried variant.
        both, status = _post_error(
            server,
            "/api/v2/productions/retry-round/acquisition-review",
            {"reviews": _review(keys, "passed")},
        )
        assert status == 400
        assert "awaiting review" in both["error"]
        assert calls == []

        passed, status = post_json(
            server,
            "/api/v2/productions/retry-round/acquisition-review",
            {"reviews": _review([finish_key], "passed")},
        )
        assert status == 200
        assert passed["production"]["status"] == "qa_review_pending"
        assert len(calls) == 1

        reviews = [
            review
            for review in server.repository.list_production_qa_reviews("retry-round")
            if review.scope == "acquisition"
        ]
        # History is preserved: the failed first-round review still exists, round-scoped.
        assert sorted((review.id, review.outcome) for review in reviews) == [
            ("retry-round:qa:acquisition:round-1:1", "failed"),
            ("retry-round:qa:acquisition:round-1:2", "passed"),
            ("retry-round:qa:acquisition:round-2:1", "passed"),
        ]
        derived_sources = {
            server.repository.get_asset(source["asset_id"]).metadata["source_asset_id"]
            for item in server.repository.get_final_media_input_snapshot(
                next(
                    entry["references"]["final_media_input_snapshot_id"]
                    for entry in passed["production"]["evidence"]
                    if entry["type"] == "snapshot"
                )
            ).scene_inputs
            for source in item["source_assets"]
        }
        assert active[finish_key]["asset_id"] in derived_sources
        assert first_finish not in derived_sources
    finally:
        server.server_close()


def test_rejected_image_counts_toward_ceiling_and_blocks_retry_before_provider(tmp_path) -> None:
    generator = ValidFakeImageGenerator()
    server = _server(tmp_path, generator)
    try:
        request, keys = _request(server, tmp_path, "retry-ceiling", image_calls=2)
        post_json(server, "/api/v2/productions", request)
        post_json(
            server,
            "/api/v2/productions/retry-ceiling/acquisition-review",
            {"reviews": _review(keys[:1], "passed") + _review(keys[1:], "failed")},
        )
        blocked, status = _post_error(server, "/api/v2/productions/retry-ceiling/resume", {})
        assert status == 422
        assert "ceiling of 2 would be exceeded" in blocked["error"]
        assert len(generator.inputs) == 2
    finally:
        server.server_close()


def test_full_frame_aspect_guard_accepts_the_approved_source_shape(tmp_path) -> None:
    runtime = media_runtime_or_skip()
    generator = ValidFakeImageGenerator(content=realistic_source_png(runtime, tmp_path))
    server = _server(tmp_path, generator, runtime)
    try:
        request, _keys = _request(server, tmp_path, "aspect-ok")
        post_json(server, "/api/v2/productions", request)
        source_id = server.production_service._acquisition_map("aspect-ok")[
            ("main-world", "explanation", "start")
        ]["asset_id"]
        raster = ManagedAssetSceneAdapter(server.repository, runtime).adapt(
            "aspect-ok", source_id, "aspect-ok:raster-v2:test", (1080, 1920)
        )
        assert (raster.width, raster.height) == (1080, 1920)
    finally:
        server.server_close()


def test_off_aspect_full_frame_result_is_retried_before_founder_review(
    tmp_path, monkeypatch
) -> None:
    runtime = media_runtime_or_skip()
    realistic = realistic_source_png(runtime, tmp_path)
    square = sized_png(runtime, tmp_path, 1080, 1080)
    generator = ValidFakeImageGenerator(sequence=[realistic, square, realistic])
    server = _server(tmp_path, generator, runtime)
    calls: list[str] = []
    _fake_narration(monkeypatch, _sine_wav(runtime, tmp_path), calls)
    try:
        request, keys = _request(server, tmp_path, "aspect-admit", image_calls=3)
        started, status = post_json(server, "/api/v2/productions", request)
        assert status == 201
        assert started["production"]["status"] == "acquisition_review_pending"
        # The valid first variant was not regenerated; only the off-aspect one was retried.
        assert [_spec_of(item) for item in generator.inputs] == [
            "aspect-admit-spec-1",
            "aspect-admit-spec-2",
            "aspect-admit-spec-2",
        ]
        evidence = sorted(
            server.repository.list_production_evidence("aspect-admit", "acquisition"),
            key=lambda item: int(item.id.rsplit(":", 1)[1]),
        )
        assert [item.generation_execution_id is not None for item in evidence] == [True] * 3
        rejected = evidence[1]
        assert rejected.asset_id is None
        assert "frame aspect" in rejected.payload["technical_rejection"]
        # Only the admissible 941x1672 assets are presented for founder review.
        adapter = ManagedAssetSceneAdapter(server.repository, runtime)
        active = server.production_service._acquisition_map("aspect-admit")
        assert {adapter.source_dimensions(item["asset_id"]) for item in active.values()} == {
            REALISTIC_SOURCE_SIZE
        }
        assert set(
            server.production_service._variant_review_states(
                server.repository.get_production_run("aspect-admit")
            ).values()
        ) == {"pending"}
        assert calls == []
        passed, status = post_json(
            server,
            "/api/v2/productions/aspect-admit/acquisition-review",
            {"reviews": _review(keys, "passed")},
        )
        assert status == 200
        assert passed["production"]["status"] == "qa_review_pending"
        assert len(calls) == 1
    finally:
        server.server_close()


@pytest.mark.parametrize("size", [(1080, 1080), (1024, 1536)])
def test_repeated_off_aspect_results_stop_at_the_image_call_ceiling(
    tmp_path, monkeypatch, size
) -> None:
    runtime = media_runtime_or_skip()
    generator = ValidFakeImageGenerator(content=sized_png(runtime, tmp_path, *size))
    server = _server(tmp_path, generator, runtime)
    calls: list[str] = []
    _fake_narration(monkeypatch, _sine_wav(runtime, tmp_path), calls)
    try:
        request, _keys = _request(server, tmp_path, "aspect-ceiling", image_calls=2)
        failed, status = _post_error(server, "/api/v2/productions", request)
        assert status == 422
        assert failed["stage"] == "acquisition"
        assert "ceiling of 2 would be exceeded" in failed["error"]
        assert len(generator.inputs) == 2
        assert server.production_service._acquisition_map("aspect-ceiling") == {}
        assert calls == []
    finally:
        server.server_close()


def test_assembly_aspect_guard_remains_as_defense_in_depth(tmp_path) -> None:
    runtime = media_runtime_or_skip()
    generator = ValidFakeImageGenerator(content=sized_png(runtime, tmp_path, 400, 400))
    server = _server(tmp_path, generator, runtime)
    try:
        request, _keys = _request(
            server,
            tmp_path,
            "aspect-depth",
            character_profile_id=None,
            intrinsic_size_wu=(400, 400),
        )
        post_json(server, "/api/v2/productions", request)
        source_id = server.production_service._acquisition_map("aspect-depth")[
            ("main-world", "explanation", "start")
        ]["asset_id"]
        with pytest.raises(ValueError, match="frame aspect"):
            ManagedAssetSceneAdapter(server.repository, runtime).adapt(
                "aspect-depth", source_id, "aspect-depth:raster-v2:test", (1080, 1920)
            )
    finally:
        server.server_close()


def test_non_full_frame_sources_are_not_aspect_guarded(tmp_path) -> None:
    runtime = media_runtime_or_skip()
    generator = ValidFakeImageGenerator(content=sized_png(runtime, tmp_path, 400, 400))
    server = _server(tmp_path, generator, runtime)
    try:
        request, _keys = _request(
            server,
            tmp_path,
            "aspect-partial",
            character_profile_id=None,
            intrinsic_size_wu=(400, 400),
        )
        started, status = post_json(server, "/api/v2/productions", request)
        assert status == 201
        assert started["production"]["status"] == "acquisition_review_pending"
        assert len(generator.inputs) == 2
        assert all(
            "technical_rejection" not in item.payload
            for item in server.repository.list_production_evidence("aspect-partial", "acquisition")
        )
        source_id = server.production_service._acquisition_map("aspect-partial")[
            ("main-world", "explanation", "start")
        ]["asset_id"]
        raster = ManagedAssetSceneAdapter(server.repository, runtime).adapt(
            "aspect-partial", source_id, "aspect-partial:raster-v2:test", None
        )
        assert (raster.width, raster.height) == (400, 400)
    finally:
        server.server_close()


# --- Bounded post-narration retiming -------------------------------------------------------


def _forbid_providers(monkeypatch, generator) -> None:
    """After the first render, any image or narration provider call is a test failure."""

    def no_narration(*_args, **_kwargs):
        raise AssertionError("narration provider must not be called by a retime")

    monkeypatch.setattr(
        "project_atlas.narration.InworldNarrationSynthesizer.synthesize", no_narration
    )
    generator.failure = GenerationFailure("image provider must not be called by a retime")


def _render_ready_run(tmp_path, monkeypatch, prefix: str):
    runtime = media_runtime_or_skip()
    generator = ValidFakeImageGenerator(content=realistic_source_png(runtime, tmp_path))
    server = _server(tmp_path, generator, runtime)
    calls: list[str] = []
    _fake_narration(monkeypatch, _sine_wav(runtime, tmp_path), calls)
    request, keys = _request(server, tmp_path, prefix)
    post_json(server, "/api/v2/productions", request)
    reviewed, status = post_json(
        server, f"/api/v2/productions/{prefix}/acquisition-review", _passing_reviews(keys)
    )
    assert status == 200 and reviewed["production"]["status"] == "qa_review_pending"
    assert len(calls) == 1
    return server, generator, request


def _durations_for(server, run_id: str, count: int) -> list[int]:
    narration_id = server.repository.list_production_evidence(run_id, "narration")[
        0
    ].narration_asset_id
    total = server.repository.get_narration_asset(narration_id).duration_ms
    first = total // 3
    return [first, total - first] if count == 2 else [total]


def test_retime_rerenders_approved_inputs_and_rebinds_human_review(tmp_path, monkeypatch) -> None:
    server, generator, request = _render_ready_run(tmp_path, monkeypatch, "retime-flow")
    repository, service = server.repository, server.production_service
    try:
        run_id = request["id"]
        run_before = repository.get_production_run(run_id)
        # Normal first render: exactly one versioned render, snapshot and cell review.
        assert [e.id for e in repository.list_production_evidence(run_id, "render")] == [
            f"{run_id}:render:evidence:1"
        ]
        assert [
            r.id for r in repository.list_production_qa_reviews(run_id) if r.scope == "cell"
        ] == [f"{run_id}:qa:cell:1"]
        assert service.resume(run_id)["current_render"]["version"] == 1  # idempotent
        assert len(repository.list_production_evidence(run_id, "render")) == 1

        image_calls = len(generator.inputs)
        _forbid_providers(monkeypatch, generator)
        original_evidence = repository.list_production_evidence(run_id)
        original_reviews = repository.list_production_qa_reviews(run_id)
        original_snapshot = repository.get_final_media_input_snapshot(f"{run_id}:snapshot:1")
        original_artifact = repository.get_final_media_artifact(f"{run_id}-artifact-1")
        narration_id = repository.list_production_evidence(run_id, "narration")[
            0
        ].narration_asset_id
        durations = _durations_for(server, run_id, 2)

        retimed, status = post_json(
            server,
            f"/api/v2/productions/{run_id}/retime",
            {"durations_ms": durations, "actor": "founder", "reason": "Align cuts to pauses."},
        )
        assert status == 200
        production = retimed["production"]
        assert production["status"] == "qa_review_pending" and production["stage"] == "qa"
        assert production["current_render"] == {
            "version": 2,
            "final_media_artifact_id": f"{run_id}-artifact-2",
        }
        assert len(generator.inputs) == image_calls
        assert production["founder_review"] is None
        assert not [
            r for r in repository.list_production_qa_reviews(run_id) if r.scope == "whole_video"
        ]
        assert (
            repository.connection.execute("SELECT COUNT(*) FROM publishing_packages").fetchone()[0]
            == 0
        )

        snapshot = repository.get_final_media_input_snapshot(f"{run_id}:snapshot:2")
        assert [item["duration_ms"] for item in snapshot.scene_inputs] == durations
        assert snapshot.narration_asset_id == narration_id
        for new, old in zip(snapshot.scene_inputs, original_snapshot.scene_inputs, strict=True):
            assert new["resolved_state_id"] == old["resolved_state_id"]
            assert new["source_assets"] == old["source_assets"]
            assert new["transition_to_next"] == old["transition_to_next"]
        assert snapshot.caption_cues == original_snapshot.caption_cues
        assert snapshot.render_settings == original_snapshot.render_settings

        # Nothing historical was replaced; new records are versioned alongside it.
        assert all(
            item in repository.list_production_evidence(run_id) for item in original_evidence
        )
        assert all(
            item in repository.list_production_qa_reviews(run_id) for item in original_reviews
        )
        assert (
            repository.get_final_media_input_snapshot(f"{run_id}:snapshot:1") == original_snapshot
        )
        assert repository.get_final_media_artifact(f"{run_id}-artifact-1") == original_artifact
        cells = {
            r.id: r for r in repository.list_production_qa_reviews(run_id) if r.scope == "cell"
        }
        assert cells[f"{run_id}:qa:cell:1"].final_media_artifact_id == f"{run_id}-artifact-1"
        assert cells[f"{run_id}:qa:cell:2"].final_media_artifact_id == f"{run_id}-artifact-2"
        assert cells[f"{run_id}:qa:cell:2"].outcome == "passed"

        retime_evidence = repository.list_production_evidence(run_id, "retime")
        assert len(retime_evidence) == 1
        payload = retime_evidence[0].payload
        assert payload["actor"] == "founder" and payload["reason"] == "Align cuts to pauses."
        assert payload["durations_ms"] == durations
        assert payload["narration_asset_id"] == narration_id
        assert payload["source_render_version"] == 1
        assert payload["source_final_media_artifact_id"] == f"{run_id}-artifact-1"
        assert payload["render_version"] == 2
        assert payload["final_media_artifact_id"] == f"{run_id}-artifact-2"
        assert retime_evidence[0].narration_asset_id == narration_id

        # Human QA after a retime binds to the new render; a failed review can be retimed.
        failed = service.record_qa(run_id, {"outcome": "failed", "evidence": {"pacing": "late"}})
        assert (failed["status"], failed["stage"]) == ("failed", "qa")
        whole = [
            r for r in repository.list_production_qa_reviews(run_id) if r.scope == "whole_video"
        ]
        assert [(r.id, r.final_media_artifact_id) for r in whole] == [
            (f"{run_id}:qa:whole-video:1", f"{run_id}-artifact-2")
        ]
        third = service.retime(run_id, list(reversed(durations)), "founder", "Second pacing pass.")
        assert third["status"] == "qa_review_pending"
        assert third["current_render"]["final_media_artifact_id"] == f"{run_id}-artifact-3"
        assert repository.get_final_media_input_snapshot(f"{run_id}:snapshot:3")
        assert repository.get_render_execution(f"{run_id}:render-execution:3").id
        assert [
            e.id
            for e in sorted(
                repository.list_production_evidence(run_id, "render"), key=lambda e: e.id
            )
        ] == [
            f"{run_id}:render:evidence:1",
            f"{run_id}:render:evidence:2",
            f"{run_id}:render:evidence:3",
        ]
        passed = service.record_qa(run_id, {"outcome": "passed", "evidence": {"pacing": "ok"}})
        assert passed["status"] == "private_founder_review_ready"
        whole = {
            r.id: r
            for r in repository.list_production_qa_reviews(run_id)
            if r.scope == "whole_video"
        }
        assert whole[f"{run_id}:qa:whole-video:2"].final_media_artifact_id == f"{run_id}-artifact-3"

        with pytest.raises(ProductionRequestError, match="awaiting or failing"):
            service.retime(run_id, durations, "founder", "Too late.")
        service.founder_review(
            run_id,
            {
                "outcome": "accepted",
                "founder_actor": "founder",
                "decision_reference": "r",
                "notes": "",
            },
        )
        with pytest.raises(ProductionRequestError, match="awaiting or failing"):
            service.retime(run_id, durations, "founder", "After acceptance.")

        run_after = repository.get_production_run(run_id)
        assert run_after.request == run_before.request
        assert run_after.request_digest == run_before.request_digest
    finally:
        server.server_close()


def test_retime_timing_and_identity_validation_fails_closed(tmp_path, monkeypatch) -> None:
    server, generator, request = _render_ready_run(tmp_path, monkeypatch, "retime-validate")
    repository, service = server.repository, server.production_service
    try:
        run_id = request["id"]
        _forbid_providers(monkeypatch, generator)
        good = _durations_for(server, run_id, 2)
        events = repository.latest_production_run_event(run_id).sequence
        for durations, match in (
            ([sum(good)], "one duration per Scene"),
            (good + [1], "one duration per Scene"),
            ([0, sum(good)], "positive integer"),
            ([-1, sum(good) + 1], "positive integer"),
            ([True, sum(good) - 1], "positive integer"),
            ([good[0] + 0.0, good[1]], "positive integer"),
            ([good[0], good[1] + 1], "sum exactly"),
            ([good[0], good[1] - 1], "sum exactly"),
            ("1,2", "one duration per Scene"),
        ):
            with pytest.raises(ProductionRequestError, match=match):
                service.retime(run_id, durations, "founder", "bad timing")
        for actor, reason in (("", "x"), ("founder", " "), (None, "x")):
            with pytest.raises(ProductionRequestError, match="required text"):
                service.retime(run_id, good, actor, reason)
        assert repository.latest_production_run_event(run_id).sequence == events
        assert len(repository.list_production_evidence(run_id, "render")) == 1
        assert repository.list_production_evidence(run_id, "retime") == []
        rejected, status = _post_error(
            server,
            f"/api/v2/productions/{run_id}/retime",
            {"durations_ms": good, "actor": "founder", "reason": "x", "images": []},
        )
        assert status == 400 and "unsupported" in rejected["error"]

        # A retime whose render fails stays failed; retime is not a recovery mechanism.
        original_render = MediaService.render

        def failing_render(*_args, **_kwargs):
            raise RuntimeError("offline render failure")

        monkeypatch.setattr(MediaService, "render", failing_render)
        with pytest.raises(ProductionLifecycleError):
            service.retime(run_id, good, "founder", "first attempt")
        latest = repository.latest_production_run_event(run_id)
        assert (latest.status, latest.stage) == ("failed", "retime")
        assert repository.get_final_media_input_snapshot(f"{run_id}:snapshot:2")
        monkeypatch.setattr(MediaService, "render", original_render)
        with pytest.raises(ProductionRequestError, match="awaiting or failing"):
            service.retime(run_id, good, "founder", "second attempt")
        assert repository.latest_production_run_event(run_id).sequence == latest.sequence
        assert [e.id for e in repository.list_production_evidence(run_id, "render")] == [
            f"{run_id}:render:evidence:1"
        ]
    finally:
        server.server_close()


def test_retime_source_snapshot_matches_the_current_render_version(tmp_path, monkeypatch) -> None:
    server, generator, request = _render_ready_run(tmp_path, monkeypatch, "retime-orphan")
    repository, service = server.repository, server.production_service
    try:
        run_id = request["id"]
        _forbid_providers(monkeypatch, generator)
        good = _durations_for(server, run_id, 2)
        original = repository.get_final_media_input_snapshot(f"{run_id}:snapshot:1")
        # An orphan, higher-version snapshot with no corresponding render evidence.
        orphan = server.media_service.create_persistent_scene_snapshot(
            f"{run_id}:snapshot:2",
            original.visual_plan_id,
            original.narration_asset_id,
            [
                {
                    "scene_id": item["scene_id"],
                    "resolved_state_id": item["resolved_state_id"],
                    "duration_ms": duration,
                    "motion": item["motion"],
                    "transition_to_next": item["transition_to_next"],
                }
                for item, duration in zip(original.scene_inputs, reversed(good), strict=True)
            ],
        )
        repository.create_production_evidence(
            f"{run_id}:snapshot:evidence:2",
            run_id,
            "snapshot",
            {"schema_version": orphan.snapshot_schema_version},
            final_media_input_snapshot_id=orphan.id,
        )

        result = service.retime(run_id, good, "founder", "Retime from the rendered snapshot.")
        payload = repository.list_production_evidence(run_id, "retime")[0].payload
        assert payload["source_render_version"] == 1
        assert payload["source_final_media_input_snapshot_id"] == f"{run_id}:snapshot:1"
        # The orphan's version is skipped rather than collided with.
        assert result["current_render"] == {
            "version": 3,
            "final_media_artifact_id": f"{run_id}-artifact-3",
        }
        assert [
            i["duration_ms"]
            for i in repository.get_final_media_input_snapshot(f"{run_id}:snapshot:3").scene_inputs
        ] == good
        assert repository.get_final_media_input_snapshot(f"{run_id}:snapshot:2") == orphan

        # A current render with no snapshot evidence of the same version fails closed.
        artifact = repository.get_final_media_artifact(f"{run_id}-artifact-3")
        repository.create_production_evidence(
            f"{run_id}:render:evidence:9",
            run_id,
            "render",
            {"technical_validation": {}},
            render_execution_id=artifact.render_execution_id,
            final_media_artifact_id=artifact.id,
        )
        with pytest.raises(ProductionRequestError, match="matching snapshot"):
            service.retime(run_id, good, "founder", "No matching snapshot.")
    finally:
        server.server_close()


def test_retime_is_refused_once_a_render_is_packaged(tmp_path, monkeypatch) -> None:
    from project_atlas.publishing_state import TARGET_CHANNEL
    from tests.test_publishing import _manifest

    server, generator, request = _render_ready_run(tmp_path, monkeypatch, "retime-packaged")
    repository, service = server.repository, server.production_service
    try:
        run_id = request["id"]
        artifact = repository.get_final_media_artifact(f"{run_id}-artifact-1")
        repository.create_publishing_package(
            "retime-package",
            "retime-pilot",
            1,
            1,
            artifact.id,
            artifact.content_digest,
            TARGET_CHANNEL,
            _manifest(),
        )
        with pytest.raises(ProductionRequestError, match="packaged"):
            service.retime(run_id, _durations_for(server, run_id, 2), "founder", "Too late.")
        assert len(repository.list_production_evidence(run_id, "render")) == 1
    finally:
        server.server_close()


def _single_beat_worlds_request(server, tmp_path: Path, prefix: str, count: int) -> dict:
    repository = server.repository
    plan = create_authorized_visual_plan(server, prefix)
    scenes, specs = [], []
    for index in range(1, count + 1):
        scene = repository.create_scene_under_visual_plan_authorization(
            f"{prefix}-scene-{index}", plan.id, index, f"Beat {index}", f"Visual {index}"
        )
        spec = repository.create_asset_spec_under_scene_authorization(
            f"{prefix}-spec-{index}",
            scene.id,
            "character",
            "Full-scene beat.",
            f"Beat {index}",
            f"Draw beat {index} without text.",
            character_profile_id=HAMSTER_PROFILE,
        )
        scenes.append(scene.id)
        specs.append(spec.id)
    reference_set_id = ensure_character_reference_set(server, tmp_path / "assets")
    repository.create_visual_reference_authority(
        "visual-reference-authority-similarstoic-global-illustration-v1",
        "similarstoic-global-illustration",
        "global_illustration_style",
        "Offline lifecycle authority",
        "Offline style authority.",
        [("asset-http-reference-basis-v1", "style")],
    )
    treatment = {
        "style_profile_id": "visual-style-profile-similarstoic-core-v3",
        "palette_id": "similarstoic-core-v3",
        "wall_treatment_id": "off-white-negative-space-v1",
        "lighting_policy_id": "flat-soft-light-v1",
    }
    return {
        "id": prefix,
        "visual_plan_id": plan.id,
        "authority": {
            "character_profile_id": HAMSTER_PROFILE,
            "character_reference_set_id": reference_set_id,
            "visual_reference_authority_id": (
                "visual-reference-authority-similarstoic-global-illustration-v1"
            ),
            "visual_style_profile_id": "visual-style-profile-similarstoic-core-v3",
        },
        "worlds": [
            {
                "key": f"beat-{index}",
                "scene_ids": [scene_id],
                "visual_treatment": treatment,
                "entities": [
                    {
                        "key": "scene",
                        "semantic_role": "full-scene-illustration",
                        "persistence_class": "LOCKED_STATIC",
                        "purpose": "Full-scene beat.",
                        "neutral_scale_id": "full-frame-v1",
                        "initial_variant_key": "beat",
                        "initial_transform": {},
                        "variants": [
                            {
                                "key": "beat",
                                "asset_spec_id": spec_id,
                                "intrinsic_size_wu": [1080, 1920],
                            }
                        ],
                    }
                ],
                "transitions": [],
            }
            for index, (scene_id, spec_id) in enumerate(zip(scenes, specs, strict=True), 1)
        ],
        "timeline": [
            {
                "scene_id": scene_id,
                "duration_weight": 1,
                "transition_to_next": "crossfade" if index < count - 1 else None,
            }
            for index, scene_id in enumerate(scenes)
        ],
        "forecast": {"image_calls": count, "narration_calls": 1},
        "narration_authorized": True,
    }


def test_retime_production_8_shape_regression(tmp_path, monkeypatch) -> None:
    """Eight full-frame v3 beats over a 30,220 ms narration, retimed to founder durations."""

    runtime = media_runtime_or_skip()
    generator = ValidFakeImageGenerator(content=realistic_source_png(runtime, tmp_path))
    server = _server(tmp_path, generator, runtime)
    wav = tmp_path / "narration-30220.wav"
    runtime._run(
        [
            runtime.ffmpeg_path,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=330:sample_rate=48000:duration=30.22",
            "-c:a",
            "pcm_s16le",
            str(wav),
        ]
    )
    calls: list[str] = []

    def synthesize(engine, text):
        calls.append(text)
        return NarrationSynthesis(
            wav.read_bytes(),
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
    repository, service = server.repository, server.production_service
    try:
        request = _single_beat_worlds_request(server, tmp_path, "p8-shape", 8)
        post_json(server, "/api/v2/productions", request)
        keys = [(f"beat-{i}", "scene", "beat") for i in range(1, 9)]
        reviewed, _status = post_json(
            server, "/api/v2/productions/p8-shape/acquisition-review", _passing_reviews(keys)
        )
        assert reviewed["production"]["status"] == "qa_review_pending"
        narration_id = repository.list_production_evidence("p8-shape", "narration")[
            0
        ].narration_asset_id
        assert repository.get_narration_asset(narration_id).duration_ms == 30220
        active = {k: v["asset_id"] for k, v in service._acquisition_map("p8-shape").items()}
        image_calls, narration_calls = len(generator.inputs), len(calls)
        original = repository.get_final_media_input_snapshot("p8-shape:snapshot:1")

        durations = [3053, 2857, 3471, 2346, 3262, 4728, 5006, 5497]
        assert sum(durations) == 30220
        result = service.retime("p8-shape", durations, "founder", "Pause-aligned pacing.")

        assert result["status"] == "qa_review_pending"
        snapshot = repository.get_final_media_input_snapshot("p8-shape:snapshot:2")
        assert [item["duration_ms"] for item in snapshot.scene_inputs] == durations
        assert snapshot.narration_asset_id == narration_id
        assert snapshot.render_settings["profile"] == "similarstoic-vertical-v3"
        assert [i["source_assets"] for i in snapshot.scene_inputs] == [
            i["source_assets"] for i in original.scene_inputs
        ]
        assert {k: v["asset_id"] for k, v in service._acquisition_map("p8-shape").items()} == active
        assert (len(generator.inputs), len(calls)) == (image_calls, narration_calls)
        artifact = repository.get_final_media_artifact("p8-shape-artifact-2")
        assert abs(artifact.duration_ms - 30220) <= 100
        cells = [r for r in repository.list_production_qa_reviews("p8-shape") if r.scope == "cell"]
        assert {(r.id, r.final_media_artifact_id, r.outcome) for r in cells} == {
            ("p8-shape:qa:cell:1", "p8-shape-artifact-1", "passed"),
            ("p8-shape:qa:cell:2", "p8-shape-artifact-2", "passed"),
        }
        assert repository.get_final_media_artifact("p8-shape-artifact-1")
    finally:
        server.server_close()


# --- Claim-timed citation overlay -----------------------------------------------------------


def _citation_dark_pixels(runtime, video: Path, seconds: float, tmp_path: Path) -> int:
    """Count dark pixels in the upper-right safe corner of one decoded frame."""

    raw = tmp_path / f"corner-{seconds:.3f}.gray"
    runtime._run(
        [
            runtime.ffmpeg_path,
            "-y",
            "-ss",
            f"{seconds:.3f}",
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-vf",
            "crop=540:240:540:80,format=gray",
            "-f",
            "rawvideo",
            str(raw),
        ]
    )
    return sum(1 for value in raw.read_bytes() if value < 128)


def _cited_render_run(tmp_path, monkeypatch, prefix: str, citations):
    runtime = media_runtime_or_skip()
    white = sized_png(runtime, tmp_path, 941, 1672)
    generator = ValidFakeImageGenerator(content=white)
    server = _server(tmp_path, generator, runtime)
    _fake_narration(monkeypatch, _sine_wav(runtime, tmp_path))
    request, keys = _request(server, tmp_path, prefix)
    if citations is not None:
        request["citations"] = citations(request)
    post_json(server, "/api/v2/productions", request)
    reviewed, status = post_json(
        server, f"/api/v2/productions/{prefix}/acquisition-review", _passing_reviews(keys)
    )
    assert status == 200 and reviewed["production"]["status"] == "qa_review_pending"
    return runtime, server, generator, request


def test_citation_requests_are_validated_and_frozen(tmp_path) -> None:
    generator = ValidFakeImageGenerator()
    server = _server(tmp_path, generator)
    try:
        request, _keys = _request(server, tmp_path, "cite-validate")
        scene = request["timeline"][1]["scene_id"]
        source = "cite-validate-source"
        good = {"scene_id": scene, "label": "Source: GOV.UK", "source_ids": [source]}
        for citations, match in (
            ([{**good, "scene_id": "not-a-scene"}], "distinct Scene"),
            ([good, good], "distinct Scene"),
            ([{**good, "label": " "}], "1-24"),
            ([{**good, "label": "x" * 25}], "1-24"),
            ([{**good, "label": "brace {x}"}], "1-24"),
            ([{**good, "source_ids": ["unknown-source"]}], "frozen ScriptClaimSet"),
            ([{**good, "source_ids": []}], "distinct source IDs"),
            ([{**good, "extra": 1}], "exactly scene_id"),
            ([], "non-empty"),
        ):
            failed, status = _post_error(
                server, "/api/v2/productions", {**request, "citations": citations}
            )
            assert status == 400 and match in failed["error"], (citations, failed)
            assert generator.inputs == []
        started, status = post_json(server, "/api/v2/productions", {**request, "citations": [good]})
        assert status == 201
        run = server.repository.get_production_run(request["id"])
        assert run.request["citations"] == [good]
        uncited = json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        assert run.request_digest != sha256(uncited.encode()).hexdigest()
    finally:
        server.server_close()


def test_citation_is_timed_to_its_scene_visible_only_there_and_follows_retime(
    tmp_path, monkeypatch
) -> None:
    def cite_second_scene(request):
        return [
            {
                "scene_id": request["timeline"][1]["scene_id"],
                "label": "Source: GOV.UK",
                "source_ids": ["cite-render-source"],
            }
        ]

    runtime, server, generator, request = _cited_render_run(
        tmp_path, monkeypatch, "cite-render", cite_second_scene
    )
    repository, service = server.repository, server.production_service
    try:
        snapshot = repository.get_final_media_input_snapshot("cite-render:snapshot:1")
        first, second = (item["duration_ms"] for item in snapshot.scene_inputs)
        overlay = snapshot.render_settings["citation_overlay"]
        assert overlay["style"] == MediaService.CITATION_STYLE
        assert overlay["citations"] == [
            {
                "scene_id": snapshot.scene_inputs[1]["scene_id"],
                "label": "Source: GOV.UK",
                "source_ids": ["cite-render-source"],
                "start_ms": first,
                "end_ms": first + second,
            }
        ]
        artifact = repository.get_final_media_artifact("cite-render-artifact-1")
        video = tmp_path / "media" / artifact.storage_path
        assert _citation_dark_pixels(runtime, video, first / 2000, tmp_path) == 0
        assert _citation_dark_pixels(runtime, video, (first + 0.75 * second) / 1000, tmp_path) > 50

        # Retime keeps the citation on the same Scene and recomputes its interval.
        _forbid_providers(monkeypatch, generator)
        total = first + second
        moved = [total // 4, total - total // 4]
        service.retime("cite-render", moved, "founder", "Earlier second scene.")
        retimed = repository.get_final_media_input_snapshot("cite-render:snapshot:2")
        assert [
            (c["scene_id"], c["start_ms"], c["end_ms"])
            for c in retimed.render_settings["citation_overlay"]["citations"]
        ] == [(snapshot.scene_inputs[1]["scene_id"], moved[0], total)]
        video2 = (
            tmp_path
            / "media"
            / repository.get_final_media_artifact("cite-render-artifact-2").storage_path
        )
        probe_at = (moved[0] + first) / 2000 + 0.05  # inside the new interval, before the old one
        assert moved[0] / 1000 < probe_at < first / 1000
        assert _citation_dark_pixels(runtime, video2, probe_at, tmp_path) > 50
        assert _citation_dark_pixels(runtime, video, probe_at, tmp_path) == 0
        assert _citation_dark_pixels(runtime, video2, moved[0] / 2000, tmp_path) == 0
    finally:
        server.server_close()


def test_citation_free_snapshots_keep_the_existing_render_graph(tmp_path, monkeypatch) -> None:
    runtime, server, _generator, request = _cited_render_run(
        tmp_path, monkeypatch, "cite-none", None
    )
    try:
        snapshot = server.repository.get_final_media_input_snapshot("cite-none:snapshot:1")
        assert "citation_overlay" not in snapshot.render_settings
        assert "citations" not in server.repository.get_production_run(request["id"]).request
        assert (
            MediaService._citation_filter(snapshot.render_settings, snapshot.scene_inputs, tmp_path)
            is None
        )
        assert not (tmp_path / "citations.srt").exists()
        artifact = server.repository.get_final_media_artifact("cite-none-artifact-1")
        video = tmp_path / "media" / artifact.storage_path
        for seconds in (0.2, 0.8):
            assert _citation_dark_pixels(runtime, video, seconds, tmp_path) == 0
    finally:
        server.server_close()


def test_tampered_citation_timing_fails_closed() -> None:
    scenes = [
        {"scene_id": "a", "duration_ms": 400},
        {"scene_id": "b", "duration_ms": 600},
    ]
    timed = MediaService.citation_overlays(
        scenes, [{"scene_id": "b", "label": "Source: TPR", "source_ids": ["s"]}]
    )
    assert timed[0]["start_ms"] == 400 and timed[0]["end_ms"] == 1000
    settings = {**MediaService.PERSISTENT_RENDER_SETTINGS}
    for overlay in (
        {"style": MediaService.CITATION_STYLE, "citations": [{**timed[0], "start_ms": 0}]},
        {"style": {**MediaService.CITATION_STYLE, "font_size": 90}, "citations": timed},
        {"style": MediaService.CITATION_STYLE, "citations": []},
    ):
        with pytest.raises(MediaRuntimeError):
            MediaService._citation_filter(
                {**settings, "citation_overlay": overlay}, scenes, Path(".")
            )
