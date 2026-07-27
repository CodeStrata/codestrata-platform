"""Assessment intelligence PostgreSQL persistence tests."""

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
from codestrata_platform.application.commands.intelligence import (
    ProcessAssessmentIntelligenceCommand,
)
from codestrata_platform.application.commands.organization import CreateOrganizationCommand
from codestrata_platform.application.commands.repository import RegisterRepositoryCommand
from codestrata_platform.application.commands.workspace import CreateWorkspaceCommand
from codestrata_platform.application.intelligence import DefaultAssessmentIntelligenceService
from codestrata_platform.application.organization import DefaultOrganizationService
from codestrata_platform.application.queries.intelligence import ListAssessmentFindingsQuery
from codestrata_platform.application.repository import DefaultRepositoryService
from codestrata_platform.application.workspace import DefaultWorkspaceService
from codestrata_platform.domain.artifact import ArtifactFormat, ArtifactType
from codestrata_platform.domain.intelligence import IntelligenceIngestionStatus
from codestrata_platform.domain.repository import RepositoryProvider, RepositoryVisibility
from codestrata_platform.infrastructure.persistence import (
    SqlAlchemyAssessmentArtifactRepository,
    SqlAlchemyAssessmentIntelligenceRepository,
    SqlAlchemyAssessmentRepository,
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
        intelligence,
        findings,
        storage,
    )


def _seed(org_s, ws_s, repo_s, assess_s):
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
    return assess_s.create_assessment(
        RegisterAssessmentCommand(
            repository_id=repository.repository_id,
            workspace_id=workspace.workspace_id,
            engine_version="1.0.0",
            assessment_version="0.1.0",
        )
    )


def _complete_artifact(
    artifact_s,
    *,
    assessment,
    artifact_type: ArtifactType,
    payload: object,
) -> str:
    content = json.dumps(payload).encode("utf-8")
    registered = artifact_s.register_artifact(
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
    artifact_s.upload_artifact(
        UploadArtifactCommand(
            artifact_id=registered.artifact_id,
            content=content,
            declared_checksum=_checksum(content),
        )
    )
    artifact_s.complete_artifact(CompleteArtifactCommand(artifact_id=registered.artifact_id))
    return registered.artifact_id.value


def test_intelligence_round_trip_and_idempotency(session) -> None:
    (
        org_s,
        ws_s,
        repo_s,
        assess_s,
        artifact_s,
        intelligence_s,
        store,
        findings,
        _storage,
    ) = _services(session)
    assessment = _seed(org_s, ws_s, repo_s, assess_s)
    _complete_artifact(
        artifact_s,
        assessment=assessment,
        artifact_type=ArtifactType.FINDINGS,
        payload={
            "findings": [
                {
                    "finding_id": "finding:1",
                    "rule_id": "rule.security.token",
                    "title": "Hard-coded token",
                    "summary": "Token found in source.",
                    "category": "security",
                    "severity": "high",
                    "confidence": 0.9,
                    "evidence": [{"path": "src/auth.py", "line_start": 10, "line_end": 12}],
                    "metadata": {"pack": "security.core"},
                }
            ]
        },
    )
    _complete_artifact(
        artifact_s,
        assessment=assessment,
        artifact_type=ArtifactType.ASSESSMENT_SUMMARY,
        payload={"metrics": {"security.findings.high": 1}},
    )
    _complete_artifact(
        artifact_s,
        assessment=assessment,
        artifact_type=ArtifactType.REPORT_JSON,
        payload={
            "recommendations": [
                {
                    "recommendation_id": "rec:1",
                    "title": "Use secret manager",
                    "rationale": "Avoid hard-coded secrets.",
                    "priority": "high",
                    "category": "security",
                    "related_finding_ids": ["finding:1"],
                    "dependencies": [],
                }
            ]
        },
    )

    first = intelligence_s.process_assessment_intelligence(
        ProcessAssessmentIntelligenceCommand(assessment_id=assessment.assessment_id)
    )
    session.flush()
    assert first.created is True
    assert first.intelligence.status is IntelligenceIngestionStatus.COMPLETED
    assert first.intelligence.finding_count == 1
    assert first.intelligence.metric_count == 1
    assert first.intelligence.recommendation_count == 1

    loaded = store.get(first.intelligence.intelligence_id)
    assert loaded is not None
    assert loaded.findings[0].title == "Hard-coded token"
    assert loaded.findings[0].evidence_references[0].path_reference == "src/auth.py"
    assert loaded.metrics[0].name.value == "assessment.security.findings.high"
    assert len(findings.list_by_assessment(assessment.assessment_id)) == 1

    second = intelligence_s.process_assessment_intelligence(
        ProcessAssessmentIntelligenceCommand(assessment_id=assessment.assessment_id)
    )
    assert second.idempotent is True
    assert second.intelligence.intelligence_id == first.intelligence.intelligence_id
    assert len(store.list_by_assessment(assessment.assessment_id)) == 1


def test_intelligence_survives_session_restart(session_factory, postgres_engine) -> None:
    _ = postgres_engine
    session = session_factory()
    try:
        org_s, ws_s, repo_s, assess_s, artifact_s, intelligence_s, store, _findings, _storage = (
            _services(session)
        )
        assessment = _seed(org_s, ws_s, repo_s, assess_s)
        _complete_artifact(
            artifact_s,
            assessment=assessment,
            artifact_type=ArtifactType.FINDINGS,
            payload={
                "findings": [
                    {
                        "finding_id": "finding:persist",
                        "rule_id": "rule.x",
                        "title": "Persisted",
                        "summary": "Round trip.",
                        "category": "architecture",
                        "severity": "medium",
                    }
                ]
            },
        )
        result = intelligence_s.process_assessment_intelligence(
            ProcessAssessmentIntelligenceCommand(assessment_id=assessment.assessment_id)
        )
        intelligence_id = result.intelligence.intelligence_id
        assessment_id = assessment.assessment_id
        session.commit()
    finally:
        session.close()

    restarted = session_factory()
    try:
        intelligence = SqlAlchemyAssessmentIntelligenceRepository(restarted)
        findings = SqlAlchemyFindingRepository(restarted)
        loaded = intelligence.get(intelligence_id)
        assert loaded is not None
        assert loaded.status is IntelligenceIngestionStatus.COMPLETED
        assert loaded.findings[0].finding_id.value == "finding:persist"
        projected = findings.list_by_assessment(assessment_id)
        assert len(projected) == 1
        assert projected[0].title == "Persisted"
    finally:
        restarted.close()


def test_parser_version_reprocessing_creates_revision(session) -> None:
    (
        org_s,
        ws_s,
        repo_s,
        assess_s,
        artifact_s,
        intelligence_s,
        store,
        _findings,
        _storage,
    ) = _services(session)
    assessment = _seed(org_s, ws_s, repo_s, assess_s)
    _complete_artifact(
        artifact_s,
        assessment=assessment,
        artifact_type=ArtifactType.FINDINGS,
        payload={
            "findings": [
                {
                    "finding_id": "finding:rev",
                    "rule_id": "rule.x",
                    "title": "First",
                    "summary": "v1",
                    "category": "security",
                    "severity": "low",
                }
            ]
        },
    )
    first = intelligence_s.process_assessment_intelligence(
        ProcessAssessmentIntelligenceCommand(
            assessment_id=assessment.assessment_id,
            parser_version="1.0.0",
        )
    )
    second = intelligence_s.process_assessment_intelligence(
        ProcessAssessmentIntelligenceCommand(
            assessment_id=assessment.assessment_id,
            parser_version="1.1.0",
        )
    )
    assert second.created is True
    assert second.intelligence.revision == 2
    revisions = store.list_by_assessment(assessment.assessment_id)
    assert len(revisions) == 2
    statuses = {item.revision: item.status for item in revisions}
    assert statuses[1] is IntelligenceIngestionStatus.SUPERSEDED
    assert statuses[2] is IntelligenceIngestionStatus.COMPLETED
    listed = intelligence_s.list_assessment_findings(
        ListAssessmentFindingsQuery(assessment_id=assessment.assessment_id)
    )
    assert len(listed) == 1
    del first
