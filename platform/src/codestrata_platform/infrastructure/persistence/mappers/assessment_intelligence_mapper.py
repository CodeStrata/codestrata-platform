"""AssessmentIntelligence ↔ persistence record mapper."""

from __future__ import annotations

from typing import Any

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
    EvidenceReferenceId,
    FindingId,
    RecommendationId,
)
from codestrata_platform.domain.intelligence.value_objects import (
    EvidenceReference,
    Finding,
    IntelligenceSchemaVersion,
    Metric,
    MetricName,
    MetricValue,
    Recommendation,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.infrastructure.persistence.mappers._helpers import audit_from_record
from codestrata_platform.infrastructure.persistence.models.assessment_intelligence_record import (
    AssessmentIntelligenceRecord,
)
from codestrata_platform.infrastructure.persistence.models.evidence_reference_record import (
    EvidenceReferenceRecord,
)
from codestrata_platform.infrastructure.persistence.models.finding_record import FindingRecord
from codestrata_platform.infrastructure.persistence.models.intelligence_source_artifact_record import (  # noqa: E501
    IntelligenceSourceArtifactRecord,
)
from codestrata_platform.infrastructure.persistence.models.metric_record import MetricRecord
from codestrata_platform.infrastructure.persistence.models.recommendation_finding_link_record import (  # noqa: E501
    RecommendationFindingLinkRecord,
)
from codestrata_platform.infrastructure.persistence.models.recommendation_record import (
    RecommendationRecord,
)


def metric_record_id(*, assessment_id: str, metric_name: str) -> str:
    return f"{assessment_id}:{metric_name}"


class AssessmentIntelligenceMapper:
    @staticmethod
    def to_record(intelligence: AssessmentIntelligence) -> AssessmentIntelligenceRecord:
        return AssessmentIntelligenceRecord(
            id=intelligence.intelligence_id.value,
            organization_id=intelligence.organization_id.value,
            workspace_id=intelligence.workspace_id.value,
            repository_id=intelligence.repository_id.value,
            assessment_id=intelligence.assessment_id.value,
            engine_assessment_id=intelligence.engine_assessment_id,
            schema_version=intelligence.schema_version.value,
            parser_version=intelligence.parser_version,
            revision=intelligence.revision,
            idempotency_key=intelligence.idempotency_key,
            status=intelligence.status.value,
            source_artifact_ids_json=list(intelligence.source_artifact_ids),
            findings_json=[
                AssessmentIntelligenceMapper.finding_to_json(finding)
                for finding in intelligence.findings
            ],
            metrics_json=[
                AssessmentIntelligenceMapper.metric_to_json(metric)
                for metric in intelligence.metrics
            ],
            recommendations_json=[
                AssessmentIntelligenceMapper.recommendation_to_json(recommendation)
                for recommendation in intelligence.recommendations
            ],
            diagnostics_json=list(intelligence.diagnostics),
            failure_reason=intelligence.failure_reason,
            created_at=intelligence.audit.created_at.value,
            updated_at=intelligence.audit.updated_at.value,
            completed_at=intelligence.completed_at,
            optimistic_version=intelligence._version,
        )

    @staticmethod
    def apply_to_record(
        intelligence: AssessmentIntelligence,
        record: AssessmentIntelligenceRecord,
    ) -> None:
        record.organization_id = intelligence.organization_id.value
        record.workspace_id = intelligence.workspace_id.value
        record.repository_id = intelligence.repository_id.value
        record.assessment_id = intelligence.assessment_id.value
        record.engine_assessment_id = intelligence.engine_assessment_id
        record.schema_version = intelligence.schema_version.value
        record.parser_version = intelligence.parser_version
        record.revision = intelligence.revision
        record.idempotency_key = intelligence.idempotency_key
        record.status = intelligence.status.value
        record.source_artifact_ids_json = list(intelligence.source_artifact_ids)
        record.findings_json = [
            AssessmentIntelligenceMapper.finding_to_json(finding)
            for finding in intelligence.findings
        ]
        record.metrics_json = [
            AssessmentIntelligenceMapper.metric_to_json(metric)
            for metric in intelligence.metrics
        ]
        record.recommendations_json = [
            AssessmentIntelligenceMapper.recommendation_to_json(recommendation)
            for recommendation in intelligence.recommendations
        ]
        record.diagnostics_json = list(intelligence.diagnostics)
        record.failure_reason = intelligence.failure_reason
        record.created_at = intelligence.audit.created_at.value
        record.updated_at = intelligence.audit.updated_at.value
        record.completed_at = intelligence.completed_at
        record.optimistic_version = intelligence._version

    @staticmethod
    def to_domain(record: AssessmentIntelligenceRecord) -> AssessmentIntelligence:
        return AssessmentIntelligence(
            intelligence_id=AssessmentIntelligenceId(record.id),
            organization_id=OrganizationId(record.organization_id),
            workspace_id=WorkspaceId(record.workspace_id),
            repository_id=RepositoryId(record.repository_id),
            assessment_id=AssessmentId(record.assessment_id),
            engine_assessment_id=record.engine_assessment_id,
            schema_version=IntelligenceSchemaVersion(record.schema_version),
            parser_version=record.parser_version,
            revision=record.revision,
            idempotency_key=record.idempotency_key,
            status=IntelligenceIngestionStatus(record.status),
            source_artifact_ids=tuple(record.source_artifact_ids_json or []),
            findings=tuple(
                AssessmentIntelligenceMapper.finding_from_json(item)
                for item in (record.findings_json or [])
            ),
            metrics=tuple(
                AssessmentIntelligenceMapper.metric_from_json(item)
                for item in (record.metrics_json or [])
            ),
            recommendations=tuple(
                AssessmentIntelligenceMapper.recommendation_from_json(item)
                for item in (record.recommendations_json or [])
            ),
            audit=audit_from_record(
                created_at=record.created_at,
                updated_at=record.updated_at,
            ),
            failure_reason=record.failure_reason,
            diagnostics=tuple(record.diagnostics_json or []),
            completed_at=record.completed_at,
            _version=record.optimistic_version,
        )

    @staticmethod
    def source_artifact_to_record(
        *,
        intelligence_id: str,
        assessment_id: str,
        artifact_id: str,
    ) -> IntelligenceSourceArtifactRecord:
        return IntelligenceSourceArtifactRecord(
            intelligence_id=intelligence_id,
            assessment_id=assessment_id,
            artifact_id=artifact_id,
        )

    @staticmethod
    def finding_to_json(finding: Finding) -> dict[str, Any]:
        return {
            "finding_id": finding.finding_id.value,
            "assessment_id": finding.assessment_id.value,
            "category": finding.category.value,
            "rule_id": finding.rule_id,
            "title": finding.title,
            "summary": finding.summary,
            "severity": finding.severity.value,
            "confidence": finding.confidence,
            "production_scope": finding.production_scope,
            "affected_component": finding.affected_component,
            "affected_path_reference": finding.affected_path_reference,
            "remediation_reference": finding.remediation_reference,
            "metadata": dict(finding.metadata or {}),
            "evidence_references": [
                AssessmentIntelligenceMapper.evidence_to_json(evidence)
                for evidence in finding.evidence_references
            ],
        }

    @staticmethod
    def finding_from_json(data: dict[str, Any]) -> Finding:
        return Finding(
            finding_id=FindingId(data["finding_id"]),
            assessment_id=AssessmentId(data["assessment_id"]),
            category=FindingCategory(data["category"]),
            rule_id=data["rule_id"],
            title=data["title"],
            summary=data["summary"],
            severity=FindingSeverity(data["severity"]),
            confidence=float(data["confidence"]),
            evidence_references=tuple(
                AssessmentIntelligenceMapper.evidence_from_json(item)
                for item in data.get("evidence_references", [])
            ),
            production_scope=data.get("production_scope"),
            affected_component=data.get("affected_component"),
            affected_path_reference=data.get("affected_path_reference"),
            remediation_reference=data.get("remediation_reference"),
            metadata=dict(data.get("metadata") or {}),
        )

    @staticmethod
    def evidence_to_json(evidence: EvidenceReference) -> dict[str, Any]:
        return {
            "evidence_id": evidence.evidence_id.value,
            "path_reference": evidence.path_reference,
            "line_start": evidence.line_start,
            "line_end": evidence.line_end,
            "symbol": evidence.symbol,
            "component": evidence.component,
            "evidence_type": evidence.evidence_type,
            "checksum": evidence.checksum,
            "redacted_excerpt": evidence.redacted_excerpt,
            "source_artifact_id": evidence.source_artifact_id,
        }

    @staticmethod
    def evidence_from_json(data: dict[str, Any]) -> EvidenceReference:
        return EvidenceReference(
            evidence_id=EvidenceReferenceId(data["evidence_id"]),
            path_reference=data["path_reference"],
            line_start=data.get("line_start"),
            line_end=data.get("line_end"),
            symbol=data.get("symbol"),
            component=data.get("component"),
            evidence_type=data.get("evidence_type"),
            checksum=data.get("checksum"),
            redacted_excerpt=data.get("redacted_excerpt"),
            source_artifact_id=data.get("source_artifact_id"),
        )

    @staticmethod
    def metric_to_json(metric: Metric) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": metric.name.value,
            "value_kind": metric.value.kind.value,
            "value": metric.value.value,
        }
        if metric.unit is not None:
            payload["unit"] = metric.unit
        if metric.metadata:
            payload["metadata"] = dict(metric.metadata)
        return payload

    @staticmethod
    def metric_from_json(data: dict[str, Any]) -> Metric:
        return Metric(
            name=MetricName(data["name"]),
            value=MetricValue(
                kind=MetricValueKind(data["value_kind"]),
                value=data["value"],
            ),
            unit=data.get("unit"),
            metadata=dict(data.get("metadata") or {}),
        )

    @staticmethod
    def recommendation_to_json(recommendation: Recommendation) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "recommendation_id": recommendation.recommendation_id.value,
            "assessment_id": recommendation.assessment_id.value,
            "category": recommendation.category.value,
            "title": recommendation.title,
            "rationale": recommendation.rationale,
            "priority": recommendation.priority.value,
            "related_finding_ids": list(recommendation.related_finding_ids),
            "dependencies": list(recommendation.dependencies),
        }
        if recommendation.effort is not None:
            payload["effort"] = recommendation.effort
        if recommendation.impact is not None:
            payload["impact"] = recommendation.impact
        if recommendation.roadmap_horizon is not None:
            payload["roadmap_horizon"] = recommendation.roadmap_horizon
        if recommendation.metadata:
            payload["metadata"] = dict(recommendation.metadata)
        return payload

    @staticmethod
    def recommendation_from_json(data: dict[str, Any]) -> Recommendation:
        return Recommendation(
            recommendation_id=RecommendationId(data["recommendation_id"]),
            assessment_id=AssessmentId(data["assessment_id"]),
            category=FindingCategory(data["category"]),
            title=data["title"],
            rationale=data["rationale"],
            priority=RecommendationPriority(data["priority"]),
            related_finding_ids=tuple(data.get("related_finding_ids", [])),
            dependencies=tuple(data.get("dependencies", [])),
            effort=data.get("effort"),
            impact=data.get("impact"),
            roadmap_horizon=data.get("roadmap_horizon"),
            metadata=dict(data.get("metadata") or {}),
        )

    @staticmethod
    def finding_to_record(
        finding: Finding,
        *,
        intelligence_id: str,
    ) -> FindingRecord:
        return FindingRecord(
            id=finding.finding_id.value,
            assessment_id=finding.assessment_id.value,
            intelligence_id=intelligence_id,
            category=finding.category.value,
            rule_id=finding.rule_id,
            title=finding.title,
            summary=finding.summary,
            severity=finding.severity.value,
            confidence=finding.confidence,
            production_scope=finding.production_scope,
            affected_component=finding.affected_component,
            affected_path_reference=finding.affected_path_reference,
            remediation_reference=finding.remediation_reference,
            metadata_json=dict(finding.metadata or {}),
        )

    @staticmethod
    def evidence_to_record(
        evidence: EvidenceReference,
        *,
        finding_id: str,
        assessment_id: str,
    ) -> EvidenceReferenceRecord:
        return EvidenceReferenceRecord(
            id=evidence.evidence_id.value,
            finding_id=finding_id,
            assessment_id=assessment_id,
            path_reference=evidence.path_reference,
            line_start=evidence.line_start,
            line_end=evidence.line_end,
            symbol=evidence.symbol,
            component=evidence.component,
            evidence_type=evidence.evidence_type,
            checksum=evidence.checksum,
            redacted_excerpt=evidence.redacted_excerpt,
            source_artifact_id=evidence.source_artifact_id,
        )

    @staticmethod
    def finding_to_domain(
        record: FindingRecord,
        evidence_records: tuple[EvidenceReferenceRecord, ...],
    ) -> Finding:
        return Finding(
            finding_id=FindingId(record.id),
            assessment_id=AssessmentId(record.assessment_id),
            category=FindingCategory(record.category),
            rule_id=record.rule_id,
            title=record.title,
            summary=record.summary,
            severity=FindingSeverity(record.severity),
            confidence=record.confidence,
            evidence_references=tuple(
                EvidenceReference(
                    evidence_id=EvidenceReferenceId(item.id),
                    path_reference=item.path_reference,
                    line_start=item.line_start,
                    line_end=item.line_end,
                    symbol=item.symbol,
                    component=item.component,
                    evidence_type=item.evidence_type,
                    checksum=item.checksum,
                    redacted_excerpt=item.redacted_excerpt,
                    source_artifact_id=item.source_artifact_id,
                )
                for item in evidence_records
            ),
            production_scope=record.production_scope,
            affected_component=record.affected_component,
            affected_path_reference=record.affected_path_reference,
            remediation_reference=record.remediation_reference,
            metadata=dict(record.metadata_json or {}),
        )

    @staticmethod
    def metric_to_record(
        metric: Metric,
        *,
        assessment_id: str,
        intelligence_id: str,
    ) -> MetricRecord:
        return MetricRecord(
            id=metric_record_id(assessment_id=assessment_id, metric_name=metric.name.value),
            assessment_id=assessment_id,
            intelligence_id=intelligence_id,
            name=metric.name.value,
            value_kind=metric.value.kind.value,
            value_text=metric.value.value,
            unit=metric.unit,
            metadata_json=dict(metric.metadata or {}),
        )

    @staticmethod
    def metric_to_domain(record: MetricRecord) -> Metric:
        return Metric(
            name=MetricName(record.name),
            value=MetricValue(
                kind=MetricValueKind(record.value_kind),
                value=record.value_text,
            ),
            unit=record.unit,
            metadata=dict(record.metadata_json or {}),
        )

    @staticmethod
    def recommendation_to_record(
        recommendation: Recommendation,
        *,
        intelligence_id: str,
    ) -> RecommendationRecord:
        return RecommendationRecord(
            id=recommendation.recommendation_id.value,
            assessment_id=recommendation.assessment_id.value,
            intelligence_id=intelligence_id,
            category=recommendation.category.value,
            title=recommendation.title,
            rationale=recommendation.rationale,
            priority=recommendation.priority.value,
            effort=recommendation.effort,
            impact=recommendation.impact,
            roadmap_horizon=recommendation.roadmap_horizon,
            dependencies_json=list(recommendation.dependencies),
            metadata_json=dict(recommendation.metadata or {}),
        )

    @staticmethod
    def recommendation_finding_link_to_record(
        *,
        recommendation_id: str,
        finding_id: str,
        assessment_id: str,
    ) -> RecommendationFindingLinkRecord:
        return RecommendationFindingLinkRecord(
            recommendation_id=recommendation_id,
            finding_id=finding_id,
            assessment_id=assessment_id,
        )

    @staticmethod
    def recommendation_to_domain(
        record: RecommendationRecord,
        *,
        related_finding_ids: tuple[str, ...],
    ) -> Recommendation:
        return Recommendation(
            recommendation_id=RecommendationId(record.id),
            assessment_id=AssessmentId(record.assessment_id),
            category=FindingCategory(record.category),
            title=record.title,
            rationale=record.rationale,
            priority=RecommendationPriority(record.priority),
            related_finding_ids=related_finding_ids,
            dependencies=tuple(record.dependencies_json or []),
            effort=record.effort,
            impact=record.impact,
            roadmap_horizon=record.roadmap_horizon,
            metadata=dict(record.metadata_json or {}),
        )
