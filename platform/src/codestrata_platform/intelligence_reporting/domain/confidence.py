"""Commercial report confidence (not an average of repository confidence)."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.domain._safety import optional_sorted_ids
from codestrata_platform.intelligence_reporting.domain.enums import (
    ComparabilityStatus,
    ConfidenceLevel,
    CoverageStatus,
    DerivationStatus,
)


@dataclass(frozen=True, slots=True)
class IntelligenceReportConfidence:
    level: ConfidenceLevel
    basis: tuple[str, ...]
    repository_sample_count: int = 0
    comparable_repository_count: int = 0
    assessment_schema_compatibility: ComparabilityStatus = ComparabilityStatus.UNKNOWN
    dataset_coverage_status: CoverageStatus = CoverageStatus.UNAVAILABLE
    weakest_material_source_confidence: ConfidenceLevel = ConfidenceLevel.UNAVAILABLE
    limitations: tuple[str, ...] = ()
    derivation_status: DerivationStatus = DerivationStatus.DEFERRED

    def __post_init__(self) -> None:
        if self.repository_sample_count < 0 or self.comparable_repository_count < 0:
            raise InvalidValueError(
                "confidence counts must be non-negative",
                reason_code="negative_confidence_count",
            )
        if self.comparable_repository_count > self.repository_sample_count:
            raise InvalidValueError(
                "comparable_repository_count cannot exceed repository_sample_count",
                reason_code="comparable_exceeds_sample",
            )
        basis = optional_sorted_ids(self.basis, label="confidence_basis")
        object.__setattr__(self, "basis", basis)
        limitations = optional_sorted_ids(self.limitations, label="limitation")
        object.__setattr__(self, "limitations", limitations)
        if self.level in {ConfidenceLevel.LIMITED, ConfidenceLevel.UNAVAILABLE}:
            if not limitations and self.derivation_status is not DerivationStatus.DEFERRED:
                raise InvalidValueError(
                    "Limited/Unavailable confidence requires limitations unless deferred",
                    reason_code="confidence_limitations_required",
                )
        if not basis and self.derivation_status is DerivationStatus.DERIVED:
            raise InvalidValueError(
                "derived confidence requires at least one basis entry",
                reason_code="confidence_basis_required",
            )
