"""Dependency-free local server for the Project Atlas MVP UI shell."""

from __future__ import annotations

import argparse
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from project_atlas.demo_data import ACTIVITY, chat_reply, content_payload
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
        if parsed.path == "/api/demo/content":
            content = content_payload().copy()
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
            self._send_json({"kind": "demo", "content": content, "activity": ACTIVITY})
            return
        if parsed.path == "/api/demo/chat":
            message = parse_qs(parsed.query).get("message", [""])[0]
            self._send_json({"kind": "demo", "reply": chat_reply(message)})
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

    def _send_json(self, payload: object) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        """Keep local demo-server logs concise."""

        print(f"[Atlas] {format % args}")


class AtlasHTTPServer(HTTPServer):
    """HTTP server that owns the local Atlas application repository."""

    def __init__(self, address: tuple[str, int], repository: AtlasRepository) -> None:
        super().__init__(address, AtlasRequestHandler)
        self.repository = repository

    def server_close(self) -> None:
        super().server_close()
        self.repository.close()


def create_server(
    host: str = "127.0.0.1", port: int = 8000, database_path: Path | None = None
) -> AtlasHTTPServer:
    """Create the MVP server without starting it, for testability."""

    return AtlasHTTPServer((host, port), AtlasRepository(database_path))


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
