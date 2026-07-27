"""API tests for Engineering Retrieval endpoints."""

from __future__ import annotations

import hashlib
import json

from fastapi.testclient import TestClient


def _checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _seed_graph(client: TestClient) -> tuple[str, str, str]:
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
            "repository_url": "https://github.com/acme/app-retrieval",
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
    snapshot_id = built.json()["snapshot_id"]
    graph = client.post("/api/v1/knowledge-graphs", json={"snapshot_id": snapshot_id})
    assert graph.status_code == 201
    return repo["id"], snapshot_id, graph.json()["graph_id"]


def test_retrieval_api_flow(client: TestClient) -> None:
    repository_id, snapshot_id, graph_id = _seed_graph(client)

    created = client.post(
        "/api/v1/retrieval/indexes",
        json={"snapshot_id": snapshot_id, "graph_id": graph_id},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["status"] == "completed"
    index_id = body["index_id"]
    assert body["document_count"] >= 1
    assert body["chunk_count"] >= 1

    again = client.post(
        "/api/v1/retrieval/indexes",
        json={"snapshot_id": snapshot_id, "graph_id": graph_id},
    )
    assert again.status_code == 200
    assert again.json()["index_id"] == index_id

    details = client.get(f"/api/v1/retrieval/indexes/{index_id}")
    assert details.status_code == 200

    latest = client.get(f"/api/v1/repositories/{repository_id}/retrieval-indexes/latest")
    assert latest.status_code == 200
    assert latest.json()["index_id"] == index_id

    listed = client.get(f"/api/v1/repositories/{repository_id}/retrieval-indexes")
    assert listed.status_code == 200
    assert len(listed.json()) >= 1

    documents = client.get(f"/api/v1/retrieval/indexes/{index_id}/documents")
    assert documents.status_code == 200
    docs = documents.json()
    assert docs
    document_id = docs[0]["document_id"]
    assert client.get(
        f"/api/v1/retrieval/indexes/{index_id}/documents/{document_id}"
    ).status_code == 200

    search = client.post(
        f"/api/v1/retrieval/indexes/{index_id}/search",
        json={"query_text": "privileged container", "mode": "hybrid", "top_k": 5},
    )
    assert search.status_code == 200, search.text
    hits = search.json()["hits"]
    assert hits
    assert "final_score" in hits[0]["score"]
    assert "embedding" not in hits[0]

    chunk_id = hits[0]["chunk_id"]
    chunk = client.get(f"/api/v1/retrieval/indexes/{index_id}/chunks/{chunk_id}")
    assert chunk.status_code == 200
    assert "has_embedding" in chunk.json()

    context = client.post(
        f"/api/v1/retrieval/indexes/{index_id}/context",
        json={"query_text": "privileged container", "top_k": 5, "max_tokens": 2000},
    )
    assert context.status_code == 200
    assert context.json()["items"]

    stats = client.get(f"/api/v1/retrieval/indexes/{index_id}/statistics")
    assert stats.status_code == 200
    assert stats.json()["embedded_chunk_count"] >= 1


def test_retrieval_rejects_blank_query_and_excessive_top_k(client: TestClient) -> None:
    _, snapshot_id, graph_id = _seed_graph(client)
    created = client.post(
        "/api/v1/retrieval/indexes",
        json={"snapshot_id": snapshot_id, "graph_id": graph_id},
    )
    index_id = created.json()["index_id"]
    blank = client.post(
        f"/api/v1/retrieval/indexes/{index_id}/search",
        json={"query_text": "   "},
    )
    assert blank.status_code in {400, 422}
    too_large = client.post(
        f"/api/v1/retrieval/indexes/{index_id}/search",
        json={"query_text": "docker", "top_k": 101},
    )
    assert too_large.status_code in {400, 422}
