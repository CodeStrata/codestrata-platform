"""Application tests for EngineeringNormalizationService."""

from __future__ import annotations

import hashlib
import json

from codestrata_platform.application.artifact import DefaultArtifactService
from codestrata_platform.application.assessment import DefaultAssessmentService
from codestrata_platform.application.commands.artifact import (
    CompleteArtifactCommand,
    RegisterArtifactCommand,
    UploadArtifactCommand,
)
from codestrata_platform.application.commands.assessment import RegisterAssessmentCommand
from codestrata_platform.application.commands.engineering import BuildEngineeringSnapshotCommand
from codestrata_platform.application.commands.intelligence import (
    ProcessAssessmentIntelligenceCommand,
)
from codestrata_platform.application.commands.organization import CreateOrganizationCommand
from codestrata_platform.application.commands.repository import RegisterRepositoryCommand
from codestrata_platform.application.commands.workspace import CreateWorkspaceCommand
from codestrata_platform.application.engineering import EngineeringNormalizationService
from codestrata_platform.application.intelligence import DefaultAssessmentIntelligenceService
from codestrata_platform.application.organization import DefaultOrganizationService
from codestrata_platform.application.queries.engineering import (
    GetFindingInventoryQuery,
    GetRecommendationInventoryQuery,
    GetTechnologyInventoryQuery,
    ListEngineeringSnapshotsQuery,
)
from codestrata_platform.application.repository import DefaultRepositoryService
from codestrata_platform.application.workspace import DefaultWorkspaceService
from codestrata_platform.domain.artifact import ArtifactFormat, ArtifactType
from codestrata_platform.domain.engineering import EngineeringSnapshotStatus
from codestrata_platform.domain.repository import RepositoryProvider, RepositoryVisibility
from codestrata_platform.infrastructure.memory import (
    InMemoryArtifactRepository,
    InMemoryAssessmentIntelligenceRepository,
    InMemoryAssessmentRepository,
    InMemoryEngineeringSnapshotRepository,
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


def _stack():
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
    snapshots = InMemoryEngineeringSnapshotRepository()
    return {
        "org": DefaultOrganizationService(organizations=orgs),
        "ws": DefaultWorkspaceService(workspaces=workspaces, organizations=orgs),
        "repo": DefaultRepositoryService(
            repositories=repositories,
            workspaces=workspaces,
            organizations=orgs,
        ),
        "assess": DefaultAssessmentService(
            assessments=assessments,
            repositories=repositories,
            workspaces=workspaces,
        ),
        "artifact": DefaultArtifactService(
            artifacts=artifacts,
            storage=storage,
            assessments=assessments,
            repositories=repositories,
        ),
        "intelligence": DefaultAssessmentIntelligenceService(
            intelligence=intelligence,
            findings=findings,
            metrics=metrics,
            recommendations=recommendations,
            artifacts=artifacts,
            storage=storage,
            assessments=assessments,
            repositories=repositories,
        ),
        "engineering": EngineeringNormalizationService(
            snapshots=snapshots,
            intelligence=intelligence,
        ),
        "snapshots": snapshots,
    }


def _seed(stack):
    org = stack["org"].create_organization(CreateOrganizationCommand(name="Acme"))
    workspace = stack["ws"].create_workspace(
        CreateWorkspaceCommand(organization_id=org.organization_id, name="Default")
    )
    repository = stack["repo"].register_repository(
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
    return stack["assess"].create_assessment(
        RegisterAssessmentCommand(
            repository_id=repository.repository_id,
            workspace_id=workspace.workspace_id,
            engine_version="1.0.0",
            assessment_version="0.1.0",
        )
    )


def _complete(stack, assessment, artifact_type: ArtifactType, payload: object) -> None:
    content = json.dumps(payload).encode("utf-8")
    registered = stack["artifact"].register_artifact(
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
    stack["artifact"].upload_artifact(
        UploadArtifactCommand(
            artifact_id=registered.artifact_id,
            assessment_id=assessment.assessment_id,
            content=content,
            declared_checksum=_checksum(content),
        )
    )
    stack["artifact"].complete_artifact(
        CompleteArtifactCommand(
            artifact_id=registered.artifact_id,
            assessment_id=assessment.assessment_id,
        )
    )


def test_intelligence_to_engineering_snapshot_flow() -> None:
    stack = _stack()
    assessment = _seed(stack)
    _complete(
        stack,
        assessment,
        ArtifactType.FINDINGS,
        {
            "findings": [
                {
                    "finding_id": "finding:1",
                    "rule_id": "rule.spring.security",
                    "title": "Hard-coded token",
                    "summary": "Token found.",
                    "category": "security",
                    "severity": "high",
                    "confidence": 0.9,
                    "affected_component": "Spring Boot",
                    "evidence": [{"path": "src/Auth.java", "line_start": 10}],
                    "metadata": {"technology": "PostgreSQL"},
                }
            ]
        },
    )
    _complete(
        stack,
        assessment,
        ArtifactType.ASSESSMENT_SUMMARY,
        {"metrics": {"security.findings.high": 1}},
    )
    _complete(
        stack,
        assessment,
        ArtifactType.REPORT_JSON,
        {
            "recommendations": [
                {
                    "recommendation_id": "rec:1",
                    "title": "Use secret manager",
                    "rationale": "Remove hard-coded secrets.",
                    "priority": "high",
                    "category": "security",
                    "related_finding_ids": ["finding:1"],
                    "dependencies": [],
                }
            ]
        },
    )
    stack["intelligence"].process_assessment_intelligence(
        ProcessAssessmentIntelligenceCommand(assessment_id=assessment.assessment_id)
    )
    first = stack["engineering"].build_engineering_snapshot(
        BuildEngineeringSnapshotCommand(assessment_id=assessment.assessment_id)
    )
    assert first.created is True
    assert first.snapshot.status is EngineeringSnapshotStatus.PUBLISHED
    assert first.snapshot.finding_count == 1
    assert first.snapshot.recommendation_count == 1
    assert first.snapshot.metric_count == 1
    assert first.snapshot.technology_count >= 1

    second = stack["engineering"].build_engineering_snapshot(
        BuildEngineeringSnapshotCommand(assessment_id=assessment.assessment_id)
    )
    assert second.idempotent is True
    assert second.snapshot.snapshot_id == first.snapshot.snapshot_id

    technologies = stack["engineering"].get_technology_inventory(
        GetTechnologyInventoryQuery(assessment_id=assessment.assessment_id)
    )
    keys = {item.canonical_key for item in technologies}
    assert "spring-boot" in keys
    assert "postgresql" in keys

    findings = stack["engineering"].get_finding_inventory(
        GetFindingInventoryQuery(assessment_id=assessment.assessment_id)
    )
    assert findings[0].severity.value == "high"
    assert findings[0].category.value == "security"

    recommendations = stack["engineering"].get_recommendation_inventory(
        GetRecommendationInventoryQuery(assessment_id=assessment.assessment_id)
    )
    assert recommendations[0].related_finding_ids == ("finding:1",)

    listed = stack["engineering"].list_engineering_snapshots(
        ListEngineeringSnapshotsQuery(assessment_id=assessment.assessment_id)
    )
    assert len(listed) == 1
