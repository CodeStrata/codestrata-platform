"""Application and storage tests for assessment artifacts."""

from __future__ import annotations

import hashlib

import pytest

from codestrata_platform.application.artifact import DefaultArtifactService
from codestrata_platform.application.assessment import DefaultAssessmentService
from codestrata_platform.application.commands.artifact import (
    CompleteArtifactCommand,
    RegisterArtifactCommand,
    UploadArtifactCommand,
)
from codestrata_platform.application.commands.assessment import RegisterAssessmentCommand
from codestrata_platform.application.commands.organization import CreateOrganizationCommand
from codestrata_platform.application.commands.repository import RegisterRepositoryCommand
from codestrata_platform.application.commands.workspace import CreateWorkspaceCommand
from codestrata_platform.application.common.errors import PayloadTooLargeError, ValidationError
from codestrata_platform.application.organization import DefaultOrganizationService
from codestrata_platform.application.repository import DefaultRepositoryService
from codestrata_platform.application.workspace import DefaultWorkspaceService
from codestrata_platform.domain.artifact import ArtifactFormat, ArtifactStatus, ArtifactType
from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.repository import RepositoryProvider, RepositoryVisibility
from codestrata_platform.infrastructure.memory import (
    InMemoryArtifactRepository,
    InMemoryAssessmentRepository,
    InMemoryOrganizationRepository,
    InMemoryRepositoryRepository,
    InMemoryWorkspaceRepository,
)
from codestrata_platform.infrastructure.storage import (
    FileSystemArtifactStorage,
    InMemoryArtifactStorage,
)


def _checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _services(*, max_bytes: int = 10_485_760):
    orgs = InMemoryOrganizationRepository()
    workspaces = InMemoryWorkspaceRepository()
    repositories = InMemoryRepositoryRepository()
    assessments = InMemoryAssessmentRepository()
    artifacts = InMemoryArtifactRepository()
    storage = InMemoryArtifactStorage()
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
        max_artifact_bytes=max_bytes,
    )
    return (
        org_service,
        workspace_service,
        repository_service,
        assessment_service,
        artifact_service,
        storage,
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


def test_idempotent_duplicate_and_new_version_on_checksum_change() -> None:
    org_s, ws_s, repo_s, assess_s, artifact_s, _storage = _services()
    assessment = _seed_assessment(org_s, ws_s, repo_s, assess_s)
    content = b'{"summary":true}'
    checksum = _checksum(content)
    first = artifact_s.register_artifact(
        RegisterArtifactCommand(
            assessment_id=assessment.assessment_id,
            engine_assessment_id="engine-assessment:1",
            artifact_type=ArtifactType.ASSESSMENT_SUMMARY,
            format=ArtifactFormat.JSON,
            schema_version="1.0",
            checksum=checksum,
            size_bytes=len(content),
        )
    )
    second = artifact_s.register_artifact(
        RegisterArtifactCommand(
            assessment_id=assessment.assessment_id,
            engine_assessment_id="engine-assessment:1",
            artifact_type=ArtifactType.ASSESSMENT_SUMMARY,
            format=ArtifactFormat.JSON,
            schema_version="1.0",
            checksum=checksum,
            size_bytes=len(content),
        )
    )
    assert first.created is True
    assert second.created is False
    assert second.artifact_id == first.artifact_id

    other = b'{"summary":false}'
    third = artifact_s.register_artifact(
        RegisterArtifactCommand(
            assessment_id=assessment.assessment_id,
            engine_assessment_id="engine-assessment:1",
            artifact_type=ArtifactType.ASSESSMENT_SUMMARY,
            format=ArtifactFormat.JSON,
            schema_version="1.0",
            checksum=_checksum(other),
            size_bytes=len(other),
        )
    )
    assert third.created is True
    assert third.version == 2
    assert third.artifact_id != first.artifact_id


def test_upload_complete_and_payload_limits() -> None:
    org_s, ws_s, repo_s, assess_s, artifact_s, storage = _services(max_bytes=32)
    assessment = _seed_assessment(org_s, ws_s, repo_s, assess_s)
    content = b'{"ok":true}'
    registered = artifact_s.register_artifact(
        RegisterArtifactCommand(
            assessment_id=assessment.assessment_id,
            engine_assessment_id="engine-assessment:1",
            artifact_type=ArtifactType.REPORT_JSON,
            format=ArtifactFormat.JSON,
            schema_version="1.0",
            checksum=_checksum(content),
            size_bytes=len(content),
        )
    )
    uploaded = artifact_s.upload_artifact(
        UploadArtifactCommand(
            artifact_id=registered.artifact_id,
            content=content,
            declared_checksum=_checksum(content),
        )
    )
    assert uploaded.status is ArtifactStatus.UPLOADING
    assert storage.exists(
        __import__(
            "codestrata_platform.domain.artifact",
            fromlist=["ArtifactReference"],
        ).ArtifactReference(uploaded.storage_key)
    )
    completed = artifact_s.complete_artifact(
        CompleteArtifactCommand(artifact_id=registered.artifact_id)
    )
    assert completed.status is ArtifactStatus.COMPLETED

    with pytest.raises(PayloadTooLargeError):
        artifact_s.register_artifact(
            RegisterArtifactCommand(
                assessment_id=assessment.assessment_id,
                engine_assessment_id="engine-assessment:1",
                artifact_type=ArtifactType.FINDINGS,
                format=ArtifactFormat.JSON,
                schema_version="1.0",
                checksum=_checksum(b"x" * 64),
                size_bytes=64,
            )
        )


def test_checksum_mismatch_on_upload() -> None:
    org_s, ws_s, repo_s, assess_s, artifact_s, _storage = _services()
    assessment = _seed_assessment(org_s, ws_s, repo_s, assess_s)
    content = b'{"ok":true}'
    registered = artifact_s.register_artifact(
        RegisterArtifactCommand(
            assessment_id=assessment.assessment_id,
            engine_assessment_id="engine-assessment:1",
            artifact_type=ArtifactType.ASSESSMENT_SUMMARY,
            format=ArtifactFormat.JSON,
            schema_version="1.0",
            checksum=_checksum(content),
            size_bytes=len(content),
        )
    )
    with pytest.raises(ValidationError) as error:
        artifact_s.upload_artifact(
            UploadArtifactCommand(
                artifact_id=registered.artifact_id,
                content=content,
                declared_checksum=_checksum(b"tampered"),
            )
        )
    assert error.value.reason_code == "checksum_mismatch"


def test_filesystem_storage_atomic_and_path_traversal(tmp_path) -> None:
    storage = FileSystemArtifactStorage(tmp_path)
    reference = storage.put(
        key="artifacts/a/report.json",
        content=b'{"a":1}',
        content_type="application/json",
    )
    assert storage.exists(reference)
    assert storage.get(reference) == b'{"a":1}'
    with pytest.raises(InvalidValueError):
        storage.put(
            key="../escape.json",
            content=b"nope",
            content_type="application/json",
        )
