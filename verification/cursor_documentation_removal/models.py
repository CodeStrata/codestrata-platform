"""Models for Slice 12.3 Cursor documentation removal verification."""

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
class CursorDocumentationRemovalReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    root_readme_status: str
    architecture_status: str
    privacy_status: str
    security_status: str
    extension_documentation_status: str
    marketplace_documentation_status: str
    branding_asset_status: str
    cli_configuration_documentation_status: str
    telemetry_analytics_documentation_status: str
    cloud_data_lake_documentation_status: str
    vscode_documentation_status: str
    historical_reference_status: str
    deferred_contract_reference_inventory: list[str] = field(default_factory=list)
    removed_document_count: int = 0
    changed_document_count: int = 0
    removed_asset_count: int = 0
    checks: list[CheckResult] = field(default_factory=list)
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0
    confirmations: dict[str, bool | str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "architecture_status": self.architecture_status,
            "blockers": sorted(sanitize_text(b) for b in self.blockers),
            "branding_asset_status": self.branding_asset_status,
            "changed_document_count": self.changed_document_count,
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda c: c.name)],
            "cli_configuration_documentation_status": self.cli_configuration_documentation_status,
            "cloud_data_lake_documentation_status": self.cloud_data_lake_documentation_status,
            "confirmations": {
                k: (sanitize_text(v) if isinstance(v, str) else v)
                for k, v in sorted(self.confirmations.items())
            },
            "deferred_contract_reference_inventory": sorted(
                sanitize_text(x) for x in self.deferred_contract_reference_inventory
            ),
            "defects": [d.to_dict() for d in sorted(self.defects, key=lambda d: d.classification)],
            "extension_documentation_status": self.extension_documentation_status,
            "failed_checks": self.failed_checks,
            "historical_reference_status": self.historical_reference_status,
            "limitations": sorted(sanitize_text(x) for x in self.limitations),
            "marketplace_documentation_status": self.marketplace_documentation_status,
            "privacy_status": self.privacy_status,
            "removed_asset_count": self.removed_asset_count,
            "removed_document_count": self.removed_document_count,
            "root_readme_status": self.root_readme_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "security_status": self.security_status,
            "telemetry_analytics_documentation_status": self.telemetry_analytics_documentation_status,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "vscode_documentation_status": self.vscode_documentation_status,
        }
        return sanitize_value(payload)

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
