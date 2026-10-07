"""Canonical HTTP-facing composition of the persistent-scene v2 production lifecycle."""

from __future__ import annotations

import json
import re
import shutil
import tempfile
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from typing import Any

from project_atlas import speech_timing
from project_atlas.generation import GenerationService
from project_atlas.media import FfmpegRuntime, MediaService
from project_atlas.narration import SIMILARSTOIC_PRONUNCIATION_ALIASES
from project_atlas.narration_verification import (
    NORMALIZATION_VERSION,
    VERIFICATION_METHOD,
    WhisperTranscriber,
    verify_narration_audio,
)
from project_atlas.persistence import AtlasRepository
from project_atlas.scene_media import load_persistent_scene_frame, unwritten_alpha_pixels
from project_atlas.scene_model import (
    Affine,
    Camera,
    DomainBindings,
    EntityDefinition,
    EntityVariant,
    GeometryContract,
    Operation,
    PersistenceClass,
    PersistentWorld,
    Plane,
    RasterAsset,
    RenderSlice,
    TransitionIntent,
    base_state,
    bind_world_definition,
)

_SAFE_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
FRAME_SIZE = (1080, 1920)
SCENE_ADAPTER_VERSION = "managed-image-to-rgba-v2"
# Derived raster identities carry the adapter generation so a resume can never reuse a
# raster produced by an earlier adapter.
DERIVED_RASTER_NAMESPACE = "raster-v2"
# Full-frame sources may differ from 9:16 only by rounding (the approved 941x1672 is ~0.05% off).
FULL_FRAME_ASPECT_TOLERANCE = 0.005
FULL_FRAME_SCALE_FILTER = (
    "scale={width}:{height}:flags=lanczos+accurate_rnd+full_chroma_int+bitexact"
)


class ProductionLifecycleError(RuntimeError):
    """A fail-closed production-stage failure already recorded in run history."""

    def __init__(self, run_id: str, stage: str, message: str) -> None:
        super().__init__(message)
        self.run_id = run_id
        self.stage = stage


class ProductionRequestError(ValueError):
    """The external command does not describe one complete canonical production."""


def full_frame_aspect_error(width: int, height: int, target_size: tuple[int, int]) -> str | None:
    """Describe a full-frame source whose aspect differs from the frame beyond tolerance."""

    if abs((width / height) / (target_size[0] / target_size[1]) - 1) > FULL_FRAME_ASPECT_TOLERANCE:
        return (
            f"Full-frame source {width}x{height} is not within "
            f"{FULL_FRAME_ASPECT_TOLERANCE:.1%} of the {target_size[0]}x{target_size[1]} "
            "frame aspect."
        )
    return None


class ManagedAssetSceneAdapter:
    """Convert verified managed images into exact managed RGBA scene assets."""

    def __init__(self, repository: AtlasRepository, runtime: FfmpegRuntime) -> None:
        self.repository = repository
        self.runtime = runtime

    def source_dimensions(self, source_asset_id: str) -> tuple[int, int]:
        """Probe one managed image's decodable pixel dimensions."""

        source_path = self.repository.managed_asset_path(source_asset_id)
        probe = self.runtime._run(
            [
                self.runtime.ffprobe_path,
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height",
                "-of",
                "json",
                str(source_path),
            ]
        )
        streams = json.loads(probe.stdout).get("streams", [])
        if len(streams) != 1:
            raise ValueError("Managed acquisition must contain one decodable image stream.")
        width, height = streams[0].get("width"), streams[0].get("height")
        if not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0:
            raise ValueError("Managed acquisition has invalid image dimensions.")
        return width, height

    def adapt(
        self,
        run_id: str,
        source_asset_id: str,
        derived_asset_id: str,
        target_size: tuple[int, int] | None = None,
    ) -> RasterAsset:
        """Decode one managed image, resampling full-frame rasters to exact frame pixels."""

        source = self.repository.get_asset(source_asset_id)
        try:
            existing = self.repository.get_asset(derived_asset_id)
        except KeyError:
            existing = None
        if existing is not None:
            if existing.metadata.get("source_asset_id") != source.id:
                raise ValueError("Derived scene identity is already bound to another source.")
            if existing.metadata.get("adapter") != SCENE_ADAPTER_VERSION:
                raise ValueError("Derived scene identity was produced by another adapter version.")
            content = self.repository.managed_scene_asset_path(existing.id).read_bytes()
            width, height = existing.metadata.get("width"), existing.metadata.get("height")
            if not isinstance(width, int) or not isinstance(height, int):
                raise ValueError("Derived scene Asset dimensions are missing.")
            return RasterAsset(existing.id, width, height, content, existing.content_digest or "")
        source_path = self.repository.managed_asset_path(source.id)
        source_bytes = source_path.read_bytes()
        if (
            source.content_digest is None
            or sha256(source_bytes).hexdigest() != source.content_digest
        ):
            raise ValueError("Managed acquisition bytes do not match their persisted digest.")
        temporary_root = Path(tempfile.mkdtemp(prefix="conveyor-scene-adapter-"))
        try:
            source_width, source_height = self.source_dimensions(source.id)
            if target_size is not None:
                # Defense in depth: acquisition already refuses off-aspect full-frame sources.
                aspect_error = full_frame_aspect_error(source_width, source_height, target_size)
                if aspect_error is not None:
                    raise ValueError(aspect_error)
            width, height = target_size or (source_width, source_height)
            scale_filter = (
                FULL_FRAME_SCALE_FILTER.format(width=width, height=height)
                if target_size is not None
                else None
            )
            raw_path = temporary_root / "frame.rgba"
            self.runtime._run(
                [
                    self.runtime.ffmpeg_path,
                    "-y",
                    "-threads",
                    "1",
                    "-i",
                    str(source_path),
                    "-frames:v",
                    "1",
                    *(["-vf", f"{scale_filter},format=rgba"] if scale_filter else []),
                    "-pix_fmt",
                    "rgba",
                    "-f",
                    "rawvideo",
                    str(raw_path),
                ]
            )
            rgba = raw_path.read_bytes()
            if len(rgba) != width * height * 4:
                raise ValueError("Decoded scene raster dimensions do not match its bytes.")
        finally:
            shutil.rmtree(temporary_root, ignore_errors=True)
        digest = sha256(rgba).hexdigest()
        storage_name = sha256(derived_asset_id.encode()).hexdigest()
        relative = Path("persistent-derived") / run_id / f"{storage_name}.rgba"
        target = (self.repository.asset_storage_root / relative).resolve()
        if self.repository.asset_storage_root not in target.parents:
            raise ValueError("Derived scene asset path escaped managed storage.")
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with target.open("xb") as stream:
                stream.write(rgba)
        except FileExistsError as error:
            raise ValueError(
                "Derived scene asset already exists without persisted evidence."
            ) from error
        try:
            version = self.repository.connection.execute(
                "SELECT COALESCE(MAX(version), 0) + 1 FROM assets WHERE asset_spec_id=?",
                (source.asset_spec_id,),
            ).fetchone()[0]
            self.repository.create_asset(
                derived_asset_id,
                source.asset_spec_id,
                version,
                relative.as_posix(),
                "application/x-rgba",
                "derived",
                {
                    "adapter": SCENE_ADAPTER_VERSION,
                    "source_asset_id": source.id,
                    "source_content_digest": source.content_digest,
                    "source_width": source_width,
                    "source_height": source_height,
                    "width": width,
                    "height": height,
                    "scale_method": "ffmpeg-lanczos-bitexact" if scale_filter else "none",
                    "scale_filter": scale_filter,
                    "renderer_version": self.runtime.version(self.runtime.ffmpeg_path),
                },
                digest,
            )
        except Exception:
            target.unlink(missing_ok=True)
            raise
        return RasterAsset(derived_asset_id, width, height, rgba, digest)


class ProductionLifecycleService:
    """Own cross-stage progression while delegating all domain work to canonical services."""

    def __init__(
        self,
        repository: AtlasRepository,
        generation_service: GenerationService,
        media_service: MediaService,
        transcriber: Any | None = None,
    ) -> None:
        self.repository = repository
        self.generation_service = generation_service
        self.media_service = media_service
        # Independent recognizer for the narration completeness gate (never the TTS provider).
        self.transcriber = transcriber or WhisperTranscriber()
        self.adapter = ManagedAssetSceneAdapter(repository, media_service.runtime)

    def start(self, request: dict[str, Any]) -> dict[str, Any]:
        normalized = self._validate_request(request)
        run_id = normalized["id"]
        try:
            existing = self.repository.get_production_run(run_id)
        except KeyError:
            run = self.repository.create_production_run(
                run_id, normalized["visual_plan_id"], normalized
            )
        else:
            frozen = json.dumps(
                normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
            if existing.request_digest != sha256(frozen.encode()).hexdigest():
                raise ProductionRequestError(
                    "Production identity already exists with a different immutable request."
                )
            return self.status(run_id)
        self._acquire(run)
        return self.status(run_id)

    def authorize_narration(self, run_id: str, evidence: dict[str, Any]) -> dict[str, Any]:
        """Record a durable founder narration authorization without touching the frozen request.

        Idempotent: a run that is already authorized (by its request or an earlier record)
        returns its status without a new record.
        """

        run = self.repository.get_production_run(run_id)
        if not isinstance(evidence, dict):
            raise ProductionRequestError("Narration authorization requires an evidence object.")
        actor = evidence.get("authorized_by")
        if not isinstance(actor, str) or not actor.strip():
            raise ProductionRequestError("Narration authorization requires authorized_by.")
        if not self._narration_authorized(run):
            self.repository.create_production_evidence(
                f"{run_id}:narration-authorization:1",
                run_id,
                "narration_authorization",
                evidence | {"authorized_by": actor.strip()},
            )
        return self.status(run_id)

    def _narration_authorized(self, run: Any) -> bool:
        return run.request.get("narration_authorized") is True or bool(
            self.repository.list_production_evidence(run.id, "narration_authorization")
        )

    def authorize_narration_verification(
        self, run_id: str, evidence: dict[str, Any]
    ) -> dict[str, Any]:
        """Record founder authority for one completeness check of one exact narration take.

        Needed only by requests frozen before the verification forecast existed; such runs
        never receive transcription spend authority implicitly. Idempotent per take.
        """

        self.repository.get_production_run(run_id)
        actor, asset_id = self._authorization_fields(
            evidence, "narration_asset_id", "Narration verification authorization"
        )
        attempt = self._narration_attempt_for_asset(run_id, asset_id)
        if self._narration_verification(run_id, attempt) is not None:
            raise ProductionRequestError(
                "That narration take was already verified; verification is never repeated."
            )
        existing = self.repository.list_production_evidence(
            run_id, "narration_verification_authorization"
        )
        if not any(item.narration_asset_id == asset_id for item in existing):
            self.repository.create_production_evidence(
                f"{run_id}:narration-verification-authorization:{len(existing) + 1}",
                run_id,
                "narration_verification_authorization",
                evidence | {"authorized_by": actor, "narration_asset_id": asset_id},
                narration_asset_id=asset_id,
            )
        return self.status(run_id)

    def authorize_narration_retake(self, run_id: str, evidence: dict[str, Any]) -> dict[str, Any]:
        """Record one founder authorization for exactly one replacement narration take."""

        self.repository.get_production_run(run_id)
        actor, asset_id = self._authorization_fields(
            evidence, "defective_narration_asset_id", "Narration retake authorization"
        )
        reason = evidence.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise ProductionRequestError("Narration retake authorization requires a reason.")
        self._narration_attempt_for_asset(run_id, asset_id)
        existing = self.repository.list_production_evidence(
            run_id, "narration_retake_authorization"
        )
        self.repository.create_production_evidence(
            f"{run_id}:narration-retake-authorization:{len(existing) + 1}",
            run_id,
            "narration_retake_authorization",
            evidence
            | {
                "run_id": run_id,
                "authorized_by": actor,
                "defective_narration_asset_id": asset_id,
                "reason": reason.strip(),
            },
            narration_asset_id=asset_id,
        )
        return self.status(run_id)

    def retake_narration(self, run_id: str) -> dict[str, Any]:
        """Replace a defective narration take with the next versioned, verified take.

        Bounded recovery inside the same run: the approved Script, accepted imagery, worlds and
        scene states are reused, no image provider is reachable, one founder authorization
        permits one provider take (and its one completeness check), and every earlier take,
        snapshot, render and review stays immutable history. A passing take produces a new
        narration-bound snapshot/render/cell-QA candidate; a failing take stops the run.
        """

        run = self.repository.get_production_run(run_id)
        latest = self.repository.latest_production_run_event(run_id)
        eligible = latest is not None and (
            (latest.status == "qa_review_pending" and latest.stage == "qa")
            or (
                latest.status == "failed"
                and latest.stage == "qa"
                and latest.error_code == "whole_video_qa_failed"
            )
            or (latest.status == "failed" and latest.stage == "narration_verification")
        )
        if not eligible:
            raise ProductionRequestError(
                "A narration retake requires a production awaiting or failing whole-video "
                "review, or one stopped by a failed narration verification."
            )
        if not self._all_variants_passed(run):
            raise ProductionRequestError(
                "A narration retake requires every acquired variant to be accepted."
            )
        if self._founder_review_payload(run_id) is not None:
            raise ProductionRequestError("A narration retake is refused after a founder decision.")
        if self._render_artifacts_published(run_id):
            raise ProductionRequestError("A narration retake is refused once a render is packaged.")
        current = self._current_narration_attempt(run_id)
        if current is None or current.narration_asset_id is None:
            raise ProductionRequestError("There is no narration take to replace.")
        consumed = {
            attempt.payload.get("retake_authorization_id")
            for attempt in self._narration_attempts(run_id)
        }
        authorization = next(
            (
                item
                for item in sorted(
                    self.repository.list_production_evidence(
                        run_id, "narration_retake_authorization"
                    ),
                    key=self._evidence_version,
                )
                if item.id not in consumed
            ),
            None,
        )
        if authorization is None:
            raise ProductionRequestError(
                "A narration retake requires an unconsumed founder retake authorization; "
                "no provider call made."
            )
        if authorization.narration_asset_id != current.narration_asset_id:
            raise ProductionRequestError(
                "The retake authorization names a different narration take than the current one."
            )
        version = self._next_narration_version(run_id)
        self.repository.append_production_run_event(
            run_id,
            "narrating",
            "narration_retake",
            {"narration_version": version, "retake_authorization_id": authorization.id},
        )
        try:
            states = self._ensure_scene_states(run)
            attempt = self._generate_narration_attempt(run, version, authorization.id)
            self._admit_narration(run, attempt)
            narration = self.repository.get_narration_asset(attempt.narration_asset_id)
            snapshot = self._ensure_snapshot(run, states, narration)
            artifact = self._ensure_render(run, snapshot)
            self._ensure_automated_cell_qa(run, states, artifact)
            self.repository.append_production_run_event(
                run_id,
                "qa_review_pending",
                "qa",
                {
                    "artifact_id": artifact.id,
                    "narration_version": version,
                    "whole_video_review": "pending",
                },
            )
        except Exception as error:
            stopped = self.repository.latest_production_run_event(run_id)
            self._fail(run_id, stopped.stage if stopped else "narration_retake", error)
        return self.status(run_id)

    # --- Versioned narration attempts and the completeness gate ---------------------------

    @staticmethod
    def _authorization_fields(evidence: Any, asset_field: str, label: str) -> tuple[str, str]:
        if not isinstance(evidence, dict):
            raise ProductionRequestError(f"{label} requires an evidence object.")
        actor, asset_id = evidence.get("authorized_by"), evidence.get(asset_field)
        if not isinstance(actor, str) or not actor.strip():
            raise ProductionRequestError(f"{label} requires authorized_by.")
        if not isinstance(asset_id, str) or not asset_id.strip():
            raise ProductionRequestError(f"{label} requires {asset_field}.")
        return actor.strip(), asset_id.strip()

    def _narration_attempts(self, run_id: str) -> list[Any]:
        return sorted(
            self.repository.list_production_evidence(run_id, "narration"),
            key=self._evidence_version,
        )

    def _current_narration_attempt(self, run_id: str) -> Any | None:
        attempts = self._narration_attempts(run_id)
        return attempts[-1] if attempts else None

    def _narration_attempt_for_asset(self, run_id: str, asset_id: str) -> Any:
        for attempt in self._narration_attempts(run_id):
            if attempt.narration_asset_id == asset_id:
                return attempt
        raise ProductionRequestError("The named narration asset is not a take of this run.")

    def _narration_verification(self, run_id: str, attempt: Any) -> Any | None:
        identity = f"{run_id}:narration_verification:{self._evidence_version(attempt)}"
        for item in self.repository.list_production_evidence(run_id, "narration_verification"):
            if item.id == identity:
                return item
        return None

    def _next_narration_version(self, run_id: str) -> int:
        """Next take version: never reuses an attempt, verification or provider identity."""

        versions = [
            self._evidence_version(item)
            for item in self.repository.list_production_evidence(run_id)
            if item.evidence_type in {"narration", "narration_verification"}
        ]
        version = 1 + max(versions, default=0)

        def exists(getter, identity: str) -> bool:
            try:
                getter(identity)
            except KeyError:
                return False
            return True

        while exists(
            self.repository.get_narration_generation_execution,
            f"{run_id}:narration-execution:{version}",
        ) or exists(self.repository.get_narration_asset, f"{run_id}-narration-{version}"):
            version += 1
        return version

    def _generate_narration_attempt(
        self, run: Any, version: int, retake_authorization_id: str | None = None
    ) -> Any:
        """Make exactly one provider narration call and record it as one versioned take."""

        plan = self.repository.get_visual_plan(run.visual_plan_id)
        result = self.media_service.generate_brand_narration(
            f"{run.id}:narration-execution:{version}",
            f"{run.id}-narration-{version}",
            plan.script_id,
            brand_key="similarstoic",
            execution_authorized=True,
        )
        payload = {
            "outcome": result.execution.outcome,
            "brand_key": "similarstoic",
            "narration_version": version,
        }
        if retake_authorization_id is not None:
            payload["retake_authorization_id"] = retake_authorization_id
        attempt = self.repository.create_production_evidence(
            f"{run.id}:narration:evidence:{version}",
            run.id,
            "narration",
            payload,
            narration_generation_execution_id=result.execution.id,
            narration_asset_id=result.narration_asset.id if result.narration_asset else None,
        )
        if result.narration_asset is None:
            raise RuntimeError("Approved SimilarStoic narration generation failed.")
        return attempt

    def _verification_allowed(self, run: Any, attempt: Any) -> bool:
        """A take's single check is planned, retake-covered or separately authorized."""

        if attempt.payload.get("retake_authorization_id"):
            return True
        if (
            self._evidence_version(attempt) == 1
            and run.request["forecast"].get("verification_calls") == 1
        ):
            return True
        return any(
            item.narration_asset_id == attempt.narration_asset_id
            for item in self.repository.list_production_evidence(
                run.id, "narration_verification_authorization"
            )
        )

    def _verify_narration_attempt(self, run: Any, attempt: Any) -> Any:
        """Run (at most once per take) and record the independent completeness check."""

        existing = self._narration_verification(run.id, attempt)
        if existing is not None:
            return existing
        version = self._evidence_version(attempt)
        self.repository.append_production_run_event(
            run.id, "narrating", "narration_verification", {"narration_version": version}
        )
        if not self._verification_allowed(run, attempt):
            raise ProductionRequestError(
                "Narration completeness verification is not authorized; no provider call made."
            )
        narration = self.repository.get_narration_asset(attempt.narration_asset_id)
        script = self.repository.get_script(narration.script_id)
        try:
            report = verify_narration_audio(
                self.media_service.storage.path(narration.storage_path),
                narration.content_digest,
                script.narration_text,
                self.transcriber,
                SIMILARSTOIC_PRONUNCIATION_ALIASES,
            )
        except Exception as error:
            # A failed check is recorded so the same take is never transcribed again.
            report = {
                "method": VERIFICATION_METHOD,
                "outcome": "error",
                "error_code": type(error).__name__,
                "error": str(error)[:1000],
            }
        return self.repository.create_production_evidence(
            f"{run.id}:narration_verification:{version}",
            run.id,
            "narration_verification",
            {
                "narration_version": version,
                "narration_asset_id": narration.id,
                "narration_execution_id": attempt.narration_generation_execution_id,
                "normalization_version": NORMALIZATION_VERSION,
                "wav_sha256": narration.content_digest,
                **report,
            },
            narration_generation_execution_id=attempt.narration_generation_execution_id,
            narration_asset_id=narration.id,
        )

    def _admit_narration(self, run: Any, attempt: Any) -> None:
        """Fail closed unless this take passed its completeness check."""

        verification = self._verify_narration_attempt(run, attempt)
        if verification.payload.get("outcome") == "passed":
            return
        payload = verification.payload
        if payload.get("outcome") == "error":
            detail = payload.get("error", "verification error")
        else:
            detail = "; ".join(
                f"{item['kind']}: expected {' '.join(item['expected']) or '-'} / "
                f"heard {' '.join(item['observed']) or '-'}"
                for item in payload.get("differences", [])[:5]
            )
        raise ProductionRequestError(
            f"Narration take {payload.get('narration_version')} failed completeness "
            f"verification ({detail}); a separately authorized narration retake is required."
        )

    def _require_verified_narration(self, run_id: str, narration: Any) -> None:
        """Backstop: only the current, verified take may feed a snapshot, render or retime."""

        attempt = self._current_narration_attempt(run_id)
        verification = self._narration_verification(run_id, attempt) if attempt else None
        if (
            attempt is None
            or attempt.narration_asset_id != narration.id
            or verification is None
            or verification.narration_asset_id != narration.id
            or verification.payload.get("outcome") != "passed"
        ):
            raise ProductionRequestError(
                "The current narration has no passing completeness verification; it cannot "
                "feed a snapshot, render or retime."
            )

    def resume(self, run_id: str) -> dict[str, Any]:
        run = self.repository.get_production_run(run_id)
        latest = self.repository.latest_production_run_event(run_id)
        if latest is None:
            raise ProductionRequestError("Production has no lifecycle event.")
        if latest.status == "failed" and latest.stage in {"acquisition", "acquisition_review"}:
            # Reacquire only missing variants and variants whose active asset was rejected.
            self._acquire(run)
        elif latest.status in {
            "acquisition_review_pending",
            "qa_review_pending",
            "private_founder_review_ready",
            "founder_accepted",
            "founder_rejected",
        }:
            return self.status(run_id)
        elif latest.status == "failed":
            if not self._all_variants_passed(run):
                raise ProductionRequestError("Acquisition approval is required before resuming.")
            self._assemble_and_render(run)
        return self.status(run_id)

    def review_acquisition(self, run_id: str, reviews: list[dict[str, Any]]) -> dict[str, Any]:
        run = self.repository.get_production_run(run_id)
        latest = self.repository.latest_production_run_event(run_id)
        if latest is None or latest.status != "acquisition_review_pending":
            if self._all_variants_passed(run):
                return self.status(run_id)
            raise ProductionRequestError("Production is not awaiting acquisition review.")
        acquired = self._acquisition_map(run_id)
        if set(acquired) != set(self._variant_keys(run.request)):
            raise ProductionRequestError("Every variant must be acquired before review.")
        # Only active assets without a review need review; earlier passes stay valid.
        states = self._variant_review_states(run)
        expected = {key for key, state in states.items() if state == "pending"}
        review_round = self._next_acquisition_review_round(run_id)
        supplied: dict[tuple[str, str, str], dict[str, Any]] = {}
        for review in reviews:
            if not isinstance(review, dict):
                raise ProductionRequestError("Acquisition reviews must be objects.")
            key = tuple(review.get(name, "") for name in ("world_key", "entity_key", "variant_key"))
            if len(key) != 3 or not all(isinstance(item, str) for item in key) or key in supplied:
                raise ProductionRequestError(
                    "Acquisition review identity is invalid or duplicated."
                )
            supplied[key] = review
        if set(supplied) != expected:
            raise ProductionRequestError(
                "Acquisition review must cover exactly the variants awaiting review."
            )
        for review in supplied.values():
            if review.get("outcome") not in {"passed", "failed"} or not isinstance(
                review.get("evidence"), dict
            ):
                raise ProductionRequestError("Acquisition review requires outcome and evidence.")
        any_failed = False
        for index, key in enumerate(sorted(expected), 1):
            review = supplied[key]
            outcome = review["outcome"]
            evidence = review["evidence"]
            self.repository.create_production_qa_review(
                f"{run_id}:qa:acquisition:round-{review_round}:{index}",
                run_id,
                "acquisition",
                outcome,
                "human",
                {"profile": "similarstoic-raw-world-acquisition-v1"},
                evidence | {"asset_id": acquired[key]["asset_id"], "variant": key},
            )
            any_failed |= outcome == "failed"
        if any_failed:
            self.repository.append_production_run_event(
                run_id,
                "failed",
                "acquisition_review",
                {"review_count": len(reviews), "review_round": review_round},
                error_code="acquisition_rejected",
                error_message="One or more acquired assets failed required review.",
            )
            return self.status(run_id)
        self._assemble_and_render(run)
        return self.status(run_id)

    def record_qa(self, run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        latest = self.repository.latest_production_run_event(run_id)
        if latest is None or latest.status != "qa_review_pending":
            if latest and latest.status in {
                "private_founder_review_ready",
                "founder_accepted",
                "founder_rejected",
            }:
                return self.status(run_id)
            raise ProductionRequestError("Production is not awaiting whole-video review.")
        outcome, evidence = payload.get("outcome"), payload.get("evidence")
        if outcome not in {"passed", "failed"} or not isinstance(evidence, dict):
            raise ProductionRequestError("Whole-video review requires outcome and evidence.")
        # Human whole-video review always binds to the current (latest) render.
        artifact = self._current_evidence(run_id, "render").final_media_artifact_id
        previous = [
            review
            for review in self.repository.list_production_qa_reviews(run_id)
            if review.scope == "whole_video"
        ]
        self.repository.create_production_qa_review(
            f"{run_id}:qa:whole-video:{len(previous) + 1}",
            run_id,
            "whole_video",
            outcome,
            "human",
            dict(MediaService.WHOLE_VIDEO_QA_PROFILE),
            evidence,
            artifact,
        )
        if outcome == "passed":
            self.repository.append_production_run_event(
                run_id,
                "private_founder_review_ready",
                "qa",
                {"artifact_id": artifact, "founder_review": "pending"},
            )
        else:
            self.repository.append_production_run_event(
                run_id,
                "failed",
                "qa",
                {"artifact_id": artifact},
                error_code="whole_video_qa_failed",
                error_message="Whole-video review did not pass.",
            )
        return self.status(run_id)

    def founder_review(self, run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        outcome = payload.get("outcome")
        if outcome not in {"accepted", "rejected"}:
            raise ProductionRequestError("Founder outcome must be accepted or rejected.")
        for field in ("founder_actor", "decision_reference", "notes"):
            if not isinstance(payload.get(field), str) or (
                field != "notes" and not payload[field].strip()
            ):
                raise ProductionRequestError(f"Founder review {field} is required text.")
        self.repository.create_production_founder_review(
            f"{run_id}:founder-review:1",
            run_id,
            outcome,
            payload["founder_actor"],
            payload["decision_reference"],
            payload["notes"],
        )
        return self.status(run_id)

    def recommend_retime(self, run_id: str) -> dict[str, Any]:
        """Recommend narration-aligned scene durations; read-only and applies nothing.

        Each scene boundary sits at the pause ending that scene's narration excerpt, measured on
        the run's persisted narration. Applying it remains a separate founder-approved retime.
        """

        run = self.repository.get_production_run(run_id)
        if not self.repository.list_production_evidence(run_id, "narration"):
            raise ProductionRequestError("Production has no narration to align scene timing to.")
        narration = self.repository.get_narration_asset(
            self._current_evidence(run_id, "narration").narration_asset_id
        )
        # Timing is always recomputed from the current verified take, never a previous one.
        self._require_verified_narration(run_id, narration)
        plan = self.repository.get_visual_plan(run.visual_plan_id)
        script = self.repository.get_script(plan.script_id)
        scenes = self.repository.list_scenes_for_visual_plan(run.visual_plan_id)
        timing = self.media_service.narration_speech_timing(narration, script.narration_text)
        try:
            recommendation = speech_timing.recommend_scene_durations(
                timing, [scene.narration_excerpt for scene in scenes]
            )
        except ValueError as error:
            raise ProductionRequestError(str(error)) from error
        snapshots = self.repository.list_production_evidence(run_id, "snapshot")
        current = (
            self.repository.get_final_media_input_snapshot(
                self._current_evidence(run_id, "snapshot").final_media_input_snapshot_id
            )
            if snapshots
            else None
        )
        return {
            "run_id": run_id,
            "narration_asset_id": narration.id,
            "narration_duration_ms": narration.duration_ms,
            "scene_ids": [scene.id for scene in scenes],
            "current_durations_ms": (
                [item["duration_ms"] for item in current.scene_inputs] if current else None
            ),
            "recommended_durations_ms": recommendation["durations_ms"],
            "boundaries": recommendation["boundaries"],
            "pauses": [
                {"start_ms": round(pause.start_ms), "end_ms": round(pause.end_ms)}
                for pause in timing.pauses
            ],
            "timing_evidence": {
                **speech_timing.timing_evidence(timing),
                "silence_detection": dict(self.media_service.runtime.SILENCE_DETECTION),
            },
        }

    def retime(
        self, run_id: str, durations_ms: list[int], actor: str, reason: str
    ) -> dict[str, Any]:
        """Re-render approved images and persisted narration with new absolute beat timing.

        A bounded post-narration operation: no image or narration provider is reachable, every
        earlier snapshot, render and review is preserved, and the new render becomes current
        for the next human whole-video review.
        """

        run = self.repository.get_production_run(run_id)
        latest = self.repository.latest_production_run_event(run_id)
        retimeable = latest is not None and (
            (latest.status == "qa_review_pending" and latest.stage == "qa")
            or (
                latest.status == "failed"
                and latest.stage == "qa"
                and latest.error_code == "whole_video_qa_failed"
            )
        )
        if not retimeable or self._founder_review_payload(run_id) is not None:
            raise ProductionRequestError(
                "Retiming requires a production awaiting or failing whole-video review."
            )
        for field, value in (("actor", actor), ("reason", reason)):
            if not isinstance(value, str) or not value.strip():
                raise ProductionRequestError(f"Retime {field} is required text.")
        scene_ids = self._plan_scene_ids(run.visual_plan_id)
        if not isinstance(durations_ms, list) or len(durations_ms) != len(scene_ids):
            raise ProductionRequestError("Retime requires exactly one duration per Scene.")
        if any(
            not isinstance(value, int) or isinstance(value, bool) or value <= 0
            for value in durations_ms
        ):
            raise ProductionRequestError("Retime durations must be positive integer milliseconds.")
        narration = self.repository.get_narration_asset(
            self._current_evidence(run_id, "narration").narration_asset_id
        )
        self._require_verified_narration(run_id, narration)
        if sum(durations_ms) != narration.duration_ms:
            raise ProductionRequestError(
                f"Retime durations must sum exactly to the narration's {narration.duration_ms} ms."
            )
        source_render = self._current_evidence(run_id, "render")
        if self._render_artifacts_published(run_id):
            raise ProductionRequestError("Retiming is refused once a render has been packaged.")
        # The source snapshot is the one that produced the current render (same version), never
        # an independently newer snapshot left behind by an incomplete render attempt.
        source_version = self._evidence_version(source_render)
        matching = [
            item
            for item in self.repository.list_production_evidence(run_id, "snapshot")
            if self._evidence_version(item) == source_version
        ]
        if len(matching) != 1:
            raise ProductionRequestError(
                "Current render has no matching snapshot evidence of the same version."
            )
        source_snapshot = self.repository.get_final_media_input_snapshot(
            matching[0].final_media_input_snapshot_id
        )
        states = {
            item.payload["scene_id"]: item.resolved_state_id
            for item in self.repository.list_production_evidence(run_id, "scene_state")
        }
        if [item["scene_id"] for item in source_snapshot.scene_inputs] != scene_ids or any(
            states.get(item["scene_id"]) != item["resolved_state_id"]
            for item in source_snapshot.scene_inputs
        ):
            raise ProductionRequestError(
                "Current snapshot does not match the run's approved states."
            )
        version = self._next_render_version(run_id)
        inputs = [
            {
                "scene_id": item["scene_id"],
                "resolved_state_id": item["resolved_state_id"],
                "duration_ms": duration,
                "motion": item["motion"],
                "transition_to_next": item["transition_to_next"],
            }
            for item, duration in zip(source_snapshot.scene_inputs, durations_ms, strict=True)
        ]
        self.repository.append_production_run_event(
            run_id, "rendering", "retime", {"render_version": version}
        )
        try:
            snapshot = self.media_service.create_persistent_scene_snapshot(
                f"{run.id}:snapshot:{version}",
                run.visual_plan_id,
                narration.id,
                inputs,
                run.request.get("citations"),
            )
            self.repository.create_production_evidence(
                f"{run.id}:snapshot:evidence:{version}",
                run.id,
                "snapshot",
                {"schema_version": snapshot.snapshot_schema_version, "render_version": version},
                final_media_input_snapshot_id=snapshot.id,
            )
            artifact = self.media_service.render(
                f"{run.id}:render-execution:{version}", f"{run.id}-artifact-{version}", snapshot.id
            )
            self.repository.create_production_evidence(
                f"{run.id}:render:evidence:{version}",
                run.id,
                "render",
                {"technical_validation": artifact.technical_validation, "render_version": version},
                render_execution_id=artifact.render_execution_id,
                final_media_artifact_id=artifact.id,
            )
            self._record_automated_cell_qa(
                run,
                {item["scene_id"]: item["resolved_state_id"] for item in inputs},
                artifact,
                f"{run.id}:qa:cell:{version}",
            )
            self.repository.create_production_evidence(
                f"{run.id}:retime:evidence:{version}",
                run.id,
                "retime",
                {
                    "actor": actor.strip(),
                    "reason": reason.strip(),
                    "durations_ms": list(durations_ms),
                    "scene_ids": scene_ids,
                    "narration_asset_id": narration.id,
                    "narration_content_digest": narration.content_digest,
                    "narration_duration_ms": narration.duration_ms,
                    "source_render_version": self._evidence_version(source_render),
                    "source_final_media_artifact_id": source_render.final_media_artifact_id,
                    "source_final_media_input_snapshot_id": source_snapshot.id,
                    "render_version": version,
                    "final_media_artifact_id": artifact.id,
                },
                narration_asset_id=narration.id,
                final_media_input_snapshot_id=snapshot.id,
                render_execution_id=artifact.render_execution_id,
                final_media_artifact_id=artifact.id,
            )
            self.repository.append_production_run_event(
                run.id,
                "qa_review_pending",
                "qa",
                {
                    "artifact_id": artifact.id,
                    "render_version": version,
                    "whole_video_review": "pending",
                },
            )
        except Exception as error:
            self._fail(run.id, "retime", error)
        return self.status(run_id)

    def status(self, run_id: str) -> dict[str, Any]:
        run = self.repository.get_production_run(run_id)
        latest = self.repository.latest_production_run_event(run_id)
        evidence = self.repository.list_production_evidence(run_id)
        reviews = self.repository.list_production_qa_reviews(run_id)
        renders = [item for item in evidence if item.evidence_type == "render"]
        current = max(renders, key=self._evidence_version) if renders else None
        narration = self._current_narration_attempt(run_id)
        verification = self._narration_verification(run_id, narration) if narration else None
        return {
            "id": run.id,
            "visual_plan_id": run.visual_plan_id,
            "request_digest": run.request_digest,
            "status": latest.status if latest else "unknown",
            "stage": latest.stage if latest else "unknown",
            "error": (
                {"code": latest.error_code, "message": latest.error_message}
                if latest and latest.status == "failed"
                else None
            ),
            "evidence": [self._evidence_payload(item) for item in evidence],
            "qa_reviews": [asdict(item) for item in reviews],
            "founder_review": self._founder_review_payload(run_id),
            "narration_authorized": self._narration_authorized(run),
            "current_narration": (
                {
                    "version": self._evidence_version(narration),
                    "narration_asset_id": narration.narration_asset_id,
                    "verification": verification.payload.get("outcome") if verification else None,
                }
                if narration
                else None
            ),
            "current_render": (
                {
                    "version": self._evidence_version(current),
                    "final_media_artifact_id": current.final_media_artifact_id,
                }
                if current
                else None
            ),
            "created_at": run.created_at,
        }

    def _acquire(self, run: Any) -> None:
        self.repository.append_production_run_event(run.id, "acquiring", "acquisition", {})
        states = self._variant_review_states(run)
        existing = {
            key: value
            for key, value in self._acquisition_map(run.id).items()
            if states.get(key) != "rejected"
        }
        attempt = len(self.repository.list_production_evidence(run.id, "acquisition"))
        ceiling = run.request["forecast"]["image_calls"]
        full_frame = self._full_frame_variant_keys(run.request)
        try:
            self._assert_generation_authority(run.request)
            for world_key, entity_key, variant_key, asset_spec_id in self._variant_specs(
                run.request
            ):
                key = (world_key, entity_key, variant_key)
                # Technically inadmissible results are retried for this variant only, within
                # the frozen ceiling; only admissible assets ever reach founder review.
                while key not in existing:
                    prior_calls = sum(
                        item.generation_execution_id is not None
                        for item in self.repository.list_production_evidence(run.id, "acquisition")
                    )
                    if prior_calls + 1 > ceiling:
                        raise ProductionRequestError(
                            f"Image-call ceiling of {ceiling} would be exceeded by another "
                            f"provider call; {prior_calls} calls already recorded for this run."
                        )
                    result = self.generation_service.generate_asset_spec(asset_spec_id)
                    attempt += 1
                    mismatch = self._execution_authority_mismatch(run.request, result.execution.id)
                    technical = (
                        full_frame_aspect_error(
                            *self.adapter.source_dimensions(result.asset.id), FRAME_SIZE
                        )
                        if mismatch is None and result.asset is not None and key in full_frame
                        else None
                    )
                    # Authority-mismatched or technically inadmissible executions still count
                    # as provider calls, but their assets are never admitted for review.
                    admitted = result.asset if mismatch is None and technical is None else None
                    payload = {
                        "world_key": world_key,
                        "entity_key": entity_key,
                        "variant_key": variant_key,
                        "asset_spec_id": asset_spec_id,
                        "outcome": result.execution.outcome,
                    }
                    if mismatch is not None:
                        payload["authority_mismatch"] = mismatch
                    if technical is not None:
                        payload["technical_rejection"] = technical
                    self.repository.create_production_evidence(
                        f"{run.id}:acquisition:attempt:{attempt}",
                        run.id,
                        "acquisition",
                        payload | ({"asset_id": admitted.id} if admitted else {}),
                        generation_execution_id=result.execution.id,
                        asset_id=admitted.id if admitted else None,
                    )
                    if mismatch is not None:
                        raise ProductionRequestError(mismatch)
                    if result.asset is None:
                        raise RuntimeError("Required managed-asset acquisition failed.")
                    if admitted is not None:
                        existing[key] = payload | {"asset_id": admitted.id}
            self.repository.append_production_run_event(
                run.id,
                "acquisition_review_pending",
                "acquisition_review",
                {"acquired_variants": len(existing)},
            )
        except Exception as error:
            self._fail(run.id, "acquisition", error)

    def _assemble_and_render(self, run: Any) -> None:
        if not self._all_variants_passed(run):
            raise ProductionRequestError(
                "Every active acquired variant needs a passing human review before assembly."
            )
        try:
            states = self._ensure_scene_states(run)
            narration = self._ensure_narration(run)
            snapshot = self._ensure_snapshot(run, states, narration)
            artifact = self._ensure_render(run, snapshot)
            self._ensure_automated_cell_qa(run, states, artifact)
            latest = self.repository.latest_production_run_event(run.id)
            if latest is None or latest.status != "qa_review_pending":
                self.repository.append_production_run_event(
                    run.id,
                    "qa_review_pending",
                    "qa",
                    {"artifact_id": artifact.id, "whole_video_review": "pending"},
                )
        except Exception as error:
            latest = self.repository.latest_production_run_event(run.id)
            stage = latest.stage if latest else "assembly"
            self._fail(run.id, stage, error)

    def _ensure_scene_states(self, run: Any) -> dict[str, str]:
        existing = self.repository.list_production_evidence(run.id, "scene_state")
        expected_scenes = self._plan_scene_ids(run.visual_plan_id)
        if len(existing) == len(expected_scenes):
            return {item.payload["scene_id"]: item.resolved_state_id for item in existing}
        self.repository.append_production_run_event(run.id, "assembling", "assembly", {})
        acquisition = self._acquisition_map(run.id)
        state_ids: dict[str, str] = {}
        completed_worlds = {
            item.payload["world_key"]
            for item in self.repository.list_production_evidence(run.id, "world")
        }
        for world_index, world_input in enumerate(run.request["worlds"], 1):
            world_id = f"{run.id}:world:{world_index}"
            if world_input["key"] in completed_worlds:
                for scene_id in world_input["scene_ids"]:
                    state_id = f"{run.id}:state:{scene_id}"
                    self.repository.get_persistent_scene_state(state_id)
                    state_ids[scene_id] = state_id
                continue
            world = self._build_world(run, world_input, world_index, acquisition)
            first_scene = world_input["scene_ids"][0]
            base = base_state(world, first_scene, f"{run.id}:state:{first_scene}")
            self.repository.create_persistent_scene_world(
                world_id,
                world,
                base,
                base_intent_id=f"{run.id}:intent:{first_scene}:base",
                base_catalog_id=f"{run.id}:catalog:{first_scene}:base",
                authorization_actor="canonical-v2-production-lifecycle",
                authorization_reference=f"production-run:{run.id}:acquisition-review",
            )
            state_ids[first_scene] = base.state_id
            predecessor = base
            for transition_index, transition in enumerate(world_input["transitions"], 1):
                scene_id = transition["scene_id"]
                intent = TransitionIntent(
                    f"{run.id}:intent:{scene_id}",
                    predecessor.state_digest,
                    scene_id,
                    tuple(
                        self._operation(run.id, world_index, operation)
                        for operation in transition["operations"]
                    ),
                    tuple(transition.get("allowed_derived_entities", [])),
                    transition["reason"],
                )
                predecessor = self.repository.resolve_and_persist_scene_state(
                    world_id,
                    predecessor.state_id,
                    intent,
                    f"{run.id}:state:{scene_id}",
                    authorization_actor="canonical-v2-production-lifecycle",
                    authorization_reference=f"production-run:{run.id}:transition:{transition_index}",
                )
                state_ids[scene_id] = predecessor.state_id
            self.repository.create_production_evidence(
                f"{run.id}:world:{world_index}:evidence",
                run.id,
                "world",
                {"world_key": world.world_key, "scene_ids": world_input["scene_ids"]},
                world_revision_id=world_id,
            )
        existing_scene_ids = {item.payload["scene_id"] for item in existing}
        for index, scene_id in enumerate(expected_scenes, 1):
            if scene_id in existing_scene_ids:
                continue
            self.repository.create_production_evidence(
                f"{run.id}:state:{index}:evidence",
                run.id,
                "scene_state",
                {"scene_id": scene_id},
                resolved_state_id=state_ids[scene_id],
            )
        return state_ids

    def _ensure_narration(self, run: Any) -> Any:
        """Return the current take only once it has passed the completeness gate.

        An existing take is never regenerated or overwritten: a failed or unverifiable take
        stops the run until a separately authorized retake produces the next version.
        """

        attempt = self._current_narration_attempt(run.id)
        if attempt is None:
            self.repository.append_production_run_event(run.id, "narrating", "narration", {})
            # The frozen request or a recorded founder authorization may authorize narration.
            if not self._narration_authorized(run):
                raise ProductionRequestError(
                    "Narration is not authorized by this production request; no provider call made."
                )
            attempt = self._generate_narration_attempt(run, self._next_narration_version(run.id))
        verification = self._narration_verification(run.id, attempt)
        latest = self.repository.latest_production_run_event(run.id)
        if (verification is None or verification.payload.get("outcome") != "passed") and (
            latest is None or latest.status != "narrating"
        ):
            # Re-entering an unadmitted take (e.g. on resume) is recorded, never repeated silently.
            self.repository.append_production_run_event(
                run.id,
                "narrating",
                "narration_verification",
                {"narration_version": self._evidence_version(attempt)},
            )
        if attempt.narration_asset_id is None:
            raise ProductionRequestError(
                f"Narration take {self._evidence_version(attempt)} produced no audio; a "
                "separately authorized narration retake is required."
            )
        self._admit_narration(run, attempt)
        return self.repository.get_narration_asset(attempt.narration_asset_id)

    def _ensure_snapshot(self, run: Any, states: dict[str, str], narration: Any) -> Any:
        """Return or create the snapshot bound to exactly this verified narration take."""

        self._require_verified_narration(run.id, narration)
        bound = []
        for item in self.repository.list_production_evidence(run.id, "snapshot"):
            snapshot = self.repository.get_final_media_input_snapshot(
                item.final_media_input_snapshot_id
            )
            if snapshot.narration_asset_id == narration.id:
                bound.append((self._evidence_version(item), snapshot))
        if bound:
            return max(bound, key=lambda pair: pair[0])[1]
        version = self._next_render_version(run.id)
        timeline = {item["scene_id"]: item for item in run.request["timeline"]}
        scene_ids = self._plan_scene_ids(run.visual_plan_id)
        total_weight = sum(item["duration_weight"] for item in timeline.values())
        remaining = narration.duration_ms
        inputs = []
        for index, scene_id in enumerate(scene_ids):
            duration = (
                remaining
                if index == len(scene_ids) - 1
                else round(
                    narration.duration_ms * timeline[scene_id]["duration_weight"] / total_weight
                )
            )
            remaining -= duration
            inputs.append(
                {
                    "scene_id": scene_id,
                    "resolved_state_id": states[scene_id],
                    "duration_ms": duration,
                    "motion": "static",
                    "transition_to_next": timeline[scene_id]["transition_to_next"],
                }
            )
        snapshot = self.media_service.create_persistent_scene_snapshot(
            f"{run.id}:snapshot:{version}",
            run.visual_plan_id,
            narration.id,
            inputs,
            run.request.get("citations"),
        )
        self.repository.create_production_evidence(
            f"{run.id}:snapshot:evidence:{version}",
            run.id,
            "snapshot",
            {
                "schema_version": snapshot.snapshot_schema_version,
                "render_version": version,
                "narration_asset_id": narration.id,
            },
            final_media_input_snapshot_id=snapshot.id,
        )
        return snapshot

    def _ensure_render(self, run: Any, snapshot: Any) -> Any:
        """Return or create the render of exactly this snapshot, at the snapshot's version."""

        for item in sorted(
            self.repository.list_production_evidence(run.id, "render"),
            key=self._evidence_version,
            reverse=True,
        ):
            if item.render_execution_id and (
                self.repository.get_render_execution(
                    item.render_execution_id
                ).final_media_input_snapshot_id
                == snapshot.id
            ):
                return self.repository.get_final_media_artifact(item.final_media_artifact_id)
        version = int(snapshot.id.rsplit(":", 1)[1])
        self.repository.append_production_run_event(run.id, "rendering", "render", {})
        artifact = self.media_service.render(
            f"{run.id}:render-execution:{version}", f"{run.id}-artifact-{version}", snapshot.id
        )
        execution = self.repository.get_render_execution(artifact.render_execution_id)
        self.repository.create_production_evidence(
            f"{run.id}:render:evidence:{version}",
            run.id,
            "render",
            {"technical_validation": artifact.technical_validation, "render_version": version},
            render_execution_id=execution.id,
            final_media_artifact_id=artifact.id,
        )
        return artifact

    def _ensure_automated_cell_qa(self, run: Any, states: dict[str, str], artifact: Any) -> None:
        if any(
            review.scope == "cell" and review.final_media_artifact_id == artifact.id
            for review in self.repository.list_production_qa_reviews(run.id)
        ):
            return
        version = int(artifact.id.rsplit("-", 1)[1])
        self._record_automated_cell_qa(run, states, artifact, f"{run.id}:qa:cell:{version}")

    def _record_automated_cell_qa(
        self, run: Any, states: dict[str, str], artifact: Any, review_id: str
    ) -> None:
        """Record one automated cell review bound to exactly one rendered artifact."""

        evidence = {
            scene_id: self.repository.verify_persistent_scene_aggregate(state_id)
            for scene_id, state_id in states.items()
        }
        coverage = {
            scene_id: unwritten_alpha_pixels(
                load_persistent_scene_frame(self.repository, state_id).rgba
            )
            for scene_id, state_id in states.items()
        }
        outcome = "passed" if not any(coverage.values()) else "failed"
        self.repository.create_production_qa_review(
            review_id,
            run.id,
            "cell",
            outcome,
            "automated",
            dict(MediaService.AUTOMATED_CELL_QA_PROFILE),
            {
                "persistent_aggregate_verification": evidence,
                MediaService.COMPOSITOR_COVERAGE_POLICY: {
                    "unwritten_alpha_pixels_by_scene": coverage
                },
            },
            artifact.id,
        )
        if outcome != "passed":
            raise ProductionRequestError("Composited scene frames contain unwritten pixels.")

    def _build_world(
        self,
        run: Any,
        world_input: dict[str, Any],
        world_index: int,
        acquisition: dict[tuple[str, str, str], dict[str, Any]],
    ) -> PersistentWorld:
        assets: list[RasterAsset] = []
        variants: list[EntityVariant] = []
        entities: list[EntityDefinition] = []
        spec_ids: list[str] = []
        for entity_index, entity in enumerate(world_input["entities"], 1):
            variant_ids = []
            for variant_index, variant in enumerate(entity["variants"], 1):
                key = (world_input["key"], entity["key"], variant["key"])
                source_id = acquisition[key]["asset_id"]
                derived_id = (
                    f"{run.id}:{DERIVED_RASTER_NAMESPACE}:"
                    f"{world_index}:{entity_index}:{variant_index}"
                )
                size = tuple(variant["intrinsic_size_wu"])
                full_frame = size == FRAME_SIZE
                raster = self.adapter.adapt(
                    run.id, source_id, derived_id, FRAME_SIZE if full_frame else None
                )
                assets.append(raster)
                spec_ids.append(variant["asset_spec_id"])
                variant_id = self._variant_id(run.id, world_index, entity["key"], variant["key"])
                variant_ids.append(variant_id)
                mapping = Affine(a=size[0] / raster.width, d=size[1] / raster.height)
                self._guard_layer_mapping(
                    self._affine(entity["initial_transform"]).compose(mapping), full_frame
                )
                variants.append(
                    EntityVariant(
                        variant_id,
                        entity["key"],
                        size,
                        entity["neutral_scale_id"],
                        (RenderSlice(f"{entity['key']}.main", raster.asset_id, None, mapping),),
                        character_authority_id=(
                            run.request["authority"]["character_profile_id"]
                            if self.repository.get_asset_spec(variant["asset_spec_id"]).asset_type
                            == "character"
                            else None
                        ),
                    )
                )
            initial_id = self._variant_id(
                run.id, world_index, entity["key"], entity["initial_variant_key"]
            )
            entities.append(
                EntityDefinition(
                    entity["key"],
                    entity["semantic_role"],
                    PersistenceClass(entity["persistence_class"]),
                    entity.get("plane_key", "main"),
                    initial_id,
                    self._affine(entity["initial_transform"]),
                    entity.get("initial_visible", True),
                    entity.get("initial_parent_key"),
                    entity.get("initial_state", "default"),
                    tuple(variant_ids),
                    entity["purpose"],
                    entity.get("depth", 0),
                )
            )
        authority = run.request["authority"]
        treatment = world_input["visual_treatment"]
        world = PersistentWorld(
            world_input["key"],
            1,
            GeometryContract(
                "WU",
                6,
                (Plane("main", Affine()),),
                Camera("vertical-1080x1920", 1080, 1920, Affine()),
            ),
            tuple(entities),
            tuple(variants),
            tuple(assets),
            (),
            treatment["style_profile_id"],
            treatment["palette_id"],
            treatment["wall_treatment_id"],
            treatment["lighting_policy_id"],
            DomainBindings(
                run.visual_plan_id,
                tuple(world_input["scene_ids"]),
                tuple(dict.fromkeys(spec_ids)),
                authority["character_profile_id"],
                authority["character_reference_set_id"],
                authority["visual_reference_authority_id"],
                authority["visual_style_profile_id"],
            ),
            "",
        )
        return bind_world_definition(world)

    @staticmethod
    def _guard_layer_mapping(mapping: Affine, full_frame: bool) -> None:
        """Reject compositor mappings the forward-mapped pixel compositor cannot fill."""

        scale_x, scale_y = mapping.scale
        if scale_x > 1 or scale_y > 1:
            raise ValueError("Scene layer mapping would upscale its raster and leave holes.")
        if full_frame and (mapping.a, mapping.b, mapping.c, mapping.d) != (1, 0, 0, 1):
            raise ValueError("Full-frame scene layers must reach the compositor at exact 1:1.")

    def _operation(self, run_id: str, world_index: int, value: dict[str, Any]) -> Operation:
        action, entity_key = value["action"], value["entity_key"]
        operation_value = value.get("value")
        if action == "set_variant":
            operation_value = self._variant_id(run_id, world_index, entity_key, operation_value)
        elif action == "set_transform":
            operation_value = self._affine(operation_value)
        elif action == "attach":
            operation_value = (
                operation_value["parent_key"],
                self._affine(operation_value["transform"]),
            )
        return Operation(action, entity_key, operation_value)

    def _validate_request(self, request: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(request, dict):
            raise ProductionRequestError("Production request must be an object.")
        allowed = {
            "id",
            "visual_plan_id",
            "authority",
            "worlds",
            "timeline",
            "forecast",
            "narration_authorized",
            "citations",
        }
        if set(request) - allowed:
            raise ProductionRequestError("Production request contains unsupported fields.")
        for field in ("id", "visual_plan_id"):
            if not isinstance(request.get(field), str) or not _SAFE_KEY.fullmatch(request[field]):
                raise ProductionRequestError(f"Production {field} must be a safe stable key.")
        self.repository._require_gate_authorized_visual_plan(request["visual_plan_id"])
        if not isinstance(request.get("narration_authorized"), bool):
            raise ProductionRequestError("Production narration_authorized must be a boolean.")
        forecast = request.get("forecast")
        if not isinstance(forecast, dict):
            raise ProductionRequestError("Production forecast must be an object.")
        image_calls = forecast.get("image_calls")
        if not isinstance(image_calls, int) or isinstance(image_calls, bool):
            raise ProductionRequestError("Production forecast image_calls must be an integer.")
        if forecast.get("narration_calls") != 1 or isinstance(
            forecast.get("narration_calls"), bool
        ):
            raise ProductionRequestError("Production forecast narration_calls must equal 1.")
        # Optional for backward compatibility: a request that plans the standard narration
        # completeness check freezes exactly one verification (transcription) call.
        if "verification_calls" in forecast and (
            forecast["verification_calls"] != 1 or isinstance(forecast["verification_calls"], bool)
        ):
            raise ProductionRequestError(
                "Production forecast verification_calls must equal 1 when present."
            )
        authority = request.get("authority")
        authority_fields = {
            "character_profile_id",
            "character_reference_set_id",
            "visual_reference_authority_id",
            "visual_style_profile_id",
        }
        if not isinstance(authority, dict) or set(authority) != authority_fields:
            raise ProductionRequestError("Production authority references are incomplete.")
        self.repository.get_character_profile(authority["character_profile_id"])
        reference = self.repository.get_character_reference_set(
            authority["character_reference_set_id"]
        )
        if reference.character_profile_id != authority["character_profile_id"]:
            raise ProductionRequestError("Character reference set does not match its profile.")
        self.repository.get_visual_reference_authority(authority["visual_reference_authority_id"])
        self.repository.get_visual_style_profile(authority["visual_style_profile_id"])
        worlds, timeline = request.get("worlds"), request.get("timeline")
        if not isinstance(worlds, list) or not worlds or not isinstance(timeline, list):
            raise ProductionRequestError("Production requires worlds and a timeline.")
        plan_scenes = self._plan_scene_ids(request["visual_plan_id"])
        world_scenes: list[str] = []
        variant_keys: set[tuple[str, str, str]] = set()
        for world in worlds:
            self._validate_world_input(request["visual_plan_id"], world, variant_keys)
            world_scenes.extend(world["scene_ids"])
        if world_scenes != plan_scenes:
            raise ProductionRequestError("World scene order must cover the exact VisualPlan.")
        if "citations" in request:
            self._validate_citations(request["visual_plan_id"], plan_scenes, request["citations"])
        if image_calls < len(variant_keys):
            raise ProductionRequestError(
                f"Production forecast image_calls ({image_calls}) is below the "
                f"{len(variant_keys)} variants this request must acquire."
            )
        if [item.get("scene_id") for item in timeline] != plan_scenes:
            raise ProductionRequestError("Timeline must cover the exact VisualPlan in sequence.")
        for index, item in enumerate(timeline):
            if not isinstance(item.get("duration_weight"), int) or item["duration_weight"] <= 0:
                raise ProductionRequestError("Timeline duration weights must be positive integers.")
            expected = None if index == len(timeline) - 1 else item.get("transition_to_next")
            if index < len(timeline) - 1 and expected not in MediaService.TRANSITIONS:
                raise ProductionRequestError("Timeline transition is unsupported.")
            if index == len(timeline) - 1 and item.get("transition_to_next") is not None:
                raise ProductionRequestError("Final timeline item cannot transition.")
        return json.loads(json.dumps(request, sort_keys=True))

    def _validate_world_input(
        self,
        plan_id: str,
        world: Any,
        variant_keys: set[tuple[str, str, str]],
    ) -> None:
        if not isinstance(world, dict) or not _SAFE_KEY.fullmatch(str(world.get("key", ""))):
            raise ProductionRequestError("World requires a safe semantic key.")
        scene_ids = world.get("scene_ids")
        entities = world.get("entities")
        transitions = world.get("transitions")
        treatment = world.get("visual_treatment")
        if (
            not isinstance(scene_ids, list)
            or not scene_ids
            or not isinstance(entities, list)
            or not entities
        ):
            raise ProductionRequestError("World requires scenes and entities.")
        if not isinstance(transitions, list) or len(transitions) != len(scene_ids) - 1:
            raise ProductionRequestError("World requires one transition per scene after its base.")
        treatment_fields = {
            "style_profile_id",
            "palette_id",
            "wall_treatment_id",
            "lighting_policy_id",
        }
        if not isinstance(treatment, dict) or set(treatment) != treatment_fields:
            raise ProductionRequestError("World visual treatment is incomplete.")
        self.repository.get_visual_style_profile(treatment["style_profile_id"])
        expected_transitions = scene_ids[1:]
        if [item.get("scene_id") for item in transitions] != expected_transitions:
            raise ProductionRequestError("World transitions must follow scene order.")
        entity_keys: set[str] = set()
        entity_variants: dict[str, set[str]] = {}
        entity_classes: dict[str, PersistenceClass] = {}
        for entity in entities:
            required = {
                "key",
                "semantic_role",
                "persistence_class",
                "purpose",
                "neutral_scale_id",
                "initial_variant_key",
                "initial_transform",
                "variants",
            }
            if not isinstance(entity, dict) or not required.issubset(entity):
                raise ProductionRequestError("World entity contract is incomplete.")
            if not _SAFE_KEY.fullmatch(str(entity["key"])) or entity["key"] in entity_keys:
                raise ProductionRequestError("Entity key is invalid or duplicated.")
            entity_keys.add(entity["key"])
            try:
                persistence_class = PersistenceClass(entity["persistence_class"])
            except ValueError as error:
                raise ProductionRequestError("Entity persistence class is unsupported.") from error
            entity_classes[entity["key"]] = persistence_class
            self._affine(entity["initial_transform"])
            variants = entity["variants"]
            if not isinstance(variants, list) or not variants:
                raise ProductionRequestError("Entity requires at least one variant.")
            keys = []
            for variant in variants:
                if not isinstance(variant, dict) or set(variant) != {
                    "key",
                    "asset_spec_id",
                    "intrinsic_size_wu",
                }:
                    raise ProductionRequestError("Entity variant contract is incomplete.")
                key = (world["key"], entity["key"], variant["key"])
                if not _SAFE_KEY.fullmatch(str(variant["key"])) or key in variant_keys:
                    raise ProductionRequestError("Variant key is invalid or duplicated.")
                variant_keys.add(key)
                keys.append(variant["key"])
                size = variant["intrinsic_size_wu"]
                if (
                    not isinstance(size, list)
                    or len(size) != 2
                    or any(not isinstance(item, (int, float)) or item <= 0 for item in size)
                ):
                    raise ProductionRequestError("Variant intrinsic size must be positive [w, h].")
                spec = self.repository.get_asset_spec(variant["asset_spec_id"])
                if self.repository.get_scene(spec.scene_id).visual_plan_id != plan_id:
                    raise ProductionRequestError("Variant AssetSpec belongs to another VisualPlan.")
            if entity["initial_variant_key"] not in keys:
                raise ProductionRequestError("Entity initial variant is not declared.")
            entity_variants[entity["key"]] = set(keys)
        permitted = {
            PersistenceClass.LOCKED_STATIC: set(),
            PersistenceClass.STATEFUL_STATIC: {"set_variant", "set_state"},
            PersistenceClass.MOVABLE_PROP: {
                "set_variant",
                "set_state",
                "set_visible",
                "set_transform",
                "attach",
            },
            PersistenceClass.ACTOR: {"set_variant", "set_transform", "attach"},
            PersistenceClass.EPHEMERAL: {"set_visible", "set_state"},
        }
        for transition in transitions:
            if not isinstance(transition.get("reason"), str) or not transition["reason"].strip():
                raise ProductionRequestError("Transition requires an explicit reason.")
            operations = transition.get("operations")
            if not isinstance(operations, list):
                raise ProductionRequestError("Transition operations must be a list.")
            seen: set[tuple[str, str]] = set()
            for operation in operations:
                if not isinstance(operation, dict) or not {
                    "action",
                    "entity_key",
                    "value",
                }.issubset(operation):
                    raise ProductionRequestError("Transition operation is incomplete.")
                if operation["entity_key"] not in entity_keys:
                    raise ProductionRequestError("Transition references an unknown entity.")
                action = operation["action"]
                entity_key = operation["entity_key"]
                if action not in permitted[entity_classes[entity_key]]:
                    raise ProductionRequestError(
                        "Transition action conflicts with the entity persistence class."
                    )
                if (entity_key, action) in seen:
                    raise ProductionRequestError("Transition action is duplicated for an entity.")
                seen.add((entity_key, action))
                value = operation["value"]
                if action == "set_variant" and value not in entity_variants[entity_key]:
                    raise ProductionRequestError("Transition selects an undeclared variant key.")
                if action == "set_transform":
                    self._affine(value)
                if action == "attach":
                    if (
                        not isinstance(value, dict)
                        or value.get("parent_key") not in entity_keys
                        or "transform" not in value
                    ):
                        raise ProductionRequestError("Attachment intent is incomplete.")
                    self._affine(value["transform"])
                if action == "set_visible" and not isinstance(value, bool):
                    raise ProductionRequestError("Visibility intent must be boolean.")
                if action == "set_state" and (not isinstance(value, str) or not value.strip()):
                    raise ProductionRequestError("State intent must be non-empty text.")
            closure = transition.get("allowed_derived_entities", [])
            if not isinstance(closure, list) or any(item not in entity_keys for item in closure):
                raise ProductionRequestError("Derived-entity closure is invalid.")

    def _validate_citations(self, plan_id: str, plan_scenes: list[str], citations: Any) -> None:
        """Accept only explicit citations whose sources back the Script's frozen claim set."""

        if not isinstance(citations, list) or not citations:
            raise ProductionRequestError("Citations must be a non-empty list when supplied.")
        try:
            MediaService.citation_overlays(
                [{"scene_id": scene_id, "duration_ms": 1} for scene_id in plan_scenes], citations
            )
        except ValueError as error:
            raise ProductionRequestError(str(error)) from error
        claim_set = self.repository.script_claim_set_payload(
            self.repository.get_visual_plan(plan_id).script_id
        )
        frozen = {
            source["id"] for source in (claim_set or {}).get("frozen_sources", []) if "id" in source
        }
        for citation in citations:
            if not set(citation["source_ids"]) <= frozen:
                raise ProductionRequestError(
                    "Citation sources must belong to the Script's frozen ScriptClaimSet."
                )

    @staticmethod
    def _affine(value: Any) -> Affine:
        fields = {"a", "b", "c", "d", "e", "f"}
        if not isinstance(value, dict) or set(value) - fields:
            raise ProductionRequestError("Transform must be an affine object.")
        return Affine(**value)

    def _plan_scene_ids(self, visual_plan_id: str) -> list[str]:
        return [item.id for item in self.repository.list_scenes_for_visual_plan(visual_plan_id)]

    @staticmethod
    def _variant_id(run_id: str, world_index: int, entity_key: str, variant_key: str) -> str:
        return f"{run_id}:variant:{world_index}:{entity_key}:{variant_key}"

    @staticmethod
    def _variant_specs(request: dict[str, Any]):
        for world in request["worlds"]:
            for entity in world["entities"]:
                for variant in entity["variants"]:
                    yield world["key"], entity["key"], variant["key"], variant["asset_spec_id"]

    @staticmethod
    def _full_frame_variant_keys(request: dict[str, Any]) -> set[tuple[str, str, str]]:
        return {
            (world["key"], entity["key"], variant["key"])
            for world in request["worlds"]
            for entity in world["entities"]
            for variant in entity["variants"]
            if tuple(variant["intrinsic_size_wu"]) == FRAME_SIZE
        }

    def _variant_keys(self, request: dict[str, Any]):
        return (
            (world, entity, variant)
            for world, entity, variant, _spec in self._variant_specs(request)
        )

    def _acquisition_map(self, run_id: str) -> dict[tuple[str, str, str], dict[str, Any]]:
        """Return each variant's active asset: its latest admitted acquisition attempt."""

        result = {}
        evidence = sorted(
            self.repository.list_production_evidence(run_id, "acquisition"),
            key=lambda item: int(item.id.rsplit(":", 1)[1]),
        )
        for item in evidence:
            if item.asset_id:
                key = tuple(
                    item.payload[name] for name in ("world_key", "entity_key", "variant_key")
                )
                result[key] = item.payload | {"asset_id": item.asset_id}
        return result

    def _assert_generation_authority(self, request: dict[str, Any]) -> None:
        """Fail before any provider call unless generation resolves the requested authority."""

        authority = request["authority"]
        service = self.generation_service
        if service.visual_style_profile_id != authority["visual_style_profile_id"]:
            raise ProductionRequestError(
                "Generation visual style differs from the production authority."
            )
        if service.global_visual_authority_id != authority["visual_reference_authority_id"]:
            raise ProductionRequestError(
                "Generation global visual authority differs from the production authority."
            )
        latest = self.repository.get_latest_character_reference_set(
            authority["character_profile_id"]
        )
        if latest is None or latest.id != authority["character_reference_set_id"]:
            raise ProductionRequestError(
                "Generation would resolve a different character reference set."
            )
        for world in request["worlds"]:
            for entity in world["entities"]:
                for variant in entity["variants"]:
                    spec = self.repository.get_asset_spec(variant["asset_spec_id"])
                    # Full-frame integrated beats are character-led under the current
                    # SimilarStoic production method; move this requirement into the channel
                    # recipe when that recipe is codified.
                    if tuple(variant["intrinsic_size_wu"]) == FRAME_SIZE:
                        if spec.character_profile_id != authority["character_profile_id"]:
                            raise ProductionRequestError(
                                "Full-frame AssetSpec character profile differs from the "
                                "production authority."
                            )
                    elif spec.character_profile_id not in {None, authority["character_profile_id"]}:
                        raise ProductionRequestError(
                            "Variant AssetSpec character profile differs from the production "
                            "authority."
                        )

    def _execution_authority_mismatch(
        self, request: dict[str, Any], execution_id: str
    ) -> str | None:
        """Describe any persisted execution provenance that contradicts the run authority."""

        authority = request["authority"]
        execution = self.repository.get_generation_execution(execution_id)
        if execution.visual_style_profile_id != authority["visual_style_profile_id"]:
            return "Generation execution recorded a different visual style profile."
        spec = self.repository.get_asset_spec(execution.asset_spec_id)
        if spec.character_profile_id is not None:
            if (
                execution.character_profile_id != authority["character_profile_id"]
                or execution.character_reference_set_id != authority["character_reference_set_id"]
            ):
                return "Generation execution recorded a different character authority."
        elif (
            execution.character_profile_id is not None
            or execution.character_reference_set_id is not None
        ):
            return "Generation execution recorded character provenance for a characterless spec."
        global_authorities = [
            item.visual_reference_authority_id
            for item in self.repository.list_generation_execution_visual_authorities(execution_id)
            if item.usage_role == "global_illustration_style"
        ]
        if global_authorities != [authority["visual_reference_authority_id"]]:
            return "Generation execution recorded a different global visual authority."
        return None

    def _variant_review_states(self, run: Any) -> dict[tuple[str, str, str], str]:
        """Classify each acquired variant's active asset as passed, rejected or pending.

        Reviews bind to the exact reviewed asset, so a rejection of a superseded asset never
        affects its replacement and a pass stays valid across later review rounds.
        """

        outcomes: dict[str, set[str]] = {}
        for review in self.repository.list_production_qa_reviews(run.id):
            if review.scope == "acquisition" and isinstance(review.evidence.get("asset_id"), str):
                outcomes.setdefault(review.evidence["asset_id"], set()).add(review.outcome)
        states = {}
        for key, active in self._acquisition_map(run.id).items():
            recorded = outcomes.get(active["asset_id"], set())
            states[key] = (
                "rejected" if "failed" in recorded else "passed" if recorded else "pending"
            )
        return states

    def _all_variants_passed(self, run: Any) -> bool:
        states = self._variant_review_states(run)
        return set(states) == set(self._variant_keys(run.request)) and all(
            state == "passed" for state in states.values()
        )

    def _next_acquisition_review_round(self, run_id: str) -> int:
        rounds = [
            1 if ":round-" not in review.id else int(review.id.split(":round-")[1].split(":")[0])
            for review in self.repository.list_production_qa_reviews(run_id)
            if review.scope == "acquisition"
        ]
        return max(rounds, default=0) + 1

    @staticmethod
    def _evidence_version(item: Any) -> int:
        """Versioned evidence IDs end in their integer render/output version."""

        return int(item.id.rsplit(":", 1)[1])

    def _current_evidence(self, run_id: str, kind: str):
        """Return the highest-version evidence of one kind; earlier versions stay queryable."""

        evidence = self.repository.list_production_evidence(run_id, kind)
        if not evidence:
            raise ProductionRequestError(f"Production has no {kind} evidence record.")
        return max(evidence, key=self._evidence_version)

    def _next_render_version(self, run_id: str) -> int:
        """Pick the next output version, skipping any identity already persisted."""

        snapshots = self.repository.list_production_evidence(run_id, "snapshot")
        renders = self.repository.list_production_evidence(run_id, "render")
        version = 1 + max([self._evidence_version(item) for item in snapshots + renders], default=0)
        evidence_ids = {item.id for item in self.repository.list_production_evidence(run_id)}
        review_ids = {item.id for item in self.repository.list_production_qa_reviews(run_id)}

        def exists(getter, identity: str) -> bool:
            try:
                getter(identity)
            except KeyError:
                return False
            return True

        while (
            exists(self.repository.get_final_media_input_snapshot, f"{run_id}:snapshot:{version}")
            or exists(self.repository.get_render_execution, f"{run_id}:render-execution:{version}")
            or exists(self.repository.get_final_media_artifact, f"{run_id}-artifact-{version}")
            or {
                f"{run_id}:snapshot:evidence:{version}",
                f"{run_id}:render:evidence:{version}",
                f"{run_id}:retime:evidence:{version}",
            }
            & evidence_ids
            or f"{run_id}:qa:cell:{version}" in review_ids
        ):
            version += 1
        return version

    def _render_artifacts_published(self, run_id: str) -> bool:
        """True once any render of this run has entered the publishing workflow."""

        return any(
            self.repository.final_media_artifact_is_packaged(item.final_media_artifact_id)
            for item in self.repository.list_production_evidence(run_id, "render")
        )

    def _fail(self, run_id: str, stage: str, error: Exception) -> None:
        self.repository.append_production_run_event(
            run_id,
            "failed",
            stage,
            {},
            error_code=type(error).__name__,
            error_message=str(error),
        )
        raise ProductionLifecycleError(run_id, stage, str(error)) from error

    def _founder_review_payload(self, run_id: str) -> dict[str, Any] | None:
        row = self.repository.connection.execute(
            "SELECT id FROM production_founder_reviews WHERE production_run_id=?", (run_id,)
        ).fetchone()
        return asdict(self.repository.get_production_founder_review(row["id"])) if row else None

    @staticmethod
    def _evidence_payload(item: Any) -> dict[str, Any]:
        return {
            "id": item.id,
            "type": item.evidence_type,
            "payload": item.payload,
            "payload_digest": item.payload_digest,
            "references": {
                name: getattr(item, name)
                for name in (
                    "generation_execution_id",
                    "asset_id",
                    "world_revision_id",
                    "resolved_state_id",
                    "narration_generation_execution_id",
                    "narration_asset_id",
                    "final_media_input_snapshot_id",
                    "render_execution_id",
                    "final_media_artifact_id",
                )
                if getattr(item, name) is not None
            },
            "created_at": item.created_at,
        }
