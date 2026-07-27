"""API tests for portfolio endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from codestrata_platform.domain.assessment import Assessment
from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.engineering import (
    EngineeringCategory,
    EngineeringFinding,
    EngineeringRecommendation,
    EngineeringSeverity,
    EngineeringSnapshot,
    EngineeringTechnology,
)
from codestrata_platform.domain.engineering.ids import (
    EngineeringFindingId,
    EngineeringRecommendationId,
    EngineeringSnapshotId,
    EngineeringTechnologyId,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId


def _seed_repo_intelligence(
    client: TestClient,
    *,
    org_id: str,
    workspace_id: str,
    repo_id: str,
    suffix: str,
) -> None:
    state = client.app.state
    assessments = state.memory_assessments
    engineering = state.memory_engineering
    assessment = Assessment.create(
        repository_id=RepositoryId(repo_id),
        workspace_id=WorkspaceId(workspace_id),
        engine_version="1.0.0",
        assessment_version="0.1.0",
        assessment_id=AssessmentId(f"assessment:{suffix}"),
    )
    assessment.start()
    assessment.complete()
    assessments.save(assessment)
    snapshot = EngineeringSnapshot.create(
        organization_id=OrganizationId(org_id),
        workspace_id=WorkspaceId(workspace_id),
        repository_id=RepositoryId(repo_id),
        assessment_id=assessment.assessment_id,
        assessment_intelligence_id=f"intel:{suffix}",
        assessment_revision=1,
        version=1,
        source_artifact_ids=("artifact:1",),
        snapshot_id=EngineeringSnapshotId(f"eng-snapshot:{suffix}"),
    )
    finding_id = EngineeringFindingId(f"eng-finding:{suffix}")
    snapshot.build(
        technologies=(
            EngineeringTechnology(
                technology_id=EngineeringTechnologyId(f"eng-tech:{suffix}"),
                canonical_key="java",
                display_name="Java",
                category=EngineeringCategory.OTHER,
            ),
        ),
        findings=(
            EngineeringFinding(
                finding_id=finding_id,
                source_finding_id=f"finding:{suffix}",
                category=EngineeringCategory.TECHNICAL_DEBT,
                severity=EngineeringSeverity.HIGH,
                title="Debt hotspot",
                summary="Debt",
                rule_id="rule.debt",
                confidence=0.8,
            ),
        ),
        recommendations=(
            EngineeringRecommendation(
                recommendation_id=EngineeringRecommendationId(f"eng-rec:{suffix}"),
                source_recommendation_id="rec:debt",
                title="Reduce debt",
                rationale="Refactor",
                category=EngineeringCategory.TECHNICAL_DEBT,
                severity=EngineeringSeverity.HIGH,
                priority="p2",
                related_finding_ids=(finding_id.value,),
            ),
        ),
    )
    snapshot.publish()
    engineering.save(snapshot)


def test_portfolio_api_flow(client: TestClient) -> None:
    org = client.post("/api/v1/organizations", json={"name": "Acme"}).json()
    org_id = org["id"]
    workspace = client.post(
        "/api/v1/workspaces",
        json={"organization_id": org_id, "name": "Main"},
    ).json()
    workspace_id = workspace["id"]
    repos = []
    for idx in range(2):
        repo = client.post(
            "/api/v1/repositories",
            json={
                "organization_id": org_id,
                "workspace_id": workspace_id,
                "display_name": f"repo-{idx}",
                "provider": "github",
                "repository_url": f"https://github.com/acme/repo-{idx}",
            },
        ).json()
        repos.append(repo["id"])
        _seed_repo_intelligence(
            client,
            org_id=org_id,
            workspace_id=workspace_id,
            repo_id=repo["id"],
            suffix=str(idx),
        )

    created = client.post(
        "/api/v1/portfolios",
        json={
            "organization_id": org_id,
            "workspace_id": workspace_id,
            "name": "Platform",
        },
    )
    assert created.status_code == 201, created.text
    portfolio_id = created.json()["portfolio"]["portfolio_id"]

    for repo_id in repos:
        added = client.post(
            f"/api/v1/portfolios/{portfolio_id}/repositories",
            json={
                "organization_id": org_id,
                "workspace_id": workspace_id,
                "repository_id": repo_id,
            },
        )
        assert added.status_code == 200, added.text

    built = client.post(
        f"/api/v1/portfolios/{portfolio_id}/snapshots",
        json={"organization_id": org_id, "workspace_id": workspace_id},
    )
    assert built.status_code == 201, built.text
    snapshot_id = built.json()["snapshot"]["portfolio_snapshot_id"]
    assert built.json()["snapshot"]["available_repository_count"] == 2

    latest = client.get(
        f"/api/v1/portfolios/{portfolio_id}/snapshots/latest",
        params={"organization_id": org_id, "workspace_id": workspace_id},
    )
    assert latest.status_code == 200
    assert latest.json()["snapshot"]["portfolio_snapshot_id"] == snapshot_id

    for path in (
        "technologies",
        "findings",
        "recommendations",
        "risks",
        "modernization",
        "coverage",
        "repository-profiles",
        "overview",
    ):
        response = client.get(f"/api/v1/portfolio-snapshots/{snapshot_id}/{path}")
        assert response.status_code == 200, path

    listed = client.get(
        "/api/v1/portfolios",
        params={"organization_id": org_id, "workspace_id": workspace_id},
    )
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1
