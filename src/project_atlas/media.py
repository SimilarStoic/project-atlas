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
from typing import Any

from project_atlas.persistence import (
    AtlasRepository,
    FinalMediaInputSnapshot,
    NarrationAsset,
    NarrationGenerationExecution,
)


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

    RENDER_SETTINGS = {
        "profile": "similarstoic-vertical-v1",
        "width": 1080,
        "height": 1920,
        "frame_rate": 30,
        "container": "mp4",
        "video_codec": "h264",
        "audio_codec": "aac",
        "pixel_format": "yuv420p",
        "caption_policy": "deterministic-script-captions-v1",
        "caption_style": "similarstoic-readable-v1",
        "crossfade_ms": 250,
        "duration_tolerance_ms": 100,
    }
    MOTIONS = frozenset({"static", "slow_zoom_in", "slow_zoom_out"})
    TRANSITIONS = frozenset({"cut", "crossfade"})

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

    def generate_local_narration(
        self,
        execution_id: str,
        narration_id: str,
        script_id: str,
        synthesizer: LocalSystemSpeechSynthesizer | None = None,
    ) -> NarrationGenerationResult:
        """Synthesize exact Script text locally and record one immutable terminal attempt."""

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

    @staticmethod
    def _srt(cues: list[dict[str, Any]]) -> str:
        def stamp(milliseconds: int) -> str:
            seconds, millis = divmod(milliseconds, 1000)
            minutes, seconds = divmod(seconds, 60)
            hours, minutes = divmod(minutes, 60)
            return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"

        return "\n\n".join(
            f"{index}\n{stamp(cue['start_ms'])} --> {stamp(cue['end_ms'])}\n{cue['text']}"
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
            f"[{current}]trim=duration={total_duration_ms / 1000:.3f},"
            "setpts=PTS-STARTPTS[composed]"
        )
        filters.append(
            "[composed]subtitles=captions.srt:"
            "force_style='FontSize=42,Alignment=2,MarginV=130,PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00101010,BorderStyle=1,Outline=3'[captioned]"
        )
        return filters

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
            subtitle.write_text(self._srt(snapshot.caption_cues), encoding="utf-8")
            arguments = [self.runtime.ffmpeg_path, "-y"]
            for item in snapshot.scene_inputs:
                asset = self.repository.get_asset(item["asset_id"])
                path = self.repository.managed_asset_path(asset.id)
                if sha256(path.read_bytes()).hexdigest() != item["content_digest"]:
                    raise MediaRuntimeError(
                        "Managed selected Asset bytes do not match their frozen digest."
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
            output = temporary_root / "output.mp4"
            arguments.extend(
                [
                    "-filter_complex",
                    ";".join(filters),
                    "-map",
                    "[captioned]",
                    "-map",
                    f"{len(snapshot.scene_inputs)}:a",
                    "-t",
                    f"{narration.duration_ms / 1000:.3f}",
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
