"""API tests for Strategic Portfolio Roadmap endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from .test_executive_intelligence import _build_portfolio_with_snapshot


def _enable_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODESTRATA_EXECUTIVE_INTELLIGENCE_ENABLED", "true")
    monkeypatch.setenv("CODESTRATA_STRATEGIC_ROADMAP_ENABLED", "true")


def _build_executive(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[str, str, str, str, str]:
    _enable_flags(monkeypatch)
    org_id, workspace_id, portfolio_id = _build_portfolio_with_snapshot(client)
    built = client.post(
        f"/api/v1/portfolios/{portfolio_id}/executive-intelligence",
        json={"organization_id": org_id, "workspace_id": workspace_id},
    )
    assert built.status_code == 201, built.text
    payload = built.json()
    return (
        org_id,
        workspace_id,
        portfolio_id,
        payload["summary"]["executive_intelligence_id"],
        payload["summary"]["portfolio_snapshot_id"],
    )


def test_roadmap_requires_feature_flag(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CODESTRATA_EXECUTIVE_INTELLIGENCE_ENABLED", "true")
    monkeypatch.delenv("CODESTRATA_STRATEGIC_ROADMAP_ENABLED", raising=False)
    org_id, workspace_id, portfolio_id = _build_portfolio_with_snapshot(client)
    built = client.post(
        f"/api/v1/portfolios/{portfolio_id}/executive-intelligence",
        json={"organization_id": org_id, "workspace_id": workspace_id},
    )
    assert built.status_code == 201, built.text
    executive_id = built.json()["summary"]["executive_intelligence_id"]
    response = client.get(f"/api/v1/executive-intelligence/{executive_id}/roadmap")
    assert response.status_code == 422, response.text


def test_roadmap_full_route_flow(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    org_id, workspace_id, portfolio_id, executive_id, portfolio_snapshot_id = _build_executive(
        client, monkeypatch
    )

    full = client.get(f"/api/v1/executive-intelligence/{executive_id}/roadmap")
    assert full.status_code == 200, full.text
    payload = full.json()
    assert payload["identity"]["executive_intelligence_id"] == executive_id
    assert "initiative_count" in payload["summary"]
    assert isinstance(payload["initiatives"], list)
    assert len(payload["waves"]) == 4
    assert payload["limitations"] == payload["summary"]["limitations"]

    initiatives = client.get(
        f"/api/v1/executive-intelligence/{executive_id}/roadmap/initiatives"
    )
    assert initiatives.status_code == 200, initiatives.text
    assert initiatives.json()["total"] == len(initiatives.json()["initiatives"])

    if initiatives.json()["initiatives"]:
        category = initiatives.json()["initiatives"][0]["category"]
        filtered = client.get(
            f"/api/v1/executive-intelligence/{executive_id}/roadmap/initiatives",
            params={"category": category},
        )
        assert filtered.status_code == 200, filtered.text
        assert all(item["category"] == category for item in filtered.json()["initiatives"])

    waves = client.get(f"/api/v1/executive-intelligence/{executive_id}/roadmap/waves")
    assert waves.status_code == 200, waves.text
    assert len(waves.json()["waves"]) == 4

    summary = client.get(f"/api/v1/executive-intelligence/{executive_id}/roadmap/summary")
    assert summary.status_code == 200, summary.text
    assert "initiative_count" in summary.json()["summary"]

    latest = client.get(
        f"/api/v1/portfolios/{portfolio_id}/roadmap/latest",
        params={"organization_id": org_id, "workspace_id": workspace_id},
    )
    assert latest.status_code == 200, latest.text

    by_snapshot = client.get(
        f"/api/v1/portfolio-snapshots/{portfolio_snapshot_id}/roadmap",
        params={"organization_id": org_id, "workspace_id": workspace_id},
    )
    assert by_snapshot.status_code == 200, by_snapshot.text


def test_missing_roadmap_source_returns_404(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_flags(monkeypatch)
    response = client.get("/api/v1/executive-intelligence/exec:missing/roadmap")
    assert response.status_code == 404, response.text
