"""API tests for Engineering Knowledge Graph endpoints."""

from __future__ import annotations

import hashlib
import json

from fastapi.testclient import TestClient


def _checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _seed_published_snapshot(client: TestClient) -> tuple[str, str]:
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
            "repository_url": "https://github.com/acme/app",
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
                    "finding_id": "finding:api",
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
            "engine_assessment_id": "engine-assessment:1",
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
    processed = client.post(f"/api/v1/ingestion/assessments/{assessment_id}/intelligence")
    assert processed.status_code == 201
    built = client.post(
        "/api/v1/engineering/snapshots",
        json={"assessment_id": assessment_id, "publish": True},
    )
    assert built.status_code == 201
    return repo["id"], built.json()["snapshot_id"]


def test_knowledge_graph_api_flow(client: TestClient) -> None:
    repository_id, snapshot_id = _seed_published_snapshot(client)

    created = client.post(
        "/api/v1/knowledge-graphs",
        json={"snapshot_id": snapshot_id},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "completed"
    assert body["created"] is True
    graph_id = body["graph_id"]

    again = client.post(
        "/api/v1/knowledge-graphs",
        json={"snapshot_id": snapshot_id},
    )
    assert again.status_code == 200
    assert again.json()["idempotent"] is True

    details = client.get(f"/api/v1/knowledge-graphs/{graph_id}")
    assert details.status_code == 200

    latest = client.get(f"/api/v1/repositories/{repository_id}/knowledge-graphs/latest")
    assert latest.status_code == 200
    assert latest.json()["graph_id"] == graph_id

    listed = client.get(f"/api/v1/repositories/{repository_id}/knowledge-graphs")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    nodes = client.get(
        f"/api/v1/knowledge-graphs/{graph_id}/nodes",
        params={"node_type": "technology"},
    )
    assert nodes.status_code == 200
    assert any(item["canonical_id"] == "docker" for item in nodes.json())

    edges = client.get(f"/api/v1/knowledge-graphs/{graph_id}/edges")
    assert edges.status_code == 200
    assert edges.json()

    all_nodes = client.get(f"/api/v1/knowledge-graphs/{graph_id}/nodes").json()
    repo_node = next(item for item in all_nodes if item["node_type"] == "repository")
    tech_node = next(item for item in all_nodes if item["node_type"] == "technology")

    neighbors = client.get(
        f"/api/v1/knowledge-graphs/{graph_id}/nodes/{repo_node['node_id']}/neighbors"
    )
    assert neighbors.status_code == 200
    assert neighbors.json()

    paths = client.post(
        f"/api/v1/knowledge-graphs/{graph_id}/paths",
        json={
            "source_node_id": repo_node["node_id"],
            "target_node_id": tech_node["node_id"],
            "max_depth": 4,
        },
    )
    assert paths.status_code == 200
    assert paths.json()

    rejected = client.post(
        f"/api/v1/knowledge-graphs/{graph_id}/paths",
        json={
            "source_node_id": repo_node["node_id"],
            "target_node_id": tech_node["node_id"],
            "max_depth": 11,
        },
    )
    assert rejected.status_code == 422


def test_knowledge_graph_auto_project_disabled_by_default(client: TestClient) -> None:
    repository_id, _snapshot_id = _seed_published_snapshot(client)
    listed = client.get(f"/api/v1/repositories/{repository_id}/knowledge-graphs")
    assert listed.status_code == 200
    assert listed.json() == []
