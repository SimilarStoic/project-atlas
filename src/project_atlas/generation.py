"""Provider-neutral synchronous image generation and Atlas-managed asset storage."""

from __future__ import annotations

import base64
import json
import os
import tempfile
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from project_atlas.persistence import (
    Asset,
    AssetSpec,
    AtlasRepository,
    GenerationExecution,
    VisualStyleProfile,
)

DEFAULT_VISUAL_STYLE_PROFILE_ID = "visual-style-profile-similarstoic-core-v1"


@dataclass(frozen=True)
class GenerationInput:
    """The deliberately small Atlas-owned input supplied to a generator."""

    asset_type: str
    prompt: str
    continuity_key: str | None
    parameters: dict[str, Any]
    style: dict[str, Any] | None = None

    def payload(self) -> dict[str, Any]:
        payload = {
            "schema_version": 2 if self.style is not None else 1,
            "asset_type": self.asset_type,
            "prompt": self.prompt,
            "continuity_key": self.continuity_key,
            "parameters": self.parameters,
        }
        if self.style is not None:
            payload["style"] = self.style
        return payload


@dataclass(frozen=True)
class GeneratedArtifact:
    """The provider-neutral result Atlas needs to store and register one image."""

    content: bytes
    media_type: str
    provider_key: str | None = None
    model_key: str | None = None
    provider_request_id: str | None = None
    response_metadata: dict[str, Any] | None = None


class GenerationFailure(Exception):
    """An expected terminal generator failure with optional provider provenance."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str | None = None,
        provider_key: str | None = None,
        model_key: str | None = None,
        provider_request_id: str | None = None,
        response_metadata: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.provider_key = provider_key
        self.model_key = model_key
        self.provider_request_id = provider_request_id
        self.response_metadata = response_metadata or {}


class UnsupportedGenerationType(ValueError):
    """Raised before invoking a generator for a non-executable AssetSpec type."""


class MissingVisualStyleProfile(ValueError):
    """Raised before generator invocation when configured style provenance is unavailable."""


class AssetStorageFailure(Exception):
    """Raised when Atlas cannot safely create a locally managed asset file."""


class AssetGenerator(Protocol):
    """A replaceable synchronous image-generation adapter."""

    generator_key: str

    def supports(self, asset_type: str) -> bool:
        """Return whether this adapter can execute this open-ended AssetSpec type."""

    def generate(self, generation_input: GenerationInput) -> GeneratedArtifact:
        """Generate one artifact without writing Atlas files or persistence records."""


def default_asset_storage_root() -> Path:
    """Return the configured local root for generated Atlas asset files."""

    return Path(os.environ.get("ATLAS_ASSET_STORAGE_ROOT", "data/assets"))


def configured_visual_style_profile_id() -> str:
    """Return the configured immutable profile ID or the deterministic seeded fallback."""

    configured = os.environ.get("ATLAS_VISUAL_STYLE_PROFILE_ID", "").strip()
    return configured or DEFAULT_VISUAL_STYLE_PROFILE_ID


def asset_spec_snapshot(asset_spec: AssetSpec) -> dict[str, Any]:
    """Freeze generation-relevant AssetSpec detail at execution time."""

    return {
        "schema_version": 1,
        "asset_spec_id": asset_spec.id,
        "scene_id": asset_spec.scene_id,
        "asset_type": asset_spec.asset_type,
        "purpose": asset_spec.purpose,
        "description": asset_spec.description,
        "generation_prompt": asset_spec.generation_prompt,
        "continuity_key": asset_spec.continuity_key,
        "metadata": asset_spec.metadata,
    }


def generation_input_for(asset_spec: AssetSpec) -> GenerationInput:
    """Build the v1 normalized Atlas generation input from persisted requirement detail."""

    return GenerationInput(
        asset_type=asset_spec.asset_type,
        prompt=asset_spec.generation_prompt,
        continuity_key=asset_spec.continuity_key,
        parameters={},
    )


class PromptComposer:
    """Compose a deterministic Atlas-owned visual prompt from one profile and AssetSpec."""

    _GLOBAL_RULE_ORDER = (
        "background",
        "composition",
        "visual_ideas",
        "shapes",
        "shading",
        "colour",
        "negative_space",
        "detail",
        "avoid",
        "narration",
    )
    _ASSET_TYPE_RULE_ORDER = (
        "role",
        "layer_discipline",
        "prefer",
        "background",
        "detail",
        "text",
        "avoid",
    )

    def compose(self, asset_spec: AssetSpec, profile: VisualStyleProfile) -> GenerationInput:
        """Return one v2 input with only the style rules relevant to the AssetSpec type."""

        global_rules, asset_type_rules = self._resolved_rules(asset_spec, profile)
        prompt = "\n\n".join(
            (
                f"Visual style guidance: {profile.generation_guidance}",
                "Global visual rules: " + self._render_rules(global_rules, self._GLOBAL_RULE_ORDER),
                f"{asset_spec.asset_type} visual rules: "
                + self._render_rules(asset_type_rules, self._ASSET_TYPE_RULE_ORDER),
                f"AssetSpec requirement: {asset_spec.generation_prompt}",
            )
        )
        return GenerationInput(
            asset_type=asset_spec.asset_type,
            prompt=prompt,
            continuity_key=asset_spec.continuity_key,
            parameters={},
            style={
                "profile_id": profile.id,
                "style_key": profile.style_key,
                "version": profile.version,
                "generation_guidance": profile.generation_guidance,
                "rules": {
                    "schema_version": profile.rules.get("schema_version", 1),
                    "global": global_rules,
                    "asset_type": asset_spec.asset_type,
                    "asset_type_rules": asset_type_rules,
                },
            },
        )

    @staticmethod
    def _resolved_rules(
        asset_spec: AssetSpec, profile: VisualStyleProfile
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        global_rules = profile.rules.get("global", {})
        asset_types = profile.rules.get("asset_types", {})
        if not isinstance(global_rules, dict) or not isinstance(asset_types, dict):
            raise ValueError(
                "VisualStyleProfile rules must contain global and asset_types objects."
            )
        asset_type_rules = asset_types.get(asset_spec.asset_type, {})
        if not isinstance(asset_type_rules, dict):
            raise ValueError("VisualStyleProfile AssetSpec-type rules must be an object.")
        return global_rules.copy(), asset_type_rules.copy()

    @staticmethod
    def _render_rules(rules: dict[str, Any], known_order: tuple[str, ...]) -> str:
        ordered_keys = [key for key in known_order if key in rules]
        ordered_keys.extend(sorted(key for key in rules if key not in known_order))
        if not ordered_keys:
            return "No additional rules."
        rendered = []
        for key in ordered_keys:
            value = rules[key]
            if isinstance(value, list):
                value_text = "; ".join(str(item) for item in value)
            else:
                value_text = str(value)
            rendered.append(f"{key.replace('_', ' ')}: {value_text}")
        return "; ".join(rendered) + "."


class LocalAssetStorage:
    """Own immutable generated files below one configurable, traversal-safe root."""

    _EXTENSIONS = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}

    def __init__(self, root: Path | str | None = None) -> None:
        self.root = Path(root or default_asset_storage_root()).resolve()

    def write(self, asset_spec_id: str, asset_id: str, content: bytes, media_type: str) -> Path:
        """Safely create one new immutable output and return its absolute file path."""

        extension = self._EXTENSIONS.get(media_type)
        if extension is None:
            raise AssetStorageFailure(f"Unsupported generated media type: {media_type}")
        if not isinstance(content, bytes) or not content:
            raise AssetStorageFailure("Generated artifact content must be non-empty bytes.")
        self._validate_component(asset_spec_id)
        self._validate_component(asset_id)
        target = (self.root / asset_spec_id / f"{asset_id}{extension}").resolve()
        if self.root not in target.parents:
            raise AssetStorageFailure("Generated asset path escaped the configured storage root.")
        temporary_path: Path | None = None
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                raise AssetStorageFailure(
                    "A generated Asset file already exists at the immutable path."
                )
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
                temporary.write(content)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = Path(temporary.name)
            try:
                os.link(temporary_path, target)
            except FileExistsError as error:
                raise AssetStorageFailure(
                    "A generated Asset file already exists at the immutable path."
                ) from error
            temporary_path.unlink()
            return target
        except OSError as error:
            raise AssetStorageFailure(f"Could not store generated Asset: {error}") from error
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()

    def relative_path(self, path: Path) -> str:
        """Return one stored path relative to the configured Atlas storage root."""

        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError as error:
            raise AssetStorageFailure(
                "Generated Asset path is outside the storage root."
            ) from error

    def remove_newly_written(self, path: Path) -> None:
        """Remove only a tracked newly written file after persistence fails."""

        resolved = path.resolve()
        if self.root not in resolved.parents:
            raise AssetStorageFailure("Refusing to remove a file outside the storage root.")
        resolved.unlink()

    @staticmethod
    def _validate_component(value: str) -> None:
        if (
            not isinstance(value, str)
            or not value
            or Path(value).name != value
            or value in {".", ".."}
        ):
            raise AssetStorageFailure("Asset storage identifiers must be safe path components.")


class OpenAIImageGenerator:
    """The first replaceable standard-library OpenAI Image API adapter."""

    generator_key = "openai-image"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 120,
        opener: Callable[..., Any] = urlopen,
        supported_asset_types: frozenset[str] | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY")
        self.model = model or os.environ.get("ATLAS_OPENAI_IMAGE_MODEL", "gpt-image-2")
        self.timeout_seconds = timeout_seconds
        self.opener = opener
        self.supported_asset_types = supported_asset_types or frozenset(
            {"environment", "character", "graphic", "prop"}
        )

    def supports(self, asset_type: str) -> bool:
        return asset_type in self.supported_asset_types

    def generate(self, generation_input: GenerationInput) -> GeneratedArtifact:
        if not self.api_key:
            raise GenerationFailure(
                "OPENAI_API_KEY is not configured for OpenAI image generation.",
                error_code="missing_api_key",
                provider_key="openai",
                model_key=self.model,
            )
        payload = json.dumps(
            {"model": self.model, "prompt": generation_input.prompt, "n": 1, "output_format": "png"}
        ).encode("utf-8")
        request = Request(
            "https://api.openai.com/v1/images/generations",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with self.opener(request, timeout=self.timeout_seconds) as response:
                body = response.read()
                provider_request_id = response.headers.get("x-request-id")
        except HTTPError as error:
            body = error.read()
            details = self._json_object(body)
            provider_error = (
                details.get("error", {}) if isinstance(details.get("error"), dict) else {}
            )
            raise GenerationFailure(
                provider_error.get(
                    "message", f"OpenAI image generation failed with HTTP {error.code}."
                ),
                error_code=provider_error.get("code") or str(error.code),
                provider_key="openai",
                model_key=self.model,
                provider_request_id=error.headers.get("x-request-id"),
                response_metadata={"http_status": error.code},
            ) from error
        except URLError as error:
            raise GenerationFailure(
                f"OpenAI image generation request failed: {error.reason}",
                error_code="network_error",
                provider_key="openai",
                model_key=self.model,
            ) from error
        response_payload = self._json_object(body)
        try:
            encoded_image = response_payload["data"][0]["b64_json"]
            content = base64.b64decode(encoded_image, validate=True)
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise GenerationFailure(
                "OpenAI returned an invalid image-generation response.",
                error_code="invalid_response",
                provider_key="openai",
                model_key=self.model,
                provider_request_id=provider_request_id,
            ) from error
        return GeneratedArtifact(
            content=content,
            media_type="image/png",
            provider_key="openai",
            model_key=self.model,
            provider_request_id=provider_request_id,
            response_metadata={
                key: response_payload[key] for key in ("created",) if key in response_payload
            },
        )

    @staticmethod
    def _json_object(body: bytes) -> dict[str, Any]:
        try:
            payload = json.loads(body)
        except (TypeError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}


@dataclass(frozen=True)
class GenerationResult:
    """The durable outcome of one Atlas generation operation."""

    execution: GenerationExecution
    asset: Asset | None


class GenerationService:
    """Orchestrate one persisted AssetSpec through a generator and Atlas storage."""

    def __init__(
        self,
        repository: AtlasRepository,
        generator: AssetGenerator,
        storage: LocalAssetStorage,
        visual_style_profile_id: str | None = None,
    ) -> None:
        self.repository = repository
        self.generator = generator
        self.storage = storage
        self.visual_style_profile_id = (
            visual_style_profile_id.strip()
            if isinstance(visual_style_profile_id, str) and visual_style_profile_id.strip()
            else configured_visual_style_profile_id()
        )
        self.prompt_composer = PromptComposer()

    def visual_style_summary(self) -> dict[str, Any]:
        """Return the active immutable profile identity for read-only Workspace display."""

        profile = self._active_visual_style_profile()
        return {
            "profile_id": profile.id,
            "style_key": profile.style_key,
            "version": profile.version,
            "name": profile.name,
        }

    def generate_asset_spec(self, asset_spec_id: str) -> GenerationResult:
        """Synchronously generate and durably register one AssetSpec output."""

        asset_spec = self.repository.get_asset_spec(asset_spec_id)
        if not self.generator.supports(asset_spec.asset_type):
            raise UnsupportedGenerationType(
                f"AssetSpec type {asset_spec.asset_type!r} is not executable by this generator."
            )
        profile = self._active_visual_style_profile()
        snapshot = asset_spec_snapshot(asset_spec)
        generation_input_object = self.prompt_composer.compose(asset_spec, profile)
        generation_input = generation_input_object.payload()
        try:
            artifact = self.generator.generate(generation_input_object)
            self._validate_artifact(artifact)
        except GenerationFailure as error:
            return GenerationResult(
                self.repository.create_failed_generation_execution(
                    self._execution_id(),
                    asset_spec.id,
                    snapshot,
                    generation_input,
                    self.generator.generator_key,
                    visual_style_profile_id=profile.id,
                    provider_key=error.provider_key,
                    model_key=error.model_key,
                    provider_request_id=error.provider_request_id,
                    error_code=error.error_code,
                    error_message=str(error),
                    response_metadata=error.response_metadata,
                ),
                None,
            )
        asset_id = self._asset_id()
        try:
            stored_path = self.storage.write(
                asset_spec.id, asset_id, artifact.content, artifact.media_type
            )
        except AssetStorageFailure as error:
            return GenerationResult(
                self.repository.create_failed_generation_execution(
                    self._execution_id(),
                    asset_spec.id,
                    snapshot,
                    generation_input,
                    self.generator.generator_key,
                    visual_style_profile_id=profile.id,
                    provider_key=artifact.provider_key,
                    model_key=artifact.model_key,
                    provider_request_id=artifact.provider_request_id,
                    error_code="storage_failure",
                    error_message=str(error),
                    response_metadata=artifact.response_metadata or {},
                ),
                None,
            )
        try:
            execution, asset = self.repository.record_successful_generation(
                self._execution_id(),
                asset_id,
                asset_spec.id,
                snapshot,
                generation_input,
                self.generator.generator_key,
                self.storage.relative_path(stored_path),
                artifact.media_type,
                visual_style_profile_id=profile.id,
                provider_key=artifact.provider_key,
                model_key=artifact.model_key,
                provider_request_id=artifact.provider_request_id,
                response_metadata=artifact.response_metadata or {},
            )
        except Exception as error:
            try:
                self.storage.remove_newly_written(stored_path)
            except Exception as cleanup_error:
                raise RuntimeError(
                    "Atlas failed to persist a generated Asset and could not remove its new file."
                ) from cleanup_error
            raise error
        return GenerationResult(execution, asset)

    def _active_visual_style_profile(self) -> VisualStyleProfile:
        try:
            return self.repository.get_visual_style_profile(self.visual_style_profile_id)
        except KeyError as error:
            raise MissingVisualStyleProfile(
                f"Configured VisualStyleProfile {self.visual_style_profile_id!r} does not exist."
            ) from error

    @staticmethod
    def _validate_artifact(artifact: GeneratedArtifact) -> None:
        if not isinstance(artifact.content, bytes) or not artifact.content:
            raise GenerationFailure(
                "Generator returned no image bytes.",
                error_code="invalid_artifact",
                provider_key=artifact.provider_key,
                model_key=artifact.model_key,
                provider_request_id=artifact.provider_request_id,
                response_metadata=artifact.response_metadata,
            )
        if artifact.media_type not in LocalAssetStorage._EXTENSIONS:
            raise GenerationFailure(
                f"Generator returned unsupported media type {artifact.media_type!r}.",
                error_code="invalid_artifact",
                provider_key=artifact.provider_key,
                model_key=artifact.model_key,
                provider_request_id=artifact.provider_request_id,
                response_metadata=artifact.response_metadata,
            )

    @staticmethod
    def _execution_id() -> str:
        return f"generation-execution-{uuid.uuid4().hex}"

    @staticmethod
    def _asset_id() -> str:
        return f"asset-{uuid.uuid4().hex}"
