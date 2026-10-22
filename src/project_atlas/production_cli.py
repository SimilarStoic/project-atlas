"""Founder-gated operator commands for SimilarStoic productions.

    python -m project_atlas.production_cli <command> ...

Read-only commands (``status``, ``check-story``, ``review-template``, ``preview``) never write
the runtime: ``status`` opens the database with ``mode=ro`` and the others work on a temporary
copy. Every live command (``plan``, ``start``, ``authorize-spend``, ``resume``, ``review``,
``revise-spec``, ``authorize-narration``, ``qa``, ``founder-review``):

1. refuses unless the database SHA-256 equals ``--expect-db-sha256``;
2. rehearses the same operation on a temporary copy with every provider replaced or blocked,
   which validates preconditions, authorization and wiring only (never image or voice quality),
   and refuses if the rehearsal reports an error;
3. takes a verified backup into ``--backup-root`` (``production_backup.verified_backup``);
4. runs the operation through the unchanged ``ProductionLifecycleService`` with only the provider
   keys that step needs; every other provider entry point is blocked in-process.

``--dry-run`` stops after the rehearsal. Founder gates are unchanged: this tool records the
founder's decisions, it never makes them.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from project_atlas import production_recipe
from project_atlas.generation import GeneratedArtifact, GenerationService, OpenAIImageGenerator
from project_atlas.media import MediaService
from project_atlas.narration import InworldNarrationSynthesizer
from project_atlas.narration_verification import WhisperTranscriber
from project_atlas.plate_anchor import Raster, encode_png
from project_atlas.production import ProductionLifecycleError
from project_atlas.production_backup import database_sha256, verified_backup

PROVIDER_KEYS = ("OPENAI_API_KEY", "INWORLD_API_KEY", "LEONARDO_API_KEY")
STEP_KEYS = {"image": ("OPENAI_API_KEY",), "narration": ("INWORLD_API_KEY", "OPENAI_API_KEY")}
REHEARSAL_NOTE = (
    "Provider-free rehearsal on a temporary copy: it validates preconditions, authorization and "
    "wiring only. Stand-in images and voices say nothing about real provider outcomes or quality."
)
SIMULATED = "simulated_for_preview"


class CliError(RuntimeError):
    """A refused operation; the runtime was not changed."""


class ProviderBlocked(RuntimeError):
    """A provider entry point was reached where this command allows none."""

    def __init__(self, provider: str) -> None:
        super().__init__(f"{provider} is not authorized in this step; no call was made.")
        self.provider = provider


class _Blocked(list):
    """Blocked provider names (as reported), plus each ``ProviderBlocked`` actually raised."""

    def __init__(self) -> None:
        super().__init__()
        self.raised: list[ProviderBlocked] = []


class RehearsalImageGenerator:
    """Stand-in image provider for rehearsals: a plain 9:16 canvas, never a real result."""

    generator_key = "rehearsal-stand-in"
    max_reference_images = 16

    def __init__(self) -> None:
        self.calls = 0

    def supports(self, asset_type: str) -> bool:
        return True

    def generation_parameters(self) -> dict[str, Any]:
        return {"output_format": "png", "image_size": "1152x2048"}

    def generate(self, generation_input: Any) -> GeneratedArtifact:
        self.calls += 1
        content = encode_png(Raster(1152, 2048, 3, bytes((246, 244, 238)) * (1152 * 2048)))
        return GeneratedArtifact(content, "image/png", provider_key="rehearsal-stand-in")


# --- process guards --------------------------------------------------------------------------


def _keep_only_keys(keep: tuple[str, ...]) -> None:
    for name in list(os.environ):
        if (name in PROVIDER_KEYS or name.endswith("_API_KEY")) and name not in keep:
            del os.environ[name]
    missing = [name for name in keep if not os.environ.get(name)]
    if missing:
        raise CliError(f"This step needs {missing} in the environment; nothing was changed.")


PROVIDER_NAMES = {
    "image": "image generation",
    "narration": "narration synthesis",
    "transcription": "transcription",
}


@contextlib.contextmanager
def _providers(allowed: set[str]) -> Iterator[_Blocked]:
    """Block, at class level (so per-request services are covered), every provider not allowed."""

    reached = _Blocked()

    def blocker(name):
        def refuse(*_args, **_kwargs):
            reached.append(name)
            reached.raised.append(ProviderBlocked(name))
            raise reached.raised[-1]

        return refuse

    patches = []
    if "image" not in allowed:
        patches += [
            (GenerationService, "generate_asset_spec", blocker(PROVIDER_NAMES["image"])),
            (OpenAIImageGenerator, "generate", blocker(PROVIDER_NAMES["image"])),
        ]
    if "narration" not in allowed:
        patches += [
            (MediaService, "generate_brand_narration", blocker(PROVIDER_NAMES["narration"])),
            (InworldNarrationSynthesizer, "synthesize", blocker(PROVIDER_NAMES["narration"])),
        ]
    if "transcription" not in allowed:
        patches.append((WhisperTranscriber, "transcribe", blocker(PROVIDER_NAMES["transcription"])))
    saved = [(owner, name, owner.__dict__[name]) for owner, name, _ in patches]
    try:
        for owner, name, replacement in patches:
            setattr(owner, name, replacement)
        yield reached
    finally:
        for owner, name, original in saved:
            setattr(owner, name, original)


# --- paths, copies and servers ----------------------------------------------------------------


def _paths(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    db = Path(args.db or os.environ.get("ATLAS_DB_PATH", ""))
    assets = Path(args.assets or os.environ.get("ATLAS_ASSET_STORAGE_ROOT", ""))
    media = Path(args.media or os.environ.get("ATLAS_MEDIA_STORAGE_ROOT", ""))
    for label, path, is_file in (
        ("database", db, True),
        ("assets", assets, False),
        ("media", media, False),
    ):
        if not str(path) or not (path.is_file() if is_file else path.is_dir()):
            raise CliError(
                f"The {label} path {str(path) or '(unset)'} does not exist; dot-source "
                "scripts/set_conveyor_environment.ps1 or pass --db/--assets/--media."
            )
    return db, assets, media


def _copy_runtime(db: Path, assets: Path, media: Path, run_id: str | None, root: Path):
    """A temporary runtime copy: the database (backup API), shared assets, the run's media."""

    target_db = root / "conveyor.db"
    source = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    try:
        copy = sqlite3.connect(target_db)
        with copy:
            source.backup(copy)
        copy.close()
    finally:
        source.close()
    keep_derived = {"scene", run_id} if run_id else {"scene"}

    def ignore(directory: str, names: list[str]) -> set[str]:
        if Path(directory).resolve() == (assets / "persistent-derived").resolve():
            return {name for name in names if name not in keep_derived}
        return set()

    shutil.copytree(assets, root / "assets", ignore=ignore)
    (root / "media").mkdir()
    if run_id:
        for path in media.rglob("*"):
            if path.is_file() and run_id in path.name:
                destination = root / "media" / path.relative_to(media)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, destination)
    return target_db, root / "assets", root / "media"


def _server(db: Path, assets: Path, media: Path, generator: Any = None):
    from project_atlas.web import create_server

    kwargs = {
        "port": 0,
        "database_path": db,
        "asset_storage_root": assets,
        "media_storage_root": media,
    }
    if generator is not None:
        kwargs["generator"] = generator
    return create_server(**kwargs)


@contextlib.contextmanager
def _rehearsal(db: Path, assets: Path, media: Path, run_id: str | None):
    root = Path(tempfile.mkdtemp(prefix="conveyor-rehearsal-"))
    saved = {name: os.environ[name] for name in list(os.environ) if name.endswith("_API_KEY")}
    try:
        _keep_only_keys(())
        copy = _copy_runtime(db, assets, media, run_id, root)
        generator = RehearsalImageGenerator()
        server = _server(*copy, generator=generator)
        try:
            yield server, generator, copy[0]
        finally:
            server.server_close()
    finally:
        os.environ.update(saved)
        shutil.rmtree(root, ignore_errors=True)


# --- the live-write protocol ------------------------------------------------------------------


def _summary(server: Any, run_id: str | None) -> dict[str, Any]:
    if not run_id:
        return {}
    try:
        status = server.production_service.status(run_id)
    except KeyError:
        return {"run": None}
    return {
        "status": status["status"],
        "stage": status["stage"],
        "run_error": status["error"],
        "spend": status["spend"],
    }


def _dispatched(server: Any, run_id: str, before: int) -> list[str]:
    from project_atlas.production import ACQUISITION_DISPATCH

    items = server.repository.list_production_evidence(run_id, ACQUISITION_DISPATCH)
    return [
        "/".join((d.payload["world_key"], d.payload["entity_key"], d.payload["variant_key"]))
        for d in sorted(items, key=lambda d: int(d.id.rsplit(":", 1)[1]))[before:]
    ]


def _attempt(operation, server: Any) -> tuple[Any, str | None, Exception | None]:
    try:
        return operation(server), None, None
    except Exception as error:  # noqa: BLE001 - reported to the founder, never retried
        return None, f"{type(error).__name__}: {error}", error


def _live(
    args: argparse.Namespace,
    *,
    label: str,
    run_id: str | None,
    step: str | None,
    operation,
    check=None,
) -> dict[str, Any]:
    db, assets, media = _paths(args)
    actual = database_sha256(db)
    if actual != args.expect_db_sha256:
        raise CliError(
            f"Database SHA-256 is {actual}, not the expected {args.expect_db_sha256}; nothing "
            "was changed."
        )
    allowed = (
        {"image"}
        if step == "image"
        else ({"narration", "transcription"} if step == "narration" else set())
    )
    report: dict[str, Any] = {"command": label, "run": run_id, "db_sha256_before": actual}
    with _rehearsal(db, assets, media, run_id) as (server, generator, _copy):
        before = len(_dispatched(server, run_id, 0)) if run_id and _exists(server, run_id) else 0
        with _providers({"image"} if step == "image" else set()) as reached:
            result, error, raised = _attempt(operation, server)
        rehearsal = {
            "note": REHEARSAL_NOTE,
            "error": error,
            "blocked_provider_calls": reached,
            "stand_in_image_calls": generator.calls,
            **_summary(server, run_id),
        }
        if run_id and _exists(server, run_id):
            rehearsal["would_dispatch"] = _dispatched(server, run_id, before)
        if check is not None:
            check(rehearsal, result)
    report["rehearsal"] = rehearsal
    if args.dry_run:
        report["mode"] = "dry-run"
        return report
    if not _rehearsed_cleanly(raised, reached, allowed):
        # Fail closed: a step that did not rehearse cleanly never reaches the backup, the live
        # database or a provider.
        raise CliError(
            f"The rehearsal failed ({rehearsal['error']}); nothing was backed up, written or "
            "sent to a provider."
        )
    report["backup"] = verified_backup(db, Path(args.backup_root), _backup_label(label, run_id))
    if database_sha256(db) != actual:
        raise CliError("The database changed during the backup; nothing was written.")
    _keep_only_keys(STEP_KEYS.get(step, ()))
    server = _server(db, assets, media)
    try:
        with _providers(allowed) as reached:
            result, error, _raised = _attempt(operation, server)
        report["live"] = {
            "error": error,
            "blocked_provider_calls": reached,
            **_summary(server, run_id),
        }
        if run_id and _exists(server, run_id):
            report["live"]["dispatched"] = _dispatched(server, run_id, before)
    finally:
        server.server_close()
    report["mode"] = "live"
    report["db_sha256_after"] = database_sha256(db)
    return report


def _rehearsed_cleanly(raised: Exception | None, reached: _Blocked, allowed: set[str]) -> bool:
    """No error and no blocked call, or the only stop was this step's own provider.

    Narration is never synthesized in a rehearsal, so a narration step's rehearsal ends at the
    narration provider once every precondition has passed. That stop is recognised by the
    exception object itself, never by its message: exactly one provider was blocked, it is one
    this step allows, and the rehearsal ended with that very ``ProviderBlocked``, either bare or
    as the direct cause of the lifecycle's own recorded failure (``ProductionLifecycleError``).
    A swallowed block, a second block, any other exception or wrapping fails closed.
    """

    if raised is None:
        return not reached
    if len(reached.raised) != 1:
        return False
    block = reached.raised[0]
    if block.provider not in {PROVIDER_NAMES[key] for key in allowed}:
        return False
    return raised is block or (
        type(raised) is ProductionLifecycleError and raised.__cause__ is block
    )


def _exists(server: Any, run_id: str) -> bool:
    try:
        server.repository.get_production_run(run_id)
    except KeyError:
        return False
    return True


def _backup_label(label: str, run_id: str | None) -> str:
    return "-".join(part for part in ("pre", label, run_id) if part).lower()[:90]


# --- commands ---------------------------------------------------------------------------------


def _spend_terms(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "authorized_by": args.authorized_by,
        "max_image_calls": args.max_image_calls,
        "stop_on_technical_rejection": args.stop_on_technical_rejection == "yes",
        "reason": args.reason,
    }


def _compiled(story_path: Path) -> production_recipe.CompiledStory:
    story, story_sha = production_recipe.load_story(story_path)
    return production_recipe.compile_story(story, story_sha)


def cmd_check_story(args: argparse.Namespace) -> dict[str, Any]:
    compiled = _compiled(Path(args.story))
    return {
        "run_id": compiled.request["id"],
        "states": len(compiled.scenes),
        "worlds": len(compiled.request["worlds"]),
        "image_specs": len(compiled.specs),
        "story_sha256": compiled.request["recipe"]["story_sha256"],
        "findings": [vars(item) for item in compiled.findings],
    }


def cmd_plan(args: argparse.Namespace) -> dict[str, Any]:
    compiled = _compiled(Path(args.story))

    def operation(server):
        service = server.production_service
        request = production_recipe.write_plan(server.repository, compiled)
        # Everything start() checks before any provider call, without creating the run.
        defaulted = service._apply_new_run_defaults(request)
        service._validate_request(defaulted, pins_pending=True)
        defaulted["environment_pins"] = service._latest_environment_pins(defaulted)
        service._require_eligible_references(service._validate_request(defaulted))
        return request

    report = _live(args, label="plan", run_id=None, step=None, operation=operation)
    report["findings"] = [vars(item) for item in compiled.findings]
    return report


def cmd_start(args: argparse.Namespace) -> dict[str, Any]:
    compiled = _compiled(Path(args.story))
    request = json.loads(json.dumps(compiled.request))
    run_id = request["id"]

    def operation(server):
        plan = server.repository.get_visual_plan(request["visual_plan_id"])
        if plan.metadata.get("story_sha256") != request["recipe"]["story_sha256"]:
            raise CliError("The story file differs from the one this plan was written from.")
        return server.production_service.start(
            request | {"spend_authorization": _spend_terms(args)}
        )

    return _live(args, label="start", run_id=run_id, step="image", operation=operation)


def cmd_authorize_spend(args: argparse.Namespace) -> dict[str, Any]:
    return _live(
        args,
        label="authorize-spend",
        run_id=args.run,
        step=None,
        operation=lambda s: s.production_service.authorize_spend(args.run, _spend_terms(args)),
    )


def _resume_step(server: Any, run_id: str) -> str:
    latest = server.repository.latest_production_run_event(run_id)
    if latest is None or latest.status != "failed":
        return "none"
    return "image" if latest.stage in {"acquisition", "acquisition_review"} else "narration"


def cmd_resume(args: argparse.Namespace) -> dict[str, Any]:
    db, _assets, _media = _paths(args)
    with _readonly_server(db) as server:
        detected = _resume_step(server, args.run)
    if detected != args.step:
        raise CliError(f"The run's next step is {detected!r}, not {args.step!r}; nothing changed.")
    expected = sorted(args.expect_targets.split(",")) if args.expect_targets else None

    def check(rehearsal, _result):
        if expected is not None and sorted(rehearsal.get("would_dispatch", [])) != expected:
            raise CliError(
                f"Rehearsal would dispatch {rehearsal.get('would_dispatch')}, not the expected "
                f"{expected}; nothing was changed."
            )

    return _live(
        args,
        label="resume",
        run_id=args.run,
        step=args.step,
        check=check,
        operation=lambda s: s.production_service.resume(args.run),
    )


def cmd_review(args: argparse.Namespace) -> dict[str, Any]:
    reviews = json.loads(Path(args.reviews).read_text(encoding="utf-8"))
    if any(SIMULATED in json.dumps(review) for review in reviews):
        raise CliError("Simulated preview reviews can never be recorded as founder reviews.")

    def operation(server):
        run = server.repository.get_production_run(args.run)
        if server.production_service._narration_authorized(run):
            raise CliError(
                "Narration is already authorized, so a completing review would start narration; "
                "record acquisition reviews before authorizing narration."
            )
        try:
            return server.production_service.review_acquisition(args.run, reviews)
        except ProductionLifecycleError as error:
            # The expected stop: every variant passed and assembly reached the narration gate.
            if "Narration is not authorized" not in str(error):
                raise
            return server.production_service.status(args.run)

    return _live(args, label="review", run_id=args.run, step=None, operation=operation)


def cmd_revise_spec(args: argparse.Namespace) -> dict[str, Any]:
    evidence = {
        "asset_spec_id": args.spec,
        "generation_prompt": Path(args.prompt_file).read_text(encoding="utf-8").strip(),
        "authorized_by": args.authorized_by,
        "reason": args.reason,
    }
    return _live(
        args,
        label="revise-spec",
        run_id=args.run,
        step=None,
        operation=lambda s: s.production_service.revise_asset_spec(args.run, evidence),
    )


def cmd_authorize_narration(args: argparse.Namespace) -> dict[str, Any]:
    evidence = {"authorized_by": args.authorized_by, "scope": args.scope}
    return _live(
        args,
        label="authorize-narration",
        run_id=args.run,
        step=None,
        operation=lambda s: s.production_service.authorize_narration(args.run, evidence),
    )


def cmd_qa(args: argparse.Namespace) -> dict[str, Any]:
    evidence = json.loads(Path(args.evidence_file).read_text(encoding="utf-8"))
    payload = {"outcome": args.outcome, "evidence": evidence}
    return _live(
        args,
        label="qa",
        run_id=args.run,
        step=None,
        operation=lambda s: s.production_service.record_qa(args.run, payload),
    )


def cmd_founder_review(args: argparse.Namespace) -> dict[str, Any]:
    payload = {
        "outcome": args.outcome,
        "founder_actor": args.founder_actor,
        "decision_reference": args.decision_reference,
        "notes": args.notes,
    }
    return _live(
        args,
        label="founder-review",
        run_id=args.run,
        step=None,
        operation=lambda s: s.production_service.founder_review(args.run, payload),
    )


@contextlib.contextmanager
def _readonly_server(db: Path):
    """Application code against a temporary copy of the database only (never the live file)."""

    root = Path(tempfile.mkdtemp(prefix="conveyor-readonly-"))
    try:
        copy = root / "conveyor.db"
        source = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
        try:
            target = sqlite3.connect(copy)
            with target:
                source.backup(target)
            target.close()
        finally:
            source.close()
        (root / "assets").mkdir()
        (root / "media").mkdir()
        server = _server(copy, root / "assets", root / "media", generator=RehearsalImageGenerator())
        try:
            yield server
        finally:
            server.server_close()
    finally:
        shutil.rmtree(root, ignore_errors=True)


def cmd_status(args: argparse.Namespace) -> dict[str, Any]:
    """Read-only: the run's position and spend straight from the database (mode=ro)."""

    db, _assets, _media = _paths(args)
    connection = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        run = connection.execute("SELECT * FROM production_runs WHERE id=?", (args.run,)).fetchone()
        if run is None:
            raise CliError(f"Production run {args.run} does not exist.")
        request = json.loads(run["request_json"])
        latest = connection.execute(
            "SELECT status, stage, error_code, error_message, created_at FROM "
            "production_run_events WHERE production_run_id=? ORDER BY sequence DESC LIMIT 1",
            (args.run,),
        ).fetchone()
        evidence = connection.execute(
            "SELECT evidence_type, generation_execution_id, payload_json FROM "
            "production_run_evidence WHERE production_run_id=?",
            (args.run,),
        ).fetchall()
        reviews = connection.execute(
            "SELECT scope, outcome, COUNT(*) AS n FROM production_qa_reviews WHERE "
            "production_run_id=? GROUP BY scope, outcome",
            (args.run,),
        ).fetchall()
    finally:
        connection.close()
    counts: dict[str, int] = {}
    for item in evidence:
        counts[item["evidence_type"]] = counts.get(item["evidence_type"], 0) + 1
    legacy = sum(
        1
        for item in evidence
        if item["evidence_type"] == "acquisition"
        and item["generation_execution_id"]
        and "dispatch_id" not in json.loads(item["payload_json"])
    )
    return {
        "run": args.run,
        "db_sha256": database_sha256(db),
        "latest_event": dict(latest) if latest else None,
        "recipe": request.get("recipe"),
        "image_calls": counts.get("acquisition_dispatch", 0) + legacy,
        "image_call_ceiling": request["forecast"]["image_calls"],
        "narration_authorized": request.get("narration_authorized") is True
        or counts.get("narration_authorization", 0) > 0,
        "evidence_counts": counts,
        "reviews": [dict(row) for row in reviews],
    }


def cmd_review_template(args: argparse.Namespace) -> dict[str, Any]:
    """Read-only: the exact review skeleton the run requires; the founder fills every blank."""

    from project_atlas.production import OBJECT_CENTER_AT_REVIEW

    db, _assets, _media = _paths(args)
    with _readonly_server(db) as server:
        service = server.production_service
        run = server.repository.get_production_run(args.run)
        at_review = {
            (world["key"], entity["key"], variant["key"])
            for world in run.request["worlds"]
            for entity in world["entities"]
            for variant in entity["variants"]
            if variant.get("object_center") == OBJECT_CENTER_AT_REVIEW
        }
        template = []
        for key, state in sorted(service._variant_review_states(run).items()):
            if state != "pending":
                continue
            required = service.acquisition_review_requirements(run, key)
            evidence: dict[str, Any] = {
                "zoom_inspection": {"asset_sha256": required["asset_sha256"]}
                | {check: "" for check in required["zoom_checks"]},
                "fixtures": {fixture: "" for fixture in required["fixture_keys"]},
                "geometry_compared_with": required["geometry_compared_with"],
                "notes": "",
            }
            if key in at_review:
                evidence |= {"object_center": None, "object_scale": None}
            template.append(
                {
                    "world_key": key[0],
                    "entity_key": key[1],
                    "variant_key": key[2],
                    "outcome": "",
                    "evidence": evidence,
                }
            )
    if args.out:
        Path(args.out).write_text(json.dumps(template, indent=1) + "\n", encoding="utf-8")
    return {"run": args.run, "pending_variants": len(template), "template": args.out or template}


def cmd_preview(args: argparse.Namespace) -> dict[str, Any]:
    """Zero-spend preview on a temporary copy: proposed object placements rendered through the
    real admission and world-building path, phone-size frames, a contact sheet and, optionally,
    a stand-in-voice video. Simulated placement reviews exist only in the temporary copy."""

    from project_atlas.scene_media import load_persistent_scene_frame

    db, assets, media = _paths(args)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    placements = (
        json.loads(Path(args.placements).read_text(encoding="utf-8")) if args.placements else {}
    )
    with _rehearsal(db, assets, media, args.run) as (server, _generator, copy_db):
        if copy_db.resolve() == db.resolve():
            raise CliError("Preview refuses to write simulated reviews to the live database.")
        service, repository = server.production_service, server.repository
        run = repository.get_production_run(args.run)
        active = service._acquisition_map(args.run)
        review_states = service._variant_review_states(run)
        for variant, proposal in placements.items():
            key = tuple(variant.split("/"))
            if key not in active:
                raise CliError(f"{variant} has no acquired asset to place.")
            if review_states.get(key) == "passed":
                raise CliError(f"{variant} already has its founder-approved placement.")
            repository.create_production_qa_review(
                f"{args.run}:preview:{variant}",
                args.run,
                "acquisition",
                "passed",
                "human",
                {"profile": SIMULATED},
                {
                    SIMULATED: True,
                    "asset_id": active[key]["asset_id"],
                    "variant": list(key),
                    "object_center": proposal["center"],
                    "object_scale": proposal.get("scale", 1.0),
                },
            )
        with _providers(set()):
            states = service._ensure_scene_states(run)
        runtime = service.media_service.runtime
        frames = []
        for index, scene_id in enumerate(service._plan_scene_ids(run.visual_plan_id), 1):
            frame = load_persistent_scene_frame(repository, states[scene_id])
            full = out / f"state-{index:02d}.png"
            full.write_bytes(frame.png)
            phone = out / f"state-{index:02d}-phone.png"
            subprocess.run(
                [
                    runtime.ffmpeg_path,
                    "-v",
                    "error",
                    "-y",
                    "-i",
                    str(full),
                    "-vf",
                    "scale=360:640:flags=area",
                    str(phone),
                ],
                check=True,
            )
            frames.append(phone)
        _contact_sheet(runtime.ffmpeg_path, frames, out / "contact-sheet-phone.png")
        admissions = {
            item.payload["world_key"]: item.payload.get("object_admissions", [])
            for item in repository.list_production_evidence(args.run, "world")
        }
        report = {
            "note": "Zero-spend preview on a temporary copy; placements are proposals for the "
            "founder's acquisition review, never approvals.",
            "states": len(frames),
            "placements": {
                record["variant"]: {
                    name: record[name]
                    for name in (
                        "object_center",
                        "size_px",
                        "placed_at",
                        "outline_px",
                        "base_outline_px",
                    )
                }
                | {"object_scale": record.get("object_scale", {}).get("scale", 1.0)}
                for records in admissions.values()
                for record in records
            },
        }
        if args.video:
            report["video"] = _standin_video(server, run, states, out)
    (out / "preview-report.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    return report


def _contact_sheet(ffmpeg: str, frames: list[Path], target: Path, columns: int = 5) -> None:
    """One image of all frames, ``columns`` per row, in state order."""

    inputs: list[str] = []
    for frame in frames:
        inputs += ["-i", str(frame)]
    rows = -(-len(frames) // columns)
    graph = (
        "".join(f"[{index}:v]" for index in range(len(frames)))
        + f"concat=n={len(frames)}:v=1:a=0,tile={columns}x{rows}:color=white"
    )
    subprocess.run(
        [
            ffmpeg,
            "-v",
            "error",
            "-y",
            *inputs,
            "-filter_complex",
            graph,
            "-frames:v",
            "1",
            str(target),
        ],
        check=True,
    )


def _standin_video(server: Any, run: Any, states: dict[str, str], out: Path) -> dict[str, Any]:
    """Local System.Speech stand-in voice (never Daniel), narration-aligned cuts and overlays."""

    from project_atlas import speech_timing
    from project_atlas.media import LocalSystemSpeechSynthesizer

    repository, media = server.repository, server.media_service
    plan = repository.get_visual_plan(run.visual_plan_id)
    script = repository.get_script(plan.script_id)
    scenes = [
        repository.get_scene(scene_id)
        for scene_id in server.production_service._plan_scene_ids(plan.id)
    ]
    synthesis = LocalSystemSpeechSynthesizer().synthesize(script.narration_text)
    narration = media.import_narration(
        f"{run.id}-standin-preview", script.id, synthesis.content, "audio/wav"
    )
    timing = media.narration_speech_timing(narration, script.narration_text)
    durations = speech_timing.recommend_scene_durations(
        timing, [scene.narration_excerpt for scene in scenes]
    )["durations_ms"]
    inputs = [
        {
            "scene_id": scene.id,
            "resolved_state_id": states[scene.id],
            "duration_ms": duration,
            "motion": "static",
            "transition_to_next": "crossfade" if index < len(scenes) - 1 else None,
        }
        for index, (scene, duration) in enumerate(zip(scenes, durations, strict=True))
    ]
    snapshot = media.create_persistent_scene_snapshot(
        f"{run.id}:standin-preview-snapshot",
        plan.id,
        narration.id,
        inputs,
        run.request.get("citations"),
        on_screen_text=run.request.get("on_screen_text_overlay") is True,
    )
    artifact = media.render(
        f"{run.id}-standin-preview-render", f"{run.id}-standin-preview", snapshot.id
    )
    target = out / "standin-preview.mp4"
    shutil.copyfile(media.storage.path(artifact.storage_path), target)
    return {
        "path": str(target),
        "note": "Stand-in local voice, not Daniel: structure and " "approximate pacing only.",
        "durations_ms": durations,
        "states_under_1500_ms": [i + 1 for i, d in enumerate(durations) if d < 1500],
    }


# --- argument parsing -------------------------------------------------------------------------


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m project_atlas.production_cli", description=__doc__.split("\n\n")[0]
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def paths(p):
        p.add_argument("--db")
        p.add_argument("--assets")
        p.add_argument("--media")

    def live(p):
        paths(p)
        p.add_argument("--expect-db-sha256", required=True)
        mode = p.add_mutually_exclusive_group(required=True)
        mode.add_argument("--dry-run", action="store_true", help="rehearse only")
        mode.add_argument("--backup-root", help="verified backup destination (live)")

    def spend(p):
        p.add_argument("--max-image-calls", type=int, required=True)
        p.add_argument("--stop-on-technical-rejection", choices=["yes", "no"], required=True)
        p.add_argument("--authorized-by", required=True)
        p.add_argument("--reason", required=True)

    p = sub.add_parser("status", help="read-only run position and spend")
    paths(p)
    p.add_argument("run")
    p = sub.add_parser("check-story", help="compile a story file and list drafting findings")
    p.add_argument("story")
    p = sub.add_parser("review-template", help="read-only acquisition review skeleton")
    paths(p)
    p.add_argument("run")
    p.add_argument("--out")
    p = sub.add_parser("preview", help="zero-spend placement and stand-in preview")
    paths(p)
    p.add_argument("run")
    p.add_argument("--placements")
    p.add_argument("--out", required=True)
    p.add_argument("--video", action="store_true")
    p = sub.add_parser("plan", help="write plan, scenes and specs from a story file")
    live(p)
    p.add_argument("story")
    p = sub.add_parser("start", help="start the run with the first step's spend authorization")
    live(p)
    spend(p)
    p.add_argument("story")
    p = sub.add_parser("authorize-spend", help="record the next acquisition step's authorization")
    live(p)
    spend(p)
    p.add_argument("run")
    p = sub.add_parser("resume", help="resume the run's next step")
    live(p)
    p.add_argument("run")
    p.add_argument("--step", choices=["image", "narration"], required=True)
    p.add_argument("--expect-targets", help="comma-separated world/entity/variant keys")
    p = sub.add_parser("review", help="record the founder's acquisition reviews")
    live(p)
    p.add_argument("run")
    p.add_argument("reviews")
    p = sub.add_parser("revise-spec", help="revise a missing or rejected variant's prompt")
    live(p)
    p.add_argument("run")
    p.add_argument("spec")
    p.add_argument("--prompt-file", required=True)
    p.add_argument("--authorized-by", required=True)
    p.add_argument("--reason", required=True)
    p = sub.add_parser("authorize-narration", help="record the founder's narration authorization")
    live(p)
    p.add_argument("run")
    p.add_argument("--authorized-by", required=True)
    p.add_argument("--scope", required=True)
    p = sub.add_parser("qa", help="record the founder's whole-video QA")
    live(p)
    p.add_argument("run")
    p.add_argument("--outcome", choices=["passed", "failed"], required=True)
    p.add_argument("--evidence-file", required=True)
    p = sub.add_parser("founder-review", help="record the founder's acceptance or rejection")
    live(p)
    p.add_argument("run")
    p.add_argument("--outcome", choices=["accepted", "rejected"], required=True)
    p.add_argument("--founder-actor", required=True)
    p.add_argument("--decision-reference", required=True)
    p.add_argument("--notes", required=True)
    return parser


COMMANDS = {
    "status": cmd_status,
    "check-story": cmd_check_story,
    "review-template": cmd_review_template,
    "preview": cmd_preview,
    "plan": cmd_plan,
    "start": cmd_start,
    "authorize-spend": cmd_authorize_spend,
    "resume": cmd_resume,
    "review": cmd_review,
    "revise-spec": cmd_revise_spec,
    "authorize-narration": cmd_authorize_narration,
    "qa": cmd_qa,
    "founder-review": cmd_founder_review,
}


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command not in {"start", "resume"}:
        # Commands without a provider step run with no provider key in the process at all.
        _keep_only_keys(())
    try:
        report = COMMANDS[args.command](args)
    except (CliError, production_recipe.StoryError) as error:
        print(json.dumps({"refused": str(error)}, indent=1), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=1, default=str, ensure_ascii=False))
    live = report.get("live") if isinstance(report, dict) else None
    return 1 if live and live.get("error") else 0


if __name__ == "__main__":
    sys.exit(main())
