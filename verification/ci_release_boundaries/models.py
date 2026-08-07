"""Models for Slice 12.9 verification."""

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
    "github.com/",
    "amazonaws.com",
    "AWS_SECRET",
    "aws_secret_access_key",
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
class CiReleaseBoundaryReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    workflow_inventory_status: str = "not_executed"
    vscode_ci_status: str = "not_executed"
    cursor_absence_status: str = "not_executed"
    community_export_ci_status: str = "not_executed"
    infrastructure_export_ci_status: str = "not_executed"
    exported_python_test_status: str = "not_executed"
    opentofu_ci_status: str = "not_executed"
    aws_credential_boundary_status: str = "not_executed"
    git_operation_boundary_status: str = "not_executed"
    workflow_permission_status: str = "not_executed"
    release_inventory_status: str = "not_executed"
    version_boundary_status: str = "not_executed"
    release_artifact_status: str = "not_executed"
    publish_boundary_status: str = "not_executed"
    deployment_boundary_status: str = "not_executed"
    job_isolation_status: str = "not_executed"
    cache_boundary_status: str = "not_executed"
    timeout_status: str = "not_executed"
    deterministic_status: str = "not_executed"
    active_editor_extensions: list[str] = field(default_factory=list)
    export_targets: list[str] = field(default_factory=list)
    required_ci_jobs: list[str] = field(default_factory=list)
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0
    checks: list[CheckResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return sanitize_value(
            {
                "active_editor_extensions": sorted(self.active_editor_extensions),
                "aws_credential_boundary_status": self.aws_credential_boundary_status,
                "blockers": sorted(self.blockers),
                "cache_boundary_status": self.cache_boundary_status,
                "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
                "community_export_ci_status": self.community_export_ci_status,
                "cursor_absence_status": self.cursor_absence_status,
                "defects": [d.to_dict() for d in self.defects],
                "deployment_boundary_status": self.deployment_boundary_status,
                "deterministic_status": self.deterministic_status,
                "export_targets": sorted(self.export_targets),
                "exported_python_test_status": self.exported_python_test_status,
                "failed_checks": self.failed_checks,
                "git_operation_boundary_status": self.git_operation_boundary_status,
                "infrastructure_export_ci_status": self.infrastructure_export_ci_status,
                "job_isolation_status": self.job_isolation_status,
                "limitations": sorted(self.limitations),
                "opentofu_ci_status": self.opentofu_ci_status,
                "publish_boundary_status": self.publish_boundary_status,
                "release_artifact_status": self.release_artifact_status,
                "release_inventory_status": self.release_inventory_status,
                "required_ci_jobs": sorted(self.required_ci_jobs),
                "schema_name": self.schema_name,
                "schema_version": self.schema_version,
                "timeout_status": self.timeout_status,
                "total_checks": self.total_checks,
                "verdict": self.verdict,
                "verification_id": self.verification_id,
                "version_boundary_status": self.version_boundary_status,
                "vscode_ci_status": self.vscode_ci_status,
                "workflow_inventory_status": self.workflow_inventory_status,
                "workflow_permission_status": self.workflow_permission_status,
            }
        )

    def write_json(self, path: Path) -> None:
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
