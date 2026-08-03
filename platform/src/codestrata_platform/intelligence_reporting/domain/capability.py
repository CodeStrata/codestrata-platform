"""Capability comparison and assessment-head distribution models."""

from __future__ import annotations

from dataclasses import dataclass, field

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.domain._safety import (
    optional_sorted_ids,
    require_nonblank,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ActivationStatus,
    ConfidenceLevel,
    CoverageStatus,
)


@dataclass(frozen=True, slots=True)
class RepositoryCapabilitySnapshot:
    repository_id: str
    assessment_id: str
    assessment_head_id: str
    activation_status: ActivationStatus
    coverage_status: CoverageStatus
    confidence_level: ConfidenceLevel
    finding_count: int = 0
    recommendation_count: int = 0
    priority_action_count: int = 0
    highest_severity: str | None = None
    limitations: tuple[str, ...] = ()
    drilldown_ref: str | None = None
    comparable: bool = True
    legacy_limited: bool = False
    assessment_run_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "repository_id", require_nonblank(self.repository_id, label="repository_id")
        )
        object.__setattr__(
            self, "assessment_id", require_nonblank(self.assessment_id, label="assessment_id")
        )
        object.__setattr__(
            self,
            "assessment_head_id",
            require_nonblank(self.assessment_head_id, label="assessment_head_id"),
        )
        for name in ("finding_count", "recommendation_count", "priority_action_count"):
            if getattr(self, name) < 0:
                raise InvalidValueError(
                    f"{name} must be non-negative",
                    reason_code=f"negative_{name}",
                )
        if self.highest_severity is not None:
            object.__setattr__(
                self,
                "highest_severity",
                require_nonblank(self.highest_severity, label="highest_severity").lower(),
            )
        object.__setattr__(
            self, "limitations", optional_sorted_ids(self.limitations, label="limitation")
        )
        if self.drilldown_ref is not None:
            object.__setattr__(
                self,
                "drilldown_ref",
                require_nonblank(self.drilldown_ref, label="drilldown_ref"),
            )
        if self.assessment_run_id is not None:
            object.__setattr__(
                self,
                "assessment_run_id",
                require_nonblank(self.assessment_run_id, label="assessment_run_id"),
            )


@dataclass(frozen=True, slots=True)
class CapabilityDistribution:
    complete_count: int = 0
    partial_count: int = 0
    insufficient_evidence_count: int = 0
    unavailable_count: int = 0
    disabled_count: int = 0
    high_confidence_count: int = 0
    moderate_confidence_count: int = 0
    limited_confidence_count: int = 0
    unavailable_confidence_count: int = 0
    not_applicable_count: int = 0
    missing_count: int = 0
    legacy_limited_count: int = 0
    comparable_count: int = 0

    def __post_init__(self) -> None:
        for name, value in (
            ("complete_count", self.complete_count),
            ("partial_count", self.partial_count),
            ("insufficient_evidence_count", self.insufficient_evidence_count),
            ("unavailable_count", self.unavailable_count),
            ("disabled_count", self.disabled_count),
            ("high_confidence_count", self.high_confidence_count),
            ("moderate_confidence_count", self.moderate_confidence_count),
            ("limited_confidence_count", self.limited_confidence_count),
            ("unavailable_confidence_count", self.unavailable_confidence_count),
            ("not_applicable_count", self.not_applicable_count),
            ("missing_count", self.missing_count),
            ("legacy_limited_count", self.legacy_limited_count),
            ("comparable_count", self.comparable_count),
        ):
            if value < 0:
                raise InvalidValueError(
                    f"{name} must be non-negative",
                    reason_code=f"negative_{name}",
                )

    @property
    def coverage_total(self) -> int:
        return (
            self.complete_count
            + self.partial_count
            + self.insufficient_evidence_count
            + self.unavailable_count
            + self.disabled_count
        )

    @property
    def confidence_total(self) -> int:
        return (
            self.high_confidence_count
            + self.moderate_confidence_count
            + self.limited_confidence_count
            + self.unavailable_confidence_count
        )


@dataclass(frozen=True, slots=True)
class CapabilityComparison:
    assessment_head_id: str
    repositories: tuple[RepositoryCapabilitySnapshot, ...] = ()
    distribution: CapabilityDistribution = field(default_factory=CapabilityDistribution)
    confidence: ConfidenceLevel = ConfidenceLevel.UNAVAILABLE
    limitations: tuple[str, ...] = ()
    comparable_repository_ids: tuple[str, ...] = ()
    limited_repository_ids: tuple[str, ...] = ()
    excluded_repository_ids: tuple[str, ...] = ()
    policy_id: str | None = None
    repositories_with_findings_count: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "assessment_head_id",
            require_nonblank(self.assessment_head_id, label="assessment_head_id"),
        )
        ordered = tuple(
            sorted(
                self.repositories,
                key=lambda item: (item.repository_id, item.assessment_id),
            )
        )
        object.__setattr__(self, "repositories", ordered)
        object.__setattr__(
            self, "limitations", optional_sorted_ids(self.limitations, label="limitation")
        )
        object.__setattr__(
            self,
            "comparable_repository_ids",
            optional_sorted_ids(self.comparable_repository_ids, label="comparable_repository_id"),
        )
        object.__setattr__(
            self,
            "limited_repository_ids",
            optional_sorted_ids(self.limited_repository_ids, label="limited_repository_id"),
        )
        object.__setattr__(
            self,
            "excluded_repository_ids",
            optional_sorted_ids(self.excluded_repository_ids, label="excluded_repository_id"),
        )
        if self.repositories_with_findings_count < 0:
            raise InvalidValueError(
                "repositories_with_findings_count must be non-negative",
                reason_code="negative_repositories_with_findings_count",
            )
        for item in ordered:
            if item.assessment_head_id != self.assessment_head_id:
                raise InvalidValueError(
                    "repository snapshot assessment_head_id must match comparison head",
                    reason_code="capability_head_mismatch",
                )
        if ordered and self.distribution.coverage_total not in {0, len(ordered)}:
            raise InvalidValueError(
                "capability coverage distribution must reconcile with repository snapshots",
                reason_code="capability_coverage_mismatch",
            )


@dataclass(frozen=True, slots=True)
class AssessmentHeadDistribution:
    """Cross-repository distribution for one assessment head (not a temporal trend)."""

    assessment_head_id: str
    repository_count: int = 0
    activated_count: int = 0
    complete_coverage_count: int = 0
    partial_coverage_count: int = 0
    insufficient_evidence_count: int = 0
    unavailable_count: int = 0
    disabled_count: int = 0
    finding_count: int = 0
    recommendation_count: int = 0
    priority_action_count: int = 0
    repositories_with_findings_count: int = 0
    severity_distribution: tuple[tuple[str, int], ...] = ()
    confidence_distribution: tuple[tuple[str, int], ...] = ()
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "assessment_head_id",
            require_nonblank(self.assessment_head_id, label="assessment_head_id"),
        )
        for name in (
            "repository_count",
            "activated_count",
            "complete_coverage_count",
            "partial_coverage_count",
            "insufficient_evidence_count",
            "unavailable_count",
            "disabled_count",
            "finding_count",
            "recommendation_count",
            "priority_action_count",
            "repositories_with_findings_count",
        ):
            if getattr(self, name) < 0:
                raise InvalidValueError(
                    f"{name} must be non-negative",
                    reason_code=f"negative_{name}",
                )
        coverage_sum = (
            self.complete_coverage_count
            + self.partial_coverage_count
            + self.insufficient_evidence_count
            + self.unavailable_count
            + self.disabled_count
        )
        if coverage_sum and coverage_sum != self.repository_count:
            raise InvalidValueError(
                "assessment-head coverage counts must reconcile with repository_count",
                reason_code="head_distribution_coverage_mismatch",
            )
        object.__setattr__(
            self,
            "severity_distribution",
            tuple(sorted((str(k).lower(), int(v)) for k, v in self.severity_distribution)),
        )
        object.__setattr__(
            self,
            "confidence_distribution",
            tuple(sorted((str(k).lower(), int(v)) for k, v in self.confidence_distribution)),
        )
        object.__setattr__(
            self, "limitations", optional_sorted_ids(self.limitations, label="limitation")
        )
