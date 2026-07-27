"""Domain tests for AssessmentArtifact aggregate."""

from __future__ import annotations

import hashlib

import pytest

from codestrata_platform.domain.artifact import (
    ArtifactChecksum,
    ArtifactFormat,
    ArtifactMetadata,
    ArtifactStatus,
    ArtifactType,
    AssessmentArtifact,
)
from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.errors import InvalidStateTransitionError, InvalidValueError
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId


def _checksum(content: bytes = b'{"ok":true}') -> str:
    return hashlib.sha256(content).hexdigest()


def _register(**overrides: object) -> AssessmentArtifact:
    params: dict[str, object] = {
        "organization_id": OrganizationId("org:1"),
        "workspace_id": WorkspaceId("workspace:1"),
        "repository_id": RepositoryId("repo:1"),
        "assessment_id": AssessmentId("assessment:1"),
        "engine_assessment_id": "engine-assessment:1",
        "artifact_type": ArtifactType.ASSESSMENT_SUMMARY,
        "format": ArtifactFormat.JSON,
        "schema_version": "1.0",
        "checksum": _checksum(),
        "size_bytes": 11,
    }
    params.update(overrides)
    return AssessmentArtifact.register(**params)  # type: ignore[arg-type]


def test_artifact_lifecycle_happy_path() -> None:
    artifact = _register()
    assert artifact.status is ArtifactStatus.REGISTERED
    artifact.begin_upload()
    assert artifact.status is ArtifactStatus.UPLOADING
    artifact.attach_content(storage_reference="artifacts/assessment:1/summary")
    artifact.complete()
    assert artifact.status is ArtifactStatus.COMPLETED
    assert artifact.completed_at is not None
    with pytest.raises(InvalidStateTransitionError):
        artifact.complete()


def test_artifact_fail_and_reject() -> None:
    artifact = _register()
    artifact.fail(reason="upload interrupted")
    assert artifact.status is ArtifactStatus.FAILED
    with pytest.raises(InvalidStateTransitionError):
        artifact.complete()

    other = _register(checksum=_checksum(b"other"))
    other.reject(reason="policy")
    assert other.status is ArtifactStatus.REJECTED
    with pytest.raises(InvalidStateTransitionError):
        other.reject(reason="again")


def test_invalid_checksum_size_format_and_secret_metadata() -> None:
    with pytest.raises(InvalidValueError):
        ArtifactChecksum("not-a-checksum")
    with pytest.raises(InvalidValueError):
        _register(size_bytes=0)
    with pytest.raises(InvalidValueError):
        _register(artifact_type=ArtifactType.REPORT_HTML, format=ArtifactFormat.JSON)
    with pytest.raises(InvalidValueError):
        ArtifactMetadata({"api_token": "secret-value"})


def test_invalid_transitions() -> None:
    failed = _register(checksum=_checksum(b"fail"))
    failed.fail(reason="boom")
    with pytest.raises(InvalidStateTransitionError):
        failed.begin_upload()
    completed = _register(checksum=_checksum(b"done"))
    completed.attach_content(storage_reference="artifacts/x")
    completed.complete()
    with pytest.raises(InvalidStateTransitionError):
        completed.attach_content(storage_reference="artifacts/y")
    with pytest.raises(InvalidStateTransitionError):
        completed.fail(reason="too late")
