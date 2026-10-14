"""Zero-spend validation of the whole recipe workflow through the operator CLI.

Every step runs against a temporary runtime with stand-in providers and an isolated network.
The founder approvals below are simulated in this isolated test database only; they prove the
workflow's wiring and gates, never image or voice quality, and never become founder evidence.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from project_atlas import production_cli
from project_atlas.generation import GeneratedArtifact
from project_atlas.production_backup import database_sha256
from tests.test_production_lifecycle import (
    GLOBAL_AUTHORITY,
    HOME_FAMILY,
    _home_authority,
    _request,
    _scores,
    _server,
    _sine_seconds,
    _take_sequence,
    realistic_source_png,
    transcription,  # noqa: F401  (autouse: no test reaches the real recognizer)
)
from tests.test_progression import _object_canvas
from tests.test_web import create_authorized_visual_plan, media_runtime_or_skip

pytestmark = pytest.mark.spend_gate
PREFIX = "wf"
EXCERPTS = [
    "Imagine one quiet room.",
    "Nobody is home.",
    "A coin appears.",
    "Then another coin appears.",
    "That is the whole story.",
]
SCRIPT = " ".join(EXCERPTS)
CANONICAL_REFERENCE_SET = "character-reference-set-similarstoic-hamster-core-v2"


class StandInGenerator:
    """Provider-free images: full scenes for bases, an outlined object canvas for props."""

    generator_key = "workflow-stand-in"

    def __init__(self, scene: bytes, prop: bytes) -> None:
        self.scene, self.prop, self.calls = scene, prop, []

    def supports(self, asset_type: str) -> bool:
        return True

    def generate(self, generation_input):
        self.calls.append(generation_input.asset_type)
        content = self.prop if generation_input.asset_type == "prop" else self.scene
        return GeneratedArtifact(content, "image/png", provider_key="workflow-stand-in")


def _story(path: Path) -> Path:
    story = {
        "recipe": "similarstoic-flow-v1",
        "run_id": f"{PREFIX}-run",
        "visual_plan_id": f"{PREFIX}-story-plan",
        "editorial_gate_decision_id": f"{PREFIX}-approve",
        "plan_summary": "Narration-led fluid visual plan: five states.",
        "hook": "ONE ROOM, TWO COINS",
        "continuity_key": f"{PREFIX}-v1",
        "image_call_ceiling": 8,
        "rooms": {"home": {"environment_family": HOME_FAMILY, "viewpoint": "front"}},
        "states": [
            {
                "excerpt": EXCERPTS[0],
                "type": "new",
                "world": "w1",
                "hamster": True,
                "intent": "Hamster in the quiet room.",
            },
            {
                "excerpt": EXCERPTS[1],
                "type": "character-free",
                "world": "w2",
                "hamster": False,
                "intent": "The empty room.",
            },
            {
                "excerpt": EXCERPTS[2],
                "type": "progression",
                "world": "w2",
                "hamster": False,
                "intent": "Same frame plus a coin.",
            },
            {
                "excerpt": EXCERPTS[3],
                "type": "progression",
                "world": "w2",
                "hamster": False,
                "intent": "Same frame plus a second coin.",
            },
            {
                "excerpt": EXCERPTS[4],
                "type": "new",
                "world": "w3",
                "hamster": True,
                "intent": "Hamster beside the coins.",
            },
        ],
        "worlds": {
            "w1": {
                "room": "home",
                "kind": "character",
                "character_clause": "proportions",
                "text": "The hamster stands in the quiet room.",
            },
            "w2": {
                "room": "home",
                "kind": "character-free",
                "character_clause": None,
                "text": "The quiet room, empty floor in front. No character.",
            },
            "w3": {
                "room": "home",
                "kind": "character",
                "character_clause": None,
                "text": "The hamster looks at two coins.",
            },
        },
        "objects": {
            "coin_a": {
                "world": "w2",
                "state": 3,
                "size": "about one tenth",
                "text": "One plain coin, drawn with extra-heavy thick black outlines.",
            },
            "coin_b": {
                "world": "w2",
                "state": 4,
                "size": "about one tenth",
                "text": "One plain coin, drawn with extra-heavy thick black outlines.",
            },
        },
        "citations": [{"state": 2, "label": "Source, 2026", "source_id": f"{PREFIX}-source"}],
    }
    path.write_text(json.dumps(story, indent=1), encoding="utf-8")
    return path


def _runtime(tmp_path, monkeypatch):
    """A temporary runtime with the editorial chain, references and an approved room."""

    runtime = media_runtime_or_skip()
    stand_in = StandInGenerator(realistic_source_png(runtime, tmp_path), _object_canvas())
    server = _server(tmp_path, stand_in, runtime)
    repository = server.repository
    _request(server, tmp_path, f"{PREFIX}-setup")  # global authority and reference basis
    profile = "character-profile-similarstoic-hamster-core-v1"
    repository.create_character_reference_set(
        CANONICAL_REFERENCE_SET, profile, ["asset-http-reference-basis-v1"]
    )
    plan = create_authorized_visual_plan(server, PREFIX, SCRIPT)
    anchor_scene = repository.create_scene_under_visual_plan_authorization(
        f"{PREFIX}-anchor-scene", plan.id, 1, SCRIPT, "Room anchors."
    )
    _home_authority(server, anchor_scene.id, "v1", viewpoints=("front",))
    assert repository.get_visual_reference_authority(GLOBAL_AUTHORITY)
    server.server_close()
    (tmp_path / "media").mkdir(exist_ok=True)
    # The CLI builds its own servers: give them the stand-in image provider and local FFmpeg.
    monkeypatch.setenv("ATLAS_FFMPEG_PATH", runtime.ffmpeg_path)
    monkeypatch.setenv("ATLAS_FFPROBE_PATH", runtime.ffprobe_path)
    real_server = production_cli._server

    def server_with_stand_in(db, assets, media, generator=None):
        return real_server(db, assets, media, generator=generator or stand_in)

    monkeypatch.setattr(production_cli, "_server", server_with_stand_in)
    paths = [
        "--db",
        str(tmp_path / "lifecycle.db"),
        "--assets",
        str(tmp_path / "assets"),
        "--media",
        str(tmp_path / "media"),
    ]
    return stand_in, paths, runtime


def _cli(capsys, args: list[str]) -> tuple[int, dict]:
    code = production_cli.main(args)
    captured = capsys.readouterr()
    text = captured.out if code != 2 else captured.err
    return code, json.loads(text)


def _live(db: Path, backup_root: Path) -> list[str]:
    return ["--expect-db-sha256", database_sha256(db), "--backup-root", str(backup_root)]


def test_a_story_runs_end_to_end_through_every_founder_gate(
    tmp_path, monkeypatch, transcription, capsys  # noqa: F811
) -> None:
    generator, paths, runtime = _runtime(tmp_path, monkeypatch)
    db, backups = tmp_path / "lifecycle.db", tmp_path / "backups"
    story = _story(tmp_path / "story.json")
    run = f"{PREFIX}-run"

    code, checked = _cli(capsys, ["check-story", str(story)])
    assert code == 0 and checked["states"] == 5 and checked["image_specs"] == 5

    # A wrong expected hash refuses before anything happens.
    code, refused = _cli(
        capsys,
        ["plan", *paths, "--expect-db-sha256", "0" * 64, "--backup-root", str(backups), str(story)],
    )
    assert code == 2 and "nothing was changed" in refused["refused"]
    # Dry run: rehearsed only, the database is unchanged.
    before = database_sha256(db)
    code, rehearsed = _cli(
        capsys, ["plan", *paths, "--expect-db-sha256", before, "--dry-run", str(story)]
    )
    assert code == 0 and rehearsed["mode"] == "dry-run" and rehearsed["rehearsal"]["error"] is None
    assert database_sha256(db) == before

    code, planned = _cli(capsys, ["plan", *paths, *_live(db, backups), str(story)])
    assert code == 0 and planned["live"]["error"] is None, planned
    assert Path(planned["backup"]["backup"]).is_file() and planned["backup"]["content_identical"]

    # Start: the founder's first-step spend authorization; the provider key must be present.
    monkeypatch.setenv("OPENAI_API_KEY", "workflow-test-not-a-key")
    code, started = _cli(
        capsys,
        [
            "start",
            *paths,
            *_live(db, backups),
            "--max-image-calls",
            "5",
            "--stop-on-technical-rejection",
            "yes",
            "--authorized-by",
            "founder",
            "--reason",
            "test",
            str(story),
        ],
    )
    assert code == 0, started
    assert sorted(started["rehearsal"]["would_dispatch"]) == sorted(started["live"]["dispatched"])
    assert started["rehearsal"]["stand_in_image_calls"] == 5
    assert started["live"]["status"] == "acquisition_review_pending"
    assert generator.calls == ["character", "environment", "prop", "prop", "character"]

    # Preview proposed placements on a temporary copy; the live database never changes.
    placements = tmp_path / "placements.json"
    placements.write_text(
        json.dumps(
            {
                "w2/coin_a/coin_a": {"center": [400, 1500], "scale": 0.5},
                "w2/coin_b/coin_b": {"center": [700, 1500], "scale": 0.5},
            }
        ),
        encoding="utf-8",
    )
    before = database_sha256(db)
    code, previewed = _cli(
        capsys,
        [
            "preview",
            *paths,
            run,
            "--placements",
            str(placements),
            "--out",
            str(tmp_path / "preview"),
        ],
    )
    assert code == 0 and previewed["states"] == 5, previewed
    assert set(previewed["placements"]) == {"w2/coin_a/coin_a", "w2/coin_b/coin_b"}
    assert (tmp_path / "preview" / "contact-sheet-phone.png").is_file()
    assert database_sha256(db) == before

    # The founder's review (simulated here, in this isolated test database only).
    code, template = _cli(
        capsys, ["review-template", *paths, run, "--out", str(tmp_path / "template.json")]
    )
    assert code == 0 and template["pending_variants"] == 5
    reviews = json.loads((tmp_path / "template.json").read_text(encoding="utf-8"))
    centres = json.loads(placements.read_text(encoding="utf-8"))
    for review in reviews:
        review["outcome"] = "passed"
        evidence = review["evidence"]
        zoom = evidence["zoom_inspection"]
        evidence["zoom_inspection"] = {k: v or "passed" for k, v in zoom.items()}
        evidence["fixtures"] = {k: "unchanged" for k in evidence["fixtures"]}
        variant = "/".join((review["world_key"], review["entity_key"], review["variant_key"]))
        if "object_center" in evidence:
            evidence["object_center"] = centres[variant]["center"]
            evidence["object_scale"] = centres[variant]["scale"]
    (tmp_path / "reviews.json").write_text(json.dumps(reviews), encoding="utf-8")
    marked = {**reviews[0]["evidence"], "simulated_for_preview": True}
    simulated = [dict(reviews[0], evidence=marked)]
    (tmp_path / "simulated.json").write_text(json.dumps(simulated), encoding="utf-8")
    code, refused = _cli(
        capsys, ["review", *paths, *_live(db, backups), run, str(tmp_path / "simulated.json")]
    )
    assert code == 2 and "never be recorded" in refused["refused"]
    code, reviewed = _cli(
        capsys, ["review", *paths, *_live(db, backups), run, str(tmp_path / "reviews.json")]
    )
    assert code == 0, reviewed
    assert (reviewed["live"]["status"], reviewed["live"]["stage"]) == ("failed", "narration")
    assert reviewed["live"]["blocked_provider_calls"] == []

    # Narration: authorize, then resume the narration step with only its two keys.
    code, _ = _cli(
        capsys,
        [
            "authorize-narration",
            *paths,
            *_live(db, backups),
            run,
            "--authorized-by",
            "founder",
            "--scope",
            "Daniel v2, up to 3 takes",
        ],
    )
    assert code == 0
    wav = _sine_seconds(runtime, tmp_path, 6.0, "take.wav")
    calls: list[str] = []
    _take_sequence(monkeypatch, [wav], calls, SCRIPT)
    _scores(monkeypatch, [("passed", 400)])
    transcription.queue = [SCRIPT]
    monkeypatch.setenv("OPENAI_API_KEY", "workflow-test-not-a-key")
    monkeypatch.setenv("INWORLD_API_KEY", "workflow-test-not-a-key")
    code, resumed = _cli(
        capsys, ["resume", *paths, *_live(db, backups), run, "--step", "narration"]
    )
    assert code == 0, resumed
    # The rehearsal stopped at the narration provider; the live step made exactly one take.
    assert resumed["rehearsal"]["blocked_provider_calls"] == ["narration synthesis"]
    assert resumed["live"]["status"] == "qa_review_pending" and len(calls) == 1
    assert generator.calls == ["character", "environment", "prop", "prop", "character"]

    evidence_file = tmp_path / "qa.json"
    evidence_file.write_text(json.dumps({"reviewer": "founder"}), encoding="utf-8")
    code, qa = _cli(
        capsys,
        [
            "qa",
            *paths,
            *_live(db, backups),
            run,
            "--outcome",
            "passed",
            "--evidence-file",
            str(evidence_file),
        ],
    )
    assert code == 0 and qa["live"]["status"] == "private_founder_review_ready", qa
    code, accepted = _cli(
        capsys,
        [
            "founder-review",
            *paths,
            *_live(db, backups),
            run,
            "--outcome",
            "accepted",
            "--founder-actor",
            "founder",
            "--decision-reference",
            "test",
            "--notes",
            "test",
        ],
    )
    assert code == 0 and accepted["live"]["status"] == "founder_accepted", accepted

    code, status = _cli(capsys, ["status", *paths, run])
    assert code == 0 and status["latest_event"]["status"] == "founder_accepted"
    assert status["recipe"]["id"] == "similarstoic-flow-v1"
    assert status["image_calls"] == 5 and status["narration_authorized"] is True
    # Every live write took its own verified backup first.
    assert len(list(backups.iterdir())) == 7


def test_a_resume_whose_rehearsal_disagrees_with_the_founder_is_refused(
    tmp_path, monkeypatch, capsys
) -> None:
    generator, paths, _runtime_ = _runtime(tmp_path, monkeypatch)
    db, backups = tmp_path / "lifecycle.db", tmp_path / "backups"
    story = _story(tmp_path / "story.json")
    run = f"{PREFIX}-run"
    assert _cli(capsys, ["plan", *paths, *_live(db, backups), str(story)])[0] == 0
    monkeypatch.setenv("OPENAI_API_KEY", "workflow-test-not-a-key")
    code, started = _cli(
        capsys,
        [
            "start",
            *paths,
            *_live(db, backups),
            "--max-image-calls",
            "2",
            "--stop-on-technical-rejection",
            "yes",
            "--authorized-by",
            "founder",
            "--reason",
            "test",
            str(story),
        ],
    )
    assert code == 1 and "allows 2 image call" in started["live"]["error"]
    assert len(generator.calls) == 2
    # Without a new authorization the next step spends nothing, even in rehearsal.
    code, resumed = _cli(
        capsys,
        [
            "resume",
            *paths,
            "--expect-db-sha256",
            database_sha256(db),
            "--dry-run",
            run,
            "--step",
            "image",
        ],
    )
    assert code == 0 and "needs a founder spend authorization" in resumed["rehearsal"]["error"]
    code, _ = _cli(
        capsys,
        [
            "authorize-spend",
            *paths,
            *_live(db, backups),
            run,
            "--max-image-calls",
            "3",
            "--stop-on-technical-rejection",
            "yes",
            "--authorized-by",
            "founder",
            "--reason",
            "remaining variants",
        ],
    )
    assert code == 0
    before = database_sha256(db)
    code, refused = _cli(
        capsys,
        [
            "resume",
            *paths,
            *_live(db, backups),
            run,
            "--step",
            "image",
            "--expect-targets",
            "w1/base/base",
        ],
    )
    assert code == 2 and "not the expected" in refused["refused"]
    assert database_sha256(db) == before and len(generator.calls) == 2
    code, refused = _cli(
        capsys, ["resume", *paths, *_live(db, backups), run, "--step", "narration"]
    )
    assert code == 2 and "next step is 'image'" in refused["refused"]
