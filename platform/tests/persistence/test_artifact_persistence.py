"""Artifact metadata persistence round-trip tests."""

from __future__ import annotations

import hashlib

from codestrata_platform.domain.artifact import (
    ArtifactFormat,
    ArtifactStatus,
    ArtifactType,
    AssessmentArtifact,
)
from codestrata_platform.domain.assessment import Assessment
from codestrata_platform.domain.organization import Organization
from codestrata_platform.domain.repository import Repository, RepositoryProvider
from codestrata_platform.domain.workspace import Workspace
from codestrata_platform.infrastructure.persistence.repositories import (
    SqlAlchemyAssessmentArtifactRepository,
    SqlAlchemyAssessmentRepository,
    SqlAlchemyOrganizationRepository,
    SqlAlchemyRepositoryRepository,
    SqlAlchemyWorkspaceRepository,
)


def _checksum(content: bytes = b'{"ok":true}') -> str:
    return hashlib.sha256(content).hexdigest()


def test_artifact_persistence_round_trip(
    org_repo: SqlAlchemyOrganizationRepository,
    workspace_repo: SqlAlchemyWorkspaceRepository,
    repository_repo: SqlAlchemyRepositoryRepository,
    assessment_repo: SqlAlchemyAssessmentRepository,
    artifact_repo: SqlAlchemyAssessmentArtifactRepository,
) -> None:
    org = Organization.create(name="Org")
    org_repo.save(org)
    workspace = Workspace.create(organization_id=org.organization_id, name="WS")
    workspace_repo.save(workspace)
    repository = Repository.register(
        workspace_id=workspace.workspace_id,
        organization_id=org.organization_id,
        display_name="App",
        provider=RepositoryProvider.GITHUB,
        repository_url="https://github.com/acme/app",
    )
    repository_repo.save(repository)
    assessment = Assessment.create(
        repository_id=repository.repository_id,
        workspace_id=workspace.workspace_id,
        engine_version="1.0.0",
        assessment_version="0.1.0",
    )
    assessment_repo.save(assessment)

    artifact = AssessmentArtifact.register(
        organization_id=org.organization_id,
        workspace_id=workspace.workspace_id,
        repository_id=repository.repository_id,
        assessment_id=assessment.assessment_id,
        engine_assessment_id="engine-assessment:1",
        artifact_type=ArtifactType.REPORT_JSON,
        format=ArtifactFormat.JSON,
        schema_version="1.0",
        checksum=_checksum(),
        size_bytes=11,
    )
    artifact.attach_content(storage_reference="artifacts/a/report.json")
    artifact.complete()
    artifact_repo.save(artifact)

    loaded = artifact_repo.get(artifact.artifact_id)
    assert loaded is not None
    assert loaded.status is ArtifactStatus.COMPLETED
    assert loaded.checksum.value == _checksum()
    assert loaded.storage_reference is not None
    assert loaded.storage_reference.value == "artifacts/a/report.json"

    listed = artifact_repo.list_by_assessment(assessment.assessment_id)
    assert len(listed) == 1
    found = artifact_repo.find_by_assessment_type_checksum(
        assessment_id=assessment.assessment_id,
        artifact_type=ArtifactType.REPORT_JSON,
        checksum=loaded.checksum,
    )
    assert found is not None
    assert found.artifact_id == artifact.artifact_id


def test_artifact_persistence_survives_engine_restart(
    session_factory,
    sqlite_engine,
) -> None:
    _ = sqlite_engine
    session = session_factory()
    try:
        org_repo = SqlAlchemyOrganizationRepository(session)
        workspace_repo = SqlAlchemyWorkspaceRepository(session)
        repository_repo = SqlAlchemyRepositoryRepository(session)
        assessment_repo = SqlAlchemyAssessmentRepository(session)
        artifact_repo = SqlAlchemyAssessmentArtifactRepository(session)

        org = Organization.create(name="Org")
        org_repo.save(org)
        workspace = Workspace.create(organization_id=org.organization_id, name="WS")
        workspace_repo.save(workspace)
        repository = Repository.register(
            workspace_id=workspace.workspace_id,
            organization_id=org.organization_id,
            display_name="App",
            provider=RepositoryProvider.GITHUB,
            repository_url="https://github.com/acme/app",
        )
        repository_repo.save(repository)
        assessment = Assessment.create(
            repository_id=repository.repository_id,
            workspace_id=workspace.workspace_id,
            engine_version="1.0.0",
            assessment_version="0.1.0",
        )
        assessment_repo.save(assessment)
        artifact = AssessmentArtifact.register(
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            repository_id=repository.repository_id,
            assessment_id=assessment.assessment_id,
            engine_assessment_id="engine-assessment:persist",
            artifact_type=ArtifactType.ASSESSMENT_SUMMARY,
            format=ArtifactFormat.JSON,
            schema_version="1.0",
            checksum=_checksum(b"persist"),
            size_bytes=7,
        )
        artifact_repo.save(artifact)
        artifact_id = artifact.artifact_id
        assessment_id = assessment.assessment_id
        session.commit()
    finally:
        session.close()

    session2 = session_factory()
    try:
        artifact_repo2 = SqlAlchemyAssessmentArtifactRepository(session2)
        loaded = artifact_repo2.get(artifact_id)
        assert loaded is not None
        assert loaded.engine_assessment_id == "engine-assessment:persist"
        assert artifact_repo2.latest_version_for_type(
            assessment_id=assessment_id,
            artifact_type=ArtifactType.ASSESSMENT_SUMMARY,
        ) == 1
    finally:
        session2.close()
