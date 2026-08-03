"""Technology distribution model (structure only — no aggregation yet)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.domain._safety import (
    bound_title,
    optional_sorted_ids,
    require_nonblank,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ConfidenceLevel,
    RatioStatus,
    VersionState,
)


@dataclass(frozen=True, slots=True)
class Ratio:
    """Numerator/denominator ratio — unavailable when denominator is zero."""

    numerator: int
    denominator: int
    status: RatioStatus
    value: str | None = None  # stable decimal string when available

    def __post_init__(self) -> None:
        if self.numerator < 0 or self.denominator < 0:
            raise InvalidValueError(
                "ratio components must be non-negative",
                reason_code="negative_ratio_component",
            )
        if self.denominator == 0:
            if self.status is not RatioStatus.UNAVAILABLE:
                raise InvalidValueError(
                    "zero denominator requires unavailable status",
                    reason_code="zero_denominator_must_be_unavailable",
                )
            if self.value is not None:
                raise InvalidValueError(
                    "unavailable ratio must not carry a value",
                    reason_code="unavailable_ratio_has_value",
                )
            return
        if self.status is RatioStatus.UNAVAILABLE:
            raise InvalidValueError(
                "non-zero denominator cannot be unavailable",
                reason_code="nonzero_denominator_unavailable",
            )
        if self.numerator > self.denominator:
            raise InvalidValueError(
                "ratio numerator cannot exceed denominator",
                reason_code="ratio_numerator_exceeds_denominator",
            )
        expected = format(
            (Decimal(self.numerator) / Decimal(self.denominator)).quantize(
                Decimal("0.0001")
            ),
            "f",
        )
        if self.value is None:
            object.__setattr__(self, "value", expected)
        else:
            try:
                Decimal(self.value)
            except (InvalidOperation, ValueError) as exc:
                raise InvalidValueError(
                    "ratio value must be a stable decimal string",
                    reason_code="invalid_ratio_value",
                ) from exc
            if self.value != expected:
                raise InvalidValueError(
                    "ratio value does not reconcile with numerator/denominator",
                    reason_code="ratio_value_mismatch",
                )

    @classmethod
    def of(cls, numerator: int, denominator: int) -> Ratio:
        if denominator == 0:
            return cls(
                numerator=numerator,
                denominator=0,
                status=RatioStatus.UNAVAILABLE,
                value=None,
            )
        value = format(
            (Decimal(numerator) / Decimal(denominator)).quantize(Decimal("0.0001")),
            "f",
        )
        return cls(
            numerator=numerator,
            denominator=denominator,
            status=RatioStatus.AVAILABLE,
            value=value,
        )


@dataclass(frozen=True, slots=True)
class TechnologyVersionObservation:
    version: str | None
    state: VersionState
    repository_ids: tuple[str, ...] = ()
    occurrence_count: int = 0
    source_assessment_ids: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.state is VersionState.KNOWN and not (self.version or "").strip():
            raise InvalidValueError(
                "known version state requires a version string",
                reason_code="missing_known_version",
            )
        if self.version is not None:
            object.__setattr__(self, "version", require_nonblank(self.version, label="version"))
        object.__setattr__(
            self,
            "repository_ids",
            optional_sorted_ids(self.repository_ids, label="repository_id"),
        )
        object.__setattr__(
            self,
            "source_assessment_ids",
            optional_sorted_ids(self.source_assessment_ids, label="source_assessment_id"),
        )
        object.__setattr__(
            self, "limitations", optional_sorted_ids(self.limitations, label="limitation")
        )
        if self.occurrence_count < 0:
            raise InvalidValueError(
                "occurrence_count must be non-negative",
                reason_code="negative_version_occurrence_count",
            )
        if self.repository_ids and self.occurrence_count < len(self.repository_ids):
            # Allow occurrence unset (0) for legacy callers; otherwise must reconcile.
            if self.occurrence_count != 0:
                raise InvalidValueError(
                    "version occurrence_count cannot be less than repository presence",
                    reason_code="version_occurrence_lt_repository_count",
                )


@dataclass(frozen=True, slots=True)
class TechnologyCategoryDistribution:
    category: str
    technology_count: int = 0
    repository_count: int = 0
    observations: tuple[str, ...] = ()  # technology_ids, ordered
    denominator: int = 0
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "category", require_nonblank(self.category, label="category"))
        ids = list(self.observations)
        if len(ids) != len(set(ids)):
            raise InvalidValueError(
                "category observations must be unique",
                reason_code="duplicate_category_observation",
            )
        object.__setattr__(self, "observations", tuple(ids))
        object.__setattr__(
            self, "limitations", optional_sorted_ids(self.limitations, label="limitation")
        )
        for name in ("technology_count", "repository_count", "denominator"):
            if getattr(self, name) < 0:
                raise InvalidValueError(
                    f"{name} must be non-negative",
                    reason_code=f"negative_{name}",
                )


@dataclass(frozen=True, slots=True)
class TechnologyDistributionObservation:
    technology_id: str
    normalized_name: str
    category: str
    repository_count: int
    repository_ratio: Ratio
    occurrence_count: int
    versions: tuple[TechnologyVersionObservation, ...] = ()
    repository_ids: tuple[str, ...] = ()
    source_assessment_ids: tuple[str, ...] = ()
    confidence: ConfidenceLevel = ConfidenceLevel.UNAVAILABLE
    limitations: tuple[str, ...] = ()
    source_names: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "technology_id", require_nonblank(self.technology_id, label="technology_id")
        )
        object.__setattr__(self, "normalized_name", bound_title(self.normalized_name))
        object.__setattr__(self, "category", require_nonblank(self.category, label="category"))
        if self.repository_count < 0 or self.occurrence_count < 0:
            raise InvalidValueError(
                "counts must be non-negative",
                reason_code="negative_technology_count",
            )
        if self.occurrence_count < self.repository_count:
            raise InvalidValueError(
                "occurrence_count cannot be less than repository_count",
                reason_code="occurrence_lt_repository_count",
            )
        repos = optional_sorted_ids(self.repository_ids, label="repository_id")
        if repos and len(repos) != self.repository_count:
            raise InvalidValueError(
                "repository_ids length must equal repository_count when provided",
                reason_code="technology_repository_count_mismatch",
            )
        object.__setattr__(self, "repository_ids", repos)
        object.__setattr__(
            self,
            "source_assessment_ids",
            optional_sorted_ids(self.source_assessment_ids, label="source_assessment_id"),
        )
        object.__setattr__(
            self, "limitations", optional_sorted_ids(self.limitations, label="limitation")
        )
        object.__setattr__(
            self, "source_names", optional_sorted_ids(self.source_names, label="source_name")
        )
        if self.repository_ratio.numerator != self.repository_count:
            raise InvalidValueError(
                "repository_ratio.numerator must equal repository_count",
                reason_code="technology_ratio_numerator_mismatch",
            )


@dataclass(frozen=True, slots=True)
class TechnologyDistribution:
    observations: tuple[TechnologyDistributionObservation, ...] = ()
    repository_denominator: int = 0
    limitations: tuple[str, ...] = ()
    category_distributions: tuple[TechnologyCategoryDistribution, ...] = ()
    policy_id: str | None = None
    eligible_repository_ids: tuple[str, ...] = ()
    unavailable_repository_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.repository_denominator < 0:
            raise InvalidValueError(
                "repository_denominator must be non-negative",
                reason_code="negative_repository_denominator",
            )
        # Commercial ordering: presence desc, occurrence desc, name, id.
        ordered = tuple(
            sorted(
                self.observations,
                key=lambda item: (
                    -item.repository_count,
                    -item.occurrence_count,
                    item.normalized_name.lower(),
                    item.technology_id,
                ),
            )
        )
        object.__setattr__(self, "observations", ordered)
        object.__setattr__(
            self, "limitations", optional_sorted_ids(self.limitations, label="limitation")
        )
        object.__setattr__(
            self,
            "eligible_repository_ids",
            optional_sorted_ids(self.eligible_repository_ids, label="eligible_repository_id"),
        )
        object.__setattr__(
            self,
            "unavailable_repository_ids",
            optional_sorted_ids(
                self.unavailable_repository_ids, label="unavailable_repository_id"
            ),
        )
        object.__setattr__(
            self,
            "category_distributions",
            tuple(sorted(self.category_distributions, key=lambda item: item.category)),
        )
        for item in ordered:
            if item.repository_ratio.denominator != self.repository_denominator:
                raise InvalidValueError(
                    "observation ratio denominator must match repository_denominator",
                    reason_code="technology_ratio_denominator_mismatch",
                )
