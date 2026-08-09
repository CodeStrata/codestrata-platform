"""Models for Slice 17.4."""

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
class CommunityCloudProductionPlanReport:
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
    plan_summary: dict[str, Any]
    inventory: dict[str, Any]
    components: dict[str, Any]
    data_lake: dict[str, Any]
    lambda_runtime: dict[str, Any]
    ecr: dict[str, Any]
    api_gateway: dict[str, Any]
    iam: dict[str, Any]
    github_plan_permissions: dict[str, Any]
    secrets: dict[str, Any]
    insights_auth: dict[str, Any]
    cloudwatch: dict[str, Any]
    networking: dict[str, Any]
    cost: dict[str, Any]
    security: dict[str, Any]
    privacy: dict[str, Any]
    schema_boundary: dict[str, Any]
    workflow: dict[str, Any]
    apply_permission_register: dict[str, Any]
    epic17_boundary: dict[str, Any]
    statuses: dict[str, str]
    scenario_results: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "api_gateway": self.api_gateway,
            "apply_permission_register": self.apply_permission_register,
            "checks": self.checks,
            "cloudwatch": self.cloudwatch,
            "components": self.components,
            "cost": self.cost,
            "data_lake": self.data_lake,
            "defects": self.defects,
            "ecr": self.ecr,
            "epic": self.epic,
            "epic17_boundary": self.epic17_boundary,
            "failed_checks": self.failed_checks,
            "github_plan_permissions": self.github_plan_permissions,
            "iam": self.iam,
            "insights_auth": self.insights_auth,
            "inventory": self.inventory,
            "lambda_runtime": self.lambda_runtime,
            "limitations": self.limitations,
            "networking": self.networking,
            "package_id": self.package_id,
            "package_version": self.package_version,
            "plan_summary": self.plan_summary,
            "policy": self.policy,
            "privacy": self.privacy,
            "register": self.register,
            "scenario_results": self.scenario_results,
            "schema": self.schema,
            "schema_boundary": self.schema_boundary,
            "schema_version": self.schema_version,
            "secrets": self.secrets,
            "security": self.security,
            "slice": self.slice,
            "statuses": self.statuses,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "workflow": self.workflow,
        }
