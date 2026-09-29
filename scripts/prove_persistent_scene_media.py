"""Create the disposable three-state persistent-scene final-media proof."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from project_atlas.scene_media import load_persistent_scene_frame


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from tests.test_media import _runtime_or_skip
    from tests.test_persistent_scene_media import _proof

    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    output = arguments.output.resolve()
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing proof directory: {output}")
    output.mkdir(parents=True)
    work = Path(tempfile.mkdtemp(prefix="persistent-scene-media-", dir=output.parent))
    runtime = _runtime_or_skip()
    repository, service, world, states, snapshot = _proof(work, runtime)
    try:
        frame_records = []
        for index, state in enumerate(states, 1):
            frame = load_persistent_scene_frame(repository, state.state_id)
            frame_path = output / f"state-{index}.png"
            frame_path.write_bytes(frame.png)
            frame_records.append(
                {
                    "state_id": state.state_id,
                    "state_digest": state.state_digest,
                    "frame_path": frame_path.name,
                    "rgba_digest": frame.rgba_digest,
                    "png_digest": frame.png_digest,
                }
            )
        (output / "snapshot-v2.json").write_text(
            json.dumps(asdict(snapshot), indent=2, sort_keys=True), encoding="utf-8"
        )
        artifact = service.render("proof-execution", "proof-artifact", snapshot.id)
        source_video = service.storage.path(artifact.storage_path)
        proof_video = output / "persistent-scene-three-state-proof.mp4"
        shutil.copyfile(source_video, proof_video)
        probe = runtime.probe(proof_video)
        (output / "ffprobe.json").write_text(
            json.dumps(probe.raw, indent=2, sort_keys=True), encoding="utf-8"
        )
        summary = {
            "snapshot_id": snapshot.id,
            "snapshot_schema_version": snapshot.snapshot_schema_version,
            "visual_plan_id": snapshot.visual_plan_id,
            "world_key": world.world_key,
            "world_definition_digest": world.definition_digest,
            "frames": frame_records,
            "video": {
                "path": proof_video.name,
                "sha256": sha256(proof_video.read_bytes()).hexdigest(),
                "duration_ms": probe.duration_ms,
                "width": probe.width,
                "height": probe.height,
                "video_codec": probe.video_codec,
                "audio_codec": probe.audio_codec,
                "frame_rate": probe.frame_rate,
            },
            "provider_calls": 0,
            "spend_usd": 0,
        }
        (output / "proof-summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
        )
        print(json.dumps(summary, sort_keys=True))
    finally:
        repository.close()
        shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
