"""Real local-media lifecycle coverage for the bounded v0.26 renderer."""

from __future__ import annotations

import base64
import json
import shutil
import sqlite3
import subprocess
from hashlib import sha256
from pathlib import Path

import pytest

from project_atlas.generation import LocalAssetStorage
from project_atlas.media import (
    FfmpegRuntime,
    LocalMediaStorage,
    LocalSystemSpeechSynthesizer,
    MediaRuntimeError,
    MediaService,
    NarrationSynthesis,
    OpenAINarrationSynthesizer,
)
from project_atlas.persistence import AtlasRepository

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _runtime_or_skip() -> FfmpegRuntime:
    """Use a provisioned local runtime when available; media proof requires no network."""

    root = Path(__file__).parents[1]
    tool_bin = next(root.glob(".tools/ffmpeg-*/bin"), None)
    ffmpeg = tool_bin / "ffmpeg.exe" if tool_bin else None
    ffprobe = tool_bin / "ffprobe.exe" if tool_bin else None
    if ffmpeg and ffprobe and ffmpeg.is_file() and ffprobe.is_file():
        return FfmpegRuntime(str(ffmpeg), str(ffprobe))
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return FfmpegRuntime()
    pytest.skip("real FFmpeg/FFprobe runtime is unavailable")


def test_local_system_speech_uses_profileless_interactive_host(monkeypatch) -> None:
    """Windows System.Speech voices remain unavailable to PowerShell's non-interactive host."""

    observed: list[str] = []

    def fake_run(command, **_kwargs):
        observed.extend(command)
        output = Path(command[command.index("-OutputPath") + 1])
        output.write_bytes(b"fixture wav bytes")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("project_atlas.media.subprocess.run", fake_run)
    engine = LocalSystemSpeechSynthesizer(powershell_path="powershell.exe")
    synthesis = engine.synthesize("Exact local fixture text.")

    assert engine.voice_identity == "Microsoft Hazel Desktop"
    assert "-NoProfile" in observed
    assert "-NonInteractive" not in observed
    assert synthesis.content == b"fixture wav bytes"


def test_openai_narration_uses_only_exact_script_and_truthful_settings(monkeypatch) -> None:
    """The OpenAI adapter sends only its explicit TTS payload and records its true settings."""

    observed: dict[str, object] = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return b"fixture neural wav"

    def fake_urlopen(request, timeout):
        observed["url"] = request.full_url
        observed["headers"] = dict(request.header_items())
        observed["payload"] = json.loads(request.data)
        observed["timeout"] = timeout
        return Response()

    monkeypatch.setattr("project_atlas.media.urllib.request.urlopen", fake_urlopen)
    engine = OpenAINarrationSynthesizer(api_key="test-key")
    script = "Exact approved narration script."

    synthesis = engine.synthesize(script)

    assert observed["url"] == "https://api.openai.com/v1/audio/speech"
    assert observed["payload"] == {
        "model": "gpt-4o-mini-tts",
        "voice": "marin",
        "input": script,
        "instructions": engine.instructions,
        "response_format": "wav",
        "speed": 1.0,
    }
    assert "mascot" not in json.dumps(observed["payload"]).lower()
    assert synthesis.content == b"fixture neural wav"
    assert synthesis.engine_kind == "openai_tts"
    assert synthesis.settings == engine.settings


def test_caption_cues_are_short_phrase_level_segments() -> None:
    """Refinement captions turn over quickly without rewriting the supplied script."""

    text = "one two three four five six seven eight nine ten eleven twelve"
    cues = MediaService.caption_cues(text, 1200)

    assert [cue["text"] for cue in cues] == [
        "one two three four five",
        "six seven eight nine ten",
        "eleven twelve",
    ]
    assert all(len(cue["text"].split()) <= 5 for cue in cues)
    assert cues[0]["start_ms"] == 0
    assert cues[-1]["end_ms"] == 1200


def test_default_social_caption_profile_is_mobile_readable_and_safe() -> None:
    settings = MediaService.RENDER_SETTINGS
    profile = settings["caption_profile"]

    assert settings["caption_style"] == "similarstoic-social-mobile-v3"
    assert profile["font_size"] >= 88
    assert profile["max_lines"] == 2
    assert profile["margin_bottom"] >= 300
    assert min(profile["margin_left"], profile["margin_right"]) >= 60
    assert round(profile["font_size"] * profile["phone_preview_width"] / 1080) >= 23
    assert profile["default_zone"] == "lower_center_safe"
    assert profile["alternate_zones"] == ["middle_center_safe", "upper_center_safe"]
    assert profile["position_change_policy"] == "scene_boundary_only_when_action_requires"
    assert settings["default_motion"] == "static"
    assert settings["global_motion_policy"] == "static_anchored_default"
    assert settings["final_frame_visual_qa"] == {
        "profile": "similarstoic-final-frame-v4",
        "inspection_scales": ["full_resolution", "normal_video", "phone"],
        "repair_policy": "repair_dont_empty",
        "structural_geometry_integrity": True,
        "facial_expression_integrity": True,
        "residual_facial_lines_rejected": True,
        "occlusion_layer_integrity": True,
        "reuse_with_variation": True,
        "exact_frame_repeat_requires_editorial_rationale": True,
    }


def test_modern_render_rejects_a_weakened_final_frame_visual_qa_profile() -> None:
    scenes = [{"duration_ms": 1000, "motion": "static", "transition_to_next": None}]
    settings = dict(MediaService.RENDER_SETTINGS)
    settings["final_frame_visual_qa"] = {
        **MediaService.FINAL_FRAME_VISUAL_QA_PROFILE,
        "structural_geometry_integrity": False,
    }

    with pytest.raises(MediaRuntimeError, match="final-frame visual QA profile"):
        MediaService._composition_filters(scenes, 1000, settings)


def test_social_caption_filter_freezes_profile_and_preserves_legacy_snapshots() -> None:
    scenes = [{"duration_ms": 1000, "motion": "static", "transition_to_next": None}]
    modern = MediaService._composition_filters(scenes, 1000)
    assert "FontSize=13.8" in modern[-1]
    assert "MarginV=48" in modern[-1]
    assert "OutlineColour=&H08FFFDF8" in modern[-1]
    assert "BorderStyle=3" in modern[-1]

    legacy_settings = dict(MediaService.RENDER_SETTINGS)
    legacy_settings["caption_style"] = "similarstoic-readable-v1"
    legacy_settings.pop("caption_profile")
    legacy = MediaService._composition_filters(scenes, 1000, legacy_settings)
    assert "FontSize=6.3" in legacy[-1]
    assert "MarginV=19.5" in legacy[-1]

    v2_settings = dict(MediaService.RENDER_SETTINGS)
    v2_settings["profile"] = "similarstoic-vertical-v1"
    v2_settings["caption_style"] = "similarstoic-social-mobile-v2"
    v2_settings["caption_profile"] = MediaService.SOCIAL_CAPTION_PROFILE_V2
    v2_settings.pop("global_motion_policy")
    v2 = MediaService._composition_filters(scenes, 1000, v2_settings)
    assert "FontSize=10.2" in v2[-1]
    assert "MarginV=37.5" in v2[-1]


@pytest.mark.parametrize(
    "caption_style", ["similarstoic-social-mobile-v3", "similarstoic-readable-v1"]
)
def test_caption_filter_changes_rendered_pixels_during_active_cue(
    tmp_path: Path, caption_style: str
) -> None:
    """A successful command is insufficient: active captions must alter output pixels."""

    runtime = _runtime_or_skip()
    settings = dict(MediaService.RENDER_SETTINGS)
    settings["caption_style"] = caption_style
    if caption_style == "similarstoic-readable-v1":
        settings.pop("caption_profile")
    scenes = [{"duration_ms": 1000, "motion": "static", "transition_to_next": None}]
    (tmp_path / "captions.srt").write_text(
        MediaService._srt([{"text": "Caption pixel proof", "start_ms": 0, "end_ms": 1000}]),
        encoding="utf-8",
    )
    output = tmp_path / "captioned.rgb"
    runtime._run(
        [
            runtime.ffmpeg_path,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=white:s=1080x1920:r=30:d=1",
            "-filter_complex",
            ";".join(MediaService._composition_filters(scenes, 1000, settings)),
            "-map",
            "[captioned]",
            "-frames:v",
            "1",
            "-pix_fmt",
            "rgb24",
            "-f",
            "rawvideo",
            str(output),
        ],
        cwd=tmp_path,
    )
    pixels = output.read_bytes()
    assert len(pixels) == 1080 * 1920 * 3
    dark_by_row = [
        sum(
            1
            for offset in range(row * 1080 * 3, (row + 1) * 1080 * 3, 3)
            if max(pixels[offset : offset + 3]) < 80
        )
        for row in range(1920)
    ]
    assert sum(dark_by_row[1200:1900]) > 1_000
    assert sum(dark_by_row[:1000]) == 0


def _ready_visual_plan(repository: AtlasRepository, prefix: str):
    """Build the accepted Gate lineage required by final-media input snapshots."""

    opportunity_id = f"{prefix}-opportunity"
    repository.create_opportunity(
        opportunity_id, "Opportunity", "Summary", "Why now", 1, "proposed"
    )
    pack = repository.create_research_pack(f"{prefix}-pack", opportunity_id, 1, "Research")
    claim = repository.create_claim(
        f"{prefix}-claim", pack.id, "Frozen claim.", "fact", "low", "stable", "reviewed", ""
    )
    source = repository.create_source(
        f"{prefix}-source",
        "primary",
        "Source",
        "Publisher",
        f"https://example.test/{prefix}",
        "2026-08-20T00:00:00+00:00",
    )
    repository.link_claim_evidence(claim.id, source.id, "supports", "p. 1")
    research_ready = repository.create_research_readiness_assessment(
        f"{prefix}-research-ready",
        pack.id,
        "Ready",
        {"summary": "Ready."},
        "policy-v1",
        "test",
        "media-test",
        "v1",
    )
    angle = repository.create_editorial_angle_under_research_readiness(
        f"{prefix}-angle",
        opportunity_id,
        pack.id,
        research_ready.id,
        "Angle",
        "Thesis",
        "Promise",
        "Frame",
        ["Takeaway"],
    )
    repository.link_claim_to_editorial_angle(angle.id, claim.id, "core")
    piece = repository.create_content_piece_under_editorial_angle_readiness(
        f"{prefix}-piece", opportunity_id, angle.id, "video", "Working title"
    )
    script = repository.create_script_under_content_piece_readiness(
        f"{prefix}-script", piece.id, "First caption. Second caption."
    )
    repository.create_script_claim_set(f"{prefix}-claim-set", script.id, [claim.id])
    title = repository.create_title_option_under_content_piece_readiness(
        f"{prefix}-title", piece.id, "Title"
    )
    hook = repository.create_hook_option_under_content_piece_readiness(
        f"{prefix}-hook", piece.id, "Hook"
    )
    package = repository.create_editorial_package_snapshot(
        f"{prefix}-package", piece.id, title.id, hook.id, script.id
    )
    editorial_ready = repository.create_editorial_readiness_assessment(
        f"{prefix}-editorial-ready", package.id
    )
    decision = repository.create_editorial_gate_decision(
        f"{prefix}-approve", package.id, editorial_ready.id, "Approve", "founder"
    )
    return (
        repository.create_visual_plan_under_editorial_gate(
            f"{prefix}-plan", decision.id, "A brief visual direction"
        ),
        script,
    )


def _create_snapshot(
    service: MediaService,
    repository: AtlasRepository,
    tmp_path: Path,
    prefix: str,
    motions: tuple[str, ...] = ("static", "slow_zoom_in"),
    transitions: tuple[str | None, ...] = ("crossfade", None),
    duration_ms: int = 1000,
    generated_narration: bool = False,
):
    """Freeze selected imported visuals and narration of exactly their intended timeline."""

    plan, script = _ready_visual_plan(repository, prefix)
    asset_storage = LocalAssetStorage(tmp_path / "assets")
    scene_inputs = []
    for sequence, (motion, transition) in enumerate(zip(motions, transitions, strict=True), 1):
        scene = repository.create_scene_under_visual_plan_authorization(
            f"{prefix}-scene-{sequence}", plan.id, sequence, f"Locator {sequence}", "Intent"
        )
        spec = repository.create_asset_spec_under_scene_authorization(
            f"{prefix}-spec-{sequence}", scene.id, "graphic", "Support", "Visual", "Draw visual"
        )
        asset = repository.import_asset_under_asset_spec_authorization(
            f"{prefix}-asset-{sequence}", spec.id, PNG, "image/png", asset_storage
        )
        selection = repository.create_asset_selection(
            f"{prefix}-selection-{sequence}", spec.id, asset.id
        )
        scene_inputs.append(
            {
                "scene_id": scene.id,
                "asset_selection_id": selection.id,
                "duration_ms": duration_ms,
                "motion": motion,
                "motion_rationale": (
                    "Test-only deliberate emphasis move." if motion != "static" else None
                ),
                "transition_to_next": transition,
            }
        )
    audio_path = tmp_path / f"{prefix}.wav"
    audio_duration = len(motions) * duration_ms / 1000
    service.runtime._run(
        [
            service.runtime.ffmpeg_path,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=440:sample_rate=48000:duration={audio_duration:.3f}",
            "-c:a",
            "pcm_s16le",
            str(audio_path),
        ]
    )
    if generated_narration:

        class FixtureLocalSynthesizer:
            engine_kind = "local_system_speech"
            engine_identity = "System.Speech.Synthesis.SpeechSynthesizer"
            voice_identity = "Microsoft Hazel"
            locale = "en-GB"
            rate = 0
            volume = 100

            def synthesize(self, text: str) -> NarrationSynthesis:
                assert text == script.narration_text
                return NarrationSynthesis(
                    audio_path.read_bytes(),
                    "audio/wav",
                    self.engine_kind,
                    self.engine_identity,
                    self.voice_identity,
                    self.locale,
                    {"rate": self.rate, "volume": self.volume, "output_format": "wav"},
                )

        result = service.generate_local_narration(
            f"{prefix}-narration-execution",
            f"{prefix}-narration",
            script.id,
            FixtureLocalSynthesizer(),
        )
        assert result.narration_asset is not None
        narration = result.narration_asset
    else:
        narration = service.import_narration(
            f"{prefix}-narration", script.id, audio_path.read_bytes(), "audio/wav"
        )
    return service.create_snapshot(f"{prefix}-snapshot", plan.id, narration.id, scene_inputs)


def test_real_final_media_lifecycle_preserves_frozen_lineage_and_bytes(tmp_path) -> None:
    """A real two-Scene crossfade produces a registered, retrieved, exact H.264/AAC MP4."""

    runtime = _runtime_or_skip()
    repository = AtlasRepository(tmp_path / "atlas.db", asset_storage_root=tmp_path / "assets")
    try:
        service = MediaService(repository, runtime, LocalMediaStorage(tmp_path / "media"))
        snapshot = _create_snapshot(service, repository, tmp_path, "real")

        artifact = service.render("real-execution", "real-artifact", snapshot.id)
        execution = repository.get_render_execution("real-execution")
        retrieved = service.artifact_content(artifact.id)
        probe = runtime.probe(service.storage.path(artifact.storage_path))

        assert execution.outcome == "succeeded"
        assert execution.execution_metadata["caption_burned"] is True
        assert artifact.render_execution_id == execution.id
        assert artifact.media_type == "video/mp4"
        assert (artifact.width, artifact.height) == (1080, 1920)
        assert (probe.width, probe.height, probe.video_codec, probe.audio_codec) == (
            1080,
            1920,
            "h264",
            "aac",
        )
        assert probe.frame_rate == "30/1"
        assert artifact.duration_ms == 2000
        assert artifact.technical_validation["caption_burned"] is True
        assert artifact.technical_validation["duration_delta_ms"] == 0
        assert sha256(retrieved).hexdigest() == artifact.content_digest
        assert retrieved == service.storage.path(artifact.storage_path).read_bytes()
        assert len(repository.list_render_executions_for_snapshot(snapshot.id)) == 1
        with pytest.raises(sqlite3.IntegrityError):
            repository.create_final_media_artifact(
                "duplicate-artifact",
                execution.id,
                artifact.storage_path,
                artifact.content_digest,
                artifact.duration_ms,
                artifact.width,
                artifact.height,
                artifact.technical_validation,
            )
    finally:
        repository.close()


def test_final_media_lifecycle_accepts_generated_narration(tmp_path) -> None:
    """A generated narration take remains a valid frozen input to the v0.26 renderer."""

    runtime = _runtime_or_skip()
    repository = AtlasRepository(tmp_path / "atlas.db", asset_storage_root=tmp_path / "assets")
    try:
        service = MediaService(repository, runtime, LocalMediaStorage(tmp_path / "media"))
        snapshot = _create_snapshot(
            service, repository, tmp_path, "generated", generated_narration=True
        )
        artifact = service.render("generated-execution", "generated-artifact", snapshot.id)

        narration = repository.get_narration_asset(snapshot.narration_asset_id)
        assert narration.source_kind == "generated"
        assert repository.get_render_execution("generated-execution").outcome == "succeeded"
        assert artifact.media_type == "video/mp4"
    finally:
        repository.close()


def test_real_scene_chain_handles_cut_crossfade_and_slow_zoom_out(tmp_path) -> None:
    """A bounded mixed chain retains its caller-visible 1.5-second timeline exactly."""

    runtime = _runtime_or_skip()
    repository = AtlasRepository(tmp_path / "atlas.db", asset_storage_root=tmp_path / "assets")
    try:
        service = MediaService(repository, runtime, LocalMediaStorage(tmp_path / "media"))
        snapshot = _create_snapshot(
            service,
            repository,
            tmp_path,
            "mixed",
            ("static", "slow_zoom_in", "slow_zoom_out"),
            ("cut", "crossfade", None),
            500,
        )
        artifact = service.render("mixed-execution", "mixed-artifact", snapshot.id)

        assert artifact.duration_ms == 1500
        assert artifact.technical_validation["duration_delta_ms"] == 0
        assert repository.get_render_execution("mixed-execution").outcome == "succeeded"
    finally:
        repository.close()


def test_render_failure_is_retained_without_artifact_and_can_retry(tmp_path) -> None:
    """A corrupted frozen input creates one failed attempt, no MP4, then permits a retry."""

    runtime = _runtime_or_skip()
    repository = AtlasRepository(tmp_path / "atlas.db", asset_storage_root=tmp_path / "assets")
    try:
        service = MediaService(repository, runtime, LocalMediaStorage(tmp_path / "media"))
        snapshot = _create_snapshot(service, repository, tmp_path, "failure")
        narration = repository.get_narration_asset(snapshot.narration_asset_id)
        service.storage.path(narration.storage_path).write_bytes(b"corrupt")

        with pytest.raises(MediaRuntimeError, match="registered digest"):
            service.render("failed-execution", "failed-artifact", snapshot.id)

        failed = repository.get_render_execution("failed-execution")
        assert failed.outcome == "failed"
        assert failed.error_code == "MediaRuntimeError"
        with pytest.raises(KeyError):
            repository.get_final_media_artifact("failed-artifact")
        assert repository.get_final_media_input_snapshot(snapshot.id) == snapshot

        restored = (tmp_path / "failure.wav").read_bytes()
        service.storage.path(narration.storage_path).write_bytes(restored)
        artifact = service.render("retry-execution", "retry-artifact", snapshot.id)
        assert artifact.render_execution_id == "retry-execution"
        assert [
            item.outcome for item in repository.list_render_executions_for_snapshot(snapshot.id)
        ] == ["failed", "succeeded"]
    finally:
        repository.close()


def test_composition_filters_cover_cut_crossfade_and_all_frozen_motions() -> None:
    """The bounded scene-chain builder keeps caller timing on intended Scene durations."""

    scenes = [
        {"duration_ms": 500, "motion": "static", "transition_to_next": "cut"},
        {
            "duration_ms": 500,
            "motion": "slow_zoom_in",
            "motion_rationale": "Deliberate reveal.",
            "transition_to_next": "crossfade",
        },
        {
            "duration_ms": 500,
            "motion": "slow_zoom_out",
            "motion_rationale": "Deliberate context reveal.",
            "transition_to_next": None,
        },
    ]
    filters = MediaService._composition_filters(scenes, 1500)

    assert "concat=n=2" in ";".join(filters)
    assert "xfade=transition=fade:duration=0.250:offset=1.000" in ";".join(filters)
    assert "zoompan" in ";".join(filters)
    assert "trim=duration=1.500" in ";".join(filters)
