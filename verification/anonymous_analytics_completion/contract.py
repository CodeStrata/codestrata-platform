"""Contract for Epic 10 completion verification (Slice 10.9)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.anonymous_analytics_completion import (
    ANONYMOUS_ANALYTICS_COMPLETION_ID,
    ANONYMOUS_ANALYTICS_COMPLETION_VERSION,
)

SCHEMA_NAME = "anonymous-analytics-completion-verification"
SCHEMA_VERSION = "1.0.0"

EPIC = "10"
EXPECTED_SLICE_COUNT = 9
SLICES_COMPLETED: tuple[str, ...] = tuple(f"10.{i}" for i in range(1, 10))

SV109_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv10-9"
REPORT_JSON = "anonymous-analytics-completion-verification.json"
REPORT_MD = "anonymous-analytics-completion-verification.md"

PRIVACY_REPORT_RELATIVE = (
    ".codestrata-artifacts/validation/suites/sv10-8/anonymous-analytics-privacy-verification.json"
)
PRIVACY_SCHEMA = "anonymous-analytics-privacy-verification"
PRIVACY_EXPECTED_CHECKS = 157

ASSESSMENT_SCHEMA_VERSION = "1.2"

FORBIDDEN_REPORT_FRAGMENTS: tuple[str, ...] = (
    "/Users/",
    "/home/",
    "file://",
    '"installation_id":',
    '"machineId"',
    '"telemetrySessionId"',
    "Authorization: Bearer",
    "-----BEGIN PRIVATE",
    "AKIA",
    "sk-",
)

INTENTIONALLY_EXCLUDED: tuple[str, ...] = (
    "production_analytics_collection",
    "analytics_event_persistence",
    "analytics_transmission",
    "analytics_queues_workers_batching",
    "community_cloud_analytics_processors",
    "data_lake_analytics_queries",
    "dashboards",
    "vscode_http_analytics_transport",
    "vscode_installation_identity",
    "cursor_analytics",
    "ai_provider_platform",
    "openrouter",
    "epic_11",
    "commit_tag_publish_deploy",
)

DEFAULT_LIMITATIONS: tuple[str, ...] = (
    "vscode_extension_host_ui_automation_not_required",
    "bounded_exact_language_counts_intentional_privacy_limitation",
    "engine_analytics_construction_only_unwired",
    "vscode_analytics_local_unavailable_sink_only",
    "production_analytics_not_operational",
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv109Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = ANONYMOUS_ANALYTICS_COMPLETION_ID
    package_version: str = ANONYMOUS_ANALYTICS_COMPLETION_VERSION
    epic: str = EPIC
    expected_slice_count: int = EXPECTED_SLICE_COUNT
    slices_completed: tuple[str, ...] = SLICES_COMPLETED
    start_epic_11: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True
    no_shared_runtime_schema: bool = True
    assessment_schema_version: str = ASSESSMENT_SCHEMA_VERSION


def default_contract() -> Sv109Contract:
    return Sv109Contract()
