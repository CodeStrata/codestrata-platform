"""Assessment intelligence value objects."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.intelligence.enums import (
    FindingCategory,
    FindingSeverity,
    MetricValueKind,
    RecommendationPriority,
)
from codestrata_platform.domain.intelligence.ids import (
    EvidenceReferenceId,
    FindingId,
    RecommendationId,
)

_SECRET_KEY_MARKERS = (
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "credential",
)
_METRIC_NAME_RE = re.compile(r"^[a-z][a-z0-9]*(?:\.[a-z][a-z0-9_]*)+$")
_ENV_FILE_MARKERS = (".env", ".env.local", ".env.production")
_MAX_METADATA_KEYS = 50
_MAX_STRING = 4000
_MAX_EXCERPT = 500
_EXCERPT_REDACTED = "[REDACTED]"
_EXCERPT_SECRET_PATTERNS = (
    re.compile(
        r"(?i)\b("
        r"password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|"
        r"private[_-]?key|client[_-]?secret|auth[_-]?token"
        r")\b(\s*[=:]\s*)(?:'[^']+'|\"[^\"]+\"|[^\s'\"#,;]+)"
    ),
    re.compile(r"(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)(Authorization:\s*(?:Bearer|Basic)\s+)\S+"),
)


def _sanitize_redacted_excerpt(excerpt: str) -> str:
    sanitized = excerpt
    for pattern in _EXCERPT_SECRET_PATTERNS:
        sanitized = pattern.sub(_EXCERPT_REDACTED, sanitized)
    return sanitized


def _validate_metadata(attributes: Mapping[str, str]) -> dict[str, str]:
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
        if len(compact_key) > _MAX_STRING or len(compact_value) > _MAX_STRING:
            raise InvalidValueError(
                "Metadata key or value exceeds maximum length",
                reason_code="metadata_string_too_long",
            )
        lowered = compact_key.lower()
        if any(marker in lowered for marker in _SECRET_KEY_MARKERS):
            raise InvalidValueError(
                f"Metadata key '{compact_key}' is not allowed",
                reason_code="secret_bearing_metadata",
            )
        normalized[compact_key] = compact_value
    return dict(sorted(normalized.items()))


def _validate_bounded_text(value: str, *, field_name: str, max_length: int = _MAX_STRING) -> str:
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


def _validate_path_reference(path_reference: str) -> str:
    compact = path_reference.strip().replace("\\", "/")
    if not compact:
        raise InvalidValueError(
            "Path reference must be non-blank",
            reason_code="empty_path_reference",
        )
    if compact.startswith("/Users/") or compact.startswith("/home/"):
        raise InvalidValueError(
            "Absolute user paths are not allowed in path references",
            reason_code="absolute_user_path",
        )
    lowered = compact.lower()
    if any(marker in lowered for marker in _ENV_FILE_MARKERS):
        raise InvalidValueError(
            "Environment file paths are not allowed in path references",
            reason_code="env_file_path",
        )
    segments = compact.split("/")
    if ".." in segments:
        raise InvalidValueError(
            "Path reference must not contain path traversal",
            reason_code="path_traversal",
        )
    return compact


@dataclass(frozen=True, slots=True)
class IntelligenceSchemaVersion:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _validate_bounded_text(self.value, field_name="schema_version"),
        )


@dataclass(frozen=True, slots=True)
class MetricName:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip().lower()
        if not compact:
            raise InvalidValueError(
                "Metric name must be non-blank",
                reason_code="empty_metric_name",
            )
        if not _METRIC_NAME_RE.match(compact):
            raise InvalidValueError(
                "Metric name must be namespaced (e.g. security.findings.critical)",
                reason_code="invalid_metric_name",
            )
        object.__setattr__(self, "value", compact)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class MetricValue:
    kind: MetricValueKind
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact:
            raise InvalidValueError(
                "Metric value must be non-blank",
                reason_code="empty_metric_value",
            )
        if len(compact) > _MAX_STRING:
            raise InvalidValueError(
                "Metric value exceeds maximum length",
                reason_code="metric_value_too_long",
            )
        object.__setattr__(self, "value", compact)
        self._validate_kind()

    def _validate_kind(self) -> None:
        if self.kind is MetricValueKind.INTEGER:
            if not re.fullmatch(r"-?\d+", self.value):
                raise InvalidValueError(
                    "Integer metric value must be a whole number",
                    reason_code="invalid_integer_metric",
                )
        elif self.kind is MetricValueKind.DECIMAL:
            if not re.fullmatch(r"-?\d+(?:\.\d+)?", self.value):
                raise InvalidValueError(
                    "Decimal metric value must be numeric",
                    reason_code="invalid_decimal_metric",
                )
        elif self.kind is MetricValueKind.PERCENTAGE:
            if not re.fullmatch(r"-?\d+(?:\.\d+)?", self.value):
                raise InvalidValueError(
                    "Percentage metric value must be numeric",
                    reason_code="invalid_percentage_metric",
                )
            numeric = float(self.value)
            if numeric < 0 or numeric > 100:
                raise InvalidValueError(
                    "Percentage metric value must be between 0 and 100",
                    reason_code="invalid_percentage_range",
                )
        elif self.kind is MetricValueKind.DURATION:
            if not re.fullmatch(r"\d+(?:\.\d+)?(?:ms|s|m|h)", self.value):
                raise InvalidValueError(
                    "Duration metric value must include a unit (ms, s, m, h)",
                    reason_code="invalid_duration_metric",
                )
        elif self.kind is MetricValueKind.COUNT:
            if not re.fullmatch(r"\d+", self.value):
                raise InvalidValueError(
                    "Count metric value must be a non-negative integer",
                    reason_code="invalid_count_metric",
                )


@dataclass(frozen=True, slots=True)
class Metric:
    name: MetricName
    value: MetricValue
    unit: str | None = None
    metadata: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        unit = self.unit.strip() if self.unit is not None else None
        if unit is not None and not unit:
            unit = None
        if unit is not None and len(unit) > 64:
            raise InvalidValueError(
                "Metric unit exceeds maximum length",
                reason_code="metric_unit_too_long",
            )
        object.__setattr__(self, "unit", unit)
        object.__setattr__(
            self,
            "metadata",
            _validate_metadata(self.metadata or {}),
        )


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    evidence_id: EvidenceReferenceId
    path_reference: str
    line_start: int | None = None
    line_end: int | None = None
    symbol: str | None = None
    component: str | None = None
    evidence_type: str | None = None
    checksum: str | None = None
    redacted_excerpt: str | None = None
    source_artifact_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "path_reference", _validate_path_reference(self.path_reference))
        if self.line_start is not None and self.line_start < 1:
            raise InvalidValueError(
                "line_start must be >= 1 when provided",
                reason_code="invalid_line_start",
            )
        if self.line_end is not None and self.line_end < 1:
            raise InvalidValueError(
                "line_end must be >= 1 when provided",
                reason_code="invalid_line_end",
            )
        if (
            self.line_start is not None
            and self.line_end is not None
            and self.line_end < self.line_start
        ):
            raise InvalidValueError(
                "line_end must be >= line_start",
                reason_code="invalid_line_range",
            )
        for field_name, raw in (
            ("symbol", self.symbol),
            ("component", self.component),
            ("evidence_type", self.evidence_type),
            ("checksum", self.checksum),
            ("source_artifact_id", self.source_artifact_id),
        ):
            if raw is None:
                continue
            compact = raw.strip()
            if not compact:
                object.__setattr__(self, field_name, None)
                continue
            if len(compact) > _MAX_STRING:
                raise InvalidValueError(
                    f"{field_name} exceeds maximum length",
                    reason_code=f"{field_name}_too_long",
                )
            object.__setattr__(self, field_name, compact)
        if self.redacted_excerpt is not None:
            excerpt = self.redacted_excerpt.strip()
            if not excerpt:
                object.__setattr__(self, "redacted_excerpt", None)
            elif len(excerpt) > _MAX_EXCERPT:
                raise InvalidValueError(
                    f"redacted_excerpt exceeds maximum length of {_MAX_EXCERPT}",
                    reason_code="excerpt_too_long",
                )
            else:
                object.__setattr__(
                    self,
                    "redacted_excerpt",
                    _sanitize_redacted_excerpt(excerpt),
                )


@dataclass(frozen=True, slots=True)
class Finding:
    finding_id: FindingId
    assessment_id: AssessmentId
    category: FindingCategory
    rule_id: str
    title: str
    summary: str
    severity: FindingSeverity
    confidence: float
    evidence_references: tuple[EvidenceReference, ...]
    production_scope: str | None = None
    affected_component: str | None = None
    affected_path_reference: str | None = None
    remediation_reference: str | None = None
    metadata: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rule_id",
            _validate_bounded_text(self.rule_id, field_name="rule_id"),
        )
        object.__setattr__(self, "title", _validate_bounded_text(self.title, field_name="title"))
        object.__setattr__(
            self,
            "summary",
            _validate_bounded_text(self.summary, field_name="summary"),
        )
        if self.confidence < 0 or self.confidence > 1:
            raise InvalidValueError(
                "Finding confidence must be between 0 and 1",
                reason_code="invalid_confidence",
            )
        if self.affected_path_reference is not None:
            object.__setattr__(
                self,
                "affected_path_reference",
                _validate_path_reference(self.affected_path_reference),
            )
        for field_name in ("production_scope", "affected_component", "remediation_reference"):
            raw = getattr(self, field_name)
            if raw is None:
                continue
            object.__setattr__(
                self,
                field_name,
                _validate_bounded_text(raw, field_name=field_name),
            )
        object.__setattr__(
            self,
            "metadata",
            _validate_metadata(self.metadata or {}),
        )
        object.__setattr__(self, "evidence_references", tuple(self.evidence_references))


@dataclass(frozen=True, slots=True)
class Recommendation:
    recommendation_id: RecommendationId
    assessment_id: AssessmentId
    category: FindingCategory
    title: str
    rationale: str
    priority: RecommendationPriority
    related_finding_ids: tuple[str, ...]
    dependencies: tuple[str, ...]
    effort: str | None = None
    impact: str | None = None
    roadmap_horizon: str | None = None
    metadata: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", _validate_bounded_text(self.title, field_name="title"))
        object.__setattr__(
            self,
            "rationale",
            _validate_bounded_text(self.rationale, field_name="rationale"),
        )
        for field_name in ("effort", "impact", "roadmap_horizon"):
            raw = getattr(self, field_name)
            if raw is None:
                continue
            object.__setattr__(
                self,
                field_name,
                _validate_bounded_text(raw, field_name=field_name),
            )
        object.__setattr__(
            self,
            "metadata",
            _validate_metadata(self.metadata or {}),
        )
        object.__setattr__(self, "related_finding_ids", tuple(self.related_finding_ids))
        object.__setattr__(self, "dependencies", tuple(self.dependencies))
