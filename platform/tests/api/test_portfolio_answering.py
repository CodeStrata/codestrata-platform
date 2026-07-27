"""API tests for Portfolio Answering endpoints."""

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
        assessment_id=AssessmentId(f"assessment:pa-{suffix}"),
    )
    assessment.start()
    assessment.complete()
    assessments.save(assessment)
    snapshot = EngineeringSnapshot.create(
        organization_id=OrganizationId(org_id),
        workspace_id=WorkspaceId(workspace_id),
        repository_id=RepositoryId(repo_id),
        assessment_id=assessment.assessment_id,
        assessment_intelligence_id=f"intel:pa-{suffix}",
        assessment_revision=1,
        version=1,
        source_artifact_ids=("artifact:1",),
        snapshot_id=EngineeringSnapshotId(f"eng-snapshot:pa-{suffix}"),
    )
    finding_id = EngineeringFindingId(f"eng-finding:pa-{suffix}")
    snapshot.build(
        technologies=(
            EngineeringTechnology(
                technology_id=EngineeringTechnologyId(f"eng-tech:pa-{suffix}"),
                canonical_key="java",
                display_name="Java",
                category=EngineeringCategory.OTHER,
            ),
        ),
        findings=(
            EngineeringFinding(
                finding_id=finding_id,
                source_finding_id=f"finding:pa-{suffix}",
                category=EngineeringCategory.TECHNICAL_DEBT,
                severity=EngineeringSeverity.HIGH,
                title="Debt hotspot",
                summary="Debt across repositories",
                rule_id="rule.debt",
                confidence=0.8,
            ),
        ),
        recommendations=(
            EngineeringRecommendation(
                recommendation_id=EngineeringRecommendationId(f"eng-rec:pa-{suffix}"),
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


def _seed_portfolio_index(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[str, str, str, str]:
    monkeypatch.setenv("CODESTRATA_PORTFOLIO_RETRIEVAL_ENABLED", "true")
    org = client.post("/api/v1/organizations", json={"name": "Acme PA"}).json()
    org_id = org["id"]
    workspace = client.post(
        "/api/v1/workspaces",
        json={"organization_id": org_id, "name": "Main"},
    ).json()
    workspace_id = workspace["id"]
    repos: list[str] = []
    for idx in range(2):
        repo = client.post(
            "/api/v1/repositories",
            json={
                "organization_id": org_id,
                "workspace_id": workspace_id,
                "display_name": f"repo-pa-{idx}",
                "provider": "github",
                "repository_url": f"https://github.com/acme/repo-pa-{idx}",
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
            "name": "Platform PA",
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
    index = client.post(
        "/api/v1/portfolio-retrieval/indexes",
        json={
            "organization_id": org_id,
            "workspace_id": workspace_id,
            "portfolio_id": portfolio_id,
            "portfolio_snapshot_id": snapshot_id,
        },
    )
    assert index.status_code in {200, 201}, index.text
    return org_id, workspace_id, portfolio_id, index.json()["index_id"]


def test_portfolio_answering_api_flow(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODESTRATA_PORTFOLIO_ANSWERING_ENABLED", "true")
    monkeypatch.setenv("CODESTRATA_LLM_PROVIDER", "deterministic")
    org_id, workspace_id, portfolio_id, index_id = _seed_portfolio_index(client, monkeypatch)

    disabled = client.post(
        f"/api/v1/portfolios/{portfolio_id}/ask",
        json={
            "question": "What is the portfolio overview?",
            "organization_id": org_id,
            "workspace_id": workspace_id,
            "portfolio_retrieval_index_id": index_id,
        },
    )
    # Already enabled above; verify happy path.
    assert disabled.status_code == 201, disabled.text
    body = disabled.json()
    assert body["answer"]
    assert body["citations"]
    assert body["status"] == "completed"
    assert body["portfolio_id"] == portfolio_id
    assert body["portfolio_retrieval_index_id"] == index_id
    assert body["confidence_score"] is not None
    assert isinstance(body["limitations"], list)
    answer_id = body["answer_run_id"]

    got = client.get(f"/api/v1/portfolio-answers/{answer_id}")
    assert got.status_code == 200
    listed = client.get(f"/api/v1/portfolios/{portfolio_id}/answers")
    assert listed.status_code == 200
    assert any(item["answer_run_id"] == answer_id for item in listed.json())

    feedback = client.post(
        f"/api/v1/portfolio-answers/{answer_id}/feedback",
        json={"rating": 4, "feedback_category": "useful", "comment": "good"},
    )
    assert feedback.status_code == 200

    created = client.post(
        "/api/v1/portfolio-answers",
        json={
            "question": "Where is technology fragmentation concentrated?",
            "organization_id": org_id,
            "workspace_id": workspace_id,
            "portfolio_id": portfolio_id,
            "portfolio_retrieval_index_id": index_id,
            "use_cache": False,
        },
    )
    assert created.status_code == 201, created.text


def test_portfolio_answering_disabled(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CODESTRATA_PORTFOLIO_ANSWERING_ENABLED", raising=False)
    monkeypatch.setenv("CODESTRATA_LLM_PROVIDER", "deterministic")
    org_id, workspace_id, portfolio_id, index_id = _seed_portfolio_index(client, monkeypatch)
    asked = client.post(
        f"/api/v1/portfolios/{portfolio_id}/ask",
        json={
            "question": "What is the portfolio overview?",
            "organization_id": org_id,
            "workspace_id": workspace_id,
            "portfolio_retrieval_index_id": index_id,
        },
    )
    assert asked.status_code in {400, 422}
    body = asked.json()
    code = body.get("code") or (body.get("error") or {}).get("code")
    assert code == "portfolio_answering_disabled"
