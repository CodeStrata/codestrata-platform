"""Canonical engineering value objects (CEIM)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from codestrata_platform.domain.engineering.enums import (
    EngineeringCategory,
    EngineeringMetricKind,
    EngineeringRelationshipType,
    EngineeringSeverity,
    EvidenceKind,
)
from codestrata_platform.domain.engineering.ids import (
    EngineeringComponentId,
    EngineeringEvidenceId,
    EngineeringFindingId,
    EngineeringMetricId,
    EngineeringRecommendationId,
    EngineeringRelationshipId,
    EngineeringTechnologyId,
)
from codestrata_platform.domain.errors import InvalidValueError

_MAX_STRING = 4000
_MAX_METADATA_KEYS = 50
_SECRET_KEY_MARKERS = (
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "credential",
)


def _bounded(value: str, *, field_name: str, max_length: int = _MAX_STRING) -> str:
    compact = value.strip()
    if not compact:
        raise InvalidValueError(
            f"{field_name} must be non-blank",
            reason_code=f"empty_{field_name}",
        )
    if len(compact) > max_length:
        raise InvalidValueError(
            f"{field_name} exceeds maximum length of {max_length}",
            reason_code=f"{field_name}_too_long",
        )
    return compact


def _metadata(attributes: Mapping[str, str] | None) -> dict[str, str]:
    if not attributes:
        return {}
    if len(attributes) > _MAX_METADATA_KEYS:
        raise InvalidValueError(
            f"Metadata may contain at most {_MAX_METADATA_KEYS} keys",
            reason_code="metadata_too_large",
        )
    normalized: dict[str, str] = {}
    for key, value in dict(attributes).items():
        compact_key = key.strip()
        compact_value = value.strip()
        if not compact_key or not compact_value:
            raise InvalidValueError(
                "Metadata keys and values must be non-blank",
                reason_code="invalid_metadata",
            )
        if any(marker in compact_key.lower() for marker in _SECRET_KEY_MARKERS):
            raise InvalidValueError(
                f"Metadata key '{compact_key}' is not allowed",
                reason_code="secret_bearing_metadata",
            )
        if len(compact_key) > _MAX_STRING or len(compact_value) > _MAX_STRING:
            raise InvalidValueError(
                "Metadata key or value exceeds maximum length",
                reason_code="metadata_string_too_long",
            )
        normalized[compact_key] = compact_value
    return dict(sorted(normalized.items()))


@dataclass(frozen=True, slots=True)
class EngineeringSnapshotVersion:
    value: int

    def __post_init__(self) -> None:
        if self.value < 1:
            raise InvalidValueError(
                "Engineering snapshot version must be >= 1",
                reason_code="invalid_snapshot_version",
            )


@dataclass(frozen=True, slots=True)
class EngineeringTag:
    name: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _bounded(self.name, field_name="tag_name", max_length=128))


@dataclass(frozen=True, slots=True)
class EngineeringTechnology:
    technology_id: EngineeringTechnologyId
    canonical_key: str
    display_name: str
    category: EngineeringCategory = EngineeringCategory.OTHER
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "canonical_key",
            _bounded(self.canonical_key, field_name="canonical_key", max_length=128),
        )
        object.__setattr__(
            self,
            "display_name",
            _bounded(self.display_name, field_name="display_name", max_length=256),
        )
        object.__setattr__(self, "metadata", _metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class EngineeringComponent:
    component_id: EngineeringComponentId
    name: str
    kind: str = "component"
    path_reference: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _bounded(self.name, field_name="component_name"))
        object.__setattr__(
            self,
            "kind",
            _bounded(self.kind, field_name="component_kind", max_length=64),
        )
        if self.path_reference is not None:
            object.__setattr__(
                self,
                "path_reference",
                _bounded(self.path_reference, field_name="path_reference"),
            )
        object.__setattr__(self, "metadata", _metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class EngineeringEvidence:
    evidence_id: EngineeringEvidenceId
    kind: EvidenceKind
    reference: str
    line_start: int | None = None
    line_end: int | None = None
    symbol: str | None = None
    source_artifact_id: str | None = None
    checksum: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "reference", _bounded(self.reference, field_name="reference"))
        if self.reference.startswith("/") and (
            self.reference.startswith("/Users/") or self.reference.startswith("/home/")
        ):
            raise InvalidValueError(
                "Absolute user paths are not allowed in evidence references",
                reason_code="absolute_user_path",
            )
        if self.line_start is not None and self.line_start < 1:
            raise InvalidValueError(
                "line_start must be >= 1",
                reason_code="invalid_line_start",
            )
        if (
            self.line_end is not None
            and self.line_start is not None
            and self.line_end < self.line_start
        ):
            raise InvalidValueError(
                "line_end must be >= line_start",
                reason_code="invalid_line_range",
            )
        object.__setattr__(self, "metadata", _metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class EngineeringFinding:
    finding_id: EngineeringFindingId
    source_finding_id: str
    category: EngineeringCategory
    severity: EngineeringSeverity
    title: str
    summary: str
    rule_id: str
    confidence: float
    evidence_ids: tuple[str, ...] = ()
    technology_keys: tuple[str, ...] = ()
    component_ids: tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_finding_id",
            _bounded(self.source_finding_id, field_name="source_finding_id", max_length=160),
        )
        object.__setattr__(self, "title", _bounded(self.title, field_name="title"))
        object.__setattr__(self, "summary", _bounded(self.summary, field_name="summary"))
        object.__setattr__(self, "rule_id", _bounded(self.rule_id, field_name="rule_id"))
        if self.confidence < 0 or self.confidence > 1:
            raise InvalidValueError(
                "Finding confidence must be between 0 and 1",
                reason_code="invalid_confidence",
            )
        object.__setattr__(self, "metadata", _metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class EngineeringRecommendation:
    recommendation_id: EngineeringRecommendationId
    source_recommendation_id: str
    category: EngineeringCategory
    severity: EngineeringSeverity
    title: str
    rationale: str
    priority: str
    related_finding_ids: tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_recommendation_id",
            _bounded(
                self.source_recommendation_id,
                field_name="source_recommendation_id",
                max_length=160,
            ),
        )
        object.__setattr__(self, "title", _bounded(self.title, field_name="title"))
        object.__setattr__(self, "rationale", _bounded(self.rationale, field_name="rationale"))
        object.__setattr__(
            self,
            "priority",
            _bounded(self.priority, field_name="priority", max_length=32),
        )
        object.__setattr__(self, "metadata", _metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class EngineeringMetric:
    metric_id: EngineeringMetricId
    name: str
    kind: EngineeringMetricKind
    value: str
    unit: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "name",
            _bounded(self.name, field_name="metric_name", max_length=256),
        )
        object.__setattr__(self, "value", _bounded(self.value, field_name="metric_value"))
        if self.unit is not None:
            object.__setattr__(
                self,
                "unit",
                _bounded(self.unit, field_name="metric_unit", max_length=64),
            )
        object.__setattr__(self, "metadata", _metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class EngineeringRelationship:
    relationship_id: EngineeringRelationshipId
    relationship_type: EngineeringRelationshipType
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_type",
            _bounded(self.source_type, field_name="source_type", max_length=64),
        )
        object.__setattr__(
            self,
            "source_id",
            _bounded(self.source_id, field_name="source_id", max_length=160),
        )
        object.__setattr__(
            self,
            "target_type",
            _bounded(self.target_type, field_name="target_type", max_length=64),
        )
        object.__setattr__(
            self,
            "target_id",
            _bounded(self.target_id, field_name="target_id", max_length=160),
        )
        object.__setattr__(self, "metadata", _metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class RiskSummaryItem:
    finding_id: str
    severity: EngineeringSeverity
    category: EngineeringCategory
    title: str
