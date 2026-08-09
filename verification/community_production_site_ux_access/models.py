"""Models for Slice 17.11."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

Verdict = Literal["PASS", "PASS_WITH_LIMITATIONS", "FAIL"]


@dataclass(slots=True)
class CheckResult:
    check_id: str
    ok: bool
    detail: str
    category: str


@dataclass(slots=True)
class Defect:
    classification: str
    surface: str
    expected: str
    observed: str


@dataclass(slots=True)
class Report:
    schema: str
    schema_version: str
    package_id: str
    package_version: str
    epic: str
    slice: str
    verdict: Verdict
    total_checks: int
    failed_checks: int
    limitations: list[str]
    checks: list[dict[str, Any]]
    defects: list[dict[str, Any]]
    policy: dict[str, Any]
    register: dict[str, Any]
    evidence: dict[str, Any]
    docs_ux: dict[str, Any]
    insights_ux: dict[str, Any]
    sites_posture: dict[str, Any]
    auth_rca: dict[str, Any]
    regressions: dict[str, Any]
    epic17_boundary: dict[str, Any]
    statuses: dict[str, str]
    scenario_results: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "auth_rca": self.auth_rca,
            "checks": self.checks,
            "defects": self.defects,
            "docs_ux": self.docs_ux,
            "epic": self.epic,
            "epic17_boundary": self.epic17_boundary,
            "evidence": self.evidence,
            "failed_checks": self.failed_checks,
            "insights_ux": self.insights_ux,
            "limitations": self.limitations,
            "package_id": self.package_id,
            "package_version": self.package_version,
            "policy": self.policy,
            "register": self.register,
            "regressions": self.regressions,
            "scenario_results": self.scenario_results,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "sites_posture": self.sites_posture,
            "slice": self.slice,
            "statuses": self.statuses,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
        }
