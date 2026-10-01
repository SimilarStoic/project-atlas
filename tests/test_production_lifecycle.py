"""Canonical v2 production lifecycle integration tests; every provider is fake."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from project_atlas.generation import GeneratedArtifact, GenerationFailure
from project_atlas.media import NarrationSynthesis
from project_atlas.web import create_server
from tests.test_web import (
    MEDIA_PNG,
    create_authorized_visual_plan,
    ensure_character_reference_set,
    media_runtime_or_skip,
    post_json,
)


class ValidFakeImageGenerator:
    """Return one decodable image and retain exact provider-free call count."""

    generator_key = "fake-v2-image"

    def __init__(self, failure: GenerationFailure | None = None) -> None:
        self.failure = failure
        self.inputs = []

    def supports(self, asset_type: str) -> bool:
        return asset_type in {"environment", "character", "graphic", "prop"}

    def generate(self, generation_input):
        self.inputs.append(generation_input)
        if self.failure:
            raise self.failure
        return GeneratedArtifact(MEDIA_PNG, "image/png", provider_key="offline-fake")


def _request(server, tmp_path: Path, prefix: str) -> tuple[dict, list[tuple[str, str, str]]]:
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
            "graphic",
            "Explain the current narration beat.",
            f"Canonical world state {sequence}",
            f"Draw state {sequence} without text.",
        )
        variants.append(
            {
                "key": variant_key,
                "asset_spec_id": spec.id,
                "intrinsic_size_wu": [1080, 1920],
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
            "forecast": {"image_calls": 2, "narration_calls": 1, "real_provider_calls": 0},
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


def test_canonical_v2_http_lifecycle_is_resumable_and_founder_distinct(
    tmp_path, monkeypatch
) -> None:
    runtime = media_runtime_or_skip()
    generator = ValidFakeImageGenerator()
    server = create_server(
        port=0,
        database_path=tmp_path / "lifecycle.db",
        generator=generator,
        asset_storage_root=tmp_path / "assets",
        media_runtime=runtime,
        media_storage_root=tmp_path / "media",
    )
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

    def synthesize(engine, text):
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
                {
                    "reviews": [
                        {
                            "world_key": world,
                            "entity_key": entity,
                            "variant_key": variant,
                            "outcome": "passed",
                            "evidence": {
                                "source_quality": "passed",
                                "semantic_support": "passed",
                            },
                        }
                        for world, entity, variant in review_keys
                    ]
                },
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
        assert (
            server.repository.get_narration_generation_execution(
                f"{request['id']}:narration-execution:1"
            ).voice_identity
            == "Daniel"
        )
        assert any(
            review.scope == "cell"
            for review in server.repository.list_production_qa_reviews(request["id"])
        )
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
    server = create_server(
        port=0,
        database_path=tmp_path / "failure.db",
        generator=generator,
        asset_storage_root=tmp_path / "assets",
        media_runtime=media_runtime_or_skip(),
        media_storage_root=tmp_path / "media",
    )
    try:
        request, _review_keys = _request(server, tmp_path, "canonical-v2-failure")
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
