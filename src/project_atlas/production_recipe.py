"""Versioned SimilarStoic production recipes: a story file compiled into the plan and request.

A recipe holds only reusable patterns: new scene, character-free state, frozen-scene progression
with added objects, the hook overlay on state 1, citations bound to scenes and narration-aligned
cuts. A story file supplies everything story-specific (excerpts, worlds, objects, texts). The
compiled request starts through the unchanged ``ProductionLifecycleService.start`` with all of
its existing gates; nothing here generates, spends or approves anything.

``similarstoic-flow-v1`` is the method of the founder-accepted P11 (``production-11-flow``); its
templates reproduce that run's frozen request exactly (see the P11 equivalence test).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any

from project_atlas import speech_timing
from project_atlas.production import (
    FRAME_SIZE,
    OBJECT_CENTER_AT_REVIEW,
    RECIPE_FLOW_V1,
)
from project_atlas.scene_model import RENDER_POLICY_ALPHA

PLAN_KIND = "narration-led-fluid-v1"
STATE_TYPES = ("new", "character-free", "progression")
WORLD_KINDS = ("character", "character-free")
CHARACTER_CLAUSES = {
    "proportions": (
        " Head and body proportions exactly as in the character reference images; the head no "
        "larger relative to the body than in those images."
    ),
    "paws": (
        " Paws exactly as in the character reference images: short rounded orange-pink paws with "
        "clean black outlines and no extra fingers."
    ),
}
OBJECT_RULE = (
    " Draw it alone, centred, on a plain flat off-white background with nothing else in the "
    "image, with a complete closed black outline around the whole object, at its real on-screen "
    "size: {size} of the image width, leaving the rest of the image empty. The drawing must be "
    "one connected shape. No text, numbers or markings."
)
AUTHORITY = {
    "character_profile_id": "character-profile-similarstoic-hamster-core-v1",
    "character_reference_set_id": "character-reference-set-similarstoic-hamster-core-v2",
    "visual_reference_authority_id": (
        "visual-reference-authority-similarstoic-global-illustration-v1"
    ),
    "visual_style_profile_id": "visual-style-profile-similarstoic-core-v4",
}
TREATMENT = {
    "lighting_policy_id": "flat-soft-light-v1",
    "palette_id": "similarstoic-core-v3",
    "style_profile_id": "visual-style-profile-similarstoic-core-v4",
    "wall_treatment_id": "off-white-negative-space-v1",
}
# Advisory pacing estimate, calibrated on one Daniel v2 take (P11): about 182 ms per syllable
# weight plus 570 ms, roughly +/- 300 ms. Below 1.8 s a state may fall under ~1.5 s on screen.
_MS_PER_SYLLABLE, _MS_BASE, SHORT_STATE_ESTIMATE_MS = 182, 570, 1800
HOOK_READING_MS_PER_WORD = 350
HEAVY_OUTLINE_WORDING = "extra-heavy thick black outlines"
_SAFE_KEY = re.compile(r"[a-z0-9][a-z0-9_-]{0,79}")
_SAFE_ID = re.compile(r"[a-z0-9][a-z0-9_.:-]{0,159}")
_STORY_FIELDS = {
    "recipe",
    "run_id",
    "visual_plan_id",
    "editorial_gate_decision_id",
    "plan_summary",
    "hook",
    "continuity_key",
    "image_call_ceiling",
    "rooms",
    "states",
    "worlds",
    "objects",
    "citations",
}


class StoryError(ValueError):
    """A story file that the recipe cannot compile; nothing was written."""


@dataclass(frozen=True)
class Finding:
    """Advisory drafting evidence for the founder's Editorial step; never blocking."""

    code: str
    state: int | None
    message: str


@dataclass(frozen=True)
class CompiledStory:
    """Everything the recipe writes, in the order it is written, plus the start request."""

    plan: dict[str, Any]
    scenes: list[dict[str, Any]]
    specs: list[dict[str, Any]]
    request: dict[str, Any]
    findings: list[Finding] = field(default_factory=list)


def load_story(path: Path) -> tuple[dict[str, Any], str]:
    """Read one story file; its SHA-256 is of the exact file bytes."""

    content = Path(path).read_bytes()
    try:
        story = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise StoryError(f"Story file is not UTF-8 JSON: {error}") from error
    return story, sha256(content).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise StoryError(message)


def _text(value: Any, label: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"{label} must be non-empty text.")
    return value


def estimate_ms(excerpt: str) -> int:
    """Rough on-screen time of one excerpt at Daniel's pace (advisory only)."""

    syllables = sum(speech_timing.syllable_weight(word) for word in excerpt.split())
    return _MS_PER_SYLLABLE * syllables + _MS_BASE


def _validate(story: Any) -> None:
    _require(isinstance(story, dict), "Story file must be a JSON object.")
    unknown = set(story) - _STORY_FIELDS
    _require(not unknown, f"Story file has unsupported fields: {sorted(unknown)}.")
    missing = _STORY_FIELDS - set(story)
    _require(not missing, f"Story file is missing fields: {sorted(missing)}.")
    _require(story["recipe"] == RECIPE_FLOW_V1, f"Story recipe must be {RECIPE_FLOW_V1!r}.")
    for name in ("run_id", "visual_plan_id", "editorial_gate_decision_id", "continuity_key"):
        _require(
            isinstance(story[name], str) and bool(_SAFE_ID.fullmatch(story[name])),
            f"Story {name} must be a safe identifier.",
        )
    _text(story["plan_summary"], "Story plan_summary")
    _text(story["hook"], "Story hook")
    ceiling = story["image_call_ceiling"]
    _require(
        type(ceiling) is int and ceiling >= 1,
        "Story image_call_ceiling must be a positive integer.",
    )
    rooms, worlds, objects = story["rooms"], story["worlds"], story["objects"]
    states, citations = story["states"], story["citations"]
    _require(isinstance(rooms, dict) and rooms, "Story rooms must be a non-empty object.")
    for key, room in rooms.items():
        _require(bool(_SAFE_KEY.fullmatch(key)), f"Room key {key!r} is not a safe key.")
        _require(
            isinstance(room, dict) and set(room) == {"environment_family", "viewpoint"},
            f"Room {key} needs exactly environment_family and viewpoint.",
        )
        _text(room["environment_family"], f"Room {key} environment_family")
        _text(room["viewpoint"], f"Room {key} viewpoint")
    _require(isinstance(worlds, dict) and worlds, "Story worlds must be a non-empty object.")
    for key, world in worlds.items():
        _require(bool(_SAFE_KEY.fullmatch(key)), f"World key {key!r} is not a safe key.")
        _require(
            isinstance(world, dict) and set(world) == {"room", "kind", "character_clause", "text"},
            f"World {key} needs exactly room, kind, character_clause and text.",
        )
        _require(world["room"] in rooms, f"World {key} names an unknown room.")
        _require(world["kind"] in WORLD_KINDS, f"World {key} kind must be one of {WORLD_KINDS}.")
        clause = world["character_clause"]
        _require(
            clause is None or (world["kind"] == "character" and clause in CHARACTER_CLAUSES),
            f"World {key} character_clause must be null or, for a character world, one of "
            f"{sorted(CHARACTER_CLAUSES)}.",
        )
        _text(world["text"], f"World {key} text")
    _require(isinstance(states, list) and states, "Story states must be a non-empty list.")
    _require(isinstance(objects, dict), "Story objects must be an object.")
    seen_worlds: list[str] = []
    for number, state in enumerate(states, 1):
        label = f"State {number}"
        _require(
            isinstance(state, dict)
            and set(state) == {"excerpt", "type", "world", "hamster", "intent"},
            f"{label} needs exactly excerpt, type, world, hamster and intent.",
        )
        _text(state["excerpt"], f"{label} excerpt")
        _text(state["intent"], f"{label} intent")
        _require(state["type"] in STATE_TYPES, f"{label} type must be one of {STATE_TYPES}.")
        _require(state["world"] in worlds, f"{label} names an unknown world.")
        _require(isinstance(state["hamster"], bool), f"{label} hamster must be true or false.")
        world = worlds[state["world"]]
        if state["type"] == "progression":
            # A frozen scene continues: the world must be the one on screen just before.
            _require(
                bool(seen_worlds) and seen_worlds[-1] == state["world"],
                f"{label} is a progression, so it must continue the previous state's world.",
            )
            _require(
                any(item.get("state") == number for item in objects.values()),
                f"{label} is a progression and must add at least one object.",
            )
        else:
            _require(
                state["world"] not in seen_worlds,
                f"{label} starts world {state['world']}, which already appeared.",
            )
            expected = "character" if state["type"] == "new" else "character-free"
            _require(
                world["kind"] == expected,
                f"{label} is {state['type']!r}, so world {state['world']} must be {expected!r}.",
            )
        _require(
            state["hamster"] == (world["kind"] == "character"),
            f"{label} hamster must match world {state['world']}'s kind.",
        )
        seen_worlds.append(state["world"])
    for key, item in objects.items():
        _require(bool(_SAFE_KEY.fullmatch(key)), f"Object key {key!r} is not a safe key.")
        _require(
            isinstance(item, dict) and set(item) == {"world", "state", "size", "text"},
            f"Object {key} needs exactly world, state, size and text.",
        )
        _require(
            type(item["state"]) is int and 1 <= item["state"] <= len(states),
            f"Object {key} names an unknown state.",
        )
        target = states[item["state"] - 1]
        _require(
            target["type"] == "progression" and target["world"] == item["world"],
            f"Object {key} must be added on a progression state of its own world.",
        )
        _text(item["size"], f"Object {key} size")
        _text(item["text"], f"Object {key} text")
    _require(isinstance(citations, list), "Story citations must be a list.")
    for index, citation in enumerate(citations, 1):
        _require(
            isinstance(citation, dict) and set(citation) == {"state", "label", "source_id"},
            f"Citation {index} needs exactly state, label and source_id.",
        )
        _require(
            type(citation["state"]) is int and 1 <= citation["state"] <= len(states),
            f"Citation {index} names an unknown state.",
        )
        _require(
            isinstance(citation["label"], str) and 0 < len(citation["label"]) <= 24,
            f"Citation {index} label must be 1-24 characters.",
        )
        _text(citation["source_id"], f"Citation {index} source_id")


def findings(story: dict[str, Any]) -> list[Finding]:
    """Advisory drafting checks from the story-file authoring rules (never blocking)."""

    result = []
    states = story["states"]
    for number, state in enumerate(states, 1):
        estimate = estimate_ms(state["excerpt"])
        if estimate < SHORT_STATE_ESTIMATE_MS:
            result.append(
                Finding(
                    "STATE_MAY_BE_SHORT",
                    number,
                    f"State {number} is estimated at {estimate / 1000:.1f} s; it may be under "
                    "~1.5 s at Daniel's pace.",
                )
            )
    hook_ms = max(SHORT_STATE_ESTIMATE_MS, len(story["hook"].split()) * HOOK_READING_MS_PER_WORD)
    first = estimate_ms(states[0]["excerpt"])
    if first < hook_ms:
        result.append(
            Finding(
                "HOOK_STATE_SHORT",
                1,
                f"State 1 carries the hook but is estimated at {first / 1000:.1f} s; the hook "
                f"needs about {hook_ms / 1000:.1f} s to read.",
            )
        )
    for key, item in story["objects"].items():
        if HEAVY_OUTLINE_WORDING not in item["text"]:
            result.append(
                Finding(
                    "OBJECT_OUTLINE_WEIGHT",
                    item["state"],
                    f"Object {key} does not ask for {HEAVY_OUTLINE_WORDING!r}; objects are "
                    "shrunk at admission, so thin source outlines end up thinner than the base.",
                )
            )
    return result


def compile_story(story: dict[str, Any], story_sha256: str) -> CompiledStory:
    """Compile a validated story into plan, scene and spec records and the start request."""

    _validate(story)
    run_id, plan_id = story["run_id"], story["visual_plan_id"]
    states, worlds, objects = story["states"], story["worlds"], story["objects"]
    scene_ids = [f"{plan_id}-scene-{number}" for number in range(1, len(states) + 1)]
    last = len(states)
    plan = {
        "visual_plan_id": plan_id,
        "editorial_gate_decision_id": story["editorial_gate_decision_id"],
        "visual_direction": story["plan_summary"],
        "metadata": {
            "plan": PLAN_KIND,
            "states": len(states),
            "recipe": RECIPE_FLOW_V1,
            "story_sha256": story_sha256,
        },
    }
    scenes = [
        {
            "scene_id": scene_ids[number - 1],
            "visual_plan_id": plan_id,
            "sequence": number,
            "narration_excerpt": state["excerpt"],
            "visual_intent": state["intent"],
            "hamster_action": "hamster on screen" if state["hamster"] else None,
            "on_screen_text": story["hook"] if number == 1 else None,
            "transition_note": "crossfade" if number < last else None,
            "metadata": {"state_type": state["type"], "world": state["world"]},
        }
        for number, state in enumerate(states, 1)
    ]
    first_state = {}
    for number, state in enumerate(states, 1):
        first_state.setdefault(state["world"], number)
    specs, spec_ids = [], {}
    for key, world in worlds.items():
        character = world["kind"] == "character"
        room = story["rooms"][world["room"]]
        clause = CHARACTER_CLAUSES.get(world["character_clause"] or "", "")
        spec_ids[key] = f"{run_id}-{key}-base"
        specs.append(
            {
                "asset_spec_id": spec_ids[key],
                "scene_id": scene_ids[first_state[key] - 1],
                "asset_type": "character" if character else "environment",
                "purpose": "Full-frame base illustration for this state.",
                "description": _base_description(run_id, key),
                "generation_prompt": world["text"] + clause,
                "continuity_key": story["continuity_key"],
                "character_profile_id": AUTHORITY["character_profile_id"] if character else None,
                "metadata": {
                    "environment_family": room["environment_family"],
                    "environment_viewpoint": room["viewpoint"],
                }
                | ({} if character else {"character_free": True}),
            }
        )
    for key, item in objects.items():
        spec_ids[key] = f"{run_id}-object-{key}"
        specs.append(
            {
                "asset_spec_id": spec_ids[key],
                "scene_id": scene_ids[item["state"] - 1],
                "asset_type": "prop",
                "purpose": "An object added on this state of a progression run.",
                "description": _object_description(run_id, key),
                "generation_prompt": item["text"] + OBJECT_RULE.format(size=item["size"]),
                "continuity_key": None,
                "character_profile_id": None,
                "metadata": {"character_free": True},
            }
        )
    request_worlds = []
    for key in worlds:
        world_states = [n for n, state in enumerate(states, 1) if state["world"] == key]
        entities = [
            {
                "key": "base",
                "semantic_role": "full-scene-illustration",
                "persistence_class": "LOCKED_STATIC",
                "purpose": "Frozen base for this run.",
                "neutral_scale_id": "full-frame-v1",
                "initial_variant_key": "base",
                "initial_transform": {},
                "depth": 0,
                "variants": [
                    {
                        "key": "base",
                        "asset_spec_id": spec_ids[key],
                        "intrinsic_size_wu": list(FRAME_SIZE),
                    }
                ],
            }
        ]
        for object_key, item in objects.items():
            if item["world"] == key:
                entities.append(
                    {
                        "key": object_key,
                        "semantic_role": "added-object",
                        "persistence_class": "MOVABLE_PROP",
                        "purpose": "Added on its state and kept for the rest of the run.",
                        "neutral_scale_id": "object-v1",
                        "initial_variant_key": object_key,
                        "initial_transform": {},
                        "initial_visible": False,
                        "depth": 1,
                        "variants": [
                            {
                                "key": object_key,
                                "asset_spec_id": spec_ids[object_key],
                                "intrinsic_size_wu": list(FRAME_SIZE),
                                "object_center": OBJECT_CENTER_AT_REVIEW,
                            }
                        ],
                    }
                )
        transitions = [
            {
                "scene_id": scene_ids[later - 1],
                "reason": f"State {later}: add its object.",
                "operations": [
                    {"action": "set_visible", "entity_key": object_key, "value": True}
                    for object_key, item in objects.items()
                    if item["world"] == key and item["state"] == later
                ],
            }
            for later in world_states[1:]
        ]
        request_worlds.append(
            {
                "key": key,
                "scene_ids": [scene_ids[n - 1] for n in world_states],
                "visual_treatment": dict(TREATMENT),
                "entities": entities,
                "transitions": transitions,
            }
        )
    request = {
        "id": run_id,
        "visual_plan_id": plan_id,
        "authority": dict(AUTHORITY),
        "worlds": request_worlds,
        "timeline": [
            {
                "scene_id": scene_ids[number - 1],
                "duration_weight": max(
                    1,
                    sum(speech_timing.syllable_weight(word) for word in state["excerpt"].split()),
                ),
                "transition_to_next": "crossfade" if number < last else None,
            }
            for number, state in enumerate(states, 1)
        ],
        "citations": [
            {
                "scene_id": scene_ids[citation["state"] - 1],
                "label": citation["label"],
                "source_ids": [citation["source_id"]],
            }
            for citation in story["citations"]
        ],
        "forecast": {"image_calls": story["image_call_ceiling"]},
        "narration_authorized": False,
        "render_policy": RENDER_POLICY_ALPHA,
        "on_screen_text_overlay": True,
        "recipe": {"id": RECIPE_FLOW_V1, "story_sha256": story_sha256},
    }
    return CompiledStory(plan, scenes, specs, request, findings(story))


def _base_description(run_id: str, world_key: str) -> str:
    return f"{_run_label(run_id)} base {world_key}"


def _object_description(run_id: str, object_key: str) -> str:
    return f"{_run_label(run_id)} object {object_key}"


def _run_label(run_id: str) -> str:
    # "production-11-flow" -> "P11 flow"; other ids are used as they are.
    match = re.fullmatch(r"production-(\d+)(?:-(.+))?", run_id)
    if not match:
        return run_id
    return f"P{match.group(1)}" + (f" {match.group(2)}" if match.group(2) else "")


def write_plan(repository: Any, compiled: CompiledStory) -> dict[str, Any]:
    """Write the plan, scenes and specs under the existing Editorial Gate authorization.

    Every write goes through the repository's gate-checked methods; the returned request is
    then started with ``ProductionLifecycleService.start`` (which still validates everything).
    """

    plan = compiled.plan
    repository.create_visual_plan_under_editorial_gate(
        plan["visual_plan_id"],
        plan["editorial_gate_decision_id"],
        plan["visual_direction"],
        plan["metadata"],
    )
    for scene in compiled.scenes:
        repository.create_scene_under_visual_plan_authorization(**scene)
    for spec in compiled.specs:
        repository.create_asset_spec_under_scene_authorization(**spec)
    return json.loads(json.dumps(compiled.request))
