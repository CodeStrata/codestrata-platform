"""Application models for Canonical Engineering Intelligence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from codestrata_platform.domain.engineering.aggregate import EngineeringSnapshot
from codestrata_platform.domain.engineering.enums import (
    EngineeringCategory,
    EngineeringMetricKind,
    EngineeringSeverity,
    EngineeringSnapshotStatus,
    EvidenceKind,
)
from codestrata_platform.domain.engineering.ids import EngineeringSnapshotId
from codestrata_platform.domain.engineering.value_objects import (
    EngineeringEvidence,
    EngineeringFinding,
    EngineeringMetric,
    EngineeringRecommendation,
    EngineeringTechnology,
)


@dataclass(frozen=True, slots=True)
class EngineeringSnapshotSummary:
    snapshot_id: EngineeringSnapshotId
    assessment_id: str
    assessment_intelligence_id: str
    assessment_revision: int
    version: int
    status: EngineeringSnapshotStatus
    technology_count: int
    finding_count: int
    recommendation_count: int
    metric_count: int
    relationship_count: int
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None

    @classmethod
    def from_aggregate(cls, snapshot: EngineeringSnapshot) -> EngineeringSnapshotSummary:
        return cls(
            snapshot_id=snapshot.snapshot_id,
            assessment_id=snapshot.assessment_id.value,
            assessment_intelligence_id=snapshot.assessment_intelligence_id,
            assessment_revision=snapshot.assessment_revision,
            version=snapshot.version.value,
            status=snapshot.status,
            technology_count=len(snapshot.technologies),
            finding_count=len(snapshot.findings),
            recommendation_count=len(snapshot.recommendations),
            metric_count=len(snapshot.metrics),
            relationship_count=len(snapshot.relationships),
            created_at=snapshot.audit.created_at.value,
            updated_at=snapshot.audit.updated_at.value,
            published_at=snapshot.published_at,
        )


@dataclass(frozen=True, slots=True)
class EngineeringSnapshotDetails(EngineeringSnapshotSummary):
    organization_id: str
    workspace_id: str
    repository_id: str
    source_artifact_ids: tuple[str, ...]

    @classmethod
    def from_aggregate(cls, snapshot: EngineeringSnapshot) -> EngineeringSnapshotDetails:
        summary = EngineeringSnapshotSummary.from_aggregate(snapshot)
        return cls(
            snapshot_id=summary.snapshot_id,
            assessment_id=summary.assessment_id,
            assessment_intelligence_id=summary.assessment_intelligence_id,
            assessment_revision=summary.assessment_revision,
            version=summary.version,
            status=summary.status,
            technology_count=summary.technology_count,
            finding_count=summary.finding_count,
            recommendation_count=summary.recommendation_count,
            metric_count=summary.metric_count,
            relationship_count=summary.relationship_count,
            created_at=summary.created_at,
            updated_at=summary.updated_at,
            published_at=summary.published_at,
            organization_id=snapshot.organization_id.value,
            workspace_id=snapshot.workspace_id.value,
            repository_id=snapshot.repository_id.value,
            source_artifact_ids=snapshot.source_artifact_ids,
        )


@dataclass(frozen=True, slots=True)
class TechnologySummary:
    technology_id: str
    canonical_key: str
    display_name: str
    category: EngineeringCategory

    @classmethod
    def from_domain(cls, item: EngineeringTechnology) -> TechnologySummary:
        return cls(
            technology_id=item.technology_id.value,
            canonical_key=item.canonical_key,
            display_name=item.display_name,
            category=item.category,
        )


@dataclass(frozen=True, slots=True)
class FindingSummary:
    finding_id: str
    source_finding_id: str
    category: EngineeringCategory
    severity: EngineeringSeverity
    title: str
    rule_id: str
    confidence: float

    @classmethod
    def from_domain(cls, item: EngineeringFinding) -> FindingSummary:
        return cls(
            finding_id=item.finding_id.value,
            source_finding_id=item.source_finding_id,
            category=item.category,
            severity=item.severity,
            title=item.title,
            rule_id=item.rule_id,
            confidence=item.confidence,
        )


@dataclass(frozen=True, slots=True)
class RiskSummary:
    finding_id: str
    severity: EngineeringSeverity
    category: EngineeringCategory
    title: str


@dataclass(frozen=True, slots=True)
class RecommendationSummary:
    recommendation_id: str
    source_recommendation_id: str
    category: EngineeringCategory
    severity: EngineeringSeverity
    title: str
    priority: str
    related_finding_ids: tuple[str, ...]

    @classmethod
    def from_domain(cls, item: EngineeringRecommendation) -> RecommendationSummary:
        return cls(
            recommendation_id=item.recommendation_id.value,
            source_recommendation_id=item.source_recommendation_id,
            category=item.category,
            severity=item.severity,
            title=item.title,
            priority=item.priority,
            related_finding_ids=item.related_finding_ids,
        )


@dataclass(frozen=True, slots=True)
class MetricSummary:
    metric_id: str
    name: str
    kind: EngineeringMetricKind
    value: str
    unit: str | None

    @classmethod
    def from_domain(cls, item: EngineeringMetric) -> MetricSummary:
        return cls(
            metric_id=item.metric_id.value,
            name=item.name,
            kind=item.kind,
            value=item.value,
            unit=item.unit,
        )


@dataclass(frozen=True, slots=True)
class EvidenceSummary:
    evidence_id: str
    kind: EvidenceKind
    reference: str
    line_start: int | None
    line_end: int | None

    @classmethod
    def from_domain(cls, item: EngineeringEvidence) -> EvidenceSummary:
        return cls(
            evidence_id=item.evidence_id.value,
            kind=item.kind,
            reference=item.reference,
            line_start=item.line_start,
            line_end=item.line_end,
        )


@dataclass(frozen=True, slots=True)
class EngineeringBuildResult:
    snapshot: EngineeringSnapshotDetails
    created: bool
    idempotent: bool
