"""Models for Slice 17.8."""

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
    export_authority: dict[str, Any]
    repositories: dict[str, Any]
    oidc: dict[str, Any]
    monorepo_authority: dict[str, Any]
    hosting: dict[str, Any]
    operational: dict[str, Any]
    regressions: dict[str, Any]
    epic17_boundary: dict[str, Any]
    statuses: dict[str, str]
    scenario_results: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "checks": self.checks,
            "defects": self.defects,
            "epic": self.epic,
            "epic17_boundary": self.epic17_boundary,
            "evidence": self.evidence,
            "export_authority": self.export_authority,
            "failed_checks": self.failed_checks,
            "hosting": self.hosting,
            "limitations": self.limitations,
            "monorepo_authority": self.monorepo_authority,
            "oidc": self.oidc,
            "operational": self.operational,
            "package_id": self.package_id,
            "package_version": self.package_version,
            "policy": self.policy,
            "register": self.register,
            "regressions": self.regressions,
            "repositories": self.repositories,
            "scenario_results": self.scenario_results,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "slice": self.slice,
            "statuses": self.statuses,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
        }
