"""API tests for Portfolio Retrieval endpoints."""

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
        assessment_id=AssessmentId(f"assessment:pr-{suffix}"),
    )
    assessment.start()
    assessment.complete()
    assessments.save(assessment)
    snapshot = EngineeringSnapshot.create(
        organization_id=OrganizationId(org_id),
        workspace_id=WorkspaceId(workspace_id),
        repository_id=RepositoryId(repo_id),
        assessment_id=assessment.assessment_id,
        assessment_intelligence_id=f"intel:pr-{suffix}",
        assessment_revision=1,
        version=1,
        source_artifact_ids=("artifact:1",),
        snapshot_id=EngineeringSnapshotId(f"eng-snapshot:pr-{suffix}"),
    )
    finding_id = EngineeringFindingId(f"eng-finding:pr-{suffix}")
    snapshot.build(
        technologies=(
            EngineeringTechnology(
                technology_id=EngineeringTechnologyId(f"eng-tech:pr-{suffix}"),
                canonical_key="java",
                display_name="Java",
                category=EngineeringCategory.OTHER,
            ),
        ),
        findings=(
            EngineeringFinding(
                finding_id=finding_id,
                source_finding_id=f"finding:pr-{suffix}",
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
                recommendation_id=EngineeringRecommendationId(f"eng-rec:pr-{suffix}"),
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


def _seed_portfolio(client: TestClient) -> tuple[str, str, str, str]:
    org = client.post("/api/v1/organizations", json={"name": "Acme PR"}).json()
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
                "display_name": f"repo-pr-{idx}",
                "provider": "github",
                "repository_url": f"https://github.com/acme/repo-pr-{idx}",
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
            "name": "Platform PR",
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
    return org_id, workspace_id, portfolio_id, snapshot_id


def test_portfolio_retrieval_api_flow(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CODESTRATA_PORTFOLIO_RETRIEVAL_ENABLED", raising=False)
    org_id, workspace_id, portfolio_id, snapshot_id = _seed_portfolio(client)
    monkeypatch.setenv("CODESTRATA_PORTFOLIO_RETRIEVAL_ENABLED", "true")

    created = client.post(
        "/api/v1/portfolio-retrieval/indexes",
        json={
            "organization_id": org_id,
            "workspace_id": workspace_id,
            "portfolio_id": portfolio_id,
            "portfolio_snapshot_id": snapshot_id,
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["status"] == "completed"
    index_id = body["index_id"]
    assert body["document_count"] >= 1
    assert body["chunk_count"] >= 1
    assert body["repository_count"] == 2

    again = client.post(
        "/api/v1/portfolio-retrieval/indexes",
        json={
            "organization_id": org_id,
            "workspace_id": workspace_id,
            "portfolio_id": portfolio_id,
            "portfolio_snapshot_id": snapshot_id,
        },
    )
    assert again.status_code == 200
    assert again.json()["index_id"] == index_id
    assert again.json()["idempotent"] is True

    scope_params = {"organization_id": org_id, "workspace_id": workspace_id}

    details = client.get(
        f"/api/v1/portfolio-retrieval/indexes/{index_id}", params=scope_params
    )
    assert details.status_code == 200

    latest = client.get(
        f"/api/v1/portfolios/{portfolio_id}/retrieval-indexes/latest", params=scope_params
    )
    assert latest.status_code == 200
    assert latest.json()["index_id"] == index_id

    listed = client.get(
        f"/api/v1/portfolios/{portfolio_id}/retrieval-indexes", params=scope_params
    )
    assert listed.status_code == 200
    assert len(listed.json()) >= 1

    documents = client.get(f"/api/v1/portfolio-retrieval/indexes/{index_id}/documents")
    assert documents.status_code == 200
    docs = documents.json()
    assert docs
    document_id = docs[0]["document_id"]
    assert (
        client.get(
            f"/api/v1/portfolio-retrieval/indexes/{index_id}/documents/{document_id}"
        ).status_code
        == 200
    )

    search = client.post(
        f"/api/v1/portfolio-retrieval/indexes/{index_id}/search",
        params=scope_params,
        json={
            "query_text": "debt hotspot modernization",
            "mode": "hybrid",
            "top_k": 5,
            "repository_balance_mode": "diversified",
        },
    )
    assert search.status_code == 200, search.text
    hits = search.json()["hits"]
    assert hits
    assert "final_score" in hits[0]["score"]
    assert "portfolio_score" in hits[0]["score"]
    assert "embedding" not in hits[0]

    chunk_id = hits[0]["chunk_id"]
    chunk = client.get(f"/api/v1/portfolio-retrieval/indexes/{index_id}/chunks/{chunk_id}")
    assert chunk.status_code == 200
    assert chunk.json()["has_embedding"] is True

    context = client.post(
        f"/api/v1/portfolio-retrieval/indexes/{index_id}/context",
        params=scope_params,
        json={
            "query_text": "debt hotspot modernization",
            "top_k": 5,
            "max_tokens": 4000,
            "repository_balance_mode": "diversified",
        },
    )
    assert context.status_code == 200, context.text
    assert context.json()["items"]
    assert "sections" in context.json()

    stats = client.get(f"/api/v1/portfolio-retrieval/indexes/{index_id}/statistics")
    assert stats.status_code == 200
    assert stats.json()["embedded_chunk_count"] >= 1
    assert stats.json()["repository_count"] == 2


def test_portfolio_retrieval_disabled_by_default(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CODESTRATA_PORTFOLIO_RETRIEVAL_ENABLED", raising=False)
    org_id, workspace_id, portfolio_id, snapshot_id = _seed_portfolio(client)
    created = client.post(
        "/api/v1/portfolio-retrieval/indexes",
        json={
            "organization_id": org_id,
            "workspace_id": workspace_id,
            "portfolio_id": portfolio_id,
            "portfolio_snapshot_id": snapshot_id,
        },
    )
    assert created.status_code == 422


def test_get_portfolio_retrieval_index_requires_scope_params(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CODESTRATA_PORTFOLIO_RETRIEVAL_ENABLED", "true")
    response = client.get("/api/v1/portfolio-retrieval/indexes/portfolio-retrieval:missing")
    assert response.status_code == 422, response.text


def test_portfolio_retrieval_rejects_blank_query_and_excessive_top_k(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CODESTRATA_PORTFOLIO_RETRIEVAL_ENABLED", raising=False)
    org_id, workspace_id, portfolio_id, snapshot_id = _seed_portfolio(client)
    monkeypatch.setenv("CODESTRATA_PORTFOLIO_RETRIEVAL_ENABLED", "true")
    created = client.post(
        "/api/v1/portfolio-retrieval/indexes",
        json={
            "organization_id": org_id,
            "workspace_id": workspace_id,
            "portfolio_id": portfolio_id,
            "portfolio_snapshot_id": snapshot_id,
        },
    )
    assert created.status_code == 201, created.text
    index_id = created.json()["index_id"]
    blank = client.post(
        f"/api/v1/portfolio-retrieval/indexes/{index_id}/search",
        json={"query_text": "   "},
    )
    assert blank.status_code in {400, 422}
    too_large = client.post(
        f"/api/v1/portfolio-retrieval/indexes/{index_id}/search",
        json={"query_text": "debt", "top_k": 101},
    )
    assert too_large.status_code in {400, 422}
