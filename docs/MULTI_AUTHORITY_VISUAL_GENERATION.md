# Multi-Authority SimilarStoic Visual Generation — Architecture Design

## Decision and boundary

Approved SimilarStoic images are **generative reference authorities**: visual DNA used to create new script-specific
poses, environments, props, metaphors and compositions. They are not a finite library of finished scene assets.

This design closes the gap between that creative rule and canonical runtime provenance. It preserves the working
character-reference path and adds the smallest provider-neutral authority model needed for other visual roles. It is
design authority only: no schema, migration, provider call, media generation, Production #5 or publishing work is
implemented here.

## Current-state gap

The existing generation foundation already provides most required primitives:

- Migration 8 adds immutable, versioned `VisualStyleProfile` guidance and direct execution lineage.
- Migration 9 adds immutable, versioned `CharacterProfile` identity and direct AssetSpec/execution lineage.
- Migration 10 adds managed-Asset SHA-256 digests plus immutable ordered `CharacterReferenceSet` membership.
- Migration 11 adds direct restrictive `GenerationExecution → CharacterReferenceSet` lineage.
- `GenerationInput` freezes resolved style, character and ordered character-reference member details.
- provider adapters receive a provider-neutral request and translate it to a generation or reference-edit call.

Normal character generation therefore answers which identity profile, reference set, ordered member Assets and digests
informed an output. The general image adapter can transport multiple references, but the service resolves those bytes
only through a character reference set. An environment, prop or graphic receives textual `VisualStyleProfile` rules
and its `AssetSpec` brief; it cannot select approved environment, composition or other reference images as typed,
digest-verified authorities with direct execution lineage. Canonical tracked examples alone do not close that runtime
provenance gap.

## Minimum domain model

Keep these existing concepts unchanged:

- `VisualStyleProfile` remains the immutable textual/rule-based global style contract.
- `CharacterProfile` remains the recurring-character identity contract.
- `CharacterReferenceSet` remains the exact ordered visual grounding for one CharacterProfile.
- `AssetSpec`, `GenerationExecution`, managed `Asset` and `content_digest` retain their present meanings.

Add one generalized concept for approved non-character visual DNA:

### VisualReferenceAuthority

An immutable, versioned authority with:

- stable authority key and positive version;
- one typed role;
- human-readable name and generation guidance;
- optional exact parent authority for inheritance;
- metadata and creation time;
- one or more ordered, immutable managed-Asset members.

The initial role vocabulary should remain small:

- `global_illustration_style` — shared illustration authorship for all visual components;
- `environment_family` — family-specific guidance such as home, work, retail, transport, outdoor or abstract;
- `composition_depth` — framing, hierarchy, scale, negative space, overlap and plane relationships;
- `special_break_frame` — bounded exceptional visual treatment.

Do not generalize character identity into this model. `CharacterProfile` plus `CharacterReferenceSet` already expresses
that truth precisely. Do not create a dedicated prop/graphic authority by default. Props and graphics normally inherit
the selected global illustration authority and, when applicable, the scene's environment-family authority. A later
role can be added only after repeated evidence shows that a distinct prop/graphic authority improves consistency.

An `environment_family` may name an exact `global_illustration_style` parent. Selecting the family requires selecting
that parent in the same recipe. A family supplies visual guidance and useful examples; it does not require a finished
reference image for every possible supermarket, bedroom, station, café, office or street.

Every member must be an immutable managed image Asset with a verified SHA-256 `content_digest`. Existing approved files
may be imported through the current managed-Asset path under suitable AssetSpecs; their imported bytes must match the
canonical tracked digest. Authority creation must never overwrite or silently replace an Asset or an older authority
version.

## Frozen generation reference recipe

Extend the provider-neutral `GenerationInput` with one versioned `visual_authority_recipe`. It freezes the canonical
intent before any adapter call:

```json
{
  "schema_version": 1,
  "scene_id": "...",
  "asset_spec_id": "...",
  "scene_specific_brief": "...",
  "authorities": [
    {
      "selection_order": 1,
      "usage_role": "global_illustration_style",
      "authority_id": "...",
      "authority_key": "...",
      "authority_version": 1,
      "parent_authority_id": null,
      "generation_guidance": "...",
      "members": [
        {
          "asset_id": "...",
          "content_digest": "...",
          "media_type": "image/png",
          "position": 1,
          "member_role": "primary"
        }
      ]
    }
  ],
  "adapter_hints": {}
}
```

The execution continues to freeze the full AssetSpec snapshot, composed prompt, `provider_key`, `model_key`, request
ID, relevant request parameters, response metadata and output digest through existing structures. `adapter_hints` may
express provider-neutral intent such as relative priority or whether a member is identity, style or composition
guidance. It must not store one provider's request syntax as canon.

The recipe lists only references actually supplied or deliberately used as non-image guidance. If an adapter supports
fewer images than the canonical selection, deterministic adapter policy selects the supported subset before the call;
the frozen recipe and execution metadata must distinguish **selected authorities**, **members actually supplied**, and
any omitted member plus reason. Historical truth must never depend on a mutable “current style” pointer.

Character generation keeps its existing `character_references` payload and direct
`character_reference_set_id`. The new recipe accompanies it when global, environment or composition authorities also
inform the generation. This avoids rewriting or renaming historical character provenance.

## Scene-driven authority selection

For each script beat, the production service performs this bounded flow:

1. resolve scene intent, action, metaphor, location family and required AssetSpecs;
2. choose reuse only when an existing finished Asset expresses the required action and context without compromise;
3. otherwise select the approved global illustration authority;
4. add the exact CharacterProfile and latest qualified CharacterReferenceSet for character AssetSpecs;
5. add the closest approved environment-family authority for an environment or scene-specific context;
6. add composition/depth or special-break-frame authority only when the scene requires it;
7. validate parent relationships, member eligibility, managed bytes and every digest;
8. freeze the recipe and composed scene-specific brief before invoking a provider adapter;
9. record the immutable terminal execution and output digest;
10. run internal visual QA and perform only a targeted, separately recorded refinement when necessary.

Routine selection uses canonical roles, AssetSpec/Scene intent and approved authority metadata. It does not require the
founder to choose images, providers or normal retries. Missing or conflicting required authority, digest mismatch or
unsupported adapter semantics fails before a provider call. The system does not silently fall back to ungrounded
generation.

## Same-illustrator enforcement

Every generated visual AssetSpec must select exactly one `global_illustration_style` authority. All independently
generated assets intended for the same scene must resolve the same exact authority ID/version unless a deliberate
special-break-frame exception is recorded. Environment-family and composition authorities supplement that shared
authority and cannot replace it.

Before execution, deterministic checks verify:

- the global authority is present exactly once;
- every selected child authority names the selected global parent where a parent is defined;
- every member resolves to managed bytes with the recorded digest and supported image media type;
- a character AssetSpec also has the exact CharacterProfile and CharacterReferenceSet required by current rules;
- authority roles are compatible with the AssetSpec and scene intent;
- the adapter can represent the required minimum reference recipe without dropping a mandatory authority.

After generation, normal Codex/vision review evaluates:

- **character:** Core v3 identity, markings, proportions, face/head/ears, bag continuity and readable action;
- **style:** line treatment, palette, flatness, detail density and absence of generic AI gloss;
- **environment:** family and scene relevance plus same-illustrator coherence;
- **composition:** hierarchy, depth, negative space, grounding, overlap and mobile readability.

Deterministic checks cover identity/provenance, digests, dimensions and recipe completeness. Visual judgement remains a
bounded QA step; this design does not introduce an ML evaluator or pretend that hashes measure illustration quality.

## Provider-adapter boundary

The canonical service resolves and freezes authority semantics independently of any provider. Each adapter declares
capabilities such as maximum reference count, accepted media, weight support and image-plus-text support, then
translates the recipe into its native request.

Provider-specific weights, strength fields or control modes belong in the adapter translation and frozen request
parameters. Changing provider must not alter authority identity, membership or canonical role. If an adapter cannot
honour the minimum recipe required by an AssetSpec, selection fails before spend rather than weakening provenance.

## Composition and local assembly

Composition does **not** require a new executable AssetSpec type. A `composition_depth` authority informs prompts when
useful and guides deterministic/local assembly through framing, character scale, negative space, plane relationships,
overlap and grounding. The selected authority and exact reference members should be frozen in the generation recipe
for outputs it informs and in the existing final-media input snapshot metadata for local composition/rendering.

A future concrete need for a provider-generated composite can use an existing supported image AssetSpec type with an
explicit scene brief. It does not justify a generic `composition` asset class today.

## Persistence decision

**A minimal additive persistence change is required.** Existing migrations 1–23 cannot express immutable typed
non-character authorities, ordered digest-backed membership or restrictive many-authority lineage from one generation
execution. Storing IDs only in mutable metadata or unvalidated JSON would not meet the audit question.

The smallest additive schema is three tables:

### `visual_reference_authorities`

- `id` primary key;
- `authority_key`, `version`, unique together;
- `role`, `name`, `generation_guidance`;
- nullable `parent_authority_id` restrictive self-reference;
- `metadata_json`, `created_at`.

Rows are immutable by domain API. Role validation uses the small domain vocabulary above. Parent validation prevents
self-reference and requires an exact compatible global-style parent when applicable.

### `visual_reference_authority_members`

- `visual_reference_authority_id` restrictive foreign key;
- `asset_id` restrictive foreign key;
- positive `position` unique within the authority;
- `member_role`, `created_at`;
- primary key across authority and Asset.

Creation validates managed image bytes and `Asset.content_digest` exactly as character-reference loading does.
Membership is immutable; a changed selection creates a new authority version.

### `generation_execution_visual_authorities`

- `generation_execution_id` restrictive foreign key;
- `visual_reference_authority_id` restrictive foreign key;
- positive `selection_order` unique per execution;
- `usage_role`, `adapter_hints_json`, `created_at`;
- primary key across execution and authority.

The join supplies queryable direct lineage. The versioned `generation_input_json` remains the exact frozen snapshot of
authority identity, ordered supplied members, digests, scene-specific brief and relevant parameters. Repository
validation requires the JSON snapshot and join rows to agree atomically for new recipe-bearing executions. Existing
executions remain valid with no backfill and no fabricated authority lineage.

No new mutable selection pointer, “best” flag, generic asset library, approval workflow, QA-result table or provider
table is needed for the first proof.

## Migration sequencing

No migration number is selected by this design. Migration numbering follows implementation order.

Both this visual-authority persistence and the publishing/learning design require additive schema work. If visual
authority implementation is approved first, it receives the next available migration number and publishing/learning
moves to the following number or numbers. If publishing is implemented first, the order reverses. Documentation that
currently calls Migration 24 a reserved publishing placeholder must be synchronized when implementation order is
chosen; no accepted schema meaning is overwritten, because Migration 24 does not yet exist.

## Bounded implementation plan

1. Add immutable domain records and repository APIs for authority creation, read/list and ordered membership.
2. Add the three additive tables, restrictive indexes/foreign keys and legacy-preserving migration tests.
3. Import only the minimum already-approved visual references required for the proof as managed digest-matched Assets.
4. Extend `GenerationInput` with the versioned recipe while preserving v1–v4 reads and the current character path.
5. Add authority selection/validation and atomic execution-lineage persistence.
6. Add provider capability declarations and recipe translation to the existing adapter boundary.
7. Add focused tests for exact digests, immutable versions, parent/global-style consistency, adapter limits, failure
   before provider invocation, historical compatibility and successful multi-authority execution.
8. Exercise one zero-spend local/fake-adapter proof before any paid Production #5 call.

## Production #5 readiness threshold

Production #5 remains **RESERVED / NOT STARTED**. It becomes implementation-ready for its
**REFERENCE-DRIVEN DYNAMIC SCENE GENERATION / QUALITY-UPLIFT PROOF** only after Conveyor can:

- autonomously select one exact global authority and relevant family/composition authorities;
- resolve verified managed reference bytes and freeze every supplied member/digest;
- combine those with the unchanged Core v3 CharacterProfile/CharacterReferenceSet path;
- translate the recipe through the selected provider adapter without losing mandatory authority semantics;
- persist complete successful and failed execution provenance;
- generate materially new scene-specific assets and run the bounded identity/style/environment/composition QA above.

Perfect automated visual scoring, a complete family catalogue and a broad reusable asset inventory are not required.
The proof should use the smallest authority set needed for one Production #5 scene and judge visible improvement against
the current approximately 50% mature-quality assessment. The target remains approximately 80–85% before public launch.

## Alternatives rejected

- **Metadata-only authority IDs:** insufficient restrictive lineage and digest validation.
- **Rename/generalize CharacterReferenceSet:** rewrites a working precise model and risks historical meaning.
- **One universal mixed reference set:** loses role, inheritance and same-illustrator validation.
- **One table per authority role:** unnecessary taxonomy and migration surface.
- **Pre-generate every pose/location/prop:** contradicts script-driven generative authority.
- **Make composition executable by default:** no concrete requirement; guidance and local assembly are sufficient.
- **Persist provider-native request objects as canon:** couples SimilarStoic authority to one adapter.
- **Automated ML style evaluator:** disproportionate to current evidence; deterministic checks plus vision QA suffice.

## Current phase and spend

- Production-method validation: **PASSED**.
- Public-launch quality: **NOT YET PASSED**.
- Founder assessment: approximately **50%** of desired mature production quality.
- Public-launch target: approximately **80–85%**.
- Production #5: **RESERVED / NOT STARTED**.
- Production #6: absent.
- Design spend: **$0**.
- Active media-quality envelope: **$4.39 / $10 used; $5.61 remaining**.
