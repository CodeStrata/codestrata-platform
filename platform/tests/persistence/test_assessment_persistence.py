"""Assessment lifecycle persistence and listing tests."""

from __future__ import annotations

from codestrata_platform.domain.assessment import Assessment, AssessmentStatus, GeneratedReport
from codestrata_platform.domain.organization import Organization
from codestrata_platform.domain.repository import Repository, RepositoryProvider
from codestrata_platform.domain.workspace import Workspace
from codestrata_platform.infrastructure.persistence.repositories import (
    SqlAlchemyAssessmentRepository,
    SqlAlchemyOrganizationRepository,
    SqlAlchemyRepositoryRepository,
    SqlAlchemyWorkspaceRepository,
)


def _seed_repo(
    org_repo: SqlAlchemyOrganizationRepository,
    workspace_repo: SqlAlchemyWorkspaceRepository,
    repository_repo: SqlAlchemyRepositoryRepository,
) -> tuple[Organization, Workspace, Repository]:
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
    return org, workspace, repository


def test_assessment_lifecycle_and_listing(
    org_repo: SqlAlchemyOrganizationRepository,
    workspace_repo: SqlAlchemyWorkspaceRepository,
    repository_repo: SqlAlchemyRepositoryRepository,
    assessment_repo: SqlAlchemyAssessmentRepository,
) -> None:
    _org, workspace, repository = _seed_repo(org_repo, workspace_repo, repository_repo)

    pending = Assessment.create(
        repository_id=repository.repository_id,
        workspace_id=workspace.workspace_id,
        engine_version="1.0.0",
        assessment_version="0.1.0",
    )
    assessment_repo.save(pending)

    pending.start()
    assessment_repo.save(pending)

    pending.complete(
        generated_reports=(GeneratedReport(report_type="html", location="/tmp/r.html"),),
    )
    assessment_repo.save(pending)

    loaded = assessment_repo.get(pending.assessment_id)
    assert loaded is not None
    assert loaded.status is AssessmentStatus.SUCCEEDED
    assert len(loaded.generated_reports) == 1

    history = assessment_repo.list_by_repository(repository.repository_id)
    assert len(history) == 1

    by_ws = assessment_repo.list_by_workspace(workspace.workspace_id)
    assert len(by_ws) == 1


def test_failed_assessment_persists_reason(
    org_repo: SqlAlchemyOrganizationRepository,
    workspace_repo: SqlAlchemyWorkspaceRepository,
    repository_repo: SqlAlchemyRepositoryRepository,
    assessment_repo: SqlAlchemyAssessmentRepository,
) -> None:
    _org, workspace, repository = _seed_repo(org_repo, workspace_repo, repository_repo)
    assessment = Assessment.create(
        repository_id=repository.repository_id,
        workspace_id=workspace.workspace_id,
        engine_version="1.0.0",
        assessment_version="0.1.0",
    )
    assessment.fail(reason="engine timeout")
    assessment_repo.save(assessment)

    loaded = assessment_repo.get(assessment.assessment_id)
    assert loaded is not None
    assert loaded.status is AssessmentStatus.FAILED
    assert loaded.failure_reason == "engine timeout"
