"""Exception mapping unit coverage."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_archive_organization_and_workspace(client: TestClient) -> None:
    org = client.post("/api/v1/organizations", json={"name": "Temp"}).json()
    workspace = client.post(
        "/api/v1/workspaces",
        json={"organization_id": org["id"], "name": "WS"},
    ).json()

    archived_ws = client.delete(f"/api/v1/workspaces/{workspace['id']}").json()
    assert archived_ws["status"] == "inactive"

    archived_org = client.delete(f"/api/v1/organizations/{org['id']}").json()
    assert archived_org["status"] == "inactive"


def test_list_organization_workspaces(client: TestClient) -> None:
    org = client.post("/api/v1/organizations", json={"name": "Org"}).json()
    client.post(
        "/api/v1/workspaces",
        json={"organization_id": org["id"], "name": "One"},
    )
    response = client.get(f"/api/v1/organizations/{org['id']}/workspaces")
    assert response.status_code == 200
    body = response.json()
    assert body["pagination"]["total"] == 1
    assert body["items"][0]["name"] == "One"
