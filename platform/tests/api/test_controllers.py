"""Controller validation, pagination, and error mapping tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _seed_org_workspace(client: TestClient) -> tuple[dict, dict]:
    org = client.post("/api/v1/organizations", json={"name": "Org"}).json()
    workspace = client.post(
        "/api/v1/workspaces",
        json={"organization_id": org["id"], "name": "WS"},
    ).json()
    return org, workspace


def test_validation_rejects_empty_organization_name(client: TestClient) -> None:
    response = client.post("/api/v1/organizations", json={"name": ""})
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "request_validation_error"
    assert "traceback" not in body["error"]["message"].lower()


def test_validation_rejects_invalid_repository_url(client: TestClient) -> None:
    org, workspace = _seed_org_workspace(client)
    response = client.post(
        "/api/v1/repositories",
        json={
            "workspace_id": workspace["id"],
            "organization_id": org["id"],
            "display_name": "App",
            "provider": "github",
            "repository_url": "not-a-url",
        },
    )
    assert response.status_code == 422


def test_duplicate_repository_returns_409(client: TestClient) -> None:
    org, workspace = _seed_org_workspace(client)
    payload = {
        "workspace_id": workspace["id"],
        "organization_id": org["id"],
        "display_name": "App",
        "provider": "github",
        "repository_url": "https://github.com/acme/app",
    }
    assert client.post("/api/v1/repositories", json=payload).status_code == 201
    response = client.post("/api/v1/repositories", json=payload)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "duplicate_repository_url"


def test_missing_resource_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/organizations/org:does-not-exist")
    assert response.status_code == 404


def test_ownership_mismatch_returns_422(client: TestClient) -> None:
    org_a = client.post("/api/v1/organizations", json={"name": "A"}).json()
    org_b = client.post("/api/v1/organizations", json={"name": "B"}).json()
    workspace = client.post(
        "/api/v1/workspaces",
        json={"organization_id": org_a["id"], "name": "WS"},
    ).json()
    response = client.post(
        "/api/v1/repositories",
        json={
            "workspace_id": workspace["id"],
            "organization_id": org_b["id"],
            "display_name": "App",
            "provider": "github",
            "repository_url": "https://github.com/acme/app",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "workspace_organization_mismatch"


def test_pagination_metadata(client: TestClient) -> None:
    org, workspace = _seed_org_workspace(client)
    for index in range(3):
        client.post(
            "/api/v1/repositories",
            json={
                "workspace_id": workspace["id"],
                "organization_id": org["id"],
                "display_name": f"App {index}",
                "provider": "github",
                "repository_url": f"https://github.com/acme/app-{index}",
            },
        )
    response = client.get(
        "/api/v1/repositories",
        params={"workspace_id": workspace["id"], "page": 2, "size": 1, "sort": "name"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["pagination"]["page"] == 2
    assert body["pagination"]["size"] == 1
    assert body["pagination"]["total"] == 3
    assert body["pagination"]["next"] == 3
    assert body["pagination"]["previous"] == 1
    assert body["pagination"]["sort"] == "name"
    assert len(body["items"]) == 1


def test_empty_patch_rejected(client: TestClient) -> None:
    org, _workspace = _seed_org_workspace(client)
    response = client.patch(f"/api/v1/organizations/{org['id']}", json={})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "empty_patch"
