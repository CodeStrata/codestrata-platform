"""Engineering snapshot PostgreSQL persistence tests."""

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
from codestrata_platform.application.repository import DefaultRepositoryService
from codestrata_platform.application.workspace import DefaultWorkspaceService
from codestrata_platform.domain.artifact import ArtifactFormat, ArtifactType
from codestrata_platform.domain.engineering import EngineeringSnapshotStatus
from codestrata_platform.domain.repository import RepositoryProvider, RepositoryVisibility
from codestrata_platform.infrastructure.persistence import (
    SqlAlchemyAssessmentArtifactRepository,
    SqlAlchemyAssessmentIntelligenceRepository,
    SqlAlchemyAssessmentRepository,
    SqlAlchemyEngineeringSnapshotRepository,
    SqlAlchemyFindingRepository,
    SqlAlchemyMetricRepository,
    SqlAlchemyOrganizationRepository,
    SqlAlchemyRecommendationRepository,
    SqlAlchemyRepositoryRepository,
    SqlAlchemyWorkspaceRepository,
)
from codestrata_platform.infrastructure.storage import InMemoryArtifactStorage


def _checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _services(session):
    orgs = SqlAlchemyOrganizationRepository(session)
    workspaces = SqlAlchemyWorkspaceRepository(session)
    repositories = SqlAlchemyRepositoryRepository(session)
    assessments = SqlAlchemyAssessmentRepository(session)
    artifacts = SqlAlchemyAssessmentArtifactRepository(session)
    intelligence = SqlAlchemyAssessmentIntelligenceRepository(session)
    findings = SqlAlchemyFindingRepository(session)
    metrics = SqlAlchemyMetricRepository(session)
    recommendations = SqlAlchemyRecommendationRepository(session)
    snapshots = SqlAlchemyEngineeringSnapshotRepository(session)
    storage = InMemoryArtifactStorage()
    return (
        DefaultOrganizationService(organizations=orgs),
        DefaultWorkspaceService(workspaces=workspaces, organizations=orgs),
        DefaultRepositoryService(
            repositories=repositories,
            workspaces=workspaces,
            organizations=orgs,
        ),
        DefaultAssessmentService(
            assessments=assessments,
            repositories=repositories,
            workspaces=workspaces,
        ),
        DefaultArtifactService(
            artifacts=artifacts,
            storage=storage,
            assessments=assessments,
            repositories=repositories,
        ),
        DefaultAssessmentIntelligenceService(
            intelligence=intelligence,
            findings=findings,
            metrics=metrics,
            recommendations=recommendations,
            artifacts=artifacts,
            storage=storage,
            assessments=assessments,
            repositories=repositories,
        ),
        EngineeringNormalizationService(
            snapshots=snapshots,
            intelligence=intelligence,
        ),
        snapshots,
    )


def test_engineering_snapshot_persistence_round_trip(session) -> None:
    org_s, ws_s, repo_s, assess_s, artifact_s, intelligence_s, engineering_s, store = _services(
        session
    )
    org = org_s.create_organization(CreateOrganizationCommand(name="Acme"))
    workspace = ws_s.create_workspace(
        CreateWorkspaceCommand(organization_id=org.organization_id, name="Default")
    )
    repository = repo_s.register_repository(
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
    assessment = assess_s.create_assessment(
        RegisterAssessmentCommand(
            repository_id=repository.repository_id,
            workspace_id=workspace.workspace_id,
            engine_version="1.0.0",
            assessment_version="0.1.0",
        )
    )
    content = json.dumps(
        {
            "findings": [
                {
                    "finding_id": "finding:pg",
                    "rule_id": "rule.kafka.partitioning",
                    "title": "Hot partition",
                    "summary": "Uneven partitions.",
                    "category": "architecture",
                    "severity": "medium",
                    "metadata": {"technology": "Kafka"},
                }
            ]
        }
    ).encode("utf-8")
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
    artifact_s.upload_artifact(
        UploadArtifactCommand(
            artifact_id=registered.artifact_id,
            assessment_id=assessment.assessment_id,
            content=content,
            declared_checksum=_checksum(content),
        )
    )
    artifact_s.complete_artifact(
        CompleteArtifactCommand(
            artifact_id=registered.artifact_id,
            assessment_id=assessment.assessment_id,
        )
    )
    intelligence_s.process_assessment_intelligence(
        ProcessAssessmentIntelligenceCommand(assessment_id=assessment.assessment_id)
    )
    result = engineering_s.build_engineering_snapshot(
        BuildEngineeringSnapshotCommand(assessment_id=assessment.assessment_id)
    )
    session.flush()
    loaded = store.get(result.snapshot.snapshot_id)
    assert loaded is not None
    assert loaded.status is EngineeringSnapshotStatus.PUBLISHED
    assert loaded.findings[0].source_finding_id == "finding:pg"
    assert any(item.canonical_key == "kafka" for item in loaded.technologies)
    latest = store.get_latest_published(assessment.assessment_id)
    assert latest is not None
    assert latest.snapshot_id == loaded.snapshot_id
