"""API tests for Engineering Answering endpoints."""

from __future__ import annotations

import hashlib
import json

import pytest
from fastapi.testclient import TestClient


def _checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _seed_retrieval(client: TestClient) -> tuple[str, str, str, str]:
    org = client.post("/api/v1/organizations", json={"name": "Acme Answer"}).json()
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
            "repository_url": "https://github.com/acme/app-answer",
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
    assert client.post(
        f"/api/v1/ingestion/assessments/{assessment_id}/intelligence"
    ).status_code == 201
    built = client.post(
        "/api/v1/engineering/snapshots",
        json={"assessment_id": assessment_id, "publish": True},
    )
    snapshot_id = built.json()["snapshot_id"]
    graph = client.post("/api/v1/knowledge-graphs", json={"snapshot_id": snapshot_id})
    index = client.post(
        "/api/v1/retrieval/indexes",
        json={"snapshot_id": snapshot_id, "graph_id": graph.json()["graph_id"]},
    )
    assert index.status_code == 201, index.text
    return org["id"], workspace["id"], repo["id"], index.json()["index_id"]


def test_answering_api_flow(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODESTRATA_ANSWERING_ENABLED", "true")
    monkeypatch.setenv("CODESTRATA_LLM_PROVIDER", "deterministic")
    org_id, workspace_id, repository_id, index_id = _seed_retrieval(client)

    asked = client.post(
        f"/api/v1/repositories/{repository_id}/ask",
        json={
            "question": "What are the highest-risk findings?",
            "organization_id": org_id,
            "workspace_id": workspace_id,
            "retrieval_index_id": index_id,
        },
    )
    assert asked.status_code == 201, asked.text
    body = asked.json()
    assert body["answer"]
    assert body["citations"]
    assert body["status"] == "completed"
    answer_run_id = body["answer_run_id"]

    got = client.get(
        f"/api/v1/answers/{answer_run_id}",
        params={"organization_id": org_id, "workspace_id": workspace_id},
    )
    assert got.status_code == 200
    listed = client.get(
        f"/api/v1/repositories/{repository_id}/answers",
        params={"organization_id": org_id, "workspace_id": workspace_id},
    )
    assert listed.status_code == 200
    assert listed.json()
    feedback = client.post(
        f"/api/v1/answers/{answer_run_id}/feedback",
        params={"organization_id": org_id, "workspace_id": workspace_id},
        json={"rating": 5, "feedback_category": "helpful", "comment": "useful"},
    )
    assert feedback.status_code in {200, 201}


def test_answering_disabled_returns_error(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CODESTRATA_ANSWERING_ENABLED", "false")
    org_id, workspace_id, repository_id, index_id = _seed_retrieval(client)
    response = client.post(
        f"/api/v1/repositories/{repository_id}/ask",
        json={
            "question": "What are the highest-risk findings?",
            "organization_id": org_id,
            "workspace_id": workspace_id,
            "retrieval_index_id": index_id,
        },
    )
    assert response.status_code in {400, 422}


def test_get_answer_requires_scope_params(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CODESTRATA_ANSWERING_ENABLED", "true")
    response = client.get("/api/v1/answers/answer-run:missing")
    assert response.status_code == 422, response.text
