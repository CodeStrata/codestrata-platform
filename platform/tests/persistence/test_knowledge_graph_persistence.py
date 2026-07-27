"""PostgreSQL persistence tests for Engineering Knowledge Graph."""

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
from codestrata_platform.application.knowledge_graph.commands import BuildKnowledgeGraphCommand
from codestrata_platform.application.knowledge_graph.services import (
    EngineeringGraphProjectionService,
)
from codestrata_platform.application.organization import DefaultOrganizationService
from codestrata_platform.application.repository import DefaultRepositoryService
from codestrata_platform.application.workspace import DefaultWorkspaceService
from codestrata_platform.domain.artifact import ArtifactFormat, ArtifactType
from codestrata_platform.domain.knowledge_graph.identifiers import KnowledgeGraphId
from codestrata_platform.domain.knowledge_graph.lifecycle import GraphStatus
from codestrata_platform.domain.repository import RepositoryProvider, RepositoryVisibility
from codestrata_platform.infrastructure.persistence import (
    SqlAlchemyAssessmentArtifactRepository,
    SqlAlchemyAssessmentIntelligenceRepository,
    SqlAlchemyAssessmentRepository,
    SqlAlchemyEngineeringSnapshotRepository,
    SqlAlchemyFindingRepository,
    SqlAlchemyKnowledgeGraphRepository,
    SqlAlchemyMetricRepository,
    SqlAlchemyOrganizationRepository,
    SqlAlchemyRecommendationRepository,
    SqlAlchemyRepositoryRepository,
    SqlAlchemyWorkspaceRepository,
)
from codestrata_platform.infrastructure.persistence.models.knowledge_graph_records import (
    EngineeringKnowledgeGraphRecord,
)
from codestrata_platform.infrastructure.storage import InMemoryArtifactStorage


def _checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _stack(session):
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
    graphs = SqlAlchemyKnowledgeGraphRepository(session)
    storage = InMemoryArtifactStorage()
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
        "graphs": EngineeringGraphProjectionService(
            graphs=graphs,
            snapshots=snapshots,
            queries=graphs,
        ),
        "graph_store": graphs,
        "snapshot_store": snapshots,
    }


def _publish_snapshot(stack, *, name: str = "App"):
    org = stack["org"].create_organization(CreateOrganizationCommand(name="Acme"))
    workspace = stack["ws"].create_workspace(
        CreateWorkspaceCommand(organization_id=org.organization_id, name="Default")
    )
    repository = stack["repo"].register_repository(
        RegisterRepositoryCommand(
            workspace_id=workspace.workspace_id,
            organization_id=org.organization_id,
            display_name=name,
            provider=RepositoryProvider.GITHUB,
            repository_url=f"https://github.com/acme/{name.lower()}",
            default_branch="main",
            visibility=RepositoryVisibility.PRIVATE,
        )
    )
    assessment = stack["assess"].create_assessment(
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
                    "finding_id": f"finding:{name}",
                    "rule_id": "rule.docker.hardening",
                    "title": "Privileged container",
                    "summary": "Container runs privileged.",
                    "category": "security",
                    "severity": "critical",
                    "confidence": 0.95,
                    "metadata": {"technology": "Docker"},
                    "evidence": [{"path": "deploy/compose.yml", "line_start": 4}],
                }
            ]
        }
    ).encode("utf-8")
    registered = stack["artifact"].register_artifact(
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
    stack["artifact"].upload_artifact(
        UploadArtifactCommand(
            artifact_id=registered.artifact_id,
            content=content,
            declared_checksum=_checksum(content),
        )
    )
    stack["artifact"].complete_artifact(
        CompleteArtifactCommand(artifact_id=registered.artifact_id)
    )
    stack["intelligence"].process_assessment_intelligence(
        ProcessAssessmentIntelligenceCommand(assessment_id=assessment.assessment_id)
    )
    result = stack["engineering"].build_engineering_snapshot(
        BuildEngineeringSnapshotCommand(assessment_id=assessment.assessment_id)
    )
    return repository, result.snapshot


def test_knowledge_graph_round_trip(session) -> None:
    stack = _stack(session)
    repository, snapshot = _publish_snapshot(stack)
    session.flush()

    result = stack["graphs"].build_knowledge_graph(
        BuildKnowledgeGraphCommand(snapshot_id=snapshot.snapshot_id)
    )
    session.flush()
    assert result.created is True

    loaded = stack["graph_store"].get(KnowledgeGraphId(result.graph.graph_id))
    assert loaded is not None
    assert loaded.status is GraphStatus.COMPLETED
    assert loaded.repository_id == repository.repository_id
    assert len(loaded.nodes) >= 5
    assert len(loaded.edges) >= 4

    record = session.get(EngineeringKnowledgeGraphRecord, result.graph.graph_id)
    assert record is not None
    assert record.projection_key == result.graph.projection_key

    again = stack["graphs"].build_knowledge_graph(
        BuildKnowledgeGraphCommand(snapshot_id=snapshot.snapshot_id)
    )
    assert again.idempotent is True


def test_new_snapshot_supersedes_prior_graph(session) -> None:
    stack = _stack(session)
    repository, first = _publish_snapshot(stack, name="One")
    session.flush()
    first_result = stack["graphs"].build_knowledge_graph(
        BuildKnowledgeGraphCommand(snapshot_id=first.snapshot_id)
    )
    session.flush()

    content = json.dumps(
        {
            "findings": [
                {
                    "finding_id": "finding:two",
                    "rule_id": "rule.k8s.rbac",
                    "title": "Broad RBAC",
                    "summary": "Cluster admin binding.",
                    "category": "security",
                    "severity": "high",
                    "confidence": 0.9,
                    "metadata": {"technology": "Kubernetes"},
                }
            ]
        }
    ).encode("utf-8")
    assessments = stack["assess"]
    assessment = assessments.create_assessment(
        RegisterAssessmentCommand(
            repository_id=repository.repository_id,
            workspace_id=repository.workspace_id,
            engine_version="1.0.1",
            assessment_version="0.2.0",
        )
    )
    registered = stack["artifact"].register_artifact(
        RegisterArtifactCommand(
            assessment_id=assessment.assessment_id,
            engine_assessment_id="engine-assessment:2",
            artifact_type=ArtifactType.FINDINGS,
            format=ArtifactFormat.JSON,
            schema_version="1.0",
            checksum=_checksum(content),
            size_bytes=len(content),
        )
    )
    stack["artifact"].upload_artifact(
        UploadArtifactCommand(
            artifact_id=registered.artifact_id,
            content=content,
            declared_checksum=_checksum(content),
        )
    )
    stack["artifact"].complete_artifact(
        CompleteArtifactCommand(artifact_id=registered.artifact_id)
    )
    stack["intelligence"].process_assessment_intelligence(
        ProcessAssessmentIntelligenceCommand(assessment_id=assessment.assessment_id)
    )
    second = stack["engineering"].build_engineering_snapshot(
        BuildEngineeringSnapshotCommand(assessment_id=assessment.assessment_id)
    ).snapshot
    session.flush()

    second_result = stack["graphs"].build_knowledge_graph(
        BuildKnowledgeGraphCommand(snapshot_id=second.snapshot_id)
    )
    session.flush()

    prior = stack["graph_store"].get(KnowledgeGraphId(first_result.graph.graph_id))
    assert prior is not None
    assert prior.status is GraphStatus.SUPERSEDED
    assert second_result.graph.graph_version == 2
    latest = stack["graph_store"].get_latest_completed(repository.repository_id)
    assert latest is not None
    assert latest.graph_id.value == second_result.graph.graph_id
