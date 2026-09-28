# Conveyor Persistent Scene Model

## Purpose and authority

This document is the primary architectural authority for persistent visual-world continuity in Conveyor. It applies
when a production deliberately adopts a continuing world, especially for recurring or multi-beat SimilarStoic scenes.
It does not require persistent decomposition for every unrelated one-off frame.

> A visual beat is a resolved state of a persistent world, not an independently regenerated picture.

> Unchanged entities are inherited exactly. Only an explicitly authorized delta may change the world.

The isolated zero-spend mechanical proof is synchronized at commit
`25fd94d65fde9d06a0fe05062a2638f327d159e0`. It proves the invariants below, not production integration or artistic
acceptance.

## Persistent world and editorial Scene are different

An existing `Scene` remains an editorial or narrative locator. A persistent visual world is a separate concept.
Several Scenes or beats may resolve states of one continuing world; a new editorial Scene does not automatically create
a new world. A genuine setting, incompatible view, metaphor or deliberate world replacement may establish a new one.

## Three immutable identity layers

### World definition — what continuing world is this?

World identity includes persistent geometry, camera/view contract, logical scale, static/base entities, relationships,
and frozen style, palette, treatment and visual-authority context. A key and revision name alone do not prove identity:
the revision must be bound to its exact immutable content.

### Approved variant admission — which exact realizations may be used?

An entity variant is an exact approved content identity, not merely a name. Its source assets, content identity, masks,
slice structure, local mapping, scale/contact contract and applicable character/visual authorities must be bound.

> Same admitted variant identity means the same exact approved content.

Different content requires a new identity or version. Candidate generation, technical success, a stored Asset, or
presence in an available collection does not imply admission. Admission is explicit and, under the currently proven
architecture, append-only.

### Resolved state — what is active now?

A resolved state binds the exact world, exact admitted content, complete entity membership, selected variants,
visibility/state, transforms, attachments, planes, order and render-relevant treatment. It inherits everything omitted
from the authorized transition. No mutable “latest”, implicit default or live lookup may silently reinterpret lineage.

The durable requirement is content binding and deterministic validation, not one eternal hashing algorithm.

## Complete-object and occlusion invariant

> Occlusion changes visibility, not identity.

A chair partly hidden by a table remains one complete chair. Render slices or masks may support compositing, but they
inherit the complete entity's identity and transform and are not independently movable world objects. Disocclusion must
reveal the same approved complete source. Conveyor may rely on hidden geometry only when complete compatible artwork
actually exists; it must not invent unknown hidden content.

## Shared geometry, scale and view

Related objects inhabit a common logical spatial system. Objects on one wall or surface must share coherent geometry
rather than independently inventing perspective. Object scale belongs to the world model, not arbitrary source-image
pixel bounds. Camera, projection and depth may affect apparent size, and an actor pose may alter silhouette without
redefining the actor's underlying world-scale contract.

The SimilarStoic default remains a static anchored camera. Camera/view is part of world/state identity; accidental drift
is prohibited. A purposeful crop or supported view change must be explicit. Unsupported view changes must not fabricate
unseen geometry. No particular unit size, projection implementation, matrix form or pixel ratio is canonical.

## Mutation discipline

Persistent entities carry semantic mutation permissions:

- **Locked static:** inherits unchanged; no routine state mutation.
- **Stateful static:** may change only an explicitly authorized state or approved realization.
- **Movable prop:** may receive explicit state, visibility, transform or attachment changes within its contract.
- **Actor:** may receive explicit approved pose, transform or attachment changes while retaining identity and scale.
- **Ephemeral effect:** may appear, disappear or change state only when explicitly authorized.

> Permission to change is not an instruction to change.

No transition may spontaneously introduce, remove, rescale or move an object, repaint palette/treatment, or drift the
camera. Attachment-driven changes must have one authoritative parent, remain cycle-free and report their dependency
closure so derived movement is explainable.

## Base plus explicit delta

The canonical state model is:

`BASE WORLD + EXPLICIT AUTHORIZED DELTA → RESOLVED STATE`

It is not `PROMPT → NEW COMPLETE FRAME`. Adjacent states must expose a machine-readable distinction between direct
authorized changes, derived changes, exact inheritance and unexpected changes. Any unexpected change blocks
progression.

## Variant evolution and generation

Future poses or prop states may be admitted without redefining unrelated static world content. Admission requires a
genuinely new identity/version, exact content binding and explicit approval/provenance. Existing admissions cannot be
deleted, replaced or rebound under the same identity in the currently proven model.

Once a world exists, generation normally answers: **what actually needs new pixels?** Typical demands are a new actor
pose, a new stateful-prop realization, a genuinely new object, or a genuinely new world. An unchanged wall, chair,
window or table causes no provider call. Generation for one entity must not replace unrelated established content.

The controlled future flow is:

`missing realization → generation demand → candidate Asset → perceptual review → explicit admission → selection`

Never: `generation succeeded → automatically trusted state`.

Full-frame generation remains valid for new-world creation, a deliberate new view, a signature break-frame, explicit
world replacement, or work where persistent decomposition adds no value. Persistent scenes do not ban it universally.

## Deterministic reuse and repair

For an unchanged entity, Conveyor preserves the exact approved source and spatial/render relationship. “Looks similar”
is weaker than exact reuse. Static content must not be regenerated merely to reproduce the same world.

When a defect is local, repair or replace the affected entity realization/state rather than rebuilding the accepted
world. A failed actor pose should not regenerate the room. A malformed persistent static entity may require a new
explicitly authorized entity or world revision rather than a silent repaint.

## Style, density and quality gates

Established palette, lighting, gradient and style treatment remain stable unless explicitly changed. Persistent-world
modeling must not create clutter merely because more objects can be represented. SimilarStoic remains sparse,
character-first and negative-space-friendly; every environmental object needs a purpose, and P5 quality does not imply
P5 density in every scene.

Mechanical continuity and visual quality are complementary, not interchangeable:

- the Persistent Scene Model protects world, entity and state identity;
- Character Model Continuity protects the mascot as the same canonical character across acting variants;
- Same Illustrator and the P5 Layer A floor protect integrated perceptual quality.

Stable world scale cannot make weak anatomy or artwork acceptable. Every generated candidate still requires the
applicable perceptual review before admission.

## Same world or new world

Usually retain the same world for the same room/setting, continuing action, prop-state evolution, actor pose or
expression changes, and deliberate progression. A purposeful supported crop or close-up may be the same world with an
explicit view state.

A new world is normally appropriate for a new location, an incompatible view requiring unseen surfaces, a
literal-to-abstract metaphor switch, a signature break-frame, or deliberate world replacement. Semantic fit and final
visual quality outrank forced reuse.

## Historical compatibility

Historical outputs are not retroactively converted into persistent scene models. No fabricated world, entity,
admission or state lineage is assigned to Production #5 or earlier work. Legacy media retains its original provenance.
This architecture applies prospectively only when a future production path explicitly adopts it.

## Proven mechanically

- exact persistent world identity/content binding;
- exact inheritance and explicit mutation;
- complete-object continuity and same-source disocclusion;
- shared geometry and source-pixel-independent logical scale;
- immutable, append-only variant admission and exact state selection;
- deterministic static reuse and machine-readable adjacent-state change evidence;
- provider-free resolution and separation of generation demand from admission.

## Not yet proven or implemented as production

- persistent database implementation or Migration 27;
- production `MediaService` or final-media snapshot integration;
- provider-backed entity acquisition and admission workflow;
- final-quality SimilarStoic visual proof or an actual Cell 1 rebuild;
- long-run throughput or artistic acceptance at scale.

The next gate is a separately authorized production-integration and visual-proof decision. This document authorizes no
migration, runtime write, provider call, generation, rebuild, production or publication.

## Non-canonical prototype choices

The current Python names, SHA-256 specifically, six-decimal precision, canonical-JSON implementation, affine matrix
layout, binary-alpha masks, nearest-neighbour compositor, fixture dimensions, proof-script structure, SQL/table count
and future migration shape are evidence mechanisms—not durable canon.
