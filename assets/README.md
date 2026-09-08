# Assets

Store project assets that are intentionally version-controlled here. Keep generated or large deployment artifacts out of the repository unless explicitly approved.

## Authoritative visual-reference manifest

The seven core-mascot PNGs and separate environment-style PNG below are founder + ChatGPT-approved, Git-tracked
visual references. They are durable reference bytes, not runtime records, generated-output registrations, a new
CharacterReferenceSet, or a change to the immutable historical `character-reference-set-similarstoic-hamster-core-v1`
/ Asset `asset-9a02b4cb416744a994965e2e1f2f0c33`.

### Identity references

Identity references define concrete character appearance. They are the primary image/reference grounding inputs; each belongs only to the core mascot, contains no other hamster model, and must not be pooled with identity references for another recurring character.

| Character scope | Filename | Repository path | Dimensions | SHA-256 | Role class | Approved use | Prohibited use |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Core mascot | `9a9ccdc1-b948-45d1-a375-fc36d4e3bdc2.png` | `assets/visual-references/core-mascot/identity/9a9ccdc1-b948-45d1-a375-fc36d4e3bdc2.png` | 1448x1086 | `11332518cdace450f8e432fe8cb3558ea2374cf0273f94973912e914cee66956` | CORE IDENTITY REFERENCE | Preferred primary core-mascot grounding asset. | Supporting-character grounding, identity pooling, or treating scene context as identity. |
| Core mascot | `a5564bd0-51d2-4713-82c1-42138f12a8dc.png` | `assets/visual-references/core-mascot/identity/a5564bd0-51d2-4713-82c1-42138f12a8dc.png` | 1448x1086 | `d3acb16af30b9a5aca29e92e2e8f19d7b5a21df4b8e572de054756ca23321cc4` | CORE IDENTITY REFERENCE | Preferred primary/supplementary core-mascot grounding asset. | Supporting-character grounding, identity pooling, or treating scene context as identity. |
| Core mascot | `fa86fc7a-9006-4478-b5a2-371ba65cf06e.png` | `assets/visual-references/core-mascot/identity/fa86fc7a-9006-4478-b5a2-371ba65cf06e.png` | 1536x1024 | `eb4eeab20550da110183819c51cd7710d067f63156ea1a1ef2e4f6c0f21b1f46` | CORE IDENTITY REFERENCE | Supplementary core-only specification/identity grounding; not preferred as the sole grounding input. | Sole primary grounding, supporting-character grounding, identity pooling, or treating its instructional context as identity. |

### Approved acting / pose references

Acting / pose references demonstrate approved physical performance and pose deformation while retaining the core identity. They are secondary grounding inputs and never replace or override the identity references.

| Character scope | Filename | Repository path | Dimensions | SHA-256 | Role class | Approved use | Prohibited use |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Core mascot | `core-v3-umbrella-resistance-acting-pose-v1.png` | `assets/visual-references/core-mascot/poses/core-v3-umbrella-resistance-acting-pose-v1.png` | 1024x1536 | `a6ebaec876b40a7a89b22bca26e18ffa56d0709078498d3126946990c55e581e` | APPROVED SECONDARY ACTING-POSE REFERENCE | Core v3 umbrella-resistance acting pose v1; secondary pose/performance grounding alongside a canonical identity reference. | Primary identity authority, proof of a complete pose pack, automatic approval of future generations, or evidence that full-scene generation passed. |

### Scene / expression exemplars

Scene / expression exemplars may guide pose, expression, composition, props and context. They do not define mascot anatomy or identity, and must not override the identity references or the founder + ChatGPT-approved written visual contract. Whiteboards, charts, books, tables, chairs and other props are scene context only.

| Character scope | Filename | Repository path | Dimensions | SHA-256 | Role class | Approved use | Prohibited use |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Core mascot | `a3e484f6-8c69-4b89-8592-dd8671563b65.png` | `assets/visual-references/core-mascot/scenes/a3e484f6-8c69-4b89-8592-dd8671563b65.png` | 1448x1086 | `27ff66e34a8649a22c649a5593c93d0532cd176cf69dafb61bc19a1d2e1eb85a` | CORE SCENE / EXPRESSION EXEMPLAR | Flowchart/explaining pose, expression, composition and scene context. | Defining core anatomy/identity or treating the flowchart/whiteboard as an identity feature. |
| Core mascot | `e2a608fa-267b-4e7b-b7e8-0065699dd13f.png` | `assets/visual-references/core-mascot/scenes/e2a608fa-267b-4e7b-b7e8-0065699dd13f.png` | 1448x1086 | `24dc9fd6367d6f7c4f9731b12bd1b7e7376edf7870ecee0a8ac066699363ff65` | CORE SCENE / EXPRESSION EXEMPLAR | Growth-chart/surprised-expression pose, composition and scene context. | Defining core anatomy/identity or treating the chart as an identity feature. |
| Core mascot | `42ee8538-a4ff-4ca5-8b00-0044ef90207e.png` | `assets/visual-references/core-mascot/scenes/42ee8538-a4ff-4ca5-8b00-0044ef90207e.png` | 1448x1086 | `95ad2c8a75b7ce798eb315d1c84d34571bb1a44ace1922b141bdb2173fdfae4f` | CORE SCENE / EXPRESSION EXEMPLAR | Reading/thinking pose, expression, composition and scene context. | Defining core anatomy/identity or treating the book, table or chair as identity features. |

### Approved environment-style references

Environment-style references define the normal visual language of the world surrounding the mascot. They do not
define character identity or require reuse of their exact scenery or composition.

| Scope | Filename | Repository path | Dimensions | SHA-256 | Role class | Approved use | Prohibited use |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SimilarStoic ordinary scenes | `similarstoic-default-scene-language-v1.png` | `assets/visual-references/environments/style/similarstoic-default-scene-language-v1.png` | 1024x1536 | `989e0da7b273a42f0bf8c229c1510b904902b1eef3336e626705966e6048ccb2` | APPROVED ENVIRONMENT-STYLE REFERENCE | Default scene-language grounding: warm off-white negative space, sparse wonky outlined forms, restrained block colours and only enough props/detail to establish location or action. Approximately the upper normal detail boundary for an ordinary scene. | Primary or secondary character identity authority, mandatory scenery/composition, universal background, complete environment pack, permanent provider selection, or permission for painterly/dense ordinary scenes. |

Character identity, acting-pose and environment-style references have distinct semantic roles. Character, props and
environment should nevertheless appear to share one illustrator: environmental line weight, complexity, colour
treatment, shape language and rendering density must remain compatible with Core v3.

Supporting-character references, when separately founder + ChatGPT-approved, must live in their own per-character directories. Identity references from distinct recurring characters must never be pooled.
