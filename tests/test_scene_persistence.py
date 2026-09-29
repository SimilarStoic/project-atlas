from __future__ import annotations

import sqlite3
from dataclasses import replace
from hashlib import sha256

import pytest

from project_atlas.persistence import MIGRATIONS, AtlasRepository
from project_atlas.scene_model import (
    Affine,
    DomainBindings,
    EntityVariant,
    Operation,
    RasterAsset,
    RasterMask,
    RenderSlice,
    TransitionIntent,
    VariantAdmissionRequest,
    base_state,
    bind_world_definition,
    build_fixture_world,
    variant_content_digest,
)

PLAN = "visual-plan-isa-deadline-video-v1"
SCENES = (
    "scene-isa-deadline-video-v1-01",
    "scene-isa-deadline-video-v1-02",
    "scene-isa-deadline-video-v1-03",
)
SPECS = (
    "asset-spec-isa-scene-01-kitchen-background-v1",
    "asset-spec-isa-scene-01-hamster-sorting-v1",
    "asset-spec-isa-scene-02-tax-year-calendar-v1",
    "asset-spec-isa-scene-03-decision-tree-v1",
    "asset-spec-isa-scene-03-hamster-reaction-v1",
)
STYLE = "visual-style-profile-similarstoic-core-v3"
CHARACTER = "character-profile-similarstoic-hamster-core-v1"
REFERENCE = "character-reference-set-persistent-proof-v1"
AUTHORITY = "visual-reference-authority-persistent-proof-v1"
WORLD_ID = "persistent-world-proof-v1"
CATALOG_0 = "admission-catalog-proof-base"


def _expanded_actor_variant(world):
    asset = RasterAsset.create("asset-actor-d", 10, 20, bytes((190, 130, 70, 255)) * 200)
    body = RasterMask.create("mask-actor-d-body", 10, 20, bytes([255] * 160 + [0] * 40))
    paw = RasterMask.create("mask-actor-d-paw", 10, 20, bytes([0] * 160 + [255] * 40))
    variant = EntityVariant(
        "actor-d",
        "actor",
        (4.0, 5.0),
        "actor-neutral-v1",
        (
            RenderSlice("actor.d.body", asset.asset_id, body.mask_id, Affine(a=0.4, d=0.25)),
            RenderSlice(
                "actor.d.paw",
                asset.asset_id,
                paw.mask_id,
                Affine(a=0.4, d=0.25),
                ("report.main",),
            ),
        ),
        character_authority_id=CHARACTER,
        partition_complete_source=True,
    )
    entities = tuple(
        (
            replace(item, approved_variants=item.approved_variants + (variant.variant_id,))
            if item.entity_key == "actor"
            else item
        )
        for item in world.entities
    )
    return bind_world_definition(
        replace(
            world,
            entities=entities,
            variants=world.variants + (variant,),
            assets=world.assets + (asset,),
            masks=world.masks + (body, paw),
        )
    )


def _managed_asset(repo, asset_id, content, digest_value, spec_id, version):
    repo.asset_storage_root.mkdir(parents=True, exist_ok=True)
    relative = f"proof/{asset_id}.png"
    path = repo.asset_storage_root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    repo.create_asset(
        asset_id,
        spec_id,
        version,
        relative,
        "image/png",
        "imported",
        content_digest=digest_value,
    )


def _prepared(tmp_path):
    repo = AtlasRepository(tmp_path / "scene.sqlite", tmp_path / "assets")
    source = build_fixture_world()
    actor_variants = []
    for variant in source.variants:
        actor_variants.append(
            replace(variant, character_authority_id=CHARACTER)
            if variant.entity_key == "actor"
            else variant
        )
    bindings = DomainBindings(PLAN, SCENES, SPECS, CHARACTER, REFERENCE, AUTHORITY, STYLE)
    world = bind_world_definition(
        replace(
            source,
            variants=tuple(actor_variants),
            style_profile_id=STYLE,
            bindings=bindings,
        )
    )
    versions = {spec: 0 for spec in SPECS}
    for index, asset in enumerate(world.assets):
        spec = SPECS[1] if asset.asset_id.startswith("asset-actor") else SPECS[index % len(SPECS)]
        versions[spec] += 1
        assert asset.rgba is not None
        _managed_asset(
            repo, asset.asset_id, asset.rgba, asset.expected_digest, spec, versions[spec]
        )
    for mask in world.masks:
        versions[SPECS[1]] += 1
        assert mask.alpha is not None
        _managed_asset(
            repo,
            mask.mask_id,
            mask.alpha,
            mask.expected_digest,
            SPECS[1],
            versions[SPECS[1]],
        )
    # This persistence fixture exercises scene aggregates, not the upstream
    # editorial-gate service that is covered independently.  Freeze the seeded
    # plan's exact imported actor directly as the reference authority fixture.
    with repo.connection:
        repo.connection.execute(
            "INSERT INTO character_reference_sets VALUES (?, ?, ?, ?)",
            (REFERENCE, CHARACTER, 1, "2026-09-29T00:00:00+00:00"),
        )
        repo.connection.execute(
            "INSERT INTO character_reference_set_members VALUES (?, ?, ?, ?)",
            (REFERENCE, "asset-actor-a", 1, "2026-09-29T00:00:00+00:00"),
        )
    repo.create_visual_reference_authority(
        AUTHORITY,
        "persistent-proof",
        "global_illustration_style",
        "Persistent proof",
        "Synthetic exact proof authority.",
        [("asset-wall", "style")],
    )
    base = base_state(world, SCENES[0])
    repo.create_persistent_scene_world(
        WORLD_ID,
        world,
        base,
        base_intent_id="intent-proof-base",
        base_catalog_id=CATALOG_0,
        authorization_actor="founder",
        authorization_reference="proof-base",
    )
    return repo, world, base, versions


def _add_expanded_assets(repo, world, versions):
    for asset in world.assets:
        if asset.asset_id != "asset-actor-d":
            continue
        versions[SPECS[1]] += 1
        _managed_asset(
            repo,
            asset.asset_id,
            asset.rgba,
            asset.expected_digest,
            SPECS[1],
            versions[SPECS[1]],
        )
    for mask in world.masks:
        if not mask.mask_id.startswith("mask-actor-d"):
            continue
        versions[SPECS[1]] += 1
        _managed_asset(
            repo,
            mask.mask_id,
            mask.alpha,
            mask.expected_digest,
            SPECS[1],
            versions[SPECS[1]],
        )


def test_migration_27_is_additive_and_integral(tmp_path):
    assert [version for version, _ in MIGRATIONS] == list(range(1, 28))
    repo = AtlasRepository(tmp_path / "clean.sqlite")
    assert repo.connection.execute("SELECT max(version) FROM schema_migrations").fetchone()[0] == 27
    tables = {
        row[0]
        for row in repo.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'persistent_scene_%'"
        )
    }
    assert len(tables) == 10
    assert repo.connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert repo.connection.execute("PRAGMA foreign_key_check").fetchall() == []
    repo.close()


def test_schema_26_upgrade_and_failed_27_are_atomic(tmp_path, monkeypatch):
    from project_atlas import persistence

    path = tmp_path / "upgrade.sqlite"
    monkeypatch.setattr(persistence, "MIGRATIONS", MIGRATIONS[:26])
    old = AtlasRepository(path)
    count = old.connection.execute("SELECT count(*) FROM opportunities").fetchone()[0]
    old.close()
    monkeypatch.setattr(persistence, "MIGRATIONS", MIGRATIONS)
    upgraded = AtlasRepository(path)
    assert (
        upgraded.connection.execute("SELECT max(version) FROM schema_migrations").fetchone()[0]
        == 27
    )
    assert upgraded.connection.execute("SELECT count(*) FROM opportunities").fetchone()[0] == count
    upgraded.close()

    failed_path = tmp_path / "failed.sqlite"
    monkeypatch.setattr(persistence, "MIGRATIONS", MIGRATIONS[:26])
    AtlasRepository(failed_path).close()
    broken = MIGRATIONS[:26] + ((27, MIGRATIONS[26][1] + ("INVALID SQL",)),)
    monkeypatch.setattr(persistence, "MIGRATIONS", broken)
    with pytest.raises(sqlite3.DatabaseError):
        AtlasRepository(failed_path)
    raw = sqlite3.connect(failed_path)
    assert raw.execute("SELECT max(version) FROM schema_migrations").fetchone()[0] == 26
    assert (
        raw.execute(
            "SELECT count(*) FROM sqlite_master WHERE name='persistent_scene_world_revisions'"
        ).fetchone()[0]
        == 0
    )
    raw.close()


def test_world_base_round_trip_and_seals(tmp_path):
    repo, world, base, _ = _prepared(tmp_path)
    loaded_world = repo.get_persistent_scene_world(WORLD_ID)
    loaded_state = repo.get_persistent_scene_state(base.state_id)
    assert loaded_world.definition_digest == world.definition_digest
    assert loaded_state.state_digest == base.state_digest
    assert loaded_state.variant_admission_digest == base.variant_admission_digest
    loaded_actor = loaded_world.variant("actor-b")
    source_actor = world.variant("actor-b")
    assert loaded_actor.intrinsic_size_wu == source_actor.intrinsic_size_wu
    assert loaded_actor.layers == source_actor.layers
    assert len({layer.asset_id for layer in loaded_actor.layers}) == 1
    with pytest.raises(sqlite3.IntegrityError, match="sealed"), repo.connection:
        repo.connection.execute(
            "INSERT INTO persistent_scene_entities "
            "SELECT world_revision_id,'late',semantic_role,purpose,persistence_class,"
            "default_plane_key,NULL,intrinsic_scale_json,anchors_json,initial_variant_id,"
            "initial_transform_json,initial_visible,initial_state,depth,entity_definition_digest,"
            "created_at FROM persistent_scene_entities LIMIT 1"
        )
    with pytest.raises(sqlite3.IntegrityError, match="immutable"), repo.connection:
        repo.connection.execute(
            "UPDATE persistent_scene_world_revisions SET world_key='changed' WHERE id=?",
            (WORLD_ID,),
        )
    repo.close()


def test_variant_admission_branch_and_history_isolation(tmp_path):
    repo, world, base, versions = _prepared(tmp_path)
    expanded = _expanded_actor_variant(world)
    _add_expanded_assets(repo, expanded, versions)
    repo.register_persistent_scene_variant(
        WORLD_ID,
        expanded,
        "actor-d",
        acceptance_actor="founder",
        acceptance_reference="actor-d-review",
        acceptance_evidence={"outcome": "accepted"},
    )
    assert "actor-d" not in {
        item.variant_id for item in repo.get_persistent_scene_admissions(CATALOG_0)
    }
    intent_a = TransitionIntent(
        "intent-a1",
        base.state_digest,
        SCENES[1],
        (
            Operation(
                "admit_variant",
                "actor",
                VariantAdmissionRequest("actor-d", "founder-a", "branch A pose"),
            ),
            Operation("set_variant", "actor", "actor-d"),
        ),
        (),
        "branch A",
    )
    a1 = repo.resolve_and_persist_scene_state(
        WORLD_ID,
        base.state_id,
        intent_a,
        "state-a1",
        catalog_id="catalog-a1",
        authorization_actor="founder",
        authorization_reference="founder-a",
    )
    assert a1.entity("actor").variant_id == "actor-d"
    intent_b = TransitionIntent(
        "intent-b1",
        base.state_digest,
        SCENES[2],
        (Operation("set_visible", "spark", True),),
        (),
        "branch B",
    )
    b1 = repo.resolve_and_persist_scene_state(
        WORLD_ID,
        base.state_id,
        intent_b,
        "state-b1",
        authorization_actor="founder",
        authorization_reference="founder-b",
    )
    assert "actor-d" not in {item.variant_id for item in b1.admitted_variants}
    assert "actor-d" not in {
        item.variant_id for item in repo.get_persistent_scene_state(base.state_id).admitted_variants
    }
    with pytest.raises(ValueError, match="not admitted"):
        repo.resolve_and_persist_scene_state(
            WORLD_ID,
            "state-b1",
            TransitionIntent(
                "intent-b2",
                b1.state_digest,
                SCENES[1],
                (Operation("set_variant", "actor", "actor-d"),),
                (),
                "illegal sideways leak",
            ),
            "state-b2",
            authorization_actor="founder",
            authorization_reference="none",
        )
    assert repo.list_persistent_scene_state_children(base.state_id) == ["state-a1", "state-b1"]
    repo.close()


def test_variant_and_state_post_seal_mutation_fail(tmp_path):
    repo, world, base, _ = _prepared(tmp_path)
    variant = world.variant("actor-b")
    assert variant_content_digest(
        repo.get_persistent_scene_world(WORLD_ID), variant
    ) == variant_content_digest(world, variant)
    with pytest.raises(sqlite3.IntegrityError, match="sealed"), repo.connection:
        repo.connection.execute(
            "INSERT INTO persistent_scene_entity_variant_layers "
            "SELECT variant_id,99,'late-node',asset_id,asset_content_digest,mask_asset_id,"
            "mask_content_digest,local_mapping_json,mask_contract_json,coverage_digest,"
            "ordering_json,slice_role,layer_digest,created_at "
            "FROM persistent_scene_entity_variant_layers WHERE variant_id='actor-b' LIMIT 1"
        )
    with pytest.raises(sqlite3.IntegrityError, match="immutable"), repo.connection:
        repo.connection.execute(
            "UPDATE persistent_scene_entity_variants SET neutral_scale_id='rebound' "
            "WHERE id='actor-b'"
        )
    with pytest.raises(sqlite3.IntegrityError, match="sealed"), repo.connection:
        repo.connection.execute(
            "INSERT INTO persistent_scene_resolved_entities "
            "SELECT state_id,world_revision_id,'late',selected_variant_id,local_transform_json,"
            "effective_transform_json,plane_key,NULL,visible,entity_state,attachment_json,"
            "ordering_occlusion_json,change_class,inherited_from_state_id,lineage_json,"
            "lineage_digest,entity_content_digest,render_input_digest,created_at "
            "FROM persistent_scene_resolved_entities WHERE state_id=? LIMIT 1",
            (base.state_id,),
        )
    repo.close()


def test_digest_redefinition_stale_predecessor_and_partial_rollback_are_blocked(tmp_path):
    repo, world, base, versions = _prepared(tmp_path)
    expanded = _expanded_actor_variant(world)
    _add_expanded_assets(repo, expanded, versions)

    changed_entities = tuple(
        replace(item, purpose="silently changed") if item.entity_key == "chair" else item
        for item in expanded.entities
    )
    redefined = bind_world_definition(replace(expanded, entities=changed_entities))
    with pytest.raises(ValueError, match="redefine"):
        repo.register_persistent_scene_variant(
            WORLD_ID,
            redefined,
            "actor-d",
            acceptance_actor="founder",
            acceptance_reference="blocked-world-redefinition",
            acceptance_evidence={"outcome": "accepted"},
        )

    false_digest = replace(expanded, definition_digest="f" * 64)
    with pytest.raises(ValueError, match="redefine"):
        repo.register_persistent_scene_variant(
            WORLD_ID,
            false_digest,
            "actor-d",
            acceptance_actor="founder",
            acceptance_reference="blocked-false-digest",
            acceptance_evidence={"outcome": "accepted"},
        )

    altered_actor_b = replace(
        expanded.variant("actor-b"),
        layers=(
            replace(
                expanded.variant("actor-b").layers[0],
                local_mapping=Affine.translate(1, 0),
            ),
            *expanded.variant("actor-b").layers[1:],
        ),
    )
    rebound = bind_world_definition(
        replace(
            expanded,
            variants=tuple(
                altered_actor_b if item.variant_id == "actor-b" else item
                for item in expanded.variants
            ),
        )
    )
    with pytest.raises(sqlite3.IntegrityError):
        repo.register_persistent_scene_variant(
            WORLD_ID,
            rebound,
            "actor-b",
            acceptance_actor="founder",
            acceptance_reference="blocked-rebind",
            acceptance_evidence={"outcome": "accepted"},
        )

    with pytest.raises(ValueError, match="stale predecessor"):
        repo.resolve_and_persist_scene_state(
            WORLD_ID,
            base.state_id,
            TransitionIntent(
                "intent-stale",
                "0" * 64,
                SCENES[1],
                (Operation("set_visible", "spark", True),),
                (),
                "stale predecessor attack",
            ),
            "state-stale",
            authorization_actor="founder",
            authorization_reference="blocked-stale",
        )
    assert (
        repo.connection.execute(
            "SELECT count(*) FROM persistent_scene_transition_intents WHERE id='intent-stale'"
        ).fetchone()[0]
        == 0
    )

    repo.register_persistent_scene_variant(
        WORLD_ID,
        expanded,
        "actor-d",
        acceptance_actor="founder",
        acceptance_reference="actor-d-review",
        acceptance_evidence={"outcome": "accepted"},
    )
    rollback_intent = TransitionIntent(
        "intent-rollback",
        base.state_digest,
        SCENES[1],
        (
            Operation(
                "admit_variant",
                "actor",
                VariantAdmissionRequest("actor-d", "founder", "rollback proof"),
            ),
        ),
        (),
        "force duplicate state ID after child inserts",
    )
    with pytest.raises(sqlite3.IntegrityError):
        repo.resolve_and_persist_scene_state(
            WORLD_ID,
            base.state_id,
            rollback_intent,
            base.state_id,
            catalog_id="catalog-rollback",
            authorization_actor="founder",
            authorization_reference="rollback",
        )
    assert (
        repo.connection.execute(
            "SELECT count(*) FROM persistent_scene_transition_intents " "WHERE id='intent-rollback'"
        ).fetchone()[0]
        == 0
    )
    assert (
        repo.connection.execute(
            "SELECT count(*) FROM persistent_scene_admission_catalogs "
            "WHERE id='catalog-rollback'"
        ).fetchone()[0]
        == 0
    )
    repo.close()


def test_catalog_and_authority_identifiers_are_immutable(tmp_path):
    repo, _, _, _ = _prepared(tmp_path)
    with pytest.raises(sqlite3.IntegrityError, match="immutable"), repo.connection:
        repo.connection.execute(
            "UPDATE persistent_scene_admission_catalogs "
            "SET predecessor_catalog_id='reinterpreted' WHERE id=?",
            (CATALOG_0,),
        )
    with pytest.raises(sqlite3.IntegrityError, match="immutable"), repo.connection:
        repo.connection.execute(
            "UPDATE persistent_scene_world_visual_authorities "
            "SET authority_payload_digest=? WHERE world_revision_id=?",
            ("0" * 64, WORLD_ID),
        )
    repo.close()


def test_cross_plan_asset_rejected_and_same_plan_cross_scene_allowed(tmp_path):
    repo, world, _, versions = _prepared(tmp_path)
    expanded = _expanded_actor_variant(world)
    _add_expanded_assets(repo, expanded, versions)
    repo.register_persistent_scene_variant(
        WORLD_ID,
        expanded,
        "actor-d",
        acceptance_actor="founder",
        acceptance_reference="same-plan",
        acceptance_evidence={"outcome": "accepted"},
    )
    assert repo.get_asset("asset-actor-d").asset_spec_id == SPECS[1]
    assert repo.get_scene(repo.get_asset_spec(SPECS[1]).scene_id).id == SCENES[0]

    foreign_plan = "visual-plan-foreign"
    foreign_scene = "scene-foreign"
    repo.create_visual_plan(
        foreign_plan,
        "content-piece-isa-deadline-video-v1",
        "script-isa-deadline-video-v1",
        "Foreign plan",
    )
    repo.create_scene(foreign_scene, foreign_plan, 1, "x", "x")
    repo.create_asset_spec("spec-foreign", foreign_scene, "graphic", "x", "x", "x")
    foreign = RasterAsset.create("asset-foreign", 1, 1, b"\x00\x00\x00\xff")
    _managed_asset(repo, foreign.asset_id, foreign.rgba, foreign.expected_digest, "spec-foreign", 1)
    actor = expanded.variant("actor-d")
    altered = replace(
        actor,
        variant_id="actor-foreign",
        layers=(replace(actor.layers[0], asset_id=foreign.asset_id, mask_id=None),),
        partition_complete_source=False,
    )
    bad = bind_world_definition(
        replace(
            expanded,
            entities=tuple(
                (
                    replace(item, approved_variants=item.approved_variants + (altered.variant_id,))
                    if item.entity_key == "actor"
                    else item
                )
                for item in expanded.entities
            ),
            variants=expanded.variants + (altered,),
            assets=expanded.assets + (foreign,),
        )
    )
    with pytest.raises(ValueError, match="same VisualPlan"):
        repo.register_persistent_scene_variant(
            WORLD_ID,
            bad,
            altered.variant_id,
            acceptance_actor="founder",
            acceptance_reference="reject",
            acceptance_evidence={"outcome": "accepted"},
        )
    repo.close()


def test_catalog_chain_performance_sanity(tmp_path):
    repo, _, base, _ = _prepared(tmp_path)
    current = base
    for index in range(20):
        intent = TransitionIntent(
            f"intent-chain-{index}",
            current.state_digest,
            SCENES[(index + 1) % len(SCENES)],
            (Operation("set_state", "laptop", f"state-{index}"),),
            (),
            "chain sanity",
        )
        current = repo.resolve_and_persist_scene_state(
            WORLD_ID,
            current.state_id,
            intent,
            f"state-chain-{index}",
            authorization_actor="founder",
            authorization_reference="chain",
        )
    assert repo.verify_persistent_scene_aggregate(current.state_id)["state_digest"]
    repo.close()


def test_runtime_digest_helper_is_stable():
    assert sha256(b"persistent-scene").hexdigest() == sha256(b"persistent-scene").hexdigest()
