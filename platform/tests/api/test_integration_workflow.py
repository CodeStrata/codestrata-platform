"""End-to-end REST workflow covering Organization → Assessment history."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_full_commercial_platform_workflow(client: TestClient) -> None:
    org = client.post("/api/v1/organizations", json={"name": "Acme"}).json()
    assert org["name"] == "Acme"
    assert org["status"] == "active"

    workspace = client.post(
        "/api/v1/workspaces",
        json={
            "organization_id": org["id"],
            "name": "Engineering",
            "description": "Primary",
        },
    ).json()
    assert workspace["organization_id"] == org["id"]

    repository = client.post(
        "/api/v1/repositories",
        json={
            "workspace_id": workspace["id"],
            "organization_id": org["id"],
            "display_name": "Petclinic",
            "provider": "github",
            "repository_url": "https://github.com/acme/petclinic",
            "visibility": "private",
            "metadata": {"tier": "critical"},
        },
    ).json()
    assert repository["display_name"] == "Petclinic"
    assert repository["metadata"]["tier"] == "critical"

    renamed = client.patch(
        f"/api/v1/repositories/{repository['id']}",
        json={"display_name": "Petclinic Core"},
    ).json()
    assert renamed["display_name"] == "Petclinic Core"

    archived = client.delete(f"/api/v1/repositories/{repository['id']}").json()
    assert archived["status"] == "archived"

    # Re-register after archive for assessment flow.
    repository2 = client.post(
        "/api/v1/repositories",
        json={
            "workspace_id": workspace["id"],
            "organization_id": org["id"],
            "display_name": "Petclinic",
            "provider": "github",
            "repository_url": "https://github.com/acme/petclinic",
        },
    ).json()

    assessment = client.post(
        "/api/v1/assessments",
        json={
            "repository_id": repository2["id"],
            "workspace_id": workspace["id"],
            "engine_version": "1.2.3",
            "assessment_version": "0.1.0",
        },
    ).json()
    assert assessment["status"] == "pending"

    started = client.post(f"/api/v1/assessments/{assessment['id']}/start").json()
    assert started["status"] == "running"

    completed = client.post(
        f"/api/v1/assessments/{assessment['id']}/complete",
        json={
            "generated_reports": [
                {"report_type": "html", "location": "/tmp/report.html"},
            ]
        },
    ).json()
    assert completed["status"] == "succeeded"
    assert completed["report_count"] == 1

    history = client.get(f"/api/v1/repositories/{repository2['id']}/assessments").json()
    assert len(history) == 1
    assert history[0]["id"] == assessment["id"]

    listed = client.get(
        "/api/v1/repositories",
        params={"workspace_id": workspace["id"], "status": "active"},
    ).json()
    assert listed["pagination"]["total"] == 1


def test_durable_postgres_workflow(durable_client: TestClient) -> None:
    org = durable_client.post("/api/v1/organizations", json={"name": "Durable"}).json()
    workspace = durable_client.post(
        "/api/v1/workspaces",
        json={"organization_id": org["id"], "name": "WS"},
    ).json()
    repo = durable_client.post(
        "/api/v1/repositories",
        json={
            "workspace_id": workspace["id"],
            "organization_id": org["id"],
            "display_name": "App",
            "provider": "github",
            "repository_url": "https://github.com/acme/app",
        },
    ).json()
    fetched = durable_client.get(f"/api/v1/repositories/{repo['id']}").json()
    assert fetched["id"] == repo["id"]
