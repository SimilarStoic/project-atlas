"""Durable adapter for the pure persistent-scene domain model."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

from project_atlas.scene_model import (
    SCHEMA_VERSION,
    Affine,
    Camera,
    DomainBindings,
    EntityDefinition,
    EntityState,
    EntityVariant,
    GeometryContract,
    PersistenceClass,
    PersistentWorld,
    Plane,
    RasterAsset,
    RasterMask,
    RenderSlice,
    ResolvedState,
    StateDiff,
    TransitionIntent,
    VariantBinding,
    canonical_json,
    digest,
    entity_render_digest,
    resolve,
    snapshot_payload,
    validate_world,
    variant_admission_digest,
    variant_content_digest,
    world_definition_digest,
)

RESOLVER_VERSION = "persistent-scene-domain-v1"


@dataclass(frozen=True)
class PersistentSceneMediaContext:
    """Exact immutable aggregate required by a final-media consumer."""

    world_id: str
    admission_catalog_id: str
    transition_intent_id: str
    world: PersistentWorld
    state: ResolvedState


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _load_document(value: str) -> Any:
    loaded = json.loads(value)
    if canonical_json(loaded) != value:
        raise ValueError("Persistent-scene JSON is not canonical.")
    return loaded


def _affine(value: dict[str, Any]) -> Affine:
    if set(value) != {"a", "b", "c", "d", "e", "f"}:
        raise ValueError("Invalid persisted affine document.")
    return Affine(**value)


def _state_diff(value: Any) -> StateDiff | None:
    if value is None:
        return None
    if set(value) != {
        "direct_changes",
        "derived_changes",
        "inherited",
        "introduced_or_hidden",
        "unexpected",
    }:
        raise ValueError("Invalid persisted state-diff document.")
    return StateDiff(
        tuple(value["direct_changes"]),
        tuple(value["derived_changes"]),
        tuple(value["inherited"]),
        tuple(value["introduced_or_hidden"]),
        tuple(value["unexpected"]),
    )


class PersistentSceneRepositoryMixin:
    """Narrow immutable aggregate persistence; no generic mutable CRUD."""

    connection: sqlite3.Connection
    asset_storage_root: Any

    def _profile_digest(self, getter: str, identity: str | None) -> str | None:
        if identity is None:
            return None
        return digest(asdict(getattr(self, getter)(identity)))

    def _reference_set_digest(self, identity: str | None) -> str | None:
        if identity is None:
            return None
        reference_set = self.get_character_reference_set(identity)
        members = self.list_character_reference_set_members(identity)
        return digest({"reference_set": asdict(reference_set), "members": members})

    def _authority_digest(self, identity: str) -> str:
        return digest(self.visual_reference_authority_payload(identity))

    def _asset_bytes_for_world(self, asset_id: str, expected_digest: str, plan_id: str) -> bytes:
        asset = self.get_asset(asset_id)
        if asset.content_digest is None or asset.content_digest != expected_digest:
            raise ValueError("Persistent-scene Asset requires the exact immutable content digest.")
        spec = self.get_asset_spec(asset.asset_spec_id)
        scene = self.get_scene(spec.scene_id)
        if scene.visual_plan_id != plan_id:
            raise ValueError("Persistent-scene Assets must belong to the same VisualPlan.")
        content = self.managed_scene_asset_path(asset.id).read_bytes()
        if sha256(content).hexdigest() != expected_digest:
            raise ValueError("Persistent-scene Asset bytes do not match their digest.")
        return content

    @staticmethod
    def _entity_payload(entity: EntityDefinition) -> dict[str, Any]:
        return {
            "entity_key": entity.entity_key,
            "semantic_role": entity.semantic_role,
            "purpose": entity.purpose,
            "persistence_class": entity.persistence_class,
            "default_plane_key": entity.plane_key,
            "default_parent_entity_key": entity.initial_parent_key,
            "initial_variant_id": entity.initial_variant_id,
            "initial_transform": entity.initial_transform,
            "initial_visible": entity.initial_visible,
            "initial_state": entity.initial_state,
            "depth": entity.depth,
        }

    @staticmethod
    def _layer_payload(
        world: PersistentWorld, variant: EntityVariant, layer: RenderSlice, position: int
    ) -> dict[str, Any]:
        asset = world.asset(layer.asset_id)
        mask = world.mask(layer.mask_id) if layer.mask_id else None
        return {
            "position": position,
            "node_key": layer.node_key,
            "asset_id": asset.asset_id,
            "asset_content_digest": asset.expected_digest,
            "asset_width": asset.width,
            "asset_height": asset.height,
            "mask_id": mask.mask_id if mask else None,
            "mask_content_digest": mask.expected_digest if mask else None,
            "mask_width": mask.width if mask else None,
            "mask_height": mask.height if mask else None,
            "local_mapping": layer.local_mapping,
            "after": layer.after,
            "partition_complete_source": variant.partition_complete_source,
        }

    def _validate_world_ownership(self, world: PersistentWorld) -> None:
        plan = self.get_visual_plan(world.bindings.visual_plan_id)
        scene_ids = {item.id for item in self.list_scenes_for_visual_plan(plan.id)}
        if not set(world.bindings.editorial_scene_ids).issubset(scene_ids):
            raise ValueError("Persistent world references a Scene outside its VisualPlan.")
        for spec_id in world.bindings.asset_spec_ids:
            spec = self.get_asset_spec(spec_id)
            if self.get_scene(spec.scene_id).visual_plan_id != plan.id:
                raise ValueError("Persistent world references an AssetSpec outside its VisualPlan.")
        self.get_visual_style_profile(world.bindings.visual_style_profile_id)
        self.get_character_profile(world.bindings.character_profile_id)
        reference_set = self.get_character_reference_set(world.bindings.character_reference_set_id)
        if reference_set.character_profile_id != world.bindings.character_profile_id:
            raise ValueError("Persistent world CharacterReferenceSet does not match its profile.")
        self.get_visual_reference_authority(world.bindings.visual_reference_authority_id)
        for asset in world.assets:
            self._asset_bytes_for_world(
                asset.asset_id, asset.expected_digest, world.bindings.visual_plan_id
            )
        for mask in world.masks:
            self._asset_bytes_for_world(
                mask.mask_id, mask.expected_digest, world.bindings.visual_plan_id
            )

    def _insert_variant(
        self,
        world_id: str,
        world: PersistentWorld,
        variant: EntityVariant,
        *,
        acceptance_actor: str,
        acceptance_reference: str,
        acceptance_evidence: dict[str, Any],
    ) -> None:
        stamp = _now()
        for position, layer in enumerate(variant.layers, 1):
            payload = self._layer_payload(world, variant, layer, position)
            mask_contract = {
                key: payload[key]
                for key in (
                    "asset_width",
                    "asset_height",
                    "mask_width",
                    "mask_height",
                    "partition_complete_source",
                )
            }
            self.connection.execute(
                "INSERT INTO persistent_scene_entity_variant_layers VALUES "
                "(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    variant.variant_id,
                    position,
                    layer.node_key,
                    layer.asset_id,
                    payload["asset_content_digest"],
                    layer.mask_id,
                    payload["mask_content_digest"],
                    canonical_json(layer.local_mapping),
                    canonical_json(mask_contract),
                    payload["mask_content_digest"] if layer.mask_id else None,
                    canonical_json({"after": layer.after}),
                    "partition" if variant.partition_complete_source else "complete",
                    digest(payload),
                    stamp,
                ),
            )
        evidence_json = canonical_json(acceptance_evidence)
        compatibility = {
            "character_profile_id": variant.character_authority_id,
            "visual_reference_authority_id": world.bindings.visual_reference_authority_id,
            "visual_style_profile_id": world.bindings.visual_style_profile_id,
            "style_profile_id": world.style_profile_id,
            "palette_id": world.palette_id,
            "wall_treatment_id": world.wall_treatment_id,
            "lighting_policy_id": world.lighting_policy_id,
        }
        self.connection.execute(
            "INSERT INTO persistent_scene_entity_variants VALUES "
            "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                variant.variant_id,
                world_id,
                variant.entity_key,
                variant.variant_id,
                1,
                SCHEMA_VERSION,
                len(variant.layers),
                canonical_json(variant.intrinsic_size_wu),
                variant.neutral_scale_id,
                canonical_json(variant.anchors),
                canonical_json({"contact_policy_id": variant.contact_policy_id}),
                int(variant.partition_complete_source),
                variant.character_authority_id,
                (
                    world.bindings.character_reference_set_id
                    if variant.character_authority_id
                    else None
                ),
                world.bindings.visual_style_profile_id,
                canonical_json(compatibility),
                acceptance_actor,
                acceptance_reference,
                evidence_json,
                digest(acceptance_evidence),
                variant_content_digest(world, variant),
                stamp,
            ),
        )

    def _insert_intent(
        self,
        world_id: str,
        intent: TransitionIntent,
        *,
        kind: str,
        predecessor_state_id: str | None,
        authorization_actor: str,
        authorization_reference: str,
    ) -> str:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "world_revision_id": world_id,
            "kind": kind,
            "predecessor_state_id": predecessor_state_id,
            "predecessor_state_digest": intent.predecessor_digest or None,
            "target_scene_id": intent.editorial_scene_id,
            "operations": intent.operations,
            "allowed_dependency_closure": intent.allowed_derived_entities,
            "authorization_actor": authorization_actor,
            "authorization_reference": authorization_reference,
            "reason": intent.reason,
        }
        self.connection.execute(
            "INSERT INTO persistent_scene_transition_intents VALUES "
            "(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                intent.intent_id,
                world_id,
                kind,
                intent.editorial_scene_id,
                predecessor_state_id,
                intent.predecessor_digest or None,
                canonical_json(intent.operations),
                canonical_json(intent.allowed_derived_entities),
                authorization_actor,
                authorization_reference,
                intent.reason,
                SCHEMA_VERSION,
                digest(payload),
                _now(),
            ),
        )
        return digest(payload)

    def _insert_catalog(
        self,
        world_id: str,
        catalog_id: str,
        intent_id: str,
        bindings: tuple[VariantBinding, ...],
        new_bindings: tuple[VariantBinding, ...],
        *,
        kind: str,
        predecessor_catalog_id: str | None,
        authorization_actor: str,
        authorization_reference: str,
    ) -> None:
        stamp = _now()
        for binding in new_bindings:
            event_reference = binding.authorization_id or authorization_reference
            event = {
                "world_revision_id": world_id,
                "catalog_id": catalog_id,
                "entity_key": binding.entity_key,
                "variant_id": binding.variant_id,
                "variant_content_digest": binding.variant_content_digest,
                "authorization_actor": authorization_actor,
                "authorization_reference": event_reference,
                "reason": binding.reason,
            }
            self.connection.execute(
                "INSERT INTO persistent_scene_variant_admissions VALUES (?,?,?,?,?,?,?,?)",
                (
                    f"{catalog_id}:{binding.variant_id}",
                    catalog_id,
                    binding.variant_id,
                    authorization_actor,
                    event_reference,
                    binding.reason,
                    digest(event),
                    stamp,
                ),
            )
        self.connection.execute(
            "INSERT INTO persistent_scene_admission_catalogs VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                catalog_id,
                world_id,
                kind,
                predecessor_catalog_id,
                intent_id,
                SCHEMA_VERSION,
                len(new_bindings),
                len(bindings),
                variant_admission_digest(bindings),
                stamp,
            ),
        )

    def _insert_state(
        self,
        world_id: str,
        world: PersistentWorld,
        state: ResolvedState,
        intent_id: str,
        predecessor_state_id: str | None,
        catalog_id: str,
    ) -> None:
        stamp = _now()
        direct = (
            {item.get("entity_key") for item in state.diff.direct_changes} if state.diff else set()
        )
        derived = (
            {item.get("entity_key") for item in state.diff.derived_changes} if state.diff else set()
        )
        entity_digests = dict(state.entity_content_digests)
        for entity in state.entities:
            if state.diff is None:
                change_class = "base"
            elif entity.entity_key in direct and entity.entity_key in derived:
                change_class = "mixed"
            elif entity.entity_key in direct:
                change_class = "direct"
            elif entity.entity_key in derived:
                change_class = "derived"
            else:
                change_class = "inherited"
            lineage = {"change_class": change_class, "state_diff": state.diff}
            self.connection.execute(
                "INSERT INTO persistent_scene_resolved_entities VALUES "
                "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    state.state_id,
                    world_id,
                    entity.entity_key,
                    entity.variant_id,
                    canonical_json(entity.local_transform),
                    canonical_json(entity.effective_transform),
                    entity.plane_key,
                    entity.parent_key,
                    int(entity.visible),
                    entity.state,
                    canonical_json({"parent_key": entity.parent_key}),
                    canonical_json({"plane_key": entity.plane_key}),
                    change_class,
                    predecessor_state_id if change_class == "inherited" else None,
                    canonical_json(lineage),
                    digest(lineage),
                    entity_digests[entity.entity_key],
                    entity_render_digest(world, entity),
                    stamp,
                ),
            )
        membership = tuple(sorted(state.entity_content_digests))
        diff_json = canonical_json(state.diff)
        self.connection.execute(
            "INSERT INTO persistent_scene_resolved_states VALUES "
            "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                state.state_id,
                world_id,
                intent_id,
                predecessor_state_id,
                state.editorial_scene_id,
                catalog_id,
                state.world_definition_digest,
                state.variant_admission_digest,
                len(state.entities),
                digest(membership),
                state.state_digest,
                diff_json,
                digest(state.diff),
                SCHEMA_VERSION,
                RESOLVER_VERSION,
                stamp,
            ),
        )

    def create_persistent_scene_world(
        self,
        world_id: str,
        world: PersistentWorld,
        base_state: ResolvedState,
        *,
        base_intent_id: str,
        base_catalog_id: str,
        authorization_actor: str,
        authorization_reference: str,
    ) -> tuple[PersistentWorld, ResolvedState]:
        """Atomically seal one world revision and its explicit base aggregate."""

        validate_world(world)
        snapshot_payload(world, base_state)
        if base_state.predecessor_digest is not None or base_state.transition_intent_id is not None:
            raise ValueError(
                "Persistent-scene base state must have no predecessor or domain intent."
            )
        if base_state.world_definition_digest != world.definition_digest:
            raise ValueError("Base state must bind the exact supplied world.")
        self._validate_world_ownership(world)
        if self.connection.in_transaction:
            self.connection.commit()
        try:
            self.connection.execute("BEGIN IMMEDIATE")
            for variant in world.variants:
                self._insert_variant(
                    world_id,
                    world,
                    variant,
                    acceptance_actor=authorization_actor,
                    acceptance_reference=authorization_reference,
                    acceptance_evidence={"kind": "base-world", "variant_id": variant.variant_id},
                )
            stamp = _now()
            for entity in world.entities:
                payload = self._entity_payload(entity)
                self.connection.execute(
                    "INSERT INTO persistent_scene_entities VALUES "
                    "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        world_id,
                        entity.entity_key,
                        entity.semantic_role,
                        entity.purpose or "explicit-purpose-required",
                        entity.persistence_class.value,
                        entity.plane_key,
                        entity.initial_parent_key,
                        canonical_json(
                            {
                                "initial_variant_size": world.variant(
                                    entity.initial_variant_id
                                ).intrinsic_size_wu,
                                "neutral_scale_id": world.variant(
                                    entity.initial_variant_id
                                ).neutral_scale_id,
                            }
                        ),
                        canonical_json(world.variant(entity.initial_variant_id).anchors),
                        entity.initial_variant_id,
                        canonical_json(entity.initial_transform),
                        int(entity.initial_visible),
                        entity.initial_state,
                        entity.depth,
                        digest(payload),
                        stamp,
                    ),
                )
            authority_id = world.bindings.visual_reference_authority_id
            authority_digest = self._authority_digest(authority_id)
            self.connection.execute(
                "INSERT INTO persistent_scene_world_visual_authorities VALUES (?,?,?,?,?,?)",
                (world_id, 1, authority_id, "world", authority_digest, stamp),
            )
            geometry = {
                "unit": world.geometry.unit,
                "precision": world.geometry.precision,
                "planes": world.geometry.planes,
            }
            treatment = {
                "style_profile_id": world.style_profile_id,
                "palette_id": world.palette_id,
                "wall_treatment_id": world.wall_treatment_id,
                "lighting_policy_id": world.lighting_policy_id,
                "bindings": world.bindings,
            }
            membership = {
                "entities": sorted(
                    (entity.entity_key, digest(self._entity_payload(entity)))
                    for entity in world.entities
                ),
                "authorities": [(authority_id, authority_digest)],
            }
            style_digest = self._profile_digest(
                "get_visual_style_profile", world.bindings.visual_style_profile_id
            )
            character_digest = self._profile_digest(
                "get_character_profile", world.bindings.character_profile_id
            )
            reference_digest = self._reference_set_digest(world.bindings.character_reference_set_id)
            self.connection.execute(
                "INSERT INTO persistent_scene_world_revisions VALUES "
                "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    world_id,
                    world.bindings.visual_plan_id,
                    world.world_key,
                    world.revision,
                    None,
                    SCHEMA_VERSION,
                    RESOLVER_VERSION,
                    canonical_json(geometry),
                    canonical_json(world.geometry.camera),
                    canonical_json(treatment),
                    world.bindings.visual_style_profile_id,
                    style_digest,
                    world.bindings.character_profile_id,
                    character_digest,
                    world.bindings.character_reference_set_id,
                    reference_digest,
                    len(world.entities),
                    1,
                    digest(membership),
                    world.definition_digest,
                    stamp,
                ),
            )
            base_intent = TransitionIntent(
                base_intent_id,
                "",
                base_state.editorial_scene_id,
                (),
                (),
                "base persistent world",
            )
            self._insert_intent(
                world_id,
                base_intent,
                kind="base",
                predecessor_state_id=None,
                authorization_actor=authorization_actor,
                authorization_reference=authorization_reference,
            )
            self._insert_catalog(
                world_id,
                base_catalog_id,
                base_intent_id,
                base_state.admitted_variants,
                base_state.admitted_variants,
                kind="base",
                predecessor_catalog_id=None,
                authorization_actor=authorization_actor,
                authorization_reference=authorization_reference,
            )
            self._insert_state(
                world_id,
                world,
                base_state,
                base_intent_id,
                None,
                base_catalog_id,
            )
            loaded_world = self.get_persistent_scene_world(world_id)
            loaded_state = self.get_persistent_scene_state(base_state.state_id)
            if loaded_world.definition_digest != world.definition_digest:
                raise ValueError("Reloaded persistent world digest differs.")
            if loaded_state.state_digest != base_state.state_digest:
                raise ValueError("Reloaded base state digest differs.")
            self.connection.commit()
            return loaded_world, loaded_state
        except Exception:
            self.connection.rollback()
            raise

    def register_persistent_scene_variant(
        self,
        world_id: str,
        expanded_world: PersistentWorld,
        variant_id: str,
        *,
        acceptance_actor: str,
        acceptance_reference: str,
        acceptance_evidence: dict[str, Any],
    ) -> EntityVariant:
        """Seal one accepted variant without admitting it to any state lineage."""

        persisted = self.get_persistent_scene_world(world_id)
        if expanded_world.definition_digest != persisted.definition_digest:
            raise ValueError("New variant cannot redefine the persistent world.")
        validate_world(expanded_world)
        self._validate_world_ownership(expanded_world)
        variant = expanded_world.variant(variant_id)
        if self.connection.in_transaction:
            self.connection.commit()
        try:
            self.connection.execute("BEGIN IMMEDIATE")
            self._insert_variant(
                world_id,
                expanded_world,
                variant,
                acceptance_actor=acceptance_actor,
                acceptance_reference=acceptance_reference,
                acceptance_evidence=acceptance_evidence,
            )
            loaded = self._load_variant(world_id, variant_id)
            if variant_content_digest(expanded_world, variant) != variant_content_digest(
                self.get_persistent_scene_world(world_id), loaded
            ):
                raise ValueError("Reloaded variant digest differs.")
            self.connection.commit()
            return loaded
        except Exception:
            self.connection.rollback()
            raise

    def resolve_and_persist_scene_state(
        self,
        world_id: str,
        predecessor_state_id: str,
        intent: TransitionIntent,
        state_id: str,
        *,
        catalog_id: str | None = None,
        authorization_actor: str,
        authorization_reference: str,
    ) -> ResolvedState:
        """Resolve through the pure domain engine and atomically seal one child state."""

        world = self.get_persistent_scene_world(world_id)
        predecessor = self.get_persistent_scene_state(predecessor_state_id)
        if predecessor.world_key != world.world_key:
            raise ValueError("Predecessor belongs to another persistent world.")
        scene = self.get_scene(intent.editorial_scene_id)
        if scene.visual_plan_id != world.bindings.visual_plan_id:
            raise ValueError("Transition target Scene belongs to another VisualPlan.")
        result = resolve(world, predecessor, intent, state_id)
        predecessor_row = self.connection.execute(
            "SELECT admission_catalog_id FROM persistent_scene_resolved_states WHERE id=?",
            (predecessor_state_id,),
        ).fetchone()
        assert predecessor_row is not None
        predecessor_catalog_id = predecessor_row["admission_catalog_id"]
        prior_ids = {item.variant_id for item in predecessor.admitted_variants}
        new_bindings = tuple(
            item for item in result.admitted_variants if item.variant_id not in prior_ids
        )
        if new_bindings and not catalog_id:
            raise ValueError("A variant admission requires an exact child catalog ID.")
        if not new_bindings and catalog_id is not None:
            raise ValueError("A catalog cannot be created without an explicit admission delta.")
        chosen_catalog = catalog_id or predecessor_catalog_id
        if self.connection.in_transaction:
            self.connection.commit()
        try:
            self.connection.execute("BEGIN IMMEDIATE")
            self._insert_intent(
                world_id,
                intent,
                kind="delta",
                predecessor_state_id=predecessor_state_id,
                authorization_actor=authorization_actor,
                authorization_reference=authorization_reference,
            )
            if new_bindings:
                self._insert_catalog(
                    world_id,
                    chosen_catalog,
                    intent.intent_id,
                    result.admitted_variants,
                    new_bindings,
                    kind="delta",
                    predecessor_catalog_id=predecessor_catalog_id,
                    authorization_actor=authorization_actor,
                    authorization_reference=authorization_reference,
                )
            self._insert_state(
                world_id,
                world,
                result,
                intent.intent_id,
                predecessor_state_id,
                chosen_catalog,
            )
            loaded = self.get_persistent_scene_state(state_id)
            if loaded.state_digest != result.state_digest:
                raise ValueError("Reloaded resolved state digest differs.")
            self.connection.commit()
            return loaded
        except Exception:
            self.connection.rollback()
            raise

    def _load_variant(self, world_id: str, variant_id: str) -> EntityVariant:
        row = self.connection.execute(
            "SELECT * FROM persistent_scene_entity_variants WHERE id=? AND world_revision_id=?",
            (variant_id, world_id),
        ).fetchone()
        if row is None:
            raise KeyError(variant_id)
        layers = []
        for layer in self.connection.execute(
            "SELECT * FROM persistent_scene_entity_variant_layers "
            "WHERE variant_id=? ORDER BY position",
            (variant_id,),
        ):
            mapping = _load_document(layer["local_mapping_json"])
            ordering = _load_document(layer["ordering_json"])
            if set(ordering) != {"after"}:
                raise ValueError("Invalid persisted layer ordering document.")
            layers.append(
                RenderSlice(
                    layer["node_key"],
                    layer["asset_id"],
                    layer["mask_asset_id"],
                    _affine(mapping),
                    tuple(ordering["after"]),
                )
            )
        if len(layers) != row["expected_layer_count"]:
            raise ValueError("Persisted variant layer count mismatch.")
        anchors = _load_document(row["anchors_json"])
        contact = _load_document(row["contact_contract_json"])
        if set(contact) != {"contact_policy_id"}:
            raise ValueError("Invalid persisted contact contract.")
        variant = EntityVariant(
            row["id"],
            row["entity_key"],
            tuple(_load_document(row["intrinsic_size_json"])),
            row["neutral_scale_id"],
            tuple(layers),
            tuple((item[0], tuple(item[1])) for item in anchors),
            contact["contact_policy_id"],
            row["character_profile_id"],
            bool(row["partition_complete_source"]),
        )
        evidence = _load_document(row["acceptance_evidence_json"])
        if digest(evidence) != row["acceptance_evidence_digest"]:
            raise ValueError("Persisted variant acceptance evidence mismatch.")
        return variant

    def get_persistent_scene_world(self, world_id: str) -> PersistentWorld:
        """Reconstruct and independently validate one sealed world revision."""

        row = self.connection.execute(
            "SELECT * FROM persistent_scene_world_revisions WHERE id=?", (world_id,)
        ).fetchone()
        if row is None:
            raise KeyError(world_id)
        treatment = _load_document(row["treatment_json"])
        if set(treatment) != {
            "bindings",
            "lighting_policy_id",
            "palette_id",
            "style_profile_id",
            "wall_treatment_id",
        }:
            raise ValueError("Invalid persisted world treatment document.")
        binding_data = treatment["bindings"]
        bindings = DomainBindings(
            binding_data["visual_plan_id"],
            tuple(binding_data["editorial_scene_ids"]),
            tuple(binding_data["asset_spec_ids"]),
            binding_data["character_profile_id"],
            binding_data["character_reference_set_id"],
            binding_data["visual_reference_authority_id"],
            binding_data["visual_style_profile_id"],
        )
        geometry_data = _load_document(row["geometry_json"])
        camera_data = _load_document(row["camera_json"])
        geometry = GeometryContract(
            geometry_data["unit"],
            geometry_data["precision"],
            tuple(
                Plane(item["key"], _affine(item["world_to_stage"]))
                for item in geometry_data["planes"]
            ),
            Camera(
                camera_data["key"],
                camera_data["width"],
                camera_data["height"],
                _affine(camera_data["world_to_pixel"]),
                camera_data["fit_policy"],
            ),
        )
        variants = tuple(
            self._load_variant(world_id, item["id"])
            for item in self.connection.execute(
                "SELECT id FROM persistent_scene_entity_variants "
                "WHERE world_revision_id=? ORDER BY id",
                (world_id,),
            )
        )
        assets: dict[str, RasterAsset] = {}
        masks: dict[str, RasterMask] = {}
        for variant in variants:
            for layer in self.connection.execute(
                "SELECT * FROM persistent_scene_entity_variant_layers "
                "WHERE variant_id=? ORDER BY position",
                (variant.variant_id,),
            ):
                contract = _load_document(layer["mask_contract_json"])
                content = self._asset_bytes_for_world(
                    layer["asset_id"], layer["asset_content_digest"], bindings.visual_plan_id
                )
                candidate = RasterAsset(
                    layer["asset_id"],
                    contract["asset_width"],
                    contract["asset_height"],
                    content,
                    layer["asset_content_digest"],
                )
                if candidate.asset_id in assets and assets[candidate.asset_id] != candidate:
                    raise ValueError("Persisted Asset identity is rebound.")
                assets[candidate.asset_id] = candidate
                if layer["mask_asset_id"]:
                    alpha = self._asset_bytes_for_world(
                        layer["mask_asset_id"],
                        layer["mask_content_digest"],
                        bindings.visual_plan_id,
                    )
                    mask = RasterMask(
                        layer["mask_asset_id"],
                        contract["mask_width"],
                        contract["mask_height"],
                        alpha,
                        layer["mask_content_digest"],
                    )
                    if mask.mask_id in masks and masks[mask.mask_id] != mask:
                        raise ValueError("Persisted mask identity is rebound.")
                    masks[mask.mask_id] = mask
        variants_by_entity: dict[str, list[str]] = {}
        for variant in variants:
            variants_by_entity.setdefault(variant.entity_key, []).append(variant.variant_id)
        entities = []
        entity_rows = list(
            self.connection.execute(
                "SELECT * FROM persistent_scene_entities WHERE world_revision_id=? "
                "ORDER BY entity_key",
                (world_id,),
            )
        )
        for item in entity_rows:
            entity = EntityDefinition(
                item["entity_key"],
                item["semantic_role"],
                PersistenceClass(item["persistence_class"]),
                item["default_plane_key"],
                item["initial_variant_id"],
                _affine(_load_document(item["initial_transform_json"])),
                bool(item["initial_visible"]),
                item["default_parent_entity_key"],
                item["initial_state"],
                tuple(sorted(variants_by_entity.get(item["entity_key"], []))),
                item["purpose"],
                item["depth"],
            )
            if digest(self._entity_payload(entity)) != item["entity_definition_digest"]:
                raise ValueError("Persisted entity definition digest mismatch.")
            entities.append(entity)
        world = PersistentWorld(
            row["world_key"],
            row["revision"],
            geometry,
            tuple(entities),
            variants,
            tuple(assets[key] for key in sorted(assets)),
            tuple(masks[key] for key in sorted(masks)),
            treatment["style_profile_id"],
            treatment["palette_id"],
            treatment["wall_treatment_id"],
            treatment["lighting_policy_id"],
            bindings,
            row["world_definition_digest"],
        )
        validate_world(world)
        if world_definition_digest(world) != row["world_definition_digest"]:
            raise ValueError("Persisted world definition digest mismatch.")
        for variant in variants:
            variant_row = self.connection.execute(
                "SELECT * FROM persistent_scene_entity_variants WHERE id=?",
                (variant.variant_id,),
            ).fetchone()
            assert variant_row is not None
            if variant_content_digest(world, variant) != variant_row["variant_content_digest"]:
                raise ValueError("Persisted variant content digest mismatch.")
            expected_compatibility = {
                "character_profile_id": variant.character_authority_id,
                "visual_reference_authority_id": bindings.visual_reference_authority_id,
                "visual_style_profile_id": bindings.visual_style_profile_id,
                "style_profile_id": world.style_profile_id,
                "palette_id": world.palette_id,
                "wall_treatment_id": world.wall_treatment_id,
                "lighting_policy_id": world.lighting_policy_id,
            }
            if (
                _load_document(variant_row["authority_compatibility_json"])
                != expected_compatibility
            ):
                raise ValueError("Persisted variant authority compatibility mismatch.")
            for position, layer in enumerate(variant.layers, 1):
                layer_row = self.connection.execute(
                    "SELECT * FROM persistent_scene_entity_variant_layers "
                    "WHERE variant_id=? AND position=?",
                    (variant.variant_id, position),
                ).fetchone()
                assert layer_row is not None
                if (
                    digest(self._layer_payload(world, variant, layer, position))
                    != layer_row["layer_digest"]
                ):
                    raise ValueError("Persisted variant layer digest mismatch.")
        authority_rows = list(
            self.connection.execute(
                "SELECT * FROM persistent_scene_world_visual_authorities "
                "WHERE world_revision_id=? ORDER BY position",
                (world_id,),
            )
        )
        if (
            len(entity_rows) != row["expected_entity_count"]
            or len(authority_rows) != row["expected_authority_count"]
        ):
            raise ValueError("Persisted world membership count mismatch.")
        authorities = []
        for authority in authority_rows:
            actual = self._authority_digest(authority["visual_reference_authority_id"])
            if actual != authority["authority_payload_digest"]:
                raise ValueError("Persistent-world authority payload changed.")
            authorities.append((authority["visual_reference_authority_id"], actual))
        membership = {
            "entities": sorted(
                (entity.entity_key, digest(self._entity_payload(entity))) for entity in entities
            ),
            "authorities": authorities,
        }
        if digest(membership) != row["world_membership_digest"]:
            raise ValueError("Persisted world membership digest mismatch.")
        checks = (
            self._profile_digest("get_visual_style_profile", row["visual_style_profile_id"])
            == row["visual_style_profile_digest"],
            self._profile_digest("get_character_profile", row["character_profile_id"])
            == row["character_profile_digest"],
            self._reference_set_digest(row["character_reference_set_id"])
            == row["character_reference_set_digest"],
        )
        if not all(checks):
            raise ValueError("Persistent-world authority snapshot changed.")
        return world

    def get_persistent_scene_admissions(self, catalog_id: str) -> tuple[VariantBinding, ...]:
        """Reconstruct one exact branch-scoped admitted set."""

        chain = []
        seen: set[str] = set()
        current: str | None = catalog_id
        while current is not None:
            if current in seen:
                raise ValueError("Persistent-scene admission catalog cycle.")
            seen.add(current)
            row = self.connection.execute(
                "SELECT * FROM persistent_scene_admission_catalogs WHERE id=?", (current,)
            ).fetchone()
            if row is None:
                raise KeyError(current)
            chain.append(row)
            current = row["predecessor_catalog_id"]
        bindings: dict[str, VariantBinding] = {}
        world_id = chain[-1]["world_revision_id"]
        world = self.get_persistent_scene_world(world_id)
        for catalog in reversed(chain):
            if catalog["world_revision_id"] != world_id:
                raise ValueError("Admission catalog crosses persistent worlds.")
            events = list(
                self.connection.execute(
                    "SELECT * FROM persistent_scene_variant_admissions "
                    "WHERE catalog_id=? ORDER BY variant_id",
                    (catalog["id"],),
                )
            )
            if len(events) != catalog["expected_delta_count"]:
                raise ValueError("Admission catalog delta count mismatch.")
            for event in events:
                if event["variant_id"] in bindings:
                    raise ValueError("Variant is admitted more than once in one lineage.")
                variant = world.variant(event["variant_id"])
                binding = VariantBinding(
                    world.world_key,
                    world.revision,
                    variant.entity_key,
                    variant.variant_id,
                    variant_content_digest(world, variant),
                    event["authorization_reference"],
                    event["reason"],
                )
                event_payload = {
                    "world_revision_id": world_id,
                    "catalog_id": catalog["id"],
                    "entity_key": binding.entity_key,
                    "variant_id": binding.variant_id,
                    "variant_content_digest": binding.variant_content_digest,
                    "authorization_actor": event["authorization_actor"],
                    "authorization_reference": event["authorization_reference"],
                    "reason": binding.reason,
                }
                if digest(event_payload) != event["admission_event_digest"]:
                    raise ValueError("Admission event digest mismatch.")
                bindings[binding.variant_id] = binding
            complete = tuple(
                sorted(bindings.values(), key=lambda item: (item.entity_key, item.variant_id))
            )
            if len(complete) != catalog["complete_admission_count"]:
                raise ValueError("Admission catalog complete count mismatch.")
            if variant_admission_digest(complete) != catalog["complete_admission_digest"]:
                raise ValueError("Admission catalog complete digest mismatch.")
        return tuple(sorted(bindings.values(), key=lambda item: (item.entity_key, item.variant_id)))

    def get_persistent_scene_state(self, state_id: str) -> ResolvedState:
        row = self.connection.execute(
            "SELECT * FROM persistent_scene_resolved_states WHERE id=?", (state_id,)
        ).fetchone()
        if row is None:
            raise KeyError(state_id)
        world = self.get_persistent_scene_world(row["world_revision_id"])
        admissions = self.get_persistent_scene_admissions(row["admission_catalog_id"])
        entities = []
        content_digests = []
        entity_rows = list(
            self.connection.execute(
                "SELECT * FROM persistent_scene_resolved_entities WHERE state_id=? "
                "ORDER BY entity_key",
                (state_id,),
            )
        )
        for item in entity_rows:
            lineage = _load_document(item["lineage_json"])
            if digest(lineage) != item["lineage_digest"]:
                raise ValueError("Resolved-entity lineage digest mismatch.")
            entity = EntityState(
                item["entity_key"],
                item["selected_variant_id"],
                _affine(_load_document(item["local_transform_json"])),
                _affine(_load_document(item["effective_transform_json"])),
                item["plane_key"],
                item["parent_entity_key"],
                bool(item["visible"]),
                item["entity_state"],
            )
            if entity_render_digest(world, entity) != item["entity_content_digest"]:
                raise ValueError("Resolved-entity content digest mismatch.")
            entities.append(entity)
            content_digests.append((entity.entity_key, item["entity_content_digest"]))
        if len(entity_rows) != row["expected_entity_count"]:
            raise ValueError("Resolved-state entity count mismatch.")
        if {item.entity_key for item in entities} != {item.entity_key for item in world.entities}:
            raise ValueError("Resolved state is sparse or contains unknown entities.")
        membership = tuple(sorted(content_digests))
        if digest(membership) != row["entity_membership_digest"]:
            raise ValueError("Resolved-state membership digest mismatch.")
        diff_value = _load_document(row["diff_json"])
        if digest(diff_value) != row["diff_digest"]:
            raise ValueError("Resolved-state diff digest mismatch.")
        intent = self.connection.execute(
            "SELECT * FROM persistent_scene_transition_intents WHERE id=?",
            (row["transition_intent_id"],),
        ).fetchone()
        if intent is None:
            raise ValueError("Resolved state is missing its TransitionIntent.")
        operations = _load_document(intent["operations_json"])
        closure = _load_document(intent["allowed_dependency_closure_json"])
        intent_payload = {
            "schema_version": intent["schema_version"],
            "world_revision_id": intent["world_revision_id"],
            "kind": intent["kind"],
            "predecessor_state_id": intent["predecessor_state_id"],
            "predecessor_state_digest": intent["predecessor_state_digest"],
            "target_scene_id": intent["target_scene_id"],
            "operations": operations,
            "allowed_dependency_closure": closure,
            "authorization_actor": intent["authorization_actor"],
            "authorization_reference": intent["authorization_reference"],
            "reason": intent["reason"],
        }
        if digest(intent_payload) != intent["input_digest"]:
            raise ValueError("Persisted TransitionIntent digest mismatch.")
        if (
            intent["world_revision_id"] != row["world_revision_id"]
            or intent["predecessor_state_id"] != row["predecessor_state_id"]
            or intent["target_scene_id"] != row["editorial_scene_id"]
        ):
            raise ValueError("Resolved state and TransitionIntent bindings differ.")
        predecessor_digest = None
        if row["predecessor_state_id"]:
            predecessor = self.connection.execute(
                "SELECT state_digest FROM persistent_scene_resolved_states WHERE id=?",
                (row["predecessor_state_id"],),
            ).fetchone()
            if (
                predecessor is None
                or predecessor["state_digest"] != intent["predecessor_state_digest"]
            ):
                raise ValueError("Resolved-state predecessor digest mismatch.")
            predecessor_digest = predecessor["state_digest"]
        state = ResolvedState(
            row["id"],
            world.world_key,
            world.revision,
            row["world_definition_digest"],
            row["editorial_scene_id"],
            predecessor_digest,
            None if intent["kind"] == "base" else intent["id"],
            admissions,
            row["admission_digest"],
            tuple(entities),
            membership,
            row["state_digest"],
            _state_diff(diff_value),
        )
        if variant_admission_digest(admissions) != row["admission_digest"]:
            raise ValueError("Resolved-state admission digest mismatch.")
        snapshot_payload(world, state)
        return state

    def list_persistent_scene_state_children(self, state_id: str) -> list[str]:
        return [
            row[0]
            for row in self.connection.execute(
                "SELECT id FROM persistent_scene_resolved_states "
                "WHERE predecessor_state_id=? ORDER BY id",
                (state_id,),
            )
        ]

    def verify_persistent_scene_aggregate(self, state_id: str) -> dict[str, str]:
        state = self.get_persistent_scene_state(state_id)
        return {
            "world_definition_digest": state.world_definition_digest,
            "admission_digest": state.variant_admission_digest,
            "state_digest": state.state_digest,
        }

    def get_persistent_scene_media_context(self, state_id: str) -> PersistentSceneMediaContext:
        """Load one exact sealed state and its relational media bindings."""

        row = self.connection.execute(
            "SELECT world_revision_id, admission_catalog_id, transition_intent_id "
            "FROM persistent_scene_resolved_states WHERE id=?",
            (state_id,),
        ).fetchone()
        if row is None:
            raise KeyError(state_id)
        world = self.get_persistent_scene_world(row["world_revision_id"])
        state = self.get_persistent_scene_state(state_id)
        return PersistentSceneMediaContext(
            row["world_revision_id"],
            row["admission_catalog_id"],
            row["transition_intent_id"],
            world,
            state,
        )
