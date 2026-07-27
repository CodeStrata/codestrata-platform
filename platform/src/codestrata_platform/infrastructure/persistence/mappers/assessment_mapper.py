"""Assessment aggregate ↔ AssessmentRecord mapper."""

from __future__ import annotations

from typing import Any

from codestrata_platform.domain.assessment import (
    Assessment,
    AssessmentId,
    AssessmentReference,
    AssessmentStatus,
    AssessmentVersion,
    GeneratedReport,
)
from codestrata_platform.domain.assessment.value_objects import AssessmentMetadata
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.shared.version import PlatformVersion
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.infrastructure.persistence.mappers._helpers import (
    audit_from_record,
    ensure_utc,
)
from codestrata_platform.infrastructure.persistence.models.assessment_record import (
    AssessmentRecord,
)


class AssessmentMapper:
    @staticmethod
    def to_record(assessment: Assessment) -> AssessmentRecord:
        return AssessmentRecord(
            id=assessment.assessment_id.value,
            repository_id=assessment.repository_id.value,
            workspace_id=assessment.workspace_id.value,
            engine_version=str(assessment.engine_version),
            assessment_version=str(assessment.assessment_version),
            status=assessment.status.value,
            started_at=assessment.started_at,
            completed_at=assessment.completed_at,
            generated_reports_json=_serialize_reports(assessment.generated_reports),
            references_json=_serialize_references(assessment.references),
            metadata_json=dict(assessment.metadata.attributes),
            failure_reason=assessment.failure_reason,
            created_at=assessment.audit.created_at.value,
            updated_at=assessment.audit.updated_at.value,
            version=assessment._version,
        )

    @staticmethod
    def apply_to_record(assessment: Assessment, record: AssessmentRecord) -> None:
        record.repository_id = assessment.repository_id.value
        record.workspace_id = assessment.workspace_id.value
        record.engine_version = str(assessment.engine_version)
        record.assessment_version = str(assessment.assessment_version)
        record.status = assessment.status.value
        record.started_at = assessment.started_at
        record.completed_at = assessment.completed_at
        record.generated_reports_json = _serialize_reports(assessment.generated_reports)
        record.references_json = _serialize_references(assessment.references)
        record.metadata_json = dict(assessment.metadata.attributes)
        record.failure_reason = assessment.failure_reason
        record.created_at = assessment.audit.created_at.value
        record.updated_at = assessment.audit.updated_at.value
        record.version = assessment._version

    @staticmethod
    def to_domain(record: AssessmentRecord) -> Assessment:
        return Assessment(
            assessment_id=AssessmentId(record.id),
            repository_id=RepositoryId(record.repository_id),
            workspace_id=WorkspaceId(record.workspace_id),
            engine_version=PlatformVersion(record.engine_version),
            assessment_version=AssessmentVersion(record.assessment_version),
            status=AssessmentStatus(record.status),
            started_at=ensure_utc(record.started_at) if record.started_at else None,
            completed_at=ensure_utc(record.completed_at) if record.completed_at else None,
            generated_reports=_deserialize_reports(record.generated_reports_json or []),
            references=_deserialize_references(record.references_json or []),
            metadata=AssessmentMetadata(dict(record.metadata_json or {})),
            audit=audit_from_record(
                created_at=record.created_at,
                updated_at=record.updated_at,
            ),
            failure_reason=record.failure_reason,
            _version=record.version,
        )


def _serialize_reports(reports: tuple[GeneratedReport, ...]) -> list[dict[str, Any]]:
    return [{"report_type": r.report_type, "location": r.location} for r in reports]


def _deserialize_reports(payload: list[dict[str, Any]]) -> tuple[GeneratedReport, ...]:
    return tuple(
        GeneratedReport(report_type=item["report_type"], location=item["location"])
        for item in payload
    )


def _serialize_references(refs: tuple[AssessmentReference, ...]) -> list[dict[str, Any]]:
    return [{"artifact_uri": r.artifact_uri, "label": r.label} for r in refs]


def _deserialize_references(payload: list[dict[str, Any]]) -> tuple[AssessmentReference, ...]:
    return tuple(
        AssessmentReference(artifact_uri=item["artifact_uri"], label=item.get("label"))
        for item in payload
    )
