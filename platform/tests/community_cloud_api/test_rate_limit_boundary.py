"""Boundary guards for Slice 7.12 rate limiting."""

from __future__ import annotations

from pathlib import Path

PKG = Path(__file__).resolve().parents[2] / "src" / "codestrata_platform" / "community_cloud_api"
ENGINE = Path(__file__).resolve().parents[3] / "engine"
CURSOR = Path(__file__).resolve().parents[3] / "cursor-plugin"
VSCODE = Path(__file__).resolve().parents[3] / "vscode-extension"


def test_rate_limiting_package_platform_only() -> None:
    assert (PKG / "rate_limiting").is_dir()
    assert not (PKG / "rate_limit").exists()
    assert not (PKG / "auth").exists()
    assert not (PKG / "persistence").exists()
    assert not (PKG / "queues").exists()
    assert not (PKG / "workers").exists()
    # No Redis / DynamoDB adapters in this slice.
    names = {path.name for path in (PKG / "rate_limiting").iterdir()}
    assert "redis.py" not in names
    assert "dynamodb.py" not in names
    assert "database.py" not in names


def test_no_engine_or_client_rate_limit_imports() -> None:
    for root in (ENGINE, CURSOR, VSCODE):
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            assert "community_cloud_api.rate_limiting" not in text
            assert "CommunityRateLimitPolicy" not in text


def test_production_route_count_unchanged() -> None:
    from codestrata_platform.community_cloud_api.registry import RouteRegistry

    assert len(RouteRegistry.foundation_v1().list_routes()) == 6


def test_schema_constants_unchanged() -> None:
    from codestrata_platform.community_cloud_api.constants import (
        COMMUNITY_CLOUD_API_SCHEMA_VERSION,
        COMMUNITY_RATE_LIMIT_POLICY_VERSION,
        COMMUNITY_TELEMETRY_SCHEMA_VERSION,
    )

    assert COMMUNITY_CLOUD_API_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_TELEMETRY_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_RATE_LIMIT_POLICY_VERSION == "1.1"
