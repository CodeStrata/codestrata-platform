"""Models for Slice 12.2 Cursor release-surface removal verification."""

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
class CursorReleaseSurfaceRemovalReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    cursor_build_surface_status: str
    cursor_package_surface_status: str
    cursor_marketplace_surface_status: str
    cursor_release_inventory_status: str
    cursor_release_artifact_status: str
    cursor_version_status: str
    cursor_checksum_status: str
    cursor_license_status: str
    cursor_publish_status: str
    cursor_ci_status: str
    vscode_build_status: str
    vscode_package_status: str
    vscode_release_status: str
    engine_release_boundary_status: str
    platform_release_boundary_status: str
    historical_reference_status: str
    deferred_documentation_inventory: list[str] = field(default_factory=list)
    removed_reference_count: int = 0
    checks: list[CheckResult] = field(default_factory=list)
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0
    confirmations: dict[str, bool | str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "blockers": sorted(sanitize_text(b) for b in self.blockers),
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda c: c.name)],
            "confirmations": {
                k: (sanitize_text(v) if isinstance(v, str) else v)
                for k, v in sorted(self.confirmations.items())
            },
            "cursor_build_surface_status": self.cursor_build_surface_status,
            "cursor_checksum_status": self.cursor_checksum_status,
            "cursor_ci_status": self.cursor_ci_status,
            "cursor_license_status": self.cursor_license_status,
            "cursor_marketplace_surface_status": self.cursor_marketplace_surface_status,
            "cursor_package_surface_status": self.cursor_package_surface_status,
            "cursor_publish_status": self.cursor_publish_status,
            "cursor_release_artifact_status": self.cursor_release_artifact_status,
            "cursor_release_inventory_status": self.cursor_release_inventory_status,
            "cursor_version_status": self.cursor_version_status,
            "deferred_documentation_inventory": sorted(
                sanitize_text(x) for x in self.deferred_documentation_inventory
            ),
            "defects": [d.to_dict() for d in sorted(self.defects, key=lambda d: d.classification)],
            "engine_release_boundary_status": self.engine_release_boundary_status,
            "failed_checks": self.failed_checks,
            "historical_reference_status": self.historical_reference_status,
            "limitations": sorted(sanitize_text(x) for x in self.limitations),
            "platform_release_boundary_status": self.platform_release_boundary_status,
            "removed_reference_count": self.removed_reference_count,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "vscode_build_status": self.vscode_build_status,
            "vscode_package_status": self.vscode_package_status,
            "vscode_release_status": self.vscode_release_status,
        }
        return sanitize_value(payload)

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
