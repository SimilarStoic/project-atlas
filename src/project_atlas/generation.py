"""Provider-neutral synchronous image generation and Atlas-managed asset storage."""

from __future__ import annotations

import base64
import hashlib
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
    CharacterProfile,
    GenerationExecution,
    VisualReferenceAuthority,
    VisualStyleProfile,
)

DEFAULT_VISUAL_STYLE_PROFILE_ID = "visual-style-profile-similarstoic-core-v3"
DEFAULT_GLOBAL_VISUAL_AUTHORITY_ID = (
    "visual-reference-authority-similarstoic-global-illustration-v1"
)
DEFAULT_COMPOSITION_VISUAL_AUTHORITY_ID = (
    "visual-reference-authority-similarstoic-composition-depth-v1"
)
DEFAULT_BREAK_FRAME_VISUAL_AUTHORITY_ID = (
    "visual-reference-authority-similarstoic-special-break-frame-v1"
)


@dataclass(frozen=True)
class ReferenceImage:
    """One verified runtime-only reference image supplied to a generator."""

    asset_id: str
    media_type: str
    content: bytes
    position: int
    usage_role: str = "character_identity"
    authority_id: str | None = None


@dataclass(frozen=True)
class GenerationInput:
    """The deliberately small Atlas-owned input supplied to a generator."""

    asset_type: str
    prompt: str
    continuity_key: str | None
    parameters: dict[str, Any]
    style: dict[str, Any] | None = None
    character: dict[str, Any] | None = None
    character_references: dict[str, Any] | None = None
    visual_authority_recipe: dict[str, Any] | None = None
    reference_images: tuple[ReferenceImage, ...] = ()

    def payload(self) -> dict[str, Any]:
        payload = {
            "schema_version": (
                5
                if self.visual_authority_recipe is not None
                else (
                    4
                    if self.character_references is not None
                    else 3 if self.style is not None else 1
                )
            ),
            "asset_type": self.asset_type,
            "prompt": self.prompt,
            "continuity_key": self.continuity_key,
            "parameters": self.parameters,
        }
        if self.style is not None:
            payload["style"] = self.style
        if self.character is not None:
            payload["character"] = self.character
        if self.character_references is not None:
            payload["character_references"] = self.character_references
        if self.visual_authority_recipe is not None:
            payload["visual_authority_recipe"] = self.visual_authority_recipe
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


class MissingCharacterReferenceSet(ValueError):
    """Raised before generator invocation when grounded character references are unavailable."""


class MissingProviderConfiguration(ValueError):
    """Raised before a provider attempt cannot be made from local configuration."""


class InvalidCharacterReferenceBootstrap(ValueError):
    """Raised before attempting an ineligible first-reference character generation."""


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
        "character_profile_id": asset_spec.character_profile_id,
        "metadata": asset_spec.metadata,
    }


def generation_input_for(asset_spec: AssetSpec) -> GenerationInput:
    """Build a legacy v1 input from persisted requirement detail for historical compatibility."""

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
        "rendering_language",
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

    def compose(
        self,
        asset_spec: AssetSpec,
        profile: VisualStyleProfile,
        character_profile: CharacterProfile | None = None,
        character_references: dict[str, Any] | None = None,
        reference_images: tuple[ReferenceImage, ...] = (),
        visual_authority_recipe: dict[str, Any] | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> GenerationInput:
        """Return one v3 input with resolved style and optional character identity provenance."""

        global_rules, asset_type_rules = self._resolved_rules(asset_spec, profile)
        prompt_parts = [
            f"Visual style guidance: {profile.generation_guidance}",
            "Global visual rules: " + self._render_rules(global_rules, self._GLOBAL_RULE_ORDER),
            f"{asset_spec.asset_type} visual rules: "
            + self._render_rules(asset_type_rules, self._ASSET_TYPE_RULE_ORDER),
        ]
        if character_profile is not None:
            prompt_parts.append(
                f"Character identity guidance: {character_profile.generation_guidance}"
            )
        if visual_authority_recipe is not None:
            for authority in visual_authority_recipe["authorities"]:
                prompt_parts.append(
                    f"{authority['usage_role'].replace('_', ' ').title()} authority guidance: "
                    f"{authority['generation_guidance']}"
                )
        prompt_parts.append(f"AssetSpec requirement: {asset_spec.generation_prompt}")
        prompt = "\n\n".join(prompt_parts)
        return GenerationInput(
            asset_type=asset_spec.asset_type,
            prompt=prompt,
            continuity_key=asset_spec.continuity_key,
            parameters=parameters or {},
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
            character=(
                {
                    "profile_id": character_profile.id,
                    "character_key": character_profile.character_key,
                    "version": character_profile.version,
                    "name": character_profile.name,
                    "identity_description": character_profile.identity_description,
                    "generation_guidance": character_profile.generation_guidance,
                }
                if character_profile is not None
                else None
            ),
            character_references=character_references,
            visual_authority_recipe=visual_authority_recipe,
            reference_images=reference_images,
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
        image_size: str | None = None,
        timeout_seconds: float = 120,
        opener: Callable[..., Any] = urlopen,
        supported_asset_types: frozenset[str] | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY")
        self.model = model or os.environ.get("ATLAS_OPENAI_IMAGE_MODEL", "gpt-image-2")
        self.image_size = image_size or os.environ.get("ATLAS_OPENAI_IMAGE_SIZE")
        self.timeout_seconds = timeout_seconds
        self.opener = opener
        self.supported_asset_types = supported_asset_types or frozenset(
            {"environment", "character", "graphic", "prop"}
        )

    def supports(self, asset_type: str) -> bool:
        return asset_type in self.supported_asset_types

    def generation_parameters(self) -> dict[str, Any]:
        """Return stable adapter settings for the frozen provider-neutral input."""

        parameters: dict[str, Any] = {"output_format": "png"}
        if self.image_size:
            parameters["image_size"] = self.image_size
        return parameters

    def validate_configuration(self) -> None:
        """Reject a missing API credential before crossing the provider-attempt boundary."""

        if not self.api_key:
            raise MissingProviderConfiguration(
                "OPENAI_API_KEY is not configured for OpenAI image generation."
            )

    def generate(self, generation_input: GenerationInput) -> GeneratedArtifact:
        self.validate_configuration()
        if generation_input.reference_images:
            endpoint = "https://api.openai.com/v1/images/edits"
            payload, content_type = self._reference_edit_payload(generation_input)
        else:
            endpoint = "https://api.openai.com/v1/images/generations"
            request_payload = {
                "model": self.model,
                "prompt": generation_input.prompt,
                "n": 1,
                "output_format": "png",
            }
            if self.image_size:
                request_payload["size"] = self.image_size
            payload = json.dumps(request_payload).encode("utf-8")
            content_type = "application/json"
        request = Request(
            endpoint,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": content_type,
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

    def _reference_edit_payload(self, generation_input: GenerationInput) -> tuple[bytes, str]:
        """Encode already verified reference bytes for OpenAI's image-edit transport."""

        boundary = f"----AtlasReference{uuid.uuid4().hex}"
        chunks: list[bytes] = []

        def add_text(name: str, value: str) -> None:
            chunks.extend(
                (
                    f"--{boundary}\r\n".encode(),
                    f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                    value.encode("utf-8"),
                    b"\r\n",
                )
            )

        add_text("model", self.model)
        add_text("prompt", generation_input.prompt)
        add_text("n", "1")
        add_text("output_format", "png")
        for reference in generation_input.reference_images:
            extension = LocalAssetStorage._EXTENSIONS.get(reference.media_type)
            if extension is None:
                raise ValueError(
                    "Reference image media type is not supported by OpenAI image edits."
                )
            chunks.extend(
                (
                    f"--{boundary}\r\n".encode(),
                    (
                        'Content-Disposition: form-data; name="image[]"; '
                        f'filename="reference-{reference.position}{extension}"\r\n'
                    ).encode(),
                    f"Content-Type: {reference.media_type}\r\n\r\n".encode(),
                    reference.content,
                    b"\r\n",
                )
            )
        chunks.append(f"--{boundary}--\r\n".encode())
        return b"".join(chunks), f"multipart/form-data; boundary={boundary}"

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
        global_visual_authority_id: str | None = None,
    ) -> None:
        self.repository = repository
        self.generator = generator
        self.storage = storage
        self.visual_style_profile_id = (
            visual_style_profile_id.strip()
            if isinstance(visual_style_profile_id, str) and visual_style_profile_id.strip()
            else configured_visual_style_profile_id()
        )
        self.global_visual_authority_id = (
            global_visual_authority_id.strip()
            if isinstance(global_visual_authority_id, str) and global_visual_authority_id.strip()
            else DEFAULT_GLOBAL_VISUAL_AUTHORITY_ID
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
        character_profile = self._character_profile_for(asset_spec)
        reference_set_id: str | None = None
        character_references: dict[str, Any] | None = None
        reference_images: tuple[ReferenceImage, ...] = ()
        if character_profile is not None:
            reference_set, character_references, reference_images = self._character_references_for(
                character_profile
            )
            reference_set_id = reference_set.id
        visual_authority_recipe, visual_reference_images = self._visual_authority_references_for(
            asset_spec, len(reference_images)
        )
        reference_images += visual_reference_images
        self._validate_reference_capacity(reference_images)
        self._validate_provider_configuration()
        snapshot = asset_spec_snapshot(asset_spec)
        generation_input_object = self.prompt_composer.compose(
            asset_spec,
            profile,
            character_profile,
            character_references,
            reference_images,
            visual_authority_recipe,
            self._generation_parameters(reference_images, visual_authority_recipe),
        )
        generation_input = generation_input_object.payload()
        return self._execute_generation(
            asset_spec,
            profile,
            character_profile,
            reference_set_id,
            snapshot,
            generation_input_object,
            generation_input,
        )

    def bootstrap_character_reference_asset(self, asset_spec_id: str) -> GenerationResult:
        """Generate one explicit first-reference candidate for an unreferenced character."""

        asset_spec = self.repository.get_asset_spec(asset_spec_id)
        if asset_spec.asset_type != "character":
            raise InvalidCharacterReferenceBootstrap(
                "Character reference bootstrap requires a character AssetSpec."
            )
        if asset_spec.character_profile_id is None:
            raise InvalidCharacterReferenceBootstrap(
                "Character reference bootstrap requires an AssetSpec CharacterProfile."
            )
        self.repository.get_scene(asset_spec.scene_id)
        if not self.generator.supports(asset_spec.asset_type):
            raise UnsupportedGenerationType(
                f"AssetSpec type {asset_spec.asset_type!r} is not executable by this generator."
            )
        profile = self._active_visual_style_profile()
        character_profile = self.repository.get_character_profile(asset_spec.character_profile_id)
        if self.repository.get_latest_character_reference_set(character_profile.id) is not None:
            raise InvalidCharacterReferenceBootstrap(
                "Character reference bootstrap is unavailable after a CharacterReferenceSet exists "
                "for this CharacterProfile."
            )
        self._validate_provider_configuration()
        snapshot = asset_spec_snapshot(asset_spec)
        generation_input_object = self.prompt_composer.compose(
            asset_spec,
            profile,
            character_profile,
        )
        generation_input = generation_input_object.payload()
        return self._execute_generation(
            asset_spec,
            profile,
            character_profile,
            None,
            snapshot,
            generation_input_object,
            generation_input,
        )

    def _execute_generation(
        self,
        asset_spec: AssetSpec,
        profile: VisualStyleProfile,
        character_profile: CharacterProfile | None,
        reference_set_id: str | None,
        snapshot: dict[str, Any],
        generation_input_object: GenerationInput,
        generation_input: dict[str, Any],
    ) -> GenerationResult:
        """Persist one provider attempt after its exact Atlas input is frozen."""

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
                    character_profile_id=(character_profile.id if character_profile else None),
                    character_reference_set_id=reference_set_id,
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
                    character_profile_id=(character_profile.id if character_profile else None),
                    character_reference_set_id=reference_set_id,
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
                character_profile_id=(character_profile.id if character_profile else None),
                character_reference_set_id=reference_set_id,
                provider_key=artifact.provider_key,
                model_key=artifact.model_key,
                provider_request_id=artifact.provider_request_id,
                response_metadata=artifact.response_metadata or {},
                content_digest=hashlib.sha256(artifact.content).hexdigest(),
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

    def _character_profile_for(self, asset_spec: AssetSpec) -> CharacterProfile | None:
        """Resolve a character identity only when the AssetSpec explicitly identifies one."""

        if asset_spec.character_profile_id is None:
            return None
        return self.repository.get_character_profile(asset_spec.character_profile_id)

    def _validate_provider_configuration(self) -> None:
        """Run an adapter's optional preflight before an execution may be recorded."""

        validator = getattr(self.generator, "validate_configuration", None)
        if validator is not None:
            validator()

    def _character_references_for(
        self, character_profile: CharacterProfile
    ) -> tuple[Any, dict[str, Any], tuple[ReferenceImage, ...]]:
        """Resolve, freeze, and verify the highest exact-profile reference set."""

        reference_set = self.repository.get_latest_character_reference_set(character_profile.id)
        if reference_set is None:
            raise MissingCharacterReferenceSet(
                f"CharacterProfile {character_profile.id!r} has no canonical CharacterReferenceSet."
            )
        members = self.repository.list_character_reference_set_members(reference_set.id)
        frozen_members = []
        reference_images = []
        for member in members:
            asset, content = self.repository.load_verified_character_reference_asset(
                member.asset_id, character_profile.id
            )
            if asset.content_digest is None:
                raise ValueError("Verified character reference Assets require a content digest.")
            frozen_members.append(
                {
                    "asset_id": asset.id,
                    "content_digest": asset.content_digest,
                    "media_type": asset.media_type,
                    "position": member.position,
                }
            )
            reference_images.append(
                ReferenceImage(asset.id, asset.media_type, content, member.position)
            )
        return (
            reference_set,
            {
                "intent": "character_identity_grounding",
                "reference_set_id": reference_set.id,
                "reference_set_version": reference_set.version,
                "character_profile": {
                    "profile_id": character_profile.id,
                    "character_key": character_profile.character_key,
                    "version": character_profile.version,
                },
                "members": frozen_members,
            },
            tuple(reference_images),
        )

    def _visual_authority_references_for(
        self, asset_spec: AssetSpec, prior_reference_count: int
    ) -> tuple[dict[str, Any] | None, tuple[ReferenceImage, ...]]:
        """Resolve exact approved non-character authorities and verified reference bytes."""

        try:
            global_authority = self.repository.get_visual_reference_authority(
                self.global_visual_authority_id
            )
        except KeyError:
            return None, ()
        selected = [global_authority]
        metadata = asset_spec.metadata
        family = metadata.get("environment_family")
        if family is not None:
            if not isinstance(family, str) or not family.strip():
                raise ValueError("AssetSpec environment_family must be non-empty text.")
            family_matches = [
                authority
                for authority in self.repository.list_visual_reference_authorities(
                    "environment_family"
                )
                if authority.metadata.get("environment_family") == family.strip()
            ]
            if family_matches:
                selected.append(max(family_matches, key=lambda item: item.version))
        if metadata.get("use_composition_depth") is True:
            selected.append(
                self.repository.get_visual_reference_authority(
                    DEFAULT_COMPOSITION_VISUAL_AUTHORITY_ID
                )
            )
        if metadata.get("special_break_frame") is True:
            selected.append(
                self.repository.get_visual_reference_authority(
                    DEFAULT_BREAK_FRAME_VISUAL_AUTHORITY_ID
                )
            )
        explicit_ids = metadata.get("visual_authority_ids", [])
        if not isinstance(explicit_ids, list) or not all(
            isinstance(authority_id, str) and authority_id.strip() for authority_id in explicit_ids
        ):
            raise ValueError("AssetSpec visual_authority_ids must be a list of IDs.")
        for authority_id in explicit_ids:
            selected.append(self.repository.get_visual_reference_authority(authority_id.strip()))
        selected = self._deduplicated_authorities(selected)
        selected_ids = {authority.id for authority in selected}
        for authority in selected:
            if authority.parent_authority_id is not None and (
                authority.parent_authority_id not in selected_ids
            ):
                raise ValueError("Selected visual authority requires its exact global parent.")
        frozen_authorities = []
        reference_images = []
        next_position = prior_reference_count + 1
        hints_by_id = metadata.get("visual_authority_adapter_hints", {})
        if not isinstance(hints_by_id, dict):
            raise ValueError("Visual authority adapter hints must be an object.")
        for selection_order, authority in enumerate(selected, start=1):
            authority_hints = hints_by_id.get(authority.id, {})
            if not isinstance(authority_hints, dict):
                raise ValueError("Per-authority adapter hints must be objects.")
            frozen_members = []
            for member in self.repository.list_visual_reference_authority_members(authority.id):
                asset, content = self.repository.load_verified_visual_reference_asset(
                    member.asset_id
                )
                if asset.content_digest is None:
                    raise ValueError("Visual authority members require immutable digests.")
                frozen_members.append(
                    {
                        "asset_id": asset.id,
                        "content_digest": asset.content_digest,
                        "media_type": asset.media_type,
                        "position": member.position,
                        "member_role": member.member_role,
                    }
                )
                reference_images.append(
                    ReferenceImage(
                        asset.id,
                        asset.media_type,
                        content,
                        next_position,
                        authority.role,
                        authority.id,
                    )
                )
                next_position += 1
            frozen_authorities.append(
                {
                    "selection_order": selection_order,
                    "usage_role": authority.role,
                    "authority_id": authority.id,
                    "authority_key": authority.authority_key,
                    "authority_version": authority.version,
                    "parent_authority_id": authority.parent_authority_id,
                    "generation_guidance": authority.generation_guidance,
                    "adapter_hints": authority_hints,
                    "members": frozen_members,
                }
            )
        return (
            {
                "schema_version": 1,
                "scene_id": asset_spec.scene_id,
                "asset_spec_id": asset_spec.id,
                "scene_specific_brief": asset_spec.generation_prompt,
                "authorities": frozen_authorities,
            },
            tuple(reference_images),
        )

    @staticmethod
    def _deduplicated_authorities(
        authorities: list[VisualReferenceAuthority],
    ) -> list[VisualReferenceAuthority]:
        unique = []
        seen: set[str] = set()
        for authority in authorities:
            if authority.id not in seen:
                seen.add(authority.id)
                unique.append(authority)
        if sum(item.role == "global_illustration_style" for item in unique) != 1:
            raise ValueError("Generation requires exactly one global illustration authority.")
        return unique

    def _validate_reference_capacity(self, reference_images: tuple[ReferenceImage, ...]) -> None:
        maximum = getattr(self.generator, "max_reference_images", None)
        if maximum is not None and (
            type(maximum) is not int or maximum < 0 or len(reference_images) > maximum
        ):
            raise ValueError("Generator cannot represent the required visual reference recipe.")

    def _generation_parameters(
        self,
        reference_images: tuple[ReferenceImage, ...],
        visual_authority_recipe: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if visual_authority_recipe is None:
            return {}
        parameters = {"reference_image_count": len(reference_images)}
        provider_parameters = getattr(self.generator, "generation_parameters", None)
        if provider_parameters is not None:
            resolved = provider_parameters()
            if not isinstance(resolved, dict):
                raise ValueError("Generator generation parameters must be an object.")
            parameters["provider_adapter"] = resolved
        return parameters

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
