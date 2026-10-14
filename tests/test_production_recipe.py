"""The similarstoic-flow-v1 recipe: P11 equivalence and story-file validation (provider-free)."""

from __future__ import annotations

import copy
import json
from hashlib import sha256
from pathlib import Path

import pytest

from project_atlas.production import ProductionLifecycleService
from project_atlas.production_recipe import (
    StoryError,
    compile_story,
    findings,
    load_story,
)

FIXTURES = Path(__file__).parent / "fixtures" / "p11-flow"
RECIPE_PROVENANCE = {"recipe", "story_sha256"}


@pytest.fixture(scope="module")
def p11():
    story, story_sha = load_story(FIXTURES / "story.json")
    frozen = json.loads((FIXTURES / "frozen.json").read_text(encoding="utf-8"))
    return story, story_sha, frozen, compile_story(story, story_sha)


def test_the_fixture_is_the_verified_frozen_p11_request(p11) -> None:
    _story, _sha, frozen, _compiled = p11
    request = frozen["request"]
    canonical = json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert sha256(canonical.encode()).hexdigest() == frozen["provenance"]["request_digest"]
    assert frozen["provenance"]["run_status"] == ["founder_accepted", "founder_review"]


def test_compiling_the_p11_story_reproduces_its_frozen_request_exactly(p11) -> None:
    _story, story_sha, frozen, compiled = p11
    request = copy.deepcopy(compiled.request)
    # The only field P11 predates is the recipe's own provenance.
    assert request.pop("recipe") == {"id": "similarstoic-flow-v1", "story_sha256": story_sha}
    # start() then freezes today's channel defaults and resolves the environment pins.
    defaulted = ProductionLifecycleService._apply_new_run_defaults(request)
    expected = {k: v for k, v in frozen["request"].items() if k != "environment_pins"}
    assert defaulted == expected
    # Pins are resolved at start() from the approved room authorities; every base spec's pin is
    # the family and viewpoint its story room names, and only base specs are pinned.
    story = p11[0]
    pins = frozen["request"]["environment_pins"]
    bases = {f"{story['run_id']}-{key}-base": world for key, world in story["worlds"].items()}
    assert set(pins) == set(bases)
    for spec_id, world in bases.items():
        room = story["rooms"][world["room"]]
        assert (pins[spec_id]["environment_family"], pins[spec_id]["viewpoint"]) == (
            room["environment_family"],
            room["viewpoint"],
        )


def test_compiling_the_p11_story_reproduces_its_plan_scenes_and_specs(p11) -> None:
    _story, _sha, frozen, compiled = p11
    plan = compiled.plan
    assert plan["visual_plan_id"] == frozen["plan"]["id"]
    assert plan["visual_direction"] == frozen["plan"]["visual_direction"]
    metadata = dict(plan["metadata"])
    assert set(metadata) - set(frozen["plan"]["metadata"]) == RECIPE_PROVENANCE
    assert {k: v for k, v in metadata.items() if k not in RECIPE_PROVENANCE} == frozen["plan"][
        "metadata"
    ]
    scenes = [
        {
            "id": scene["scene_id"],
            "sequence": scene["sequence"],
            "narration_excerpt": scene["narration_excerpt"],
            "visual_intent": scene["visual_intent"],
            "hamster_action": scene["hamster_action"],
            "on_screen_text": scene["on_screen_text"],
            "transition_note": scene["transition_note"],
            "metadata": scene["metadata"],
        }
        for scene in compiled.scenes
    ]
    assert scenes == frozen["scenes"]
    revised = {item["asset_spec_id"]: item for item in frozen["spec_revisions"]}
    frozen_specs = {spec["id"]: spec for spec in frozen["asset_specs"]}
    assert {spec["asset_spec_id"] for spec in compiled.specs} == set(frozen_specs)
    for spec in compiled.specs:
        stored = frozen_specs[spec["asset_spec_id"]]
        for name in ("scene_id", "asset_type", "purpose", "description", "continuity_key"):
            assert spec[name] == stored[name], (spec["asset_spec_id"], name)
        assert spec["metadata"] == stored["metadata"]
        assert spec["character_profile_id"] == stored["character_profile_id"]
        prompt_sha = sha256(spec["generation_prompt"].encode()).hexdigest()
        if spec["asset_spec_id"] in revised:
            # Revised before regeneration: the story holds the approved original wording.
            revision = revised[spec["asset_spec_id"]]
            assert prompt_sha == revision["old_prompt_sha256"]
            stored_sha = sha256(stored["generation_prompt"].encode()).hexdigest()
            assert stored_sha == revision["new_prompt_sha256"]
        else:
            assert spec["generation_prompt"] == stored["generation_prompt"]


def test_the_p11_story_draws_the_known_drafting_findings(p11) -> None:
    story = p11[0]
    codes = {(item.code, item.state) for item in findings(story)}
    # P11's 1.40 s hook state and 1.46 s state 11 are flagged; so are its thin-outline objects.
    assert ("HOOK_STATE_SHORT", 1) in codes
    assert {("STATE_MAY_BE_SHORT", 1), ("STATE_MAY_BE_SHORT", 11)} <= codes
    assert {state for code, state in codes if code == "OBJECT_OUTLINE_WEIGHT"} == {
        6,
        8,
        9,
        10,
        11,
        15,
    }


def _edited(story, edit):
    changed = copy.deepcopy(story)
    edit(changed)
    return changed


@pytest.mark.parametrize(
    ("edit", "match"),
    [
        (lambda s: s.update(recipe="similarstoic-flow-v9"), "recipe must be"),
        (lambda s: s.pop("hook"), "missing fields"),
        (lambda s: s.update(extra=1), "unsupported fields"),
        (lambda s: s["states"][1].update(type="progression"), "continue the previous state"),
        (lambda s: s["objects"].pop("shoot"), "must add at least one object"),
        (lambda s: s["states"][6].update(world="w5"), "already appeared|kind"),
        (lambda s: s["states"][2].update(hamster=False), "hamster must match"),
        (lambda s: s["objects"]["shoot"].update(world="w6"), "progression state of its own world"),
        (lambda s: s["worlds"]["w2"].update(character_clause="paws"), "character_clause"),
        (lambda s: s["citations"][0].update(label="x" * 25), "1-24 characters"),
        (lambda s: s["worlds"]["w1"].update(room="kitchen"), "unknown room"),
        (lambda s: s.update(image_call_ceiling=0), "positive integer"),
    ],
)
def test_story_files_that_break_the_recipe_are_refused(p11, edit, match) -> None:
    story, story_sha = p11[0], p11[1]
    with pytest.raises(StoryError, match=match):
        compile_story(_edited(story, edit), story_sha)
