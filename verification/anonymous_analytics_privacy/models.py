"""Models for Slice 10.8 anonymous analytics privacy verification."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

Verdict = Literal["pass", "pass_with_limitations", "fail", "blocked"]

_ABS_PATH_RE = re.compile(r"(?<![\w.-])/Users/[\w./-]+")
_HOME_PATH_RE = re.compile(r"(?<![\w.-])/home/[\w./-]+")
_USERNAME_RE = re.compile(r"(?<![\w@])[\w.-]+@[\w.-]+\.\w+")
_FORBIDDEN_REPORT_TOKENS = (
    '"installation_id":',
    '"machineId"',
    '"telemetrySessionId"',
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
    text = _USERNAME_RE.sub("[REDACTED_USER]", text)
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
    contract: str = "epic10"

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "contract": self.contract,
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
class PrincipleStatus:
    principle: str
    applicable_contracts: tuple[str, ...]
    evidence: str
    verdict: str = "pass"
    intentional_exceptions: str = ""
    limitation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "applicable_contracts": list(self.applicable_contracts),
            "evidence": sanitize_text(self.evidence),
            "intentional_exceptions": sanitize_text(self.intentional_exceptions),
            "limitation": sanitize_text(self.limitation),
            "principle": self.principle,
            "verdict": self.verdict,
        }


@dataclass
class AnonymousAnalyticsPrivacyReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    analytics_contract_status: str = "unknown"
    identity_status: str = "unknown"
    runtime_analytics_status: str = "unknown"
    assessment_analytics_status: str = "unknown"
    repository_aggregate_status: str = "unknown"
    ai_analytics_status: str = "unknown"
    vscode_analytics_status: str = "unknown"
    consent_status: str = "unknown"
    persistence_status: str = "unknown"
    transport_status: str = "unknown"
    isolation_status: str = "unknown"
    documentation_status: str = "unknown"
    boundary_status: str = "unknown"
    privacy_categories: list[PrincipleStatus] = field(default_factory=list)
    field_matrix: list[CheckResult] = field(default_factory=list)
    identity_matrix: list[CheckResult] = field(default_factory=list)
    persistence_matrix: list[CheckResult] = field(default_factory=list)
    transport_matrix: list[CheckResult] = field(default_factory=list)
    product_path_matrix: list[CheckResult] = field(default_factory=list)
    deterministic_checks: list[CheckResult] = field(default_factory=list)
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
            "analytics_contract_status": self.analytics_contract_status,
            "assessment_analytics_status": self.assessment_analytics_status,
            "blockers": list(self.blockers),
            "boundary_status": self.boundary_status,
            "checks": [c.to_dict() for c in self.checks],
            "confirmations": dict(sorted(self.confirmations.items())),
            "consent_status": self.consent_status,
            "defects": [d.to_dict() for d in self.defects],
            "deterministic_checks": [c.to_dict() for c in self.deterministic_checks],
            "documentation_status": self.documentation_status,
            "failed_checks": self.failed_checks,
            "field_matrix": [c.to_dict() for c in self.field_matrix],
            "identity_matrix": [c.to_dict() for c in self.identity_matrix],
            "identity_status": self.identity_status,
            "isolation_status": self.isolation_status,
            "limitations": list(self.limitations),
            "persistence_matrix": [c.to_dict() for c in self.persistence_matrix],
            "persistence_status": self.persistence_status,
            "privacy_categories": [p.to_dict() for p in self.privacy_categories],
            "product_path_matrix": [c.to_dict() for c in self.product_path_matrix],
            "repository_aggregate_status": self.repository_aggregate_status,
            "runtime_analytics_status": self.runtime_analytics_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "total_checks": self.total_checks,
            "transport_matrix": [c.to_dict() for c in self.transport_matrix],
            "transport_status": self.transport_status,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "vscode_analytics_status": self.vscode_analytics_status,
        }
        return sanitize_value(payload)

    def to_stable_json(self) -> str:
        return json.dumps(self.to_stable_dict(), indent=2, sort_keys=True) + "\n"

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_stable_json(), encoding="utf-8")
