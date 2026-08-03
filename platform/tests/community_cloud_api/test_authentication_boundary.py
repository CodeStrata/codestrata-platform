"""Authentication package boundary guards."""

from __future__ import annotations

from pathlib import Path

PKG = Path(__file__).resolve().parents[2] / "src" / "codestrata_platform" / "community_cloud_api"
ENGINE = Path(__file__).resolve().parents[3] / "engine"


def test_authentication_package_present_without_user_auth_stack() -> None:
    assert (PKG / "authentication").is_dir()
    for name in ("auth", "oauth", "saml", "sessions", "cognito", "secrets_manager"):
        assert not (PKG / name).exists()


def test_engine_does_not_import_community_authentication() -> None:
    if not ENGINE.exists():
        return
    for path in ENGINE.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "community_cloud_api.authentication" not in text
        assert "CommunityAuthenticationPolicy" not in text
