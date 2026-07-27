"""Domain tests for Assessment aggregate."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from codestrata_platform.domain.assessment import (
    Assessment,
    AssessmentReference,
    AssessmentStatus,
    AssessmentVersion,
    GeneratedReport,
)
from codestrata_platform.domain.errors import (
    InvalidStateTransitionError,
    InvalidValueError,
)
from codestrata_platform.domain.organization import Organization
from codestrata_platform.domain.repository import Repository, RepositoryProvider
from codestrata_platform.domain.workspace import Workspace


def _registered_repository() -> tuple[Workspace, Repository]:
    org = Organization.create(name="Acme")
    workspace = Workspace.create(organization_id=org.organization_id, name="Default")
    repo = Repository.register(
        workspace_id=workspace.workspace_id,
        organization_id=org.organization_id,
        display_name="app",
        provider=RepositoryProvider.GITHUB,
        repository_url="https://github.com/example/app",
    )
    return workspace, repo


def test_assessment_happy_path() -> None:
    workspace, repo = _registered_repository()
    assessment = Assessment.create(
        repository_id=repo.repository_id,
        workspace_id=workspace.workspace_id,
        engine_version="0.1.0",
        assessment_version="3.0.0",
    )
    assert assessment.status is AssessmentStatus.PENDING
    assessment.start()
    assert assessment.status is AssessmentStatus.RUNNING
    assert assessment.started_at is not None
    assessment.complete(
        generated_reports=(
            GeneratedReport(report_type="html", location="reports/report.html"),
        ),
        references=(
            AssessmentReference(artifact_uri="reports/report.json", label="report"),
        ),
    )
    assert assessment.status is AssessmentStatus.SUCCEEDED
    assert assessment.completed_at is not None
    assert len(assessment.generated_reports) == 1


def test_assessment_fail_from_running() -> None:
    workspace, repo = _registered_repository()
    assessment = Assessment.create(
        repository_id=repo.repository_id,
        workspace_id=workspace.workspace_id,
        engine_version="0.1.0",
        assessment_version=AssessmentVersion("3.0.0"),
    )
    assessment.start()
    assessment.fail(reason="Engine timed out")
    assert assessment.status is AssessmentStatus.FAILED
    assert assessment.failure_reason == "Engine timed out"
    with pytest.raises(InvalidStateTransitionError):
        assessment.complete()


def test_assessment_invalid_transitions() -> None:
    workspace, repo = _registered_repository()
    assessment = Assessment.create(
        repository_id=repo.repository_id,
        workspace_id=workspace.workspace_id,
        engine_version="0.1.0",
        assessment_version="3.0.0",
    )
    with pytest.raises(InvalidStateTransitionError):
        assessment.complete()
    assessment.start()
    with pytest.raises(InvalidStateTransitionError):
        assessment.start()
    with pytest.raises(InvalidValueError):
        assessment.fail(reason=" ")


def test_assessment_completion_cannot_precede_start() -> None:
    workspace, repo = _registered_repository()
    assessment = Assessment.create(
        repository_id=repo.repository_id,
        workspace_id=workspace.workspace_id,
        engine_version="0.1.0",
        assessment_version="3.0.0",
    )
    started = datetime(2026, 7, 26, 12, 0, tzinfo=UTC)
    assessment.start(at=started)
    with pytest.raises(InvalidValueError):
        assessment.complete(at=started - timedelta(minutes=1))
