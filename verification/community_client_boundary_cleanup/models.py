"""Models for Slice 12.4 Community client boundary cleanup verification."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

Verdict = Literal["PASS", "PASS_WITH_LIMITATIONS", "FAIL", "BLOCKED"]

_ABS_PATH_RE = re.compile(r"(?<![\w.-])/Users/[\w./-]+")
_HOME_PATH_RE = re.compile(r"(?<![\w.-])/home/[\w./-]+")
_FORBIDDEN_REPORT_TOKENS = (
    "/Users/",
    "/home/",
    "file://",
    "-----BEGIN",
    "sk-",
    "AKIA",
    "VSCE_PAT=",
    "OVSX_TOKEN=",
)


def sanitize_text(value: str) -> str:
    text = _ABS_PATH_RE.sub("[REDACTED_PATH]", value)
    text = _HOME_PATH_RE.sub("[REDACTED_PATH]", text)
    return text


def sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return sanitize_text(value)
    if isinstance(value, dict):
        return {k: sanitize_value(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    return value


def report_contains_forbidden_leak(blob: str) -> list[str]:
    return [token for token in _FORBIDDEN_REPORT_TOKENS if token in blob]


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    ok: bool
    detail: str = ""
    category: str = "general"

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "detail": sanitize_text(self.detail),
            "name": self.name,
            "ok": self.ok,
        }


@dataclass(frozen=True, slots=True)
class Defect:
    classification: str
    component: str
    expected: str
    actual: str
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "actual": sanitize_text(self.actual),
            "classification": self.classification,
            "component": self.component,
            "detail": sanitize_text(self.detail),
            "expected": sanitize_text(self.expected),
        }


@dataclass
class CommunityClientBoundaryCleanupReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    active_client_inventory: list[str] = field(default_factory=list)
    retired_client_inventory: list[str] = field(default_factory=list)
    schema_compatibility_decision: str = ""
    engine_telemetry_status: str = "not_executed"
    engine_analytics_status: str = "not_executed"
    vscode_runtime_status: str = "not_executed"
    current_api_status: str = "not_executed"
    historical_deserialization_status: str = "not_executed"
    envelope_compatibility_status: str = "not_executed"
    partition_compatibility_status: str = "not_executed"
    metadata_compatibility_status: str = "not_executed"
    quarantine_status: str = "not_executed"
    production_fail_closed_status: str = "not_executed"
    platform_boundary_status: str = "not_executed"
    data_lake_boundary_status: str = "not_executed"
    privacy_status: str = "not_executed"
    migration_required: bool = False
    rewrite_required: bool = False
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0
    checks: list[CheckResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return sanitize_value(
            {
                "active_client_inventory": sorted(self.active_client_inventory),
                "blockers": sorted(self.blockers),
                "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
                "current_api_status": self.current_api_status,
                "data_lake_boundary_status": self.data_lake_boundary_status,
                "defects": [d.to_dict() for d in self.defects],
                "engine_analytics_status": self.engine_analytics_status,
                "engine_telemetry_status": self.engine_telemetry_status,
                "envelope_compatibility_status": self.envelope_compatibility_status,
                "failed_checks": self.failed_checks,
                "historical_deserialization_status": self.historical_deserialization_status,
                "limitations": sorted(self.limitations),
                "metadata_compatibility_status": self.metadata_compatibility_status,
                "migration_required": self.migration_required,
                "partition_compatibility_status": self.partition_compatibility_status,
                "platform_boundary_status": self.platform_boundary_status,
                "privacy_status": self.privacy_status,
                "production_fail_closed_status": self.production_fail_closed_status,
                "quarantine_status": self.quarantine_status,
                "retired_client_inventory": sorted(self.retired_client_inventory),
                "rewrite_required": self.rewrite_required,
                "schema_compatibility_decision": self.schema_compatibility_decision,
                "schema_name": self.schema_name,
                "schema_version": self.schema_version,
                "total_checks": self.total_checks,
                "verdict": self.verdict,
                "verification_id": self.verification_id,
                "vscode_runtime_status": self.vscode_runtime_status,
            }
        )

    def write_json(self, path: Path) -> None:
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
