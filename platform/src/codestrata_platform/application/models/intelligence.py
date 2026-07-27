"""Assessment intelligence application models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.intelligence.aggregate import AssessmentIntelligence
from codestrata_platform.domain.intelligence.enums import (
    FindingCategory,
    FindingSeverity,
    IntelligenceIngestionStatus,
    MetricValueKind,
    RecommendationPriority,
)
from codestrata_platform.domain.intelligence.ids import (
    AssessmentIntelligenceId,
    FindingId,
    RecommendationId,
)
from codestrata_platform.domain.intelligence.value_objects import (
    EvidenceReference,
    Finding,
    Metric,
    Recommendation,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId


@dataclass(frozen=True, slots=True)
class IntelligenceRegistration:
    intelligence_id: AssessmentIntelligenceId
    assessment_id: AssessmentId
    revision: int
    idempotency_key: str
    status: IntelligenceIngestionStatus
    created: bool


@dataclass(frozen=True, slots=True)
class IntelligenceSummary:
    intelligence_id: AssessmentIntelligenceId
    assessment_id: AssessmentId
    revision: int
    status: IntelligenceIngestionStatus
    finding_count: int
    metric_count: int
    recommendation_count: int


@dataclass(frozen=True, slots=True)
class IntelligenceDetails:
    intelligence_id: AssessmentIntelligenceId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    repository_id: RepositoryId
    assessment_id: AssessmentId
    engine_assessment_id: str
    schema_version: str
    parser_version: str
    revision: int
    idempotency_key: str
    status: IntelligenceIngestionStatus
    source_artifact_ids: tuple[str, ...]
    finding_count: int
    metric_count: int
    recommendation_count: int
    failure_reason: str | None
    diagnostics: tuple[str, ...]
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    @classmethod
    def from_aggregate(cls, intelligence: AssessmentIntelligence) -> IntelligenceDetails:
        return cls(
            intelligence_id=intelligence.intelligence_id,
            organization_id=intelligence.organization_id,
            workspace_id=intelligence.workspace_id,
            repository_id=intelligence.repository_id,
            assessment_id=intelligence.assessment_id,
            engine_assessment_id=intelligence.engine_assessment_id,
            schema_version=intelligence.schema_version.value,
            parser_version=intelligence.parser_version,
            revision=intelligence.revision,
            idempotency_key=intelligence.idempotency_key,
            status=intelligence.status,
            source_artifact_ids=intelligence.source_artifact_ids,
            finding_count=len(intelligence.findings),
            metric_count=len(intelligence.metrics),
            recommendation_count=len(intelligence.recommendations),
            failure_reason=intelligence.failure_reason,
            diagnostics=intelligence.diagnostics,
            created_at=intelligence.audit.created_at.value,
            updated_at=intelligence.audit.updated_at.value,
            completed_at=intelligence.completed_at,
        )

    def to_summary(self) -> IntelligenceSummary:
        return IntelligenceSummary(
            intelligence_id=self.intelligence_id,
            assessment_id=self.assessment_id,
            revision=self.revision,
            status=self.status,
            finding_count=self.finding_count,
            metric_count=self.metric_count,
            recommendation_count=self.recommendation_count,
        )


@dataclass(frozen=True, slots=True)
class FindingView:
    finding_id: FindingId
    assessment_id: AssessmentId
    category: FindingCategory
    rule_id: str
    title: str
    summary: str
    severity: FindingSeverity
    confidence: float
    production_scope: str | None
    affected_component: str | None
    affected_path_reference: str | None
    evidence_count: int
    remediation_reference: str | None
    metadata: dict[str, str]

    @classmethod
    def from_domain(cls, finding: Finding) -> FindingView:
        return cls(
            finding_id=finding.finding_id,
            assessment_id=finding.assessment_id,
            category=finding.category,
            rule_id=finding.rule_id,
            title=finding.title,
            summary=finding.summary,
            severity=finding.severity,
            confidence=finding.confidence,
            production_scope=finding.production_scope,
            affected_component=finding.affected_component,
            affected_path_reference=finding.affected_path_reference,
            evidence_count=len(finding.evidence_references),
            remediation_reference=finding.remediation_reference,
            metadata=dict(finding.metadata),
        )


@dataclass(frozen=True, slots=True)
class FindingDetails(FindingView):
    evidence_references: tuple[EvidenceReference, ...]

    @classmethod
    def from_domain(cls, finding: Finding) -> FindingDetails:
        return cls(
            finding_id=finding.finding_id,
            assessment_id=finding.assessment_id,
            category=finding.category,
            rule_id=finding.rule_id,
            title=finding.title,
            summary=finding.summary,
            severity=finding.severity,
            confidence=finding.confidence,
            production_scope=finding.production_scope,
            affected_component=finding.affected_component,
            affected_path_reference=finding.affected_path_reference,
            evidence_count=len(finding.evidence_references),
            remediation_reference=finding.remediation_reference,
            metadata=dict(finding.metadata),
            evidence_references=finding.evidence_references,
        )


@dataclass(frozen=True, slots=True)
class MetricView:
    name: str
    kind: MetricValueKind
    value: str
    unit: str | None
    metadata: dict[str, str]

    @classmethod
    def from_domain(cls, metric: Metric) -> MetricView:
        return cls(
            name=metric.name.value,
            kind=metric.value.kind,
            value=metric.value.value,
            unit=metric.unit,
            metadata=dict(metric.metadata),
        )


@dataclass(frozen=True, slots=True)
class RecommendationView:
    recommendation_id: RecommendationId
    assessment_id: AssessmentId
    category: FindingCategory
    title: str
    rationale: str
    priority: RecommendationPriority
    effort: str | None
    impact: str | None
    dependencies: tuple[str, ...]
    related_finding_ids: tuple[str, ...]
    roadmap_horizon: str | None
    metadata: dict[str, str]

    @classmethod
    def from_domain(cls, recommendation: Recommendation) -> RecommendationView:
        return cls(
            recommendation_id=recommendation.recommendation_id,
            assessment_id=recommendation.assessment_id,
            category=recommendation.category,
            title=recommendation.title,
            rationale=recommendation.rationale,
            priority=recommendation.priority,
            effort=recommendation.effort,
            impact=recommendation.impact,
            dependencies=recommendation.dependencies,
            related_finding_ids=recommendation.related_finding_ids,
            roadmap_horizon=recommendation.roadmap_horizon,
            metadata=dict(recommendation.metadata),
        )


@dataclass(frozen=True, slots=True)
class IntelligenceProcessingResult:
    intelligence: IntelligenceDetails
    created: bool
    idempotent: bool
