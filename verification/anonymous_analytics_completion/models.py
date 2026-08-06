"""Models for Epic 10 completion verification reports."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

Verdict = Literal["pass", "pass_with_limitations", "fail", "blocked"]

_ABS_PATH_RE = re.compile(r"(?<![\w.-])/Users/[\w./-]+")
_HOME_PATH_RE = re.compile(r"(?<![\w.-])/home/[\w./-]+")


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


def report_contains_forbidden_leak(blob: str, fragments: tuple[str, ...]) -> list[str]:
    return [token for token in fragments if token in blob]


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


@dataclass(frozen=True, slots=True)
class SliceEvidence:
    slice_id: str
    purpose: str
    implementation_evidence: str
    documentation_evidence: str
    test_evidence: str
    verification_evidence: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "documentation_evidence": sanitize_text(self.documentation_evidence),
            "implementation_evidence": sanitize_text(self.implementation_evidence),
            "purpose": self.purpose,
            "slice_id": self.slice_id,
            "status": self.status,
            "test_evidence": sanitize_text(self.test_evidence),
            "verification_evidence": sanitize_text(self.verification_evidence),
        }


@dataclass
class Epic10CompletionReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    epic: str
    expected_slice_count: int = 9
    completed_slice_count: int = 0
    slice_matrix: list[SliceEvidence] = field(default_factory=list)
    base_analytics_status: str = "unknown"
    installation_identity_status: str = "unknown"
    runtime_analytics_status: str = "unknown"
    assessment_analytics_status: str = "unknown"
    repository_aggregate_status: str = "unknown"
    ai_analytics_status: str = "unknown"
    vscode_analytics_status: str = "unknown"
    privacy_verification_status: str = "unknown"
    consent_status: str = "unknown"
    identity_status: str = "unknown"
    persistence_status: str = "unknown"
    transport_status: str = "unknown"
    product_path_status: str = "unknown"
    isolation_status: str = "unknown"
    documentation_status: str = "unknown"
    public_export_status: str = "unknown"
    packaging_status: str = "unknown"
    platform_boundary_status: str = "unknown"
    data_lake_boundary_status: str = "unknown"
    cursor_boundary_status: str = "unknown"
    next_epic_absence_status: str = "unknown"
    production_posture: str = "contracts_only_not_operational"
    policy_registry: list[str] = field(default_factory=list)
    schema_registry: list[str] = field(default_factory=list)
    verification_registry: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    confirmations: dict[str, bool] = field(default_factory=dict)
    total_checks: int = 0
    failed_checks: int = 0

    def to_stable_dict(self) -> dict[str, Any]:
        payload = {
            "ai_analytics_status": self.ai_analytics_status,
            "assessment_analytics_status": self.assessment_analytics_status,
            "base_analytics_status": self.base_analytics_status,
            "blockers": list(self.blockers),
            "checks": [c.to_dict() for c in self.checks],
            "completed_slice_count": self.completed_slice_count,
            "confirmations": dict(sorted(self.confirmations.items())),
            "consent_status": self.consent_status,
            "cursor_boundary_status": self.cursor_boundary_status,
            "data_lake_boundary_status": self.data_lake_boundary_status,
            "defects": [d.to_dict() for d in self.defects],
            "documentation_status": self.documentation_status,
            "epic": self.epic,
            "expected_slice_count": self.expected_slice_count,
            "failed_checks": self.failed_checks,
            "identity_status": self.identity_status,
            "installation_identity_status": self.installation_identity_status,
            "isolation_status": self.isolation_status,
            "limitations": list(self.limitations),
            "next_epic_absence_status": self.next_epic_absence_status,
            "packaging_status": self.packaging_status,
            "persistence_status": self.persistence_status,
            "platform_boundary_status": self.platform_boundary_status,
            "policy_registry": list(self.policy_registry),
            "privacy_verification_status": self.privacy_verification_status,
            "product_path_status": self.product_path_status,
            "production_posture": self.production_posture,
            "public_export_status": self.public_export_status,
            "repository_aggregate_status": self.repository_aggregate_status,
            "runtime_analytics_status": self.runtime_analytics_status,
            "schema_name": self.schema_name,
            "schema_registry": list(self.schema_registry),
            "schema_version": self.schema_version,
            "slice_matrix": [s.to_dict() for s in self.slice_matrix],
            "total_checks": self.total_checks,
            "transport_status": self.transport_status,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "verification_registry": list(self.verification_registry),
            "vscode_analytics_status": self.vscode_analytics_status,
        }
        return sanitize_value(payload)

    def to_stable_json(self) -> str:
        return json.dumps(self.to_stable_dict(), indent=2, sort_keys=True) + "\n"

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_stable_json(), encoding="utf-8")
