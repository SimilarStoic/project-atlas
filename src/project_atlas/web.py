"""Dependency-free local server for the Project Atlas MVP UI shell."""

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
                {"error": "Atlas could not persist the generation result."},
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

        print(f"[Atlas] {format % args}")


class AtlasHTTPServer(HTTPServer):
    """HTTP server that owns the local Atlas application repository."""

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

    parser = argparse.ArgumentParser(description="Run the Project Atlas MVP UI shell.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1).")
    parser.add_argument("--port", default=8000, type=int, help="Port to bind (default: 8000).")
    args = parser.parse_args()
    server = create_server(args.host, args.port)
    print(f"Project Atlas MVP is running at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nProject Atlas MVP stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
