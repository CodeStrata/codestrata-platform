"""API tests for graph intelligence endpoints."""

from __future__ import annotations

import hashlib
import json

from fastapi.testclient import TestClient


def _checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _seed_graph(client: TestClient) -> tuple[str, str]:
    org = client.post("/api/v1/organizations", json={"name": "Acme"}).json()
    workspace = client.post(
        "/api/v1/workspaces",
        json={"organization_id": org["id"], "name": "Default"},
    ).json()
    repo = client.post(
        "/api/v1/repositories",
        json={
            "workspace_id": workspace["id"],
            "organization_id": org["id"],
            "display_name": "App",
            "provider": "github",
            "repository_url": "https://github.com/acme/app-gi",
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
                    "finding_id": "finding:gi",
                    "rule_id": "rule.docker.hardening",
                    "title": "Privileged container",
                    "summary": "Container runs privileged.",
                    "category": "security",
                    "severity": "critical",
                    "confidence": 0.95,
                    "metadata": {"technology": "Docker"},
                    "evidence": [{"path": "deploy/compose.yml", "line_start": 4}],
                }
            ]
        }
    ).encode("utf-8")
    checksum = _checksum(content)
    registered = client.post(
        f"/api/v1/ingestion/assessments/{assessment_id}/artifacts",
        json={
            "engine_assessment_id": "engine-assessment:gi",
            "artifact_type": "findings",
            "format": "json",
            "schema_version": "1.0",
            "checksum": checksum,
            "size_bytes": len(content),
        },
    )
    artifact_id = registered.json()["artifact_id"]
    client.put(
        f"/api/v1/ingestion/assessments/{assessment_id}/artifacts/{artifact_id}",
        content=content,
        headers={"Content-Type": "application/json", "X-CodeStrata-Checksum": checksum},
    )
    client.post(
        f"/api/v1/ingestion/assessments/{assessment_id}/artifacts/{artifact_id}/complete"
    )
    assert client.post(
        f"/api/v1/ingestion/assessments/{assessment_id}/intelligence"
    ).status_code == 201
    snapshot = client.post(
        "/api/v1/engineering/snapshots",
        json={"assessment_id": assessment_id, "publish": True},
    ).json()
    graph = client.post(
        "/api/v1/knowledge-graphs",
        json={"snapshot_id": snapshot["snapshot_id"]},
    ).json()
    return repo["id"], graph["graph_id"]


def test_graph_intelligence_api_flow(client: TestClient) -> None:
    repository_id, graph_id = _seed_graph(client)

    overview = client.get(f"/api/v1/repositories/{repository_id}/engineering-overview")
    assert overview.status_code == 200
    assert overview.json()["graph_id"] == graph_id
    assert overview.json()["integrity_passed"] is True

    coverage = client.get(f"/api/v1/knowledge-graphs/{graph_id}/coverage")
    assert coverage.status_code == 200
    assert coverage.json()["findings_with_evidence"]["denominator"] == 1

    risks = client.get(f"/api/v1/knowledge-graphs/{graph_id}/risks")
    assert risks.status_code == 200

    deps = client.get(f"/api/v1/knowledge-graphs/{graph_id}/dependencies")
    assert deps.status_code == 200

    integrity = client.get(f"/api/v1/knowledge-graphs/{graph_id}/integrity")
    assert integrity.status_code == 200
    assert integrity.json()["passed"] is True

    recommendations = client.get(
        f"/api/v1/knowledge-graphs/{graph_id}/recommendation-analysis"
    )
    assert recommendations.status_code == 200

    nodes = client.get(f"/api/v1/knowledge-graphs/{graph_id}/nodes").json()
    finding = next(item for item in nodes if item["node_type"] == "finding")
    evidence = next(item for item in nodes if item["node_type"] == "evidence")
    technology = next(item for item in nodes if item["node_type"] == "technology")
    recommendation = next(
        (item for item in nodes if item["node_type"] == "recommendation"),
        None,
    )

    finding_impact = client.post(
        f"/api/v1/knowledge-graphs/{graph_id}/impact/findings/{finding['node_id']}",
        json={"max_depth": 4, "include_diagnostics": True},
    )
    assert finding_impact.status_code == 200
    assert "contributing_factors" in finding_impact.json()
    assert finding_impact.json()["policy_version"]

    tech_impact = client.post(
        f"/api/v1/knowledge-graphs/{graph_id}/impact/technologies/{technology['node_id']}",
        json={"direction": "both"},
    )
    assert tech_impact.status_code == 200

    rejected = client.post(
        f"/api/v1/knowledge-graphs/{graph_id}/impact/findings/{finding['node_id']}",
        json={"max_depth": 11},
    )
    assert rejected.status_code == 422

    trace = client.get(
        f"/api/v1/knowledge-graphs/{graph_id}/traceability/findings/{finding['node_id']}"
    )
    assert trace.status_code == 200
    assert trace.json()["related"]["evidence"]

    evidence_trace = client.get(
        f"/api/v1/knowledge-graphs/{graph_id}/traceability/evidence/{evidence['node_id']}"
    )
    assert evidence_trace.status_code == 200

    if recommendation is not None:
        rec_trace = client.get(
            "/api/v1/knowledge-graphs/"
            f"{graph_id}/traceability/recommendations/{recommendation['node_id']}"
        )
        assert rec_trace.status_code == 200

    graph_overview = client.get(f"/api/v1/knowledge-graphs/{graph_id}/overview")
    assert graph_overview.status_code == 200
