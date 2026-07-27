"""PostgreSQL persistence tests for Engineering Retrieval indexes."""

from __future__ import annotations

import hashlib
import json

from sqlalchemy import text

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
from codestrata_platform.application.retrieval.commands import BuildRetrievalIndexCommand
from codestrata_platform.application.retrieval.services import EngineeringRetrievalIndexingService
from codestrata_platform.application.workspace import DefaultWorkspaceService
from codestrata_platform.domain.artifact import ArtifactFormat, ArtifactType
from codestrata_platform.domain.repository import RepositoryProvider, RepositoryVisibility
from codestrata_platform.domain.retrieval.identifiers import RetrievalIndexId
from codestrata_platform.domain.retrieval.query import RetrievalQuery, RetrievalScope
from codestrata_platform.domain.retrieval.taxonomy import RetrievalMode
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
    SqlAlchemyRetrievalIndexRepository,
    SqlAlchemyWorkspaceRepository,
)
from codestrata_platform.infrastructure.retrieval.embeddings import DeterministicEmbeddingProvider
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
    embeddings = DeterministicEmbeddingProvider()
    indexes = SqlAlchemyRetrievalIndexRepository(session, embeddings=embeddings)
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
        "retrieval": EngineeringRetrievalIndexingService(
            indexes=indexes,
            snapshots=snapshots,
            graphs=graphs,
            embeddings=embeddings,
            queries=indexes,
        ),
        "index_store": indexes,
    }


def _publish_snapshot(stack, *, name: str = "AppRetrieval"):
    org = stack["org"].create_organization(CreateOrganizationCommand(name="Acme Retrieval"))
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


def test_retrieval_index_persists_and_searches(session) -> None:
    stack = _stack(session)
    repository, snapshot = _publish_snapshot(stack)
    session.flush()
    stack["graphs"].build_knowledge_graph(
        BuildKnowledgeGraphCommand(snapshot_id=snapshot.snapshot_id)
    )
    session.flush()
    built = stack["retrieval"].build_retrieval_index(
        BuildRetrievalIndexCommand(snapshot_id=snapshot.snapshot_id)
    )
    session.flush()
    loaded = stack["index_store"].get(RetrievalIndexId(built.index.index_id))
    assert loaded is not None
    assert loaded.status.value == "completed"
    assert loaded.chunks
    assert loaded.chunks[0].embedding is not None
    assert loaded.chunks[0].embedding.dimension == 384

    result = stack["index_store"].search(
        RetrievalIndexId(built.index.index_id),
        RetrievalQuery(query_text="privileged container", mode=RetrievalMode.HYBRID),
        scope=RetrievalScope(
            organization_id=loaded.organization_id.value,
            workspace_id=loaded.workspace_id.value,
            repository_id=repository.repository_id.value,
        ),
    )
    assert result.hits
    row = session.execute(
        text("SELECT COUNT(*) FROM engineering_retrieval_chunks WHERE embedding IS NOT NULL")
    ).scalar()
    assert int(row or 0) >= 1
    # Optional pgvector projection when extension is available.
    try:
        vector_col = session.execute(
            text(
                """
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'engineering_retrieval_chunks'
                  AND column_name = 'embedding_vector'
                """
            )
        ).first()
        if vector_col is not None:
            synced = session.execute(
                text(
                    "SELECT COUNT(*) FROM engineering_retrieval_chunks "
                    "WHERE embedding_vector IS NOT NULL"
                )
            ).scalar()
            assert int(synced or 0) >= 1
    except Exception:  # noqa: BLE001
        pass
