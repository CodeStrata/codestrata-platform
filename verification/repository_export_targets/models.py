"""Models for Slice 12.8 verification."""

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
class RepositoryExportTargetReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    command_surface_status: str = "not_executed"
    target_registry_status: str = "not_executed"
    target_selection_status: str = "not_executed"
    community_target_status: str = "not_executed"
    infrastructure_target_status: str = "not_executed"
    community_manifest_status: str = "not_executed"
    infrastructure_manifest_status: str = "not_executed"
    manifest_separation_status: str = "not_executed"
    destination_semantics_status: str = "not_executed"
    destination_ownership_status: str = "not_executed"
    dry_run_status: str = "not_executed"
    community_regression_status: str = "not_executed"
    infrastructure_regression_status: str = "not_executed"
    cross_target_isolation_status: str = "not_executed"
    platform_boundary_status: str = "not_executed"
    visibility_status: str = "not_executed"
    compatibility_wrapper_status: str = "not_executed"
    git_boundary_status: str = "not_executed"
    aws_boundary_status: str = "not_executed"
    deployment_boundary_status: str = "not_executed"
    deterministic_status: str = "not_executed"
    supported_targets: list[str] = field(default_factory=list)
    target_visibility: dict[str, str] = field(default_factory=dict)
    target_manifest_schemas: dict[str, str] = field(default_factory=dict)
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0
    checks: list[CheckResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return sanitize_value(
            {
                "aws_boundary_status": self.aws_boundary_status,
                "blockers": sorted(self.blockers),
                "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
                "command_surface_status": self.command_surface_status,
                "community_manifest_status": self.community_manifest_status,
                "community_regression_status": self.community_regression_status,
                "community_target_status": self.community_target_status,
                "compatibility_wrapper_status": self.compatibility_wrapper_status,
                "cross_target_isolation_status": self.cross_target_isolation_status,
                "defects": [d.to_dict() for d in self.defects],
                "deployment_boundary_status": self.deployment_boundary_status,
                "destination_ownership_status": self.destination_ownership_status,
                "destination_semantics_status": self.destination_semantics_status,
                "deterministic_status": self.deterministic_status,
                "dry_run_status": self.dry_run_status,
                "failed_checks": self.failed_checks,
                "git_boundary_status": self.git_boundary_status,
                "infrastructure_manifest_status": self.infrastructure_manifest_status,
                "infrastructure_regression_status": self.infrastructure_regression_status,
                "infrastructure_target_status": self.infrastructure_target_status,
                "limitations": sorted(self.limitations),
                "manifest_separation_status": self.manifest_separation_status,
                "platform_boundary_status": self.platform_boundary_status,
                "schema_name": self.schema_name,
                "schema_version": self.schema_version,
                "supported_targets": sorted(self.supported_targets),
                "target_manifest_schemas": dict(sorted(self.target_manifest_schemas.items())),
                "target_registry_status": self.target_registry_status,
                "target_selection_status": self.target_selection_status,
                "target_visibility": dict(sorted(self.target_visibility.items())),
                "total_checks": self.total_checks,
                "verdict": self.verdict,
                "verification_id": self.verification_id,
                "visibility_status": self.visibility_status,
            }
        )

    def write_json(self, path: Path) -> None:
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
