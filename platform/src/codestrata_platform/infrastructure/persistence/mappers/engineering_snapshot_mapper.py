"""EngineeringSnapshot ↔ persistence record mapper."""

from __future__ import annotations

from typing import Any

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.engineering.aggregate import EngineeringSnapshot
from codestrata_platform.domain.engineering.enums import (
    EngineeringCategory,
    EngineeringMetricKind,
    EngineeringRelationshipType,
    EngineeringSeverity,
    EngineeringSnapshotStatus,
    EvidenceKind,
)
from codestrata_platform.domain.engineering.ids import (
    EngineeringComponentId,
    EngineeringEvidenceId,
    EngineeringFindingId,
    EngineeringMetricId,
    EngineeringRecommendationId,
    EngineeringRelationshipId,
    EngineeringSnapshotId,
    EngineeringTechnologyId,
)
from codestrata_platform.domain.engineering.value_objects import (
    EngineeringComponent,
    EngineeringEvidence,
    EngineeringFinding,
    EngineeringMetric,
    EngineeringRecommendation,
    EngineeringRelationship,
    EngineeringSnapshotVersion,
    EngineeringTag,
    EngineeringTechnology,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.infrastructure.persistence.mappers._helpers import (
    audit_from_record,
    ensure_utc,
)
from codestrata_platform.infrastructure.persistence.models.engineering_records import (
    EngineeringComponentRecord,
    EngineeringEvidenceRecord,
    EngineeringFindingRecord,
    EngineeringMetricRecord,
    EngineeringRecommendationRecord,
    EngineeringRelationshipRecord,
    EngineeringSnapshotRecord,
    EngineeringTagRecord,
    EngineeringTechnologyRecord,
)


def tag_record_id(*, snapshot_id: str, name: str) -> str:
    return f"{snapshot_id}:tag:{name}"


class EngineeringSnapshotMapper:
    @staticmethod
    def to_record(snapshot: EngineeringSnapshot) -> EngineeringSnapshotRecord:
        return EngineeringSnapshotRecord(
            id=snapshot.snapshot_id.value,
            organization_id=snapshot.organization_id.value,
            workspace_id=snapshot.workspace_id.value,
            repository_id=snapshot.repository_id.value,
            assessment_id=snapshot.assessment_id.value,
            assessment_intelligence_id=snapshot.assessment_intelligence_id,
            assessment_revision=snapshot.assessment_revision,
            version=snapshot.version.value,
            status=snapshot.status.value,
            source_artifact_ids_json=list(snapshot.source_artifact_ids),
            technologies_json=[
                EngineeringSnapshotMapper.technology_to_json(item)
                for item in snapshot.technologies
            ],
            components_json=[
                EngineeringSnapshotMapper.component_to_json(item)
                for item in snapshot.components
            ],
            findings_json=[
                EngineeringSnapshotMapper.finding_to_json(item) for item in snapshot.findings
            ],
            recommendations_json=[
                EngineeringSnapshotMapper.recommendation_to_json(item)
                for item in snapshot.recommendations
            ],
            metrics_json=[
                EngineeringSnapshotMapper.metric_to_json(item) for item in snapshot.metrics
            ],
            evidence_json=[
                EngineeringSnapshotMapper.evidence_to_json(item) for item in snapshot.evidence
            ],
            relationships_json=[
                EngineeringSnapshotMapper.relationship_to_json(item)
                for item in snapshot.relationships
            ],
            tags_json=[item.name for item in snapshot.tags],
            created_at=snapshot.audit.created_at.value,
            updated_at=snapshot.audit.updated_at.value,
            published_at=snapshot.published_at,
            optimistic_version=snapshot._version,
        )

    @staticmethod
    def apply_to_record(
        snapshot: EngineeringSnapshot,
        record: EngineeringSnapshotRecord,
    ) -> None:
        record.organization_id = snapshot.organization_id.value
        record.workspace_id = snapshot.workspace_id.value
        record.repository_id = snapshot.repository_id.value
        record.assessment_id = snapshot.assessment_id.value
        record.assessment_intelligence_id = snapshot.assessment_intelligence_id
        record.assessment_revision = snapshot.assessment_revision
        record.version = snapshot.version.value
        record.status = snapshot.status.value
        record.source_artifact_ids_json = list(snapshot.source_artifact_ids)
        record.technologies_json = [
            EngineeringSnapshotMapper.technology_to_json(item)
            for item in snapshot.technologies
        ]
        record.components_json = [
            EngineeringSnapshotMapper.component_to_json(item) for item in snapshot.components
        ]
        record.findings_json = [
            EngineeringSnapshotMapper.finding_to_json(item) for item in snapshot.findings
        ]
        record.recommendations_json = [
            EngineeringSnapshotMapper.recommendation_to_json(item)
            for item in snapshot.recommendations
        ]
        record.metrics_json = [
            EngineeringSnapshotMapper.metric_to_json(item) for item in snapshot.metrics
        ]
        record.evidence_json = [
            EngineeringSnapshotMapper.evidence_to_json(item) for item in snapshot.evidence
        ]
        record.relationships_json = [
            EngineeringSnapshotMapper.relationship_to_json(item)
            for item in snapshot.relationships
        ]
        record.tags_json = [item.name for item in snapshot.tags]
        record.created_at = snapshot.audit.created_at.value
        record.updated_at = snapshot.audit.updated_at.value
        record.published_at = snapshot.published_at
        record.optimistic_version = snapshot._version

    @staticmethod
    def to_domain(record: EngineeringSnapshotRecord) -> EngineeringSnapshot:
        return EngineeringSnapshot(
            snapshot_id=EngineeringSnapshotId(record.id),
            organization_id=OrganizationId(record.organization_id),
            workspace_id=WorkspaceId(record.workspace_id),
            repository_id=RepositoryId(record.repository_id),
            assessment_id=AssessmentId(record.assessment_id),
            assessment_intelligence_id=record.assessment_intelligence_id,
            assessment_revision=record.assessment_revision,
            version=EngineeringSnapshotVersion(record.version),
            status=EngineeringSnapshotStatus(record.status),
            source_artifact_ids=tuple(record.source_artifact_ids_json or []),
            technologies=tuple(
                EngineeringSnapshotMapper.technology_from_json(item)
                for item in (record.technologies_json or [])
            ),
            components=tuple(
                EngineeringSnapshotMapper.component_from_json(item)
                for item in (record.components_json or [])
            ),
            findings=tuple(
                EngineeringSnapshotMapper.finding_from_json(item)
                for item in (record.findings_json or [])
            ),
            recommendations=tuple(
                EngineeringSnapshotMapper.recommendation_from_json(item)
                for item in (record.recommendations_json or [])
            ),
            metrics=tuple(
                EngineeringSnapshotMapper.metric_from_json(item)
                for item in (record.metrics_json or [])
            ),
            evidence=tuple(
                EngineeringSnapshotMapper.evidence_from_json(item)
                for item in (record.evidence_json or [])
            ),
            relationships=tuple(
                EngineeringSnapshotMapper.relationship_from_json(item)
                for item in (record.relationships_json or [])
            ),
            tags=tuple(EngineeringTag(name=name) for name in (record.tags_json or [])),
            audit=audit_from_record(
                created_at=record.created_at,
                updated_at=record.updated_at,
            ),
            published_at=(
                ensure_utc(record.published_at) if record.published_at is not None else None
            ),
            _version=record.optimistic_version,
        )

    @staticmethod
    def technology_to_json(technology: EngineeringTechnology) -> dict[str, Any]:
        return {
            "technology_id": technology.technology_id.value,
            "canonical_key": technology.canonical_key,
            "display_name": technology.display_name,
            "category": technology.category.value,
            "metadata": dict(technology.metadata or {}),
        }

    @staticmethod
    def technology_from_json(data: dict[str, Any]) -> EngineeringTechnology:
        return EngineeringTechnology(
            technology_id=EngineeringTechnologyId(data["technology_id"]),
            canonical_key=data["canonical_key"],
            display_name=data["display_name"],
            category=EngineeringCategory(data["category"]),
            metadata=dict(data.get("metadata") or {}),
        )

    @staticmethod
    def component_to_json(component: EngineeringComponent) -> dict[str, Any]:
        return {
            "component_id": component.component_id.value,
            "name": component.name,
            "kind": component.kind,
            "path_reference": component.path_reference,
            "metadata": dict(component.metadata or {}),
        }

    @staticmethod
    def component_from_json(data: dict[str, Any]) -> EngineeringComponent:
        return EngineeringComponent(
            component_id=EngineeringComponentId(data["component_id"]),
            name=data["name"],
            kind=data.get("kind", "component"),
            path_reference=data.get("path_reference"),
            metadata=dict(data.get("metadata") or {}),
        )

    @staticmethod
    def finding_to_json(finding: EngineeringFinding) -> dict[str, Any]:
        return {
            "finding_id": finding.finding_id.value,
            "source_finding_id": finding.source_finding_id,
            "category": finding.category.value,
            "severity": finding.severity.value,
            "title": finding.title,
            "summary": finding.summary,
            "rule_id": finding.rule_id,
            "confidence": finding.confidence,
            "evidence_ids": list(finding.evidence_ids),
            "technology_keys": list(finding.technology_keys),
            "component_ids": list(finding.component_ids),
            "metadata": dict(finding.metadata or {}),
        }

    @staticmethod
    def finding_from_json(data: dict[str, Any]) -> EngineeringFinding:
        return EngineeringFinding(
            finding_id=EngineeringFindingId(data["finding_id"]),
            source_finding_id=data["source_finding_id"],
            category=EngineeringCategory(data["category"]),
            severity=EngineeringSeverity(data["severity"]),
            title=data["title"],
            summary=data["summary"],
            rule_id=data["rule_id"],
            confidence=float(data["confidence"]),
            evidence_ids=tuple(data.get("evidence_ids", [])),
            technology_keys=tuple(data.get("technology_keys", [])),
            component_ids=tuple(data.get("component_ids", [])),
            metadata=dict(data.get("metadata") or {}),
        )

    @staticmethod
    def recommendation_to_json(recommendation: EngineeringRecommendation) -> dict[str, Any]:
        return {
            "recommendation_id": recommendation.recommendation_id.value,
            "source_recommendation_id": recommendation.source_recommendation_id,
            "category": recommendation.category.value,
            "severity": recommendation.severity.value,
            "title": recommendation.title,
            "rationale": recommendation.rationale,
            "priority": recommendation.priority,
            "related_finding_ids": list(recommendation.related_finding_ids),
            "metadata": dict(recommendation.metadata or {}),
        }

    @staticmethod
    def recommendation_from_json(data: dict[str, Any]) -> EngineeringRecommendation:
        return EngineeringRecommendation(
            recommendation_id=EngineeringRecommendationId(data["recommendation_id"]),
            source_recommendation_id=data["source_recommendation_id"],
            category=EngineeringCategory(data["category"]),
            severity=EngineeringSeverity(data["severity"]),
            title=data["title"],
            rationale=data["rationale"],
            priority=data["priority"],
            related_finding_ids=tuple(data.get("related_finding_ids", [])),
            metadata=dict(data.get("metadata") or {}),
        )

    @staticmethod
    def metric_to_json(metric: EngineeringMetric) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "metric_id": metric.metric_id.value,
            "name": metric.name,
            "kind": metric.kind.value,
            "value": metric.value,
            "metadata": dict(metric.metadata or {}),
        }
        if metric.unit is not None:
            payload["unit"] = metric.unit
        return payload

    @staticmethod
    def metric_from_json(data: dict[str, Any]) -> EngineeringMetric:
        return EngineeringMetric(
            metric_id=EngineeringMetricId(data["metric_id"]),
            name=data["name"],
            kind=EngineeringMetricKind(data["kind"]),
            value=data["value"],
            unit=data.get("unit"),
            metadata=dict(data.get("metadata") or {}),
        )

    @staticmethod
    def evidence_to_json(evidence: EngineeringEvidence) -> dict[str, Any]:
        return {
            "evidence_id": evidence.evidence_id.value,
            "kind": evidence.kind.value,
            "reference": evidence.reference,
            "line_start": evidence.line_start,
            "line_end": evidence.line_end,
            "symbol": evidence.symbol,
            "source_artifact_id": evidence.source_artifact_id,
            "checksum": evidence.checksum,
            "metadata": dict(evidence.metadata or {}),
        }

    @staticmethod
    def evidence_from_json(data: dict[str, Any]) -> EngineeringEvidence:
        return EngineeringEvidence(
            evidence_id=EngineeringEvidenceId(data["evidence_id"]),
            kind=EvidenceKind(data["kind"]),
            reference=data["reference"],
            line_start=data.get("line_start"),
            line_end=data.get("line_end"),
            symbol=data.get("symbol"),
            source_artifact_id=data.get("source_artifact_id"),
            checksum=data.get("checksum"),
            metadata=dict(data.get("metadata") or {}),
        )

    @staticmethod
    def relationship_to_json(relationship: EngineeringRelationship) -> dict[str, Any]:
        return {
            "relationship_id": relationship.relationship_id.value,
            "relationship_type": relationship.relationship_type.value,
            "source_type": relationship.source_type,
            "source_id": relationship.source_id,
            "target_type": relationship.target_type,
            "target_id": relationship.target_id,
            "metadata": dict(relationship.metadata or {}),
        }

    @staticmethod
    def relationship_from_json(data: dict[str, Any]) -> EngineeringRelationship:
        return EngineeringRelationship(
            relationship_id=EngineeringRelationshipId(data["relationship_id"]),
            relationship_type=EngineeringRelationshipType(data["relationship_type"]),
            source_type=data["source_type"],
            source_id=data["source_id"],
            target_type=data["target_type"],
            target_id=data["target_id"],
            metadata=dict(data.get("metadata") or {}),
        )

    @staticmethod
    def technology_to_record(
        technology: EngineeringTechnology,
        *,
        snapshot_id: str,
        assessment_id: str,
    ) -> EngineeringTechnologyRecord:
        return EngineeringTechnologyRecord(
            id=technology.technology_id.value,
            snapshot_id=snapshot_id,
            assessment_id=assessment_id,
            canonical_key=technology.canonical_key,
            display_name=technology.display_name,
            category=technology.category.value,
            metadata_json=dict(technology.metadata or {}),
        )

    @staticmethod
    def finding_to_record(
        finding: EngineeringFinding,
        *,
        snapshot_id: str,
        assessment_id: str,
    ) -> EngineeringFindingRecord:
        return EngineeringFindingRecord(
            id=finding.finding_id.value,
            snapshot_id=snapshot_id,
            assessment_id=assessment_id,
            source_finding_id=finding.source_finding_id,
            category=finding.category.value,
            severity=finding.severity.value,
            title=finding.title,
            summary=finding.summary,
            rule_id=finding.rule_id,
            confidence=finding.confidence,
            payload_json={
                "evidence_ids": list(finding.evidence_ids),
                "technology_keys": list(finding.technology_keys),
                "component_ids": list(finding.component_ids),
                "metadata": dict(finding.metadata or {}),
            },
        )

    @staticmethod
    def recommendation_to_record(
        recommendation: EngineeringRecommendation,
        *,
        snapshot_id: str,
        assessment_id: str,
    ) -> EngineeringRecommendationRecord:
        return EngineeringRecommendationRecord(
            id=recommendation.recommendation_id.value,
            snapshot_id=snapshot_id,
            assessment_id=assessment_id,
            source_recommendation_id=recommendation.source_recommendation_id,
            category=recommendation.category.value,
            severity=recommendation.severity.value,
            title=recommendation.title,
            rationale=recommendation.rationale,
            priority=recommendation.priority,
            related_finding_ids_json=list(recommendation.related_finding_ids),
            metadata_json=dict(recommendation.metadata or {}),
        )

    @staticmethod
    def metric_to_record(
        metric: EngineeringMetric,
        *,
        snapshot_id: str,
        assessment_id: str,
    ) -> EngineeringMetricRecord:
        return EngineeringMetricRecord(
            id=metric.metric_id.value,
            snapshot_id=snapshot_id,
            assessment_id=assessment_id,
            name=metric.name,
            kind=metric.kind.value,
            value=metric.value,
            unit=metric.unit,
            metadata_json=dict(metric.metadata or {}),
        )

    @staticmethod
    def evidence_to_record(
        evidence: EngineeringEvidence,
        *,
        snapshot_id: str,
        assessment_id: str,
    ) -> EngineeringEvidenceRecord:
        return EngineeringEvidenceRecord(
            id=evidence.evidence_id.value,
            snapshot_id=snapshot_id,
            assessment_id=assessment_id,
            kind=evidence.kind.value,
            reference=evidence.reference,
            line_start=evidence.line_start,
            line_end=evidence.line_end,
            symbol=evidence.symbol,
            source_artifact_id=evidence.source_artifact_id,
            checksum=evidence.checksum,
            metadata_json=dict(evidence.metadata or {}),
        )

    @staticmethod
    def relationship_to_record(
        relationship: EngineeringRelationship,
        *,
        snapshot_id: str,
        assessment_id: str,
    ) -> EngineeringRelationshipRecord:
        return EngineeringRelationshipRecord(
            id=relationship.relationship_id.value,
            snapshot_id=snapshot_id,
            assessment_id=assessment_id,
            relationship_type=relationship.relationship_type.value,
            source_type=relationship.source_type,
            source_id=relationship.source_id,
            target_type=relationship.target_type,
            target_id=relationship.target_id,
            metadata_json=dict(relationship.metadata or {}),
        )

    @staticmethod
    def tag_to_record(
        tag: EngineeringTag,
        *,
        snapshot_id: str,
        assessment_id: str,
    ) -> EngineeringTagRecord:
        return EngineeringTagRecord(
            id=tag_record_id(snapshot_id=snapshot_id, name=tag.name),
            snapshot_id=snapshot_id,
            assessment_id=assessment_id,
            name=tag.name,
        )

    @staticmethod
    def component_to_record(
        component: EngineeringComponent,
        *,
        snapshot_id: str,
        assessment_id: str,
    ) -> EngineeringComponentRecord:
        return EngineeringComponentRecord(
            id=component.component_id.value,
            snapshot_id=snapshot_id,
            assessment_id=assessment_id,
            name=component.name,
            kind=component.kind,
            path_reference=component.path_reference,
            metadata_json=dict(component.metadata or {}),
        )

    @staticmethod
    def projection_records(
        snapshot: EngineeringSnapshot,
    ) -> tuple[
        tuple[EngineeringTechnologyRecord, ...],
        tuple[EngineeringFindingRecord, ...],
        tuple[EngineeringRecommendationRecord, ...],
        tuple[EngineeringMetricRecord, ...],
        tuple[EngineeringEvidenceRecord, ...],
        tuple[EngineeringRelationshipRecord, ...],
        tuple[EngineeringTagRecord, ...],
        tuple[EngineeringComponentRecord, ...],
    ]:
        snapshot_id = snapshot.snapshot_id.value
        assessment_id = snapshot.assessment_id.value
        return (
            tuple(
                EngineeringSnapshotMapper.technology_to_record(
                    item, snapshot_id=snapshot_id, assessment_id=assessment_id
                )
                for item in snapshot.technologies
            ),
            tuple(
                EngineeringSnapshotMapper.finding_to_record(
                    item, snapshot_id=snapshot_id, assessment_id=assessment_id
                )
                for item in snapshot.findings
            ),
            tuple(
                EngineeringSnapshotMapper.recommendation_to_record(
                    item, snapshot_id=snapshot_id, assessment_id=assessment_id
                )
                for item in snapshot.recommendations
            ),
            tuple(
                EngineeringSnapshotMapper.metric_to_record(
                    item, snapshot_id=snapshot_id, assessment_id=assessment_id
                )
                for item in snapshot.metrics
            ),
            tuple(
                EngineeringSnapshotMapper.evidence_to_record(
                    item, snapshot_id=snapshot_id, assessment_id=assessment_id
                )
                for item in snapshot.evidence
            ),
            tuple(
                EngineeringSnapshotMapper.relationship_to_record(
                    item, snapshot_id=snapshot_id, assessment_id=assessment_id
                )
                for item in snapshot.relationships
            ),
            tuple(
                EngineeringSnapshotMapper.tag_to_record(
                    item, snapshot_id=snapshot_id, assessment_id=assessment_id
                )
                for item in snapshot.tags
            ),
            tuple(
                EngineeringSnapshotMapper.component_to_record(
                    item, snapshot_id=snapshot_id, assessment_id=assessment_id
                )
                for item in snapshot.components
            ),
        )
