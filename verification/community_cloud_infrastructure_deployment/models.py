"""Models for Slice 17.5."""

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
class CommunityCloudInfrastructureDeploymentReport:
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
    inventory: dict[str, Any]
    image: dict[str, Any]
    ecr: dict[str, Any]
    lambda_runtime: dict[str, Any]
    api_gateway: dict[str, Any]
    data_lake: dict[str, Any]
    iam: dict[str, Any]
    cloudwatch: dict[str, Any]
    apply: dict[str, Any]
    workflow: dict[str, Any]
    apply_permissions: dict[str, Any]
    operator_iam: dict[str, Any]
    ingestion: dict[str, Any]
    writer: dict[str, Any]
    secrets: dict[str, Any]
    insights: dict[str, Any]
    docs: dict[str, Any]
    health: dict[str, Any]
    rollback: dict[str, Any]
    cost: dict[str, Any]
    security: dict[str, Any]
    privacy: dict[str, Any]
    epic17_boundary: dict[str, Any]
    statuses: dict[str, str]
    scenario_results: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "api_gateway": self.api_gateway,
            "apply": self.apply,
            "apply_permissions": self.apply_permissions,
            "checks": self.checks,
            "cloudwatch": self.cloudwatch,
            "cost": self.cost,
            "data_lake": self.data_lake,
            "defects": self.defects,
            "docs": self.docs,
            "ecr": self.ecr,
            "epic": self.epic,
            "epic17_boundary": self.epic17_boundary,
            "evidence": self.evidence,
            "failed_checks": self.failed_checks,
            "health": self.health,
            "iam": self.iam,
            "image": self.image,
            "ingestion": self.ingestion,
            "insights": self.insights,
            "inventory": self.inventory,
            "lambda_runtime": self.lambda_runtime,
            "limitations": self.limitations,
            "operator_iam": self.operator_iam,
            "package_id": self.package_id,
            "package_version": self.package_version,
            "policy": self.policy,
            "privacy": self.privacy,
            "register": self.register,
            "rollback": self.rollback,
            "scenario_results": self.scenario_results,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "secrets": self.secrets,
            "security": self.security,
            "slice": self.slice,
            "statuses": self.statuses,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "workflow": self.workflow,
            "writer": self.writer,
        }
