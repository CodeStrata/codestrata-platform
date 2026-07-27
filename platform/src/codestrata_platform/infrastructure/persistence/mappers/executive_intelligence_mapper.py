"""ExecutiveIntelligenceSnapshot <-> persistence mapper."""

from __future__ import annotations

from codestrata_platform.domain.executive_intelligence.identifiers import (
    ExecutiveFindingId,
    ExecutiveIntelligenceId,
    ExecutiveIntelligenceVersion,
    ExecutiveMetricId,
    ExecutivePolicyVersion,
    ExecutiveProjectionKey,
    ExecutiveRecommendationId,
)
from codestrata_platform.domain.executive_intelligence.lifecycle import (
    ExecutiveConfidenceBand,
    ExecutiveFindingCategory,
    ExecutiveImpactBand,
    ExecutiveIntelligenceStatus,
    ExecutiveMetricKey,
    ExecutiveRecommendationTheme,
)
from codestrata_platform.domain.executive_intelligence.models import (
    ExecutiveFinding,
    ExecutiveMetric,
    ExecutiveRecommendation,
    StrategicObservation,
)
from codestrata_platform.domain.executive_intelligence.snapshot import ExecutiveIntelligenceSnapshot
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.infrastructure.persistence.mappers._helpers import audit_from_record
from codestrata_platform.infrastructure.persistence.models.executive_intelligence_records import (
    EngineeringExecutiveFindingRecord,
    EngineeringExecutiveIntelligenceSnapshotRecord,
    EngineeringExecutiveMetricRecord,
    EngineeringExecutiveObservationRecord,
    EngineeringExecutiveRecommendationRecord,
)


class ExecutiveIntelligenceMapper:
    @staticmethod
    def to_snapshot_record(
        snapshot: ExecutiveIntelligenceSnapshot,
    ) -> EngineeringExecutiveIntelligenceSnapshotRecord:
        return EngineeringExecutiveIntelligenceSnapshotRecord(
            executive_intelligence_id=snapshot.executive_intelligence_id.value,
            organization_id=snapshot.organization_id.value,
            workspace_id=snapshot.workspace_id.value,
            portfolio_id=snapshot.portfolio_id.value,
            portfolio_snapshot_id=snapshot.portfolio_snapshot_id.value,
            portfolio_snapshot_version=snapshot.portfolio_snapshot_version,
            version=snapshot.version.value,
            status=snapshot.status.value,
            projection_key=snapshot.projection_key.value,
            schema_version=snapshot.schema_version,
            policy_version=snapshot.policy_version.value,
            limitations=list(snapshot.limitations),
            created_at=snapshot.audit.created_at.value,
            updated_at=snapshot.audit.updated_at.value,
            completed_at=snapshot.completed_at,
            superseded_at=snapshot.superseded_at,
            failure_reason=snapshot.failure_reason,
            optimistic_version=snapshot._version,  # noqa: SLF001
        )

    @staticmethod
    def apply_snapshot_to_record(
        snapshot: ExecutiveIntelligenceSnapshot,
        record: EngineeringExecutiveIntelligenceSnapshotRecord,
    ) -> None:
        fresh = ExecutiveIntelligenceMapper.to_snapshot_record(snapshot)
        for column in EngineeringExecutiveIntelligenceSnapshotRecord.__table__.columns:
            if column.name == "executive_intelligence_id":
                continue
            setattr(record, column.name, getattr(fresh, column.name))

    @staticmethod
    def to_metric_records(
        snapshot: ExecutiveIntelligenceSnapshot,
    ) -> list[EngineeringExecutiveMetricRecord]:
        exec_id = snapshot.executive_intelligence_id.value
        return [
            EngineeringExecutiveMetricRecord(
                id=item.metric_id.value,
                executive_intelligence_id=exec_id,
                key=item.key.value,
                score=item.score,
                confidence=item.confidence,
                confidence_band=item.confidence_band.value,
                coverage=item.coverage,
                inputs=list(item.inputs),
                calculation_rule=item.calculation_rule,
                limitations=list(item.limitations),
                policy_version=item.policy_version,
            )
            for item in snapshot.metrics
        ]

    @staticmethod
    def to_finding_records(
        snapshot: ExecutiveIntelligenceSnapshot,
    ) -> list[EngineeringExecutiveFindingRecord]:
        exec_id = snapshot.executive_intelligence_id.value
        return [
            EngineeringExecutiveFindingRecord(
                id=item.finding_id.value,
                executive_intelligence_id=exec_id,
                category=item.category.value,
                title=item.title,
                summary=item.summary,
                severity_band=item.severity_band.value,
                confidence=item.confidence,
                confidence_band=item.confidence_band.value,
                affected_repository_ids=list(item.affected_repository_ids),
                source_references=list(item.source_references),
                evidence=list(item.evidence),
                policy_version=item.policy_version,
            )
            for item in snapshot.findings
        ]

    @staticmethod
    def to_recommendation_records(
        snapshot: ExecutiveIntelligenceSnapshot,
    ) -> list[EngineeringExecutiveRecommendationRecord]:
        exec_id = snapshot.executive_intelligence_id.value
        return [
            EngineeringExecutiveRecommendationRecord(
                id=item.recommendation_id.value,
                executive_intelligence_id=exec_id,
                theme=item.theme.value,
                title=item.title,
                rationale=item.rationale,
                affected_repository_ids=list(item.affected_repository_ids),
                confidence=item.confidence,
                confidence_band=item.confidence_band.value,
                expected_impact=item.expected_impact.value,
                source_references=list(item.source_references),
                priority_score=item.priority_score,
                policy_version=item.policy_version,
            )
            for item in snapshot.recommendations
        ]

    @staticmethod
    def to_observation_records(
        snapshot: ExecutiveIntelligenceSnapshot,
    ) -> list[EngineeringExecutiveObservationRecord]:
        exec_id = snapshot.executive_intelligence_id.value
        return [
            EngineeringExecutiveObservationRecord(
                id=f"{exec_id}:{item.observation_key}",
                executive_intelligence_id=exec_id,
                observation_key=item.observation_key,
                title=item.title,
                summary=item.summary,
                related_metric_keys=list(item.related_metric_keys),
                related_finding_ids=list(item.related_finding_ids),
                confidence=item.confidence,
                confidence_band=item.confidence_band.value,
            )
            for item in snapshot.observations
        ]

    @staticmethod
    def from_records(
        record: EngineeringExecutiveIntelligenceSnapshotRecord,
        *,
        metric_records: list[EngineeringExecutiveMetricRecord],
        finding_records: list[EngineeringExecutiveFindingRecord],
        recommendation_records: list[EngineeringExecutiveRecommendationRecord],
        observation_records: list[EngineeringExecutiveObservationRecord],
    ) -> ExecutiveIntelligenceSnapshot:
        metrics = tuple(
            ExecutiveMetric(
                metric_id=ExecutiveMetricId(item.id),
                key=ExecutiveMetricKey(item.key),
                score=item.score,
                confidence=item.confidence,
                confidence_band=ExecutiveConfidenceBand(item.confidence_band),
                coverage=item.coverage,
                inputs=tuple(item.inputs or ()),
                calculation_rule=item.calculation_rule,
                limitations=tuple(item.limitations or ()),
                policy_version=item.policy_version,
            )
            for item in metric_records
        )
        findings = tuple(
            ExecutiveFinding(
                finding_id=ExecutiveFindingId(item.id),
                category=ExecutiveFindingCategory(item.category),
                title=item.title,
                summary=item.summary,
                severity_band=ExecutiveImpactBand(item.severity_band),
                confidence=item.confidence,
                confidence_band=ExecutiveConfidenceBand(item.confidence_band),
                affected_repository_ids=tuple(item.affected_repository_ids or ()),
                source_references=tuple(item.source_references or ()),
                evidence=tuple(item.evidence or ()),
                policy_version=item.policy_version,
            )
            for item in finding_records
        )
        recommendations = tuple(
            ExecutiveRecommendation(
                recommendation_id=ExecutiveRecommendationId(item.id),
                theme=ExecutiveRecommendationTheme(item.theme),
                title=item.title,
                rationale=item.rationale,
                affected_repository_ids=tuple(item.affected_repository_ids or ()),
                confidence=item.confidence,
                confidence_band=ExecutiveConfidenceBand(item.confidence_band),
                expected_impact=ExecutiveImpactBand(item.expected_impact),
                source_references=tuple(item.source_references or ()),
                priority_score=item.priority_score,
                policy_version=item.policy_version,
            )
            for item in recommendation_records
        )
        observations = tuple(
            StrategicObservation(
                observation_key=item.observation_key,
                title=item.title,
                summary=item.summary,
                related_metric_keys=tuple(item.related_metric_keys or ()),
                related_finding_ids=tuple(item.related_finding_ids or ()),
                confidence=item.confidence,
                confidence_band=ExecutiveConfidenceBand(item.confidence_band),
            )
            for item in observation_records
        )
        return ExecutiveIntelligenceSnapshot(
            executive_intelligence_id=ExecutiveIntelligenceId(record.executive_intelligence_id),
            organization_id=OrganizationId(record.organization_id),
            workspace_id=WorkspaceId(record.workspace_id),
            portfolio_id=PortfolioId(record.portfolio_id),
            portfolio_snapshot_id=PortfolioSnapshotId(record.portfolio_snapshot_id),
            portfolio_snapshot_version=record.portfolio_snapshot_version,
            version=ExecutiveIntelligenceVersion(record.version),
            status=ExecutiveIntelligenceStatus(record.status),
            projection_key=ExecutiveProjectionKey(record.projection_key),
            schema_version=record.schema_version,
            policy_version=ExecutivePolicyVersion(record.policy_version),
            metrics=metrics,
            findings=findings,
            recommendations=recommendations,
            observations=observations,
            limitations=tuple(record.limitations or ()),
            audit=audit_from_record(created_at=record.created_at, updated_at=record.updated_at),
            completed_at=record.completed_at,
            superseded_at=record.superseded_at,
            failure_reason=record.failure_reason,
            _version=record.optimistic_version,
        )
