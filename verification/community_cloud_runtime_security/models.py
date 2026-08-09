"""Models for Slice 17.6."""

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
class CommunityCloudRuntimeSecurityReport:
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
    secrets: dict[str, Any]
    secret_generation: dict[str, Any]
    secret_storage: dict[str, Any]
    secret_rotation: dict[str, Any]
    lambda_role: dict[str, Any]
    writer_policy: dict[str, Any]
    reader_policy: dict[str, Any]
    secret_policy: dict[str, Any]
    iam_simulation: dict[str, Any]
    lambda_environment: dict[str, Any]
    insights_auth: dict[str, Any]
    api_auth: dict[str, Any]
    ingestion: dict[str, Any]
    data_lake: dict[str, Any]
    provider_boundary: dict[str, Any]
    github_apply_role: dict[str, Any]
    operator_iam: dict[str, Any]
    failure_behavior: dict[str, Any]
    security: dict[str, Any]
    privacy: dict[str, Any]
    cost: dict[str, Any]
    deployment_regression: dict[str, Any]
    plan_regression: dict[str, Any]
    oidc_regression: dict[str, Any]
    epic16_regression: dict[str, Any]
    epic17_boundary: dict[str, Any]
    statuses: dict[str, str]
    scenario_results: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "api_auth": self.api_auth,
            "checks": self.checks,
            "cost": self.cost,
            "data_lake": self.data_lake,
            "defects": self.defects,
            "deployment_regression": self.deployment_regression,
            "epic": self.epic,
            "epic16_regression": self.epic16_regression,
            "epic17_boundary": self.epic17_boundary,
            "evidence": self.evidence,
            "failed_checks": self.failed_checks,
            "failure_behavior": self.failure_behavior,
            "github_apply_role": self.github_apply_role,
            "iam_simulation": self.iam_simulation,
            "ingestion": self.ingestion,
            "insights_auth": self.insights_auth,
            "inventory": self.inventory,
            "lambda_environment": self.lambda_environment,
            "lambda_role": self.lambda_role,
            "limitations": self.limitations,
            "oidc_regression": self.oidc_regression,
            "operator_iam": self.operator_iam,
            "package_id": self.package_id,
            "package_version": self.package_version,
            "plan_regression": self.plan_regression,
            "policy": self.policy,
            "privacy": self.privacy,
            "provider_boundary": self.provider_boundary,
            "reader_policy": self.reader_policy,
            "register": self.register,
            "scenario_results": self.scenario_results,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "secret_generation": self.secret_generation,
            "secret_policy": self.secret_policy,
            "secret_rotation": self.secret_rotation,
            "secret_storage": self.secret_storage,
            "secrets": self.secrets,
            "security": self.security,
            "slice": self.slice,
            "statuses": self.statuses,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "writer_policy": self.writer_policy,
        }
