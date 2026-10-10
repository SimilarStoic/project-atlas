"""Isolated persistent-scene mechanical prototype.

This pure domain module remains independent of SQLite, FFmpeg, generation and
publishing. Persistence and media adapters may reconstruct its immutable inputs
and consume its deterministic local raster output without duplicating resolution.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import StrEnum
from typing import Any

SCHEMA_VERSION = 1
RENDER_POLICY = "scene-proof-rgba-nearest-v1"
# Opt-in for new worlds only, persisted in the world's identity: premultiplied 8-bit alpha "over"
# compositing with layers placed 1:1 at integer pixels (any resampling happens once, at admission)
# and optional contact shadows. Worlds without it keep RENDER_POLICY and its exact bytes.
RENDER_POLICY_ALPHA = "scene-rgba-premultiplied-over-v1"
RENDER_POLICIES = frozenset({RENDER_POLICY, RENDER_POLICY_ALPHA})
PRECISION = 6


class SceneModelError(ValueError):
    """Raised when an invariant fails before rendering."""


def _q(value: float | int) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SceneModelError("numeric values must be int or float")
    if not math.isfinite(value):
        raise SceneModelError("NaN and Infinity are forbidden")
    return round(float(value), PRECISION)


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return {field.name: _canonical(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _canonical(value[key]) for key in sorted(value)}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, float):
        return _q(value)
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise SceneModelError(f"unsupported canonical value: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    return json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class PersistenceClass(StrEnum):
    LOCKED_STATIC = "LOCKED_STATIC"
    STATEFUL_STATIC = "STATEFUL_STATIC"
    MOVABLE_PROP = "MOVABLE_PROP"
    ACTOR = "ACTOR"
    EPHEMERAL = "EPHEMERAL"


@dataclass(frozen=True)
class Affine:
    """2D affine matrix: x'=a*x+c*y+e, y'=b*x+d*y+f."""

    a: float = 1.0
    b: float = 0.0
    c: float = 0.0
    d: float = 1.0
    e: float = 0.0
    f: float = 0.0

    def __post_init__(self) -> None:
        for name in ("a", "b", "c", "d", "e", "f"):
            object.__setattr__(self, name, _q(getattr(self, name)))
        if abs(self.a * self.d - self.b * self.c) < 10**-PRECISION:
            raise SceneModelError("singular affine transform")

    @classmethod
    def translate(cls, x: float, y: float) -> Affine:
        return cls(e=x, f=y)

    @classmethod
    def scale_translate(cls, scale_x: float, scale_y: float, x: float, y: float) -> Affine:
        return cls(a=scale_x, d=scale_y, e=x, f=y)

    def compose(self, child: Affine) -> Affine:
        return Affine(
            a=self.a * child.a + self.c * child.b,
            b=self.b * child.a + self.d * child.b,
            c=self.a * child.c + self.c * child.d,
            d=self.b * child.c + self.d * child.d,
            e=self.a * child.e + self.c * child.f + self.e,
            f=self.b * child.e + self.d * child.f + self.f,
        )

    def apply(self, x: float, y: float) -> tuple[float, float]:
        return (_q(self.a * x + self.c * y + self.e), _q(self.b * x + self.d * y + self.f))

    @property
    def scale(self) -> tuple[float, float]:
        return (_q(math.hypot(self.a, self.b)), _q(math.hypot(self.c, self.d)))


@dataclass(frozen=True)
class Plane:
    key: str
    world_to_stage: Affine


@dataclass(frozen=True)
class Camera:
    key: str
    width: int
    height: int
    world_to_pixel: Affine
    fit_policy: str = "locked"

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise SceneModelError("camera viewport must be positive")


@dataclass(frozen=True)
class GeometryContract:
    unit: str
    precision: int
    planes: tuple[Plane, ...]
    camera: Camera

    def __post_init__(self) -> None:
        if self.unit != "WU" or self.precision != PRECISION:
            raise SceneModelError("prototype requires WU and pinned precision")
        if len({plane.key for plane in self.planes}) != len(self.planes):
            raise SceneModelError("duplicate plane key")

    def plane(self, key: str) -> Plane:
        try:
            return next(plane for plane in self.planes if plane.key == key)
        except StopIteration as exc:
            raise SceneModelError(f"missing plane: {key}") from exc


@dataclass(frozen=True)
class RasterAsset:
    asset_id: str
    width: int
    height: int
    rgba: bytes | None
    expected_digest: str

    @classmethod
    def create(cls, asset_id: str, width: int, height: int, rgba: bytes) -> RasterAsset:
        return cls(asset_id, width, height, rgba, hashlib.sha256(rgba).hexdigest())

    def validate(self) -> None:
        if self.rgba is None:
            raise SceneModelError(f"missing source bytes: {self.asset_id}")
        if len(self.rgba) != self.width * self.height * 4:
            raise SceneModelError(f"invalid source length: {self.asset_id}")
        if hashlib.sha256(self.rgba).hexdigest() != self.expected_digest:
            raise SceneModelError(f"source digest mismatch: {self.asset_id}")


@dataclass(frozen=True)
class RasterMask:
    mask_id: str
    width: int
    height: int
    alpha: bytes | None
    expected_digest: str

    @classmethod
    def create(cls, mask_id: str, width: int, height: int, alpha: bytes) -> RasterMask:
        return cls(mask_id, width, height, alpha, hashlib.sha256(alpha).hexdigest())

    def validate(self) -> None:
        if self.alpha is None:
            raise SceneModelError(f"missing mask bytes: {self.mask_id}")
        if len(self.alpha) != self.width * self.height:
            raise SceneModelError(f"invalid mask length: {self.mask_id}")
        if hashlib.sha256(self.alpha).hexdigest() != self.expected_digest:
            raise SceneModelError(f"mask digest mismatch: {self.mask_id}")


@dataclass(frozen=True)
class RenderSlice:
    node_key: str
    asset_id: str
    mask_id: str | None
    local_mapping: Affine = Affine()
    after: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContactShadow:
    """A deterministic soft floor ellipse under a free-standing entity (alpha policy only).

    It is centred on one of the variant's anchors, never drawn while the entity is attached to a
    parent (held or carried objects follow their parent without a floor shadow), and is drawn
    immediately below the entity's own layers.
    """

    anchor_key: str
    radius_x: float
    radius_y: float
    softness: float
    rgb: tuple[int, int, int]
    opacity: int

    def __post_init__(self) -> None:
        for name in ("radius_x", "radius_y", "softness"):
            value = _q(getattr(self, name))
            if value <= 0:
                raise SceneModelError(f"contact shadow {name} must be positive")
            object.__setattr__(self, name, value)
        if (
            not isinstance(self.rgb, tuple)
            or len(self.rgb) != 3
            or any(type(channel) is not int or not 0 <= channel <= 255 for channel in self.rgb)
        ):
            raise SceneModelError("contact shadow rgb must be three 0-255 integers")
        if type(self.opacity) is not int or not 0 < self.opacity <= 255:
            raise SceneModelError("contact shadow opacity must be 1-255")


@dataclass(frozen=True)
class EntityVariant:
    variant_id: str
    entity_key: str
    intrinsic_size_wu: tuple[float, float]
    neutral_scale_id: str
    layers: tuple[RenderSlice, ...]
    anchors: tuple[tuple[str, tuple[float, float]], ...] = ()
    contact_policy_id: str | None = None
    character_authority_id: str | None = None
    partition_complete_source: bool = False
    contact_shadow: ContactShadow | None = None


@dataclass(frozen=True)
class EntityDefinition:
    entity_key: str
    semantic_role: str
    persistence_class: PersistenceClass
    plane_key: str
    initial_variant_id: str
    initial_transform: Affine
    initial_visible: bool = True
    initial_parent_key: str | None = None
    initial_state: str = "default"
    approved_variants: tuple[str, ...] = ()
    purpose: str | None = None
    depth: int = 0


@dataclass(frozen=True)
class EntityState:
    entity_key: str
    variant_id: str
    local_transform: Affine
    effective_transform: Affine
    plane_key: str
    parent_key: str | None
    visible: bool
    state: str


@dataclass(frozen=True)
class DomainBindings:
    visual_plan_id: str
    editorial_scene_ids: tuple[str, ...]
    asset_spec_ids: tuple[str, ...]
    character_profile_id: str
    character_reference_set_id: str
    visual_reference_authority_id: str
    visual_style_profile_id: str


@dataclass(frozen=True)
class PersistentWorld:
    world_key: str
    revision: int
    geometry: GeometryContract
    entities: tuple[EntityDefinition, ...]
    variants: tuple[EntityVariant, ...]
    assets: tuple[RasterAsset, ...]
    masks: tuple[RasterMask, ...]
    style_profile_id: str
    palette_id: str
    wall_treatment_id: str
    lighting_policy_id: str
    bindings: DomainBindings
    definition_digest: str
    render_policy: str = RENDER_POLICY

    def entity(self, key: str) -> EntityDefinition:
        try:
            return next(entity for entity in self.entities if entity.entity_key == key)
        except StopIteration as exc:
            raise SceneModelError(f"unknown entity: {key}") from exc

    def variant(self, variant_id: str) -> EntityVariant:
        try:
            return next(variant for variant in self.variants if variant.variant_id == variant_id)
        except StopIteration as exc:
            raise SceneModelError(f"missing variant: {variant_id}") from exc

    def asset(self, asset_id: str) -> RasterAsset:
        try:
            return next(asset for asset in self.assets if asset.asset_id == asset_id)
        except StopIteration as exc:
            raise SceneModelError(f"missing asset: {asset_id}") from exc

    def mask(self, mask_id: str) -> RasterMask:
        try:
            return next(mask for mask in self.masks if mask.mask_id == mask_id)
        except StopIteration as exc:
            raise SceneModelError(f"missing mask: {mask_id}") from exc


@dataclass(frozen=True)
class Operation:
    action: str
    entity_key: str | None
    value: Any


@dataclass(frozen=True)
class TransitionIntent:
    intent_id: str
    predecessor_digest: str
    editorial_scene_id: str
    operations: tuple[Operation, ...]
    allowed_derived_entities: tuple[str, ...] = ()
    reason: str = "mechanical proof"


@dataclass(frozen=True)
class VariantAdmissionRequest:
    """Explicit approval to append one exact variant identity/content binding."""

    variant_id: str
    authorization_id: str
    reason: str


@dataclass(frozen=True)
class VariantBinding:
    """Immutable identity-to-content admission scoped to one world revision."""

    world_key: str
    world_revision: int
    entity_key: str
    variant_id: str
    variant_content_digest: str
    authorization_id: str
    reason: str


@dataclass(frozen=True)
class StateDiff:
    direct_changes: tuple[dict[str, Any], ...]
    derived_changes: tuple[dict[str, Any], ...]
    inherited: tuple[dict[str, Any], ...]
    introduced_or_hidden: tuple[dict[str, Any], ...]
    unexpected: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class ResolvedState:
    state_id: str
    world_key: str
    world_revision: int
    world_definition_digest: str
    editorial_scene_id: str
    predecessor_digest: str | None
    transition_intent_id: str | None
    admitted_variants: tuple[VariantBinding, ...]
    variant_admission_digest: str
    entities: tuple[EntityState, ...]
    entity_content_digests: tuple[tuple[str, str], ...]
    state_digest: str
    diff: StateDiff | None

    def entity(self, key: str) -> EntityState:
        try:
            return next(entity for entity in self.entities if entity.entity_key == key)
        except StopIteration as exc:
            raise SceneModelError(f"unknown state entity: {key}") from exc


def _state_content(state: ResolvedState) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "world_key": state.world_key,
        "world_revision": state.world_revision,
        "world_definition_digest": state.world_definition_digest,
        "editorial_scene_id": state.editorial_scene_id,
        "predecessor_digest": state.predecessor_digest,
        "transition_intent_id": state.transition_intent_id,
        "admitted_variants": state.admitted_variants,
        "variant_admission_digest": state.variant_admission_digest,
        "entities": state.entities,
        "entity_content_digests": state.entity_content_digests,
    }


def _variant_content_payload(world: PersistentWorld, variant: EntityVariant) -> dict[str, Any]:
    """Exact selected pixels and mappings, independent of registry membership.

    A contact shadow is part of a variant's content only when declared, so variants without
    one keep their historical payload and digests.
    """

    layers = []
    for layer in variant.layers:
        asset = world.asset(layer.asset_id)
        mask = world.mask(layer.mask_id) if layer.mask_id else None
        layers.append(
            {
                "node_key": layer.node_key,
                "asset": {
                    "asset_id": asset.asset_id,
                    "width": asset.width,
                    "height": asset.height,
                    "content_digest": asset.expected_digest,
                },
                "mask": (
                    {
                        "mask_id": mask.mask_id,
                        "width": mask.width,
                        "height": mask.height,
                        "content_digest": mask.expected_digest,
                    }
                    if mask
                    else None
                ),
                "local_mapping": layer.local_mapping,
                "after": layer.after,
            }
        )
    return {
        "variant_id": variant.variant_id,
        "entity_key": variant.entity_key,
        "intrinsic_size_wu": variant.intrinsic_size_wu,
        "neutral_scale_id": variant.neutral_scale_id,
        "character_authority_id": variant.character_authority_id,
        "partition_complete_source": variant.partition_complete_source,
        "anchors": variant.anchors,
        "contact_policy_id": variant.contact_policy_id,
        "compatibility": {
            "character_authority_id": variant.character_authority_id,
            "visual_reference_authority_id": world.bindings.visual_reference_authority_id,
            "visual_style_profile_id": world.bindings.visual_style_profile_id,
            "style_profile_id": world.style_profile_id,
            "palette_id": world.palette_id,
            "wall_treatment_id": world.wall_treatment_id,
            "lighting_policy_id": world.lighting_policy_id,
        },
        "layers": layers,
    } | ({"contact_shadow": variant.contact_shadow} if variant.contact_shadow else {})


def variant_content_digest(world: PersistentWorld, variant: EntityVariant) -> str:
    """Recompute the exact content identity of one variant."""

    return digest(
        {
            "schema_version": SCHEMA_VERSION,
            "world_scope": {"key": world.world_key, "revision": world.revision},
            "variant": _variant_content_payload(world, variant),
        }
    )


def _variant_binding(
    world: PersistentWorld,
    variant: EntityVariant,
    authorization_id: str,
    reason: str,
) -> VariantBinding:
    return VariantBinding(
        world.world_key,
        world.revision,
        variant.entity_key,
        variant.variant_id,
        variant_content_digest(world, variant),
        authorization_id,
        reason,
    )


def variant_admission_payload(bindings: Iterable[VariantBinding]) -> dict[str, Any]:
    ordered = sorted(bindings, key=lambda item: (item.entity_key, item.variant_id))
    return {"schema_version": SCHEMA_VERSION, "admitted_variants": ordered}


def variant_admission_digest(bindings: Iterable[VariantBinding]) -> str:
    return digest(variant_admission_payload(bindings))


def world_definition_payload(world: PersistentWorld) -> dict[str, Any]:
    """Canonical immutable base-world contract for one named revision.

    The approved-variant registry is intentionally outside this digest: admitting a
    later pose expands available state content, not the established room.  Every
    selected variant is instead bound into its ResolvedState.  Base selections and
    their exact bytes remain part of the immutable world definition.
    """

    entities = []
    for entity in sorted(world.entities, key=lambda item: item.entity_key):
        entities.append(
            {
                "entity_key": entity.entity_key,
                "semantic_role": entity.semantic_role,
                "persistence_class": entity.persistence_class,
                "plane_key": entity.plane_key,
                "initial_variant_id": entity.initial_variant_id,
                "initial_transform": entity.initial_transform,
                "initial_visible": entity.initial_visible,
                "initial_parent_key": entity.initial_parent_key,
                "initial_state": entity.initial_state,
                "purpose": entity.purpose,
                "depth": entity.depth,
                "base_variant": _variant_content_payload(
                    world, world.variant(entity.initial_variant_id)
                ),
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "world_key": world.world_key,
        "world_revision": world.revision,
        "geometry": {
            "unit": world.geometry.unit,
            "precision": world.geometry.precision,
            "planes": sorted(
                (_canonical(plane) for plane in world.geometry.planes),
                key=lambda plane: plane["key"],
            ),
            "camera": world.geometry.camera,
        },
        "render_policy": world.render_policy,
        "style_profile_id": world.style_profile_id,
        "palette_id": world.palette_id,
        "wall_treatment_id": world.wall_treatment_id,
        "lighting_policy_id": world.lighting_policy_id,
        "authority_contract": {
            "visual_plan_id": world.bindings.visual_plan_id,
            "character_profile_id": world.bindings.character_profile_id,
            "character_reference_set_id": world.bindings.character_reference_set_id,
            "visual_reference_authority_id": world.bindings.visual_reference_authority_id,
            "visual_style_profile_id": world.bindings.visual_style_profile_id,
        },
        "entities": entities,
    }


def world_definition_digest(world: PersistentWorld) -> str:
    return digest(world_definition_payload(world))


def bind_world_definition(world: PersistentWorld) -> PersistentWorld:
    """Return a frozen world carrying its freshly recomputed content digest."""

    return replace(world, definition_digest=world_definition_digest(world))


def _resolved_entity_content(world: PersistentWorld, state: EntityState) -> dict[str, Any]:
    definition = world.entity(state.entity_key)
    return {
        "entity_state": state,
        "semantic_role": definition.semantic_role,
        "persistence_class": definition.persistence_class,
        "purpose": definition.purpose,
        "depth": definition.depth,
        "selected_variant": _variant_content_payload(world, world.variant(state.variant_id)),
        "plane": world.geometry.plane(state.plane_key),
        "camera": world.geometry.camera,
        "render_policy": world.render_policy,
        "style_profile_id": world.style_profile_id,
        "palette_id": world.palette_id,
        "wall_treatment_id": world.wall_treatment_id,
        "lighting_policy_id": world.lighting_policy_id,
    }


def _entity_content_digests(
    world: PersistentWorld, entities: Iterable[EntityState]
) -> tuple[tuple[str, str], ...]:
    return tuple(
        (entity.entity_key, digest(_resolved_entity_content(world, entity)))
        for entity in sorted(entities, key=lambda item: item.entity_key)
    )


def validate_world(world: PersistentWorld) -> None:
    if world.render_policy not in RENDER_POLICIES:
        raise SceneModelError(f"unknown render policy: {world.render_policy}")
    for variant in world.variants:
        if variant.contact_shadow is None:
            continue
        if world.render_policy != RENDER_POLICY_ALPHA:
            raise SceneModelError("contact shadows require the alpha render policy")
        if variant.contact_shadow.anchor_key not in dict(variant.anchors):
            raise SceneModelError(f"contact shadow anchor missing: {variant.variant_id}")
    entity_keys = [entity.entity_key for entity in world.entities]
    if len(entity_keys) != len(set(entity_keys)):
        raise SceneModelError("duplicate entity key")
    variant_ids = [variant.variant_id for variant in world.variants]
    asset_ids = [asset.asset_id for asset in world.assets]
    mask_ids = [mask.mask_id for mask in world.masks]
    if len(variant_ids) != len(set(variant_ids)):
        raise SceneModelError("duplicate variant identity")
    if len(asset_ids) != len(set(asset_ids)):
        raise SceneModelError("duplicate asset identity")
    if len(mask_ids) != len(set(mask_ids)):
        raise SceneModelError("duplicate mask identity")
    variants = {variant.variant_id: variant for variant in world.variants}
    node_owners: dict[str, str] = {}
    for entity in world.entities:
        world.geometry.plane(entity.plane_key)
        if entity.initial_variant_id not in entity.approved_variants:
            raise SceneModelError(f"initial variant not approved: {entity.entity_key}")
        for variant_id in entity.approved_variants:
            variant = variants.get(variant_id)
            if variant is None or variant.entity_key != entity.entity_key:
                raise SceneModelError(f"invalid variant membership: {variant_id}")
        if entity.initial_parent_key is not None and entity.initial_parent_key not in entity_keys:
            raise SceneModelError(f"missing parent: {entity.initial_parent_key}")
    for variant in world.variants:
        for layer in variant.layers:
            owner = node_owners.setdefault(layer.node_key, variant.entity_key)
            if owner != variant.entity_key:
                raise SceneModelError(f"render node shared across entities: {layer.node_key}")
            asset = world.asset(layer.asset_id)
            asset.validate()
            if layer.mask_id:
                mask = world.mask(layer.mask_id)
                mask.validate()
                if (mask.width, mask.height) != (asset.width, asset.height):
                    raise SceneModelError("mask dimensions differ from source")
        if variant.partition_complete_source:
            _validate_partition(world, variant)
    _validate_parent_graph(
        {entity.entity_key: entity.initial_parent_key for entity in world.entities}
    )
    initial_variants = tuple(world.variant(entity.initial_variant_id) for entity in world.entities)
    _compile_order(world, initial_variants)
    recomputed = world_definition_digest(world)
    if not world.definition_digest or world.definition_digest != recomputed:
        raise SceneModelError("world definition digest mismatch")


def _validate_partition(world: PersistentWorld, variant: EntityVariant) -> None:
    if len(variant.layers) < 2:
        raise SceneModelError("partitioned variant needs multiple slices")
    assets = {layer.asset_id for layer in variant.layers}
    if len(assets) != 1:
        raise SceneModelError("partition slices must share one complete source")
    asset = world.asset(next(iter(assets)))
    coverage = [0] * (asset.width * asset.height)
    for layer in variant.layers:
        if not layer.mask_id:
            raise SceneModelError("partition slice requires mask")
        mask = world.mask(layer.mask_id)
        assert mask.alpha is not None
        for index, value in enumerate(mask.alpha):
            if value not in (0, 255):
                raise SceneModelError("prototype masks must be binary")
            coverage[index] += int(value > 0)
    assert asset.rgba is not None
    for index, count in enumerate(coverage):
        source_alpha = asset.rgba[index * 4 + 3]
        if (source_alpha > 0 and count != 1) or (source_alpha == 0 and count != 0):
            raise SceneModelError("mask partition has gap or overlap")


def _validate_parent_graph(parents: Mapping[str, str | None]) -> None:
    for start in parents:
        seen: set[str] = set()
        key: str | None = start
        while key is not None:
            if key in seen:
                raise SceneModelError("parent cycle")
            seen.add(key)
            key = parents.get(key)


def _compile_order(world: PersistentWorld, variants: Iterable[EntityVariant]) -> tuple[str, ...]:
    layers = [layer for variant in variants for layer in variant.layers]
    by_key = {layer.node_key: layer for layer in layers}
    incoming = {layer.node_key: {key for key in layer.after if key in by_key} for layer in layers}
    result: list[str] = []
    while incoming:
        ready = sorted(key for key, deps in incoming.items() if not deps)
        if not ready:
            raise SceneModelError("contradictory render-slice order")
        for key in ready:
            result.append(key)
            incoming.pop(key)
            for deps in incoming.values():
                deps.discard(key)
    return tuple(result)


def base_state(
    world: PersistentWorld,
    editorial_scene_id: str = "scene-base",
    state_id: str = "state-base",
) -> ResolvedState:
    validate_world(world)
    admissions = tuple(
        sorted(
            (
                _variant_binding(
                    world,
                    world.variant(variant_id),
                    "base-world-admission",
                    "declared before base-state resolution",
                )
                for entity in world.entities
                for variant_id in entity.approved_variants
            ),
            key=lambda item: (item.entity_key, item.variant_id),
        )
    )
    local = {
        entity.entity_key: EntityState(
            entity.entity_key,
            entity.initial_variant_id,
            entity.initial_transform,
            Affine(),
            entity.plane_key,
            entity.initial_parent_key,
            entity.initial_visible,
            entity.initial_state,
        )
        for entity in world.entities
    }
    entities = _with_effective(local)
    entity_bindings = _entity_content_digests(world, entities)
    provisional = ResolvedState(
        state_id=state_id,
        world_key=world.world_key,
        world_revision=world.revision,
        world_definition_digest=world.definition_digest,
        editorial_scene_id=editorial_scene_id,
        predecessor_digest=None,
        transition_intent_id=None,
        admitted_variants=admissions,
        variant_admission_digest=variant_admission_digest(admissions),
        entities=entities,
        entity_content_digests=entity_bindings,
        state_digest="",
        diff=None,
    )
    resolved = replace(provisional, state_digest=digest(_state_content(provisional)))
    _validate_resolved_state_binding(world, resolved)
    return resolved


def _with_effective(states: Mapping[str, EntityState]) -> tuple[EntityState, ...]:
    _validate_parent_graph({key: state.parent_key for key, state in states.items()})
    cache: dict[str, Affine] = {}

    def effective(key: str) -> Affine:
        if key in cache:
            return cache[key]
        state = states[key]
        transform = (
            effective(state.parent_key).compose(state.local_transform)
            if state.parent_key
            else state.local_transform
        )
        cache[key] = transform
        return transform

    return tuple(replace(states[key], effective_transform=effective(key)) for key in sorted(states))


_PERMITTED = {
    PersistenceClass.LOCKED_STATIC: frozenset(),
    PersistenceClass.STATEFUL_STATIC: frozenset({"set_variant", "set_state"}),
    PersistenceClass.MOVABLE_PROP: frozenset(
        {"set_variant", "set_state", "set_visible", "set_transform", "attach"}
    ),
    PersistenceClass.ACTOR: frozenset({"set_variant", "set_transform", "attach"}),
    PersistenceClass.EPHEMERAL: frozenset({"set_visible", "set_state"}),
}


def resolve(
    world: PersistentWorld,
    predecessor: ResolvedState,
    intent: TransitionIntent,
    state_id: str,
) -> ResolvedState:
    validate_world(world)
    _validate_resolved_state_binding(world, predecessor)
    if predecessor.state_digest != intent.predecessor_digest:
        raise SceneModelError("stale predecessor")
    before = {state.entity_key: state for state in predecessor.entities}
    current = dict(before)
    admissions = {binding.variant_id: binding for binding in predecessor.admitted_variants}
    direct: list[dict[str, Any]] = []
    seen: set[tuple[str | None, str]] = set()
    for operation in intent.operations:
        if operation.action != "admit_variant":
            continue
        if operation.entity_key is None or operation.entity_key not in current:
            raise SceneModelError(f"spontaneous entity introduction: {operation.entity_key}")
        if not isinstance(operation.value, VariantAdmissionRequest):
            raise SceneModelError("variant admission requires typed request")
        request = operation.value
        if not request.authorization_id or not request.reason:
            raise SceneModelError("variant admission requires authorization and reason")
        if request.variant_id in admissions:
            raise SceneModelError(f"variant identity already admitted: {request.variant_id}")
        definition = world.entity(operation.entity_key)
        if request.variant_id not in definition.approved_variants:
            raise SceneModelError(f"variant not approved for admission: {request.variant_id}")
        variant = world.variant(request.variant_id)
        if variant.entity_key != operation.entity_key:
            raise SceneModelError("variant entity mismatch")
        current_variant = world.variant(current[operation.entity_key].variant_id)
        if current_variant.neutral_scale_id != variant.neutral_scale_id:
            raise SceneModelError("neutral world scale changed")
        binding = _variant_binding(world, variant, request.authorization_id, request.reason)
        admissions[request.variant_id] = binding
        direct.append(
            {
                "entity_key": operation.entity_key,
                "operation": operation.action,
                "before": None,
                "after": _canonical(binding),
            }
        )
    for operation in intent.operations:
        if operation.action == "admit_variant":
            continue
        if operation.action in {
            "set_camera",
            "set_style",
            "set_wall_treatment",
            "set_slice_transform",
        }:
            raise SceneModelError(f"unauthorized world mutation: {operation.action}")
        if operation.entity_key is None or operation.entity_key not in current:
            raise SceneModelError(f"spontaneous entity introduction: {operation.entity_key}")
        if (operation.entity_key, operation.action) in seen:
            raise SceneModelError("duplicate operation")
        seen.add((operation.entity_key, operation.action))
        definition = world.entity(operation.entity_key)
        if operation.action not in _PERMITTED[definition.persistence_class]:
            raise SceneModelError(
                f"{definition.persistence_class} forbids {operation.action}: {operation.entity_key}"
            )
        old = current[operation.entity_key]
        if operation.action == "set_variant" and str(operation.value) not in admissions:
            raise SceneModelError(f"variant not admitted: {operation.value}")
        new = _apply_operation(world, definition, old, operation)
        if new == old:
            raise SceneModelError("operation does not change state")
        current[operation.entity_key] = new
        direct.append(
            {
                "entity_key": operation.entity_key,
                "operation": operation.action,
                "before": _canonical(old),
                "after": _canonical(new),
            }
        )
    materialized = _with_effective(current)
    after = {state.entity_key: state for state in materialized}
    direct_keys = {operation.entity_key for operation in intent.operations}
    attachment_keys = {
        operation.entity_key for operation in intent.operations if operation.action == "attach"
    }
    derived: list[dict[str, Any]] = []
    for key in sorted(after):
        if before[key].effective_transform != after[key].effective_transform:
            if key not in direct_keys:
                if key not in intent.allowed_derived_entities:
                    raise SceneModelError(f"derived child outside permitted closure: {key}")
                derived.append(
                    {
                        "entity_key": key,
                        "property": "effective_transform",
                        "before": _canonical(before[key].effective_transform),
                        "after": _canonical(after[key].effective_transform),
                        "cause": after[key].parent_key,
                    }
                )
            elif (
                key in attachment_keys or before[key].local_transform == after[key].local_transform
            ):
                derived.append(
                    {
                        "entity_key": key,
                        "property": "effective_transform",
                        "before": _canonical(before[key].effective_transform),
                        "after": _canonical(after[key].effective_transform),
                        "cause": "attachment",
                    }
                )
    introduced = tuple(
        {
            "entity_key": key,
            "before": before[key].visible,
            "after": after[key].visible,
        }
        for key in sorted(after)
        if before[key].visible != after[key].visible
    )
    inherited = tuple(
        {"entity_key": key, "render_input_digest": entity_render_digest(world, after[key])}
        for key in sorted(after)
        if key not in direct_keys and before[key] == after[key]
    )
    state_diff = StateDiff(tuple(direct), tuple(derived), inherited, introduced)
    entity_bindings = _entity_content_digests(world, materialized)
    next_admissions = tuple(
        sorted(admissions.values(), key=lambda item: (item.entity_key, item.variant_id))
    )
    provisional = ResolvedState(
        state_id=state_id,
        world_key=world.world_key,
        world_revision=world.revision,
        world_definition_digest=world.definition_digest,
        editorial_scene_id=intent.editorial_scene_id,
        predecessor_digest=predecessor.state_digest,
        transition_intent_id=intent.intent_id,
        admitted_variants=next_admissions,
        variant_admission_digest=variant_admission_digest(next_admissions),
        entities=materialized,
        entity_content_digests=entity_bindings,
        state_digest="",
        diff=state_diff,
    )
    _validate_state_sources(world, provisional)
    resolved = replace(provisional, state_digest=digest(_state_content(provisional)))
    _validate_resolved_state_binding(world, resolved)
    return resolved


def _apply_operation(
    world: PersistentWorld,
    definition: EntityDefinition,
    state: EntityState,
    operation: Operation,
) -> EntityState:
    if operation.action == "set_variant":
        variant_id = str(operation.value)
        if variant_id not in definition.approved_variants:
            raise SceneModelError(f"unauthorized variant: {variant_id}")
        old_variant = world.variant(state.variant_id)
        new_variant = world.variant(variant_id)
        if old_variant.neutral_scale_id != new_variant.neutral_scale_id:
            raise SceneModelError("neutral world scale changed")
        return replace(state, variant_id=variant_id)
    if operation.action == "set_state":
        return replace(state, state=str(operation.value))
    if operation.action == "set_visible":
        if not isinstance(operation.value, bool):
            raise SceneModelError("visibility must be boolean")
        return replace(state, visible=operation.value)
    if operation.action == "set_transform":
        if not isinstance(operation.value, Affine):
            raise SceneModelError("transform value must be Affine")
        if operation.value.scale != state.local_transform.scale:
            raise SceneModelError("scale cannot be used to fake movement")
        return replace(state, local_transform=operation.value)
    if operation.action == "attach":
        parent_key, transform = operation.value
        if parent_key is not None:
            world.entity(parent_key)
        if not isinstance(transform, Affine):
            raise SceneModelError("attachment transform must be Affine")
        if transform.scale != state.local_transform.scale:
            raise SceneModelError("attachment cannot alter intrinsic scale")
        return replace(state, parent_key=parent_key, local_transform=transform)
    raise SceneModelError(f"unknown operation: {operation.action}")


def _validate_state_sources(world: PersistentWorld, state: ResolvedState) -> None:
    for entity in state.entities:
        variant = world.variant(entity.variant_id)
        if variant.entity_key != entity.entity_key:
            raise SceneModelError("variant entity mismatch")
        for layer in variant.layers:
            world.asset(layer.asset_id).validate()
            if layer.mask_id:
                world.mask(layer.mask_id).validate()


def _validate_resolved_state_binding(world: PersistentWorld, state: ResolvedState) -> None:
    if state.world_key != world.world_key or state.world_revision != world.revision:
        raise SceneModelError("world mismatch")
    if state.world_definition_digest != world.definition_digest:
        raise SceneModelError("world definition mismatch")
    if state.variant_admission_digest != variant_admission_digest(state.admitted_variants):
        raise SceneModelError("variant admission digest mismatch")
    admission_ids = [binding.variant_id for binding in state.admitted_variants]
    if len(admission_ids) != len(set(admission_ids)):
        raise SceneModelError("duplicate admitted variant identity")
    for binding in state.admitted_variants:
        if (binding.world_key, binding.world_revision) != (world.world_key, world.revision):
            raise SceneModelError("variant admission world mismatch")
        variant = world.variant(binding.variant_id)
        if variant.entity_key != binding.entity_key:
            raise SceneModelError("variant admission entity mismatch")
        if variant_content_digest(world, variant) != binding.variant_content_digest:
            raise SceneModelError("admitted variant content mismatch")
    selected_ids = {entity.variant_id for entity in state.entities}
    if not selected_ids.issubset(set(admission_ids)):
        raise SceneModelError("selected variant is not admitted")
    expected_bindings = _entity_content_digests(world, state.entities)
    if state.entity_content_digests != expected_bindings:
        raise SceneModelError("resolved entity content mismatch")
    if state.state_digest and state.state_digest != digest(_state_content(state)):
        raise SceneModelError("resolved state digest mismatch")


def entity_render_digest(world: PersistentWorld, state: EntityState) -> str:
    return digest(_resolved_entity_content(world, state))


@dataclass(frozen=True)
class RenderResult:
    rgba: bytes
    composite_digest: str
    layer_digests: tuple[tuple[str, str], ...]
    layer_render_input_digests: tuple[tuple[str, str], ...]
    owner_map: tuple[str | None, ...]


def render(world: PersistentWorld, state: ResolvedState) -> RenderResult:
    validate_world(world)
    _validate_resolved_state_binding(world, state)
    _validate_state_sources(world, state)
    # Dispatch from the persisted policy; the legacy renderer below is unchanged.
    if world.render_policy == RENDER_POLICY_ALPHA:
        return _render_alpha(world, state)
    active_variants = tuple(
        world.variant(entity.variant_id) for entity in state.entities if entity.visible
    )
    order = _compile_order(world, active_variants)
    layer_to_state: dict[str, tuple[RenderSlice, EntityState]] = {}
    for entity in state.entities:
        if not entity.visible:
            continue
        for layer in world.variant(entity.variant_id).layers:
            layer_to_state[layer.node_key] = (layer, entity)
    camera = world.geometry.camera
    composite = bytearray(camera.width * camera.height * 4)
    owners: list[str | None] = [None] * (camera.width * camera.height)
    layer_hashes: list[tuple[str, str]] = []
    signatures: list[tuple[str, str]] = []
    for node_key in order:
        layer, entity = layer_to_state[node_key]
        raster = _raster_layer(world, entity, layer)
        layer_hashes.append((node_key, hashlib.sha256(raster).hexdigest()))
        signatures.append((node_key, _layer_signature(world, entity, layer)))
        for pixel in range(camera.width * camera.height):
            offset = pixel * 4
            alpha = raster[offset + 3]
            if alpha == 0:
                continue
            if alpha != 255:
                raise SceneModelError("prototype renderer requires binary alpha")
            composite[offset : offset + 4] = raster[offset : offset + 4]
            owners[pixel] = entity.entity_key
    result = bytes(composite)
    return RenderResult(
        result,
        hashlib.sha256(result).hexdigest(),
        tuple(layer_hashes),
        tuple(signatures),
        tuple(owners),
    )


def _layer_signature(world: PersistentWorld, state: EntityState, layer: RenderSlice) -> str:
    asset = world.asset(layer.asset_id)
    variant = world.variant(state.variant_id)
    definition = world.entity(state.entity_key)
    return digest(
        {
            "variant_id": variant.variant_id,
            "intrinsic_size_wu": variant.intrinsic_size_wu,
            "neutral_scale_id": variant.neutral_scale_id,
            "asset_id": asset.asset_id,
            "content_digest": asset.expected_digest,
            "local_mapping": layer.local_mapping,
            "effective_transform": state.effective_transform,
            "plane": world.geometry.plane(state.plane_key),
            "camera": world.geometry.camera,
            "depth": definition.depth,
            "mask_id": layer.mask_id,
            "mask_digest": world.mask(layer.mask_id).expected_digest if layer.mask_id else None,
            "render_policy": world.render_policy,
            "style_profile_id": world.style_profile_id,
            "palette_id": world.palette_id,
            "wall_treatment_id": world.wall_treatment_id,
            "lighting_policy_id": world.lighting_policy_id,
        }
    )


def _pixel_offset(
    world: PersistentWorld, state: EntityState, layer: RenderSlice
) -> tuple[int, int]:
    """The alpha policy places every layer 1:1 at an integer pixel offset."""

    transform = (
        world.geometry.camera.world_to_pixel.compose(
            world.geometry.plane(state.plane_key).world_to_stage
        )
        .compose(state.effective_transform)
        .compose(layer.local_mapping)
    )
    if (transform.a, transform.b, transform.c, transform.d) != (1, 0, 0, 1) or not (
        float(transform.e).is_integer() and float(transform.f).is_integer()
    ):
        raise SceneModelError(
            "alpha render policy places layers 1:1 at integer pixels; resample at admission"
        )
    return int(transform.e), int(transform.f)


def _over(canvas: bytearray, offset: int, rgb: tuple[int, int, int] | bytes, alpha: int) -> None:
    """Premultiplied 8-bit 'over' of one straight-colour source pixel onto the canvas."""

    inverse = 255 - alpha
    for channel in range(3):
        premultiplied = (rgb[channel] * alpha + 127) // 255
        canvas[offset + channel] = premultiplied + (canvas[offset + channel] * inverse + 127) // 255
    canvas[offset + 3] = alpha + (canvas[offset + 3] * inverse + 127) // 255


def contact_shadow_alpha(shadow: ContactShadow, dx: float, dy: float) -> int:
    """Deterministic shadow opacity at a pixel-centre offset from the anchor."""

    distance = math.hypot(dx / shadow.radius_x, dy / shadow.radius_y)
    band = shadow.softness / min(shadow.radius_x, shadow.radius_y)
    t = min(1.0, max(0.0, (1.0 - distance) / band))
    return int(shadow.opacity * t * t * (3.0 - 2.0 * t) + 0.5)


def _render_alpha(world: PersistentWorld, state: ResolvedState) -> RenderResult:
    """Premultiplied 'over' compositing of 1:1 layers, with optional contact shadows."""

    active_variants = tuple(
        world.variant(entity.variant_id) for entity in state.entities if entity.visible
    )
    order = _compile_order(world, active_variants)
    layer_to_state: dict[str, tuple[RenderSlice, EntityState]] = {}
    for entity in state.entities:
        if not entity.visible:
            continue
        for layer in world.variant(entity.variant_id).layers:
            layer_to_state[layer.node_key] = (layer, entity)
    camera = world.geometry.camera
    width, height = camera.width, camera.height
    canvas = bytearray(width * height * 4)
    owners: list[str | None] = [None] * (width * height)
    layer_hashes: list[tuple[str, str]] = []
    signatures: list[tuple[str, str]] = []
    shadowed: set[str] = set()
    for node_key in order:
        layer, entity = layer_to_state[node_key]
        variant = world.variant(entity.variant_id)
        shadow = variant.contact_shadow
        if shadow is not None and entity.parent_key is None and entity.entity_key not in shadowed:
            shadowed.add(entity.entity_key)
            anchor = dict(variant.anchors)[shadow.anchor_key]
            centre_x, centre_y = (
                camera.world_to_pixel.compose(world.geometry.plane(entity.plane_key).world_to_stage)
                .compose(entity.effective_transform)
                .apply(*anchor)
            )
            for y in range(
                max(0, math.floor(centre_y - shadow.radius_y)),
                min(height, math.ceil(centre_y + shadow.radius_y) + 1),
            ):
                for x in range(
                    max(0, math.floor(centre_x - shadow.radius_x)),
                    min(width, math.ceil(centre_x + shadow.radius_x) + 1),
                ):
                    alpha = contact_shadow_alpha(shadow, x + 0.5 - centre_x, y + 0.5 - centre_y)
                    if alpha:
                        _over(canvas, (y * width + x) * 4, shadow.rgb, alpha)
                        owners[y * width + x] = f"{entity.entity_key}.shadow"
        asset = world.asset(layer.asset_id)
        asset.validate()
        assert asset.rgba is not None
        mask = world.mask(layer.mask_id) if layer.mask_id else None
        if mask:
            mask.validate()
            assert mask.alpha is not None
        left, top = _pixel_offset(world, entity, layer)
        for sy in range(asset.height):
            y = top + sy
            if not 0 <= y < height:
                continue
            for sx in range(asset.width):
                x = left + sx
                if not 0 <= x < width:
                    continue
                source = (sy * asset.width + sx) * 4
                alpha = asset.rgba[source + 3]
                if mask:
                    alpha = (alpha * mask.alpha[sy * asset.width + sx] + 127) // 255
                if alpha == 0:
                    continue
                target = (y * width + x) * 4
                if alpha == 255:
                    canvas[target : target + 3] = asset.rgba[source : source + 3]
                    canvas[target + 3] = 255
                else:
                    _over(canvas, target, asset.rgba[source : source + 3], alpha)
                owners[y * width + x] = entity.entity_key
        placement = {"offset": [left, top], "asset": asset.expected_digest}
        placement["mask"] = mask.expected_digest if mask else None
        layer_hashes.append((node_key, digest(placement)))
        signatures.append((node_key, _layer_signature(world, entity, layer)))
    for offset in range(0, len(canvas), 4):
        alpha = canvas[offset + 3]
        if 0 < alpha < 255:
            for channel in range(3):
                canvas[offset + channel] = min(
                    255, (canvas[offset + channel] * 255 + alpha // 2) // alpha
                )
    result = bytes(canvas)
    return RenderResult(
        result,
        hashlib.sha256(result).hexdigest(),
        tuple(layer_hashes),
        tuple(signatures),
        tuple(owners),
    )


def _raster_layer(world: PersistentWorld, state: EntityState, layer: RenderSlice) -> bytes:
    asset = world.asset(layer.asset_id)
    asset.validate()
    assert asset.rgba is not None
    mask = world.mask(layer.mask_id) if layer.mask_id else None
    if mask:
        mask.validate()
        assert mask.alpha is not None
    camera = world.geometry.camera
    transform = (
        camera.world_to_pixel.compose(world.geometry.plane(state.plane_key).world_to_stage)
        .compose(state.effective_transform)
        .compose(layer.local_mapping)
    )
    output = bytearray(camera.width * camera.height * 4)
    for sy in range(asset.height):
        for sx in range(asset.width):
            source_pixel = sy * asset.width + sx
            source_offset = source_pixel * 4
            alpha = asset.rgba[source_offset + 3]
            if mask:
                alpha = min(alpha, mask.alpha[source_pixel])
            if alpha == 0:
                continue
            px, py = transform.apply(sx, sy)
            x, y = round(px), round(py)
            if 0 <= x < camera.width and 0 <= y < camera.height:
                target = (y * camera.width + x) * 4
                output[target : target + 4] = asset.rgba[source_offset : source_offset + 3] + bytes(
                    [alpha]
                )
    return bytes(output)


def plan_generation_demand(
    world: PersistentWorld,
    predecessor: ResolvedState,
    intent: TransitionIntent,
    available_variants: Iterable[str],
) -> dict[str, list[str]]:
    available = set(available_variants)
    needs = []
    changed = set()
    for operation in intent.operations:
        if operation.entity_key:
            changed.add(operation.entity_key)
        if operation.action == "set_variant" and operation.value not in available:
            needs.append(f"{operation.entity_key}:{operation.value}")
    exact_reuse = [
        entity.entity_key for entity in predecessor.entities if entity.entity_key not in changed
    ]
    return {"needs_new_variant": sorted(needs), "exact_reuse": sorted(exact_reuse)}


def density_problems(world: PersistentWorld) -> tuple[str, ...]:
    environmental = {"background", "wall", "window", "painting", "floor", "chair", "table"}
    return tuple(
        f"{entity.entity_key}:missing-purpose"
        for entity in world.entities
        if entity.semantic_role in environmental and not entity.purpose
    )


def snapshot_payload(world: PersistentWorld, state: ResolvedState) -> dict[str, Any]:
    _validate_resolved_state_binding(world, state)
    selected_content = [
        _resolved_entity_content(world, entity)
        for entity in sorted(state.entities, key=lambda item: item.entity_key)
    ]
    selected_assets = {
        layer.asset_id
        for entity in state.entities
        for layer in world.variant(entity.variant_id).layers
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "world": {"key": world.world_key, "revision": world.revision},
        "world_definition_digest": state.world_definition_digest,
        "state_id": state.state_id,
        "predecessor_digest": state.predecessor_digest,
        "transition_intent_id": state.transition_intent_id,
        "editorial_scene_id": state.editorial_scene_id,
        "variant_admission_digest": state.variant_admission_digest,
        "admitted_variants": state.admitted_variants,
        "camera": _canonical(world.geometry.camera),
        "geometry_contract_digest": digest(world.geometry),
        "entities": [_canonical(entity) for entity in state.entities],
        "selected_entity_content": selected_content,
        "assets": [
            {"asset_id": asset.asset_id, "digest": asset.expected_digest}
            for asset in sorted(world.assets, key=lambda item: item.asset_id)
            if asset.asset_id in selected_assets
        ],
        "authority_and_style": _canonical(world.bindings)
        | {
            "style_profile_id": world.style_profile_id,
            "palette_id": world.palette_id,
            "wall_treatment_id": world.wall_treatment_id,
            "lighting_policy_id": world.lighting_policy_id,
        },
        "lineage": _canonical(state.diff) if state.diff else None,
        "render_policy": world.render_policy,
        "complete_state_digest": state.state_digest,
    }


_SNAPSHOT_KEYS = frozenset(
    {
        "schema_version",
        "world",
        "world_definition_digest",
        "state_id",
        "predecessor_digest",
        "transition_intent_id",
        "editorial_scene_id",
        "variant_admission_digest",
        "admitted_variants",
        "camera",
        "geometry_contract_digest",
        "entities",
        "selected_entity_content",
        "assets",
        "authority_and_style",
        "lineage",
        "render_policy",
        "complete_state_digest",
    }
)


def validate_snapshot_payload(payload: Mapping[str, Any]) -> None:
    if set(payload) != _SNAPSHOT_KEYS:
        raise SceneModelError("unknown or missing snapshot fields")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise SceneModelError("unknown snapshot schema")
    canonical_json(payload)


def rgba_asset(
    asset_id: str, width: int, height: int, color: tuple[int, int, int, int]
) -> RasterAsset:
    return RasterAsset.create(asset_id, width, height, bytes(color) * (width * height))


def mask_rows(mask_id: str, width: int, height: int, selected_rows: range) -> RasterMask:
    selected = set(selected_rows)
    return RasterMask.create(
        mask_id,
        width,
        height,
        bytes(255 if row in selected else 0 for row in range(height) for _ in range(width)),
    )


def build_fixture_world() -> PersistentWorld:
    """Build deterministic synthetic evidence; never loads production/runtime state."""

    pixel_to_wu = Affine(a=0.5, d=0.5)

    def layer(
        node_key: str,
        asset_id: str,
        mask_id: str | None = None,
        *,
        after: tuple[str, ...] = (),
        mapping: Affine = pixel_to_wu,
    ) -> RenderSlice:
        return RenderSlice(node_key, asset_id, mask_id, mapping, after)

    assets = [
        rgba_asset("asset-wall", 48, 36, (240, 232, 210, 255)),
        rgba_asset("asset-window", 8, 6, (120, 190, 220, 255)),
        rgba_asset("asset-painting", 6, 5, (220, 120, 80, 255)),
        rgba_asset("asset-floor", 48, 8, (190, 160, 120, 255)),
        rgba_asset("asset-chair", 10, 14, (110, 70, 40, 255)),
        rgba_asset("asset-chair-clone", 10, 14, (110, 70, 40, 255)),
        rgba_asset("asset-table", 18, 7, (95, 55, 30, 255)),
        rgba_asset("asset-occluder", 5, 14, (60, 90, 120, 255)),
        rgba_asset("asset-actor-a", 8, 10, (210, 150, 90, 255)),
        rgba_asset("asset-actor-b", 12, 15, (205, 145, 85, 255)),
        rgba_asset("asset-actor-c", 6, 12, (200, 140, 80, 255)),
        rgba_asset("asset-report", 4, 4, (250, 250, 245, 255)),
        rgba_asset("asset-laptop-off", 7, 4, (70, 70, 75, 255)),
        rgba_asset("asset-laptop-on", 7, 4, (80, 130, 180, 255)),
        rgba_asset("asset-spark", 3, 3, (250, 220, 20, 255)),
    ]
    masks = [
        mask_rows("mask-chair-top", 10, 14, range(0, 7)),
        mask_rows("mask-chair-bottom", 10, 14, range(7, 14)),
    ]
    actor_dimensions = {"a": (8, 10, 8), "b": (12, 15, 12), "c": (6, 12, 10)}
    for name, (width, height, body_rows) in actor_dimensions.items():
        masks.extend(
            [
                mask_rows(f"mask-actor-{name}-body", width, height, range(0, body_rows)),
                mask_rows(f"mask-actor-{name}-paw", width, height, range(body_rows, height)),
            ]
        )
    variants = [
        EntityVariant(
            "wall-v1",
            "wall",
            (24, 18),
            "wall-scale",
            (layer("wall.main", "asset-wall"),),
        ),
        EntityVariant(
            "window-v1",
            "window",
            (4, 3),
            "wall-object-scale",
            (layer("window.main", "asset-window", after=("wall.main",)),),
        ),
        EntityVariant(
            "painting-v1",
            "painting",
            (3, 2.5),
            "wall-object-scale",
            (layer("painting.main", "asset-painting", after=("wall.main",)),),
        ),
        EntityVariant(
            "floor-v1",
            "floor",
            (24, 4),
            "floor-scale",
            (layer("floor.main", "asset-floor", after=("wall.main",)),),
        ),
        EntityVariant(
            "chair-v1",
            "chair",
            (5, 7),
            "chair-scale",
            (
                layer("chair.top", "asset-chair", "mask-chair-top", after=("floor.main",)),
                layer("chair.bottom", "asset-chair", "mask-chair-bottom", after=("floor.main",)),
            ),
            partition_complete_source=True,
        ),
        EntityVariant(
            "chair-identical-unauthorized",
            "chair",
            (5, 7),
            "chair-scale",
            (layer("chair.clone", "asset-chair-clone"),),
        ),
        EntityVariant(
            "table-v1",
            "table",
            (9, 3.5),
            "table-scale",
            (
                layer(
                    "table.main",
                    "asset-table",
                    None,
                    after=("chair.top", "chair.bottom", "actor.paw"),
                ),
            ),
        ),
        EntityVariant(
            "occluder-v1",
            "occluder",
            (2.5, 7),
            "occluder-scale",
            (layer("occluder.main", "asset-occluder", None, after=("chair.top", "chair.bottom")),),
        ),
        EntityVariant(
            "report-v1",
            "report",
            (2, 2),
            "report-scale",
            (layer("report.main", "asset-report", after=("actor.body",)),),
        ),
        EntityVariant(
            "laptop-off",
            "laptop",
            (3.5, 2),
            "laptop-scale",
            (layer("laptop.main", "asset-laptop-off", after=("table.main",)),),
        ),
        EntityVariant(
            "laptop-on",
            "laptop",
            (3.5, 2),
            "laptop-scale",
            (layer("laptop.on", "asset-laptop-on", after=("table.main",)),),
        ),
        EntityVariant(
            "spark-v1",
            "spark",
            (1.5, 1.5),
            "spark-scale",
            (layer("spark.main", "asset-spark", after=("actor.paw",)),),
        ),
    ]
    actor_geometry = {
        "a": ((4.0, 5.0), Affine(a=0.5, d=0.5)),
        "b": ((4.0, 5.0), Affine(a=1 / 3, d=1 / 3)),
        "c": ((4.5, 5.0), Affine(a=0.75, d=5 / 12)),
    }
    for name, (intrinsic_size, mapping) in actor_geometry.items():
        variants.append(
            EntityVariant(
                f"actor-{name}",
                "actor",
                intrinsic_size,
                "actor-neutral-v1",
                (
                    layer(
                        "actor.body",
                        f"asset-actor-{name}",
                        f"mask-actor-{name}-body",
                        after=("floor.main",),
                        mapping=mapping,
                    ),
                    layer(
                        "actor.paw",
                        f"asset-actor-{name}",
                        f"mask-actor-{name}-paw",
                        after=("report.main",),
                        mapping=mapping,
                    ),
                ),
                character_authority_id="character-profile-core-v3",
                partition_complete_source=True,
            )
        )
    entities = (
        EntityDefinition(
            "wall",
            "wall",
            PersistenceClass.LOCKED_STATIC,
            "wall-plane",
            "wall-v1",
            Affine(),
            approved_variants=("wall-v1",),
            purpose="location",
            depth=0,
        ),
        EntityDefinition(
            "window",
            "window",
            PersistenceClass.LOCKED_STATIC,
            "wall-plane",
            "window-v1",
            Affine.translate(1.5, 1.5),
            approved_variants=("window-v1",),
            purpose="useful-depth",
            depth=1,
        ),
        EntityDefinition(
            "painting",
            "painting",
            PersistenceClass.LOCKED_STATIC,
            "wall-plane",
            "painting-v1",
            Affine.translate(8, 1.5),
            approved_variants=("painting-v1",),
            purpose="semantic-meaning",
            depth=1,
        ),
        EntityDefinition(
            "floor",
            "floor",
            PersistenceClass.LOCKED_STATIC,
            "floor-plane",
            "floor-v1",
            Affine.translate(0, 14),
            approved_variants=("floor-v1",),
            purpose="location",
            depth=1,
        ),
        EntityDefinition(
            "chair",
            "chair",
            PersistenceClass.LOCKED_STATIC,
            "floor-plane",
            "chair-v1",
            Affine.translate(4.5, 7.5),
            approved_variants=("chair-v1", "chair-identical-unauthorized"),
            purpose="action",
            depth=2,
        ),
        EntityDefinition(
            "table",
            "table",
            PersistenceClass.LOCKED_STATIC,
            "floor-plane",
            "table-v1",
            Affine.translate(3, 11),
            approved_variants=("table-v1",),
            purpose="action",
            depth=5,
        ),
        EntityDefinition(
            "occluder",
            "prop",
            PersistenceClass.MOVABLE_PROP,
            "floor-plane",
            "occluder-v1",
            Affine.translate(6, 7.5),
            approved_variants=("occluder-v1",),
            purpose="mechanical-disocclusion",
            depth=6,
        ),
        EntityDefinition(
            "actor",
            "actor",
            PersistenceClass.ACTOR,
            "floor-plane",
            "actor-a",
            Affine.translate(14, 8),
            approved_variants=("actor-a", "actor-b", "actor-c"),
            purpose="action",
            depth=3,
        ),
        EntityDefinition(
            "report",
            "document",
            PersistenceClass.MOVABLE_PROP,
            "floor-plane",
            "report-v1",
            Affine.translate(11, 11.5),
            initial_visible=False,
            approved_variants=("report-v1",),
            purpose="semantic-meaning",
            depth=4,
        ),
        EntityDefinition(
            "laptop",
            "stateful-prop",
            PersistenceClass.STATEFUL_STATIC,
            "floor-plane",
            "laptop-off",
            Affine.translate(2.5, -1.5),
            initial_parent_key="table",
            approved_variants=("laptop-off", "laptop-on"),
            purpose="action",
            depth=6,
        ),
        EntityDefinition(
            "spark",
            "effect",
            PersistenceClass.EPHEMERAL,
            "floor-plane",
            "spark-v1",
            Affine.translate(19, 4),
            initial_visible=False,
            approved_variants=("spark-v1",),
            purpose="deliberate-visual-joke",
            depth=7,
        ),
    )
    world = PersistentWorld(
        "similarstoic-proof-world",
        1,
        GeometryContract(
            "WU",
            PRECISION,
            (Plane("wall-plane", Affine()), Plane("floor-plane", Affine())),
            Camera("locked-camera-v1", 48, 36, Affine(a=2, d=2)),
        ),
        entities,
        tuple(variants),
        tuple(assets),
        tuple(masks),
        "visual-style-profile-fixture-v1",
        "palette-fixture-v1",
        "wall-treatment-flat-v1",
        "lighting-none-v1",
        DomainBindings(
            "visual-plan-fixture",
            ("scene-base", "scene-1", "scene-2", "scene-3"),
            tuple(f"asset-spec-{key}" for key in ("wall", "actor", "report")),
            "character-profile-core-v3",
            "character-reference-set-fixture",
            "visual-reference-authority-fixture",
            "visual-style-profile-fixture-v1",
        ),
        "",
    )
    return bind_world_definition(world)


def build_fixture_states(world: PersistentWorld) -> tuple[ResolvedState, ...]:
    base = base_state(world)
    intent1 = TransitionIntent(
        "intent-1", base.state_digest, "scene-1", (Operation("set_variant", "actor", "actor-b"),)
    )
    state1 = resolve(world, base, intent1, "state-1")
    intent2 = TransitionIntent(
        "intent-2",
        state1.state_digest,
        "scene-2",
        (
            Operation("set_visible", "report", True),
            Operation("attach", "report", ("actor", Affine.translate(1, 1.5))),
            Operation("set_variant", "laptop", "laptop-on"),
        ),
    )
    state2 = resolve(world, state1, intent2, "state-2")
    intent3 = TransitionIntent(
        "intent-3",
        state2.state_digest,
        "scene-3",
        (
            Operation("set_variant", "actor", "actor-c"),
            Operation("attach", "report", ("table", Affine.translate(4, -1))),
            Operation("set_state", "report", "reviewed"),
            Operation("set_transform", "occluder", Affine.translate(17.5, 7.5)),
        ),
    )
    state3 = resolve(world, state2, intent3, "state-3")
    return base, state1, state2, state3
