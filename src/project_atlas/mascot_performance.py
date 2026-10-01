"""Founder-approved SimilarStoic Core mascot performance admission."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from project_atlas.static_character import (
    extract_boundary_connected_background,
    verify_static_character_extraction,
)

CORE_MASCOT_PROFILE_ID = "character-profile-similarstoic-hamster-core-v1"
PERFORMANCE_AUTHORITY = "founder-approved-similarstoic-core-mascot-performance-v1"


class CoreMascotPerformanceMissing(ValueError):
    """The requested Core mascot performance has no approved exact asset."""

    def __init__(self, semantic_performance: str) -> None:
        super().__init__(f"CORE MASCOT PERFORMANCE MISSING: {semantic_performance}")


@dataclass(frozen=True)
class ApprovedMascotPerformance:
    """One exact approved performance and its immutable source authority."""

    key: str
    semantic_performance: str
    relative_path: str
    source_sha256: str
    accepted_by: str
    accepted_date: str
    extraction_required: bool = True
    background_min_channel: int = 230
    background_max_channel_spread: int = 24
    edge_matte_min_channel: int = 220
    edge_matte_max_channel_spread: int = 32


APPROVED_CORE_MASCOT_PERFORMANCES = {
    item.key: item
    for item in (
        ApprovedMascotPerformance(
            "umbrella-resistance",
            "high-effort umbrella resistance",
            "assets/visual-references/core-mascot/poses/"
            "core-v3-umbrella-resistance-acting-pose-v1.png",
            "a6ebaec876b40a7a89b22bca26e18ffa56d0709078498d3126946990c55e581e",
            "Founder + ChatGPT",
            "2026-09-08",
        ),
        ApprovedMascotPerformance(
            "sorting-decisions",
            "calm focused sorting and decision behaviour",
            "assets/visual-references/core-mascot/poses/"
            "core-v3-sorting-decisions-acting-pose-v1.png",
            "16eb2a1ec14e7ddccca7332f2cf2b8e0842d51f5ce7fb3d0b8d672d21f9605bf",
            "Founder + ChatGPT",
            "2026-09-08",
        ),
        ApprovedMascotPerformance(
            "things-in-hand",
            "calm selective effort on reachable objects",
            "assets/visual-references/core-mascot/poses/"
            "core-v3-things-in-hand-acting-pose-v1.png",
            "b61fe5512df30e50ebc421b23069eafb350016e8995a0afba0bb40c33757cc5e",
            "Founder + ChatGPT",
            "2026-09-08",
        ),
    )
}


class CoreMascotPerformanceService:
    """Admit exact approved performances through the existing managed Asset boundary."""

    def __init__(
        self,
        repository: Any,
        storage: Any,
        source_root: Path | str | None = None,
    ) -> None:
        self.repository = repository
        self.storage = storage
        self.source_root = Path(source_root or Path(__file__).resolve().parents[2]).resolve()

    @staticmethod
    def definition(key: str) -> ApprovedMascotPerformance:
        try:
            return APPROVED_CORE_MASCOT_PERFORMANCES[key]
        except (KeyError, TypeError) as error:
            raise CoreMascotPerformanceMissing(str(key)) from error

    def admit(
        self,
        asset_spec_id: str,
        performance_key: str,
        character_reference_set_id: str,
    ) -> Any:
        """Return one exact managed derivative without crossing a provider boundary."""

        performance = self.definition(performance_key)
        spec = self.repository.get_asset_spec(asset_spec_id)
        if spec.asset_type != "character" or spec.character_profile_id != CORE_MASCOT_PROFILE_ID:
            raise ValueError(
                "Approved Core mascot performances require the Core character profile."
            )
        reference_set = self.repository.get_character_reference_set(character_reference_set_id)
        if reference_set.character_profile_id != CORE_MASCOT_PROFILE_ID:
            raise ValueError("Core mascot performance identity authority does not match.")
        source_path = (self.source_root / performance.relative_path).resolve()
        if self.source_root not in source_path.parents or not source_path.is_file():
            raise ValueError("Approved Core mascot performance source is unavailable.")
        source = source_path.read_bytes()
        if sha256(source).hexdigest() != performance.source_sha256:
            raise ValueError("Approved Core mascot performance digest mismatch.")
        if performance.extraction_required:
            extraction = extract_boundary_connected_background(
                source,
                background_min_channel=performance.background_min_channel,
                background_max_channel_spread=performance.background_max_channel_spread,
                edge_matte_min_channel=performance.edge_matte_min_channel,
                edge_matte_max_channel_spread=performance.edge_matte_max_channel_spread,
            )
            verify_static_character_extraction(source, extraction)
            content = extraction.content
            extraction_provenance: dict[str, Any] | None = extraction.provenance()
        else:
            content = source
            extraction_provenance = None
        asset_id = (
            f"asset-core-performance-{performance.key}-"
            f"{sha256(asset_spec_id.encode()).hexdigest()[:16]}"
        )
        expected_digest = sha256(content).hexdigest()
        metadata = {
            "authority": PERFORMANCE_AUTHORITY,
            "performance": asdict(performance),
            "character_profile_id": CORE_MASCOT_PROFILE_ID,
            "character_reference_set_id": character_reference_set_id,
            "extraction": extraction_provenance,
        }
        try:
            existing = self.repository.get_asset(asset_id)
        except KeyError:
            existing = self.repository.import_asset_under_asset_spec_authorization(
                asset_id,
                asset_spec_id,
                content,
                "image/png",
                self.storage,
                metadata=metadata,
            )
        if (
            existing.asset_spec_id != asset_spec_id
            or existing.source_kind != "imported"
            or existing.content_digest != expected_digest
            or existing.metadata != metadata
        ):
            raise ValueError("Approved Core mascot managed Asset provenance differs.")
        managed = self.repository.managed_asset_path(existing.id).read_bytes()
        if managed != content:
            raise ValueError("Approved Core mascot managed Asset bytes differ.")
        return existing
