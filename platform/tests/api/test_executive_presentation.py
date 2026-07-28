"""API tests for Executive Presentation endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from .test_executive_intelligence import _build_portfolio_with_snapshot


def _enable_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODESTRATA_EXECUTIVE_INTELLIGENCE_ENABLED", "true")
    monkeypatch.setenv("CODESTRATA_EXECUTIVE_PRESENTATION_ENABLED", "true")


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
    executive_id = built.json()["summary"]["executive_intelligence_id"]
    portfolio_snapshot_id = built.json()["summary"]["portfolio_snapshot_id"]
    return org_id, workspace_id, portfolio_id, executive_id, portfolio_snapshot_id


def test_presentation_requires_feature_flag(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CODESTRATA_EXECUTIVE_INTELLIGENCE_ENABLED", "true")
    monkeypatch.delenv("CODESTRATA_EXECUTIVE_PRESENTATION_ENABLED", raising=False)
    org_id, workspace_id, portfolio_id = _build_portfolio_with_snapshot(client)
    built = client.post(
        f"/api/v1/portfolios/{portfolio_id}/executive-intelligence",
        json={"organization_id": org_id, "workspace_id": workspace_id},
    )
    assert built.status_code == 201, built.text
    executive_id = built.json()["summary"]["executive_intelligence_id"]
    response = client.get(
        f"/api/v1/executive-intelligence/{executive_id}/presentation",
        params={"organization_id": org_id, "workspace_id": workspace_id},
    )
    assert response.status_code == 422, response.text


def test_presentation_full_route_flow(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    org_id, workspace_id, portfolio_id, executive_id, portfolio_snapshot_id = _build_executive(
        client, monkeypatch
    )

    scope_params = {"organization_id": org_id, "workspace_id": workspace_id}

    full = client.get(
        f"/api/v1/executive-intelligence/{executive_id}/presentation",
        params=scope_params,
    )
    assert full.status_code == 200, full.text
    payload = full.json()
    assert payload["identity"]["executive_intelligence_id"] == executive_id
    assert payload["executive_summary"]["headline"]
    assert payload["cto_summary"]["engineering_health"]["score"] >= 0
    assert payload["kpi_cards"]
    assert payload["limitations_and_assumptions"]
    assert all(point["direction"] == "unknown" for point in payload["trend_ready_metrics"])

    latest = client.get(
        f"/api/v1/portfolios/{portfolio_id}/executive-presentation/latest",
        params={"organization_id": org_id, "workspace_id": workspace_id},
    )
    assert latest.status_code == 200, latest.text
    assert latest.json()["identity"]["executive_intelligence_id"] == executive_id

    by_snapshot = client.get(
        f"/api/v1/portfolio-snapshots/{portfolio_snapshot_id}/executive-presentation",
        params={"organization_id": org_id, "workspace_id": workspace_id},
    )
    assert by_snapshot.status_code == 200, by_snapshot.text

    executive_summary = client.get(
        f"/api/v1/executive-intelligence/{executive_id}/presentation/executive-summary",
        params=scope_params,
    )
    assert executive_summary.status_code == 200, executive_summary.text
    assert "headline" in executive_summary.json()

    cto = client.get(
        f"/api/v1/executive-intelligence/{executive_id}/presentation/cto-summary",
        params=scope_params,
    )
    assert cto.status_code == 200, cto.text
    assert "engineering_health" in cto.json()

    scorecard = client.get(
        f"/api/v1/executive-intelligence/{executive_id}/presentation/scorecard",
        params=scope_params,
    )
    assert scorecard.status_code == 200, scorecard.text
    assert scorecard.json()["cards"]


def test_missing_presentation_source_returns_404(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_flags(monkeypatch)
    response = client.get(
        "/api/v1/executive-intelligence/exec:missing/presentation",
        params={"organization_id": "org:missing", "workspace_id": "workspace:missing"},
    )
    assert response.status_code == 404, response.text


def test_get_executive_presentation_requires_scope_params(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_flags(monkeypatch)
    response = client.get("/api/v1/executive-intelligence/exec:missing/presentation")
    assert response.status_code == 422, response.text
