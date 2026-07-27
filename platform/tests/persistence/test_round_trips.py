"""Lossless aggregate ↔ persistence round-trip tests."""

from __future__ import annotations

from codestrata_platform.domain.assessment import Assessment, AssessmentReference, GeneratedReport
from codestrata_platform.domain.organization import Organization
from codestrata_platform.domain.repository import (
    Repository,
    RepositoryMetadata,
    RepositoryProvider,
    RepositoryVisibility,
)
from codestrata_platform.domain.workspace import Workspace
from codestrata_platform.infrastructure.persistence.repositories import (
    SqlAlchemyAssessmentRepository,
    SqlAlchemyOrganizationRepository,
    SqlAlchemyRepositoryRepository,
    SqlAlchemyWorkspaceRepository,
)


def test_organization_round_trip(org_repo: SqlAlchemyOrganizationRepository) -> None:
    original = Organization.create(name="Acme Corp")
    original.rename("Acme Corporation")
    org_repo.save(original)

    loaded = org_repo.get(original.organization_id)
    assert loaded is not None
    assert loaded.organization_id == original.organization_id
    assert loaded.name == "Acme Corporation"
    assert loaded.status is original.status
    assert loaded.audit.created_at.value == original.audit.created_at.value
    assert loaded.audit.updated_at.value == original.audit.updated_at.value
    assert loaded._version == original._version


def test_workspace_round_trip(
    org_repo: SqlAlchemyOrganizationRepository,
    workspace_repo: SqlAlchemyWorkspaceRepository,
) -> None:
    org = Organization.create(name="Org")
    org_repo.save(org)
    original = Workspace.create(
        organization_id=org.organization_id,
        name="Engineering",
        description="Primary",
    )
    workspace_repo.save(original)

    loaded = workspace_repo.get(original.workspace_id)
    assert loaded is not None
    assert loaded.workspace_id == original.workspace_id
    assert loaded.organization_id == org.organization_id
    assert loaded.name == "Engineering"
    assert loaded.description == "Primary"
    assert loaded.status is original.status
    assert loaded._version == original._version


def test_repository_round_trip(
    org_repo: SqlAlchemyOrganizationRepository,
    workspace_repo: SqlAlchemyWorkspaceRepository,
    repository_repo: SqlAlchemyRepositoryRepository,
) -> None:
    org = Organization.create(name="Org")
    org_repo.save(org)
    workspace = Workspace.create(organization_id=org.organization_id, name="WS")
    workspace_repo.save(workspace)

    original = Repository.register(
        workspace_id=workspace.workspace_id,
        organization_id=org.organization_id,
        display_name="Petclinic",
        provider=RepositoryProvider.GITHUB,
        repository_url="https://github.com/acme/petclinic",
        default_branch="develop",
        visibility=RepositoryVisibility.INTERNAL,
        description="Sample",
        metadata=RepositoryMetadata({"tier": "critical"}),
    )
    repository_repo.save(original)

    loaded = repository_repo.get(original.repository_id)
    assert loaded is not None
    assert loaded.repository_id == original.repository_id
    assert loaded.display_name == "Petclinic"
    assert loaded.provider is RepositoryProvider.GITHUB
    assert loaded.repository_url == "https://github.com/acme/petclinic"
    assert loaded.default_branch == "develop"
    assert loaded.visibility is RepositoryVisibility.INTERNAL
    assert loaded.description == "Sample"
    assert dict(loaded.metadata.attributes) == {"tier": "critical"}
    assert loaded.status is original.status
    assert loaded._version == original._version


def test_assessment_round_trip(
    org_repo: SqlAlchemyOrganizationRepository,
    workspace_repo: SqlAlchemyWorkspaceRepository,
    repository_repo: SqlAlchemyRepositoryRepository,
    assessment_repo: SqlAlchemyAssessmentRepository,
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
        engine_version="1.2.3",
        assessment_version="0.1.0",
    )
    assessment.start()
    assessment.complete(
        generated_reports=(GeneratedReport(report_type="html", location="/tmp/r.html"),),
        references=(AssessmentReference(artifact_uri="s3://bucket/a.json", label="raw"),),
    )
    assessment_repo.save(assessment)

    loaded = assessment_repo.get(assessment.assessment_id)
    assert loaded is not None
    assert loaded.assessment_id == assessment.assessment_id
    assert loaded.status is assessment.status
    assert loaded.started_at == assessment.started_at
    assert loaded.completed_at == assessment.completed_at
    assert loaded.generated_reports == assessment.generated_reports
    assert loaded.references == assessment.references
    assert loaded.failure_reason is None
    assert str(loaded.engine_version) == "1.2.3"
    assert str(loaded.assessment_version) == "0.1.0"
    assert loaded._version == assessment._version
