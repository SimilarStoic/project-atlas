"""Tests for the local MVP UI shell."""

import json
import os
import threading
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from project_atlas.demo_data import chat_reply, content_payload, opportunity_payload
from project_atlas.generation import (
    GeneratedArtifact,
    GenerationFailure,
    LocalAssetStorage,
    PromptComposer,
    asset_spec_snapshot,
)
from project_atlas.web import create_server


class FakeImageGenerator:
    """Deterministic generator for HTTP tests; it never uses the network."""

    generator_key = "fake-http-image"

    def __init__(self, failure: GenerationFailure | None = None) -> None:
        self.failure = failure
        self.inputs: list[object] = []

    def supports(self, asset_type: str) -> bool:
        return asset_type in {"environment", "character", "graphic", "prop"}

    def generate(self, generation_input: object) -> GeneratedArtifact:
        self.inputs.append(generation_input)
        if self.failure:
            raise self.failure
        return GeneratedArtifact(
            b"http fake image",
            "image/png",
            provider_key="fake-http-provider",
            model_key="fake-http-model",
            provider_request_id="fake-http-request",
        )


def ensure_character_reference_set(server, storage_root: Path) -> str:
    """Seed historical v0.12 character evidence before exercising v0.13 HTTP generation."""

    repository = server.repository
    profile_id = "character-profile-similarstoic-hamster-core-v1"
    existing = repository.get_latest_character_reference_set(profile_id)
    if existing is not None:
        return existing.id
    profile = repository.get_character_profile(profile_id)
    asset_spec = repository.create_asset_spec(
        "asset-spec-http-reference-basis-v1",
        "scene-isa-deadline-video-v1-01",
        "character",
        "Historical HTTP character-reference basis.",
        "A historical character reference for HTTP tests.",
        "Illustrate the canonical hamster reference basis.",
        character_profile_id=profile.id,
    )
    storage = LocalAssetStorage(storage_root)
    content = b"http historical reference png bytes"
    stored = storage.write(asset_spec.id, "asset-http-reference-basis-v1", content, "image/png")
    style = repository.get_visual_style_profile("visual-style-profile-similarstoic-core-v2")
    repository.record_successful_generation(
        "generation-execution-http-reference-basis-v1",
        "asset-http-reference-basis-v1",
        asset_spec.id,
        asset_spec_snapshot(asset_spec),
        PromptComposer().compose(asset_spec, style, profile).payload(),
        "historical-http-generator",
        storage.relative_path(stored),
        "image/png",
        visual_style_profile_id=style.id,
        character_profile_id=profile.id,
        content_digest=sha256(content).hexdigest(),
    )
    return repository.create_character_reference_set(
        "character-reference-set-http-basis-v1", profile.id, ["asset-http-reference-basis-v1"]
    ).id


def test_demo_data_represents_future_content_concepts() -> None:
    """Demo data keeps opportunities and content-package concepts separate."""

    assert 5 <= len(opportunity_payload()) <= 10
    assert {"claim_count", "source_count", "lifecycle"} <= content_payload().keys()


def test_demo_chat_is_local_and_deterministic() -> None:
    """The local chat is useful without a model integration."""

    assert "ISA" in chat_reply("What should we make tomorrow?")


def test_server_can_be_created_for_local_use(tmp_path: Path) -> None:
    """The server binds an ephemeral local port for testability."""

    server = create_server(port=0, database_path=tmp_path / "atlas.db")
    try:
        assert server.server_address[1] > 0
    finally:
        server.server_close()


def test_content_piece_lifecycle_api_requires_ready_authorized_angle_provenance(
    tmp_path: Path,
) -> None:
    """v0.19 creates ContentPieces only from eligible Ready-authorized Angles."""

    server = create_server(port=0, database_path=tmp_path / "atlas.db")
    base_url = f"http://127.0.0.1:{server.server_address[1]}"

    def request_json(request: Request) -> tuple[dict, int]:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        with urlopen(request) as response:
            payload = json.load(response)
            status = response.status
        thread.join(timeout=2)
        return payload, status

    def request_error(request: Request) -> tuple[dict, int]:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        try:
            urlopen(request)
        except HTTPError as error:
            payload = json.loads(error.read())
            status = error.code
        else:
            raise AssertionError(
                "The invalid ContentPiece lifecycle request unexpectedly succeeded."
            )
        thread.join(timeout=2)
        return payload, status

    try:
        repository = server.repository
        opportunity_id = "uk-isa-rules"
        pack_id = "research-pack-isa-deadline-v1"
        other_opportunity_id = "http-content-piece-other-opportunity"
        repository.create_opportunity(
            other_opportunity_id, "Other", "Summary", "Why now", 1, "proposed"
        )
        other_pack = repository.create_research_pack(
            "http-content-piece-other-pack", other_opportunity_id, 1, "Other pack"
        )

        def assessment(assessment_id: str, target_pack_id: str, outcome: str):
            return repository.create_research_readiness_assessment(
                assessment_id,
                target_pack_id,
                outcome,
                {"summary": f"{outcome} for HTTP lifecycle testing."},
                "readiness-policy-v1",
                "test",
                "http-test",
                "v1",
            )

        ready = assessment("http-content-piece-ready", pack_id, "Ready")
        blocked = assessment("http-content-piece-blocked", pack_id, "Blocked")
        other_ready = assessment("http-content-piece-other-ready", other_pack.id, "Ready")
        angle = repository.create_editorial_angle_under_research_readiness(
            "http-content-piece-ready-angle",
            opportunity_id,
            pack_id,
            ready.id,
            "A deliberate lifecycle Angle",
            "Exact Ready provenance is stored.",
            "Understand the decision boundary.",
            "A focused explainer.",
            ["Ready provenance is exact."],
        )
        endpoint = f"{base_url}/api/opportunities/{opportunity_id}/content-pieces"
        payload = {
            "id": "http-ready-content-piece",
            "editorial_angle_id": angle.id,
            "format_key": "video",
            "working_title": "A deliberate lifecycle ContentPiece",
            "metadata": {"source": "http-test"},
        }
        created, status = request_json(
            Request(
                endpoint,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 201
        content_piece = created["content_piece"]
        assert created["kind"] == "content_piece"
        assert content_piece["opportunity_id"] == opportunity_id
        assert content_piece["editorial_angle_id"] == angle.id
        assert content_piece["latest_script"] is None
        assert (
            repository.connection.execute(
                "SELECT COUNT(*) FROM scripts WHERE content_piece_id = ?", (payload["id"],)
            ).fetchone()[0]
            == 0
        )
        second, status = request_json(
            Request(
                endpoint,
                data=json.dumps(payload | {"id": "http-ready-content-piece-second"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 201
        assert second["content_piece"]["editorial_angle_id"] == angle.id

        def post_error(target_url: str, body: dict) -> tuple[dict, int]:
            return request_error(
                Request(
                    target_url,
                    data=json.dumps(body).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
            )

        for invalid_payload in (
            payload | {"editorial_angle_id": ""},
            payload | {"id": "http-unsupported", "research_readiness_assessment_id": ready.id},
        ):
            rejected, status = post_error(endpoint, invalid_payload)
            assert status == 400
            assert rejected["error"]
        missing_angle, status = post_error(
            endpoint, payload | {"id": "http-missing-angle", "editorial_angle_id": "missing"}
        )
        assert status == 404
        assert "not found" in missing_angle["error"]
        missing_opportunity, status = post_error(
            f"{base_url}/api/opportunities/missing/content-pieces",
            payload | {"id": "http-missing-opportunity"},
        )
        assert status == 404
        assert "not found" in missing_opportunity["error"]
        wrong_opportunity, status = post_error(
            f"{base_url}/api/opportunities/{other_opportunity_id}/content-pieces",
            payload | {"id": "http-wrong-opportunity"},
        )
        assert status == 400
        assert wrong_opportunity["error"]
        null_provenance, status = post_error(
            endpoint,
            payload
            | {
                "id": "http-null-provenance",
                "editorial_angle_id": "editorial-angle-isa-decision-tree-v1",
            },
        )
        assert status == 400
        assert "provenance" in null_provenance["error"]

        non_ready_angle = repository.create_editorial_angle(
            "http-content-piece-blocked-angle",
            opportunity_id,
            pack_id,
            "Blocked angle",
            "Thesis",
            "Promise",
            "Frame",
            ["One"],
        )
        mismatched_angle = repository.create_editorial_angle(
            "http-content-piece-mismatched-angle",
            opportunity_id,
            pack_id,
            "Mismatched angle",
            "Thesis",
            "Promise",
            "Frame",
            ["One"],
        )
        missing_assessment_angle = repository.create_editorial_angle(
            "http-content-piece-missing-assessment-angle",
            opportunity_id,
            pack_id,
            "Missing assessment angle",
            "Thesis",
            "Promise",
            "Frame",
            ["One"],
        )
        missing_pack_assessment = assessment(
            "http-content-piece-missing-pack-assessment", pack_id, "Ready"
        )
        missing_pack_angle = repository.create_editorial_angle_under_research_readiness(
            "http-content-piece-missing-pack-angle",
            opportunity_id,
            pack_id,
            missing_pack_assessment.id,
            "Missing Pack angle",
            "Thesis",
            "Promise",
            "Frame",
            ["One"],
        )
        repository.connection.execute("PRAGMA foreign_keys = OFF")
        with repository.connection:
            repository.connection.execute(
                "UPDATE editorial_angles SET research_readiness_assessment_id = ? WHERE id = ?",
                (blocked.id, non_ready_angle.id),
            )
            repository.connection.execute(
                "UPDATE editorial_angles SET research_readiness_assessment_id = ? WHERE id = ?",
                (other_ready.id, mismatched_angle.id),
            )
            repository.connection.execute(
                "UPDATE editorial_angles SET research_readiness_assessment_id = ? WHERE id = ?",
                ("missing-assessment", missing_assessment_angle.id),
            )
            repository.connection.execute(
                "UPDATE editorial_angles SET research_pack_id = ? WHERE id = ?",
                ("missing-pack", missing_pack_angle.id),
            )
            repository.connection.execute(
                "UPDATE research_readiness_assessments SET research_pack_id = ? WHERE id = ?",
                ("missing-pack", missing_pack_assessment.id),
            )
        repository.connection.execute("PRAGMA foreign_keys = ON")
        for angle_id in (
            non_ready_angle.id,
            mismatched_angle.id,
            missing_assessment_angle.id,
            missing_pack_angle.id,
        ):
            rejected, status = post_error(
                endpoint,
                payload | {"id": f"http-rejected-{angle_id}", "editorial_angle_id": angle_id},
            )
            assert status == 400
            assert rejected["error"]
    finally:
        server.server_close()


def test_script_lifecycle_api_appends_versions_only_under_ready_content_piece_lineage(
    tmp_path: Path,
) -> None:
    """v0.20 exposes deliberate Script drafting without downstream side effects."""

    server = create_server(port=0, database_path=tmp_path / "atlas.db")
    base_url = f"http://127.0.0.1:{server.server_address[1]}"

    def request_json(request: Request) -> tuple[dict, int]:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        with urlopen(request) as response:
            payload = json.load(response)
            status = response.status
        thread.join(timeout=2)
        return payload, status

    def request_error(request: Request) -> tuple[dict, int]:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        try:
            urlopen(request)
        except HTTPError as error:
            payload = json.loads(error.read())
            status = error.code
        else:
            raise AssertionError("The invalid Script lifecycle request unexpectedly succeeded.")
        thread.join(timeout=2)
        return payload, status

    try:
        repository = server.repository
        opportunity_id = "uk-isa-rules"
        other_opportunity_id = "http-script-other-opportunity"
        repository.create_opportunity(
            other_opportunity_id, "Other", "Summary", "Why now", 1, "proposed"
        )
        pack_id = "research-pack-isa-deadline-v1"
        other_pack = repository.create_research_pack(
            "http-script-other-pack", other_opportunity_id, 1, "Other pack"
        )

        def assessment(assessment_id: str, target_pack_id: str, outcome: str):
            return repository.create_research_readiness_assessment(
                assessment_id,
                target_pack_id,
                outcome,
                {"summary": f"{outcome} for HTTP Script lifecycle testing."},
                "readiness-policy-v1",
                "test",
                "http-test",
                "v1",
            )

        ready = assessment("http-script-ready", pack_id, "Ready")
        blocked = assessment("http-script-blocked", pack_id, "Blocked")
        other_ready = assessment("http-script-other-ready", other_pack.id, "Ready")
        fields = (
            "A deliberate lifecycle Angle",
            "Exact Ready provenance is stored.",
            "Understand the decision boundary.",
            "A focused explainer.",
            ["Ready provenance is exact."],
        )
        eligible_angle = repository.create_editorial_angle_under_research_readiness(
            "http-script-ready-angle", opportunity_id, pack_id, ready.id, *fields
        )
        eligible_piece = repository.create_content_piece_under_editorial_angle_readiness(
            "http-script-ready-piece",
            opportunity_id,
            eligible_angle.id,
            "video",
            "A deliberate lifecycle ContentPiece",
        )
        endpoint = f"{base_url}/api/content-pieces/{eligible_piece.id}/scripts"
        payload = {
            "id": "http-script-v1",
            "narration_text": "First complete narration.",
            "metadata": {"source": "http-test"},
        }
        created, status = request_json(
            Request(
                endpoint,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 201
        assert created == {
            "kind": "script",
            "script": {
                "id": "http-script-v1",
                "content_piece_id": eligible_piece.id,
                "version": 1,
                "narration_text": "First complete narration.",
            },
        }
        second, status = request_json(
            Request(
                endpoint,
                data=json.dumps(payload | {"id": "http-script-v2"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 201
        assert second["script"]["version"] == 2
        assert repository.get_script("http-script-v1").narration_text == "First complete narration."
        assert repository.get_content_piece(eligible_piece.id) == eligible_piece
        assert repository.list_visual_plans_for_content_piece(eligible_piece.id) == []

        def post_error(content_piece_id: str, body: dict) -> tuple[dict, int]:
            return request_error(
                Request(
                    f"{base_url}/api/content-pieces/{content_piece_id}/scripts",
                    data=json.dumps(body).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
            )

        for invalid_payload in (
            payload | {"id": "http-script-version", "version": 99},
            payload | {"id": "http-script-readiness", "research_readiness_assessment_id": ready.id},
            payload | {"id": "http-script-title", "title": "Unsupported title"},
            payload | {"id": "http-script-hook", "hook": "Unsupported hook"},
            payload | {"id": "http-script-claims", "claim_ids": ["claim"]},
            payload | {"id": "http-script-production", "visual_plan_id": "plan"},
            payload | {"id": "http-script-empty", "narration_text": ""},
        ):
            rejected, status = post_error(eligible_piece.id, invalid_payload)
            assert status == 400
            assert rejected["error"]
        missing_piece, status = post_error(
            "missing-content-piece", payload | {"id": "http-script-missing"}
        )
        assert status == 404
        assert "ContentPiece not found" in missing_piece["error"]

        def legacy_piece(angle_id: str, piece_id: str):
            editorial_angle = repository.create_editorial_angle(
                angle_id, opportunity_id, pack_id, *fields
            )
            return repository.create_content_piece(
                piece_id, opportunity_id, editorial_angle.id, "video", "Legacy ContentPiece"
            )

        null_piece = legacy_piece("http-script-null-angle", "http-script-null-piece")
        blocked_piece = legacy_piece("http-script-blocked-angle", "http-script-blocked-piece")
        mismatched_piece = legacy_piece(
            "http-script-mismatched-angle", "http-script-mismatched-piece"
        )
        missing_assessment_piece = legacy_piece(
            "http-script-missing-assessment-angle", "http-script-missing-assessment-piece"
        )
        missing_angle_piece = legacy_piece(
            "http-script-missing-angle", "http-script-missing-angle-piece"
        )
        missing_pack = repository.create_research_pack(
            "http-script-missing-pack", opportunity_id, 2, "Missing pack"
        )
        missing_pack_ready = assessment("http-script-missing-pack-ready", missing_pack.id, "Ready")
        missing_pack_angle = repository.create_editorial_angle_under_research_readiness(
            "http-script-missing-pack-angle",
            opportunity_id,
            missing_pack.id,
            missing_pack_ready.id,
            *fields,
        )
        missing_pack_piece = repository.create_content_piece_under_editorial_angle_readiness(
            "http-script-missing-pack-piece",
            opportunity_id,
            missing_pack_angle.id,
            "video",
            "Missing-pack ContentPiece",
        )
        wrong_pack = repository.create_research_pack(
            "http-script-wrong-pack", opportunity_id, 3, "Wrong pack"
        )
        wrong_ready = assessment("http-script-wrong-ready", wrong_pack.id, "Ready")
        wrong_angle = repository.create_editorial_angle_under_research_readiness(
            "http-script-wrong-angle", opportunity_id, wrong_pack.id, wrong_ready.id, *fields
        )
        wrong_piece = repository.create_content_piece_under_editorial_angle_readiness(
            "http-script-wrong-piece",
            opportunity_id,
            wrong_angle.id,
            "video",
            "Wrong-lineage ContentPiece",
        )
        repository.connection.execute("PRAGMA foreign_keys = OFF")
        with repository.connection:
            repository.connection.execute(
                "UPDATE editorial_angles SET research_readiness_assessment_id = ? WHERE id = ?",
                (blocked.id, blocked_piece.editorial_angle_id),
            )
            repository.connection.execute(
                "UPDATE editorial_angles SET research_readiness_assessment_id = ? WHERE id = ?",
                (other_ready.id, mismatched_piece.editorial_angle_id),
            )
            repository.connection.execute(
                "UPDATE editorial_angles SET research_readiness_assessment_id = ? WHERE id = ?",
                ("missing-assessment", missing_assessment_piece.editorial_angle_id),
            )
            repository.connection.execute(
                "DELETE FROM editorial_angles WHERE id = ?",
                (missing_angle_piece.editorial_angle_id,),
            )
            repository.connection.execute(
                "UPDATE editorial_angles SET research_pack_id = ? WHERE id = ?",
                ("missing-pack", missing_pack_piece.editorial_angle_id),
            )
            repository.connection.execute(
                "UPDATE research_readiness_assessments SET research_pack_id = ? WHERE id = ?",
                ("missing-pack", missing_pack_ready.id),
            )
            repository.connection.execute(
                "UPDATE research_packs SET opportunity_id = ? WHERE id = ?",
                (other_opportunity_id, wrong_pack.id),
            )
        repository.connection.execute("PRAGMA foreign_keys = ON")

        for piece in (
            null_piece,
            blocked_piece,
            mismatched_piece,
            missing_assessment_piece,
            missing_angle_piece,
            missing_pack_piece,
            wrong_piece,
        ):
            rejected, status = post_error(piece.id, payload | {"id": f"rejected-{piece.id}"})
            assert status == 400
            assert rejected["error"]
    finally:
        server.server_close()


def test_editorial_package_api_retains_explicit_options_and_exact_snapshots(tmp_path: Path) -> None:
    """v0.21 exposes append-only editorial alternatives and frozen package history."""

    server = create_server(port=0, database_path=tmp_path / "atlas.db")
    base_url = f"http://127.0.0.1:{server.server_address[1]}"

    def request_json(request: Request) -> tuple[dict, int]:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        with urlopen(request) as response:
            payload = json.load(response)
            status = response.status
        thread.join(timeout=2)
        return payload, status

    def request_error(request: Request) -> tuple[dict, int]:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        try:
            urlopen(request)
        except HTTPError as error:
            payload = json.loads(error.read())
            status = error.code
        else:
            raise AssertionError("The invalid editorial-package request unexpectedly succeeded.")
        thread.join(timeout=2)
        return payload, status

    def post(path: str, payload: dict) -> tuple[dict, int]:
        return request_json(
            Request(
                f"{base_url}{path}",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )

    try:
        repository = server.repository
        opportunity_id = "http-editorial-package-opportunity"
        repository.create_opportunity(
            opportunity_id, "Opportunity", "Summary", "Why now", 1, "proposed"
        )
        pack = repository.create_research_pack(
            "http-editorial-package-pack", opportunity_id, 1, "Research pack"
        )
        ready = repository.create_research_readiness_assessment(
            "http-editorial-package-ready",
            pack.id,
            "Ready",
            {"summary": "Ready."},
            "policy-v1",
            "test",
            "web-test",
            "v1",
        )
        fields = ("Angle", "Thesis", "Promise", "Frame", ["Takeaway"])
        angle = repository.create_editorial_angle_under_research_readiness(
            "http-editorial-package-angle", opportunity_id, pack.id, ready.id, *fields
        )
        content_piece = repository.create_content_piece_under_editorial_angle_readiness(
            "http-editorial-package-piece",
            opportunity_id,
            angle.id,
            "video",
            "Compatibility title",
        )
        script = repository.create_script_under_content_piece_readiness(
            "http-editorial-package-script", content_piece.id, "Exact narration."
        )
        prefix = f"/api/content-pieces/{content_piece.id}"
        title_payload = {
            "id": "http-title-1",
            "text": "Exact title",
            "metadata": {"author": "human"},
        }
        first_title, status = post(f"{prefix}/title-options", title_payload)
        assert status == 201
        assert first_title["kind"] == "title_option"
        assert first_title["title_option"]["text"] == "Exact title"
        second_title, status = post(
            f"{prefix}/title-options", {"id": "http-title-2", "text": "Revised title"}
        )
        assert status == 201
        hook_payload = {"id": "http-hook-1", "text": "Exact hook"}
        first_hook, status = post(f"{prefix}/hook-options", hook_payload)
        assert status == 201
        second_hook, status = post(
            f"{prefix}/hook-options", {"id": "http-hook-2", "text": "Revised hook"}
        )
        assert status == 201
        snapshot_payload = {
            "id": "http-package-1",
            "title_option_id": first_title["title_option"]["id"],
            "hook_option_id": first_hook["hook_option"]["id"],
            "script_id": script.id,
        }
        snapshot, status = post(f"{prefix}/editorial-package-snapshots", snapshot_payload)
        assert status == 201
        assert snapshot["kind"] == "editorial_package_snapshot"
        assert snapshot["editorial_package_snapshot"]["content_piece_id"] == content_piece.id
        assert snapshot["editorial_package_snapshot"]["title_option_id"] == "http-title-1"
        snapshot_two, status = post(
            f"{prefix}/editorial-package-snapshots",
            snapshot_payload
            | {
                "id": "http-package-2",
                "title_option_id": second_title["title_option"]["id"],
                "hook_option_id": second_hook["hook_option"]["id"],
            },
        )
        assert status == 201
        assert snapshot_two["editorial_package_snapshot"]["id"] == "http-package-2"

        title_history, status = request_json(Request(f"{base_url}{prefix}/title-options"))
        assert status == 200
        assert [record["id"] for record in title_history["title_options"]] == [
            "http-title-1",
            "http-title-2",
        ]
        hook_history, _ = request_json(Request(f"{base_url}{prefix}/hook-options"))
        assert len(hook_history["hook_options"]) == 2
        package_history, _ = request_json(
            Request(f"{base_url}{prefix}/editorial-package-snapshots")
        )
        assert [record["id"] for record in package_history["editorial_package_snapshots"]] == [
            "http-package-1",
            "http-package-2",
        ]
        fetched, _ = request_json(
            Request(f"{base_url}/api/editorial-package-snapshots/http-package-1")
        )
        assert fetched["editorial_package_snapshot"]["script_id"] == script.id
        assert repository.get_content_piece(content_piece.id).working_title == "Compatibility title"
        assert repository.list_visual_plans_for_content_piece(content_piece.id) == []

        malformed, status = request_error(
            Request(
                f"{base_url}{prefix}/title-options",
                data=json.dumps(title_payload | {"id": "bad-title", "selected": True}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 400
        assert malformed["error"]
        missing_piece, status = request_error(
            Request(
                f"{base_url}/api/content-pieces/missing/title-options",
                data=json.dumps(title_payload | {"id": "missing-piece-title"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 404
        assert "ContentPiece not found" in missing_piece["error"]
        missing_option, status = request_error(
            Request(
                f"{base_url}{prefix}/editorial-package-snapshots",
                data=json.dumps(
                    snapshot_payload | {"id": "missing-option", "title_option_id": "missing"}
                ).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 404
        assert missing_option["error"]

        legacy_angle = repository.create_editorial_angle(
            "http-editorial-package-legacy-angle", opportunity_id, pack.id, *fields
        )
        legacy_piece = repository.create_content_piece(
            "http-editorial-package-legacy-piece",
            opportunity_id,
            legacy_angle.id,
            "video",
            "Legacy title",
        )
        rejected, status = request_error(
            Request(
                f"{base_url}/api/content-pieces/{legacy_piece.id}/hook-options",
                data=json.dumps({"id": "legacy-hook", "text": "Rejected"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 400
        assert "readiness provenance" in rejected["error"]
    finally:
        server.server_close()


def test_script_claim_set_api_closes_and_reads_exact_frozen_provenance(tmp_path: Path) -> None:
    """v0.22 exposes one closed, explicit Claim set per immutable Script."""

    server = create_server(port=0, database_path=tmp_path / "atlas.db")
    base_url = f"http://127.0.0.1:{server.server_address[1]}"

    def request_json(request: Request) -> tuple[dict, int]:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        with urlopen(request) as response:
            payload = json.load(response)
            status = response.status
        thread.join(timeout=2)
        return payload, status

    def request_error(request: Request) -> tuple[dict, int]:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        try:
            urlopen(request)
        except HTTPError as error:
            payload = json.loads(error.read())
            status = error.code
        else:
            raise AssertionError("The invalid ScriptClaimSet request unexpectedly succeeded.")
        thread.join(timeout=2)
        return payload, status

    def post(path: str, payload: dict) -> tuple[dict, int]:
        return request_json(
            Request(
                f"{base_url}{path}",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )

    try:
        repository = server.repository
        opportunity_id = "http-script-claim-opportunity"
        other_opportunity_id = "http-script-claim-other-opportunity"
        repository.create_opportunity(
            opportunity_id, "Opportunity", "Summary", "Why now", 1, "proposed"
        )
        repository.create_opportunity(
            other_opportunity_id, "Other", "Summary", "Why now", 1, "proposed"
        )
        pack = repository.create_research_pack(
            "http-script-claim-pack", opportunity_id, 1, "Research pack"
        )
        other_pack = repository.create_research_pack(
            "http-script-claim-other-pack", other_opportunity_id, 1, "Other pack"
        )
        claim = repository.create_claim(
            "http-script-claim",
            pack.id,
            "Frozen HTTP Claim.",
            "fact",
            "low",
            "current",
            "reviewed",
            "",
        )
        unlinked_claim = repository.create_claim(
            "http-script-claim-unlinked",
            pack.id,
            "Unlinked Claim.",
            "fact",
            "low",
            "current",
            "reviewed",
            "",
        )
        other_claim = repository.create_claim(
            "http-script-claim-other",
            other_pack.id,
            "Other Claim.",
            "fact",
            "low",
            "current",
            "reviewed",
            "",
        )
        ready = repository.create_research_readiness_assessment(
            "http-script-claim-ready",
            pack.id,
            "Ready",
            {"summary": "Ready."},
            "policy-v1",
            "test",
            "web-test",
            "v1",
        )
        fields = ("Angle", "Thesis", "Promise", "Frame", ["Takeaway"])
        angle = repository.create_editorial_angle_under_research_readiness(
            "http-script-claim-angle", opportunity_id, pack.id, ready.id, *fields
        )
        repository.link_claim_to_editorial_angle(angle.id, claim.id, "core")
        piece = repository.create_content_piece_under_editorial_angle_readiness(
            "http-script-claim-piece", opportunity_id, angle.id, "video", "Compatibility title"
        )
        script = repository.create_script_under_content_piece_readiness(
            "http-script-claim-script", piece.id, "Complete narration."
        )
        endpoint = f"/api/scripts/{script.id}/claim-set"

        no_set, status = request_json(Request(f"{base_url}{endpoint}"))
        assert status == 200
        assert no_set["script_claim_set"] is None
        created, status = post(endpoint, {"id": "http-script-claim-set", "claim_ids": [claim.id]})
        assert status == 201
        assert created["kind"] == "script_claim_set"
        assert created["script_claim_set"]["claim_ids"] == [claim.id]
        assert created["script_claim_set"]["frozen_claims"][0]["text"] == "Frozen HTTP Claim."
        fetched, status = request_json(Request(f"{base_url}{endpoint}"))
        assert status == 200
        assert fetched["script_claim_set"] == created["script_claim_set"]

        for invalid_payload in (
            {"id": "duplicate", "claim_ids": [claim.id, claim.id]},
            {"id": "unsupported", "claim_ids": [], "range": [0, 1]},
            {"id": "missing-field"},
            {"id": "wrong-pack", "claim_ids": [other_claim.id]},
            {"id": "unlinked", "claim_ids": [unlinked_claim.id]},
        ):
            rejected, status = request_error(
                Request(
                    f"{base_url}{endpoint}",
                    data=json.dumps(invalid_payload).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
            )
            assert status == 400
            assert rejected["error"]
        second, status = request_error(
            Request(
                f"{base_url}{endpoint}",
                data=json.dumps({"id": "second", "claim_ids": []}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 400
        assert "only one" in second["error"]

        empty_script = repository.create_script_under_content_piece_readiness(
            "http-script-claim-empty-script", piece.id, "Editorial-only narration."
        )
        empty_endpoint = f"/api/scripts/{empty_script.id}/claim-set"
        empty, status = post(empty_endpoint, {"id": "http-script-claim-empty", "claim_ids": []})
        assert status == 201
        assert empty["script_claim_set"]["claim_ids"] == []
        assert empty["script_claim_set"]["frozen_claims"] == []
        missing_script, status = request_error(
            Request(
                f"{base_url}/api/scripts/missing/claim-set",
                data=json.dumps({"id": "missing", "claim_ids": []}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 404
        assert "Script not found" in missing_script["error"]
        missing_claim_script = repository.create_script_under_content_piece_readiness(
            "http-script-claim-missing-script", piece.id, "Another narration."
        )
        missing_claim, status = request_error(
            Request(
                f"{base_url}/api/scripts/{missing_claim_script.id}/claim-set",
                data=json.dumps({"id": "missing-claim", "claim_ids": ["missing"]}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 404
        assert "Claim not found" in missing_claim["error"]
        assert repository.list_editorial_package_snapshots_for_content_piece(piece.id) == []
    finally:
        server.server_close()


def test_editorial_readiness_assessment_api_is_server_derived_and_append_only(
    tmp_path: Path,
) -> None:
    """v0.23 exposes immutable deterministic package readiness without a Gate."""

    server = create_server(port=0, database_path=tmp_path / "atlas.db")
    base_url = f"http://127.0.0.1:{server.server_address[1]}"

    def request_json(request: Request) -> tuple[dict, int]:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        with urlopen(request) as response:
            payload = json.load(response)
            status = response.status
        thread.join(timeout=2)
        return payload, status

    def request_error(request: Request) -> tuple[dict, int]:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        try:
            urlopen(request)
        except HTTPError as error:
            payload = json.loads(error.read())
            status = error.code
        else:
            raise AssertionError("The invalid editorial readiness request unexpectedly succeeded.")
        thread.join(timeout=2)
        return payload, status

    def post(path: str, payload: dict) -> tuple[dict, int]:
        return request_json(
            Request(
                f"{base_url}{path}",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )

    try:
        repository = server.repository
        opportunity_id = "http-editorial-readiness-opportunity"
        repository.create_opportunity(
            opportunity_id, "Opportunity", "Summary", "Why now", 1, "proposed"
        )
        pack = repository.create_research_pack(
            "http-editorial-readiness-pack", opportunity_id, 1, "Research pack"
        )
        claim = repository.create_claim(
            "http-editorial-readiness-claim",
            pack.id,
            "Frozen Claim.",
            "fact",
            "low",
            "stable",
            "reviewed",
            "",
        )
        ready = repository.create_research_readiness_assessment(
            "http-editorial-readiness-research-ready",
            pack.id,
            "Ready",
            {"summary": "Ready."},
            "policy-v1",
            "test",
            "web-test",
            "v1",
        )
        fields = ("Angle", "Thesis", "Promise", "Frame", ["Takeaway"])
        angle = repository.create_editorial_angle_under_research_readiness(
            "http-editorial-readiness-angle", opportunity_id, pack.id, ready.id, *fields
        )
        repository.link_claim_to_editorial_angle(angle.id, claim.id, "core")
        piece = repository.create_content_piece_under_editorial_angle_readiness(
            "http-editorial-readiness-piece", opportunity_id, angle.id, "video", "Working title"
        )

        def package(script_id: str, suffix: str):
            title = repository.create_title_option_under_content_piece_readiness(
                f"http-editorial-readiness-title-{suffix}", piece.id, f"Title {suffix}"
            )
            hook = repository.create_hook_option_under_content_piece_readiness(
                f"http-editorial-readiness-hook-{suffix}", piece.id, f"Hook {suffix}"
            )
            return repository.create_editorial_package_snapshot(
                f"http-editorial-readiness-package-{suffix}", piece.id, title.id, hook.id, script_id
            )

        missing_script = repository.create_script_under_content_piece_readiness(
            "http-editorial-readiness-missing-script", piece.id, "Narration."
        )
        missing_package = package(missing_script.id, "missing")
        endpoint = f"/api/editorial-package-snapshots/{missing_package.id}/readiness-assessments"
        created, status = post(endpoint, {"id": "http-editorial-readiness-not-ready"})
        assert status == 201
        assessment = created["assessment"]
        assert assessment["editorial_package_snapshot_id"] == missing_package.id
        assert assessment["outcome"] == "NotReady"
        assert assessment["findings"]["findings"][0]["code"] == "SCRIPT_CLAIM_SET_MISSING"
        assert assessment["findings"]["findings"][0]["blocking"] is True
        assert assessment["evaluator_id"] == "deterministic-editorial-readiness"
        assert assessment["evaluator_version"] == "v1"
        history, status = request_json(Request(f"{base_url}{endpoint}"))
        assert status == 200
        assert history["assessments"] == [assessment]
        fetched, status = request_json(
            Request(f"{base_url}/api/editorial-readiness-assessments/{assessment['id']}")
        )
        assert status == 200
        assert fetched["assessment"] == assessment
        rerun, status = post(endpoint, {"id": "http-editorial-readiness-not-ready-rerun"})
        assert status == 201
        assert [
            record["id"]
            for record in request_json(Request(f"{base_url}{endpoint}"))[0]["assessments"]
        ] == [
            assessment["id"],
            rerun["assessment"]["id"],
        ]

        empty_script = repository.create_script_under_content_piece_readiness(
            "http-editorial-readiness-empty-script", piece.id, "Empty narration."
        )
        empty_package = package(empty_script.id, "empty")
        repository.create_script_claim_set(
            "http-editorial-readiness-empty-set", empty_script.id, []
        )
        empty_created, status = post(
            f"/api/editorial-package-snapshots/{empty_package.id}/readiness-assessments",
            {"id": "http-editorial-readiness-ready"},
        )
        assert status == 201
        assert empty_created["assessment"]["outcome"] == "Ready"
        assert empty_created["assessment"]["findings"] == {"findings": []}

        populated_script = repository.create_script_under_content_piece_readiness(
            "http-editorial-readiness-populated-script", piece.id, "Populated narration."
        )
        populated_package = package(populated_script.id, "populated")
        repository.create_script_claim_set(
            "http-editorial-readiness-populated-set", populated_script.id, [claim.id]
        )
        populated_created, status = post(
            f"/api/editorial-package-snapshots/{populated_package.id}/readiness-assessments",
            {"id": "http-editorial-readiness-populated-ready"},
        )
        assert status == 201
        assert populated_created["assessment"]["outcome"] == "Ready"

        for invalid_payload in (
            {},
            {"id": "unsupported", "outcome": "Ready"},
            {"id": "unsupported-findings", "findings": {"findings": []}},
            {"id": "unsupported-evaluator", "evaluator_id": "caller"},
        ):
            rejected, status = request_error(
                Request(
                    f"{base_url}{endpoint}",
                    data=json.dumps(invalid_payload).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
            )
            assert status == 400
            assert rejected["error"]
        missing, status = request_error(
            Request(
                f"{base_url}/api/editorial-package-snapshots/missing/readiness-assessments",
                data=json.dumps({"id": "missing"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 404
        assert "EditorialPackageSnapshot" in missing["error"]
        missing_get, status = request_error(
            Request(f"{base_url}/api/editorial-readiness-assessments/missing")
        )
        assert status == 404
        assert "assessment not found" in missing_get["error"]
    finally:
        server.server_close()


def test_content_endpoint_adapts_persisted_research_angle_piece_script_and_scenes(
    tmp_path: Path,
) -> None:
    """The Content Workspace receives persistence through v0.6 while QA remains demo-backed."""

    server = create_server(port=0, database_path=tmp_path / "atlas.db")
    try:
        angle = server.repository.get_editorial_angle("editorial-angle-isa-decision-tree-v1")
        server.repository.update_editorial_angle(
            replace(angle, thesis="A persisted thesis exposed through the Content Workspace.")
        )
        content_piece = server.repository.get_content_piece("content-piece-isa-deadline-video-v1")
        server.repository.update_content_piece(
            replace(content_piece, working_title="A persisted ContentPiece title.")
        )
        server.repository.create_script(
            "script-isa-deadline-video-v2",
            content_piece.id,
            2,
            "A persisted latest narration version exposed through the Content Workspace.",
        )
        visual_plan = server.repository.get_visual_plan("visual-plan-isa-deadline-video-v1")
        server.repository.update_visual_plan(
            replace(
                visual_plan,
                visual_direction=(
                    "A persisted visual direction exposed through the Content Workspace."
                ),
            )
        )
        scene = server.repository.get_scene("scene-isa-deadline-video-v1-01")
        server.repository.update_scene(
            replace(scene, visual_intent="A persisted first ordered Scene intent.")
        )
        asset_spec = server.repository.get_asset_spec(
            "asset-spec-isa-scene-01-kitchen-background-v1"
        )
        server.repository.update_asset_spec(
            replace(asset_spec, description="A persisted AssetSpec description.")
        )
        server.repository.create_asset(
            "asset-isa-kitchen-background-v1",
            asset_spec.id,
            1,
            "assets/isa-kitchen-background-v1.png",
            "image/png",
            "manual",
        )
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        with urlopen(f"http://127.0.0.1:{server.server_address[1]}/api/demo/content") as response:
            payload = json.load(response)
        thread.join(timeout=2)
        content = payload["content"]
        assert content["visual_style"] == {
            "profile_id": "visual-style-profile-similarstoic-core-v3",
            "style_key": "similarstoic-core",
            "version": 3,
            "name": "SimilarStoic Core",
        }
        assert content["selected_angle"] == "The 15-minute ISA decision tree before the deadline."
        assert content["research"]["opportunity_id"] == "uk-isa-rules"
        assert content["research"]["version"] == 1
        assert len(content["research"]["claims"]) == 3
        assert content["research"]["claims"][0]["evidence"]
        assert content["editorial_angle"]["thesis"] == (
            "A persisted thesis exposed through the Content Workspace."
        )
        assert len(content["editorial_angles"]) == 2
        assert {claim["role"] for claim in content["editorial_angle"]["claims"]} == {
            "core",
            "supporting",
        }
        assert content["content_piece"]["working_title"] == "A persisted ContentPiece title."
        assert content["content_piece"]["latest_script"]["version"] == 2
        assert content["title"] == "A persisted ContentPiece title."
        assert content["script"] == (
            "A persisted latest narration version exposed through the Content Workspace."
        )
        assert content["visual_plan"]["visual_direction"] == (
            "A persisted visual direction exposed through the Content Workspace."
        )
        assert [scene["sequence"] for scene in content["visual_plan"]["scenes"]] == [1, 2, 3]
        assert content["visual_plan"]["scenes"][0]["visual_intent"] == (
            "A persisted first ordered Scene intent."
        )
        asset_specs = content["visual_plan"]["scenes"][0]["asset_specs"]
        assert len(asset_specs) == 2
        persisted_asset_spec = next(
            asset_spec
            for asset_spec in asset_specs
            if asset_spec["id"] == "asset-spec-isa-scene-01-kitchen-background-v1"
        )
        assert persisted_asset_spec["description"] == "A persisted AssetSpec description."
        assert persisted_asset_spec["generation_prompt"]
        persisted_asset_specs = [
            candidate
            for scene in content["visual_plan"]["scenes"]
            for candidate in scene["asset_specs"]
        ]
        assert {candidate["asset_type"] for candidate in persisted_asset_specs} == {
            "environment",
            "character",
            "graphic",
        }
        hamster_asset_spec = next(
            candidate
            for candidate in persisted_asset_specs
            if candidate["id"] == "asset-spec-isa-scene-01-hamster-sorting-v1"
        )
        assert hamster_asset_spec["character_profile"] == {
            "id": "character-profile-similarstoic-hamster-core-v1",
            "name": "SimilarStoic Hamster Core",
            "version": 1,
            "identity_description": (
                "A recognisable classic hamster with a recurring consistent identity, "
                "young-professional relatability and a small everyday sling/crossbody bag. "
                "The hamster uses hamster-native behaviour to embody SimilarStoic money, "
                "work, behaviour and life-strategy concepts, and is intended to remain "
                "recognisably the same individual across character assets."
            ),
        }
        assert persisted_asset_spec["character_profile"] is None
        assert all(
            candidate["generation_supported"]
            for candidate in persisted_asset_specs
            if candidate["asset_type"] == "character"
        )
        assert persisted_asset_spec["assets"] == [
            {
                "id": "asset-isa-kitchen-background-v1",
                "version": 1,
                "storage_path": "assets/isa-kitchen-background-v1.png",
                "media_type": "image/png",
                "source_kind": "manual",
            }
        ]
        assert all(
            not asset_spec["assets"]
            for scene in content["visual_plan"]["scenes"]
            for asset_spec in scene["asset_specs"]
            if asset_spec["id"] != "asset-spec-isa-scene-01-kitchen-background-v1"
        )
        assert content["scene_plan"] == " ".join(
            scene["visual_intent"] for scene in content["visual_plan"]["scenes"]
        )
        assert content["scene_plan"] != content_payload()["scene_plan"]
        assert content["qa"] == content_payload()["qa"]
    finally:
        server.server_close()


def test_content_endpoint_can_expose_explicitly_configured_v1_style(
    tmp_path: Path, monkeypatch
) -> None:
    """Profile selection remains configuration-only while v3 is the default."""

    monkeypatch.setenv("ATLAS_VISUAL_STYLE_PROFILE_ID", "visual-style-profile-similarstoic-core-v1")
    server = create_server(port=0, database_path=tmp_path / "atlas.db")
    try:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        with urlopen(f"http://127.0.0.1:{server.server_address[1]}/api/demo/content") as response:
            content = json.load(response)["content"]
        thread.join(timeout=2)
        assert content["visual_style"] == {
            "profile_id": "visual-style-profile-similarstoic-core-v1",
            "style_key": "similarstoic-core",
            "version": 1,
            "name": "SimilarStoic Core",
        }
        assert not {"selected", "current", "best", "approved"} & content["visual_style"].keys()
    finally:
        server.server_close()


def test_content_endpoint_has_no_demo_scene_plan_fallback_without_visual_plan(
    tmp_path: Path,
) -> None:
    """QA remains demo-backed when a temporary setup has no persisted VisualPlan."""

    server = create_server(port=0, database_path=tmp_path / "atlas.db")
    try:
        with server.repository.connection:
            server.repository.connection.execute("DELETE FROM assets")
            server.repository.connection.execute("DELETE FROM asset_specs")
            server.repository.connection.execute("DELETE FROM scenes")
            server.repository.connection.execute("DELETE FROM visual_plans")
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        with urlopen(f"http://127.0.0.1:{server.server_address[1]}/api/demo/content") as response:
            payload = json.load(response)
        thread.join(timeout=2)
        content = payload["content"]
        assert "visual_plan" not in content
        assert "scene_plan" not in content
        assert content["qa"] == content_payload()["qa"]
    finally:
        server.server_close()


def test_demo_endpoints_keep_discover_and_chat_compatible(tmp_path: Path) -> None:
    """Persistent angle work leaves Discover, Command Centre assets, and chat deterministic."""

    server = create_server(port=0, database_path=tmp_path / "atlas.db")
    try:
        for path in ("/", "/api/demo/opportunities", "/api/demo/chat?message=tomorrow"):
            thread = threading.Thread(target=server.handle_request)
            thread.start()
            with urlopen(f"http://127.0.0.1:{server.server_address[1]}{path}") as response:
                body = response.read()
            thread.join(timeout=2)
            if path == "/":
                assert b"Command Centre" in body
            elif "opportunities" in path:
                assert len(json.loads(body)["opportunities"]) == 6
            else:
                assert "ISA" in json.loads(body)["reply"]
    finally:
        server.server_close()


def test_discover_ui_exposes_minimal_persistent_idea_gate_controls() -> None:
    """Discover offers only snapshot review and immutable founder outcomes."""

    static_root = Path(__file__).parents[1] / "src/project_atlas/static"
    index = (static_root / "index.html").read_text(encoding="utf-8")
    script = (static_root / "app.js").read_text(encoding="utf-8")
    assert "idea-gate-review" in index
    assert "idea-gate-history" in index
    assert "open-idea-gate" in script
    assert 'data-outcome="Proceed"' in script
    assert 'data-outcome="Reject"' in script
    assert 'data-outcome="Steer"' in script
    assert "Steer requires founder direction." in script
    assert "/idea-gate-review-snapshots" in script
    assert "/idea-gate-history" in script
    assert "initiate-research" in script
    assert "data-decision-id" in script
    assert '"/research-packs"' in script
    assert "ResearchPack initiated with Idea Gate provenance." in script


def test_idea_gate_endpoints_freeze_reviews_and_persist_one_decision(tmp_path: Path) -> None:
    """The narrow Idea Gate API stores additive snapshots without downstream effects."""

    server = create_server(port=0, database_path=tmp_path / "atlas.db")
    base_url = f"http://127.0.0.1:{server.server_address[1]}"

    def request_json(request: Request | str) -> tuple[dict, int]:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        with urlopen(request) as response:
            payload = json.load(response)
            status = response.status
        thread.join(timeout=2)
        return payload, status

    try:
        opportunity_id = "uk-isa-rules"
        original = server.repository.get_opportunity(opportunity_id)
        research_count = server.repository.connection.execute(
            "SELECT COUNT(*) FROM research_packs"
        ).fetchone()[0]
        snapshot_response, status = request_json(
            Request(
                f"{base_url}/api/opportunities/{opportunity_id}/idea-gate-review-snapshots",
                method="POST",
            )
        )
        assert status == 201
        snapshot = snapshot_response["snapshot"]
        assert snapshot_response["kind"] == "idea_gate_review_snapshot"
        assert snapshot["payload_schema_version"] == 1
        assert snapshot["review_payload"]["opportunity"]["title"] == original.title
        assert snapshot["review_payload"]["subjects"][0]["id"] == "subject-isa"

        fetched, status = request_json(
            f"{base_url}/api/idea-gate-review-snapshots/{snapshot['id']}"
        )
        assert status == 200
        assert fetched["snapshot"] == snapshot

        thread = threading.Thread(target=server.handle_request)
        thread.start()
        invalid_steer = Request(
            f"{base_url}/api/idea-gate-review-snapshots/{snapshot['id']}/decisions",
            data=json.dumps({"outcome": "Steer", "founder_direction": "   "}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urlopen(invalid_steer)
        except HTTPError as error:
            assert error.code == 400
            assert "requires non-empty" in error.read().decode()
        else:
            raise AssertionError("Idea Gate accepted an empty Steer direction.")
        thread.join(timeout=2)

        decision_response, status = request_json(
            Request(
                f"{base_url}/api/idea-gate-review-snapshots/{snapshot['id']}/decisions",
                data=json.dumps(
                    {
                        "outcome": "Steer",
                        "founder_direction": "Lead with the practical deadline choice.",
                    }
                ).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 201
        assert decision_response["decision"]["outcome"] == "Steer"
        assert decision_response["decision"]["founder_direction"] == (
            "Lead with the practical deadline choice."
        )

        server.repository.update_opportunity(
            replace(original, title="A later mutable Opportunity presentation")
        )
        history, status = request_json(
            f"{base_url}/api/opportunities/{opportunity_id}/idea-gate-history"
        )
        assert status == 200
        assert history["history"][0]["snapshot"]["review_payload"]["opportunity"]["title"] == (
            original.title
        )
        assert history["history"][0]["decision"]["id"] == decision_response["decision"]["id"]
        assert server.repository.get_opportunity(opportunity_id).status == original.status
        assert (
            server.repository.connection.execute("SELECT COUNT(*) FROM research_packs").fetchone()[
                0
            ]
            == research_count
        )

        thread = threading.Thread(target=server.handle_request)
        thread.start()
        duplicate = Request(
            f"{base_url}/api/idea-gate-review-snapshots/{snapshot['id']}/decisions",
            data=json.dumps({"outcome": "Proceed"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urlopen(duplicate)
        except HTTPError as error:
            assert error.code == 400
            assert "only one decision" in error.read().decode()
        else:
            raise AssertionError("Idea Gate accepted a second decision for one snapshot.")
        thread.join(timeout=2)
    finally:
        server.server_close()


def test_research_pack_initiation_endpoint_preserves_idea_gate_provenance(tmp_path: Path) -> None:
    """The narrow API deliberately creates only qualifying provenance-linked ResearchPacks."""

    server = create_server(port=0, database_path=tmp_path / "atlas.db")
    base_url = f"http://127.0.0.1:{server.server_address[1]}"

    def request_json(request: Request) -> tuple[dict, int]:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        with urlopen(request) as response:
            payload = json.load(response)
            status = response.status
        thread.join(timeout=2)
        return payload, status

    def request_error(request: Request) -> tuple[dict, int]:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        try:
            urlopen(request)
        except HTTPError as error:
            payload = json.loads(error.read())
            status = error.code
        else:
            raise AssertionError("The invalid research-initiation request unexpectedly succeeded.")
        thread.join(timeout=2)
        return payload, status

    def initiate(opportunity_id: str, payload: dict) -> tuple[dict, int]:
        return request_json(
            Request(
                f"{base_url}/api/opportunities/{opportunity_id}/research-packs",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )

    try:
        repository = server.repository
        opportunity_id = "uk-isa-rules"
        original_status = repository.get_opportunity(opportunity_id).status
        initial_count = repository.connection.execute(
            "SELECT COUNT(*) FROM research_packs"
        ).fetchone()[0]

        proceed_snapshot = repository.create_idea_gate_review_snapshot(
            "http-initiation-proceed-snapshot", opportunity_id
        )
        proceed = repository.record_idea_gate_decision(
            "http-initiation-proceed-decision", proceed_snapshot.id, "Proceed"
        )
        assert (
            repository.connection.execute("SELECT COUNT(*) FROM research_packs").fetchone()[0]
            == initial_count
        )
        created, status = initiate(
            opportunity_id,
            {
                "id": "research-pack-http-proceed-v2",
                "version": 2,
                "summary": "A deliberately initiated Proceed ResearchPack.",
                "idea_gate_decision_id": proceed.id,
            },
        )
        assert status == 201
        assert created["kind"] == "research_pack"
        research_pack = created["research_pack"]
        assert research_pack["id"] == "research-pack-http-proceed-v2"
        assert research_pack["opportunity_id"] == opportunity_id
        assert research_pack["idea_gate_decision_id"] == proceed.id
        assert research_pack["idea_gate_provenance"]["decision"]["outcome"] == "Proceed"
        assert research_pack["idea_gate_provenance"]["snapshot"]["id"] == proceed_snapshot.id

        steer_snapshot = repository.create_idea_gate_review_snapshot(
            "http-initiation-steer-snapshot", opportunity_id
        )
        steer = repository.record_idea_gate_decision(
            "http-initiation-steer-decision",
            steer_snapshot.id,
            "Steer",
            founder_direction="Lead with the practical deadline choice.",
        )
        created, status = initiate(
            opportunity_id,
            {
                "id": "research-pack-http-steer-v3",
                "version": 3,
                "summary": "A deliberately initiated Steer ResearchPack.",
                "idea_gate_decision_id": steer.id,
                "metadata": {"review": "manual"},
            },
        )
        assert status == 201
        assert (
            created["research_pack"]["idea_gate_provenance"]["decision"]["founder_direction"]
            == "Lead with the practical deadline choice."
        )
        assert repository.get_research_pack("research-pack-http-steer-v3").metadata == {
            "review": "manual"
        }

        reject_snapshot = repository.create_idea_gate_review_snapshot(
            "http-initiation-reject-snapshot", opportunity_id
        )
        reject = repository.record_idea_gate_decision(
            "http-initiation-reject-decision", reject_snapshot.id, "Reject"
        )
        payload, status = request_error(
            Request(
                f"{base_url}/api/opportunities/{opportunity_id}/research-packs",
                data=json.dumps(
                    {
                        "id": "research-pack-http-reject-v4",
                        "version": 4,
                        "summary": "This must not be created.",
                        "idea_gate_decision_id": reject.id,
                    }
                ).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 400
        assert "Proceed or Steer" in payload["error"]

        payload, status = request_error(
            Request(
                f"{base_url}/api/opportunities/{opportunity_id}/research-packs",
                data=json.dumps(
                    {
                        "id": "research-pack-http-missing-v4",
                        "version": 4,
                        "summary": "This must not be created.",
                        "idea_gate_decision_id": "missing-decision",
                    }
                ).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 404
        assert "not found" in payload["error"]

        other_snapshot = repository.create_idea_gate_review_snapshot(
            "http-initiation-other-snapshot", "credit-utilisation"
        )
        other_decision = repository.record_idea_gate_decision(
            "http-initiation-other-decision", other_snapshot.id, "Proceed"
        )
        payload, status = request_error(
            Request(
                f"{base_url}/api/opportunities/{opportunity_id}/research-packs",
                data=json.dumps(
                    {
                        "id": "research-pack-http-mismatch-v4",
                        "version": 4,
                        "summary": "This must not be created.",
                        "idea_gate_decision_id": other_decision.id,
                    }
                ).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 400
        assert "must belong" in payload["error"]

        payload, status = request_error(
            Request(
                f"{base_url}/api/opportunities/{opportunity_id}/research-packs",
                data=json.dumps(
                    {
                        "id": "research-pack-http-duplicate-v2",
                        "version": 2,
                        "summary": "Duplicate version.",
                        "idea_gate_decision_id": proceed.id,
                    }
                ).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 400
        assert "UNIQUE constraint failed" in payload["error"]

        payload, status = request_error(
            Request(
                f"{base_url}/api/opportunities/{opportunity_id}/research-packs",
                data=b"[]",
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 400
        assert "must be an object" in payload["error"]
        assert repository.get_opportunity(opportunity_id).status == original_status
        assert (
            repository.connection.execute("SELECT COUNT(*) FROM research_packs").fetchone()[0]
            == initial_count + 2
        )
    finally:
        server.server_close()


def test_generation_endpoint_uses_persisted_prompt_and_exposes_execution(tmp_path: Path) -> None:
    """POST generation ignores caller prompt text and returns durable provenance."""

    generator = FakeImageGenerator()
    server = create_server(
        port=0,
        database_path=tmp_path / "atlas.db",
        generator=generator,
        asset_storage_root=tmp_path / "assets",
    )
    try:
        asset_spec = server.repository.get_asset_spec(
            "asset-spec-isa-scene-01-kitchen-background-v1"
        )
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        request = Request(
            f"http://127.0.0.1:{server.server_address[1]}/api/asset-specs/{asset_spec.id}/generate",
            data=b'{"prompt":"caller supplied replacement"}',
            method="POST",
        )
        with urlopen(request) as response:
            payload = json.load(response)
        thread.join(timeout=2)
        assert payload["execution"]["outcome"] == "succeeded"
        assert (
            payload["execution"]["visual_style_profile_id"]
            == "visual-style-profile-similarstoic-core-v3"
        )
        assert payload["asset"]["generation_execution_id"] == payload["execution"]["id"]
        assert asset_spec.generation_prompt in generator.inputs[0].prompt
        assert generator.inputs[0].style["style_key"] == "similarstoic-core"
        assert (
            tmp_path / "assets" / server.repository.get_asset(payload["asset"]["id"]).storage_path
        ).exists()

        thread = threading.Thread(target=server.handle_request)
        thread.start()
        with urlopen(f"http://127.0.0.1:{server.server_address[1]}/api/demo/content") as response:
            content = json.load(response)["content"]
        thread.join(timeout=2)
        persisted_spec = next(
            candidate
            for scene in content["visual_plan"]["scenes"]
            for candidate in scene["asset_specs"]
            if candidate["id"] == asset_spec.id
        )
        assert persisted_spec["generation_executions"][-1]["outcome"] == "succeeded"
        assert persisted_spec["assets"][-1]["generation_execution_id"] == payload["execution"]["id"]
        assert persisted_spec["generation_supported"] is True
    finally:
        server.server_close()


def test_generation_endpoint_represents_provider_failure_without_asset(tmp_path: Path) -> None:
    """A provider failure is visible to the Workspace but does not register an Asset."""

    server = create_server(
        port=0,
        database_path=tmp_path / "atlas.db",
        generator=FakeImageGenerator(
            GenerationFailure("Fake provider rejected generation.", error_code="rejected")
        ),
        asset_storage_root=tmp_path / "assets",
    )
    try:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        request = Request(
            "http://127.0.0.1:"
            f"{server.server_address[1]}/api/asset-specs/"
            "asset-spec-isa-scene-01-kitchen-background-v1/generate",
            method="POST",
        )
        with urlopen(request) as response:
            payload = json.load(response)
        thread.join(timeout=2)
        assert payload["execution"]["outcome"] == "failed"
        assert payload["execution"]["error_code"] == "rejected"
        assert payload["asset"] is None
        assert (
            server.repository.connection.execute("SELECT COUNT(*) FROM assets").fetchone()[0] == 0
        )
    finally:
        server.server_close()


def test_bootstrap_reference_endpoint_is_explicit_and_stops_after_first_set(tmp_path: Path) -> None:
    """The local UI API exposes first-reference generation without changing normal generation."""

    storage_root = tmp_path / "assets"
    generator = FakeImageGenerator()
    server = create_server(
        port=0,
        database_path=tmp_path / "atlas.db",
        generator=generator,
        asset_storage_root=storage_root,
    )
    try:
        asset_spec_id = "asset-spec-isa-scene-01-hamster-sorting-v1"

        def request_json(request: Request | str) -> tuple[dict, int]:
            thread = threading.Thread(target=server.handle_request)
            thread.start()
            with urlopen(request) as response:
                payload = json.load(response)
                status = response.status
            thread.join(timeout=2)
            return payload, status

        content, _ = request_json(f"http://127.0.0.1:{server.server_address[1]}/api/demo/content")
        character_spec = next(
            candidate
            for scene in content["content"]["visual_plan"]["scenes"]
            for candidate in scene["asset_specs"]
            if candidate["id"] == asset_spec_id
        )
        assert character_spec["bootstrap_reference_generation_available"] is True

        bootstrapped, status = request_json(
            Request(
                "http://127.0.0.1:"
                f"{server.server_address[1]}/api/asset-specs/{asset_spec_id}/"
                "bootstrap-character-reference",
                method="POST",
            )
        )
        assert status == 200
        assert bootstrapped["kind"] == "character_reference_bootstrap"
        assert bootstrapped["execution"]["character_reference_set_id"] is None
        assert bootstrapped["asset"] is not None
        assert len(generator.inputs) == 1
        assert generator.inputs[0].payload()["schema_version"] == 3

        profile_id = "character-profile-similarstoic-hamster-core-v1"
        reference_set, status = request_json(
            Request(
                "http://127.0.0.1:"
                f"{server.server_address[1]}/api/character-profiles/{profile_id}/reference-sets",
                data=json.dumps({"asset_ids": [bootstrapped["asset"]["id"]]}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 201
        assert reference_set["reference_set"]["version"] == 1

        thread = threading.Thread(target=server.handle_request)
        thread.start()
        blocked_request = Request(
            "http://127.0.0.1:"
            f"{server.server_address[1]}/api/asset-specs/{asset_spec_id}/"
            "bootstrap-character-reference",
            method="POST",
        )
        try:
            urlopen(blocked_request)
        except HTTPError as error:
            assert error.code == 400
            assert "unavailable after a CharacterReferenceSet exists" in error.read().decode()
        else:
            raise AssertionError("Bootstrap API accepted a profile with a reference set.")
        thread.join(timeout=2)
        assert len(generator.inputs) == 1

        refreshed, _ = request_json(f"http://127.0.0.1:{server.server_address[1]}/api/demo/content")
        refreshed_spec = next(
            candidate
            for scene in refreshed["content"]["visual_plan"]["scenes"]
            for candidate in scene["asset_specs"]
            if candidate["id"] == asset_spec_id
        )
        assert refreshed_spec["bootstrap_reference_generation_available"] is False
    finally:
        server.server_close()


def test_reference_review_serves_eligible_hamster_and_creates_ordered_set(tmp_path: Path) -> None:
    """The local UI API exposes only eligible generated hamster evidence for selection."""

    storage_root = tmp_path / "assets"
    server = create_server(
        port=0,
        database_path=tmp_path / "atlas.db",
        generator=FakeImageGenerator(),
        asset_storage_root=storage_root,
    )
    profile_id = "character-profile-similarstoic-hamster-core-v1"
    ensure_character_reference_set(server, storage_root)

    def request_json(request: Request | str) -> tuple[dict, int]:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        with urlopen(request) as response:
            payload = json.load(response)
            status = response.status
        thread.join(timeout=2)
        return payload, status

    try:
        first, _ = request_json(
            Request(
                "http://127.0.0.1:"
                f"{server.server_address[1]}/api/asset-specs/"
                "asset-spec-isa-scene-01-hamster-sorting-v1/generate",
                method="POST",
            )
        )
        second, _ = request_json(
            Request(
                "http://127.0.0.1:"
                f"{server.server_address[1]}/api/asset-specs/"
                "asset-spec-isa-scene-03-hamster-reaction-v1/generate",
                method="POST",
            )
        )
        first_asset_id = first["asset"]["id"]
        second_asset_id = second["asset"]["id"]

        thread = threading.Thread(target=server.handle_request)
        thread.start()
        with urlopen(
            f"http://127.0.0.1:{server.server_address[1]}/api/assets/{first_asset_id}/content"
        ) as response:
            assert response.headers["Content-Type"] == "image/png"
            assert response.read() == b"http fake image"
        thread.join(timeout=2)

        content, _ = request_json(f"http://127.0.0.1:{server.server_address[1]}/api/demo/content")
        review = content["content"]["character_reference_review"]
        assert review["character_profile"]["id"] == profile_id
        assert {first_asset_id, second_asset_id} <= {
            candidate["id"] for candidate in review["eligible_assets"]
        }
        assert review["eligible_assets"][0]["content_digest"]
        assert (
            review["eligible_assets"][0]["generation_execution"]["character_profile"]["id"]
            == profile_id
        )

        created, status = request_json(
            Request(
                "http://127.0.0.1:"
                f"{server.server_address[1]}/api/character-profiles/{profile_id}/reference-sets",
                data=json.dumps({"asset_ids": [second_asset_id, first_asset_id]}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 201
        assert created["reference_set"]["version"] == 2
        assert [member["asset"]["id"] for member in created["reference_set"]["members"]] == [
            second_asset_id,
            first_asset_id,
        ]

        content, _ = request_json(f"http://127.0.0.1:{server.server_address[1]}/api/demo/content")
        retained = content["content"]["character_reference_review"]["reference_sets"]
        assert retained[-1]["members"][0]["asset"]["content_digest"]
        assert (
            "At character-generation time, Conveyor resolves the highest version"
            in (Path(__file__).parents[1] / "src/project_atlas/static/app.js").read_text()
        )
        script = (Path(__file__).parents[1] / "src/project_atlas/static/app.js").read_text()
        assert "referenceSelection.push(assetId)" in script
        assert "asset_ids: referenceSelection" in script
    finally:
        server.server_close()


def test_asset_content_endpoint_rejects_unknown_missing_and_unsafe_files(tmp_path: Path) -> None:
    """Asset content is resolved by Atlas ID and never by an arbitrary filesystem path."""

    storage_root = tmp_path / "assets"
    server = create_server(
        port=0,
        database_path=tmp_path / "atlas.db",
        generator=FakeImageGenerator(),
        asset_storage_root=storage_root,
    )
    try:
        asset_spec = server.repository.get_asset_spec("asset-spec-isa-scene-01-hamster-sorting-v1")
        ensure_character_reference_set(server, storage_root)
        missing = server.generation_service.generate_asset_spec(asset_spec.id).asset
        assert missing is not None
        (storage_root / missing.storage_path).unlink()
        unsafe = server.repository.create_asset(
            "asset-unsafe-generated-path-v1",
            asset_spec.id,
            2,
            "../outside.png",
            "image/png",
            "generated",
        )
        absolute = server.repository.create_asset(
            "asset-absolute-generated-path-v1",
            asset_spec.id,
            3,
            str((tmp_path / "outside.png").resolve()),
            "image/png",
            "generated",
        )
        unsupported_media = server.repository.create_asset(
            "asset-unsupported-media-v1",
            asset_spec.id,
            4,
            "unsupported.txt",
            "text/plain",
            "generated",
        )
        rejected_asset_ids = [
            "missing-asset",
            missing.id,
            unsafe.id,
            absolute.id,
            unsupported_media.id,
        ]
        if os.name == "nt":
            backslash_escape = server.repository.create_asset(
                "asset-backslash-generated-path-v1",
                asset_spec.id,
                5,
                r"..\outside.png",
                "image/png",
                "generated",
            )
            rejected_asset_ids.append(backslash_escape.id)
        for asset_id in rejected_asset_ids:
            thread = threading.Thread(target=server.handle_request)
            thread.start()
            try:
                urlopen(
                    f"http://127.0.0.1:{server.server_address[1]}/api/assets/{asset_id}/content"
                )
            except HTTPError as error:
                assert error.code == 404
            else:
                raise AssertionError("Unsafe or unknown Asset content was served.")
            thread.join(timeout=2)
    finally:
        server.server_close()


def test_research_readiness_assessment_api_is_server_frozen_and_history_only(
    tmp_path: Path,
) -> None:
    """The v0.17 API persists additive assessment history without a UI or evaluator."""

    server = create_server(port=0, database_path=tmp_path / "atlas.db")
    base_url = f"http://127.0.0.1:{server.server_address[1]}"

    def request_json(request: Request | str) -> tuple[dict, int]:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        with urlopen(request) as response:
            payload = json.load(response)
            status = response.status
        thread.join(timeout=2)
        return payload, status

    def request_error(request: Request) -> tuple[dict, int]:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        try:
            urlopen(request)
        except HTTPError as error:
            payload = json.loads(error.read())
            status = error.code
        else:
            raise AssertionError("The invalid readiness request unexpectedly succeeded.")
        thread.join(timeout=2)
        return payload, status

    try:
        pack_id = "research-pack-isa-deadline-v1"
        history, status = request_json(
            f"{base_url}/api/research-packs/{pack_id}/readiness-assessments"
        )
        assert status == 200
        assert history["kind"] == "research_readiness_assessment_history"
        assert history["assessments"] == []

        endpoint = f"{base_url}/api/research-packs/{pack_id}/readiness-assessments"
        base_payload = {
            "id": "http-readiness-assessment-a",
            "outcome": "Ready",
            "findings": {"summary": "The stored evidence is ready for this test."},
            "policy_version": "readiness-policy-v1",
            "producer_kind": "test",
            "producer_identifier": "http-test",
            "producer_implementation_version": "v1",
        }
        created, status = request_json(
            Request(
                endpoint,
                data=json.dumps(base_payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 201
        assessment = created["assessment"]
        assert assessment["outcome"] == "Ready"
        assert assessment["frozen_evidence_state"]["research_pack"]["id"] == pack_id
        assert assessment["frozen_evidence_state"]["schema_version"] == 1

        fetched, status = request_json(
            f"{base_url}/api/research-readiness-assessments/{assessment['id']}"
        )
        assert status == 200
        assert fetched["assessment"] == assessment

        second_payload = base_payload | {
            "id": "http-readiness-assessment-b",
            "outcome": "Blocked",
            "findings": {"summary": "The required source is unavailable."},
        }
        created_second, status = request_json(
            Request(
                endpoint,
                data=json.dumps(second_payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 201
        history, status = request_json(endpoint)
        assert status == 200
        assert [item["id"] for item in history["assessments"]] == [
            assessment["id"],
            created_second["assessment"]["id"],
        ]

        invalid, status = request_error(
            Request(
                endpoint,
                data=json.dumps(base_payload | {"id": "http-invalid", "outcome": "ready"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 400
        assert "outcome" in invalid["error"]
        for key in (
            "findings",
            "policy_version",
            "producer_kind",
            "producer_identifier",
            "producer_implementation_version",
        ):
            incomplete, status = request_error(
                Request(
                    endpoint,
                    data=json.dumps(
                        {
                            item_key: value
                            for item_key, value in (base_payload | {"id": f"http-{key}"}).items()
                            if item_key != key
                        }
                    ).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
            )
            assert status == 400
            assert incomplete["error"]
        duplicate, status = request_error(
            Request(
                endpoint,
                data=json.dumps(base_payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 400
        assert "already exists" in duplicate["error"]
        rejected_snapshot, status = request_error(
            Request(
                endpoint,
                data=json.dumps(
                    base_payload | {"id": "http-snapshot", "frozen_evidence_state": {}}
                ).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 400
        assert "built by the server" in rejected_snapshot["error"]
        missing, status = request_error(
            Request(
                f"{base_url}/api/research-packs/missing/readiness-assessments",
                data=json.dumps(base_payload | {"id": "http-missing"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 404
        assert "ResearchPack" in missing["error"]
        missing_get, status = request_error(
            Request(
                f"{base_url}/api/research-readiness-assessments/missing",
                method="GET",
            )
        )
        assert status == 404
        assert "not found" in missing_get["error"]
    finally:
        server.server_close()


def test_editorial_angle_lifecycle_api_requires_explicit_exact_ready_provenance(
    tmp_path: Path,
) -> None:
    """v0.18 exposes only deliberate Ready-assessment Angle initiation over HTTP."""

    server = create_server(port=0, database_path=tmp_path / "atlas.db")
    base_url = f"http://127.0.0.1:{server.server_address[1]}"

    def request_json(request: Request) -> tuple[dict, int]:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        with urlopen(request) as response:
            payload = json.load(response)
            status = response.status
        thread.join(timeout=2)
        return payload, status

    def request_error(request: Request) -> tuple[dict, int]:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        try:
            urlopen(request)
        except HTTPError as error:
            payload = json.loads(error.read())
            status = error.code
        else:
            raise AssertionError("The invalid lifecycle request unexpectedly succeeded.")
        thread.join(timeout=2)
        return payload, status

    try:
        repository = server.repository
        pack_id = "research-pack-isa-deadline-v1"
        other_opportunity_id = "http-angle-other-opportunity"
        repository.create_opportunity(
            other_opportunity_id, "Other", "Summary", "Why now", 1, "proposed"
        )
        other_pack = repository.create_research_pack(
            "http-angle-other-pack", other_opportunity_id, 1, "Other pack"
        )

        def assessment(assessment_id: str, target_pack_id: str, outcome: str):
            return repository.create_research_readiness_assessment(
                assessment_id,
                target_pack_id,
                outcome,
                {"summary": f"{outcome} for HTTP lifecycle testing."},
                "readiness-policy-v1",
                "test",
                "http-test",
                "v1",
            )

        ready = assessment("http-angle-ready", pack_id, "Ready")
        needs_more = assessment("http-angle-needs-more", pack_id, "NeedsMoreResearch")
        blocked = assessment("http-angle-blocked", pack_id, "Blocked")
        other_ready = assessment("http-angle-other-ready", other_pack.id, "Ready")
        endpoint = f"{base_url}/api/opportunities/uk-isa-rules/editorial-angles"
        payload = {
            "id": "http-readiness-angle",
            "research_pack_id": pack_id,
            "research_readiness_assessment_id": ready.id,
            "working_title": "A deliberate lifecycle Angle",
            "thesis": "Exact Ready provenance is stored.",
            "audience_promise": "Understand the decision boundary.",
            "framing": "A focused explainer.",
            "key_takeaways": ["Ready provenance is exact."],
            "metadata": {"source": "http-test"},
        }
        created, status = request_json(
            Request(
                endpoint,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 201
        angle = created["editorial_angle"]
        assert created["kind"] == "editorial_angle"
        assert angle["opportunity_id"] == "uk-isa-rules"
        assert angle["research_pack_id"] == pack_id
        assert angle["research_readiness_assessment_id"] == ready.id
        assert (
            repository.connection.execute(
                "SELECT COUNT(*) FROM content_pieces WHERE editorial_angle_id = ?", (angle["id"],)
            ).fetchone()[0]
            == 0
        )

        for assessment_id in (needs_more.id, blocked.id):
            rejected, status = request_error(
                Request(
                    endpoint,
                    data=json.dumps(
                        payload
                        | {
                            "id": f"http-rejected-{assessment_id}",
                            "research_readiness_assessment_id": assessment_id,
                        }
                    ).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
            )
            assert status == 400
            assert "Ready" in rejected["error"]
        for patch in (
            {"research_readiness_assessment_id": "missing"},
            {"research_pack_id": other_pack.id},
            {"research_readiness_assessment_id": other_ready.id},
            {"key_takeaways": "not-a-list"},
        ):
            rejected, status = request_error(
                Request(
                    endpoint,
                    data=json.dumps(
                        payload | {"id": f"http-invalid-{len(patch)}"} | patch
                    ).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
            )
            assert status == (
                404 if patch.get("research_readiness_assessment_id") == "missing" else 400
            )
            assert rejected["error"]
        missing_opportunity, status = request_error(
            Request(
                f"{base_url}/api/opportunities/missing/editorial-angles",
                data=json.dumps(payload | {"id": "http-missing-opportunity"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 404
        assert "not found" in missing_opportunity["error"]
    finally:
        server.server_close()
