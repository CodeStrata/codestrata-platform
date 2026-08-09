"""Contract constants for Slice 10.8 anonymous analytics privacy verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.anonymous_analytics_privacy import (
    ANONYMOUS_ANALYTICS_PRIVACY_VERIFICATION_ID,
    ANONYMOUS_ANALYTICS_PRIVACY_VERIFICATION_VERSION,
)

SCHEMA_NAME = "anonymous-analytics-privacy-verification"
SCHEMA_VERSION = "1.0.0"

SV108_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv10-8"
REPORT_JSON = "anonymous-analytics-privacy-verification.json"
REPORT_MD = "anonymous-analytics-privacy-verification.md"

ASSESSMENT_SCHEMA_VERSION = "1.2"

# Product contract tokens (all expected 1.0).
ENGINE_BASE_POLICY = "community-anonymous-analytics-policy:1.0"
ENGINE_BASE_SCHEMA = "community-anonymous-analytics-schema:1.0"
ENGINE_IDENTITY_POLICY = "community-anonymous-installation-identity-policy:1.0"
ENGINE_RUNTIME_POLICY = "community-runtime-analytics-policy:1.0"
ENGINE_ASSESSMENT_POLICY = "community-assessment-analytics-policy:1.0"
ENGINE_REPO_POLICY = "community-repository-aggregate-analytics-policy:1.0"
ENGINE_AI_POLICY = "community-ai-analytics-policy:1.0"
VSCODE_ANALYTICS_POLICY = "community-vscode-anonymous-analytics-policy:1.0"
VSCODE_ANALYTICS_SCHEMA = "community-vscode-anonymous-analytics-schema:1.0"


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv108Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = ANONYMOUS_ANALYTICS_PRIVACY_VERIFICATION_ID
    package_version: str = ANONYMOUS_ANALYTICS_PRIVACY_VERIFICATION_VERSION
    start_slice_109: bool = False
    no_commit: bool = True
    no_shared_runtime_schema: bool = True
    no_analytics_transmission: bool = True
    no_analytics_event_persistence: bool = True
    no_vscode_http: bool = True
    no_vscode_identity: bool = True
    no_cursor_analytics: bool = True
    no_cloud_analytics_processors: bool = True
    assessment_schema_version: str = ASSESSMENT_SCHEMA_VERSION


def default_contract() -> Sv108Contract:
    return Sv108Contract()
