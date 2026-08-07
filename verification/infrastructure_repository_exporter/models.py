"""Models for Slice 12.6 exporter verification."""

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
    "amazonaws.com",
    "github.com/",
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
class InfrastructureRepositoryExporterReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    command_surface_status: str = "not_executed"
    source_allowlist_status: str = "not_executed"
    prohibited_file_status: str = "not_executed"
    destination_safety_status: str = "not_executed"
    path_mapping_status: str = "not_executed"
    root_generation_status: str = "not_executed"
    boundary_test_generation_status: str = "not_executed"
    documentation_rewrite_status: str = "not_executed"
    permission_status: str = "not_executed"
    symlink_status: str = "not_executed"
    manifest_status: str = "not_executed"
    inventory_status: str = "not_executed"
    checksum_status: str = "not_executed"
    change_plan_status: str = "not_executed"
    atomicity_status: str = "not_executed"
    dry_run_status: str = "not_executed"
    git_boundary_status: str = "not_executed"
    aws_boundary_status: str = "not_executed"
    opentofu_boundary_status: str = "not_executed"
    deterministic_status: str = "not_executed"
    fixture_export_status: str = "not_executed"
    implementation_command: str = ""
    manifest_schema: str = ""
    source_file_count: int = 0
    generated_file_count: int = 0
    excluded_category_count: int = 0
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0
    checks: list[CheckResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return sanitize_value(
            {
                "atomicity_status": self.atomicity_status,
                "aws_boundary_status": self.aws_boundary_status,
                "blockers": sorted(self.blockers),
                "boundary_test_generation_status": self.boundary_test_generation_status,
                "change_plan_status": self.change_plan_status,
                "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
                "checksum_status": self.checksum_status,
                "command_surface_status": self.command_surface_status,
                "defects": [d.to_dict() for d in self.defects],
                "destination_safety_status": self.destination_safety_status,
                "deterministic_status": self.deterministic_status,
                "documentation_rewrite_status": self.documentation_rewrite_status,
                "dry_run_status": self.dry_run_status,
                "excluded_category_count": self.excluded_category_count,
                "failed_checks": self.failed_checks,
                "fixture_export_status": self.fixture_export_status,
                "generated_file_count": self.generated_file_count,
                "git_boundary_status": self.git_boundary_status,
                "implementation_command": self.implementation_command,
                "inventory_status": self.inventory_status,
                "limitations": sorted(self.limitations),
                "manifest_schema": self.manifest_schema,
                "manifest_status": self.manifest_status,
                "opentofu_boundary_status": self.opentofu_boundary_status,
                "path_mapping_status": self.path_mapping_status,
                "permission_status": self.permission_status,
                "prohibited_file_status": self.prohibited_file_status,
                "root_generation_status": self.root_generation_status,
                "schema_name": self.schema_name,
                "schema_version": self.schema_version,
                "source_allowlist_status": self.source_allowlist_status,
                "source_file_count": self.source_file_count,
                "symlink_status": self.symlink_status,
                "total_checks": self.total_checks,
                "verdict": self.verdict,
                "verification_id": self.verification_id,
            }
        )

    def write_json(self, path: Path) -> None:
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
