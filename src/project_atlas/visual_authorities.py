"""Materialize the approved SimilarStoic non-character visual-reference authorities."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from project_atlas.generation import LocalAssetStorage
from project_atlas.persistence import AtlasRepository, VisualReferenceAuthority

AUTHORITY_SCENE_ID = "scene-similarstoic-control-v1-1"


@dataclass(frozen=True)
class CanonicalReference:
    key: str
    repository_path: str
    content_digest: str
    asset_type: str
    purpose: str

    @property
    def asset_spec_id(self) -> str:
        return f"asset-spec-visual-authority-{self.key}-v1"

    @property
    def asset_id(self) -> str:
        return f"asset-visual-authority-{self.key}-v1"


CANONICAL_REFERENCES = (
    CanonicalReference(
        "default-scene-language",
        "assets/visual-references/environments/style/" "similarstoic-default-scene-language-v1.png",
        "989e0da7b273a42f0bf8c229c1510b904902b1eef3336e626705966e6048ccb2",
        "environment",
        "Ground all generated components in the approved SimilarStoic illustration authorship.",
    ),
    CanonicalReference(
        "environment-home",
        "assets/visual-references/environments/examples/"
        "similarstoic-calm-indoor-sorting-scene-v1.png",
        "45a8fcf77d1ba6d1b85601e9eba9a05e0554df705d3399c083f23a7b523dba2a",
        "environment",
        "Ground new home and interior environments in an approved family example.",
    ),
    CanonicalReference(
        "environment-abstract",
        "assets/visual-references/environments/examples/"
        "similarstoic-abstract-reach-boundary-scene-v1.png",
        "c30a8e66321fe9b725d6646ca1639fc6b01e87da3035092a0765067eaf2458b5",
        "environment",
        "Ground new abstract explanation spaces in an approved family example.",
    ),
    CanonicalReference(
        "composition-grammar",
        "assets/visual-references/compositions/grammar/"
        "similarstoic-static-composition-grammar-v1.png",
        "c6f933eddf7394ff3d00708650f7c1fa1df2f29ff8011e7ae4858653dd1f45d8",
        "graphic",
        "Ground new framing and depth in the approved SimilarStoic composition grammar.",
    ),
    CanonicalReference(
        "composition-example-indoor",
        "assets/visual-references/compositions/examples/"
        "similarstoic-static-composition-example-2-indoor-sorting-v1.png",
        "dae3ca8f2cd035a686fdbc87458bf280120ef0bf4e53ebb39c9fd3e422d933a7",
        "graphic",
        "Provide an approved calm indoor application of the composition grammar.",
    ),
    CanonicalReference(
        "composition-example-abstract",
        "assets/visual-references/compositions/examples/"
        "similarstoic-static-composition-example-3-things-in-hand-v1.png",
        "a5c7664ffcc40a6decdba0dc1a5c793d5850b6ddb975131a7395dc712329e427",
        "graphic",
        "Provide an approved abstract application of the composition grammar.",
    ),
    CanonicalReference(
        "special-break-frame",
        "assets/visual-references/break-frames/examples/"
        "similarstoic-hand-drawn-gross-up-notification-v1.png",
        "c38e0af357b0beb35ded28e78739115a630ca68ea9f6249f37f5ff8dcbae185e",
        "graphic",
        "Ground a rare exaggerated break-frame in approved hand-drawn authorship.",
    ),
)

GLOBAL_AUTHORITY_ID = "visual-reference-authority-similarstoic-global-illustration-v1"


def materialize_canonical_visual_authorities(
    repository: AtlasRepository,
    storage: LocalAssetStorage,
    repository_root: Path,
) -> list[VisualReferenceAuthority]:
    """Idempotently import approved bytes and create the minimum authority registry."""

    repository_root = repository_root.resolve()
    assets: dict[str, str] = {}
    for reference in CANONICAL_REFERENCES:
        source = (repository_root / reference.repository_path).resolve()
        if repository_root not in source.parents or not source.is_file():
            raise ValueError(f"Canonical visual reference is unavailable: {reference.key}")
        content = source.read_bytes()
        if sha256(content).hexdigest() != reference.content_digest:
            raise ValueError(f"Canonical visual reference digest mismatch: {reference.key}")
        try:
            asset_spec = repository.get_asset_spec(reference.asset_spec_id)
        except KeyError:
            asset_spec = repository.create_asset_spec_under_scene_authorization(
                reference.asset_spec_id,
                AUTHORITY_SCENE_ID,
                reference.asset_type,
                reference.purpose,
                "Immutable managed copy of an approved Git-tracked visual authority member.",
                "Do not generate; import the exact approved canonical reference bytes.",
                continuity_key="similarstoic-visual-authority",
                metadata={
                    "canonical_visual_authority": True,
                    "repository_path": reference.repository_path,
                    "expected_sha256": reference.content_digest,
                },
            )
        try:
            asset = repository.get_asset(reference.asset_id)
        except KeyError:
            asset = repository.import_asset_under_asset_spec_authorization(
                reference.asset_id,
                asset_spec.id,
                content,
                "image/png",
                storage,
                metadata={
                    "canonical_repository_path": reference.repository_path,
                    "canonical_sha256": reference.content_digest,
                    "import_purpose": "visual_reference_authority_member",
                },
            )
        if asset.asset_spec_id != asset_spec.id or asset.content_digest != reference.content_digest:
            raise ValueError(f"Materialized authority Asset identity mismatch: {reference.key}")
        _, verified_content = repository.load_verified_visual_reference_asset(asset.id)
        if sha256(verified_content).hexdigest() != reference.content_digest:
            raise ValueError(f"Materialized authority Asset bytes mismatch: {reference.key}")
        assets[reference.key] = asset.id

    authorities = [
        _ensure_authority(
            repository,
            GLOBAL_AUTHORITY_ID,
            "similarstoic-global-illustration",
            "global_illustration_style",
            "SimilarStoic global illustration style",
            (
                "Preserve crude human-drawn linework, restrained flat colour, warm off-white "
                "negative space and one coherent same-illustrator treatment."
            ),
            [(assets["default-scene-language"], "primary_style")],
        ),
        _ensure_authority(
            repository,
            "visual-reference-authority-similarstoic-environment-home-v1",
            "similarstoic-environment-home",
            "environment_family",
            "SimilarStoic home and interior environment family",
            (
                "Create a new sparse home or interior location with only useful context, "
                "generous negative space and the shared SimilarStoic illustration authorship."
            ),
            [(assets["environment-home"], "family_example")],
            parent_authority_id=GLOBAL_AUTHORITY_ID,
            metadata={"environment_family": "home"},
        ),
        _ensure_authority(
            repository,
            "visual-reference-authority-similarstoic-environment-abstract-v1",
            "similarstoic-environment-abstract",
            "environment_family",
            "SimilarStoic abstract explanation environment family",
            (
                "Create a new sparse illustrated explanation space without corporate-infographic "
                "polish, retaining the shared SimilarStoic authorship."
            ),
            [(assets["environment-abstract"], "family_example")],
            parent_authority_id=GLOBAL_AUTHORITY_ID,
            metadata={"environment_family": "abstract"},
        ),
        _ensure_authority(
            repository,
            "visual-reference-authority-similarstoic-composition-depth-v1",
            "similarstoic-composition-depth",
            "composition_depth",
            "SimilarStoic composition and depth grammar",
            (
                "Use character-first hierarchy, mobile-readable scale, active negative space, "
                "simple grounding and coherent foreground, midground and background overlap."
            ),
            [
                (assets["composition-grammar"], "primary_grammar"),
                (assets["composition-example-indoor"], "indoor_example"),
                (assets["composition-example-abstract"], "abstract_example"),
            ],
            parent_authority_id=GLOBAL_AUTHORITY_ID,
        ),
        _ensure_authority(
            repository,
            "visual-reference-authority-similarstoic-special-break-frame-v1",
            "similarstoic-special-break-frame",
            "special_break_frame",
            "SimilarStoic exaggerated break-frame treatment",
            (
                "Use only for a deliberate comedic rupture with stronger expression, crop and "
                "line detail while preserving original SimilarStoic identity and authorship."
            ),
            [(assets["special-break-frame"], "approved_example")],
            parent_authority_id=GLOBAL_AUTHORITY_ID,
        ),
    ]
    return authorities


def _ensure_authority(
    repository: AtlasRepository,
    authority_id: str,
    authority_key: str,
    role: str,
    name: str,
    generation_guidance: str,
    members: list[tuple[str, str]],
    *,
    parent_authority_id: str | None = None,
    metadata: dict[str, object] | None = None,
) -> VisualReferenceAuthority:
    try:
        authority = repository.get_visual_reference_authority(authority_id)
    except KeyError:
        return repository.create_visual_reference_authority(
            authority_id,
            authority_key,
            role,
            name,
            generation_guidance,
            members,
            parent_authority_id=parent_authority_id,
            metadata=metadata,
        )
    payload = repository.visual_reference_authority_payload(authority.id)
    expected_members = [
        {"asset_id": asset_id, "member_role": member_role, "position": position}
        for position, (asset_id, member_role) in enumerate(members, start=1)
    ]
    actual_members = [
        {
            "asset_id": item["asset_id"],
            "member_role": item["member_role"],
            "position": item["position"],
        }
        for item in payload["members"]
    ]
    if (
        authority.authority_key != authority_key
        or authority.version != 1
        or authority.role != role
        or authority.name != name
        or authority.generation_guidance != generation_guidance
        or authority.parent_authority_id != parent_authority_id
        or authority.metadata != (metadata or {})
        or actual_members != expected_members
    ):
        raise ValueError(f"Existing canonical authority differs: {authority_id}")
    return authority


def main() -> None:
    repository = AtlasRepository()
    try:
        authorities = materialize_canonical_visual_authorities(
            repository, LocalAssetStorage(), Path.cwd()
        )
        for authority in authorities:
            print(f"{authority.id}\t{authority.role}\tv{authority.version}")
    finally:
        repository.close()


if __name__ == "__main__":
    main()
