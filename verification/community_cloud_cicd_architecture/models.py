"""Models for Slice 17.1."""

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
class CommunityCloudCicdArchitectureReport:
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
    cicd_register: dict[str, Any]
    component_register: dict[str, Any]
    remote_state: dict[str, Any]
    oidc: dict[str, Any]
    environment_strategy: dict[str, Any]
    deployment_order: list[str]
    lambda_strategy: dict[str, Any]
    release_boundary: dict[str, Any]
    epic17_boundary: dict[str, Any]
    statuses: dict[str, str]
    scenario_results: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "checks": self.checks,
            "cicd_register": self.cicd_register,
            "component_register": self.component_register,
            "defects": self.defects,
            "deployment_order": self.deployment_order,
            "environment_strategy": self.environment_strategy,
            "epic": self.epic,
            "epic17_boundary": self.epic17_boundary,
            "failed_checks": self.failed_checks,
            "lambda_strategy": self.lambda_strategy,
            "limitations": self.limitations,
            "oidc": self.oidc,
            "package_id": self.package_id,
            "package_version": self.package_version,
            "policy": self.policy,
            "release_boundary": self.release_boundary,
            "remote_state": self.remote_state,
            "scenario_results": self.scenario_results,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "slice": self.slice,
            "statuses": self.statuses,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
        }
