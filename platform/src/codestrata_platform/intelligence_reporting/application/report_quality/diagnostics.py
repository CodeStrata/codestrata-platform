"""ReportQualityDiagnostics — factual counters only."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReportQualityDiagnostics:
    included_repository_count: int = 0
    comparable_repository_count: int = 0
    canonical_repository_count: int = 0
    legacy_repository_count: int = 0
    material_section_count: int = 0
    supported_material_section_count: int = 0
    unavailable_material_section_count: int = 0
    small_sample_section_count: int = 0
    limitation_count: int = 0
    material_limitation_count: int = 0
    moderate_limitation_count: int = 0
    report_confidence_level: str = "unavailable"
    policy_bundle_id: str = ""
    unresolved_reference_count: int = 0
    deduplicated_limitation_count: int = 0
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "limitations",
            tuple(sorted({item for item in self.limitations if item})),
        )
