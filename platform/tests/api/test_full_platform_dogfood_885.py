"""Phase 8.8.5 – Full Platform end-to-end dogfood.

Exercises the canonical commercial pipeline with CodeStrata-shaped portfolios,
security isolation, reliability, performance, and observability checks.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

import pytest
from fastapi.testclient import TestClient

from codestrata_platform.api import create_app
from codestrata_platform.api.security import PLATFORM_API_KEY_ENV, PLATFORM_ENV_VAR
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


def _checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _enable_commercial_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODESTRATA_ANSWERING_ENABLED", "true")
    monkeypatch.setenv("CODESTRATA_PORTFOLIO_RETRIEVAL_ENABLED", "true")
    monkeypatch.setenv("CODESTRATA_PORTFOLIO_ANSWERING_ENABLED", "true")
    monkeypatch.setenv("CODESTRATA_EXECUTIVE_INTELLIGENCE_ENABLED", "true")
    monkeypatch.setenv("CODESTRATA_EXECUTIVE_PRESENTATION_ENABLED", "true")
    monkeypatch.setenv("CODESTRATA_STRATEGIC_ROADMAP_ENABLED", "true")
    monkeypatch.setenv("CODESTRATA_LLM_PROVIDER", "deterministic")
    monkeypatch.setenv("CODESTRATA_EMBEDDING_PROVIDER", "deterministic")


def _seed_repo_ceim(
    client: TestClient,
    *,
    org_id: str,
    workspace_id: str,
    repo_id: str,
    suffix: str,
    tech_key: str,
    category: EngineeringCategory,
    severity: EngineeringSeverity = EngineeringSeverity.HIGH,
    title: str = "Engineering finding",
    incomplete: bool = False,
) -> None:
    """Inject published CEIM for portfolio participation (CodeStrata-shaped fixtures)."""

    state = client.app.state
    assessments = state.memory_assessments
    engineering = state.memory_engineering
    assessment = Assessment.create(
        repository_id=RepositoryId(repo_id),
        workspace_id=WorkspaceId(workspace_id),
        engine_version="1.0.0",
        assessment_version="0.1.0",
        assessment_id=AssessmentId(f"assessment:dogfood-{suffix}"),
    )
    assessment.start()
    assessment.complete()
    assessments.save(assessment)
    snapshot = EngineeringSnapshot.create(
        organization_id=OrganizationId(org_id),
        workspace_id=WorkspaceId(workspace_id),
        repository_id=RepositoryId(repo_id),
        assessment_id=assessment.assessment_id,
        assessment_intelligence_id=f"intel:dogfood-{suffix}",
        assessment_revision=1,
        version=1,
        source_artifact_ids=("artifact:dogfood",),
        snapshot_id=EngineeringSnapshotId(f"eng-snapshot:dogfood-{suffix}"),
    )
    if incomplete:
        # Placeholder repos remain visibly thin — no inflated findings.
        snapshot.build(
            technologies=(
                EngineeringTechnology(
                    technology_id=EngineeringTechnologyId(f"eng-tech:dogfood-{suffix}"),
                    canonical_key=tech_key,
                    display_name=tech_key,
                    category=category,
                ),
            ),
            findings=(),
            recommendations=(),
        )
    else:
        finding_id = EngineeringFindingId(f"eng-finding:dogfood-{suffix}")
        snapshot.build(
            technologies=(
                EngineeringTechnology(
                    technology_id=EngineeringTechnologyId(f"eng-tech:dogfood-{suffix}"),
                    canonical_key=tech_key,
                    display_name=tech_key.title(),
                    category=category,
                ),
            ),
            findings=(
                EngineeringFinding(
                    finding_id=finding_id,
                    source_finding_id=f"finding:dogfood-{suffix}",
                    category=category,
                    severity=severity,
                    title=title,
                    summary=f"{title} observed in {suffix}",
                    rule_id=f"rule.dogfood.{suffix}",
                    confidence=0.85,
                ),
            ),
            recommendations=(
                EngineeringRecommendation(
                    recommendation_id=EngineeringRecommendationId(
                        f"eng-rec:dogfood-{suffix}"
                    ),
                    source_recommendation_id=f"rec:dogfood-{suffix}",
                    title=f"Address {title}",
                    rationale="Evidence-backed remediation",
                    category=category,
                    severity=severity,
                    priority="p1",
                    related_finding_ids=(finding_id.value,),
                ),
            ),
        )
    snapshot.publish()
    engineering.save(snapshot)


def _seed_repository_pipeline(client: TestClient) -> dict[str, str]:
    """Full REST chain: onboard → assessment → intelligence → CEIM → KG → retrieval."""

    org = client.post("/api/v1/organizations", json={"name": "CodeStrata"}).json()
    workspace = client.post(
        "/api/v1/workspaces",
        json={"organization_id": org["id"], "name": "Platform Dogfood"},
    ).json()
    repo = client.post(
        "/api/v1/repositories",
        json={
            "workspace_id": workspace["id"],
            "organization_id": org["id"],
            "display_name": "codestrata-engine",
            "provider": "github",
            "repository_url": "https://github.com/codestrata/engine",
            "default_branch": "main",
            "visibility": "private",
        },
    ).json()
    assessment = client.post(
        "/api/v1/assessments",
        json={
            "repository_id": repo["id"],
            "workspace_id": workspace["id"],
            "engine_version": "1.0.0",
            "assessment_version": "0.1.0",
        },
    ).json()
    assessment_id = assessment["id"]
    content = json.dumps(
        {
            "findings": [
                {
                    "finding_id": "finding:engine-sec",
                    "rule_id": "rule.security.hardening",
                    "title": "Hardening gap",
                    "summary": "Privileged runtime configuration observed.",
                    "category": "security",
                    "severity": "critical",
                    "confidence": 0.92,
                    "metadata": {"technology": "Docker"},
                    "evidence": [{"path": "deploy/compose.yml", "line_start": 4}],
                },
                {
                    "finding_id": "finding:engine-debt",
                    "rule_id": "rule.debt.complexity",
                    "title": "Complexity hotspot",
                    "summary": "High complexity in orchestration module.",
                    "category": "maintainability",
                    "severity": "high",
                    "confidence": 0.8,
                    "evidence": [{"path": "src/codestrata/application/assessment/service.py"}],
                },
            ]
        }
    ).encode("utf-8")
    checksum = _checksum(content)
    registered = client.post(
        f"/api/v1/ingestion/assessments/{assessment_id}/artifacts",
        json={
            "engine_assessment_id": "engine-assessment:dogfood-1",
            "artifact_type": "findings",
            "format": "json",
            "schema_version": "1.0",
            "checksum": checksum,
            "size_bytes": len(content),
        },
    )
    assert registered.status_code == 201, registered.text
    artifact_id = registered.json()["artifact_id"]
    uploaded = client.put(
        f"/api/v1/ingestion/assessments/{assessment_id}/artifacts/{artifact_id}",
        content=content,
        headers={"Content-Type": "application/json", "X-CodeStrata-Checksum": checksum},
    )
    assert uploaded.status_code in {200, 201, 204}, uploaded.text
    completed = client.post(
        f"/api/v1/ingestion/assessments/{assessment_id}/artifacts/{artifact_id}/complete"
    )
    assert completed.status_code in {200, 201}, completed.text
    intel = client.post(f"/api/v1/ingestion/assessments/{assessment_id}/intelligence")
    assert intel.status_code == 201, intel.text
    built = client.post(
        "/api/v1/engineering/snapshots",
        json={"assessment_id": assessment_id, "publish": True},
    )
    assert built.status_code == 201, built.text
    snapshot_id = built.json()["snapshot_id"]
    graph = client.post("/api/v1/knowledge-graphs", json={"snapshot_id": snapshot_id})
    assert graph.status_code == 201, graph.text
    index = client.post(
        "/api/v1/retrieval/indexes",
        json={"snapshot_id": snapshot_id, "graph_id": graph.json()["graph_id"]},
    )
    assert index.status_code == 201, index.text
    return {
        "organization_id": org["id"],
        "workspace_id": workspace["id"],
        "repository_id": repo["id"],
        "assessment_id": assessment_id,
        "snapshot_id": snapshot_id,
        "graph_id": graph.json()["graph_id"],
        "index_id": index.json()["index_id"],
    }


def _create_codestrata_portfolio(client: TestClient) -> dict[str, Any]:
    org = client.post("/api/v1/organizations", json={"name": "CodeStrata Inc"}).json()
    org_id = org["id"]
    workspace = client.post(
        "/api/v1/workspaces",
        json={"organization_id": org_id, "name": "Commercial"},
    ).json()
    workspace_id = workspace["id"]

    catalog = (
        ("engine", "python", EngineeringCategory.ARCHITECTURE, False, "Architecture drift"),
        ("platform", "fastapi", EngineeringCategory.ARCHITECTURE, False, "API boundary debt"),
        ("examples", "python", EngineeringCategory.OTHER, False, "Sample inconsistency"),
        ("vscode-ext", "typescript", EngineeringCategory.OTHER, True, ""),
        ("cursor-ext", "nodejs", EngineeringCategory.OTHER, True, ""),
        ("docs", "markdown", EngineeringCategory.DOCUMENTATION, True, ""),
    )
    repo_ids: list[str] = []
    for idx, (name, tech, category, incomplete, title) in enumerate(catalog, start=1):
        repo = client.post(
            "/api/v1/repositories",
            json={
                "organization_id": org_id,
                "workspace_id": workspace_id,
                "display_name": f"codestrata-{name}",
                "provider": "github",
                "repository_url": f"https://github.com/codestrata/{name}",
            },
        ).json()
        repo_ids.append(repo["id"])
        _seed_repo_ceim(
            client,
            org_id=org_id,
            workspace_id=workspace_id,
            repo_id=repo["id"],
            suffix=f"{idx}-{name}",
            tech_key=tech,
            category=category,
            incomplete=incomplete,
            title=title or "placeholder",
            severity=(
                EngineeringSeverity.CRITICAL
                if name == "engine"
                else EngineeringSeverity.HIGH
            ),
        )

    created = client.post(
        "/api/v1/portfolios",
        json={
            "organization_id": org_id,
            "workspace_id": workspace_id,
            "name": "CodeStrata Full Portfolio",
        },
    )
    assert created.status_code == 201, created.text
    portfolio_id = created.json()["portfolio"]["portfolio_id"]
    for repo_id in repo_ids:
        added = client.post(
            f"/api/v1/portfolios/{portfolio_id}/repositories",
            json={
                "organization_id": org_id,
                "workspace_id": workspace_id,
                "repository_id": repo_id,
            },
        )
        assert added.status_code == 200, added.text

    snapshot = client.post(
        f"/api/v1/portfolios/{portfolio_id}/snapshots",
        json={"organization_id": org_id, "workspace_id": workspace_id},
    )
    assert snapshot.status_code == 201, snapshot.text
    portfolio_snapshot_id = snapshot.json()["snapshot"]["portfolio_snapshot_id"]
    return {
        "organization_id": org_id,
        "workspace_id": workspace_id,
        "portfolio_id": portfolio_id,
        "portfolio_snapshot_id": portfolio_snapshot_id,
        "repository_ids": repo_ids,
    }


def test_full_platform_dogfood_canonical_pipeline(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_commercial_flags(monkeypatch)

    # --- Repository-level canonical flow ---
    repo_ctx = _seed_repository_pipeline(client)
    asked = client.post(
        f"/api/v1/repositories/{repo_ctx['repository_id']}/ask",
        json={
            "question": "What are the highest-risk engineering issues?",
            "organization_id": repo_ctx["organization_id"],
            "workspace_id": repo_ctx["workspace_id"],
            "retrieval_index_id": repo_ctx["index_id"],
        },
        headers={"X-Request-Id": "dogfood-repo-ask-1"},
    )
    assert asked.status_code == 201, asked.text
    assert asked.headers.get("X-Request-Id") == "dogfood-repo-ask-1"
    answer = asked.json()
    assert answer["status"] == "completed"
    assert answer["answer"]
    assert answer["citations"]
    assert isinstance(answer["limitations"], list)
    # Idempotent re-ask with cache allowed should not invent citations.
    asked_again = client.post(
        f"/api/v1/repositories/{repo_ctx['repository_id']}/ask",
        json={
            "question": "What are the highest-risk engineering issues?",
            "organization_id": repo_ctx["organization_id"],
            "workspace_id": repo_ctx["workspace_id"],
            "retrieval_index_id": repo_ctx["index_id"],
        },
    )
    assert asked_again.status_code == 201, asked_again.text

    # --- Portfolio / executive flow (CodeStrata-shaped) ---
    portfolio = _create_codestrata_portfolio(client)
    org_id = portfolio["organization_id"]
    workspace_id = portfolio["workspace_id"]
    portfolio_id = portfolio["portfolio_id"]
    portfolio_snapshot_id = portfolio["portfolio_snapshot_id"]
    scope = {"organization_id": org_id, "workspace_id": workspace_id}

    # Incomplete participation remains bounded.
    snapshot = client.get(
        f"/api/v1/portfolio-snapshots/{portfolio_snapshot_id}",
        params=scope,
    )
    assert snapshot.status_code == 200, snapshot.text
    assert snapshot.json()["snapshot"]["status"] == "completed"
    assert snapshot.json()["envelope"]["selected_repository_count"] >= 3
    assert snapshot.json()["envelope"]["unavailable_repository_count"] == 0

    index = client.post(
        "/api/v1/portfolio-retrieval/indexes",
        json={
            "organization_id": org_id,
            "workspace_id": workspace_id,
            "portfolio_id": portfolio_id,
            "portfolio_snapshot_id": portfolio_snapshot_id,
        },
    )
    assert index.status_code in {200, 201}, index.text
    index_id = index.json()["index_id"]

    portfolio_ask = client.post(
        f"/api/v1/portfolios/{portfolio_id}/ask",
        json={
            "question": "Which repositories should be modernized first?",
            "organization_id": org_id,
            "workspace_id": workspace_id,
            "portfolio_retrieval_index_id": index_id,
        },
    )
    assert portfolio_ask.status_code == 201, portfolio_ask.text
    portfolio_answer = portfolio_ask.json()
    assert portfolio_answer["citations"]
    assert portfolio_answer["confidence_score"] is not None
    assert isinstance(portfolio_answer["limitations"], list)

    ei = client.post(
        f"/api/v1/portfolios/{portfolio_id}/executive-intelligence",
        json={"organization_id": org_id, "workspace_id": workspace_id},
    )
    assert ei.status_code == 201, ei.text
    ei_body = ei.json()
    executive_id = ei_body["summary"]["executive_intelligence_id"]
    assert ei_body["summary"]["status"] == "completed"
    assert ei_body["metrics"]
    assert ei_body["findings"]
    assert isinstance(ei_body["limitations"], list)

    # Idempotent rebuild returns same completed projection.
    ei_again = client.post(
        f"/api/v1/portfolios/{portfolio_id}/executive-intelligence",
        json={"organization_id": org_id, "workspace_id": workspace_id},
    )
    assert ei_again.status_code == 201, ei_again.text
    assert (
        ei_again.json()["summary"]["executive_intelligence_id"] == executive_id
    )

    presentation = client.get(
        f"/api/v1/executive-intelligence/{executive_id}/presentation",
        params=scope,
    )
    assert presentation.status_code == 200, presentation.text
    presentation_body = presentation.json()
    assert "executive_summary" in presentation_body or "identity" in presentation_body

    roadmap = client.get(
        f"/api/v1/executive-intelligence/{executive_id}/roadmap",
        params=scope,
    )
    assert roadmap.status_code == 200, roadmap.text
    roadmap_body = roadmap.json()
    assert roadmap_body["identity"]["executive_intelligence_id"] == executive_id
    assert len(roadmap_body["waves"]) == 4
    finding_ids = {item["finding_id"] for item in ei_body["findings"]}
    recommendation_ids = {item["recommendation_id"] for item in ei_body["recommendations"]}
    for initiative in roadmap_body["initiatives"]:
        assert initiative["depends_on_initiative_ids"] == []
        for finding_id in initiative.get("supporting_finding_ids", []):
            assert finding_id in finding_ids
        for recommendation_id in initiative.get("supporting_recommendation_ids", []):
            assert recommendation_id in recommendation_ids
        # Recommendation-backed initiatives must not invent finding links.
        if initiative.get("supporting_recommendation_ids"):
            assert initiative.get("supporting_finding_ids", []) == []

    # Repeated on-read projections remain identical.
    presentation_2 = client.get(
        f"/api/v1/executive-intelligence/{executive_id}/presentation",
        params=scope,
    )
    roadmap_2 = client.get(
        f"/api/v1/executive-intelligence/{executive_id}/roadmap",
        params=scope,
    )
    assert presentation_2.json() == presentation.json()
    assert [item["initiative_id"] for item in roadmap_2.json()["initiatives"]] == [
        item["initiative_id"] for item in roadmap_body["initiatives"]
    ]


def test_full_platform_dogfood_security_isolation(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_commercial_flags(monkeypatch)
    portfolio = _create_codestrata_portfolio(client)
    org_id = portfolio["organization_id"]
    workspace_id = portfolio["workspace_id"]
    portfolio_id = portfolio["portfolio_id"]

    ei = client.post(
        f"/api/v1/portfolios/{portfolio_id}/executive-intelligence",
        json={"organization_id": org_id, "workspace_id": workspace_id},
    )
    assert ei.status_code == 201, ei.text
    executive_id = ei.json()["summary"]["executive_intelligence_id"]

    other = client.post("/api/v1/organizations", json={"name": "Other Tenant"}).json()
    other_ws = client.post(
        "/api/v1/workspaces",
        json={"organization_id": other["id"], "name": "Isolated"},
    ).json()

    # Cross-tenant reads are indistinguishable 404s.
    for path in (
        f"/api/v1/executive-intelligence/{executive_id}",
        f"/api/v1/executive-intelligence/{executive_id}/presentation",
        f"/api/v1/executive-intelligence/{executive_id}/roadmap",
        f"/api/v1/portfolios/{portfolio_id}/executive-intelligence/latest",
    ):
        response = client.get(
            path,
            params={
                "organization_id": other["id"],
                "workspace_id": other_ws["id"],
            },
        )
        assert response.status_code == 404, (path, response.text)
        assert "traceback" not in response.text.lower()
        assert "postgresql+" not in response.text.lower()

    # Missing/incorrect API key.
    monkeypatch.setenv(PLATFORM_ENV_VAR, "development")
    monkeypatch.setenv(PLATFORM_API_KEY_ENV, "dogfood-api-key")
    locked = create_app(use_memory=True)
    with TestClient(locked) as locked_client:
        denied = locked_client.get("/api/v1/organizations")
        assert denied.status_code == 401
        wrong = locked_client.get(
            "/api/v1/organizations",
            headers={"Authorization": "Bearer wrong-key"},
        )
        assert wrong.status_code == 401
        assert locked_client.get("/health").status_code == 200
        assert locked_client.get("/ready").status_code == 200


def test_full_platform_dogfood_feature_flags_and_observability(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    health = client.get("/health", headers={"X-Request-Id": "dogfood-health"})
    assert health.status_code == 200
    assert health.headers["X-Request-Id"] == "dogfood-health"
    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"

    monkeypatch.delenv("CODESTRATA_EXECUTIVE_INTELLIGENCE_ENABLED", raising=False)
    portfolio = _create_codestrata_portfolio(client)
    disabled = client.post(
        f"/api/v1/portfolios/{portfolio['portfolio_id']}/executive-intelligence",
        json={
            "organization_id": portfolio["organization_id"],
            "workspace_id": portfolio["workspace_id"],
        },
    )
    assert disabled.status_code == 422
    assert disabled.json()["error"]["code"] == "executive_intelligence_disabled"


def test_full_platform_dogfood_performance_repeated_projections(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_commercial_flags(monkeypatch)
    portfolio = _create_codestrata_portfolio(client)
    scope = {
        "organization_id": portfolio["organization_id"],
        "workspace_id": portfolio["workspace_id"],
    }
    ei = client.post(
        f"/api/v1/portfolios/{portfolio['portfolio_id']}/executive-intelligence",
        json=scope,
    )
    assert ei.status_code == 201, ei.text
    executive_id = ei.json()["summary"]["executive_intelligence_id"]

    presentation_times: list[float] = []
    roadmap_times: list[float] = []
    presentation_payloads: list[dict[str, Any]] = []
    roadmap_ids: list[list[str]] = []
    for _ in range(5):
        t0 = time.perf_counter()
        presentation = client.get(
            f"/api/v1/executive-intelligence/{executive_id}/presentation",
            params=scope,
        )
        presentation_times.append(time.perf_counter() - t0)
        assert presentation.status_code == 200
        presentation_payloads.append(presentation.json())

        t1 = time.perf_counter()
        roadmap = client.get(
            f"/api/v1/executive-intelligence/{executive_id}/roadmap",
            params=scope,
        )
        roadmap_times.append(time.perf_counter() - t1)
        assert roadmap.status_code == 200
        roadmap_ids.append(
            [item["initiative_id"] for item in roadmap.json()["initiatives"]]
        )

    assert all(item == presentation_payloads[0] for item in presentation_payloads)
    assert all(item == roadmap_ids[0] for item in roadmap_ids)
    # Soft observation only — no hard SLO.
    assert max(presentation_times) < 5.0
    assert max(roadmap_times) < 5.0


def test_full_platform_dogfood_durable_postgres(
    durable_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PostgreSQL-backed smoke of the repository intelligence path (no SQLite)."""

    _enable_commercial_flags(monkeypatch)
    ctx = _seed_repository_pipeline(durable_client)
    asked = durable_client.post(
        f"/api/v1/repositories/{ctx['repository_id']}/ask",
        json={
            "question": "What security issues require immediate action?",
            "organization_id": ctx["organization_id"],
            "workspace_id": ctx["workspace_id"],
            "retrieval_index_id": ctx["index_id"],
        },
    )
    assert asked.status_code == 201, asked.text
    body = asked.json()
    assert body["status"] == "completed"
    assert body["citations"]

    ready = durable_client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["checks"]["persistence"] == "ok"
    assert "password" not in str(ready.json()).lower()
