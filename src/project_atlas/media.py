"""Bounded local FFmpeg/FFprobe support for v0.26 final media."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Protocol

from project_atlas import speech_timing
from project_atlas.persistence import (
    AtlasRepository,
    FinalMediaInputSnapshot,
    NarrationAsset,
    NarrationGenerationExecution,
)
from project_atlas.scene_media import (
    SNAPSHOT_SCHEMA_VERSION,
    compositor_contract,
    load_persistent_scene_frame,
    unwritten_alpha_pixels,
)
from project_atlas.scene_model import canonical_json, digest


class MediaRuntimeError(RuntimeError):
    """Raised when the configured local media runtime cannot meet the fixed profile."""


class NarrationSynthesisError(MediaRuntimeError):
    """Raised when the configured local narration engine cannot create a usable take."""


def _utc_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _configured_executable(environment_name: str, fallback: str) -> str:
    configured = os.environ.get(environment_name, "").strip()
    if configured:
        path = Path(configured)
        if path.is_file():
            return str(path)
        raise MediaRuntimeError(f"{environment_name} does not name an executable file.")
    resolved = shutil.which(fallback)
    if resolved is None:
        raise MediaRuntimeError(f"{fallback} is unavailable; configure {environment_name} or PATH.")
    return resolved


@dataclass(frozen=True)
class MediaProbe:
    media_type: str
    duration_ms: int
    width: int | None
    height: int | None
    video_codec: str | None
    audio_codec: str | None
    frame_rate: str | None
    raw: dict


class FfmpegRuntime:
    """Resolve and use one explicit local FFmpeg/FFprobe pair without shell invocation."""

    def __init__(self, ffmpeg_path: str | None = None, ffprobe_path: str | None = None) -> None:
        self.ffmpeg_path = ffmpeg_path or _configured_executable("ATLAS_FFMPEG_PATH", "ffmpeg")
        self.ffprobe_path = ffprobe_path or _configured_executable("ATLAS_FFPROBE_PATH", "ffprobe")

    @staticmethod
    def _run(
        arguments: list[str], timeout: float = 30, cwd: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                arguments, capture_output=True, text=True, timeout=timeout, check=True, cwd=cwd
            )
        except subprocess.CalledProcessError as error:
            detail = (error.stderr or error.stdout or "media command failed").strip()
            raise MediaRuntimeError(
                f"Media command failed ({error.returncode}): {detail[-2000:]}"
            ) from error
        except (OSError, subprocess.SubprocessError) as error:
            raise MediaRuntimeError(str(error)) from error

    def version(self, executable: str) -> str:
        return self._run([executable, "-version"]).stdout.splitlines()[0]

    def assert_capabilities(self) -> dict[str, str]:
        encoders = self._run([self.ffmpeg_path, "-hide_banner", "-encoders"]).stdout
        filters = self._run([self.ffmpeg_path, "-hide_banner", "-filters"]).stdout
        for capability, output in (
            ("libx264", encoders),
            ("aac", encoders),
            ("zoompan", filters),
            ("xfade", filters),
            ("subtitles", filters),
        ):
            if capability not in output:
                raise MediaRuntimeError(
                    f"Configured FFmpeg lacks required {capability} capability."
                )
        return {
            "renderer_version": self.version(self.ffmpeg_path),
            "probe_version": self.version(self.ffprobe_path),
        }

    def probe(self, path: Path) -> MediaProbe:
        result = self._run(
            [
                self.ffprobe_path,
                "-v",
                "error",
                "-show_format",
                "-show_streams",
                "-of",
                "json",
                str(path),
            ]
        )
        payload = json.loads(result.stdout)
        streams = payload.get("streams", [])
        video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
        audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
        duration = float(payload.get("format", {}).get("duration") or 0)
        if duration <= 0:
            raise MediaRuntimeError("FFprobe did not report a positive media duration.")
        if not audio:
            raise MediaRuntimeError("Media must contain an audio stream.")
        return MediaProbe(
            "video/mp4" if video else "audio",
            round(duration * 1000),
            video.get("width") if video else None,
            video.get("height") if video else None,
            video.get("codec_name") if video else None,
            audio.get("codec_name"),
            video.get("avg_frame_rate") if video else None,
            payload,
        )

    def assert_audible(self, path: Path) -> None:
        """Reject a technically valid but silent audio file using FFmpeg's local detector."""

        result = self._run(
            [
                self.ffmpeg_path,
                "-hide_banner",
                "-i",
                str(path),
                "-af",
                "volumedetect",
                "-f",
                "null",
                "-",
            ]
        )
        detected = re.search(r"max_volume:\s+(-?inf|[-0-9.]+) dB", result.stderr)
        if detected is None or detected.group(1) == "-inf":
            raise NarrationSynthesisError("Narration audio is silent or could not be measured.")
        if float(detected.group(1)) <= -70:
            raise NarrationSynthesisError("Narration audio is too quiet for production use.")

    SILENCE_DETECTION = {"filter": "silencedetect", "noise_db": -35, "min_duration_s": 0.12}

    def detect_silences(self, path: Path) -> list[tuple[float, float]]:
        """Return (start_ms, end_ms) narration pauses using FFmpeg's local silence detector."""

        settings = self.SILENCE_DETECTION
        result = self._run(
            [
                self.ffmpeg_path,
                "-hide_banner",
                "-i",
                str(path),
                "-af",
                f"silencedetect=noise={settings['noise_db']}dB:d={settings['min_duration_s']}",
                "-f",
                "null",
                "-",
            ]
        )
        silences, start = [], None
        for kind, value in re.findall(r"silence_(start|end):\s*(-?[0-9.]+)", result.stderr):
            if kind == "start":
                start = max(0.0, float(value) * 1000)
            elif start is not None:
                silences.append((start, float(value) * 1000))
                start = None
        if start is not None:
            silences.append((start, self.probe(path).duration_ms))
        return silences


class LocalMediaStorage:
    """Store new narration and MP4 files under a traversal-safe configured root."""

    _EXTENSIONS = {
        "audio/wav": ".wav",
        "audio/mpeg": ".mp3",
        "audio/mp4": ".m4a",
        "video/mp4": ".mp4",
    }

    def __init__(self, root: Path | str | None = None) -> None:
        self.root = Path(root or os.environ.get("ATLAS_MEDIA_STORAGE_ROOT", "data/media")).resolve()

    def write(
        self, category: str, identifier: str, content: bytes, media_type: str
    ) -> tuple[str, str]:
        extension = self._EXTENSIONS.get(media_type)
        if extension is None or not content or Path(identifier).name != identifier:
            raise MediaRuntimeError("Unsupported media content or unsafe media identifier.")
        target = (self.root / category / f"{identifier}{extension}").resolve()
        if self.root not in target.parents or target.exists():
            raise MediaRuntimeError("Managed media path is unsafe or already exists.")
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        try:
            os.replace(temporary_path, target)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise
        return target.relative_to(self.root).as_posix(), sha256(content).hexdigest()

    def path(self, storage_path: str) -> Path:
        path = (self.root / storage_path).resolve()
        if self.root not in path.parents:
            raise MediaRuntimeError("Managed media path escaped its storage root.")
        return path

    def remove(self, storage_path: str) -> None:
        self.path(storage_path).unlink(missing_ok=True)

    def read_verified(self, storage_path: str, expected_digest: str) -> bytes:
        """Read one managed file only after checking its registered byte identity."""

        content = self.path(storage_path).read_bytes()
        if sha256(content).hexdigest() != expected_digest:
            raise MediaRuntimeError("Managed media bytes do not match their registered digest.")
        return content


@dataclass(frozen=True)
class NarrationSynthesis:
    """One local synthesis payload plus the exact stable engine configuration used."""

    content: bytes
    media_type: str
    engine_kind: str
    engine_identity: str
    voice_identity: str
    locale: str
    settings: dict[str, Any]


@dataclass(frozen=True)
class NarrationGenerationResult:
    """One terminal generated-narration attempt and its optional successful take."""

    execution: NarrationGenerationExecution
    narration_asset: NarrationAsset | None


class LocalSystemSpeechSynthesizer:
    """Use the already-installed Windows System.Speech engine without network access."""

    engine_kind = "local_system_speech"
    engine_identity = "System.Speech.Synthesis.SpeechSynthesizer"

    def __init__(
        self,
        voice_identity: str = "Microsoft Hazel Desktop",
        locale: str = "en-GB",
        rate: int = 0,
        volume: int = 100,
        powershell_path: str | None = None,
    ) -> None:
        self.voice_identity = voice_identity
        self.locale = locale
        self.rate = rate
        self.volume = volume
        self.powershell_path = powershell_path or shutil.which("powershell")

    def synthesize(self, text: str) -> NarrationSynthesis:
        """Produce one WAV from exact local text using a fixed installed voice."""

        if not self.powershell_path:
            raise NarrationSynthesisError(
                "Windows PowerShell is unavailable for local narration synthesis."
            )
        if not isinstance(text, str) or not text.strip():
            raise NarrationSynthesisError(
                "Narration synthesis requires non-empty exact Script text."
            )
        if not -10 <= self.rate <= 10 or not 0 <= self.volume <= 100:
            raise NarrationSynthesisError("System.Speech rate or volume is out of range.")
        with tempfile.TemporaryDirectory(prefix="atlas-narration-") as temporary:
            root = Path(temporary)
            text_path = root / "script.txt"
            output_path = root / "narration.wav"
            command_path = root / "synthesize.ps1"
            text_path.write_text(text, encoding="utf-8")
            command_path.write_text(
                """param(
  [string]$TextPath,
  [string]$OutputPath,
  [string]$Voice,
  [int]$Rate,
  [int]$Volume
)
Add-Type -AssemblyName System.Speech
$synthesizer = [System.Speech.Synthesis.SpeechSynthesizer]::new()
try {
  $voiceNames = $synthesizer.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name }
  if (-not ($voiceNames | Where-Object { $_ -eq $Voice })) {
    throw "Requested local voice is not installed: $Voice"
  }
  $synthesizer.SelectVoice($Voice)
  $synthesizer.Rate = $Rate
  $synthesizer.Volume = $Volume
  $synthesizer.SetOutputToWaveFile($OutputPath)
  $synthesizer.Speak([System.IO.File]::ReadAllText($TextPath, [System.Text.Encoding]::UTF8))
}
finally {
  $synthesizer.Dispose()
}
""",
                encoding="utf-8",
            )
            try:
                subprocess.run(
                    [
                        self.powershell_path,
                        "-NoLogo",
                        "-NoProfile",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(command_path),
                        "-TextPath",
                        str(text_path),
                        "-OutputPath",
                        str(output_path),
                        "-Voice",
                        self.voice_identity,
                        "-Rate",
                        str(self.rate),
                        "-Volume",
                        str(self.volume),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
            except (OSError, subprocess.SubprocessError) as error:
                raise NarrationSynthesisError(
                    f"Local System.Speech synthesis failed: {error}"
                ) from error
            if not output_path.is_file() or not output_path.stat().st_size:
                raise NarrationSynthesisError(
                    "Local System.Speech did not create WAV narration bytes."
                )
            content = output_path.read_bytes()
        return NarrationSynthesis(
            content,
            "audio/wav",
            self.engine_kind,
            self.engine_identity,
            self.voice_identity,
            self.locale,
            {
                "rate": self.rate,
                "volume": self.volume,
                "output_format": "wav",
                "text_transport": "local_utf8_file",
            },
        )


class NarrationSynthesizer(Protocol):
    engine_kind: str
    engine_identity: str
    voice_identity: str
    locale: str

    def synthesize(self, text: str) -> NarrationSynthesis: ...


class OpenAINarrationSynthesizer:
    """Generate one WAV through OpenAI's authorized speech endpoint."""

    engine_kind = "openai_tts"
    engine_identity = "OpenAI:gpt-4o-mini-tts"
    voice_identity = "marin"
    locale = "en-GB"
    instructions = (
        "Warm, calm, conversational, natural and intelligent. Lightly personable short-form "
        "pacing with restrained emphasis; no robotic cadence, announcer voice, dramatic pauses, "
        "or motivational-speaker delivery."
    )

    @property
    def settings(self) -> dict[str, Any]:
        return {
            "provider": "OpenAI",
            "model": "gpt-4o-mini-tts",
            "voice": "marin",
            "instructions": self.instructions,
            "response_format": "wav",
            "speed": 1.0,
        }

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")

    def synthesize(self, text: str) -> NarrationSynthesis:
        if not self.api_key:
            raise NarrationSynthesisError(
                "OPENAI_API_KEY is required for authorized neural narration."
            )
        payload = json.dumps(
            {
                "model": "gpt-4o-mini-tts",
                "voice": "marin",
                "input": text,
                "instructions": self.instructions,
                "response_format": "wav",
                "speed": 1.0,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            "https://api.openai.com/v1/audio/speech",
            payload,
            {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                content = response.read()
        except (OSError, urllib.error.URLError) as error:
            raise NarrationSynthesisError(f"OpenAI speech synthesis failed: {error}") from error
        if not content:
            raise NarrationSynthesisError("OpenAI speech synthesis returned no audio bytes.")
        return NarrationSynthesis(
            content,
            "audio/wav",
            self.engine_kind,
            self.engine_identity,
            self.voice_identity,
            self.locale,
            self.settings,
        )


class MediaService:
    """Small v0.26 lifecycle service; all public inputs are opaque IDs or content bytes."""

    SOCIAL_CAPTION_PROFILE_V2 = {
        "font_name": "Arial",
        "font_size": 68,
        "bold": True,
        "max_lines": 2,
        "margin_left": 72,
        "margin_right": 72,
        "margin_bottom": 250,
        "primary_colour": "&H001D1E1F",
        "background_colour": "&H18FFFDF8",
        "border_style": 3,
        "outline": 10,
        "shadow": 0,
        "phone_preview_width": 270,
        "minimum_phone_font_pixels": 17,
    }
    SOCIAL_CAPTION_PROFILE = {
        "font_name": "Arial",
        "font_size": 92,
        "bold": True,
        "max_lines": 2,
        "margin_left": 72,
        "margin_right": 72,
        "margin_bottom": 320,
        "primary_colour": "&H001D1E1F",
        "background_colour": "&H08FFFDF8",
        "border_style": 3,
        "outline": 13,
        "shadow": 0,
        "phone_preview_width": 270,
        "minimum_phone_font_pixels": 23,
        "default_zone": "lower_center_safe",
        "alternate_zones": ["middle_center_safe", "upper_center_safe"],
        "position_change_policy": "scene_boundary_only_when_action_requires",
    }
    # Arial Bold advance widths per 1000 em (metric-compatible with Helvetica-Bold); used
    # only to decide whether caption text fits the renderer's two-line caption layout.
    CAPTION_GLYPH_WIDTHS = {
        " ": 278,
        "!": 333,
        '"': 474,
        "'": 238,
        "(": 333,
        ")": 333,
        ",": 278,
        "-": 333,
        ".": 278,
        "0": 556,
        "1": 556,
        "2": 556,
        "3": 556,
        "4": 556,
        "5": 556,
        "6": 556,
        "7": 556,
        "8": 556,
        "9": 556,
        ":": 333,
        ";": 333,
        "?": 611,
        "A": 722,
        "B": 722,
        "C": 722,
        "D": 722,
        "E": 667,
        "F": 611,
        "G": 778,
        "H": 722,
        "I": 278,
        "J": 556,
        "K": 722,
        "L": 611,
        "M": 833,
        "N": 722,
        "O": 778,
        "P": 667,
        "Q": 778,
        "R": 722,
        "S": 667,
        "T": 611,
        "U": 722,
        "V": 667,
        "W": 944,
        "X": 667,
        "Y": 667,
        "Z": 611,
        "a": 556,
        "b": 611,
        "c": 556,
        "d": 611,
        "e": 556,
        "f": 333,
        "g": 611,
        "h": 611,
        "i": 278,
        "j": 278,
        "k": 556,
        "l": 278,
        "m": 889,
        "n": 611,
        "o": 611,
        "p": 611,
        "q": 611,
        "r": 389,
        "s": 556,
        "t": 333,
        "u": 611,
        "v": 556,
        "w": 778,
        "x": 556,
        "y": 556,
        "z": 500,
        "—": 1000,
        "’": 278,
    }
    # libass sizes a font by ascent + descent (Arial: 1854 + 434 of 2048 units per em).
    CAPTION_EM_PER_FONT_SIZE = 2048 / 2288

    FINAL_FRAME_VISUAL_QA_PROFILE = {
        "profile": "similarstoic-final-frame-v4",
        "inspection_scales": ["full_resolution", "normal_video", "phone"],
        "repair_policy": "repair_dont_empty",
        "structural_geometry_integrity": True,
        "facial_expression_integrity": True,
        "residual_facial_lines_rejected": True,
        "occlusion_layer_integrity": True,
        "reuse_with_variation": True,
        "exact_frame_repeat_requires_editorial_rationale": True,
        "actor_presence_requires_semantic_role": True,
        "character_model_continuity": True,
        "explanatory_artwork_unobscured": True,
        "caption_collision_free": True,
        "source_composite_encode_edge_proof": True,
        "state_replacement_residue_free": True,
    }
    WHOLE_VIDEO_QA_PROFILE = {
        "profile": "similarstoic-whole-video-v1",
        "semantic_change_requires_visual_response": True,
        "persistent_world_evolves_with_meaning": True,
        "long_static_stretch_requires_editorial_rationale": True,
        "actor_optional_and_semantically_justified": True,
        "performance_reuse_requires_semantic_gain": True,
        "world_relevance_required": True,
        "caption_composition_aware": True,
        "callback_requires_progression": True,
        "meaningless_motion_rejected": True,
        "review_scales": ["normal_playback", "phone"],
    }

    RENDER_SETTINGS = {
        "profile": "similarstoic-vertical-v2",
        "width": 1080,
        "height": 1920,
        "frame_rate": 30,
        "container": "mp4",
        "video_codec": "h264",
        "audio_codec": "aac",
        "pixel_format": "yuv420p",
        "caption_policy": "deterministic-script-captions-v1",
        "caption_style": "similarstoic-social-mobile-v3",
        "caption_profile": SOCIAL_CAPTION_PROFILE,
        "default_motion": "static",
        "global_motion_policy": "static_anchored_default",
        "non_static_motion_requires_rationale": True,
        "final_frame_visual_qa": FINAL_FRAME_VISUAL_QA_PROFILE,
        "whole_video_qa": WHOLE_VIDEO_QA_PROFILE,
        "crossfade_ms": 250,
        "duration_tolerance_ms": 100,
    }
    # Frozen snapshots select their encode behaviour. Snapshots without an explicit encode
    # block keep the historical FFmpeg-default libx264/AAC arguments.
    PERSISTENT_ENCODE_PROFILE = {
        "video_encoder": "libx264",
        "crf": 18,
        "preset": "medium",
        "pixel_format": "yuv420p",
        "width": 1080,
        "height": 1920,
        "frame_rate": 30,
        "audio_encoder": "aac",
        "audio_bitrate": "192k",
        "audio_channels": 1,
        "audio_sample_rate": 48000,
        "faststart": True,
    }
    COMPOSITOR_COVERAGE_POLICY = "zero_unwritten_alpha_pixels_v1"
    PERSISTENT_RENDER_SETTINGS = {
        **RENDER_SETTINGS,
        "profile": "similarstoic-vertical-v3",
        "encode": PERSISTENT_ENCODE_PROFILE,
        "compositor_coverage": COMPOSITOR_COVERAGE_POLICY,
    }
    QA_PROFILED_RENDER_PROFILES = frozenset(
        {"similarstoic-vertical-v2", "similarstoic-vertical-v3"}
    )
    # Automated cell review records only deterministic properties it actually measures;
    # perceptual final-frame properties remain human-review contracts.
    AUTOMATED_CELL_QA_PROFILE = {
        "profile": "conveyor-automated-cell-v2",
        "checks": ["persistent_aggregate_verification", COMPOSITOR_COVERAGE_POLICY],
        "perceptual_review": "not_automated",
    }
    # Small, unobtrusive upper-right source label shown only while its cited Scene is on screen.
    CITATION_LABEL_MAX_CHARS = 24
    CITATION_STYLE = {
        "style": "conveyor-citation-upper-right-v1",
        "font_name": "Arial",
        "font_size": 38,
        "bold": True,
        "alignment": 9,
        "margin_horizontal": 110,
        "margin_top": 260,
        "primary_colour": "&H00383838",
        "background_colour": "&H40FFFDF8",
        "border_style": 3,
        "outline": 8,
        "shadow": 0,
    }
    MOTIONS = frozenset({"static", "slow_zoom_in", "slow_zoom_out"})
    TRANSITIONS = frozenset({"cut", "crossfade"})
    # FFmpeg/libass converts SRT input to an internal 384x288 ASS script.  Pixel
    # values from the frozen output profile must be expressed in that coordinate
    # system or large mobile-safe margins can move the caption entirely off-frame.
    SRT_ASS_PLAY_RESOLUTION = (384, 288)
    PERSISTENT_SCENE_INPUT_KEYS = frozenset(
        {
            "scene_id",
            "visual_plan_id",
            "sequence",
            "narration_excerpt",
            "visual_intent",
            "on_screen_text",
            "render_source_kind",
            "world_revision_id",
            "world_key",
            "world_revision",
            "world_definition_digest",
            "resolved_state_id",
            "complete_state_digest",
            "admission_catalog_id",
            "variant_admission_digest",
            "transition_intent_id",
            "scene_model_snapshot",
            "scene_model_snapshot_digest",
            "source_assets",
            "compositor",
            "compositor_digest",
            "frame_width",
            "frame_height",
            "composited_frame_digest",
            "encoded_frame_digest",
            "duration_ms",
            "motion",
            "transition_to_next",
        }
    )

    def __init__(
        self, repository: AtlasRepository, runtime: FfmpegRuntime, storage: LocalMediaStorage
    ) -> None:
        self.repository, self.runtime, self.storage = repository, runtime, storage

    def import_narration(self, narration_id: str, script_id: str, content: bytes, media_type: str):
        if media_type not in {"audio/wav", "audio/mpeg", "audio/mp4"}:
            raise ValueError("Narration media type must be WAV, MP3, or M4A audio.")
        path, digest = self.storage.write("narration", narration_id, content, media_type)
        try:
            probe = self.runtime.probe(self.storage.path(path))
            if probe.media_type != "audio" or probe.duration_ms <= 0:
                raise ValueError("Narration must be usable audio without a video stream.")
            return self.repository.create_narration_asset(
                narration_id, script_id, path, media_type, digest, probe.duration_ms
            )
        except Exception:
            self.storage.remove(path)
            raise

    def generate_brand_narration(
        self,
        execution_id: str,
        narration_id: str,
        script_id: str,
        *,
        brand_key: str,
        execution_authorized: bool = False,
        narrator_profile_id: str | None = None,
    ) -> NarrationGenerationResult:
        """Use approved brand configuration through the existing immutable lifecycle.

        ``narrator_profile_id`` is the profile a production request froze; without one the
        brand resolves to its historical narrator.

        Callers must obtain separate execution/spend authority and migrate the
        target database before invoking this explicit, non-default entry point.
        """
        from project_atlas.narration import resolve_narrator

        if not execution_authorized:
            raise NarrationSynthesisError("Separate narration spend authorization is required.")
        if (
            self.repository.connection.execute(
                "SELECT 1 FROM schema_migrations WHERE version = 26"
            ).fetchone()
            is None
        ):
            raise NarrationSynthesisError("Migration 26 is required before Inworld execution.")
        return self.generate_local_narration(
            execution_id,
            narration_id,
            script_id,
            synthesizer=resolve_narrator(
                brand_key, execution_authorized=True, profile_id=narrator_profile_id
            ),
        )

    def generate_local_narration(
        self,
        execution_id: str,
        narration_id: str,
        script_id: str,
        synthesizer: NarrationSynthesizer | None = None,
    ) -> NarrationGenerationResult:
        """Synthesize exact Script text and record one immutable terminal attempt."""

        script = self.repository.get_script(script_id)
        engine = synthesizer or LocalSystemSpeechSynthesizer()
        started_at = _utc_timestamp()
        path: str | None = None
        synthesis: NarrationSynthesis | None = None
        try:
            synthesis = engine.synthesize(script.narration_text)
            if synthesis.media_type != "audio/wav":
                raise NarrationSynthesisError("Local generated narration must be managed as WAV.")
            path, digest = self.storage.write(
                "narration", narration_id, synthesis.content, synthesis.media_type
            )
            probe = self.runtime.probe(self.storage.path(path))
            if probe.media_type != "audio" or probe.duration_ms <= 0:
                raise NarrationSynthesisError(
                    "Generated narration is not usable audio without video."
                )
            self.runtime.assert_audible(self.storage.path(path))
            execution, asset = self.repository.record_successful_generated_narration(
                execution_id,
                narration_id,
                script.id,
                path,
                synthesis.media_type,
                digest,
                probe.duration_ms,
                synthesis.engine_kind,
                synthesis.engine_identity,
                synthesis.voice_identity,
                synthesis.locale,
                synthesis.settings,
                started_at,
                _utc_timestamp(),
            )
            return NarrationGenerationResult(execution, asset)
        except Exception as error:
            if path is not None:
                self.storage.remove(path)
            if synthesis is None:
                synthesis = NarrationSynthesis(
                    b"",
                    "audio/wav",
                    engine.engine_kind,
                    engine.engine_identity,
                    engine.voice_identity,
                    engine.locale,
                    getattr(engine, "settings", {}),
                )
            execution = self.repository.record_failed_narration_generation(
                execution_id,
                script.id,
                synthesis.engine_kind,
                synthesis.engine_identity,
                synthesis.voice_identity,
                synthesis.locale,
                synthesis.settings,
                type(error).__name__,
                str(error)[:1000],
                started_at,
                _utc_timestamp(),
            )
            return NarrationGenerationResult(execution, None)

    @staticmethod
    def caption_cues(text: str, duration_ms: int) -> list[dict[str, Any]]:
        """Historical five-word captions, kept only for legacy AssetSelection snapshots.

        Canonical persistent-scene snapshots use ``speech_timing.build_caption_cues``.
        """
        words = text.split()
        chunks = [" ".join(words[index : index + 5]) for index in range(0, len(words), 5)]
        if not chunks:
            raise ValueError("Script narration must produce captions.")
        weights = [max(1, len(chunk.split())) for chunk in chunks]
        total = sum(weights)
        start, cues = 0, []
        for index, (chunk, weight) in enumerate(zip(chunks, weights, strict=True)):
            end = (
                duration_ms
                if index == len(chunks) - 1
                else start + round(duration_ms * weight / total)
            )
            cues.append({"text": chunk, "start_ms": start, "end_ms": end})
            start = end
        return cues

    def create_snapshot(
        self,
        snapshot_id: str,
        visual_plan_id: str,
        narration_id: str,
        scene_inputs: list[dict[str, Any]],
    ) -> FinalMediaInputSnapshot:
        plan = self.repository._require_gate_authorized_visual_plan(visual_plan_id)
        narration = self.repository.get_narration_asset(narration_id)
        if narration.script_id != plan.script_id:
            raise ValueError("NarrationAsset must belong to the exact VisualPlan Script.")
        scenes = self.repository.list_scenes_for_visual_plan(plan.id)
        if len(scene_inputs) != len(scenes):
            raise ValueError("Every current VisualPlan Scene must appear exactly once.")
        frozen = []
        for scene, supplied in zip(scenes, scene_inputs, strict=True):
            if supplied.get("scene_id") != scene.id:
                raise ValueError("Scene inputs must use canonical VisualPlan sequence order.")
            duration = supplied.get("duration_ms")
            motion, transition = supplied.get("motion"), supplied.get("transition_to_next")
            if not isinstance(duration, int) or duration <= 0 or motion not in self.MOTIONS:
                raise ValueError("Scene duration and motion are invalid.")
            if scene is scenes[-1]:
                if transition is not None:
                    raise ValueError("The final Scene must not specify a transition.")
            elif transition not in self.TRANSITIONS:
                raise ValueError("Scene transition is invalid.")
            selection = self.repository.get_asset_selection(supplied.get("asset_selection_id", ""))
            asset_spec = self.repository.get_asset_spec(selection.asset_spec_id)
            asset = self.repository.get_asset(selection.asset_id)
            if asset_spec.scene_id != scene.id:
                raise ValueError("AssetSelection must belong to its exact supplied Scene.")
            self.repository._validate_selectable_managed_asset(asset)
            frozen.append(
                {
                    "scene_id": scene.id,
                    "sequence": scene.sequence,
                    "narration_excerpt": scene.narration_excerpt,
                    "visual_intent": scene.visual_intent,
                    "on_screen_text": scene.on_screen_text,
                    "asset_selection_id": selection.id,
                    "asset_spec_id": asset_spec.id,
                    "asset_spec": {
                        "asset_type": asset_spec.asset_type,
                        "purpose": asset_spec.purpose,
                        "description": asset_spec.description,
                    },
                    "asset_id": asset.id,
                    "media_type": asset.media_type,
                    "content_digest": asset.content_digest,
                    "duration_ms": duration,
                    "motion": motion,
                    "transition_to_next": transition,
                    "character_reference_set_id": selection.character_reference_set_id,
                }
            )
        if sum(item["duration_ms"] for item in frozen) != narration.duration_ms:
            raise ValueError("Scene durations must equal the exact NarrationAsset duration.")
        script = self.repository.get_script(plan.script_id)
        return self.repository.create_final_media_input_snapshot(
            snapshot_id,
            plan.id,
            narration.id,
            frozen,
            self.caption_cues(script.narration_text, narration.duration_ms),
            dict(self.RENDER_SETTINGS),
        )

    def create_persistent_scene_snapshot(
        self,
        snapshot_id: str,
        visual_plan_id: str,
        narration_id: str,
        scene_inputs: list[dict[str, Any]],
        citations: list[dict[str, Any]] | None = None,
    ) -> FinalMediaInputSnapshot:
        """Freeze exact persisted scene states as first-class v2 render inputs."""

        plan = self.repository._require_gate_authorized_visual_plan(visual_plan_id)
        narration = self.repository.get_narration_asset(narration_id)
        if narration.script_id != plan.script_id:
            raise ValueError("NarrationAsset must belong to the exact VisualPlan Script.")
        scenes = self.repository.list_scenes_for_visual_plan(plan.id)
        if len(scene_inputs) != len(scenes):
            raise ValueError("Every current VisualPlan Scene must appear exactly once.")
        contract = compositor_contract()
        frozen = []
        seen_states: set[str] = set()
        for index, (scene, supplied) in enumerate(zip(scenes, scene_inputs, strict=True)):
            if supplied.get("scene_id") != scene.id:
                raise ValueError("Scene inputs must use canonical VisualPlan sequence order.")
            state_id = supplied.get("resolved_state_id")
            if not isinstance(state_id, str) or not state_id or state_id in seen_states:
                raise ValueError("Every Scene requires one unique exact persistent state.")
            seen_states.add(state_id)
            duration = supplied.get("duration_ms")
            motion = supplied.get("motion")
            transition = supplied.get("transition_to_next")
            if not isinstance(duration, int) or duration <= 0 or motion != "static":
                raise ValueError("Persistent-scene proof inputs require positive static durations.")
            if index == len(scenes) - 1:
                if transition is not None:
                    raise ValueError("The final Scene must not specify a transition.")
            elif transition not in self.TRANSITIONS:
                raise ValueError("Scene transition is invalid.")
            context = self.repository.get_persistent_scene_media_context(state_id)
            if context.world.bindings.visual_plan_id != plan.id:
                raise ValueError("Persistent state belongs to another VisualPlan.")
            if context.state.editorial_scene_id != scene.id:
                raise ValueError("Persistent state belongs to another editorial Scene.")
            frame = load_persistent_scene_frame(self.repository, state_id)
            payload = frame.scene_model_snapshot
            frozen.append(
                {
                    "scene_id": scene.id,
                    "visual_plan_id": plan.id,
                    "sequence": scene.sequence,
                    "narration_excerpt": scene.narration_excerpt,
                    "visual_intent": scene.visual_intent,
                    "on_screen_text": scene.on_screen_text,
                    "render_source_kind": "persistent_scene_state",
                    "world_revision_id": frame.world_id,
                    "world_key": context.world.world_key,
                    "world_revision": context.world.revision,
                    "world_definition_digest": context.state.world_definition_digest,
                    "resolved_state_id": context.state.state_id,
                    "complete_state_digest": context.state.state_digest,
                    "admission_catalog_id": frame.admission_catalog_id,
                    "variant_admission_digest": context.state.variant_admission_digest,
                    "transition_intent_id": frame.transition_intent_id,
                    "scene_model_snapshot": payload,
                    "scene_model_snapshot_digest": frame.scene_model_snapshot_digest,
                    "source_assets": payload["assets"],
                    "compositor": contract,
                    "compositor_digest": digest(contract),
                    "frame_width": frame.width,
                    "frame_height": frame.height,
                    "composited_frame_digest": frame.rgba_digest,
                    "encoded_frame_digest": frame.png_digest,
                    "duration_ms": duration,
                    "motion": motion,
                    "transition_to_next": transition,
                }
            )
        if sum(item["duration_ms"] for item in frozen) != narration.duration_ms:
            raise ValueError("Scene durations must equal the exact NarrationAsset duration.")
        script = self.repository.get_script(plan.script_id)
        settings = dict(self.PERSISTENT_RENDER_SETTINGS)
        settings["persistent_scene_compositor"] = contract
        if citations:
            settings["citation_overlay"] = {
                "style": dict(self.CITATION_STYLE),
                "citations": self.citation_overlays(frozen, citations),
            }
        timing = self.narration_speech_timing(narration, script.narration_text)
        boundaries, elapsed = [], 0
        for item in frozen[:-1]:
            elapsed += item["duration_ms"]
            boundaries.append(elapsed)
        settings["caption_policy"] = speech_timing.CAPTION_POLICY
        settings["caption_timing"] = {
            **speech_timing.timing_evidence(timing),
            "silence_detection": dict(self.runtime.SILENCE_DETECTION),
        }
        return self.repository.create_persistent_final_media_input_snapshot(
            snapshot_id,
            plan.id,
            narration.id,
            frozen,
            speech_timing.build_caption_cues(
                timing,
                script.narration_text,
                boundaries,
                lambda text: self.caption_fits(text, settings["caption_profile"]),
            ),
            settings,
        )

    @classmethod
    def caption_fits(cls, text: str, profile: dict[str, Any]) -> bool:
        """Whether text wraps into the social caption layout's maximum lines at 1080 px.

        Uses the frozen profile's font size, side margins and box padding, the same values the
        renderer passes to libass, with greedy word wrapping (which minimises line count).
        """

        em = profile["font_size"] * cls.CAPTION_EM_PER_FONT_SIZE
        line_width = (
            cls.PERSISTENT_RENDER_SETTINGS["width"]
            - profile["margin_left"]
            - profile["margin_right"]
            - 2 * profile["outline"]
        )

        def width(value: str) -> float:
            return em * sum(cls.CAPTION_GLYPH_WIDTHS.get(char, 556) for char in value) / 1000

        lines, current = 1, ""
        for word in text.split():
            candidate = f"{current} {word}" if current else word
            if width(candidate) <= line_width:
                current = candidate
                continue
            if not current or width(word) > line_width:
                return False
            lines, current = lines + 1, word
        return lines <= profile["max_lines"]

    def narration_speech_timing(self, narration: Any, text: str) -> speech_timing.SpeechTiming:
        """Derive word timings for exact narration audio from its detected pauses."""

        pauses = self.runtime.detect_silences(self.storage.path(narration.storage_path))
        return speech_timing.estimate_word_timings(
            text,
            narration.duration_ms,
            [speech_timing.Silence(start, end) for start, end in pauses],
        )

    @classmethod
    def citation_overlays(
        cls, scene_inputs: list[dict[str, Any]], citations: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Time each explicitly supplied citation to exactly its cited Scene's interval."""

        intervals: dict[str, tuple[int, int]] = {}
        elapsed = 0
        for item in scene_inputs:
            intervals[item["scene_id"]] = (elapsed, elapsed + item["duration_ms"])
            elapsed += item["duration_ms"]
        if not isinstance(citations, list):
            raise ValueError("Citations must be a list.")
        timed, seen = [], set()
        for citation in citations:
            if not isinstance(citation, dict) or set(citation) != {
                "scene_id",
                "label",
                "source_ids",
            }:
                raise ValueError("A citation requires exactly scene_id, label and source_ids.")
            scene_id, label, source_ids = (
                citation["scene_id"],
                citation["label"],
                citation["source_ids"],
            )
            if scene_id not in intervals or scene_id in seen:
                raise ValueError("A citation must name one distinct Scene of this timeline.")
            if (
                not isinstance(label, str)
                or not label.strip()
                or len(label.strip()) > cls.CITATION_LABEL_MAX_CHARS
                or any(character in label for character in "{}\\\r\n")
            ):
                raise ValueError("A citation label must be 1-24 plain characters.")
            if (
                not isinstance(source_ids, list)
                or not source_ids
                or not all(isinstance(item, str) and item.strip() for item in source_ids)
                or len(set(source_ids)) != len(source_ids)
            ):
                raise ValueError("A citation requires distinct source IDs.")
            seen.add(scene_id)
            start, end = intervals[scene_id]
            timed.append(
                {
                    "scene_id": scene_id,
                    "label": label.strip(),
                    "source_ids": list(source_ids),
                    "start_ms": start,
                    "end_ms": end,
                }
            )
        return sorted(timed, key=lambda item: item["start_ms"])

    @classmethod
    def _citation_filter(
        cls,
        render_settings: dict[str, Any],
        scene_inputs: list[dict[str, Any]],
        temporary_root: Path,
    ) -> str | None:
        """Return the frozen citation overlay filter, or None for citation-free snapshots."""

        overlay = render_settings.get("citation_overlay")
        if overlay is None:
            return None
        if not isinstance(overlay, dict) or overlay.get("style") != cls.CITATION_STYLE:
            raise MediaRuntimeError("Snapshot has an unsupported citation overlay style.")
        frozen = overlay.get("citations")
        supplied = [
            {key: item[key] for key in ("scene_id", "label", "source_ids")}
            for item in frozen or []
            if isinstance(item, dict)
        ]
        try:
            expected = cls.citation_overlays(scene_inputs, supplied)
        except (KeyError, ValueError) as error:
            raise MediaRuntimeError("Snapshot citation overlay is invalid.") from error
        if not frozen or frozen != expected:
            raise MediaRuntimeError("Snapshot citation timing differs from its cited Scenes.")
        # Position with a numpad override tag, as caption safe zones do; SRT force_style
        # Alignment would be interpreted with legacy SSA numbering.
        position = rf"{{\an{cls.CITATION_STYLE['alignment']}}}"
        (temporary_root / "citations.srt").write_text(
            cls._srt([{**item, "text": position + item["label"]} for item in expected]),
            encoding="utf-8",
        )
        style = cls.CITATION_STYLE
        width, height = cls.SRT_ASS_PLAY_RESOLUTION

        def ass(value: int, play: int, frame: int) -> str:
            return f"{value * play / frame:.6f}".rstrip("0").rstrip(".")

        force_style = (
            f"FontName={style['font_name']},"
            f"FontSize={ass(style['font_size'], height, render_settings['height'])},"
            f"Bold={-1 if style['bold'] else 0},"
            f"MarginL={ass(style['margin_horizontal'], width, render_settings['width'])},"
            f"MarginR={ass(style['margin_horizontal'], width, render_settings['width'])},"
            f"MarginV={ass(style['margin_top'], height, render_settings['height'])},"
            f"PrimaryColour={style['primary_colour']},"
            f"OutlineColour={style['background_colour']},"
            f"BackColour={style['background_colour']},"
            f"BorderStyle={style['border_style']},"
            f"Outline={ass(style['outline'], height, render_settings['height'])},"
            f"Shadow={style['shadow']}"
        )
        return f"[captioned]subtitles=citations.srt:force_style='{force_style}'[cited]"

    def _persistent_scene_frame(
        self,
        item: dict[str, Any],
        visual_plan_id: str | None = None,
        require_full_coverage: bool = False,
    ) -> bytes:
        """Revalidate every frozen v2 binding and return exact deterministic PNG bytes."""

        if set(item) != self.PERSISTENT_SCENE_INPUT_KEYS:
            raise MediaRuntimeError("Persistent snapshot has unknown or missing scene fields.")
        if item["render_source_kind"] != "persistent_scene_state":
            raise MediaRuntimeError("Persistent snapshot has an invalid render source kind.")
        if item["motion"] != "static":
            raise MediaRuntimeError("Persistent snapshot motion must remain static.")
        frame = load_persistent_scene_frame(self.repository, item["resolved_state_id"])
        context = self.repository.get_persistent_scene_media_context(item["resolved_state_id"])
        scene = self.repository.get_scene(item["scene_id"])
        expected_plan_id = visual_plan_id or item["visual_plan_id"]
        if (
            item["visual_plan_id"] != expected_plan_id
            or context.world.bindings.visual_plan_id != expected_plan_id
            or scene.visual_plan_id != expected_plan_id
        ):
            raise MediaRuntimeError("Persistent snapshot VisualPlan binding differs.")
        editorial = {
            "sequence": scene.sequence,
            "narration_excerpt": scene.narration_excerpt,
            "visual_intent": scene.visual_intent,
            "on_screen_text": scene.on_screen_text,
        }
        if any(item[key] != value for key, value in editorial.items()):
            raise MediaRuntimeError("Persistent snapshot editorial Scene content differs.")
        expected = {
            "world_revision_id": frame.world_id,
            "world_key": context.world.world_key,
            "world_revision": context.world.revision,
            "world_definition_digest": context.state.world_definition_digest,
            "complete_state_digest": context.state.state_digest,
            "admission_catalog_id": frame.admission_catalog_id,
            "variant_admission_digest": context.state.variant_admission_digest,
            "transition_intent_id": frame.transition_intent_id,
            "scene_model_snapshot_digest": frame.scene_model_snapshot_digest,
            "compositor_digest": digest(compositor_contract()),
            "frame_width": frame.width,
            "frame_height": frame.height,
            "composited_frame_digest": frame.rgba_digest,
            "encoded_frame_digest": frame.png_digest,
        }
        if any(item[key] != value for key, value in expected.items()):
            raise MediaRuntimeError("Persistent snapshot identity or digest no longer matches.")
        if item["scene_id"] != context.state.editorial_scene_id:
            raise MediaRuntimeError("Persistent snapshot Scene binding differs.")
        if canonical_json(item["scene_model_snapshot"]) != canonical_json(
            frame.scene_model_snapshot
        ):
            raise MediaRuntimeError("Persistent scene-model snapshot payload differs.")
        if item["source_assets"] != frame.scene_model_snapshot["assets"]:
            raise MediaRuntimeError("Persistent snapshot source Asset set differs.")
        if item["compositor"] != compositor_contract():
            raise MediaRuntimeError("Persistent snapshot compositor contract differs.")
        if require_full_coverage and unwritten_alpha_pixels(frame.rgba):
            raise MediaRuntimeError("Persistent scene frame has unwritten compositor pixels.")
        return frame.png

    CAPTION_ZONE_OVERRIDES = {
        "lower_center_safe": "",
        "middle_center_safe": r"{\an5}",
        "upper_center_safe": r"{\an8}",
    }

    @classmethod
    def _validated_caption_cues(
        cls,
        cues: list[dict[str, Any]],
        scenes: list[dict[str, Any]],
        settings: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Validate explicit cue zones and allow changes only at Scene boundaries."""

        profile = settings.get("caption_profile")
        default_zone = (
            profile.get("default_zone", "lower_center_safe")
            if isinstance(profile, dict)
            else "lower_center_safe"
        )
        allowed_zones = {default_zone, *(profile.get("alternate_zones", []) if profile else [])}
        boundaries = []
        elapsed = 0
        for scene in scenes[:-1]:
            elapsed += scene["duration_ms"]
            boundaries.append(elapsed)
        validated: list[dict[str, Any]] = []
        previous_end = 0
        previous_zone: str | None = None
        for cue in cues:
            text = cue.get("text")
            start, end = cue.get("start_ms"), cue.get("end_ms")
            zone = cue.get("zone", default_zone)
            if (
                not isinstance(text, str)
                or not text.strip()
                or "{\\" in text
                or len(text.splitlines()) > 2
            ):
                raise MediaRuntimeError("Caption cue text is invalid or contains raw positioning.")
            if (
                not isinstance(start, int)
                or not isinstance(end, int)
                or start < previous_end
                or end <= start
            ):
                raise MediaRuntimeError("Caption cue timing is invalid or overlapping.")
            if zone not in allowed_zones or zone not in cls.CAPTION_ZONE_OVERRIDES:
                raise MediaRuntimeError("Caption cue uses an unsupported safe zone.")
            if (
                previous_zone is not None
                and zone != previous_zone
                and not any(abs(start - boundary) <= 150 for boundary in boundaries)
            ):
                raise MediaRuntimeError("Caption zone changes must occur at a Scene boundary.")
            validated.append({**cue, "text": text.strip(), "zone": zone})
            previous_end, previous_zone = end, zone
        return validated

    @classmethod
    def _srt(cls, cues: list[dict[str, Any]]) -> str:
        def stamp(milliseconds: int) -> str:
            seconds, millis = divmod(milliseconds, 1000)
            minutes, seconds = divmod(seconds, 60)
            hours, minutes = divmod(minutes, 60)
            return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"

        return "\n\n".join(
            f"{index}\n{stamp(cue['start_ms'])} --> {stamp(cue['end_ms'])}\n"
            f"{cls.CAPTION_ZONE_OVERRIDES.get(cue.get('zone', 'lower_center_safe'), '')}"
            f"{cue['text']}"
            for index, cue in enumerate(cues, 1)
        )

    @classmethod
    def _scene_filter(
        cls, index: int, item: dict[str, Any], render_settings: dict[str, Any]
    ) -> str:
        """Normalize one still input and apply the one frozen deterministic motion choice."""

        effective_seconds = (
            item["duration_ms"]
            + (render_settings["crossfade_ms"] if item["transition_to_next"] == "crossfade" else 0)
        ) / 1000
        normalized = (
            "scale=1080:1920:force_original_aspect_ratio=decrease,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0x101010,"
            "fps=30,setsar=1"
        )
        motion = item["motion"]
        if motion == "static":
            return f"[{index}:v]{normalized},setpts=PTS-STARTPTS,settb=AVTB[v{index}]"
        frames = round(effective_seconds * render_settings["frame_rate"])
        if motion == "slow_zoom_in":
            zoom = f"min(zoom+0.08/{max(frames, 1)},1.08)"
        elif motion == "slow_zoom_out":
            zoom = f"max(1.08-on*0.08/{max(frames, 1)},1)"
        else:
            raise MediaRuntimeError("Snapshot has an unsupported frozen motion.")
        return (
            f"[{index}:v]{normalized},"
            f"zoompan=z='{zoom}':d=1:s=1080x1920:fps=30,"
            f"trim=duration={effective_seconds:.3f},setpts=PTS-STARTPTS,settb=AVTB[v{index}]"
        )

    @classmethod
    def _composition_filters(
        cls,
        scenes: list[dict[str, Any]],
        total_duration_ms: int,
        render_settings: dict[str, Any] | None = None,
    ) -> list[str]:
        """Compose cuts and crossfades on the frozen intended—not overlap-adjusted—timeline."""

        if not scenes:
            raise MediaRuntimeError("A final-media snapshot must freeze at least one Scene.")
        settings = render_settings or cls.RENDER_SETTINGS
        try:
            crossfade_ms = settings["crossfade_ms"]
            frame_rate = settings["frame_rate"]
        except KeyError as error:
            raise MediaRuntimeError("Snapshot has incomplete frozen render settings.") from error
        if not isinstance(crossfade_ms, int) or crossfade_ms <= 0 or frame_rate != 30:
            raise MediaRuntimeError("Snapshot has unsupported frozen render settings.")
        if (
            settings.get("profile") in cls.QA_PROFILED_RENDER_PROFILES
            and settings.get("final_frame_visual_qa") != cls.FINAL_FRAME_VISUAL_QA_PROFILE
        ):
            raise MediaRuntimeError("Snapshot has an unsupported final-frame visual QA profile.")
        if (
            settings.get("profile") in cls.QA_PROFILED_RENDER_PROFILES
            and settings.get("whole_video_qa") != cls.WHOLE_VIDEO_QA_PROFILE
        ):
            raise MediaRuntimeError("Snapshot has an unsupported whole-video QA profile.")
        filters = [cls._scene_filter(index, item, settings) for index, item in enumerate(scenes)]
        current = "v0"
        cumulative_ms = scenes[0]["duration_ms"]
        crossfade_seconds = crossfade_ms / 1000
        for index in range(1, len(scenes)):
            transition = scenes[index - 1]["transition_to_next"]
            target = f"chain{index}"
            if transition == "crossfade":
                filters.append(
                    f"[{current}][v{index}]xfade=transition=fade:duration={crossfade_seconds:.3f}:"
                    f"offset={cumulative_ms / 1000:.3f}[{target}]"
                )
            elif transition == "cut":
                filters.append(f"[{current}][v{index}]concat=n=2:v=1:a=0[{target}]")
            else:
                raise MediaRuntimeError("Snapshot has an invalid frozen scene transition.")
            current = target
            cumulative_ms += scenes[index]["duration_ms"]
        if cumulative_ms != total_duration_ms:
            raise MediaRuntimeError(
                "Frozen Scene durations do not match the intended final timeline."
            )
        filters.append(
            f"[{current}]trim=duration={total_duration_ms / 1000:.3f},setpts=PTS-STARTPTS[composed]"
        )
        caption_style = settings.get("caption_style")
        ass_width, ass_height = cls.SRT_ASS_PLAY_RESOLUTION

        def ass_x(value: int | float) -> str:
            return f"{value * ass_width / settings['width']:.6f}".rstrip("0").rstrip(".")

        def ass_y(value: int | float) -> str:
            return f"{value * ass_height / settings['height']:.6f}".rstrip("0").rstrip(".")

        if caption_style == "similarstoic-readable-v1":
            force_style = (
                f"FontSize={ass_y(42)},Alignment=2,MarginV={ass_y(130)},"
                "PrimaryColour=&H00FFFFFF,OutlineColour=&H00101010,"
                f"BorderStyle=1,Outline={ass_y(3)}"
            )
        elif caption_style in {
            "similarstoic-social-mobile-v2",
            "similarstoic-social-mobile-v3",
        }:
            profile = settings.get("caption_profile")
            expected_profile = (
                cls.SOCIAL_CAPTION_PROFILE_V2
                if caption_style == "similarstoic-social-mobile-v2"
                else cls.SOCIAL_CAPTION_PROFILE
            )
            if profile != expected_profile:
                raise MediaRuntimeError("Snapshot has an unsupported social caption profile.")
            phone_font_pixels = round(
                profile["font_size"] * profile["phone_preview_width"] / settings["width"]
            )
            if (
                profile["max_lines"] != 2
                or profile["margin_bottom"] < (300 if caption_style.endswith("v3") else 220)
                or min(profile["margin_left"], profile["margin_right"]) < 60
                or phone_font_pixels < profile["minimum_phone_font_pixels"]
            ):
                raise MediaRuntimeError("Social caption profile fails mobile readability bounds.")
            if caption_style.endswith("v3") and (
                profile.get("default_zone") != "lower_center_safe"
                or profile.get("alternate_zones") != ["middle_center_safe", "upper_center_safe"]
                or profile.get("position_change_policy")
                != "scene_boundary_only_when_action_requires"
            ):
                raise MediaRuntimeError("Social caption profile has an unsafe position hierarchy.")
            force_style = (
                f"FontName={profile['font_name']},FontSize={ass_y(profile['font_size'])},"
                f"Bold={-1 if profile['bold'] else 0},Alignment=2,"
                f"MarginL={ass_x(profile['margin_left'])},"
                f"MarginR={ass_x(profile['margin_right'])},"
                f"MarginV={ass_y(profile['margin_bottom'])},"
                f"PrimaryColour={profile['primary_colour']},"
                f"OutlineColour={profile['background_colour']},"
                f"BackColour={profile['background_colour']},"
                f"BorderStyle={profile['border_style']},"
                f"Outline={ass_y(profile['outline'])},Shadow={ass_y(profile['shadow'])}"
            )
        else:
            raise MediaRuntimeError("Snapshot has an unsupported caption style.")
        filters.append(f"[composed]subtitles=captions.srt:force_style='{force_style}'[captioned]")
        return filters

    @classmethod
    def _encode_arguments(cls, render_settings: dict[str, Any]) -> tuple[list[str], bool]:
        """Return the frozen profile's encode arguments and whether full coverage is required."""

        profile = render_settings.get("profile")
        if "encode" not in render_settings and profile != cls.PERSISTENT_RENDER_SETTINGS["profile"]:
            return (
                [
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-r",
                    "30",
                    "-c:a",
                    "aac",
                    "-movflags",
                    "+faststart",
                ],
                False,
            )
        if (
            profile != cls.PERSISTENT_RENDER_SETTINGS["profile"]
            or render_settings.get("encode") != cls.PERSISTENT_ENCODE_PROFILE
            or render_settings.get("compositor_coverage") != cls.COMPOSITOR_COVERAGE_POLICY
            or (render_settings.get("width"), render_settings.get("height"))
            != (cls.PERSISTENT_ENCODE_PROFILE["width"], cls.PERSISTENT_ENCODE_PROFILE["height"])
        ):
            raise MediaRuntimeError("Snapshot has an unsupported frozen encode profile.")
        encode = cls.PERSISTENT_ENCODE_PROFILE
        return (
            [
                "-c:v",
                encode["video_encoder"],
                "-preset",
                encode["preset"],
                "-crf",
                str(encode["crf"]),
                "-pix_fmt",
                encode["pixel_format"],
                "-r",
                str(encode["frame_rate"]),
                "-c:a",
                encode["audio_encoder"],
                "-b:a",
                encode["audio_bitrate"],
                "-ac",
                str(encode["audio_channels"]),
                "-ar",
                str(encode["audio_sample_rate"]),
                "-movflags",
                "+faststart",
            ],
            True,
        )

    def artifact_content(self, artifact_id: str) -> bytes:
        """Safely retrieve only the exact managed bytes registered for one MP4 artifact."""

        artifact = self.repository.get_final_media_artifact(artifact_id)
        if artifact.media_type != "video/mp4":
            raise MediaRuntimeError("FinalMediaArtifact is not a safe MP4 artifact.")
        return self.storage.read_verified(artifact.storage_path, artifact.content_digest)

    def narration_content(self, narration_asset_id: str) -> bytes:
        """Safely retrieve only the exact managed bytes registered for one narration take."""

        narration = self.repository.get_narration_asset(narration_asset_id)
        return self.storage.read_verified(narration.storage_path, narration.content_digest)

    def render(self, execution_id: str, artifact_id: str, snapshot_id: str):
        """Synchronously create one terminal FFmpeg render and registered MP4 artifact."""
        snapshot = self.repository.get_final_media_input_snapshot(snapshot_id)
        temporary_root = Path(tempfile.mkdtemp(prefix="atlas-render-"))
        final_path: str | None = None
        versions = {"renderer_version": "unavailable", "probe_version": "unavailable"}
        attempt_recorded = False
        try:
            versions = self.runtime.assert_capabilities()
            narration = self.repository.get_narration_asset(snapshot.narration_asset_id)
            render_settings = snapshot.render_settings
            narration_path = self.storage.path(narration.storage_path)
            self.storage.read_verified(narration.storage_path, narration.content_digest)
            subtitle = temporary_root / "captions.srt"
            caption_cues = self._validated_caption_cues(
                snapshot.caption_cues, snapshot.scene_inputs, render_settings
            )
            subtitle.write_text(self._srt(caption_cues), encoding="utf-8")
            if snapshot.snapshot_schema_version not in {"v1", SNAPSHOT_SCHEMA_VERSION}:
                raise MediaRuntimeError("Final-media snapshot schema version is unsupported.")
            if snapshot.snapshot_schema_version == SNAPSHOT_SCHEMA_VERSION and (
                render_settings.get("persistent_scene_compositor") != compositor_contract()
            ):
                raise MediaRuntimeError("Snapshot has an unsupported persistent compositor.")
            encode_arguments, require_full_coverage = self._encode_arguments(render_settings)
            arguments = [self.runtime.ffmpeg_path, "-y"]
            for index, item in enumerate(snapshot.scene_inputs):
                if snapshot.snapshot_schema_version == "v1":
                    asset = self.repository.get_asset(item["asset_id"])
                    path = self.repository.managed_asset_path(asset.id)
                    if sha256(path.read_bytes()).hexdigest() != item["content_digest"]:
                        raise MediaRuntimeError(
                            "Managed selected Asset bytes do not match their frozen digest."
                        )
                else:
                    path = temporary_root / f"persistent-scene-{index:04d}.png"
                    path.write_bytes(
                        self._persistent_scene_frame(
                            item, snapshot.visual_plan_id, require_full_coverage
                        )
                    )
                source_duration_ms = item["duration_ms"] + (
                    render_settings["crossfade_ms"]
                    if item["transition_to_next"] == "crossfade"
                    else 0
                )
                arguments.extend(
                    [
                        "-loop",
                        "1",
                        "-t",
                        f"{source_duration_ms / 1000:.3f}",
                        "-i",
                        str(path),
                    ]
                )
            arguments.extend(["-i", str(narration_path)])
            filters = self._composition_filters(
                snapshot.scene_inputs, narration.duration_ms, render_settings
            )
            citation_filter = self._citation_filter(
                render_settings, snapshot.scene_inputs, temporary_root
            )
            if citation_filter is not None:
                filters.append(citation_filter)
            output = temporary_root / "output.mp4"
            arguments.extend(
                [
                    "-filter_complex",
                    ";".join(filters),
                    "-map",
                    "[cited]" if citation_filter is not None else "[captioned]",
                    "-map",
                    f"{len(snapshot.scene_inputs)}:a",
                    "-t",
                    f"{narration.duration_ms / 1000:.3f}",
                    *encode_arguments,
                    str(output),
                ]
            )
            self.runtime._run(arguments, timeout=120, cwd=temporary_root)
            probe = self.runtime.probe(output)
            if (probe.width, probe.height, probe.video_codec, probe.audio_codec) != (
                1080,
                1920,
                "h264",
                "aac",
            ):
                raise MediaRuntimeError("Rendered MP4 does not meet the fixed technical profile.")
            delta_ms = abs(probe.duration_ms - narration.duration_ms)
            if delta_ms > render_settings["duration_tolerance_ms"]:
                raise MediaRuntimeError(
                    "Rendered MP4 duration differs from the frozen final timeline."
                )
            content = output.read_bytes()
            final_path, digest = self.storage.write("final", artifact_id, content, "video/mp4")
            artifact = self.repository.record_successful_render(
                execution_id,
                snapshot.id,
                versions["renderer_version"],
                versions["probe_version"],
                {
                    "caption_burned": True,
                    "crossfade_ms": render_settings["crossfade_ms"],
                    "duration_ms": probe.duration_ms,
                    "intended_duration_ms": narration.duration_ms,
                },
                artifact_id,
                final_path,
                digest,
                probe.duration_ms,
                probe.width or 0,
                probe.height or 0,
                {
                    "probe": probe.raw,
                    "caption_burned": True,
                    "duration_delta_ms": delta_ms,
                    "frame_rate": probe.frame_rate,
                },
            )
            attempt_recorded = True
            return artifact
        except Exception as error:
            if final_path:
                self.storage.remove(final_path)
            if not attempt_recorded:
                with suppress(Exception):
                    self.repository.create_render_execution(
                        execution_id,
                        snapshot_id,
                        versions["renderer_version"],
                        versions["probe_version"],
                        "failed",
                        {"caption_burned": False},
                        type(error).__name__,
                        str(error)[:1000],
                    )
            raise
        finally:
            shutil.rmtree(temporary_root, ignore_errors=True)
