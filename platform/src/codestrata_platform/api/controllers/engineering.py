"""Engineering intelligence query and build controllers."""

from __future__ import annotations

from fastapi import APIRouter, Query, status
from pydantic import BaseModel, ConfigDict, Field

from codestrata_platform.api.configuration.dependencies import ServicesDep
from codestrata_platform.application.commands.engineering import BuildEngineeringSnapshotCommand
from codestrata_platform.application.queries.engineering import (
    GetEngineeringSnapshotQuery,
    GetFindingInventoryQuery,
    GetMetricInventoryQuery,
    GetRecommendationInventoryQuery,
    GetTechnologyInventoryQuery,
    ListEngineeringSnapshotsQuery,
)
from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.engineering.enums import EngineeringSeverity
from codestrata_platform.domain.engineering.ids import EngineeringSnapshotId
from codestrata_platform.domain.intelligence.ids import AssessmentIntelligenceId

router = APIRouter(prefix="/engineering", tags=["Engineering Intelligence"])


class BuildSnapshotRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assessment_id: str = Field(min_length=1, max_length=160)
    intelligence_id: str | None = Field(default=None, max_length=160)
    publish: bool = True


class SnapshotSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot_id: str
    assessment_id: str
    assessment_intelligence_id: str
    assessment_revision: int
    version: int
    status: str
    technology_count: int
    finding_count: int
    recommendation_count: int
    metric_count: int
    relationship_count: int


class SnapshotDetailsResponse(SnapshotSummaryResponse):
    organization_id: str
    workspace_id: str
    repository_id: str
    source_artifact_ids: list[str]
    created: bool | None = None
    idempotent: bool | None = None


@router.post(
    "/snapshots",
    response_model=SnapshotDetailsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Build canonical engineering snapshot from assessment intelligence",
)
def build_snapshot(
    body: BuildSnapshotRequest,
    services: ServicesDep,
) -> SnapshotDetailsResponse:
    result = services.engineering.build_engineering_snapshot(
        BuildEngineeringSnapshotCommand(
            assessment_id=AssessmentId(body.assessment_id.strip()),
            intelligence_id=(
                AssessmentIntelligenceId(body.intelligence_id.strip())
                if body.intelligence_id
                else None
            ),
            publish=body.publish,
        )
    )
    details = result.snapshot
    return SnapshotDetailsResponse(
        snapshot_id=details.snapshot_id.value,
        assessment_id=details.assessment_id,
        assessment_intelligence_id=details.assessment_intelligence_id,
        assessment_revision=details.assessment_revision,
        version=details.version,
        status=details.status.value,
        technology_count=details.technology_count,
        finding_count=details.finding_count,
        recommendation_count=details.recommendation_count,
        metric_count=details.metric_count,
        relationship_count=details.relationship_count,
        organization_id=details.organization_id,
        workspace_id=details.workspace_id,
        repository_id=details.repository_id,
        source_artifact_ids=list(details.source_artifact_ids),
        created=result.created,
        idempotent=result.idempotent,
    )


@router.get("/snapshots", response_model=list[SnapshotSummaryResponse])
def list_snapshots(
    services: ServicesDep,
    assessment_id: str = Query(..., min_length=1),
) -> list[SnapshotSummaryResponse]:
    items = services.engineering.list_engineering_snapshots(
        ListEngineeringSnapshotsQuery(assessment_id=AssessmentId(assessment_id.strip()))
    )
    return [
        SnapshotSummaryResponse(
            snapshot_id=item.snapshot_id.value,
            assessment_id=item.assessment_id,
            assessment_intelligence_id=item.assessment_intelligence_id,
            assessment_revision=item.assessment_revision,
            version=item.version,
            status=item.status.value,
            technology_count=item.technology_count,
            finding_count=item.finding_count,
            recommendation_count=item.recommendation_count,
            metric_count=item.metric_count,
            relationship_count=item.relationship_count,
        )
        for item in items
    ]


@router.get("/snapshots/{snapshot_id}", response_model=SnapshotDetailsResponse)
def get_snapshot(snapshot_id: str, services: ServicesDep) -> SnapshotDetailsResponse:
    details = services.engineering.get_engineering_snapshot(
        GetEngineeringSnapshotQuery(snapshot_id=EngineeringSnapshotId(snapshot_id.strip()))
    )
    return SnapshotDetailsResponse(
        snapshot_id=details.snapshot_id.value,
        assessment_id=details.assessment_id,
        assessment_intelligence_id=details.assessment_intelligence_id,
        assessment_revision=details.assessment_revision,
        version=details.version,
        status=details.status.value,
        technology_count=details.technology_count,
        finding_count=details.finding_count,
        recommendation_count=details.recommendation_count,
        metric_count=details.metric_count,
        relationship_count=details.relationship_count,
        organization_id=details.organization_id,
        workspace_id=details.workspace_id,
        repository_id=details.repository_id,
        source_artifact_ids=list(details.source_artifact_ids),
    )


@router.get("/technologies")
def list_technologies(
    services: ServicesDep,
    assessment_id: str | None = Query(default=None),
    snapshot_id: str | None = Query(default=None),
) -> list[dict[str, object]]:
    items = services.engineering.get_technology_inventory(
        GetTechnologyInventoryQuery(
            snapshot_id=EngineeringSnapshotId(snapshot_id.strip()) if snapshot_id else None,
            assessment_id=AssessmentId(assessment_id.strip()) if assessment_id else None,
        )
    )
    return [
        {
            "technology_id": item.technology_id,
            "canonical_key": item.canonical_key,
            "display_name": item.display_name,
            "category": item.category.value,
        }
        for item in items
    ]


@router.get("/findings")
def list_findings(
    services: ServicesDep,
    assessment_id: str | None = Query(default=None),
    snapshot_id: str | None = Query(default=None),
    severity: str | None = Query(default=None),
) -> list[dict[str, object]]:
    severity_filter = (
        EngineeringSeverity(severity.strip().lower()) if severity else None
    )
    items = services.engineering.get_finding_inventory(
        GetFindingInventoryQuery(
            snapshot_id=EngineeringSnapshotId(snapshot_id.strip()) if snapshot_id else None,
            assessment_id=AssessmentId(assessment_id.strip()) if assessment_id else None,
            severity=severity_filter,
        )
    )
    return [
        {
            "finding_id": item.finding_id,
            "source_finding_id": item.source_finding_id,
            "category": item.category.value,
            "severity": item.severity.value,
            "title": item.title,
            "rule_id": item.rule_id,
            "confidence": item.confidence,
        }
        for item in items
    ]


@router.get("/recommendations")
def list_recommendations(
    services: ServicesDep,
    assessment_id: str | None = Query(default=None),
    snapshot_id: str | None = Query(default=None),
) -> list[dict[str, object]]:
    items = services.engineering.get_recommendation_inventory(
        GetRecommendationInventoryQuery(
            snapshot_id=EngineeringSnapshotId(snapshot_id.strip()) if snapshot_id else None,
            assessment_id=AssessmentId(assessment_id.strip()) if assessment_id else None,
        )
    )
    return [
        {
            "recommendation_id": item.recommendation_id,
            "source_recommendation_id": item.source_recommendation_id,
            "category": item.category.value,
            "severity": item.severity.value,
            "title": item.title,
            "priority": item.priority,
            "related_finding_ids": list(item.related_finding_ids),
        }
        for item in items
    ]


@router.get("/metrics")
def list_metrics(
    services: ServicesDep,
    assessment_id: str | None = Query(default=None),
    snapshot_id: str | None = Query(default=None),
) -> list[dict[str, object]]:
    items = services.engineering.get_metric_inventory(
        GetMetricInventoryQuery(
            snapshot_id=EngineeringSnapshotId(snapshot_id.strip()) if snapshot_id else None,
            assessment_id=AssessmentId(assessment_id.strip()) if assessment_id else None,
        )
    )
    return [
        {
            "metric_id": item.metric_id,
            "name": item.name,
            "kind": item.kind.value,
            "value": item.value,
            "unit": item.unit,
        }
        for item in items
    ]
