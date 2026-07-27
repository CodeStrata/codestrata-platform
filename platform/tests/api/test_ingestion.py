"""Platform ingestion API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _seed(client: TestClient) -> tuple[dict, dict]:
    org = client.post("/api/v1/organizations", json={"name": "Acme"}).json()
    workspace = client.post(
        "/api/v1/workspaces",
        json={"organization_id": org["id"], "name": "Engineering"},
    ).json()
    return org, workspace


def test_ingestion_register_lookup_and_assessment_lifecycle(client: TestClient) -> None:
    org, workspace = _seed(client)
    registered = client.post(
        "/api/v1/ingestion/repositories",
        json={
            "organization_id": org["id"],
            "workspace_id": workspace["id"],
            "display_name": "Petclinic",
            "provider": "github",
            "repository_url": "https://github.com/acme/petclinic",
            "engine_repository_id": "engine-repo-1",
        },
    )
    assert registered.status_code == 201
    body = registered.json()
    assert body["created"] is True

    again = client.post(
        "/api/v1/ingestion/repositories",
        json={
            "organization_id": org["id"],
            "workspace_id": workspace["id"],
            "display_name": "Petclinic",
            "provider": "github",
            "repository_url": "https://github.com/acme/petclinic/",
        },
    )
    assert again.status_code == 201
    assert again.json()["created"] is False
    assert again.json()["repository_id"] == body["repository_id"]

    lookup = client.get(
        "/api/v1/ingestion/repositories/lookup",
        params={
            "workspace_id": workspace["id"],
            "repository_url": "https://github.com/acme/petclinic",
        },
    )
    assert lookup.status_code == 200

    assessment = client.post(
        "/api/v1/ingestion/assessments",
        json={
            "repository_id": body["repository_id"],
            "workspace_id": workspace["id"],
            "engine_assessment_id": "engine-assessment:abc123",
            "engine_version": "0.1.0",
            "assessment_version": "1.2.0",
            "technology_summary": "Java, Spring",
        },
    )
    assert assessment.status_code == 201
    assessment_id = assessment.json()["assessment_id"]
    assert assessment.json()["engine_assessment_id"] == "engine-assessment:abc123"

    started = client.post(f"/api/v1/ingestion/assessments/{assessment_id}/start")
    assert started.status_code == 200
    assert started.json()["status"] == "running"

    completed = client.post(
        f"/api/v1/ingestion/assessments/{assessment_id}/complete",
        json={
            "generated_reports": [
                {"report_type": "html", "location": "/tmp/report.html"},
            ]
        },
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "succeeded"
