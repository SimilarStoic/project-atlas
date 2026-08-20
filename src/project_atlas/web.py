"""Dependency-free local server for the Conveyor MVP UI shell."""

from __future__ import annotations

import argparse
import json
import mimetypes
import sqlite3
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from project_atlas.demo_data import ACTIVITY, chat_reply, content_payload
from project_atlas.generation import (
    AssetGenerator,
    GenerationService,
    InvalidCharacterReferenceBootstrap,
    LocalAssetStorage,
    MissingCharacterReferenceSet,
    MissingProviderConfiguration,
    MissingVisualStyleProfile,
    OpenAIImageGenerator,
    UnsupportedGenerationType,
)
from project_atlas.persistence import AtlasRepository

STATIC_DIRECTORY = Path(__file__).parent / "static"


class AtlasRequestHandler(BaseHTTPRequestHandler):
    """Serve local demo data and the static browser UI."""

    server_version = "ProjectAtlasMVP/0.1"

    def do_GET(self) -> None:  # noqa: N802
        """Handle only local static assets and demo API responses."""

        parsed = urlparse(self.path)
        if parsed.path == "/api/demo/opportunities":
            self._send_json(
                {"kind": "demo", "opportunities": self.server.repository.discover_payload()}
            )
            return
        idea_gate_history_prefix = "/api/opportunities/"
        idea_gate_history_suffix = "/idea-gate-history"
        if parsed.path.startswith(idea_gate_history_prefix) and parsed.path.endswith(
            idea_gate_history_suffix
        ):
            opportunity_id = unquote(
                parsed.path[len(idea_gate_history_prefix) : -len(idea_gate_history_suffix)]
            ).strip("/")
            if not opportunity_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                self._send_json(self.server.repository.idea_gate_history_payload(opportunity_id))
            except KeyError:
                self._send_json({"error": "Opportunity not found."}, HTTPStatus.NOT_FOUND)
            return
        idea_gate_snapshot_prefix = "/api/idea-gate-review-snapshots/"
        if parsed.path.startswith(idea_gate_snapshot_prefix):
            snapshot_id = unquote(parsed.path[len(idea_gate_snapshot_prefix) :]).strip("/")
            if not snapshot_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                self._send_json(
                    {
                        "kind": "idea_gate_review_snapshot",
                        "snapshot": self.server.repository.idea_gate_review_snapshot_payload(
                            snapshot_id
                        ),
                    }
                )
            except KeyError:
                self._send_json(
                    {"error": "Idea Gate review snapshot not found."}, HTTPStatus.NOT_FOUND
                )
            return
        research_readiness_prefix = "/api/research-packs/"
        research_readiness_suffix = "/readiness-assessments"
        if parsed.path.startswith(research_readiness_prefix) and parsed.path.endswith(
            research_readiness_suffix
        ):
            research_pack_id = unquote(
                parsed.path[len(research_readiness_prefix) : -len(research_readiness_suffix)]
            ).strip("/")
            if not research_pack_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                self._send_json(
                    {
                        "kind": "research_readiness_assessment_history",
                        **self.server.repository.research_readiness_history_payload(
                            research_pack_id
                        ),
                    }
                )
            except KeyError:
                self._send_json({"error": "ResearchPack not found."}, HTTPStatus.NOT_FOUND)
            return
        readiness_assessment_prefix = "/api/research-readiness-assessments/"
        if parsed.path.startswith(readiness_assessment_prefix):
            assessment_id = unquote(parsed.path[len(readiness_assessment_prefix) :]).strip("/")
            if not assessment_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                self._send_json(
                    {
                        "kind": "research_readiness_assessment",
                        "assessment": self.server.repository.research_readiness_assessment_payload(
                            assessment_id
                        ),
                    }
                )
            except KeyError:
                self._send_json(
                    {"error": "Research readiness assessment not found."}, HTTPStatus.NOT_FOUND
                )
            return
        script_claim_set_prefix = "/api/scripts/"
        script_claim_set_suffix = "/claim-set"
        if parsed.path.startswith(script_claim_set_prefix) and parsed.path.endswith(
            script_claim_set_suffix
        ):
            script_id = unquote(
                parsed.path[len(script_claim_set_prefix) : -len(script_claim_set_suffix)]
            ).strip("/")
            if not script_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                claim_set = self.server.repository.script_claim_set_payload(script_id)
            except KeyError:
                self._send_json({"error": "Script not found."}, HTTPStatus.NOT_FOUND)
                return
            except ValueError as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            self._send_json(
                {
                    "kind": "script_claim_set",
                    "script_id": script_id,
                    "script_claim_set": claim_set,
                }
            )
            return
        editorial_readiness_history_prefix = "/api/editorial-package-snapshots/"
        editorial_readiness_history_suffix = "/readiness-assessments"
        if parsed.path.startswith(editorial_readiness_history_prefix) and parsed.path.endswith(
            editorial_readiness_history_suffix
        ):
            snapshot_id = unquote(
                parsed.path[
                    len(editorial_readiness_history_prefix) : -len(
                        editorial_readiness_history_suffix
                    )
                ]
            ).strip("/")
            if not snapshot_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                self._send_json(
                    {
                        "kind": "editorial_readiness_assessment_history",
                        **self.server.repository.editorial_readiness_assessment_history_payload(
                            snapshot_id
                        ),
                    }
                )
            except KeyError:
                self._send_json(
                    {"error": "EditorialPackageSnapshot not found."}, HTTPStatus.NOT_FOUND
                )
            return
        editorial_readiness_assessment_prefix = "/api/editorial-readiness-assessments/"
        if parsed.path.startswith(editorial_readiness_assessment_prefix):
            assessment_id = unquote(
                parsed.path[len(editorial_readiness_assessment_prefix) :]
            ).strip("/")
            if not assessment_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                self._send_json(
                    {
                        "kind": "editorial_readiness_assessment",
                        "assessment": self.server.repository.editorial_readiness_assessment_payload(
                            assessment_id
                        ),
                    }
                )
            except KeyError:
                self._send_json(
                    {"error": "Editorial readiness assessment not found."}, HTTPStatus.NOT_FOUND
                )
            return
        editorial_gate_history_prefix = "/api/editorial-package-snapshots/"
        editorial_gate_history_suffix = "/gate-decisions"
        if parsed.path.startswith(editorial_gate_history_prefix) and parsed.path.endswith(
            editorial_gate_history_suffix
        ):
            snapshot_id = unquote(
                parsed.path[
                    len(editorial_gate_history_prefix) : -len(editorial_gate_history_suffix)
                ]
            ).strip("/")
            if not snapshot_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                self._send_json(
                    {
                        "kind": "editorial_gate_decision_history",
                        **self.server.repository.editorial_gate_decision_history_payload(
                            snapshot_id
                        ),
                    }
                )
            except KeyError:
                self._send_json(
                    {"error": "EditorialPackageSnapshot not found."}, HTTPStatus.NOT_FOUND
                )
            return
        editorial_gate_decision_prefix = "/api/editorial-gate-decisions/"
        if parsed.path.startswith(editorial_gate_decision_prefix):
            decision_id = unquote(parsed.path[len(editorial_gate_decision_prefix) :]).strip("/")
            if not decision_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                self._send_json(
                    {
                        "kind": "editorial_gate_decision",
                        "decision": self.server.repository.editorial_gate_decision_payload(
                            decision_id
                        ),
                    }
                )
            except KeyError:
                self._send_json(
                    {"error": "Editorial Gate decision not found."}, HTTPStatus.NOT_FOUND
                )
            return
        content_piece_prefix = "/api/content-pieces/"
        editorial_history_routes = {
            "/title-options": (
                "title_option_history",
                self.server.repository.list_title_options_for_content_piece,
                self.server.repository.title_option_payload,
                "title_options",
            ),
            "/hook-options": (
                "hook_option_history",
                self.server.repository.list_hook_options_for_content_piece,
                self.server.repository.hook_option_payload,
                "hook_options",
            ),
            "/editorial-package-snapshots": (
                "editorial_package_snapshot_history",
                self.server.repository.list_editorial_package_snapshots_for_content_piece,
                self.server.repository.editorial_package_snapshot_payload,
                "editorial_package_snapshots",
            ),
        }
        for suffix, (
            kind,
            list_records,
            payload_for,
            response_key,
        ) in editorial_history_routes.items():
            if parsed.path.startswith(content_piece_prefix) and parsed.path.endswith(suffix):
                content_piece_id = unquote(
                    parsed.path[len(content_piece_prefix) : -len(suffix)]
                ).strip("/")
                if not content_piece_id:
                    self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                    return
                try:
                    self.server.repository.get_content_piece(content_piece_id)
                except KeyError:
                    self._send_json({"error": "ContentPiece not found."}, HTTPStatus.NOT_FOUND)
                    return
                self._send_json(
                    {
                        "kind": kind,
                        "content_piece_id": content_piece_id,
                        response_key: [
                            payload_for(record) for record in list_records(content_piece_id)
                        ],
                    }
                )
                return
        editorial_record_routes = {
            "/api/title-options/": (
                "title_option",
                self.server.repository.get_title_option,
                self.server.repository.title_option_payload,
                "title_option",
            ),
            "/api/hook-options/": (
                "hook_option",
                self.server.repository.get_hook_option,
                self.server.repository.hook_option_payload,
                "hook_option",
            ),
            "/api/editorial-package-snapshots/": (
                "editorial_package_snapshot",
                self.server.repository.get_editorial_package_snapshot,
                self.server.repository.editorial_package_snapshot_payload,
                "editorial_package_snapshot",
            ),
        }
        for prefix, (
            kind,
            get_record,
            payload_for,
            response_key,
        ) in editorial_record_routes.items():
            if parsed.path.startswith(prefix):
                record_id = unquote(parsed.path[len(prefix) :]).strip("/")
                if not record_id:
                    self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                    return
                try:
                    self._send_json(
                        {"kind": kind, response_key: payload_for(get_record(record_id))}
                    )
                except KeyError:
                    self._send_json({"error": f"{kind} not found."}, HTTPStatus.NOT_FOUND)
                return
        if parsed.path == "/api/demo/content":
            content = content_payload().copy()
            content.pop("scene_plan", None)
            content["visual_style"] = self.server.generation_service.visual_style_summary()
            research_pack = self.server.repository.latest_research_pack_payload("uk-isa-rules")
            if research_pack is not None:
                content["research"] = research_pack
                content["research_summary"] = research_pack["summary"]
                content["claim_count"] = len(research_pack["claims"])
                content["source_count"] = research_pack["source_count"]
                editorial_angles = self.server.repository.list_editorial_angles_for_research_pack(
                    research_pack["id"]
                )
                if editorial_angles:
                    default_angle = editorial_angles[0]
                    content["selected_angle"] = default_angle.working_title
                    content["editorial_angle"] = self.server.repository.editorial_angle_payload(
                        default_angle.id
                    )
                    content["editorial_angles"] = [
                        {"id": angle.id, "working_title": angle.working_title}
                        for angle in editorial_angles
                    ]
                    content_pieces = self.server.repository.list_content_pieces_for_editorial_angle(
                        default_angle.id
                    )
                    if content_pieces:
                        default_content_piece = content_pieces[0]
                        content_piece = self.server.repository.content_piece_payload(
                            default_content_piece.id
                        )
                        content["content_piece"] = content_piece
                        content["title"] = content_piece["working_title"]
                        if content_piece["latest_script"] is not None:
                            content["script"] = content_piece["latest_script"]["narration_text"]
                        visual_plans = self.server.repository.list_visual_plans_for_content_piece(
                            default_content_piece.id
                        )
                        if visual_plans:
                            visual_plan = self.server.repository.visual_plan_payload(
                                visual_plans[0].id
                            )
                            content["visual_plan"] = visual_plan
                            for scene in visual_plan["scenes"]:
                                for asset_spec in scene["asset_specs"]:
                                    asset_spec["generation_supported"] = (
                                        self.server.generation_service.generator.supports(
                                            asset_spec["asset_type"]
                                        )
                                    )
                                    character_profile = asset_spec["character_profile"]
                                    bootstrap_available = False
                                    if (
                                        asset_spec["asset_type"] == "character"
                                        and character_profile is not None
                                    ):
                                        bootstrap_available = (
                                            self.server.repository.get_latest_character_reference_set(
                                                character_profile["id"]
                                            )
                                            is None
                                        )
                                    asset_spec["bootstrap_reference_generation_available"] = (
                                        bootstrap_available
                                    )
                            content["scene_plan"] = " ".join(
                                scene["visual_intent"] for scene in visual_plan["scenes"]
                            )
            content["character_reference_review"] = (
                self.server.repository.character_reference_review_payload(
                    "character-profile-similarstoic-hamster-core-v1"
                )
            )
            self._send_json({"kind": "demo", "content": content, "activity": ACTIVITY})
            return
        if parsed.path == "/api/demo/chat":
            message = parse_qs(parsed.query).get("message", [""])[0]
            self._send_json({"kind": "demo", "reply": chat_reply(message)})
            return
        asset_prefix = "/api/assets/"
        asset_suffix = "/content"
        if parsed.path.startswith(asset_prefix) and parsed.path.endswith(asset_suffix):
            asset_id = unquote(parsed.path[len(asset_prefix) : -len(asset_suffix)]).strip("/")
            if not asset_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                asset = self.server.repository.get_asset(asset_id)
                path = self.server.repository.managed_asset_path(asset_id)
            except (KeyError, ValueError):
                self.send_error(HTTPStatus.NOT_FOUND, "Asset content not found")
                return
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", asset.media_type)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(path.read_bytes())
            return

        requested = "index.html" if parsed.path in {"", "/"} else parsed.path.lstrip("/")
        asset = STATIC_DIRECTORY / requested
        if not asset.is_file() or STATIC_DIRECTORY not in asset.resolve().parents:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        content_type, _ = mimetypes.guess_type(asset.name)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(asset.read_bytes())

    def do_POST(self) -> None:  # noqa: N802
        """Execute one narrow persisted generation or reference-selection action."""

        path = urlparse(self.path).path
        editorial_readiness_prefix = "/api/editorial-package-snapshots/"
        editorial_readiness_suffix = "/readiness-assessments"
        if path.startswith(editorial_readiness_prefix) and path.endswith(
            editorial_readiness_suffix
        ):
            snapshot_id = unquote(
                path[len(editorial_readiness_prefix) : -len(editorial_readiness_suffix)]
            ).strip("/")
            if not snapshot_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(content_length))
                if not isinstance(payload, dict):
                    raise ValueError("Editorial readiness assessment payload must be an object.")
                if set(payload) - {"id"}:
                    raise ValueError(
                        "Editorial readiness assessment payload contains unsupported fields."
                    )
                assessment_id = payload.get("id")
                if not isinstance(assessment_id, str) or not assessment_id.strip():
                    raise ValueError("Editorial readiness assessment ID must be non-empty text.")
                assessment = self.server.repository.create_editorial_readiness_assessment(
                    assessment_id.strip(), snapshot_id
                )
            except (json.JSONDecodeError, ValueError, sqlite3.IntegrityError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except KeyError:
                self._send_json(
                    {"error": "EditorialPackageSnapshot not found."}, HTTPStatus.NOT_FOUND
                )
                return
            self._send_json(
                {
                    "kind": "editorial_readiness_assessment",
                    "assessment": self.server.repository.editorial_readiness_assessment_payload(
                        assessment.id
                    ),
                },
                HTTPStatus.CREATED,
            )
            return
        editorial_gate_prefix = "/api/editorial-package-snapshots/"
        editorial_gate_suffix = "/gate-decisions"
        if path.startswith(editorial_gate_prefix) and path.endswith(editorial_gate_suffix):
            snapshot_id = unquote(
                path[len(editorial_gate_prefix) : -len(editorial_gate_suffix)]
            ).strip("/")
            if not snapshot_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(content_length))
                if not isinstance(payload, dict):
                    raise ValueError("Editorial Gate decision payload must be an object.")
                allowed_fields = {
                    "id",
                    "editorial_readiness_assessment_id",
                    "outcome",
                    "actor",
                    "comment",
                }
                if set(payload) - allowed_fields:
                    raise ValueError("Editorial Gate decision payload contains unsupported fields.")
                decision_id = payload.get("id")
                assessment_id = payload.get("editorial_readiness_assessment_id")
                outcome = payload.get("outcome")
                actor = payload.get("actor")
                comment = payload.get("comment")
                if not isinstance(decision_id, str) or not decision_id.strip():
                    raise ValueError("Editorial Gate decision ID must be non-empty text.")
                if not isinstance(assessment_id, str) or not assessment_id.strip():
                    raise ValueError("Editorial readiness assessment ID must be non-empty text.")
                if comment is not None and not isinstance(comment, str):
                    raise ValueError("Editorial Gate decision comment must be text or null.")
                decision = self.server.repository.create_editorial_gate_decision(
                    decision_id.strip(),
                    snapshot_id,
                    assessment_id.strip(),
                    outcome,
                    actor,
                    comment,
                )
            except (json.JSONDecodeError, ValueError, sqlite3.IntegrityError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except KeyError as error:
                message = (
                    "EditorialPackageSnapshot not found."
                    if error.args and error.args[0] == snapshot_id
                    else "Editorial readiness assessment not found."
                )
                self._send_json({"error": message}, HTTPStatus.NOT_FOUND)
                return
            self._send_json(
                {
                    "kind": "editorial_gate_decision",
                    "decision": self.server.repository.editorial_gate_decision_payload(decision.id),
                },
                HTTPStatus.CREATED,
            )
            return
        editorial_gate_decision_prefix = "/api/editorial-gate-decisions/"
        visual_plan_suffix = "/visual-plans"
        if path.startswith(editorial_gate_decision_prefix) and path.endswith(visual_plan_suffix):
            decision_id = unquote(
                path[len(editorial_gate_decision_prefix) : -len(visual_plan_suffix)]
            ).strip("/")
            if not decision_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(content_length))
                if not isinstance(payload, dict):
                    raise ValueError("Approved VisualPlan payload must be an object.")
                allowed_fields = {"id", "visual_direction", "metadata"}
                if set(payload) - allowed_fields:
                    raise ValueError("Approved VisualPlan payload contains unsupported fields.")
                visual_plan_id = payload.get("id")
                visual_direction = payload.get("visual_direction")
                metadata = payload.get("metadata")
                if not isinstance(visual_plan_id, str) or not visual_plan_id.strip():
                    raise ValueError("VisualPlan ID must be non-empty text.")
                if not isinstance(visual_direction, str) or not visual_direction.strip():
                    raise ValueError("VisualPlan visual_direction must be non-empty text.")
                if metadata is not None and not isinstance(metadata, dict):
                    raise ValueError("VisualPlan metadata must be an object or null.")
                visual_plan = self.server.repository.create_visual_plan_under_editorial_gate(
                    visual_plan_id.strip(), decision_id, visual_direction, metadata
                )
            except (json.JSONDecodeError, ValueError, sqlite3.IntegrityError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except KeyError:
                self._send_json(
                    {"error": "Editorial Gate decision not found."}, HTTPStatus.NOT_FOUND
                )
                return
            self._send_json(
                {
                    "kind": "visual_plan",
                    "visual_plan": self.server.repository.visual_plan_payload(visual_plan.id),
                    "gate_provenance": self.server.repository.visual_plan_gate_provenance_payload(
                        visual_plan.id
                    ),
                },
                HTTPStatus.CREATED,
            )
            return
        script_claim_set_prefix = "/api/scripts/"
        script_claim_set_suffix = "/claim-set"
        if path.startswith(script_claim_set_prefix) and path.endswith(script_claim_set_suffix):
            script_id = unquote(
                path[len(script_claim_set_prefix) : -len(script_claim_set_suffix)]
            ).strip("/")
            if not script_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(content_length))
                if not isinstance(payload, dict):
                    raise ValueError("ScriptClaimSet payload must be an object.")
                allowed_fields = {"id", "claim_ids"}
                if set(payload) - allowed_fields:
                    raise ValueError("ScriptClaimSet payload contains unsupported fields.")
                claim_set_id = payload.get("id")
                claim_ids = payload.get("claim_ids")
                if not isinstance(claim_set_id, str) or not claim_set_id.strip():
                    raise ValueError("ScriptClaimSet ID must be non-empty text.")
                if not isinstance(claim_ids, list) or any(
                    not isinstance(claim_id, str) or not claim_id.strip() for claim_id in claim_ids
                ):
                    raise ValueError("ScriptClaimSet claim_ids must be an array of non-empty text.")
                claim_set = self.server.repository.create_script_claim_set(
                    claim_set_id.strip(), script_id, claim_ids
                )
            except (json.JSONDecodeError, ValueError, sqlite3.IntegrityError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except KeyError as error:
                message = (
                    "Script not found."
                    if error.args and error.args[0] == script_id
                    else "Claim not found."
                )
                self._send_json({"error": message}, HTTPStatus.NOT_FOUND)
                return
            self._send_json(
                {
                    "kind": "script_claim_set",
                    "script_claim_set": self.server.repository.script_claim_set_payload(
                        claim_set.script_id
                    ),
                },
                HTTPStatus.CREATED,
            )
            return
        opportunity_prefix = "/api/opportunities/"
        snapshot_suffix = "/idea-gate-review-snapshots"
        if path.startswith(opportunity_prefix) and path.endswith(snapshot_suffix):
            opportunity_id = unquote(path[len(opportunity_prefix) : -len(snapshot_suffix)]).strip(
                "/"
            )
            if not opportunity_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                snapshot = self.server.repository.create_idea_gate_review_snapshot(
                    f"idea-gate-review-snapshot-{uuid.uuid4().hex}", opportunity_id
                )
            except KeyError:
                self._send_json({"error": "Opportunity not found."}, HTTPStatus.NOT_FOUND)
                return
            self._send_json(
                {
                    "kind": "idea_gate_review_snapshot",
                    "snapshot": self.server.repository.idea_gate_review_snapshot_payload(
                        snapshot.id
                    ),
                },
                HTTPStatus.CREATED,
            )
            return
        research_pack_suffix = "/research-packs"
        if path.startswith(opportunity_prefix) and path.endswith(research_pack_suffix):
            opportunity_id = unquote(
                path[len(opportunity_prefix) : -len(research_pack_suffix)]
            ).strip("/")
            if not opportunity_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(content_length))
                if not isinstance(payload, dict):
                    raise ValueError("ResearchPack initiation payload must be an object.")
                research_pack_id = payload.get("id")
                decision_id = payload.get("idea_gate_decision_id")
                version = payload.get("version")
                summary = payload.get("summary")
                as_of_date = payload.get("as_of_date")
                metadata = payload.get("metadata")
                if not isinstance(research_pack_id, str) or not research_pack_id.strip():
                    raise ValueError("ResearchPack ID must be non-empty text.")
                if not isinstance(decision_id, str) or not decision_id.strip():
                    raise ValueError("Idea Gate decision ID must be non-empty text.")
                if not isinstance(version, int) or isinstance(version, bool):
                    raise ValueError("ResearchPack version must be an integer.")
                if not isinstance(summary, str) or not summary.strip():
                    raise ValueError("ResearchPack summary must be non-empty text.")
                if as_of_date is not None and not isinstance(as_of_date, str):
                    raise ValueError("ResearchPack as_of_date must be text or null.")
                if metadata is not None and not isinstance(metadata, dict):
                    raise ValueError("ResearchPack metadata must be an object or null.")
                research_pack = (
                    self.server.repository.create_research_pack_under_idea_gate_authorization(
                        research_pack_id.strip(),
                        opportunity_id,
                        version,
                        summary,
                        decision_id.strip(),
                        as_of_date,
                        metadata,
                    )
                )
            except (json.JSONDecodeError, ValueError, sqlite3.IntegrityError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except KeyError:
                self._send_json(
                    {"error": "Opportunity or Idea Gate decision not found."},
                    HTTPStatus.NOT_FOUND,
                )
                return
            self._send_json(
                {
                    "kind": "research_pack",
                    "research_pack": self.server.repository.research_pack_payload(research_pack.id),
                },
                HTTPStatus.CREATED,
            )
            return
        content_piece_prefix = "/api/content-pieces/"
        title_option_suffix = "/title-options"
        hook_option_suffix = "/hook-options"
        for suffix, record_name, create_option, payload_for, response_key in (
            (
                title_option_suffix,
                "TitleOption",
                self.server.repository.create_title_option_under_content_piece_readiness,
                self.server.repository.title_option_payload,
                "title_option",
            ),
            (
                hook_option_suffix,
                "HookOption",
                self.server.repository.create_hook_option_under_content_piece_readiness,
                self.server.repository.hook_option_payload,
                "hook_option",
            ),
        ):
            if path.startswith(content_piece_prefix) and path.endswith(suffix):
                content_piece_id = unquote(path[len(content_piece_prefix) : -len(suffix)]).strip(
                    "/"
                )
                if not content_piece_id:
                    self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                    return
                try:
                    content_length = int(self.headers.get("Content-Length", "0"))
                    payload = json.loads(self.rfile.read(content_length))
                    if not isinstance(payload, dict):
                        raise ValueError(f"{record_name} initiation payload must be an object.")
                    allowed_fields = {"id", "text", "metadata"}
                    if set(payload) - allowed_fields:
                        raise ValueError(
                            f"{record_name} initiation payload contains unsupported fields."
                        )
                    record_id = payload.get("id")
                    text = payload.get("text")
                    metadata = payload.get("metadata")
                    if not isinstance(record_id, str) or not record_id.strip():
                        raise ValueError(f"{record_name} ID must be non-empty text.")
                    if not isinstance(text, str) or not text.strip():
                        raise ValueError(f"{record_name} text must be non-empty text.")
                    if metadata is not None and not isinstance(metadata, dict):
                        raise ValueError(f"{record_name} metadata must be an object or null.")
                    record = create_option(record_id.strip(), content_piece_id, text, metadata)
                except (json.JSONDecodeError, ValueError, sqlite3.IntegrityError) as error:
                    self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                    return
                except KeyError:
                    self._send_json({"error": "ContentPiece not found."}, HTTPStatus.NOT_FOUND)
                    return
                self._send_json(
                    {"kind": response_key, response_key: payload_for(record)}, HTTPStatus.CREATED
                )
                return
        editorial_package_snapshot_suffix = "/editorial-package-snapshots"
        if path.startswith(content_piece_prefix) and path.endswith(
            editorial_package_snapshot_suffix
        ):
            content_piece_id = unquote(
                path[len(content_piece_prefix) : -len(editorial_package_snapshot_suffix)]
            ).strip("/")
            if not content_piece_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(content_length))
                if not isinstance(payload, dict):
                    raise ValueError("EditorialPackageSnapshot payload must be an object.")
                allowed_fields = {"id", "title_option_id", "hook_option_id", "script_id"}
                if set(payload) - allowed_fields:
                    raise ValueError(
                        "EditorialPackageSnapshot payload contains unsupported fields."
                    )
                values = {name: payload.get(name) for name in allowed_fields}
                if any(
                    not isinstance(value, str) or not value.strip() for value in values.values()
                ):
                    raise ValueError("EditorialPackageSnapshot IDs must be non-empty text.")
                snapshot = self.server.repository.create_editorial_package_snapshot(
                    values["id"].strip(),
                    content_piece_id,
                    values["title_option_id"].strip(),
                    values["hook_option_id"].strip(),
                    values["script_id"].strip(),
                )
            except (json.JSONDecodeError, ValueError, sqlite3.IntegrityError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except KeyError as error:
                message = (
                    "ContentPiece not found."
                    if error.args and error.args[0] == content_piece_id
                    else "TitleOption, HookOption, or Script not found."
                )
                self._send_json({"error": message}, HTTPStatus.NOT_FOUND)
                return
            self._send_json(
                {
                    "kind": "editorial_package_snapshot",
                    "editorial_package_snapshot": (
                        self.server.repository.editorial_package_snapshot_payload(snapshot)
                    ),
                },
                HTTPStatus.CREATED,
            )
            return
        script_suffix = "/scripts"
        if path.startswith(content_piece_prefix) and path.endswith(script_suffix):
            content_piece_id = unquote(path[len(content_piece_prefix) : -len(script_suffix)]).strip(
                "/"
            )
            if not content_piece_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(content_length))
                if not isinstance(payload, dict):
                    raise ValueError("Script initiation payload must be an object.")
                allowed_fields = {"id", "narration_text", "metadata"}
                unexpected_fields = set(payload) - allowed_fields
                if unexpected_fields:
                    raise ValueError("Script initiation payload contains unsupported fields.")
                script_id = payload.get("id")
                narration_text = payload.get("narration_text")
                metadata = payload.get("metadata")
                if not isinstance(script_id, str) or not script_id.strip():
                    raise ValueError("Script ID must be non-empty text.")
                if not isinstance(narration_text, str) or not narration_text.strip():
                    raise ValueError("Script narration_text must be non-empty text.")
                if metadata is not None and not isinstance(metadata, dict):
                    raise ValueError("Script metadata must be an object or null.")
                script = self.server.repository.create_script_under_content_piece_readiness(
                    script_id.strip(), content_piece_id, narration_text, metadata
                )
            except (json.JSONDecodeError, ValueError, sqlite3.IntegrityError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except KeyError:
                self._send_json({"error": "ContentPiece not found."}, HTTPStatus.NOT_FOUND)
                return
            self._send_json(
                {
                    "kind": "script",
                    "script": {
                        "id": script.id,
                        "content_piece_id": script.content_piece_id,
                        "version": script.version,
                        "narration_text": script.narration_text,
                    },
                },
                HTTPStatus.CREATED,
            )
            return
        content_piece_suffix = "/content-pieces"
        if path.startswith(opportunity_prefix) and path.endswith(content_piece_suffix):
            opportunity_id = unquote(
                path[len(opportunity_prefix) : -len(content_piece_suffix)]
            ).strip("/")
            if not opportunity_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(content_length))
                if not isinstance(payload, dict):
                    raise ValueError("ContentPiece initiation payload must be an object.")
                allowed_fields = {
                    "id",
                    "editorial_angle_id",
                    "format_key",
                    "working_title",
                    "metadata",
                }
                unexpected_fields = set(payload) - allowed_fields
                if unexpected_fields:
                    raise ValueError("ContentPiece initiation payload contains unsupported fields.")
                content_piece_id = payload.get("id")
                editorial_angle_id = payload.get("editorial_angle_id")
                format_key = payload.get("format_key")
                working_title = payload.get("working_title")
                metadata = payload.get("metadata")
                if not isinstance(content_piece_id, str) or not content_piece_id.strip():
                    raise ValueError("ContentPiece ID must be non-empty text.")
                if not isinstance(editorial_angle_id, str) or not editorial_angle_id.strip():
                    raise ValueError("EditorialAngle ID must be non-empty text.")
                if not isinstance(format_key, str) or not format_key.strip():
                    raise ValueError("ContentPiece format_key must be non-empty text.")
                if not isinstance(working_title, str) or not working_title.strip():
                    raise ValueError("ContentPiece working_title must be non-empty text.")
                if metadata is not None and not isinstance(metadata, dict):
                    raise ValueError("ContentPiece metadata must be an object or null.")
                content_piece = (
                    self.server.repository.create_content_piece_under_editorial_angle_readiness(
                        content_piece_id.strip(),
                        opportunity_id,
                        editorial_angle_id.strip(),
                        format_key,
                        working_title,
                        metadata,
                    )
                )
            except (json.JSONDecodeError, ValueError, sqlite3.IntegrityError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except KeyError:
                self._send_json(
                    {"error": "Opportunity or EditorialAngle not found."}, HTTPStatus.NOT_FOUND
                )
                return
            self._send_json(
                {
                    "kind": "content_piece",
                    "content_piece": self.server.repository.content_piece_payload(content_piece.id),
                },
                HTTPStatus.CREATED,
            )
            return
        editorial_angle_suffix = "/editorial-angles"
        if path.startswith(opportunity_prefix) and path.endswith(editorial_angle_suffix):
            opportunity_id = unquote(
                path[len(opportunity_prefix) : -len(editorial_angle_suffix)]
            ).strip("/")
            if not opportunity_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(content_length))
                if not isinstance(payload, dict):
                    raise ValueError("EditorialAngle initiation payload must be an object.")
                editorial_angle_id = payload.get("id")
                research_pack_id = payload.get("research_pack_id")
                assessment_id = payload.get("research_readiness_assessment_id")
                if not isinstance(editorial_angle_id, str) or not editorial_angle_id.strip():
                    raise ValueError("EditorialAngle ID must be non-empty text.")
                if not isinstance(research_pack_id, str) or not research_pack_id.strip():
                    raise ValueError("ResearchPack ID must be non-empty text.")
                if not isinstance(assessment_id, str) or not assessment_id.strip():
                    raise ValueError("Research readiness assessment ID must be non-empty text.")
                required_text = (
                    "working_title",
                    "thesis",
                    "audience_promise",
                    "framing",
                )
                if any(
                    not isinstance(payload.get(field), str) or not payload[field].strip()
                    for field in required_text
                ):
                    raise ValueError("EditorialAngle text fields must be non-empty text.")
                key_takeaways = payload.get("key_takeaways")
                if not isinstance(key_takeaways, list):
                    raise ValueError("EditorialAngle key_takeaways must be a list.")
                metadata = payload.get("metadata")
                if metadata is not None and not isinstance(metadata, dict):
                    raise ValueError("EditorialAngle metadata must be an object or null.")
                editorial_angle = (
                    self.server.repository.create_editorial_angle_under_research_readiness(
                        editorial_angle_id.strip(),
                        opportunity_id,
                        research_pack_id.strip(),
                        assessment_id.strip(),
                        payload["working_title"],
                        payload["thesis"],
                        payload["audience_promise"],
                        payload["framing"],
                        key_takeaways,
                        metadata,
                    )
                )
            except (json.JSONDecodeError, ValueError, sqlite3.IntegrityError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except KeyError:
                self._send_json(
                    {
                        "error": "Opportunity, ResearchPack or "
                        "ResearchReadinessAssessment not found."
                    },
                    HTTPStatus.NOT_FOUND,
                )
                return
            self._send_json(
                {
                    "kind": "editorial_angle",
                    "editorial_angle": self.server.repository.editorial_angle_payload(
                        editorial_angle.id
                    ),
                },
                HTTPStatus.CREATED,
            )
            return
        readiness_assessment_prefix = "/api/research-packs/"
        readiness_assessment_suffix = "/readiness-assessments"
        if path.startswith(readiness_assessment_prefix) and path.endswith(
            readiness_assessment_suffix
        ):
            research_pack_id = unquote(
                path[len(readiness_assessment_prefix) : -len(readiness_assessment_suffix)]
            ).strip("/")
            if not research_pack_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(content_length))
                if not isinstance(payload, dict):
                    raise ValueError("Research readiness assessment payload must be an object.")
                if "frozen_evidence_state" in payload:
                    raise ValueError(
                        "Frozen evidence state is built by the server and cannot be supplied."
                    )
                assessment = self.server.repository.create_research_readiness_assessment(
                    payload.get("id"),
                    research_pack_id,
                    payload.get("outcome"),
                    payload.get("findings"),
                    payload.get("policy_version"),
                    payload.get("producer_kind"),
                    payload.get("producer_identifier"),
                    payload.get("producer_implementation_version"),
                )
            except (json.JSONDecodeError, ValueError, sqlite3.IntegrityError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except KeyError:
                self._send_json({"error": "ResearchPack not found."}, HTTPStatus.NOT_FOUND)
                return
            self._send_json(
                {
                    "kind": "research_readiness_assessment",
                    "assessment": self.server.repository.research_readiness_assessment_payload(
                        assessment.id
                    ),
                },
                HTTPStatus.CREATED,
            )
            return
        idea_gate_snapshot_prefix = "/api/idea-gate-review-snapshots/"
        decision_suffix = "/decisions"
        if path.startswith(idea_gate_snapshot_prefix) and path.endswith(decision_suffix):
            snapshot_id = unquote(
                path[len(idea_gate_snapshot_prefix) : -len(decision_suffix)]
            ).strip("/")
            if not snapshot_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(content_length))
                if not isinstance(payload, dict):
                    raise ValueError("Idea Gate decision payload must be an object.")
                decision = self.server.repository.record_idea_gate_decision(
                    f"idea-gate-decision-{uuid.uuid4().hex}",
                    snapshot_id,
                    payload.get("outcome"),
                    payload.get("founder_actor", "founder"),
                    payload.get("founder_comment"),
                    payload.get("founder_direction"),
                )
            except (json.JSONDecodeError, ValueError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except KeyError:
                self._send_json(
                    {"error": "Idea Gate review snapshot not found."}, HTTPStatus.NOT_FOUND
                )
                return
            self._send_json(
                {
                    "kind": "idea_gate_decision",
                    "decision": self.server.repository.idea_gate_decision_payload(decision.id),
                },
                HTTPStatus.CREATED,
            )
            return
        reference_prefix = "/api/character-profiles/"
        reference_suffix = "/reference-sets"
        if path.startswith(reference_prefix) and path.endswith(reference_suffix):
            character_profile_id = unquote(
                path[len(reference_prefix) : -len(reference_suffix)]
            ).strip("/")
            if not character_profile_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(content_length))
                asset_ids = payload.get("asset_ids") if isinstance(payload, dict) else None
                if not isinstance(asset_ids, list):
                    raise ValueError("asset_ids must be an ordered list.")
                reference_set = self.server.repository.create_character_reference_set(
                    f"character-reference-set-{uuid.uuid4().hex}",
                    character_profile_id,
                    asset_ids,
                )
            except (json.JSONDecodeError, ValueError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except KeyError:
                self._send_json(
                    {"error": "CharacterProfile or Asset not found."}, HTTPStatus.NOT_FOUND
                )
                return
            self._send_json(
                {
                    "kind": "character_reference_set",
                    "reference_set": self.server.repository.character_reference_set_payload(
                        reference_set.id
                    ),
                },
                HTTPStatus.CREATED,
            )
            return
        prefix = "/api/asset-specs/"
        bootstrap_suffix = "/bootstrap-character-reference"
        generate_suffix = "/generate"
        if not path.startswith(prefix):
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        if path.endswith(bootstrap_suffix):
            asset_spec_id = unquote(path[len(prefix) : -len(bootstrap_suffix)]).strip("/")
            operation = self.server.generation_service.bootstrap_character_reference_asset
            kind = "character_reference_bootstrap"
        elif path.endswith(generate_suffix):
            asset_spec_id = unquote(path[len(prefix) : -len(generate_suffix)]).strip("/")
            operation = self.server.generation_service.generate_asset_spec
            kind = "generation"
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        if not asset_spec_id:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        try:
            result = operation(asset_spec_id)
        except KeyError:
            self._send_json({"error": "AssetSpec not found."}, HTTPStatus.NOT_FOUND)
            return
        except (
            InvalidCharacterReferenceBootstrap,
            MissingCharacterReferenceSet,
            MissingProviderConfiguration,
            MissingVisualStyleProfile,
            UnsupportedGenerationType,
        ) as error:
            self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        except Exception:
            self._send_json(
                {"error": "Conveyor could not persist the generation result."},
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )
            return
        self._send_json(
            {
                "kind": kind,
                "execution": self.server.repository.generation_execution_payload(
                    result.execution.id
                ),
                "asset": (
                    {
                        "id": result.asset.id,
                        "version": result.asset.version,
                        "generation_execution_id": result.asset.generation_execution_id,
                    }
                    if result.asset
                    else None
                ),
            }
        )

    def _send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        """Keep local demo-server logs concise."""

        print(f"[Conveyor] {format % args}")


class AtlasHTTPServer(HTTPServer):
    """HTTP server that owns the local Conveyor application repository."""

    def __init__(
        self,
        address: tuple[str, int],
        repository: AtlasRepository,
        generation_service: GenerationService,
    ) -> None:
        super().__init__(address, AtlasRequestHandler)
        self.repository = repository
        self.generation_service = generation_service

    def server_close(self) -> None:
        super().server_close()
        self.repository.close()


def create_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    database_path: Path | None = None,
    generator: AssetGenerator | None = None,
    asset_storage_root: Path | None = None,
) -> AtlasHTTPServer:
    """Create the MVP server without starting it, for testability."""

    repository = AtlasRepository(database_path, asset_storage_root=asset_storage_root)
    return AtlasHTTPServer(
        (host, port),
        repository,
        GenerationService(
            repository,
            generator or OpenAIImageGenerator(),
            LocalAssetStorage(asset_storage_root),
        ),
    )


def main() -> None:
    """Start the local MVP UI shell."""

    parser = argparse.ArgumentParser(description="Run the Conveyor MVP UI shell.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1).")
    parser.add_argument("--port", default=8000, type=int, help="Port to bind (default: 8000).")
    args = parser.parse_args()
    server = create_server(args.host, args.port)
    print(f"Conveyor MVP is running at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nConveyor MVP stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
