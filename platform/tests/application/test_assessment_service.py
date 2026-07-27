"""Assessment application service tests."""

from __future__ import annotations

import pytest

from codestrata_platform.application.assessment import DefaultAssessmentService
from codestrata_platform.application.commands.assessment import (
    CompleteAssessmentCommand,
    FailAssessmentCommand,
    RegisterAssessmentCommand,
    StartAssessmentCommand,
)
from codestrata_platform.application.commands.repository import (
    ArchiveRepositoryCommand,
    RegisterRepositoryCommand,
)
from codestrata_platform.application.common.errors import NotFoundError, ValidationError
from codestrata_platform.application.queries.assessment import AssessmentQuery
from codestrata_platform.application.repository import DefaultRepositoryService
from codestrata_platform.domain.assessment import AssessmentId, AssessmentStatus, GeneratedReport
from codestrata_platform.domain.repository import RepositoryProvider, RepositoryVisibility
from codestrata_platform.domain.workspace.ids import WorkspaceId


def _seed_repository(
    repository_service: DefaultRepositoryService,
    seeded_workspace: tuple,
):
    org, workspace = seeded_workspace
    return repository_service.register_repository(
        RegisterRepositoryCommand(
            workspace_id=workspace.workspace_id,
            organization_id=org.organization_id,
            display_name="App",
            provider=RepositoryProvider.GITHUB,
            repository_url="https://github.com/acme/app",
            visibility=RepositoryVisibility.PRIVATE,
        )
    ), workspace


def test_assessment_lifecycle(
    assessment_service: DefaultAssessmentService,
    repository_service: DefaultRepositoryService,
    seeded_workspace: tuple,
) -> None:
    repository, workspace = _seed_repository(repository_service, seeded_workspace)

    pending = assessment_service.create_assessment(
        RegisterAssessmentCommand(
            repository_id=repository.repository_id,
            workspace_id=workspace.workspace_id,
            engine_version="1.2.3",
            assessment_version="0.1.0",
        )
    )
    assert pending.status is AssessmentStatus.PENDING

    running = assessment_service.start_assessment(
        StartAssessmentCommand(assessment_id=pending.assessment_id)
    )
    assert running.status is AssessmentStatus.RUNNING
    assert running.started_at is not None

    completed = assessment_service.complete_assessment(
        CompleteAssessmentCommand(
            assessment_id=pending.assessment_id,
            generated_reports=(
                GeneratedReport(report_type="html", location="/tmp/report.html"),
            ),
        )
    )
    assert completed.status is AssessmentStatus.SUCCEEDED
    assert completed.report_count == 1
    assert completed.completed_at is not None

    history = assessment_service.list_assessment_history(repository.repository_id)
    assert len(history) == 1

    listed = assessment_service.list_assessments(
        AssessmentQuery(repository_id=repository.repository_id)
    )
    assert listed.total == 1


def test_assessment_fail_path(
    assessment_service: DefaultAssessmentService,
    repository_service: DefaultRepositoryService,
    seeded_workspace: tuple,
) -> None:
    repository, workspace = _seed_repository(repository_service, seeded_workspace)
    pending = assessment_service.create_assessment(
        RegisterAssessmentCommand(
            repository_id=repository.repository_id,
            workspace_id=workspace.workspace_id,
            engine_version="1.0.0",
            assessment_version="0.1.0",
        )
    )
    failed = assessment_service.fail_assessment(
        FailAssessmentCommand(assessment_id=pending.assessment_id, reason="engine timeout")
    )
    assert failed.status is AssessmentStatus.FAILED
    assert failed.failure_reason == "engine timeout"


def test_assessment_rejects_workspace_mismatch(
    assessment_service: DefaultAssessmentService,
    repository_service: DefaultRepositoryService,
    seeded_workspace: tuple,
) -> None:
    repository, _workspace = _seed_repository(repository_service, seeded_workspace)
    with pytest.raises(ValidationError) as exc:
        assessment_service.create_assessment(
            RegisterAssessmentCommand(
                repository_id=repository.repository_id,
                workspace_id=WorkspaceId.generate(),
                engine_version="1.0.0",
                assessment_version="0.1.0",
            )
        )
    assert exc.value.reason_code == "assessment_workspace_mismatch"


def test_assessment_rejects_archived_repository(
    assessment_service: DefaultAssessmentService,
    repository_service: DefaultRepositoryService,
    seeded_workspace: tuple,
) -> None:
    repository, workspace = _seed_repository(repository_service, seeded_workspace)
    repository_service.archive_repository(
        ArchiveRepositoryCommand(repository_id=repository.repository_id)
    )
    with pytest.raises(ValidationError) as exc:
        assessment_service.create_assessment(
            RegisterAssessmentCommand(
                repository_id=repository.repository_id,
                workspace_id=workspace.workspace_id,
                engine_version="1.0.0",
                assessment_version="0.1.0",
            )
        )
    assert exc.value.reason_code == "repository_archived"


def test_missing_assessment(assessment_service: DefaultAssessmentService) -> None:
    with pytest.raises(NotFoundError):
        assessment_service.get_assessment(AssessmentId.generate())
