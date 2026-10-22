"""A failed rehearsal never reaches the backup, the live database or a provider (P12-F08).

Every live operator command runs through ``production_cli._live``; these tests drive that shared
boundary with each command's label and provider step, then two commands end to end.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import sqlite3

import pytest

from project_atlas import production_cli
from project_atlas.narration import InworldNarrationSynthesizer
from project_atlas.persistence import AtlasRepository
from project_atlas.production import ProductionLifecycleError
from project_atlas.production_backup import database_sha256
from tests.test_production_workflow import _cli, _live, _runtime, _story

pytestmark = pytest.mark.spend_gate

# (label, step) exactly as each live command passes them to ``_live``.
LIVE_COMMANDS = [
    ("plan", None),
    ("start", "image"),
    ("authorize-spend", None),
    ("resume", "image"),
    ("resume", "narration"),
    ("review", None),
    ("revise-spec", None),
    ("authorize-narration", None),
    ("qa", None),
    ("founder-review", None),
]


def _args(tmp_path) -> argparse.Namespace:
    db = tmp_path / "runtime.db"
    (tmp_path / "assets").mkdir()
    (tmp_path / "media").mkdir()
    AtlasRepository(db, tmp_path / "assets").close()
    return argparse.Namespace(
        db=str(db),
        assets=str(tmp_path / "assets"),
        media=str(tmp_path / "media"),
        expect_db_sha256=database_sha256(db),
        dry_run=False,
        backup_root=str(tmp_path / "backups"),
    )


def test_every_live_command_is_covered() -> None:
    labels = {label for label, _step in LIVE_COMMANDS}
    read_only = {"status", "check-story", "review-template", "preview"}
    assert labels == set(production_cli.COMMANDS) - read_only


@pytest.mark.parametrize(("label", "step"), LIVE_COMMANDS)
def test_a_failed_rehearsal_blocks_every_live_command(tmp_path, label, step) -> None:
    args = _args(tmp_path)
    before = database_sha256(args.db)
    servers = []

    def operation(server):
        servers.append(server)
        raise RuntimeError("precondition not met")

    with pytest.raises(production_cli.CliError) as refused:
        production_cli._live(args, label=label, run_id=None, step=step, operation=operation)
    message = str(refused.value)
    assert "precondition not met" in message
    assert "nothing was backed up, written or sent to a provider" in message
    assert len(servers) == 1  # the rehearsal only; the live operation never ran
    assert not (tmp_path / "backups").exists()
    assert database_sha256(args.db) == before


def test_a_dry_run_still_reports_a_failed_rehearsal_without_refusing(tmp_path) -> None:
    args = _args(tmp_path)
    args.dry_run = True

    def operation(_server):
        raise RuntimeError("precondition not met")

    report = production_cli._live(args, label="plan", run_id=None, step=None, operation=operation)
    assert report["mode"] == "dry-run" and "precondition not met" in report["rehearsal"]["error"]
    assert not (tmp_path / "backups").exists()


def test_a_narration_rehearsal_that_stops_at_its_own_provider_proceeds(
    tmp_path, monkeypatch
) -> None:
    args = _args(tmp_path)
    monkeypatch.setenv("INWORLD_API_KEY", "gate-test-not-a-key")
    monkeypatch.setenv("OPENAI_API_KEY", "gate-test-not-a-key")
    takes = []
    monkeypatch.setattr(
        InworldNarrationSynthesizer, "synthesize", lambda *_a, **_k: takes.append("take")
    )

    def operation(_server):
        InworldNarrationSynthesizer.synthesize(None)
        return "narrated"

    report = production_cli._live(
        args, label="resume", run_id=None, step="narration", operation=operation
    )
    assert report["rehearsal"]["blocked_provider_calls"] == ["narration synthesis"]
    assert report["rehearsal"]["error"] is not None
    assert report["live"]["error"] is None and takes == ["take"]
    assert report["backup"]["content_identical"]


@pytest.mark.parametrize(
    ("step", "reach_provider", "fail_before", "fail_after"),
    [
        ("narration", True, False, False),  # sanity: covered above, must proceed
        ("narration", False, True, False),  # a narration step failing before its provider
        ("narration", True, False, True),  # a different failure after reaching the provider
        ("image", True, False, False),  # an image step reaching the narration provider
        (None, True, False, False),  # a provider-free step reaching any provider
    ],
)
def test_only_the_steps_own_provider_boundary_counts_as_a_clean_rehearsal(
    tmp_path, monkeypatch, step, reach_provider, fail_before, fail_after
) -> None:
    args = _args(tmp_path)
    for key in ("INWORLD_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.setenv(key, "gate-test-not-a-key")
    monkeypatch.setattr(InworldNarrationSynthesizer, "synthesize", lambda *_a, **_k: None)

    def operation(_server):
        if fail_before:
            raise RuntimeError("precondition not met")
        if reach_provider:
            try:
                InworldNarrationSynthesizer.synthesize(None)
            except production_cli.ProviderBlocked:
                if not fail_after:
                    raise
        if fail_after:
            raise RuntimeError("a later check failed")
        return "done"

    if step == "narration" and not (fail_before or fail_after):
        report = production_cli._live(
            args, label="resume", run_id=None, step=step, operation=operation
        )
        assert report["live"]["error"] is None
        return
    with pytest.raises(production_cli.CliError, match="rehearsal failed"):
        production_cli._live(args, label="resume", run_id=None, step=step, operation=operation)
    assert not (tmp_path / "backups").exists()


def _stub_narration(monkeypatch) -> list[str]:
    for key in ("INWORLD_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.setenv(key, "gate-test-not-a-key")
    takes: list[str] = []
    monkeypatch.setattr(
        InworldNarrationSynthesizer, "synthesize", lambda *_a, **_k: takes.append("take")
    )
    return takes


def _refused(args, step, operation) -> None:
    with pytest.raises(production_cli.CliError, match="rehearsal failed"):
        production_cli._live(args, label="resume", run_id=None, step=step, operation=operation)


def test_an_unrelated_error_quoting_the_block_text_is_refused(tmp_path, monkeypatch) -> None:
    args = _args(tmp_path)
    takes = _stub_narration(monkeypatch)

    def operation(_server):
        with contextlib.suppress(production_cli.ProviderBlocked):
            InworldNarrationSynthesizer.synthesize(None)
        raise RuntimeError("later check failed; narration synthesis is not authorized in this step")

    _refused(args, "narration", operation)
    assert takes == [] and not (tmp_path / "backups").exists()


@pytest.mark.parametrize("step", ["narration", "image", None])
def test_a_swallowed_provider_block_is_refused(tmp_path, monkeypatch, step) -> None:
    args = _args(tmp_path)
    takes = _stub_narration(monkeypatch)

    def operation(_server):
        with contextlib.suppress(production_cli.ProviderBlocked):
            InworldNarrationSynthesizer.synthesize(None)  # swallowed: no error reported
        return "done"

    _refused(args, step, operation)
    assert takes == [] and not (tmp_path / "backups").exists()


def test_the_lifecycles_own_record_of_the_narration_block_proceeds(tmp_path, monkeypatch) -> None:
    args = _args(tmp_path)
    takes = _stub_narration(monkeypatch)

    def operation(_server):
        try:
            InworldNarrationSynthesizer.synthesize(None)
        except production_cli.ProviderBlocked as error:
            # What ProductionLifecycleService._fail does with a provider failure.
            raise ProductionLifecycleError("run", "narration", str(error)) from error
        return "narrated"

    report = production_cli._live(
        args, label="resume", run_id=None, step="narration", operation=operation
    )
    assert report["rehearsal"]["blocked_provider_calls"] == ["narration synthesis"]
    assert report["live"]["error"] is None and takes == ["take"]


@pytest.mark.parametrize("wrapper", [RuntimeError, ValueError])
def test_any_other_wrapping_of_the_block_is_refused(tmp_path, monkeypatch, wrapper) -> None:
    args = _args(tmp_path)
    takes = _stub_narration(monkeypatch)

    def operation(_server):
        try:
            InworldNarrationSynthesizer.synthesize(None)
        except production_cli.ProviderBlocked as error:
            raise wrapper(str(error)) from error

    _refused(args, "narration", operation)
    assert takes == []


def test_a_lifecycle_error_not_caused_by_the_block_is_refused(tmp_path, monkeypatch) -> None:
    args = _args(tmp_path)
    takes = _stub_narration(monkeypatch)

    def operation(_server):
        try:
            InworldNarrationSynthesizer.synthesize(None)
        except production_cli.ProviderBlocked as error:
            message = str(error)
        raise ProductionLifecycleError("run", "narration", message)  # no causal link

    _refused(args, "narration", operation)
    assert takes == []


def test_a_second_block_after_a_swallowed_one_is_refused(tmp_path, monkeypatch) -> None:
    args = _args(tmp_path)
    takes = _stub_narration(monkeypatch)

    def operation(_server):
        with contextlib.suppress(production_cli.ProviderBlocked):
            InworldNarrationSynthesizer.synthesize(None)
        InworldNarrationSynthesizer.synthesize(None)

    _refused(args, "narration", operation)
    assert takes == []


def test_plan_with_an_unapproved_room_writes_nothing(tmp_path, monkeypatch, capsys) -> None:
    _generator, paths, _runtime_ = _runtime(tmp_path, monkeypatch)
    db, backups = tmp_path / "lifecycle.db", tmp_path / "backups"
    story_path = _story(tmp_path / "story.json")
    story = json.loads(story_path.read_text(encoding="utf-8"))
    story["rooms"]["home"]["environment_family"] = "no-such-approved-room"
    story_path.write_text(json.dumps(story), encoding="utf-8")
    before = database_sha256(db)
    code, refused = _cli(capsys, ["plan", *paths, *_live(db, backups), str(story_path)])
    assert code == 2 and "unknown environment family" in refused["refused"]
    assert database_sha256(db) == before and not backups.exists()
    with sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True) as connection:
        plans = connection.execute(
            "SELECT COUNT(*) FROM visual_plans WHERE id = ?", (story["visual_plan_id"],)
        ).fetchone()[0]
        scenes = connection.execute(
            "SELECT COUNT(*) FROM scenes WHERE visual_plan_id = ?", (story["visual_plan_id"],)
        ).fetchone()[0]
    assert (plans, scenes) == (0, 0)  # no partial plan (the P12-F08 symptom)


def test_a_spend_authorization_for_an_unknown_run_writes_nothing(
    tmp_path, monkeypatch, capsys
) -> None:
    _generator, paths, _runtime_ = _runtime(tmp_path, monkeypatch)
    db, backups = tmp_path / "lifecycle.db", tmp_path / "backups"
    before = database_sha256(db)
    code, refused = _cli(
        capsys,
        [
            "authorize-spend",
            *paths,
            *_live(db, backups),
            "no-such-run",
            "--max-image-calls",
            "3",
            "--stop-on-technical-rejection",
            "yes",
            "--authorized-by",
            "founder",
            "--reason",
            "test",
        ],
    )
    assert code == 2 and "rehearsal failed" in refused["refused"]
    assert database_sha256(db) == before and not backups.exists()
