"""Application tests for DefaultAssessmentIntelligenceService."""

from __future__ import annotations

import hashlib
import json

import pytest

from codestrata_platform.application.artifact import DefaultArtifactService
from codestrata_platform.application.assessment import DefaultAssessmentService
from codestrata_platform.application.commands.artifact import (
    CompleteArtifactCommand,
    RegisterArtifactCommand,
    UploadArtifactCommand,
)
from codestrata_platform.application.commands.assessment import RegisterAssessmentCommand
from codestrata_platform.application.commands.intelligence import (
    ProcessAssessmentIntelligenceCommand,
)
from codestrata_platform.application.commands.organization import CreateOrganizationCommand
from codestrata_platform.application.commands.repository import RegisterRepositoryCommand
from codestrata_platform.application.commands.workspace import CreateWorkspaceCommand
from codestrata_platform.application.common.errors import ValidationError
from codestrata_platform.application.intelligence import DefaultAssessmentIntelligenceService
from codestrata_platform.application.organization import DefaultOrganizationService
from codestrata_platform.application.queries.intelligence import (
    GetFindingQuery,
    ListAssessmentFindingsQuery,
    ListAssessmentMetricsQuery,
    ListAssessmentRecommendationsQuery,
)
from codestrata_platform.application.repository import DefaultRepositoryService
from codestrata_platform.application.workspace import DefaultWorkspaceService
from codestrata_platform.domain.artifact import ArtifactFormat, ArtifactType
from codestrata_platform.domain.intelligence import (
    FindingId,
    IntelligenceIngestionStatus,
)
from codestrata_platform.domain.repository import RepositoryProvider, RepositoryVisibility
from codestrata_platform.infrastructure.memory import (
    InMemoryArtifactRepository,
    InMemoryAssessmentIntelligenceRepository,
    InMemoryAssessmentRepository,
    InMemoryFindingRepository,
    InMemoryMetricRepository,
    InMemoryOrganizationRepository,
    InMemoryRecommendationRepository,
    InMemoryRepositoryRepository,
    InMemoryWorkspaceRepository,
)
from codestrata_platform.infrastructure.storage import InMemoryArtifactStorage


def _checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _services():
    orgs = InMemoryOrganizationRepository()
    workspaces = InMemoryWorkspaceRepository()
    repositories = InMemoryRepositoryRepository()
    assessments = InMemoryAssessmentRepository()
    artifacts = InMemoryArtifactRepository()
    storage = InMemoryArtifactStorage()
    intelligence = InMemoryAssessmentIntelligenceRepository()
    findings = InMemoryFindingRepository()
    metrics = InMemoryMetricRepository()
    recommendations = InMemoryRecommendationRepository()

    org_service = DefaultOrganizationService(organizations=orgs)
    workspace_service = DefaultWorkspaceService(workspaces=workspaces, organizations=orgs)
    repository_service = DefaultRepositoryService(
        repositories=repositories,
        workspaces=workspaces,
        organizations=orgs,
    )
    assessment_service = DefaultAssessmentService(
        assessments=assessments,
        repositories=repositories,
        workspaces=workspaces,
    )
    artifact_service = DefaultArtifactService(
        artifacts=artifacts,
        storage=storage,
        assessments=assessments,
        repositories=repositories,
    )
    intelligence_service = DefaultAssessmentIntelligenceService(
        intelligence=intelligence,
        findings=findings,
        metrics=metrics,
        recommendations=recommendations,
        artifacts=artifacts,
        storage=storage,
        assessments=assessments,
        repositories=repositories,
    )
    return (
        org_service,
        workspace_service,
        repository_service,
        assessment_service,
        artifact_service,
        intelligence_service,
        intelligence,
    )


def _seed_assessment(org_service, workspace_service, repository_service, assessment_service):
    org = org_service.create_organization(CreateOrganizationCommand(name="Acme"))
    workspace = workspace_service.create_workspace(
        CreateWorkspaceCommand(organization_id=org.organization_id, name="Default")
    )
    repository = repository_service.register_repository(
        RegisterRepositoryCommand(
            workspace_id=workspace.workspace_id,
            organization_id=org.organization_id,
            display_name="App",
            provider=RepositoryProvider.GITHUB,
            repository_url="https://github.com/acme/app",
            default_branch="main",
            visibility=RepositoryVisibility.PRIVATE,
        )
    )
    assessment = assessment_service.create_assessment(
        RegisterAssessmentCommand(
            repository_id=repository.repository_id,
            workspace_id=workspace.workspace_id,
            engine_version="1.0.0",
            assessment_version="0.1.0",
        )
    )
    return assessment


def _register_complete_artifact(
    artifact_service,
    *,
    assessment,
    artifact_type: ArtifactType,
    payload: object,
) -> str:
    content = json.dumps(payload).encode("utf-8")
    registered = artifact_service.register_artifact(
        RegisterArtifactCommand(
            assessment_id=assessment.assessment_id,
            engine_assessment_id="engine-assessment:1",
            artifact_type=artifact_type,
            format=ArtifactFormat.JSON,
            schema_version="1.0",
            checksum=_checksum(content),
            size_bytes=len(content),
        )
    )
    artifact_service.upload_artifact(
        UploadArtifactCommand(
            artifact_id=registered.artifact_id,
            assessment_id=assessment.assessment_id,
            content=content,
            declared_checksum=_checksum(content),
        )
    )
    artifact_service.complete_artifact(
        CompleteArtifactCommand(
            artifact_id=registered.artifact_id,
            assessment_id=assessment.assessment_id,
        )
    )
    return registered.artifact_id.value


def test_process_intelligence_idempotent_and_revision_on_change() -> None:
    (
        org_s,
        ws_s,
        repo_s,
        assess_s,
        artifact_s,
        intelligence_s,
        intelligence_store,
    ) = _services()
    assessment = _seed_assessment(org_s, ws_s, repo_s, assess_s)
    findings_payload = {
        "findings": [
            {
                "finding_id": "finding:1",
                "rule_id": "rule.security.token",
                "title": "Hard-coded token",
                "summary": "Token found in source.",
                "category": "security",
                "severity": "high",
                "confidence": 0.9,
                "evidence": [{"path": "src/auth.py", "line_start": 10}],
            }
        ]
    }
    summary_payload = {
        "metrics": {"security.findings.high": 1},
    }
    findings_id = _register_complete_artifact(
        artifact_s,
        assessment=assessment,
        artifact_type=ArtifactType.FINDINGS,
        payload=findings_payload,
    )
    summary_id = _register_complete_artifact(
        artifact_s,
        assessment=assessment,
        artifact_type=ArtifactType.ASSESSMENT_SUMMARY,
        payload=summary_payload,
    )

    first = intelligence_s.process_assessment_intelligence(
        ProcessAssessmentIntelligenceCommand(assessment_id=assessment.assessment_id)
    )
    assert first.created is True
    assert first.idempotent is False
    assert first.intelligence.status is IntelligenceIngestionStatus.COMPLETED
    assert first.intelligence.finding_count == 1
    assert first.intelligence.metric_count == 1

    second = intelligence_s.process_assessment_intelligence(
        ProcessAssessmentIntelligenceCommand(assessment_id=assessment.assessment_id)
    )
    assert second.created is False
    assert second.idempotent is True
    assert second.intelligence.intelligence_id == first.intelligence.intelligence_id

    changed_payload = {
        "findings": [
            {
                "finding_id": "finding:2",
                "rule_id": "rule.security.token",
                "title": "Updated finding",
                "summary": "Changed artifact set.",
                "category": "security",
                "severity": "critical",
            }
        ]
    }
    changed_content = json.dumps(changed_payload).encode("utf-8")
    changed = artifact_s.register_artifact(
        RegisterArtifactCommand(
            assessment_id=assessment.assessment_id,
            engine_assessment_id="engine-assessment:1",
            artifact_type=ArtifactType.FINDINGS,
            format=ArtifactFormat.JSON,
            schema_version="1.0",
            checksum=_checksum(changed_content),
            size_bytes=len(changed_content),
        )
    )
    artifact_s.upload_artifact(
        UploadArtifactCommand(
            artifact_id=changed.artifact_id,
            assessment_id=assessment.assessment_id,
            content=changed_content,
            declared_checksum=_checksum(changed_content),
        )
    )
    artifact_s.complete_artifact(
        CompleteArtifactCommand(
            artifact_id=changed.artifact_id,
            assessment_id=assessment.assessment_id,
        )
    )

    third = intelligence_s.process_assessment_intelligence(
        ProcessAssessmentIntelligenceCommand(
            assessment_id=assessment.assessment_id,
            artifact_ids=(changed.artifact_id.value, summary_id),
        )
    )
    assert third.created is True
    assert third.intelligence.revision == 2
    assert third.intelligence.intelligence_id != first.intelligence.intelligence_id

    revisions = intelligence_store.list_by_assessment(assessment.assessment_id)
    statuses = {item.revision: item.status for item in revisions}
    assert statuses[1] is IntelligenceIngestionStatus.SUPERSEDED
    assert statuses[2] is IntelligenceIngestionStatus.COMPLETED

    listed_findings = intelligence_s.list_assessment_findings(
        ListAssessmentFindingsQuery(assessment_id=assessment.assessment_id)
    )
    assert len(listed_findings) == 1
    assert listed_findings[0].title == "Updated finding"

    listed_metrics = intelligence_s.list_assessment_metrics(
        ListAssessmentMetricsQuery(assessment_id=assessment.assessment_id)
    )
    assert len(listed_metrics) == 1

    finding = intelligence_s.get_finding(
        GetFindingQuery(finding_id=FindingId("finding:2"), assessment_id=assessment.assessment_id)
    )
    assert finding.title == "Updated finding"

    del findings_id


def test_process_intelligence_requires_completed_artifacts() -> None:
    org_s, ws_s, repo_s, assess_s, artifact_s, intelligence_s, _store = _services()
    assessment = _seed_assessment(org_s, ws_s, repo_s, assess_s)
    content = json.dumps({"findings": []}).encode("utf-8")
    registered = artifact_s.register_artifact(
        RegisterArtifactCommand(
            assessment_id=assessment.assessment_id,
            engine_assessment_id="engine-assessment:1",
            artifact_type=ArtifactType.FINDINGS,
            format=ArtifactFormat.JSON,
            schema_version="1.0",
            checksum=_checksum(content),
            size_bytes=len(content),
        )
    )
    with pytest.raises(ValidationError) as error:
        intelligence_s.process_assessment_intelligence(
            ProcessAssessmentIntelligenceCommand(assessment_id=assessment.assessment_id)
        )
    assert error.value.reason_code == "artifact_not_completed"
    del registered


def test_process_intelligence_parse_failure_leaves_failed_record() -> None:
    org_s, ws_s, repo_s, assess_s, artifact_s, intelligence_s, store = _services()
    assessment = _seed_assessment(org_s, ws_s, repo_s, assess_s)
    _register_complete_artifact(
        artifact_s,
        assessment=assessment,
        artifact_type=ArtifactType.FINDINGS,
        payload={"findings": [{"metadata": {"password_hash": "nope"}}]},
    )
    with pytest.raises(ValidationError):
        intelligence_s.process_assessment_intelligence(
            ProcessAssessmentIntelligenceCommand(assessment_id=assessment.assessment_id)
        )
    records = store.list_by_assessment(assessment.assessment_id)
    assert len(records) == 1
    assert records[0].status is IntelligenceIngestionStatus.FAILED
    assert records[0].findings == ()


def test_list_recommendations_from_report_json() -> None:
    org_s, ws_s, repo_s, assess_s, artifact_s, intelligence_s, _store = _services()
    assessment = _seed_assessment(org_s, ws_s, repo_s, assess_s)
    _register_complete_artifact(
        artifact_s,
        assessment=assessment,
        artifact_type=ArtifactType.REPORT_JSON,
        payload={
            "findings": [],
            "recommendations": [
                {
                    "recommendation_id": "rec:1",
                    "title": "Use secret manager",
                    "rationale": "Avoid hard-coded secrets.",
                    "priority": "high",
                    "category": "security",
                    "related_finding_ids": [],
                    "dependencies": [],
                }
            ],
        },
    )
    intelligence_s.process_assessment_intelligence(
        ProcessAssessmentIntelligenceCommand(assessment_id=assessment.assessment_id)
    )
    recommendations = intelligence_s.list_assessment_recommendations(
        ListAssessmentRecommendationsQuery(assessment_id=assessment.assessment_id)
    )
    assert len(recommendations) == 1
    assert recommendations[0].title == "Use secret manager"
