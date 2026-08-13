"""Assessment metadata Platform-only boundary guards.

Public Engine may ship a Community *client* for the public assessment_metadata
API. Public path literals belong only in
``engine/.../community_cloud/public_api_authority.py``. Private Platform
implementation (``codestrata_platform.community_cloud_api``) remains forbidden.
"""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

from pathlib import Path

import yaml

from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION
from codestrata_platform.community_cloud_api import (
    COMMUNITY_ASSESSMENT_METADATA_POLICY_VERSION,
    COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION,
    COMMUNITY_CLOUD_API_SCHEMA_VERSION,
    COMMUNITY_EVENT_IDENTITY_POLICY_VERSION,
    COMMUNITY_LOGGING_POLICY_VERSION,
    COMMUNITY_PAYLOAD_LIMIT_POLICY_VERSION,
    COMMUNITY_REQUEST_VALIDATION_POLICY_VERSION,
    COMMUNITY_TELEMETRY_POLICY_VERSION,
    COMMUNITY_TELEMETRY_SCHEMA_VERSION,
    create_community_cloud_app,
)
from codestrata_platform.community_cloud_api.assessment_metadata import (
    COMMUNITY_ASSESSMENT_METADATA_POLICY_URN,
)
from codestrata_platform.intelligence_reporting.application.website_export import (
    WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
ENGINE_SRC = REPO_ROOT / "engine" / "src" / "codestrata"
ENGINE_AMD_CLIENT = ENGINE_SRC / "telemetry" / "assessment_metadata"
PKG = (
    REPO_ROOT
    / "platform"
    / "src"
    / "codestrata_platform"
    / "community_cloud_api"
)

_PUBLIC_AMD_PATH = "/api/v1/assessment-metadata"
_PRIVATE_PLATFORM_TOKENS = (
    "create_community_cloud_app",
    "codestrata_platform",
    "community_cloud_api",
)


def test_package_platform_only() -> None:
    """Platform owns the server package; Engine may only know public client contract."""

    assert (PKG / "assessment_metadata" / "service.py").is_file()
    assert not (ENGINE_SRC / "community_cloud_api").exists()
    # Approved Engine Community client location (Slice 20.8).
    assert (ENGINE_AMD_CLIENT / "transport.py").is_file()
    assert (ENGINE_AMD_CLIENT / "projector.py").is_file()
    assert (ENGINE_AMD_CLIENT / "emitter.py").is_file()

    for path in ENGINE_SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        # Canonical public endpoint authority — only place for path literals.
        if path.name == "public_api_authority.py":
            assert _PUBLIC_AMD_PATH in text
            continue
        assert "create_community_cloud_app" not in text
        assert _PUBLIC_AMD_PATH not in text


def test_engine_amd_client_uses_public_api_authority() -> None:
    """Positive: approved client modules resolve endpoint via public authority."""

    transport = (ENGINE_AMD_CLIENT / "transport.py").read_text(encoding="utf-8")
    assert "codestrata.community_cloud.public_api_authority" in transport
    assert "production_assessment_metadata_url" in transport
    for token in _PRIVATE_PLATFORM_TOKENS:
        assert token not in transport


def test_engine_amd_client_forbids_private_platform_coupling() -> None:
    """Negative: approved client package must not embed Platform implementation."""

    for path in ENGINE_AMD_CLIENT.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "codestrata_platform" not in text
        assert "community_cloud_api" not in text
        assert "create_community_cloud_app" not in text
        assert "data_lake" not in text
        assert "intelligence_reporting" not in text


def test_boundary_scan_still_flags_private_factory_outside_authority() -> None:
    """Negative: non-authority Engine modules with Platform factory tokens fail scan."""

    synthetic = (
        "from codestrata_platform.community_cloud_api import create_community_cloud_app\n"
        f"URL = '{_PUBLIC_AMD_PATH}'\n"
    )
    assert "create_community_cloud_app" in synthetic
    assert _PUBLIC_AMD_PATH in synthetic
    # Real Engine tree (outside authority) must not contain those tokens.
    offenders: list[str] = []
    for path in ENGINE_SRC.rglob("*.py"):
        if path.name == "public_api_authority.py":
            continue
        text = path.read_text(encoding="utf-8")
        if "create_community_cloud_app" in text or _PUBLIC_AMD_PATH in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == []


def test_production_routes() -> None:
    paths = {
        (r.method, r.path)
        for r in create_community_cloud_app(authentication_policy=disabled_authentication_policy()).state.community_cloud_route_registry.list_routes()
    }
    assert paths >= {
        ("GET", "/health"),
        ("POST", "/ai-usage"),
        ("POST", "/assessment-metadata"),
        ("POST", "/cli-events"),
        ("POST", "/extension-events"),
        ("POST", "/telemetry"),
    }
    for path in ("/events", "/assessment", "/telemetry/batch"):
        assert ("POST", path) not in paths


def test_no_persistence_auth() -> None:
    for name in ("persistence", "queues", "workers", "auth", "rate_limit"):
        assert not (PKG / name).exists()
    assert (PKG / "assessment_metadata").is_dir()
    assert (PKG / "telemetry").is_dir()


def test_public_export_excludes_platform() -> None:
    manifest = yaml.safe_load(
        (REPO_ROOT / "public-export-manifest.yaml").read_text(encoding="utf-8")
    )
    forbidden = manifest.get("release", {}).get("forbidden_internal_paths") or []
    assert "platform/" in forbidden


def test_schema_constants_unchanged() -> None:
    assert ASSESSMENT_JSON_SCHEMA_VERSION == "1.2"
    assert ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION == "1.0"
    assert WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_CLOUD_API_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_REQUEST_VALIDATION_POLICY_VERSION == "1.0"
    assert COMMUNITY_PAYLOAD_LIMIT_POLICY_VERSION == "1.0"
    assert COMMUNITY_LOGGING_POLICY_VERSION == "1.0"
    assert COMMUNITY_EVENT_IDENTITY_POLICY_VERSION == "1.0"
    assert COMMUNITY_TELEMETRY_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_TELEMETRY_POLICY_VERSION == "1.0"
    assert COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_ASSESSMENT_METADATA_POLICY_VERSION == "1.0"
    assert (
        COMMUNITY_ASSESSMENT_METADATA_POLICY_URN
        == "community-assessment-metadata-policy:1.0"
    )
