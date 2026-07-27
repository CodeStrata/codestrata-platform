"""API tests for Canonical Engineering Intelligence."""

from __future__ import annotations

import hashlib
import json

from fastapi.testclient import TestClient


def _checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _seed_assessment(client: TestClient) -> str:
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
    return assessment["id"]


def _publish(client: TestClient, assessment_id: str, artifact_type: str, payload: object) -> None:
    content = json.dumps(payload).encode("utf-8")
    checksum = _checksum(content)
    registered = client.post(
        f"/api/v1/ingestion/assessments/{assessment_id}/artifacts",
        json={
            "engine_assessment_id": "engine-assessment:1",
            "artifact_type": artifact_type,
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


def test_engineering_api_flow(client: TestClient) -> None:
    assessment_id = _seed_assessment(client)
    _publish(
        client,
        assessment_id,
        "findings",
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
        },
    )
    _publish(
        client,
        assessment_id,
        "assessment_summary",
        {"metrics": {"security.findings.critical": 1}},
    )
    processed = client.post(f"/api/v1/ingestion/assessments/{assessment_id}/intelligence")
    assert processed.status_code == 201

    built = client.post(
        "/api/v1/engineering/snapshots",
        json={"assessment_id": assessment_id, "publish": True},
    )
    assert built.status_code == 201
    body = built.json()
    assert body["status"] == "published"
    assert body["finding_count"] == 1
    snapshot_id = body["snapshot_id"]

    listed = client.get(
        "/api/v1/engineering/snapshots",
        params={"assessment_id": assessment_id},
    )
    assert listed.status_code == 200
    assert listed.json()[0]["snapshot_id"] == snapshot_id

    details = client.get(f"/api/v1/engineering/snapshots/{snapshot_id}")
    assert details.status_code == 200

    technologies = client.get(
        "/api/v1/engineering/technologies",
        params={"assessment_id": assessment_id},
    )
    assert technologies.status_code == 200
    assert any(item["canonical_key"] == "docker" for item in technologies.json())

    findings = client.get(
        "/api/v1/engineering/findings",
        params={"assessment_id": assessment_id},
    )
    assert findings.status_code == 200
    assert findings.json()[0]["severity"] == "critical"

    metrics = client.get(
        "/api/v1/engineering/metrics",
        params={"assessment_id": assessment_id},
    )
    assert metrics.status_code == 200
    assert len(metrics.json()) == 1

    recommendations = client.get(
        "/api/v1/engineering/recommendations",
        params={"assessment_id": assessment_id},
    )
    assert recommendations.status_code == 200
