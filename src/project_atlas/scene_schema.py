"""Additive SQLite schema for persistent-scene world and lineage aggregates."""

from __future__ import annotations


def _immutable(table: str) -> tuple[str, str]:
    return (
        f"CREATE TRIGGER {table}_immutable_update BEFORE UPDATE ON {table} "
        f"BEGIN SELECT RAISE(ABORT, '{table} is immutable'); END",
        f"CREATE TRIGGER {table}_immutable_delete BEFORE DELETE ON {table} "
        f"BEGIN SELECT RAISE(ABORT, '{table} is immutable'); END",
    )


MIGRATION_27: tuple[int, tuple[str, ...]] = (
    27,
    (
        """
        CREATE TABLE persistent_scene_world_revisions (
          id TEXT PRIMARY KEY,
          visual_plan_id TEXT NOT NULL,
          world_key TEXT NOT NULL CHECK (length(trim(world_key)) > 0),
          revision INTEGER NOT NULL CHECK (revision >= 1),
          predecessor_world_revision_id TEXT NULL,
          schema_version INTEGER NOT NULL CHECK (schema_version >= 1),
          resolver_contract_version TEXT NOT NULL,
          geometry_json TEXT NOT NULL,
          camera_json TEXT NOT NULL,
          treatment_json TEXT NOT NULL,
          visual_style_profile_id TEXT NOT NULL,
          visual_style_profile_digest TEXT NOT NULL CHECK (length(visual_style_profile_digest)=64),
          character_profile_id TEXT NULL,
          character_profile_digest TEXT NULL CHECK (
            character_profile_digest IS NULL OR length(character_profile_digest)=64),
          character_reference_set_id TEXT NULL,
          character_reference_set_digest TEXT NULL CHECK (
            character_reference_set_digest IS NULL OR length(character_reference_set_digest)=64),
          expected_entity_count INTEGER NOT NULL CHECK (expected_entity_count > 0),
          expected_authority_count INTEGER NOT NULL CHECK (expected_authority_count >= 0),
          world_membership_digest TEXT NOT NULL CHECK (length(world_membership_digest)=64),
          world_definition_digest TEXT NOT NULL CHECK (length(world_definition_digest)=64),
          created_at TEXT NOT NULL,
          UNIQUE (visual_plan_id, world_key, revision),
          UNIQUE (id, visual_plan_id),
          CHECK (predecessor_world_revision_id IS NULL OR predecessor_world_revision_id <> id),
          CHECK ((character_profile_id IS NULL) = (character_profile_digest IS NULL)),
          CHECK ((character_reference_set_id IS NULL) =
                 (character_reference_set_digest IS NULL)),
          FOREIGN KEY (visual_plan_id) REFERENCES visual_plans(id) ON DELETE RESTRICT,
          FOREIGN KEY (predecessor_world_revision_id)
            REFERENCES persistent_scene_world_revisions(id) ON DELETE RESTRICT,
          FOREIGN KEY (visual_style_profile_id)
            REFERENCES visual_style_profiles(id) ON DELETE RESTRICT,
          FOREIGN KEY (character_profile_id) REFERENCES character_profiles(id) ON DELETE RESTRICT,
          FOREIGN KEY (character_reference_set_id)
            REFERENCES character_reference_sets(id) ON DELETE RESTRICT
        )
        """,
        """
        CREATE TABLE persistent_scene_entities (
          world_revision_id TEXT NOT NULL,
          entity_key TEXT NOT NULL,
          semantic_role TEXT NOT NULL,
          purpose TEXT NOT NULL CHECK (length(trim(purpose)) > 0),
          persistence_class TEXT NOT NULL CHECK (persistence_class IN
            ('LOCKED_STATIC','STATEFUL_STATIC','MOVABLE_PROP','ACTOR','EPHEMERAL')),
          default_plane_key TEXT NOT NULL,
          default_parent_entity_key TEXT NULL,
          intrinsic_scale_json TEXT NOT NULL,
          anchors_json TEXT NOT NULL,
          initial_variant_id TEXT NOT NULL,
          initial_transform_json TEXT NOT NULL,
          initial_visible INTEGER NOT NULL CHECK (initial_visible IN (0,1)),
          initial_state TEXT NOT NULL,
          depth INTEGER NOT NULL,
          entity_definition_digest TEXT NOT NULL CHECK (length(entity_definition_digest)=64),
          created_at TEXT NOT NULL,
          PRIMARY KEY (world_revision_id, entity_key),
          CHECK (default_parent_entity_key IS NULL OR default_parent_entity_key <> entity_key),
          FOREIGN KEY (world_revision_id)
            REFERENCES persistent_scene_world_revisions(id) ON DELETE RESTRICT
            DEFERRABLE INITIALLY DEFERRED,
          FOREIGN KEY (world_revision_id, default_parent_entity_key)
            REFERENCES persistent_scene_entities(world_revision_id, entity_key)
            ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
          FOREIGN KEY (initial_variant_id)
            REFERENCES persistent_scene_entity_variants(id) ON DELETE RESTRICT
            DEFERRABLE INITIALLY DEFERRED
        )
        """,
        """
        CREATE TABLE persistent_scene_entity_variants (
          id TEXT PRIMARY KEY,
          world_revision_id TEXT NOT NULL,
          entity_key TEXT NOT NULL,
          variant_key TEXT NOT NULL,
          version INTEGER NOT NULL CHECK (version >= 1),
          schema_version INTEGER NOT NULL CHECK (schema_version >= 1),
          expected_layer_count INTEGER NOT NULL CHECK (expected_layer_count > 0),
          intrinsic_size_json TEXT NOT NULL,
          neutral_scale_id TEXT NOT NULL,
          anchors_json TEXT NOT NULL,
          contact_contract_json TEXT NOT NULL,
          partition_complete_source INTEGER NOT NULL CHECK (partition_complete_source IN (0,1)),
          character_profile_id TEXT NULL,
          character_reference_set_id TEXT NULL,
          visual_style_profile_id TEXT NOT NULL,
          authority_compatibility_json TEXT NOT NULL,
          acceptance_actor TEXT NOT NULL,
          acceptance_reference TEXT NOT NULL,
          acceptance_evidence_json TEXT NOT NULL,
          acceptance_evidence_digest TEXT NOT NULL CHECK (length(acceptance_evidence_digest)=64),
          variant_content_digest TEXT NOT NULL CHECK (length(variant_content_digest)=64),
          created_at TEXT NOT NULL,
          UNIQUE (world_revision_id, entity_key, variant_key, version),
          UNIQUE (id, world_revision_id, entity_key),
          FOREIGN KEY (world_revision_id, entity_key)
            REFERENCES persistent_scene_entities(world_revision_id, entity_key)
            ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
          FOREIGN KEY (character_profile_id) REFERENCES character_profiles(id) ON DELETE RESTRICT,
          FOREIGN KEY (character_reference_set_id)
            REFERENCES character_reference_sets(id) ON DELETE RESTRICT,
          FOREIGN KEY (visual_style_profile_id)
            REFERENCES visual_style_profiles(id) ON DELETE RESTRICT
        )
        """,
        """
        CREATE TABLE persistent_scene_entity_variant_layers (
          variant_id TEXT NOT NULL,
          position INTEGER NOT NULL CHECK (position >= 1),
          node_key TEXT NOT NULL,
          asset_id TEXT NOT NULL,
          asset_content_digest TEXT NOT NULL CHECK (length(asset_content_digest)=64),
          mask_asset_id TEXT NULL,
          mask_content_digest TEXT NULL CHECK (
            mask_content_digest IS NULL OR length(mask_content_digest)=64),
          local_mapping_json TEXT NOT NULL,
          mask_contract_json TEXT NOT NULL,
          coverage_digest TEXT NULL CHECK (coverage_digest IS NULL OR length(coverage_digest)=64),
          ordering_json TEXT NOT NULL,
          slice_role TEXT NOT NULL,
          layer_digest TEXT NOT NULL CHECK (length(layer_digest)=64),
          created_at TEXT NOT NULL,
          PRIMARY KEY (variant_id, position),
          UNIQUE (variant_id, node_key),
          CHECK ((mask_asset_id IS NULL) = (mask_content_digest IS NULL)),
          FOREIGN KEY (variant_id) REFERENCES persistent_scene_entity_variants(id)
            ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
          FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE RESTRICT,
          FOREIGN KEY (mask_asset_id) REFERENCES assets(id) ON DELETE RESTRICT
        )
        """,
        """
        CREATE TABLE persistent_scene_world_visual_authorities (
          world_revision_id TEXT NOT NULL,
          position INTEGER NOT NULL CHECK (position >= 1),
          visual_reference_authority_id TEXT NOT NULL,
          usage_role TEXT NOT NULL,
          authority_payload_digest TEXT NOT NULL CHECK (length(authority_payload_digest)=64),
          created_at TEXT NOT NULL,
          PRIMARY KEY (world_revision_id, visual_reference_authority_id),
          UNIQUE (world_revision_id, position),
          FOREIGN KEY (world_revision_id) REFERENCES persistent_scene_world_revisions(id)
            ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
          FOREIGN KEY (visual_reference_authority_id)
            REFERENCES visual_reference_authorities(id) ON DELETE RESTRICT
        )
        """,
        """
        CREATE TABLE persistent_scene_transition_intents (
          id TEXT PRIMARY KEY,
          world_revision_id TEXT NOT NULL,
          kind TEXT NOT NULL CHECK (kind IN ('base','delta')),
          target_scene_id TEXT NOT NULL,
          predecessor_state_id TEXT NULL,
          predecessor_state_digest TEXT NULL CHECK (
            predecessor_state_digest IS NULL OR length(predecessor_state_digest)=64),
          operations_json TEXT NOT NULL,
          allowed_dependency_closure_json TEXT NOT NULL,
          authorization_actor TEXT NOT NULL,
          authorization_reference TEXT NOT NULL,
          reason TEXT NOT NULL,
          schema_version INTEGER NOT NULL CHECK (schema_version >= 1),
          input_digest TEXT NOT NULL CHECK (length(input_digest)=64),
          created_at TEXT NOT NULL,
          CHECK ((kind='base' AND predecessor_state_id IS NULL
                              AND predecessor_state_digest IS NULL) OR
                 (kind='delta' AND predecessor_state_id IS NOT NULL
                               AND predecessor_state_digest IS NOT NULL)),
          CHECK (predecessor_state_id IS NULL OR predecessor_state_id <> id),
          FOREIGN KEY (world_revision_id) REFERENCES persistent_scene_world_revisions(id)
            ON DELETE RESTRICT,
          FOREIGN KEY (target_scene_id) REFERENCES scenes(id) ON DELETE RESTRICT,
          FOREIGN KEY (predecessor_state_id) REFERENCES persistent_scene_resolved_states(id)
            ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
        )
        """,
        """
        CREATE TABLE persistent_scene_admission_catalogs (
          id TEXT PRIMARY KEY,
          world_revision_id TEXT NOT NULL,
          kind TEXT NOT NULL CHECK (kind IN ('base','delta')),
          predecessor_catalog_id TEXT NULL,
          transition_intent_id TEXT NOT NULL UNIQUE,
          schema_version INTEGER NOT NULL CHECK (schema_version >= 1),
          expected_delta_count INTEGER NOT NULL CHECK (expected_delta_count >= 0),
          complete_admission_count INTEGER NOT NULL CHECK (complete_admission_count > 0),
          complete_admission_digest TEXT NOT NULL CHECK (length(complete_admission_digest)=64),
          created_at TEXT NOT NULL,
          CHECK ((kind='base' AND predecessor_catalog_id IS NULL) OR
                 (kind='delta' AND predecessor_catalog_id IS NOT NULL)),
          CHECK (predecessor_catalog_id IS NULL OR predecessor_catalog_id <> id),
          FOREIGN KEY (world_revision_id) REFERENCES persistent_scene_world_revisions(id)
            ON DELETE RESTRICT,
          FOREIGN KEY (predecessor_catalog_id) REFERENCES persistent_scene_admission_catalogs(id)
            ON DELETE RESTRICT,
          FOREIGN KEY (transition_intent_id) REFERENCES persistent_scene_transition_intents(id)
            ON DELETE RESTRICT
        )
        """,
        """
        CREATE TABLE persistent_scene_variant_admissions (
          id TEXT PRIMARY KEY,
          catalog_id TEXT NOT NULL,
          variant_id TEXT NOT NULL,
          authorization_actor TEXT NOT NULL,
          authorization_reference TEXT NOT NULL,
          reason TEXT NOT NULL,
          admission_event_digest TEXT NOT NULL CHECK (length(admission_event_digest)=64),
          created_at TEXT NOT NULL,
          UNIQUE (catalog_id, variant_id),
          FOREIGN KEY (catalog_id) REFERENCES persistent_scene_admission_catalogs(id)
            ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
          FOREIGN KEY (variant_id) REFERENCES persistent_scene_entity_variants(id)
            ON DELETE RESTRICT
        )
        """,
        """
        CREATE TABLE persistent_scene_resolved_states (
          id TEXT PRIMARY KEY,
          world_revision_id TEXT NOT NULL,
          transition_intent_id TEXT NOT NULL UNIQUE,
          predecessor_state_id TEXT NULL,
          editorial_scene_id TEXT NOT NULL,
          admission_catalog_id TEXT NOT NULL,
          world_definition_digest TEXT NOT NULL CHECK (length(world_definition_digest)=64),
          admission_digest TEXT NOT NULL CHECK (length(admission_digest)=64),
          expected_entity_count INTEGER NOT NULL CHECK (expected_entity_count > 0),
          entity_membership_digest TEXT NOT NULL CHECK (length(entity_membership_digest)=64),
          state_digest TEXT NOT NULL CHECK (length(state_digest)=64),
          diff_json TEXT NOT NULL,
          diff_digest TEXT NOT NULL CHECK (length(diff_digest)=64),
          schema_version INTEGER NOT NULL CHECK (schema_version >= 1),
          resolver_version TEXT NOT NULL,
          created_at TEXT NOT NULL,
          FOREIGN KEY (world_revision_id) REFERENCES persistent_scene_world_revisions(id)
            ON DELETE RESTRICT,
          FOREIGN KEY (transition_intent_id) REFERENCES persistent_scene_transition_intents(id)
            ON DELETE RESTRICT,
          FOREIGN KEY (predecessor_state_id) REFERENCES persistent_scene_resolved_states(id)
            ON DELETE RESTRICT,
          FOREIGN KEY (editorial_scene_id) REFERENCES scenes(id) ON DELETE RESTRICT,
          FOREIGN KEY (admission_catalog_id) REFERENCES persistent_scene_admission_catalogs(id)
            ON DELETE RESTRICT
        )
        """,
        """
        CREATE TABLE persistent_scene_resolved_entities (
          state_id TEXT NOT NULL,
          world_revision_id TEXT NOT NULL,
          entity_key TEXT NOT NULL,
          selected_variant_id TEXT NOT NULL,
          local_transform_json TEXT NOT NULL,
          effective_transform_json TEXT NOT NULL,
          plane_key TEXT NOT NULL,
          parent_entity_key TEXT NULL,
          visible INTEGER NOT NULL CHECK (visible IN (0,1)),
          entity_state TEXT NOT NULL,
          attachment_json TEXT NOT NULL,
          ordering_occlusion_json TEXT NOT NULL,
          change_class TEXT NOT NULL CHECK (change_class IN
            ('base','direct','derived','inherited','mixed')),
          inherited_from_state_id TEXT NULL,
          lineage_json TEXT NOT NULL,
          lineage_digest TEXT NOT NULL CHECK (length(lineage_digest)=64),
          entity_content_digest TEXT NOT NULL CHECK (length(entity_content_digest)=64),
          render_input_digest TEXT NOT NULL CHECK (length(render_input_digest)=64),
          created_at TEXT NOT NULL,
          PRIMARY KEY (state_id, entity_key),
          FOREIGN KEY (state_id) REFERENCES persistent_scene_resolved_states(id)
            ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
          FOREIGN KEY (world_revision_id, entity_key)
            REFERENCES persistent_scene_entities(world_revision_id, entity_key)
            ON DELETE RESTRICT,
          FOREIGN KEY (selected_variant_id, world_revision_id, entity_key)
            REFERENCES persistent_scene_entity_variants(id, world_revision_id, entity_key)
            ON DELETE RESTRICT,
          FOREIGN KEY (world_revision_id, parent_entity_key)
            REFERENCES persistent_scene_entities(world_revision_id, entity_key)
            ON DELETE RESTRICT,
          FOREIGN KEY (inherited_from_state_id)
            REFERENCES persistent_scene_resolved_states(id) ON DELETE RESTRICT
        )
        """,
        "CREATE INDEX idx_persistent_world_predecessor "
        "ON persistent_scene_world_revisions(predecessor_world_revision_id)",
        "CREATE INDEX idx_persistent_variant_entity "
        "ON persistent_scene_entity_variants(world_revision_id, entity_key)",
        "CREATE INDEX idx_persistent_variant_layer_asset "
        "ON persistent_scene_entity_variant_layers(asset_id)",
        "CREATE INDEX idx_persistent_catalog_predecessor "
        "ON persistent_scene_admission_catalogs(predecessor_catalog_id)",
        "CREATE INDEX idx_persistent_admission_variant "
        "ON persistent_scene_variant_admissions(variant_id)",
        "CREATE INDEX idx_persistent_intent_predecessor "
        "ON persistent_scene_transition_intents(predecessor_state_id)",
        "CREATE INDEX idx_persistent_state_predecessor "
        "ON persistent_scene_resolved_states(predecessor_state_id)",
        "CREATE INDEX idx_persistent_state_catalog "
        "ON persistent_scene_resolved_states(admission_catalog_id)",
        "CREATE INDEX idx_persistent_resolved_variant "
        "ON persistent_scene_resolved_entities(selected_variant_id)",
        """
        CREATE TRIGGER persistent_scene_entities_late_insert
        BEFORE INSERT ON persistent_scene_entities
        WHEN EXISTS (SELECT 1 FROM persistent_scene_world_revisions WHERE id=NEW.world_revision_id)
        BEGIN SELECT RAISE(ABORT, 'persistent scene world is sealed'); END
        """,
        """
        CREATE TRIGGER persistent_scene_world_authorities_late_insert
        BEFORE INSERT ON persistent_scene_world_visual_authorities
        WHEN EXISTS (SELECT 1 FROM persistent_scene_world_revisions WHERE id=NEW.world_revision_id)
        BEGIN SELECT RAISE(ABORT, 'persistent scene world is sealed'); END
        """,
        """
        CREATE TRIGGER persistent_scene_variant_layers_late_insert
        BEFORE INSERT ON persistent_scene_entity_variant_layers
        WHEN EXISTS (SELECT 1 FROM persistent_scene_entity_variants WHERE id=NEW.variant_id)
        BEGIN SELECT RAISE(ABORT, 'persistent scene variant is sealed'); END
        """,
        """
        CREATE TRIGGER persistent_scene_admissions_late_insert
        BEFORE INSERT ON persistent_scene_variant_admissions
        WHEN EXISTS (SELECT 1 FROM persistent_scene_admission_catalogs WHERE id=NEW.catalog_id)
        BEGIN SELECT RAISE(ABORT, 'persistent scene admission catalog is sealed'); END
        """,
        """
        CREATE TRIGGER persistent_scene_resolved_entities_late_insert
        BEFORE INSERT ON persistent_scene_resolved_entities
        WHEN EXISTS (SELECT 1 FROM persistent_scene_resolved_states WHERE id=NEW.state_id)
        BEGIN SELECT RAISE(ABORT, 'persistent scene state is sealed'); END
        """,
        """
        CREATE TRIGGER persistent_scene_world_seal_count
        BEFORE INSERT ON persistent_scene_world_revisions
        WHEN NEW.expected_entity_count <>
          (SELECT count(*) FROM persistent_scene_entities
           WHERE world_revision_id=NEW.id)
          OR NEW.expected_authority_count <>
          (SELECT count(*) FROM persistent_scene_world_visual_authorities
           WHERE world_revision_id=NEW.id)
        BEGIN SELECT RAISE(ABORT, 'persistent scene world membership incomplete'); END
        """,
        """
        CREATE TRIGGER persistent_scene_variant_seal_count
        BEFORE INSERT ON persistent_scene_entity_variants
        WHEN NEW.expected_layer_count <>
          (SELECT count(*) FROM persistent_scene_entity_variant_layers
           WHERE variant_id=NEW.id)
        BEGIN SELECT RAISE(ABORT, 'persistent scene variant layers incomplete'); END
        """,
        """
        CREATE TRIGGER persistent_scene_catalog_seal_count
        BEFORE INSERT ON persistent_scene_admission_catalogs
        WHEN NEW.expected_delta_count <>
          (SELECT count(*) FROM persistent_scene_variant_admissions
           WHERE catalog_id=NEW.id)
        BEGIN SELECT RAISE(ABORT, 'persistent scene admission delta incomplete'); END
        """,
        """
        CREATE TRIGGER persistent_scene_state_seal_count
        BEFORE INSERT ON persistent_scene_resolved_states
        WHEN NEW.expected_entity_count <>
          (SELECT count(*) FROM persistent_scene_resolved_entities
           WHERE state_id=NEW.id)
        BEGIN SELECT RAISE(ABORT, 'persistent scene state membership incomplete'); END
        """,
        *_immutable("persistent_scene_world_revisions"),
        *_immutable("persistent_scene_entities"),
        *_immutable("persistent_scene_entity_variants"),
        *_immutable("persistent_scene_entity_variant_layers"),
        *_immutable("persistent_scene_world_visual_authorities"),
        *_immutable("persistent_scene_admission_catalogs"),
        *_immutable("persistent_scene_variant_admissions"),
        *_immutable("persistent_scene_transition_intents"),
        *_immutable("persistent_scene_resolved_states"),
        *_immutable("persistent_scene_resolved_entities"),
    ),
)
