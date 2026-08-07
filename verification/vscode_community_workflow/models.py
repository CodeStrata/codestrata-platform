"""Models for Slice 13.1 verification."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

Verdict = Literal["PASS", "PASS_WITH_LIMITATIONS", "FAIL", "BLOCKED"]

_ABS_PATH_RE = re.compile(r"(?<![\w.-])/Users/[\w./-]+")
_HOME_PATH_RE = re.compile(r"(?<![\w.-])/home/[\w./-]+")
_FORBIDDEN = (
    "/Users/",
    "/home/",
    "file://",
    "-----BEGIN",
    "sk-",
    "AKIA",
    "AWS_SECRET",
)


def sanitize_text(value: str) -> str:
    text = _ABS_PATH_RE.sub("[REDACTED_PATH]", value)
    return _HOME_PATH_RE.sub("[REDACTED_PATH]", text)


def sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return sanitize_text(value)
    if isinstance(value, dict):
        return {k: sanitize_value(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [sanitize_value(v) for v in value]
    return value


def report_contains_forbidden_leak(blob: str) -> list[str]:
    return [t for t in _FORBIDDEN if t in blob]


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

    def to_dict(self) -> dict[str, Any]:
        return {
            "actual": sanitize_text(self.actual),
            "classification": self.classification,
            "component": self.component,
            "expected": sanitize_text(self.expected),
        }


@dataclass
class VsCodeCommunityWorkflowReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    command_inventory: list[str] = field(default_factory=list)
    operation_inventory: list[str] = field(default_factory=list)
    workflow_state_inventory: list[str] = field(default_factory=list)
    workflow_policy_status: str = "not_executed"
    command_registration_status: str = "not_executed"
    activation_status: str = "not_executed"
    workspace_boundary_status: str = "not_executed"
    initialization_boundary_status: str = "not_executed"
    standard_assessment_status: str = "not_executed"
    ai_assessment_status: str = "not_executed"
    cli_invocation_status: str = "not_executed"
    telemetry_boundary_status: str = "not_executed"
    analytics_boundary_status: str = "not_executed"
    progress_boundary_status: str = "not_executed"
    report_boundary_status: str = "not_executed"
    primary_authority_status: str = "not_executed"
    error_boundary_status: str = "not_executed"
    privacy_status: str = "not_executed"
    vscode_regression_status: str = "not_executed"
    deferred_slice_inventory: list[str] = field(default_factory=list)
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0
    checks: list[CheckResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return sanitize_value(
            {
                "activation_status": self.activation_status,
                "ai_assessment_status": self.ai_assessment_status,
                "analytics_boundary_status": self.analytics_boundary_status,
                "blockers": sorted(self.blockers),
                "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
                "cli_invocation_status": self.cli_invocation_status,
                "command_inventory": sorted(self.command_inventory),
                "command_registration_status": self.command_registration_status,
                "deferred_slice_inventory": sorted(self.deferred_slice_inventory),
                "defects": [d.to_dict() for d in self.defects],
                "error_boundary_status": self.error_boundary_status,
                "failed_checks": self.failed_checks,
                "initialization_boundary_status": self.initialization_boundary_status,
                "limitations": sorted(self.limitations),
                "operation_inventory": sorted(self.operation_inventory),
                "primary_authority_status": self.primary_authority_status,
                "privacy_status": self.privacy_status,
                "progress_boundary_status": self.progress_boundary_status,
                "report_boundary_status": self.report_boundary_status,
                "schema_name": self.schema_name,
                "schema_version": self.schema_version,
                "standard_assessment_status": self.standard_assessment_status,
                "telemetry_boundary_status": self.telemetry_boundary_status,
                "total_checks": self.total_checks,
                "verdict": self.verdict,
                "verification_id": self.verification_id,
                "vscode_regression_status": self.vscode_regression_status,
                "workflow_policy_status": self.workflow_policy_status,
                "workflow_state_inventory": sorted(self.workflow_state_inventory),
                "workspace_boundary_status": self.workspace_boundary_status,
            }
        )

    def write_json(self, path: Path) -> None:
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
