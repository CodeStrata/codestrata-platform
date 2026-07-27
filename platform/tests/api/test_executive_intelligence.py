"""API tests for Executive Intelligence endpoints."""

from __future__ import annotations

import pytest
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


def _build_portfolio_with_snapshot(client: TestClient) -> tuple[str, str, str]:
    org = client.post("/api/v1/organizations", json={"name": "Acme"}).json()
    org_id = org["id"]
    workspace = client.post(
        "/api/v1/workspaces",
        json={"organization_id": org_id, "name": "Main"},
    ).json()
    workspace_id = workspace["id"]
    repo = client.post(
        "/api/v1/repositories",
        json={
            "organization_id": org_id,
            "workspace_id": workspace_id,
            "display_name": "repo-1",
            "provider": "github",
            "repository_url": "https://github.com/acme/repo-1",
        },
    ).json()
    _seed_repo_intelligence(
        client,
        org_id=org_id,
        workspace_id=workspace_id,
        repo_id=repo["id"],
        suffix="1",
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

    added = client.post(
        f"/api/v1/portfolios/{portfolio_id}/repositories",
        json={
            "organization_id": org_id,
            "workspace_id": workspace_id,
            "repository_id": repo["id"],
        },
    )
    assert added.status_code == 200, added.text

    built = client.post(
        f"/api/v1/portfolios/{portfolio_id}/snapshots",
        json={"organization_id": org_id, "workspace_id": workspace_id},
    )
    assert built.status_code == 201, built.text

    return org_id, workspace_id, portfolio_id


def test_build_executive_intelligence_requires_feature_flag(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CODESTRATA_EXECUTIVE_INTELLIGENCE_ENABLED", raising=False)
    org_id, workspace_id, portfolio_id = _build_portfolio_with_snapshot(client)

    response = client.post(
        f"/api/v1/portfolios/{portfolio_id}/executive-intelligence",
        json={"organization_id": org_id, "workspace_id": workspace_id},
    )
    assert response.status_code == 422, response.text


def test_executive_intelligence_full_route_flow(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CODESTRATA_EXECUTIVE_INTELLIGENCE_ENABLED", "true")
    org_id, workspace_id, portfolio_id = _build_portfolio_with_snapshot(client)

    built = client.post(
        f"/api/v1/portfolios/{portfolio_id}/executive-intelligence",
        json={"organization_id": org_id, "workspace_id": workspace_id},
    )
    assert built.status_code == 201, built.text
    payload = built.json()
    executive_intelligence_id = payload["summary"]["executive_intelligence_id"]
    assert payload["metrics"]
    assert payload["summary"]["status"] == "completed"

    listed = client.get(
        f"/api/v1/portfolios/{portfolio_id}/executive-intelligence",
        params={"organization_id": org_id, "workspace_id": workspace_id},
    )
    assert listed.status_code == 200, listed.text
    assert listed.json()["total"] == 1

    latest = client.get(
        f"/api/v1/portfolios/{portfolio_id}/executive-intelligence/latest",
        params={"organization_id": org_id, "workspace_id": workspace_id},
    )
    assert latest.status_code == 200, latest.text
    assert latest.json()["summary"]["executive_intelligence_id"] == executive_intelligence_id

    detail = client.get(f"/api/v1/executive-intelligence/{executive_intelligence_id}")
    assert detail.status_code == 200, detail.text

    metrics = client.get(
        f"/api/v1/executive-intelligence/{executive_intelligence_id}/metrics"
    )
    assert metrics.status_code == 200, metrics.text
    assert metrics.json()["metrics"]

    findings = client.get(
        f"/api/v1/executive-intelligence/{executive_intelligence_id}/findings"
    )
    assert findings.status_code == 200, findings.text

    recommendations = client.get(
        f"/api/v1/executive-intelligence/{executive_intelligence_id}/recommendations"
    )
    assert recommendations.status_code == 200, recommendations.text

    overview = client.get(
        f"/api/v1/executive-intelligence/{executive_intelligence_id}/overview"
    )
    assert overview.status_code == 200, overview.text
    assert overview.json()["summary"]["executive_intelligence_id"] == executive_intelligence_id
