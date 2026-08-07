"""Models for Slice 12.1 Cursor extension removal verification."""

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
class CursorExtensionRemovalReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    cursor_directory_status: str
    cursor_source_status: str
    cursor_package_status: str
    cursor_test_status: str
    cursor_telemetry_runtime_status: str
    cursor_analytics_runtime_status: str
    cursor_asset_status: str
    vscode_regression_status: str
    engine_boundary_status: str
    platform_boundary_status: str
    historical_compatibility_status: str
    deferred_reference_inventory: list[str] = field(default_factory=list)
    removed_file_count: int = 0
    preserved_shared_inventory: list[str] = field(default_factory=list)
    preserved_historical_inventory: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0
    confirmations: dict[str, bool | str] = field(default_factory=dict)
    classification: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "blockers": sorted(sanitize_text(b) for b in self.blockers),
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda c: c.name)],
            "classification": {
                key: sorted(sanitize_text(v) for v in values)
                for key, values in sorted(self.classification.items())
            },
            "confirmations": {
                k: (sanitize_text(v) if isinstance(v, str) else v)
                for k, v in sorted(self.confirmations.items())
            },
            "cursor_analytics_runtime_status": self.cursor_analytics_runtime_status,
            "cursor_asset_status": self.cursor_asset_status,
            "cursor_directory_status": self.cursor_directory_status,
            "cursor_package_status": self.cursor_package_status,
            "cursor_source_status": self.cursor_source_status,
            "cursor_telemetry_runtime_status": self.cursor_telemetry_runtime_status,
            "cursor_test_status": self.cursor_test_status,
            "defects": [d.to_dict() for d in sorted(self.defects, key=lambda d: d.classification)],
            "deferred_reference_inventory": sorted(
                sanitize_text(x) for x in self.deferred_reference_inventory
            ),
            "engine_boundary_status": self.engine_boundary_status,
            "failed_checks": self.failed_checks,
            "historical_compatibility_status": self.historical_compatibility_status,
            "limitations": sorted(sanitize_text(x) for x in self.limitations),
            "platform_boundary_status": self.platform_boundary_status,
            "preserved_historical_inventory": sorted(
                sanitize_text(x) for x in self.preserved_historical_inventory
            ),
            "preserved_shared_inventory": sorted(
                sanitize_text(x) for x in self.preserved_shared_inventory
            ),
            "removed_file_count": self.removed_file_count,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "vscode_regression_status": self.vscode_regression_status,
        }
        return sanitize_value(payload)

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
