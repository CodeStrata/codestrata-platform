"""Contract constants for Slice 12.4 Community client boundary cleanup."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.community_client_boundary_cleanup import (
    COMMUNITY_CLIENT_BOUNDARY_CLEANUP_ID,
    COMMUNITY_CLIENT_BOUNDARY_CLEANUP_VERSION,
)

SCHEMA_NAME = "community-client-boundary-cleanup-verification"
SCHEMA_VERSION = "1.0.0"

SV124_OUTPUT_RELATIVE = "reports/verification/sv12-4"
REPORT_JSON = "community-client-boundary-cleanup-verification.json"
REPORT_MD = "community-client-boundary-cleanup-verification.md"

ASSESSMENT_SCHEMA_VERSION = "1.2"
EXPECTED_VSCODE_VERSION = "0.2.0"
RETIRED_CLIENT_POLICY_URN = "community-retired-client-policy:1.0"
SCHEMA_COMPATIBILITY_DECISION = "approach_a_active_policy_restriction_without_schema_removal"

ACTIVE_CLIENTS = (
    "codestrata_cli",
    "vscode_extension",
)
# Telemetry public contract still lists other_extension intentionally.
TELEMETRY_OTHER_EXTENSION = "other_extension"
RETIRED_HISTORICAL_CLIENTS = ("cursor_extension",)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv124Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = COMMUNITY_CLIENT_BOUNDARY_CLEANUP_ID
    package_version: str = COMMUNITY_CLIENT_BOUNDARY_CLEANUP_VERSION
    start_slice_12_5: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True
    no_s3_migration: bool = True
    no_stored_event_rewrite: bool = True
    no_historical_report_rewrite: bool = True
    assessment_schema_version: str = ASSESSMENT_SCHEMA_VERSION
    schema_compatibility_decision: str = SCHEMA_COMPATIBILITY_DECISION
    retired_client_policy_urn: str = RETIRED_CLIENT_POLICY_URN


def default_contract() -> Sv124Contract:
    return Sv124Contract()
