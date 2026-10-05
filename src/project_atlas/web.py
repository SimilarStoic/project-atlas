"""Dependency-free local server for the Conveyor MVP UI shell."""

from __future__ import annotations

import argparse
import ipaddress
import json
import mimetypes
import os
import sqlite3
import uuid
from collections.abc import Callable
from dataclasses import replace
from html import escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from project_atlas.demo_data import ACTIVITY, chat_reply, content_payload
from project_atlas.generation import (
    AssetGenerator,
    AssetStorageFailure,
    GenerationService,
    InvalidCharacterReferenceBootstrap,
    LocalAssetStorage,
    MissingCharacterReferenceSet,
    MissingProviderConfiguration,
    MissingVisualStyleProfile,
    OpenAIImageGenerator,
    UnsupportedGenerationType,
)
from project_atlas.media import FfmpegRuntime, LocalMediaStorage, MediaRuntimeError, MediaService
from project_atlas.persistence import AtlasRepository
from project_atlas.production import (
    ProductionLifecycleError,
    ProductionLifecycleService,
    ProductionRequestError,
)

STATIC_DIRECTORY = Path(__file__).parent / "static"
YOUTUBE_UPLOAD_PATH = "/youtube/upload"


def is_loopback(address: str) -> bool:
    """True only for a literal loopback address (IPv4, IPv6 or IPv4-mapped IPv6)."""

    try:
        value = ipaddress.ip_address(address.split("%", 1)[0])
    except ValueError:
        return False
    mapped = getattr(value, "ipv4_mapped", None)
    return (mapped or value).is_loopback


MAX_IMPORTED_ASSET_BYTES = 10 * 1024 * 1024
MAX_IMPORTED_NARRATION_BYTES = 100 * 1024 * 1024


class AtlasRequestHandler(BaseHTTPRequestHandler):
    """Serve local demo data and the static browser UI."""

    server_version = "ProjectAtlasMVP/0.1"

    def do_GET(self) -> None:  # noqa: N802
        """Handle only local static assets and demo API responses."""

        parsed = urlparse(self.path)
        if parsed.path == YOUTUBE_UPLOAD_PATH:
            package_id = parse_qs(parsed.query).get("package", [""])[0]
            self._youtube_upload(lambda controller: controller.page(package_id))
            return
        production_prefix = "/api/v2/productions/"
        recommendation_suffix = "/retime-recommendation"
        if parsed.path.startswith(production_prefix) and parsed.path.endswith(
            recommendation_suffix
        ):
            run_id = unquote(
                parsed.path[len(production_prefix) : -len(recommendation_suffix)]
            ).strip("/")
            try:
                recommendation = self.server.production_service.recommend_retime(run_id)
            except KeyError:
                self._send_json({"error": "ProductionRun not found."}, HTTPStatus.NOT_FOUND)
                return
            except ProductionRequestError as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            self._send_json({"kind": "retime_recommendation", "recommendation": recommendation})
            return
        if parsed.path.startswith(production_prefix):
            run_id = unquote(parsed.path[len(production_prefix) :]).strip("/")
            if not run_id or "/" in run_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                production = self.server.production_service.status(run_id)
            except KeyError:
                self._send_json({"error": "ProductionRun not found."}, HTTPStatus.NOT_FOUND)
                return
            self._send_json({"kind": "persistent_scene_production", "production": production})
            return
        visual_plan_prefix = "/api/visual-plans/"
        scene_suffix = "/scenes"
        if parsed.path.startswith(visual_plan_prefix) and parsed.path.endswith(scene_suffix):
            visual_plan_id = unquote(
                parsed.path[len(visual_plan_prefix) : -len(scene_suffix)]
            ).strip("/")
            if not visual_plan_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                scenes = self.server.repository.list_scenes_under_visual_plan_authorization(
                    visual_plan_id
                )
            except KeyError:
                self._send_json({"error": "VisualPlan not found."}, HTTPStatus.NOT_FOUND)
                return
            except ValueError as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            self._send_json(
                {
                    "kind": "scene_history",
                    "visual_plan_id": visual_plan_id,
                    "scenes": [self._scene_payload(scene) for scene in scenes],
                }
            )
            return
        scene_prefix = "/api/scenes/"
        asset_spec_suffix = "/asset-specs"
        if parsed.path.startswith(scene_prefix) and parsed.path.endswith(asset_spec_suffix):
            scene_id = unquote(parsed.path[len(scene_prefix) : -len(asset_spec_suffix)]).strip("/")
            if not scene_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                asset_specs = self.server.repository.list_asset_specs_under_scene_authorization(
                    scene_id
                )
            except KeyError:
                self._send_json({"error": "Scene not found."}, HTTPStatus.NOT_FOUND)
                return
            except ValueError as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            self._send_json(
                {
                    "kind": "asset_spec_history",
                    "scene_id": scene_id,
                    "asset_specs": [
                        self.server.repository.asset_spec_payload(asset_spec.id)
                        for asset_spec in asset_specs
                    ],
                }
            )
            return
        asset_spec_prefix = "/api/asset-specs/"
        asset_suffix = "/assets"
        selection_suffix = "/asset-selections"
        if parsed.path.startswith(asset_spec_prefix) and parsed.path.endswith(asset_suffix):
            asset_spec_id = unquote(parsed.path[len(asset_spec_prefix) : -len(asset_suffix)]).strip(
                "/"
            )
            if not asset_spec_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                assets = self.server.repository.list_assets_under_asset_spec_authorization(
                    asset_spec_id
                )
            except KeyError:
                self._send_json({"error": "AssetSpec not found."}, HTTPStatus.NOT_FOUND)
                return
            self._send_json(
                {
                    "kind": "asset_history",
                    "asset_spec_id": asset_spec_id,
                    "assets": [self._asset_payload(asset) for asset in assets],
                }
            )
            return
        if parsed.path.startswith(asset_spec_prefix) and parsed.path.endswith(selection_suffix):
            asset_spec_id = unquote(
                parsed.path[len(asset_spec_prefix) : -len(selection_suffix)]
            ).strip("/")
            if not asset_spec_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                selections = self.server.repository.list_asset_selections_for_asset_spec(
                    asset_spec_id
                )
            except KeyError:
                self._send_json({"error": "AssetSpec not found."}, HTTPStatus.NOT_FOUND)
                return
            self._send_json(
                {
                    "kind": "asset_selection_history",
                    "asset_spec_id": asset_spec_id,
                    "asset_selections": [
                        self.server.repository.asset_selection_payload(selection.id)
                        for selection in selections
                    ],
                }
            )
            return
        asset_selection_prefix = "/api/asset-selections/"
        if parsed.path.startswith(asset_selection_prefix):
            selection_id = unquote(parsed.path[len(asset_selection_prefix) :]).strip("/")
            if not selection_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                self._send_json(
                    {
                        "kind": "asset_selection",
                        "asset_selection": self.server.repository.asset_selection_payload(
                            selection_id
                        ),
                    }
                )
            except KeyError:
                self._send_json({"error": "AssetSelection not found."}, HTTPStatus.NOT_FOUND)
            return
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
        narration_history_prefix = "/api/scripts/"
        narration_history_suffix = "/narration-assets"
        if parsed.path.startswith(narration_history_prefix) and parsed.path.endswith(
            narration_history_suffix
        ):
            script_id = unquote(
                parsed.path[len(narration_history_prefix) : -len(narration_history_suffix)]
            ).strip("/")
            if not script_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                narration_assets = self.server.repository.list_narration_assets_for_script(
                    script_id
                )
            except KeyError:
                self._send_json({"error": "Script not found."}, HTTPStatus.NOT_FOUND)
                return
            self._send_json(
                {
                    "kind": "narration_asset_history",
                    "script_id": script_id,
                    "narration_assets": [
                        self._narration_asset_payload(item) for item in narration_assets
                    ],
                }
            )
            return
        narration_asset_prefix = "/api/narration-assets/"
        narration_content_suffix = "/content"
        if parsed.path.startswith(narration_asset_prefix) and parsed.path.endswith(
            narration_content_suffix
        ):
            narration_asset_id = unquote(
                parsed.path[len(narration_asset_prefix) : -len(narration_content_suffix)]
            ).strip("/")
            if not narration_asset_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                narration = self.server.repository.get_narration_asset(narration_asset_id)
                content = self.server.media_service.narration_content(narration_asset_id)
            except (KeyError, MediaRuntimeError, OSError):
                self.send_error(HTTPStatus.NOT_FOUND, "NarrationAsset content not found")
                return
            self._send_binary(content, narration.media_type)
            return
        if parsed.path.startswith(narration_asset_prefix):
            narration_asset_id = unquote(parsed.path[len(narration_asset_prefix) :]).strip("/")
            if not narration_asset_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                narration = self.server.repository.get_narration_asset(narration_asset_id)
            except KeyError:
                self._send_json({"error": "NarrationAsset not found."}, HTTPStatus.NOT_FOUND)
                return
            self._send_json(
                {
                    "kind": "narration_asset",
                    "narration_asset": self._narration_asset_payload(narration),
                }
            )
            return
        snapshot_prefix = "/api/final-media-input-snapshots/"
        if parsed.path.startswith(snapshot_prefix):
            snapshot_id = unquote(parsed.path[len(snapshot_prefix) :]).strip("/")
            if not snapshot_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                snapshot = self.server.repository.get_final_media_input_snapshot(snapshot_id)
            except KeyError:
                self._send_json(
                    {"error": "FinalMediaInputSnapshot not found."}, HTTPStatus.NOT_FOUND
                )
                return
            self._send_json(
                {
                    "kind": "final_media_input_snapshot",
                    "final_media_input_snapshot": self._snapshot_payload(snapshot),
                }
            )
            return
        execution_prefix = "/api/render-executions/"
        if parsed.path.startswith(execution_prefix):
            execution_id = unquote(parsed.path[len(execution_prefix) :]).strip("/")
            if not execution_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                execution = self.server.repository.get_render_execution(execution_id)
            except KeyError:
                self._send_json({"error": "RenderExecution not found."}, HTTPStatus.NOT_FOUND)
                return
            self._send_json(
                {
                    "kind": "render_execution",
                    "render_execution": self._render_execution_payload(execution),
                }
            )
            return
        artifact_prefix = "/api/final-media-artifacts/"
        artifact_content_suffix = "/content"
        if parsed.path.startswith(artifact_prefix) and parsed.path.endswith(
            artifact_content_suffix
        ):
            artifact_id = unquote(
                parsed.path[len(artifact_prefix) : -len(artifact_content_suffix)]
            ).strip("/")
            if not artifact_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                content = self.server.media_service.artifact_content(artifact_id)
            except (KeyError, MediaRuntimeError, OSError):
                self.send_error(HTTPStatus.NOT_FOUND, "FinalMediaArtifact content not found")
                return
            self._send_binary(content, "video/mp4")
            return
        if parsed.path.startswith(artifact_prefix):
            artifact_id = unquote(parsed.path[len(artifact_prefix) :]).strip("/")
            if not artifact_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                artifact = self.server.repository.get_final_media_artifact(artifact_id)
            except KeyError:
                self._send_json({"error": "FinalMediaArtifact not found."}, HTTPStatus.NOT_FOUND)
                return
            self._send_json(
                {
                    "kind": "final_media_artifact",
                    "final_media_artifact": self._artifact_payload(artifact),
                }
            )
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
        if path == YOUTUBE_UPLOAD_PATH:
            self._youtube_upload(lambda controller: controller.submit(self._read_upload_form()))
            return
        if path == "/api/v2/productions":
            try:
                production = self.server.production_service.start(
                    self._read_json_object("Canonical v2 production request")
                )
            except KeyError:
                self._send_json(
                    {"error": "Referenced canonical production input not found."},
                    HTTPStatus.NOT_FOUND,
                )
                return
            except (
                json.JSONDecodeError,
                ProductionRequestError,
                ValueError,
                sqlite3.IntegrityError,
            ) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except ProductionLifecycleError as error:
                self._send_json(
                    {
                        "error": str(error),
                        "stage": error.stage,
                        "production": self.server.production_service.status(error.run_id),
                    },
                    HTTPStatus.UNPROCESSABLE_ENTITY,
                )
                return
            self._send_json(
                {"kind": "persistent_scene_production", "production": production},
                HTTPStatus.CREATED,
            )
            return
        production_prefix = "/api/v2/productions/"
        production_commands = {
            "/resume": "resume",
            "/acquisition-review": "acquisition_review",
            "/qa": "qa",
            "/founder-review": "founder_review",
            "/retime": "retime",
            "/narration-authorization": "narration_authorization",
        }
        for suffix, command in production_commands.items():
            if path.startswith(production_prefix) and path.endswith(suffix):
                run_id = unquote(path[len(production_prefix) : -len(suffix)]).strip("/")
                if not run_id:
                    self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                    return
                try:
                    if command == "resume":
                        payload = self._read_json_object("Production resume command")
                        if payload:
                            raise ProductionRequestError("Production resume payload must be empty.")
                        production = self.server.production_service.resume(run_id)
                    elif command == "acquisition_review":
                        payload = self._read_json_object("Acquisition review command")
                        self._reject_unsupported_fields(
                            payload, {"reviews"}, "Acquisition review command"
                        )
                        reviews = payload.get("reviews")
                        if not isinstance(reviews, list):
                            raise ProductionRequestError("Acquisition reviews must be a list.")
                        production = self.server.production_service.review_acquisition(
                            run_id, reviews
                        )
                    elif command == "qa":
                        payload = self._read_json_object("Whole-video QA command")
                        self._reject_unsupported_fields(
                            payload, {"outcome", "evidence"}, "Whole-video QA command"
                        )
                        production = self.server.production_service.record_qa(run_id, payload)
                    elif command == "narration_authorization":
                        payload = self._read_json_object("Narration authorization command")
                        self._reject_unsupported_fields(
                            payload, {"evidence"}, "Narration authorization command"
                        )
                        production = self.server.production_service.authorize_narration(
                            run_id, payload.get("evidence")
                        )
                    elif command == "retime":
                        payload = self._read_json_object("Production retime command")
                        self._reject_unsupported_fields(
                            payload,
                            {"durations_ms", "actor", "reason"},
                            "Production retime command",
                        )
                        production = self.server.production_service.retime(
                            run_id,
                            payload.get("durations_ms"),
                            payload.get("actor"),
                            payload.get("reason"),
                        )
                    else:
                        payload = self._read_json_object("Founder review command")
                        self._reject_unsupported_fields(
                            payload,
                            {
                                "outcome",
                                "founder_actor",
                                "decision_reference",
                                "notes",
                            },
                            "Founder review command",
                        )
                        production = self.server.production_service.founder_review(run_id, payload)
                except KeyError:
                    self._send_json({"error": "ProductionRun not found."}, HTTPStatus.NOT_FOUND)
                    return
                except (
                    json.JSONDecodeError,
                    ProductionRequestError,
                    ValueError,
                    sqlite3.IntegrityError,
                ) as error:
                    self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                    return
                except ProductionLifecycleError as error:
                    self._send_json(
                        {
                            "error": str(error),
                            "stage": error.stage,
                            "production": self.server.production_service.status(error.run_id),
                        },
                        HTTPStatus.UNPROCESSABLE_ENTITY,
                    )
                    return
                self._send_json({"kind": "persistent_scene_production", "production": production})
                return
        if path == "/api/opportunities":
            try:
                payload = self._read_json_object("Opportunity payload")
                self._reject_unsupported_fields(
                    payload,
                    {"id", "title", "summary", "why_now", "score", "status", "metadata"},
                    "Opportunity payload",
                )
                score = payload.get("score")
                if not isinstance(score, int) or isinstance(score, bool):
                    raise ValueError("Opportunity score must be an integer.")
                opportunity = self.server.repository.create_opportunity(
                    self._required_text(payload, "id", "Opportunity"),
                    self._required_text(payload, "title", "Opportunity"),
                    self._required_text(payload, "summary", "Opportunity"),
                    self._required_text(payload, "why_now", "Opportunity"),
                    score,
                    self._required_text(payload, "status", "Opportunity"),
                    self._optional_object(payload, "metadata", "Opportunity"),
                )
            except (json.JSONDecodeError, ValueError, sqlite3.IntegrityError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            self._send_json(
                {"kind": "opportunity", "opportunity": self._opportunity_payload(opportunity)},
                HTTPStatus.CREATED,
            )
            return
        source_prefix = "/api/sources"
        if path == source_prefix:
            try:
                payload = self._read_json_object("Source payload")
                self._reject_unsupported_fields(
                    payload,
                    {
                        "id",
                        "source_type",
                        "title",
                        "publisher",
                        "url",
                        "accessed_at",
                        "author",
                        "publication_date",
                        "jurisdiction",
                        "metadata",
                    },
                    "Source payload",
                )
                source = self.server.repository.create_source(
                    self._required_text(payload, "id", "Source"),
                    self._required_text(payload, "source_type", "Source"),
                    self._required_text(payload, "title", "Source"),
                    self._required_text(payload, "publisher", "Source"),
                    self._required_text(payload, "url", "Source"),
                    self._required_text(payload, "accessed_at", "Source"),
                    self._optional_text(payload, "author", "Source"),
                    self._optional_text(payload, "publication_date", "Source"),
                    self._optional_text(payload, "jurisdiction", "Source"),
                    self._optional_object(payload, "metadata", "Source"),
                )
            except (json.JSONDecodeError, ValueError, sqlite3.IntegrityError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            self._send_json(
                {"kind": "source", "source": self._source_payload(source)}, HTTPStatus.CREATED
            )
            return
        claim_prefix = "/api/claims/"
        evidence_suffix = "/evidence"
        if path.startswith(claim_prefix) and path.endswith(evidence_suffix):
            claim_id = unquote(path[len(claim_prefix) : -len(evidence_suffix)]).strip("/")
            if not claim_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                payload = self._read_json_object("ClaimEvidence payload")
                self._reject_unsupported_fields(
                    payload, {"source_id", "stance", "reference", "notes"}, "ClaimEvidence payload"
                )
                self.server.repository.get_claim(claim_id)
                source_id = self._required_text(payload, "source_id", "ClaimEvidence")
                self.server.repository.get_source(source_id)
                reference = payload.get("reference")
                notes = payload.get("notes", "")
                if reference is not None and not isinstance(reference, str):
                    raise ValueError("ClaimEvidence reference must be text or null.")
                if not isinstance(notes, str):
                    raise ValueError("ClaimEvidence notes must be text.")
                evidence = self.server.repository.link_claim_evidence(
                    claim_id,
                    source_id,
                    self._required_text(payload, "stance", "ClaimEvidence"),
                    reference,
                    notes,
                )
            except (json.JSONDecodeError, ValueError, sqlite3.IntegrityError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except KeyError:
                self._send_json({"error": "Claim or Source not found."}, HTTPStatus.NOT_FOUND)
                return
            self._send_json(
                {
                    "kind": "claim_evidence",
                    "claim_evidence": self._claim_evidence_payload(evidence),
                },
                HTTPStatus.CREATED,
            )
            return
        research_pack_prefix = "/api/research-packs/"
        claim_suffix = "/claims"
        if path.startswith(research_pack_prefix) and path.endswith(claim_suffix):
            research_pack_id = unquote(path[len(research_pack_prefix) : -len(claim_suffix)]).strip(
                "/"
            )
            if not research_pack_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                payload = self._read_json_object("Claim payload")
                self._reject_unsupported_fields(
                    payload,
                    {
                        "id",
                        "text",
                        "claim_type",
                        "risk_level",
                        "freshness_type",
                        "verification_status",
                        "verification_notes",
                        "reviewed_at",
                        "metadata",
                    },
                    "Claim payload",
                )
                self.server.repository.get_research_pack(research_pack_id)
                verification_notes = payload.get("verification_notes")
                if not isinstance(verification_notes, str):
                    raise ValueError("Claim verification_notes must be text.")
                claim = self.server.repository.create_claim(
                    self._required_text(payload, "id", "Claim"),
                    research_pack_id,
                    self._required_text(payload, "text", "Claim"),
                    self._required_text(payload, "claim_type", "Claim"),
                    self._required_text(payload, "risk_level", "Claim"),
                    self._required_text(payload, "freshness_type", "Claim"),
                    self._required_text(payload, "verification_status", "Claim"),
                    verification_notes,
                    self._optional_text(payload, "reviewed_at", "Claim"),
                    self._optional_object(payload, "metadata", "Claim"),
                )
            except (json.JSONDecodeError, ValueError, sqlite3.IntegrityError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except KeyError:
                self._send_json({"error": "ResearchPack not found."}, HTTPStatus.NOT_FOUND)
                return
            self._send_json(
                {"kind": "claim", "claim": self._claim_payload(claim)}, HTTPStatus.CREATED
            )
            return
        editorial_angle_prefix = "/api/editorial-angles/"
        editorial_angle_claim_suffix = "/claims"
        if path.startswith(editorial_angle_prefix) and path.endswith(editorial_angle_claim_suffix):
            editorial_angle_id = unquote(
                path[len(editorial_angle_prefix) : -len(editorial_angle_claim_suffix)]
            ).strip("/")
            if not editorial_angle_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                payload = self._read_json_object("EditorialAngle Claim payload")
                self._reject_unsupported_fields(
                    payload, {"claim_id", "role"}, "EditorialAngle Claim payload"
                )
                self.server.repository.get_editorial_angle(editorial_angle_id)
                claim_id = self._required_text(payload, "claim_id", "EditorialAngle Claim")
                self.server.repository.get_claim(claim_id)
                link = self.server.repository.link_claim_to_editorial_angle(
                    editorial_angle_id,
                    claim_id,
                    self._required_text(payload, "role", "EditorialAngle Claim"),
                )
            except (json.JSONDecodeError, ValueError, sqlite3.IntegrityError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except KeyError:
                self._send_json(
                    {"error": "EditorialAngle or Claim not found."}, HTTPStatus.NOT_FOUND
                )
                return
            self._send_json(
                {
                    "kind": "editorial_angle_claim",
                    "editorial_angle_claim": self._editorial_angle_claim_payload(link),
                },
                HTTPStatus.CREATED,
            )
            return
        imported_reference_suffix = "/reference-sets/imported"
        reference_prefix = "/api/character-profiles/"
        if path.startswith(reference_prefix) and path.endswith(imported_reference_suffix):
            character_profile_id = unquote(
                path[len(reference_prefix) : -len(imported_reference_suffix)]
            ).strip("/")
            if not character_profile_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                payload = self._read_json_object("Imported CharacterReferenceSet payload")
                self._reject_unsupported_fields(
                    payload, {"id", "asset_ids"}, "Imported CharacterReferenceSet payload"
                )
                asset_ids = payload.get("asset_ids")
                if not isinstance(asset_ids, list):
                    raise ValueError("asset_ids must be an ordered list.")
                create_reference_set = (
                    self.server.repository.create_character_reference_set_from_imported_assets
                )
                reference_set = create_reference_set(
                    self._required_text(payload, "id", "Imported CharacterReferenceSet"),
                    character_profile_id,
                    asset_ids,
                )
            except (json.JSONDecodeError, ValueError, sqlite3.IntegrityError) as error:
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
        narration_prefix = "/api/scripts/"
        narration_import_suffix = "/narration-assets/import"
        if path.startswith(narration_prefix) and path.endswith(narration_import_suffix):
            script_id = unquote(path[len(narration_prefix) : -len(narration_import_suffix)]).strip(
                "/"
            )
            if not script_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                forbidden_headers = {
                    "X-Narration-Digest",
                    "X-Narration-Duration",
                    "X-Narration-Storage-Path",
                    "X-Narration-Source-Kind",
                }
                content = self._read_imported_narration_content()
                if any(header in self.headers for header in forbidden_headers):
                    raise ValueError(
                        "NarrationAsset digest, duration, storage path, and source kind are "
                        "server-derived."
                    )
                media_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip()
                narration_asset_id = self.headers.get("X-Narration-Asset-ID") or (
                    f"narration-import-{uuid.uuid4().hex}"
                )
                narration = self.server.media_service.import_narration(
                    narration_asset_id, script_id, content, media_type
                )
            except (ValueError, MediaRuntimeError, sqlite3.IntegrityError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except KeyError:
                self._send_json({"error": "Script not found."}, HTTPStatus.NOT_FOUND)
                return
            self._send_json(
                {
                    "kind": "narration_asset",
                    "narration_asset": self._narration_asset_payload(narration),
                },
                HTTPStatus.CREATED,
            )
            return
        final_media_snapshot_prefix = "/api/visual-plans/"
        final_media_snapshot_suffix = "/final-media-input-snapshots"
        if path.startswith(final_media_snapshot_prefix) and path.endswith(
            final_media_snapshot_suffix
        ):
            visual_plan_id = unquote(
                path[len(final_media_snapshot_prefix) : -len(final_media_snapshot_suffix)]
            ).strip("/")
            if not visual_plan_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                payload = self._read_json_object("FinalMediaInputSnapshot payload")
                self._reject_unsupported_fields(
                    payload,
                    {"id", "narration_asset_id", "scene_inputs"},
                    "FinalMediaInputSnapshot payload",
                )
                scene_inputs = payload.get("scene_inputs")
                if not isinstance(scene_inputs, list):
                    raise ValueError("FinalMediaInputSnapshot scene_inputs must be a list.")
                snapshot = self.server.media_service.create_snapshot(
                    self._required_text(payload, "id", "FinalMediaInputSnapshot"),
                    visual_plan_id,
                    self._required_text(payload, "narration_asset_id", "FinalMediaInputSnapshot"),
                    scene_inputs,
                )
            except (json.JSONDecodeError, ValueError, sqlite3.IntegrityError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except KeyError:
                self._send_json(
                    {
                        "error": (
                            "VisualPlan, NarrationAsset, AssetSelection, AssetSpec, or Asset "
                            "not found."
                        )
                    },
                    HTTPStatus.NOT_FOUND,
                )
                return
            self._send_json(
                {
                    "kind": "final_media_input_snapshot",
                    "final_media_input_snapshot": self._snapshot_payload(snapshot),
                },
                HTTPStatus.CREATED,
            )
            return
        render_prefix = "/api/final-media-input-snapshots/"
        render_suffix = "/render-executions"
        if path.startswith(render_prefix) and path.endswith(render_suffix):
            snapshot_id = unquote(path[len(render_prefix) : -len(render_suffix)]).strip("/")
            if not snapshot_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                payload = self._read_json_object("RenderExecution payload")
                self._reject_unsupported_fields(
                    payload, {"id", "artifact_id"}, "RenderExecution payload"
                )
                execution_id = self._required_text(payload, "id", "RenderExecution")
                artifact_id = self._required_text(payload, "artifact_id", "RenderExecution")
                artifact = self.server.media_service.render(execution_id, artifact_id, snapshot_id)
                execution = self.server.repository.get_render_execution(execution_id)
            except json.JSONDecodeError as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except KeyError as error:
                if error.args and error.args[0] == snapshot_id:
                    self._send_json(
                        {"error": "FinalMediaInputSnapshot not found."}, HTTPStatus.NOT_FOUND
                    )
                else:
                    self._send_json(
                        {"error": "Render lifecycle input not found."}, HTTPStatus.NOT_FOUND
                    )
                return
            except (ValueError, sqlite3.IntegrityError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except MediaRuntimeError as error:
                try:
                    execution = self.server.repository.get_render_execution(execution_id)
                except KeyError:
                    self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                    return
                self._send_json(
                    {
                        "kind": "render_execution",
                        "render_execution": self._render_execution_payload(execution),
                        "final_media_artifact": None,
                    },
                    HTTPStatus.CREATED,
                )
                return
            self._send_json(
                {
                    "kind": "render_execution",
                    "render_execution": self._render_execution_payload(execution),
                    "final_media_artifact": self._artifact_payload(artifact),
                },
                HTTPStatus.CREATED,
            )
            return
        visual_plan_prefix = "/api/visual-plans/"
        scene_suffix = "/scenes"
        if path.startswith(visual_plan_prefix) and path.endswith(scene_suffix):
            visual_plan_id = unquote(path[len(visual_plan_prefix) : -len(scene_suffix)]).strip("/")
            if not visual_plan_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                payload = self._read_json_object("Scene payload")
                allowed_fields = {
                    "id",
                    "sequence",
                    "narration_excerpt",
                    "visual_intent",
                    "hamster_action",
                    "on_screen_text",
                    "transition_note",
                    "metadata",
                }
                self._reject_unsupported_fields(payload, allowed_fields, "Scene payload")
                scene = self.server.repository.create_scene_under_visual_plan_authorization(
                    self._required_text(payload, "id", "Scene"),
                    visual_plan_id,
                    payload.get("sequence"),
                    self._required_text(payload, "narration_excerpt", "Scene"),
                    self._required_text(payload, "visual_intent", "Scene"),
                    self._optional_text(payload, "hamster_action", "Scene"),
                    self._optional_text(payload, "on_screen_text", "Scene"),
                    self._optional_text(payload, "transition_note", "Scene"),
                    self._optional_object(payload, "metadata", "Scene"),
                )
            except (json.JSONDecodeError, ValueError, sqlite3.IntegrityError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except KeyError:
                self._send_json({"error": "VisualPlan not found."}, HTTPStatus.NOT_FOUND)
                return
            self._send_json(
                {"kind": "scene", "scene": self._scene_payload(scene)}, HTTPStatus.CREATED
            )
            return
        scene_prefix = "/api/scenes/"
        asset_spec_suffix = "/asset-specs"
        if path.startswith(scene_prefix) and path.endswith(asset_spec_suffix):
            scene_id = unquote(path[len(scene_prefix) : -len(asset_spec_suffix)]).strip("/")
            if not scene_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                payload = self._read_json_object("AssetSpec payload")
                allowed_fields = {
                    "id",
                    "asset_type",
                    "purpose",
                    "description",
                    "generation_prompt",
                    "continuity_key",
                    "character_profile_id",
                    "metadata",
                }
                self._reject_unsupported_fields(payload, allowed_fields, "AssetSpec payload")
                asset_spec = self.server.repository.create_asset_spec_under_scene_authorization(
                    self._required_text(payload, "id", "AssetSpec"),
                    scene_id,
                    self._required_text(payload, "asset_type", "AssetSpec"),
                    self._required_text(payload, "purpose", "AssetSpec"),
                    self._required_text(payload, "description", "AssetSpec"),
                    self._required_text(payload, "generation_prompt", "AssetSpec"),
                    self._optional_text(payload, "continuity_key", "AssetSpec"),
                    self._optional_text(payload, "character_profile_id", "AssetSpec"),
                    self._optional_object(payload, "metadata", "AssetSpec"),
                )
            except (json.JSONDecodeError, ValueError, sqlite3.IntegrityError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except KeyError:
                self._send_json(
                    {"error": "Scene or CharacterProfile not found."}, HTTPStatus.NOT_FOUND
                )
                return
            self._send_json(
                {
                    "kind": "asset_spec",
                    "asset_spec": self.server.repository.asset_spec_payload(asset_spec.id),
                },
                HTTPStatus.CREATED,
            )
            return
        asset_spec_prefix = "/api/asset-specs/"
        import_suffix = "/assets/import"
        selection_suffix = "/asset-selections"
        if path.startswith(asset_spec_prefix) and path.endswith(import_suffix):
            asset_spec_id = unquote(path[len(asset_spec_prefix) : -len(import_suffix)]).strip("/")
            if not asset_spec_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                forbidden_headers = {
                    "X-Asset-Version",
                    "X-Asset-Digest",
                    "X-Asset-Storage-Path",
                    "X-Asset-Source-Kind",
                }
                if any(header in self.headers for header in forbidden_headers):
                    raise ValueError(
                        "Imported Asset version, digest, storage path, and source kind are "
                        "server-derived."
                    )
                content = self._read_imported_asset_content()
                media_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip()
                asset_id = self.headers.get("X-Asset-ID") or f"asset-import-{uuid.uuid4().hex}"
                asset = self.server.repository.import_asset_under_asset_spec_authorization(
                    asset_id,
                    asset_spec_id,
                    content,
                    media_type,
                    self.server.generation_service.storage,
                )
            except (ValueError, sqlite3.IntegrityError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except KeyError:
                self._send_json({"error": "AssetSpec not found."}, HTTPStatus.NOT_FOUND)
                return
            except (AssetStorageFailure, OSError):
                self._send_json(
                    {"error": "Conveyor could not store the imported Asset."},
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                )
                return
            self._send_json(
                {"kind": "asset", "asset": self._asset_payload(asset)}, HTTPStatus.CREATED
            )
            return
        if path.startswith(asset_spec_prefix) and path.endswith(selection_suffix):
            asset_spec_id = unquote(path[len(asset_spec_prefix) : -len(selection_suffix)]).strip(
                "/"
            )
            if not asset_spec_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                payload = self._read_json_object("AssetSelection payload")
                self._reject_unsupported_fields(
                    payload,
                    {"id", "asset_id", "character_reference_set_id"},
                    "AssetSelection payload",
                )
                selection = self.server.repository.create_asset_selection(
                    self._required_text(payload, "id", "AssetSelection"),
                    asset_spec_id,
                    self._required_text(payload, "asset_id", "AssetSelection"),
                    self._optional_text(payload, "character_reference_set_id", "AssetSelection"),
                )
            except (json.JSONDecodeError, ValueError, sqlite3.IntegrityError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except KeyError:
                self._send_json(
                    {"error": "AssetSpec, Asset, or CharacterReferenceSet not found."},
                    HTTPStatus.NOT_FOUND,
                )
                return
            self._send_json(
                {
                    "kind": "asset_selection",
                    "asset_selection": self.server.repository.asset_selection_payload(selection.id),
                },
                HTTPStatus.CREATED,
            )
            return
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

    def do_PUT(self) -> None:  # noqa: N802
        """Update only mutable operational Scene or AssetSpec authoring detail."""

        path = urlparse(self.path).path
        scene_prefix = "/api/scenes/"
        if path.startswith(scene_prefix):
            scene_id = unquote(path[len(scene_prefix) :]).strip("/")
            if not scene_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                payload = self._read_json_object("Scene update payload")
                allowed_fields = {
                    "sequence",
                    "narration_excerpt",
                    "visual_intent",
                    "hamster_action",
                    "on_screen_text",
                    "transition_note",
                    "metadata",
                }
                self._reject_unsupported_fields(payload, allowed_fields, "Scene update payload")
                if not payload:
                    raise ValueError("Scene update payload must include one mutable field.")
                scene = self.server.repository.get_scene(scene_id)
                changes = self._scene_changes(payload)
                updated = self.server.repository.update_scene_under_visual_plan_authorization(
                    replace(scene, **changes)
                )
            except (json.JSONDecodeError, ValueError, sqlite3.IntegrityError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except KeyError:
                self._send_json({"error": "Scene not found."}, HTTPStatus.NOT_FOUND)
                return
            self._send_json({"kind": "scene", "scene": self._scene_payload(updated)})
            return
        asset_spec_prefix = "/api/asset-specs/"
        if path.startswith(asset_spec_prefix):
            asset_spec_id = unquote(path[len(asset_spec_prefix) :]).strip("/")
            if not asset_spec_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                return
            try:
                payload = self._read_json_object("AssetSpec update payload")
                allowed_fields = {
                    "asset_type",
                    "purpose",
                    "description",
                    "generation_prompt",
                    "continuity_key",
                    "character_profile_id",
                    "metadata",
                }
                self._reject_unsupported_fields(payload, allowed_fields, "AssetSpec update payload")
                if not payload:
                    raise ValueError("AssetSpec update payload must include one mutable field.")
                asset_spec = self.server.repository.get_asset_spec(asset_spec_id)
                changes = self._asset_spec_changes(payload)
                updated = self.server.repository.update_asset_spec_under_scene_authorization(
                    replace(asset_spec, **changes)
                )
            except (json.JSONDecodeError, ValueError, sqlite3.IntegrityError) as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            except KeyError:
                self._send_json(
                    {"error": "AssetSpec or CharacterProfile not found."}, HTTPStatus.NOT_FOUND
                )
                return
            self._send_json(
                {
                    "kind": "asset_spec",
                    "asset_spec": self.server.repository.asset_spec_payload(updated.id),
                }
            )
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def _read_json_object(self, label: str) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(content_length))
        if not isinstance(payload, dict):
            raise ValueError(f"{label} must be an object.")
        return payload

    def _read_imported_asset_content(self) -> bytes:
        try:
            content_length = int(self.headers.get("Content-Length", ""))
        except ValueError as error:
            raise ValueError("Imported Asset Content-Length must be an integer.") from error
        if content_length < 1 or content_length > MAX_IMPORTED_ASSET_BYTES:
            raise ValueError(
                f"Imported Asset content must be between 1 and {MAX_IMPORTED_ASSET_BYTES} bytes."
            )
        content = self.rfile.read(content_length)
        if len(content) != content_length:
            raise ValueError(
                "Imported Asset request body ended before Content-Length bytes arrived."
            )
        return content

    def _read_imported_narration_content(self) -> bytes:
        try:
            content_length = int(self.headers.get("Content-Length", ""))
        except ValueError as error:
            raise ValueError("NarrationAsset Content-Length must be an integer.") from error
        if content_length < 1 or content_length > MAX_IMPORTED_NARRATION_BYTES:
            raise ValueError(
                "NarrationAsset content must be between 1 and "
                f"{MAX_IMPORTED_NARRATION_BYTES} bytes."
            )
        content = self.rfile.read(content_length)
        if len(content) != content_length:
            raise ValueError(
                "NarrationAsset request body ended before Content-Length bytes arrived."
            )
        return content

    @staticmethod
    def _reject_unsupported_fields(payload: dict, allowed_fields: set[str], label: str) -> None:
        if set(payload) - allowed_fields:
            raise ValueError(f"{label} contains unsupported fields.")

    @staticmethod
    def _required_text(payload: dict, field: str, label: str) -> str:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{label} {field} must be non-empty text.")
        return value.strip()

    @staticmethod
    def _optional_text(payload: dict, field: str, label: str) -> str | None:
        value = payload.get(field)
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{label} {field} must be non-empty text or null.")
        return value.strip()

    @staticmethod
    def _optional_object(payload: dict, field: str, label: str) -> dict | None:
        value = payload.get(field)
        if value is None:
            return None
        if not isinstance(value, dict):
            raise ValueError(f"{label} {field} must be an object or null.")
        return value

    def _scene_changes(self, payload: dict) -> dict:
        changes = {}
        for field in (
            "narration_excerpt",
            "visual_intent",
            "hamster_action",
            "on_screen_text",
            "transition_note",
        ):
            if field in payload:
                changes[field] = self._optional_text(payload, field, "Scene")
                if field in {"narration_excerpt", "visual_intent"} and changes[field] is None:
                    raise ValueError(f"Scene {field} must be non-empty text.")
        if "sequence" in payload:
            changes["sequence"] = payload["sequence"]
        if "metadata" in payload:
            changes["metadata"] = self._optional_object(payload, "metadata", "Scene") or {}
        return changes

    def _asset_spec_changes(self, payload: dict) -> dict:
        changes = {}
        for field in ("asset_type", "purpose", "description", "generation_prompt"):
            if field in payload:
                changes[field] = self._required_text(payload, field, "AssetSpec")
        for field in ("continuity_key", "character_profile_id"):
            if field in payload:
                changes[field] = self._optional_text(payload, field, "AssetSpec")
        if "metadata" in payload:
            changes["metadata"] = self._optional_object(payload, "metadata", "AssetSpec") or {}
        return changes

    @staticmethod
    def _opportunity_payload(opportunity) -> dict:
        return {
            "id": opportunity.id,
            "title": opportunity.title,
            "summary": opportunity.summary,
            "why_now": opportunity.why_now,
            "score": opportunity.score,
            "status": opportunity.status,
            "metadata": opportunity.metadata,
            "created_at": opportunity.created_at,
            "updated_at": opportunity.updated_at,
        }

    @staticmethod
    def _claim_payload(claim) -> dict:
        return {
            "id": claim.id,
            "research_pack_id": claim.research_pack_id,
            "text": claim.text,
            "claim_type": claim.claim_type,
            "risk_level": claim.risk_level,
            "freshness_type": claim.freshness_type,
            "verification_status": claim.verification_status,
            "verification_notes": claim.verification_notes,
            "reviewed_at": claim.reviewed_at,
            "metadata": claim.metadata,
            "created_at": claim.created_at,
            "updated_at": claim.updated_at,
        }

    @staticmethod
    def _source_payload(source) -> dict:
        return {
            "id": source.id,
            "source_type": source.source_type,
            "title": source.title,
            "publisher": source.publisher,
            "author": source.author,
            "url": source.url,
            "publication_date": source.publication_date,
            "accessed_at": source.accessed_at,
            "jurisdiction": source.jurisdiction,
            "metadata": source.metadata,
            "created_at": source.created_at,
            "updated_at": source.updated_at,
        }

    @staticmethod
    def _claim_evidence_payload(evidence) -> dict:
        return {
            "claim_id": evidence.claim_id,
            "source_id": evidence.source_id,
            "stance": evidence.stance,
            "reference": evidence.reference,
            "notes": evidence.notes,
            "created_at": evidence.created_at,
            "updated_at": evidence.updated_at,
        }

    @staticmethod
    def _editorial_angle_claim_payload(link) -> dict:
        return {
            "editorial_angle_id": link.editorial_angle_id,
            "claim_id": link.claim_id,
            "role": link.role,
            "created_at": link.created_at,
        }

    @staticmethod
    def _scene_payload(scene) -> dict:
        return {
            "id": scene.id,
            "visual_plan_id": scene.visual_plan_id,
            "sequence": scene.sequence,
            "narration_excerpt": scene.narration_excerpt,
            "visual_intent": scene.visual_intent,
            "hamster_action": scene.hamster_action,
            "on_screen_text": scene.on_screen_text,
            "transition_note": scene.transition_note,
            "metadata": scene.metadata,
        }

    @staticmethod
    def _asset_payload(asset) -> dict:
        return {
            "id": asset.id,
            "asset_spec_id": asset.asset_spec_id,
            "version": asset.version,
            "storage_path": asset.storage_path,
            "media_type": asset.media_type,
            "source_kind": asset.source_kind,
            "content_digest": asset.content_digest,
        }

    @staticmethod
    def _narration_asset_payload(narration) -> dict:
        return {
            "id": narration.id,
            "script_id": narration.script_id,
            "media_type": narration.media_type,
            "source_kind": narration.source_kind,
            "content_digest": narration.content_digest,
            "duration_ms": narration.duration_ms,
            "created_at": narration.created_at,
        }

    @staticmethod
    def _snapshot_payload(snapshot) -> dict:
        return {
            "id": snapshot.id,
            "visual_plan_id": snapshot.visual_plan_id,
            "script_id": snapshot.script_id,
            "narration_asset_id": snapshot.narration_asset_id,
            "snapshot_schema_version": snapshot.snapshot_schema_version,
            "scene_inputs": snapshot.scene_inputs,
            "caption_cues": snapshot.caption_cues,
            "render_settings": snapshot.render_settings,
            "created_at": snapshot.created_at,
        }

    @staticmethod
    def _render_execution_payload(execution) -> dict:
        return {
            "id": execution.id,
            "final_media_input_snapshot_id": execution.final_media_input_snapshot_id,
            "renderer_key": execution.renderer_key,
            "renderer_version": execution.renderer_version,
            "probe_version": execution.probe_version,
            "outcome": execution.outcome,
            "error_code": execution.error_code,
            "error_message": execution.error_message,
            "execution_metadata": execution.execution_metadata,
            "created_at": execution.created_at,
        }

    @staticmethod
    def _artifact_payload(artifact) -> dict:
        return {
            "id": artifact.id,
            "render_execution_id": artifact.render_execution_id,
            "media_type": artifact.media_type,
            "content_digest": artifact.content_digest,
            "duration_ms": artifact.duration_ms,
            "width": artifact.width,
            "height": artifact.height,
            "technical_validation": artifact.technical_validation,
            "created_at": artifact.created_at,
        }

    def _youtube_upload(self, action) -> None:
        """Serve the founder upload screen only to same-origin loopback requests."""

        controller = self.server.youtube_upload
        if controller is None:
            self._discard_small_body()
            self._send_html(
                "<!doctype html><title>YouTube upload</title><p>YouTube upload is not "
                "configured for this server.</p>",
                HTTPStatus.SERVICE_UNAVAILABLE,
            )
            return
        # The real socket peer and the bound address must be loopback; Host and Origin are
        # client-controlled and only add DNS-rebinding/cross-site protection on top.
        if (
            not is_loopback(self.client_address[0])
            or not is_loopback(self.server.server_address[0])
            or not controller.allowed_request(
                self.headers.get("Host"), self.headers.get("Origin"), self.server.server_address[1]
            )
        ):
            self._discard_small_body()
            self._send_html("<!doctype html><p>Forbidden.</p>", HTTPStatus.FORBIDDEN)
            return
        try:
            status, page = action(controller)
        except ValueError as error:
            status, page = HTTPStatus.BAD_REQUEST, f"<!doctype html><p>{escape(str(error))}</p>"
        self._send_html(page, HTTPStatus(status))

    def _discard_small_body(self) -> None:
        """Consume a small refused request body so the client sees the response, not a reset."""

        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return
        if 0 < length <= 64 * 1024:
            self.rfile.read(length)

    def _read_upload_form(self) -> dict[str, str]:
        media_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip()
        length = int(self.headers.get("Content-Length") or 0)
        if media_type != "application/x-www-form-urlencoded" or not 0 < length <= 64 * 1024:
            raise ValueError("The upload confirmation form is invalid.")
        fields = parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True)
        return {name: values[0] for name, values in fields.items() if len(values) == 1}

    def _send_html(self, page: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = page.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        # The confirmation screen must not be framed (clickjacking) or post elsewhere.
        self.send_header("X-Frame-Options", "DENY")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; "
            "frame-ancestors 'none'",
        )
        self.end_headers()
        self.wfile.write(body)

    def _send_binary(self, content: bytes, media_type: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", media_type)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

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
        media_runtime: FfmpegRuntime | None = None,
        media_storage_root: Path | None = None,
        youtube_upload: Any | None = None,
    ) -> None:
        if youtube_upload is not None and not is_loopback(address[0]):
            # Fail closed: the founder upload surface never listens beyond this machine.
            raise ValueError("YouTube upload requires the server to bind a loopback address.")
        super().__init__(address, AtlasRequestHandler)
        self.repository = repository
        self.generation_service = generation_service
        self.media_runtime = media_runtime
        self.media_storage_root = media_storage_root
        # Optional founder YouTube upload screen; absent unless explicitly configured.
        self.youtube_upload = youtube_upload

    @property
    def media_service(self) -> MediaService:
        """Resolve local FFmpeg only when an approved media lifecycle route needs it."""

        return MediaService(
            self.repository,
            self.media_runtime or FfmpegRuntime(),
            LocalMediaStorage(self.media_storage_root),
        )

    @property
    def production_service(self) -> ProductionLifecycleService:
        """Compose the canonical v2 lifecycle from existing server-owned services."""

        return ProductionLifecycleService(
            self.repository,
            self.generation_service,
            self.media_service,
        )

    def server_close(self) -> None:
        super().server_close()
        self.repository.close()


def create_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    database_path: Path | None = None,
    generator: AssetGenerator | None = None,
    asset_storage_root: Path | None = None,
    media_runtime: FfmpegRuntime | None = None,
    media_storage_root: Path | None = None,
    youtube_upload: Callable[[AtlasRepository], Any] | None = None,
) -> AtlasHTTPServer:
    """Create the MVP server without starting it, for testability.

    ``youtube_upload`` builds the optional founder upload controller from the repository.
    """

    if youtube_upload is not None and not is_loopback(host):
        raise ValueError("YouTube upload requires the server to bind a loopback address.")
    repository = AtlasRepository(database_path, asset_storage_root=asset_storage_root)
    return AtlasHTTPServer(
        (host, port),
        repository,
        GenerationService(
            repository,
            generator or OpenAIImageGenerator(),
            LocalAssetStorage(asset_storage_root),
        ),
        media_runtime,
        media_storage_root,
        youtube_upload(repository) if youtube_upload else None,
    )


def main() -> None:
    """Start the local MVP UI shell."""

    parser = argparse.ArgumentParser(description="Run the Conveyor MVP UI shell.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1).")
    parser.add_argument("--port", default=8000, type=int, help="Port to bind (default: 8000).")
    args = parser.parse_args()
    youtube_upload = None
    client_config = os.environ.get("ATLAS_YOUTUBE_CLIENT_CONFIG", "").strip()
    if client_config:
        from project_atlas.youtube_upload import YouTubeUploadController

        def youtube_upload(repository: AtlasRepository) -> YouTubeUploadController:
            return YouTubeUploadController.from_client_config(
                repository,
                None,
                Path(client_config),
                Path(__file__).resolve().parents[2],
            )

    server = create_server(args.host, args.port, youtube_upload=youtube_upload)
    print(f"Conveyor MVP is running at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nConveyor MVP stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
