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

from project_atlas.generation import GenerationService
from project_atlas.media import FfmpegRuntime, MediaService
from project_atlas.persistence import AtlasRepository
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


class ProductionLifecycleError(RuntimeError):
    """A fail-closed production-stage failure already recorded in run history."""

    def __init__(self, run_id: str, stage: str, message: str) -> None:
        super().__init__(message)
        self.run_id = run_id
        self.stage = stage


class ProductionRequestError(ValueError):
    """The external command does not describe one complete canonical production."""


class ManagedAssetSceneAdapter:
    """Convert verified managed images into exact managed RGBA scene assets."""

    def __init__(self, repository: AtlasRepository, runtime: FfmpegRuntime) -> None:
        self.repository = repository
        self.runtime = runtime

    def adapt(self, run_id: str, source_asset_id: str, derived_asset_id: str) -> RasterAsset:
        source = self.repository.get_asset(source_asset_id)
        try:
            existing = self.repository.get_asset(derived_asset_id)
        except KeyError:
            existing = None
        if existing is not None:
            if existing.metadata.get("source_asset_id") != source.id:
                raise ValueError("Derived scene identity is already bound to another source.")
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
            if (
                not isinstance(width, int)
                or not isinstance(height, int)
                or width <= 0
                or height <= 0
            ):
                raise ValueError("Managed acquisition has invalid image dimensions.")
            raw_path = temporary_root / "frame.rgba"
            self.runtime._run(
                [
                    self.runtime.ffmpeg_path,
                    "-y",
                    "-i",
                    str(source_path),
                    "-frames:v",
                    "1",
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
                    "adapter": "managed-image-to-rgba-v1",
                    "source_asset_id": source.id,
                    "source_content_digest": source.content_digest,
                    "width": width,
                    "height": height,
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
    ) -> None:
        self.repository = repository
        self.generation_service = generation_service
        self.media_service = media_service
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

    def resume(self, run_id: str) -> dict[str, Any]:
        run = self.repository.get_production_run(run_id)
        latest = self.repository.latest_production_run_event(run_id)
        if latest is None:
            raise ProductionRequestError("Production has no lifecycle event.")
        if latest.status == "failed" and latest.stage == "acquisition":
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
            if not self._passed_review(run_id, "acquisition"):
                raise ProductionRequestError("Acquisition approval is required before resuming.")
            self._assemble_and_render(run)
        return self.status(run_id)

    def review_acquisition(self, run_id: str, reviews: list[dict[str, Any]]) -> dict[str, Any]:
        run = self.repository.get_production_run(run_id)
        latest = self.repository.latest_production_run_event(run_id)
        if latest is None or latest.status not in {"acquisition_review_pending", "failed"}:
            if self._passed_review(run_id, "acquisition"):
                return self.status(run_id)
            raise ProductionRequestError("Production is not awaiting acquisition review.")
        acquired = self._acquisition_map(run_id)
        expected = set(self._variant_keys(run.request))
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
        if set(supplied) != expected or set(acquired) != expected:
            raise ProductionRequestError(
                "Acquisition review must cover every exact acquired variant."
            )
        any_failed = False
        for index, key in enumerate(sorted(expected), 1):
            review = supplied[key]
            outcome = review.get("outcome")
            evidence = review.get("evidence")
            if outcome not in {"passed", "failed"} or not isinstance(evidence, dict):
                raise ProductionRequestError("Acquisition review requires outcome and evidence.")
            self.repository.create_production_qa_review(
                f"{run_id}:qa:acquisition:{index}",
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
                {"review_count": len(reviews)},
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
        artifact = self._single_evidence(run_id, "render").final_media_artifact_id
        self.repository.create_production_qa_review(
            f"{run_id}:qa:whole-video:1",
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

    def status(self, run_id: str) -> dict[str, Any]:
        run = self.repository.get_production_run(run_id)
        latest = self.repository.latest_production_run_event(run_id)
        evidence = self.repository.list_production_evidence(run_id)
        reviews = self.repository.list_production_qa_reviews(run_id)
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
            "created_at": run.created_at,
        }

    def _acquire(self, run: Any) -> None:
        self.repository.append_production_run_event(run.id, "acquiring", "acquisition", {})
        existing = self._acquisition_map(run.id)
        attempt = len(self.repository.list_production_evidence(run.id, "acquisition"))
        try:
            for world_key, entity_key, variant_key, asset_spec_id in self._variant_specs(
                run.request
            ):
                key = (world_key, entity_key, variant_key)
                if key in existing:
                    continue
                result = self.generation_service.generate_asset_spec(asset_spec_id)
                attempt += 1
                payload = {
                    "world_key": world_key,
                    "entity_key": entity_key,
                    "variant_key": variant_key,
                    "asset_spec_id": asset_spec_id,
                    "outcome": result.execution.outcome,
                }
                self.repository.create_production_evidence(
                    f"{run.id}:acquisition:attempt:{attempt}",
                    run.id,
                    "acquisition",
                    payload | ({"asset_id": result.asset.id} if result.asset else {}),
                    generation_execution_id=result.execution.id,
                    asset_id=result.asset.id if result.asset else None,
                )
                if result.asset is None:
                    raise RuntimeError("Required managed-asset acquisition failed.")
                existing[key] = payload | {"asset_id": result.asset.id}
            self.repository.append_production_run_event(
                run.id,
                "acquisition_review_pending",
                "acquisition_review",
                {"acquired_variants": len(existing)},
            )
        except Exception as error:
            self._fail(run.id, "acquisition", error)

    def _assemble_and_render(self, run: Any) -> None:
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
        existing = self.repository.list_production_evidence(run.id, "narration")
        if existing:
            return self.repository.get_narration_asset(existing[-1].narration_asset_id)
        self.repository.append_production_run_event(run.id, "narrating", "narration", {})
        plan = self.repository.get_visual_plan(run.visual_plan_id)
        result = self.media_service.generate_brand_narration(
            f"{run.id}:narration-execution:1",
            f"{run.id}-narration-1",
            plan.script_id,
            brand_key="similarstoic",
            execution_authorized=True,
        )
        self.repository.create_production_evidence(
            f"{run.id}:narration:evidence:1",
            run.id,
            "narration",
            {"outcome": result.execution.outcome, "brand_key": "similarstoic"},
            narration_generation_execution_id=result.execution.id,
            narration_asset_id=result.narration_asset.id if result.narration_asset else None,
        )
        if result.narration_asset is None:
            raise RuntimeError("Approved SimilarStoic narration generation failed.")
        return result.narration_asset

    def _ensure_snapshot(self, run: Any, states: dict[str, str], narration: Any) -> Any:
        existing = self.repository.list_production_evidence(run.id, "snapshot")
        if existing:
            return self.repository.get_final_media_input_snapshot(
                existing[-1].final_media_input_snapshot_id
            )
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
            f"{run.id}:snapshot:1", run.visual_plan_id, narration.id, inputs
        )
        self.repository.create_production_evidence(
            f"{run.id}:snapshot:evidence:1",
            run.id,
            "snapshot",
            {"schema_version": snapshot.snapshot_schema_version},
            final_media_input_snapshot_id=snapshot.id,
        )
        return snapshot

    def _ensure_render(self, run: Any, snapshot: Any) -> Any:
        existing = self.repository.list_production_evidence(run.id, "render")
        if existing:
            return self.repository.get_final_media_artifact(existing[-1].final_media_artifact_id)
        self.repository.append_production_run_event(run.id, "rendering", "render", {})
        artifact = self.media_service.render(
            f"{run.id}:render-execution:1", f"{run.id}-artifact-1", snapshot.id
        )
        execution = self.repository.get_render_execution(artifact.render_execution_id)
        self.repository.create_production_evidence(
            f"{run.id}:render:evidence:1",
            run.id,
            "render",
            {"technical_validation": artifact.technical_validation},
            render_execution_id=execution.id,
            final_media_artifact_id=artifact.id,
        )
        return artifact

    def _ensure_automated_cell_qa(self, run: Any, states: dict[str, str], artifact: Any) -> None:
        if any(
            review.scope == "cell" for review in self.repository.list_production_qa_reviews(run.id)
        ):
            return
        evidence = {
            scene_id: self.repository.verify_persistent_scene_aggregate(state_id)
            for scene_id, state_id in states.items()
        }
        self.repository.create_production_qa_review(
            f"{run.id}:qa:cell:1",
            run.id,
            "cell",
            "passed",
            "automated",
            dict(MediaService.FINAL_FRAME_VISUAL_QA_PROFILE),
            {"persistent_aggregate_verification": evidence},
            artifact.id,
        )

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
                derived_id = f"{run.id}:raster:{world_index}:{entity_index}:{variant_index}"
                raster = self.adapter.adapt(run.id, source_id, derived_id)
                assets.append(raster)
                spec_ids.append(variant["asset_spec_id"])
                variant_id = self._variant_id(run.id, world_index, entity["key"], variant["key"])
                variant_ids.append(variant_id)
                size = tuple(variant["intrinsic_size_wu"])
                mapping = Affine(a=size[0] / raster.width, d=size[1] / raster.height)
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
        allowed = {"id", "visual_plan_id", "authority", "worlds", "timeline", "forecast"}
        if set(request) - allowed:
            raise ProductionRequestError("Production request contains unsupported fields.")
        for field in ("id", "visual_plan_id"):
            if not isinstance(request.get(field), str) or not _SAFE_KEY.fullmatch(request[field]):
                raise ProductionRequestError(f"Production {field} must be a safe stable key.")
        self.repository._require_gate_authorized_visual_plan(request["visual_plan_id"])
        if not isinstance(request.get("forecast", {}), dict):
            raise ProductionRequestError("Production forecast must be an object.")
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

    def _variant_keys(self, request: dict[str, Any]):
        return (
            (world, entity, variant)
            for world, entity, variant, _spec in self._variant_specs(request)
        )

    def _acquisition_map(self, run_id: str) -> dict[tuple[str, str, str], dict[str, Any]]:
        result = {}
        for item in self.repository.list_production_evidence(run_id, "acquisition"):
            if item.asset_id:
                key = tuple(
                    item.payload[name] for name in ("world_key", "entity_key", "variant_key")
                )
                result[key] = item.payload | {"asset_id": item.asset_id}
        return result

    def _passed_review(self, run_id: str, scope: str) -> bool:
        reviews = [
            item
            for item in self.repository.list_production_qa_reviews(run_id)
            if item.scope == scope
        ]
        return bool(reviews) and all(item.outcome == "passed" for item in reviews)

    def _single_evidence(self, run_id: str, kind: str):
        evidence = self.repository.list_production_evidence(run_id, kind)
        if len(evidence) != 1:
            raise ProductionRequestError(f"Production requires exactly one {kind} evidence record.")
        return evidence[0]

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
