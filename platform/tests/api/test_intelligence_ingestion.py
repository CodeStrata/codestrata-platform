"""API tests for assessment intelligence ingestion and queries."""

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


def _publish_json_artifact(
    client: TestClient,
    *,
    assessment_id: str,
    artifact_type: str,
    payload: object,
) -> str:
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
    assert registered.status_code in (200, 201)
    artifact_id = registered.json()["artifact_id"]
    upload = client.put(
        f"/api/v1/ingestion/assessments/{assessment_id}/artifacts/{artifact_id}",
        content=content,
        headers={
            "Content-Type": "application/json",
            "X-CodeStrata-Checksum": checksum,
        },
    )
    assert upload.status_code == 200
    complete = client.post(
        f"/api/v1/ingestion/assessments/{assessment_id}/artifacts/{artifact_id}/complete"
    )
    assert complete.status_code == 200
    return artifact_id


def test_intelligence_process_query_and_idempotent(client: TestClient) -> None:
    assessment_id = _seed_assessment(client)
    _publish_json_artifact(
        client,
        assessment_id=assessment_id,
        artifact_type="findings",
        payload={
            "findings": [
                {
                    "finding_id": "finding:api-1",
                    "rule_id": "rule.security.token",
                    "title": "Hard-coded token",
                    "summary": "Token found in source.",
                    "category": "security",
                    "severity": "critical",
                    "confidence": 0.95,
                    "evidence": [{"path": "src/auth.py", "line_start": 4}],
                }
            ]
        },
    )
    _publish_json_artifact(
        client,
        assessment_id=assessment_id,
        artifact_type="assessment_summary",
        payload={"metrics": {"security.findings.critical": 1}},
    )
    _publish_json_artifact(
        client,
        assessment_id=assessment_id,
        artifact_type="report_json",
        payload={
            "recommendations": [
                {
                    "recommendation_id": "rec:api-1",
                    "title": "Rotate secrets",
                    "rationale": "Remove hard-coded credentials.",
                    "priority": "high",
                    "category": "security",
                    "related_finding_ids": ["finding:api-1"],
                    "dependencies": [],
                }
            ]
        },
    )

    processed = client.post(f"/api/v1/ingestion/assessments/{assessment_id}/intelligence")
    assert processed.status_code == 201
    body = processed.json()
    assert body["status"] == "completed"
    assert body["finding_count"] == 1
    assert body["metric_count"] == 1
    assert body["recommendation_count"] == 1
    assert body["created"] is True

    again = client.post(f"/api/v1/ingestion/assessments/{assessment_id}/intelligence/process")
    assert again.status_code == 200
    assert again.json()["idempotent"] is True
    assert again.json()["intelligence_id"] == body["intelligence_id"]

    latest = client.get(f"/api/v1/ingestion/assessments/{assessment_id}/intelligence")
    assert latest.status_code == 200
    assert latest.json()["intelligence_id"] == body["intelligence_id"]

    findings = client.get(f"/api/v1/assessments/{assessment_id}/findings")
    assert findings.status_code == 200
    assert len(findings.json()) == 1
    assert findings.json()[0]["severity"] == "critical"

    filtered = client.get(
        f"/api/v1/assessments/{assessment_id}/findings",
        params={"severity": "low"},
    )
    assert filtered.status_code == 200
    assert filtered.json() == []

    finding = client.get(f"/api/v1/assessments/{assessment_id}/findings/finding:api-1")
    assert finding.status_code == 200
    assert finding.json()["title"] == "Hard-coded token"
    assert finding.json()["evidence_references"][0]["path_reference"] == "src/auth.py"

    metrics = client.get(f"/api/v1/assessments/{assessment_id}/metrics")
    assert metrics.status_code == 200
    assert metrics.json()[0]["name"] == "assessment.security.findings.critical"

    recommendations = client.get(f"/api/v1/assessments/{assessment_id}/recommendations")
    assert recommendations.status_code == 200
    assert recommendations.json()[0]["recommendation_id"] == "rec:api-1"

    recommendation = client.get(
        f"/api/v1/assessments/{assessment_id}/recommendations/rec:api-1"
    )
    assert recommendation.status_code == 200
    assert recommendation.json()["title"] == "Rotate secrets"


def test_intelligence_missing_artifacts_is_sanitized(client: TestClient) -> None:
    assessment_id = _seed_assessment(client)
    response = client.post(f"/api/v1/ingestion/assessments/{assessment_id}/intelligence")
    assert response.status_code == 422
    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == "no_completed_artifacts"
    assert "traceback" not in json.dumps(body).lower()


def test_intelligence_malformed_artifact_fails_cleanly(client: TestClient) -> None:
    assessment_id = _seed_assessment(client)
    _publish_json_artifact(
        client,
        assessment_id=assessment_id,
        artifact_type="findings",
        payload={"findings": [{"metadata": {"password": "secret-value"}}]},
    )
    response = client.post(f"/api/v1/ingestion/assessments/{assessment_id}/intelligence")
    assert response.status_code == 422
    body = response.json()
    assert "error" in body
    assert "secret-value" not in json.dumps(body)


def test_durable_intelligence_processing(durable_client: TestClient) -> None:
    assessment_id = _seed_assessment(durable_client)
    _publish_json_artifact(
        durable_client,
        assessment_id=assessment_id,
        artifact_type="findings",
        payload={
            "findings": [
                {
                    "finding_id": "finding:durable",
                    "rule_id": "rule.x",
                    "title": "Durable finding",
                    "summary": "Stored in PostgreSQL.",
                    "category": "architecture",
                    "severity": "medium",
                }
            ]
        },
    )
    processed = durable_client.post(
        f"/api/v1/ingestion/assessments/{assessment_id}/intelligence/process"
    )
    assert processed.status_code == 201
    findings = durable_client.get(f"/api/v1/assessments/{assessment_id}/findings")
    assert findings.status_code == 200
    assert findings.json()[0]["finding_id"] == "finding:durable"
