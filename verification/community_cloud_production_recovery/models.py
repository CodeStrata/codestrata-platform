"""Models for Slice 17.10."""

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
    classification: dict[str, Any]
    evidence: dict[str, Any]
    inventory: dict[str, Any]
    baseline: dict[str, Any]
    lambda_image: dict[str, Any]
    lambda_config: dict[str, Any]
    resource_classification: dict[str, Any]
    destructive_gate: dict[str, Any]
    state_recovery: dict[str, Any]
    lock_recovery: dict[str, Any]
    cloudflare_insights: dict[str, Any]
    cloudflare_docs: dict[str, Any]
    github_iam: dict[str, Any]
    github_workflows: dict[str, Any]
    application_update: dict[str, Any]
    data_safety: dict[str, Any]
    secrets_safety: dict[str, Any]
    recovery_matrix: dict[str, Any]
    security: dict[str, Any]
    cost: dict[str, Any]
    zero_drift: dict[str, Any]
    prior_slices: dict[str, Any]
    epic17_boundary: dict[str, Any]
    statuses: dict[str, str]
    scenario_results: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "application_update": self.application_update,
            "baseline": self.baseline,
            "checks": self.checks,
            "classification": self.classification,
            "cloudflare_docs": self.cloudflare_docs,
            "cloudflare_insights": self.cloudflare_insights,
            "cost": self.cost,
            "data_safety": self.data_safety,
            "defects": self.defects,
            "destructive_gate": self.destructive_gate,
            "epic": self.epic,
            "epic17_boundary": self.epic17_boundary,
            "evidence": self.evidence,
            "failed_checks": self.failed_checks,
            "github_iam": self.github_iam,
            "github_workflows": self.github_workflows,
            "inventory": self.inventory,
            "lambda_config": self.lambda_config,
            "lambda_image": self.lambda_image,
            "limitations": self.limitations,
            "lock_recovery": self.lock_recovery,
            "package_id": self.package_id,
            "package_version": self.package_version,
            "policy": self.policy,
            "prior_slices": self.prior_slices,
            "recovery_matrix": self.recovery_matrix,
            "register": self.register,
            "resource_classification": self.resource_classification,
            "scenario_results": self.scenario_results,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "secrets_safety": self.secrets_safety,
            "security": self.security,
            "slice": self.slice,
            "state_recovery": self.state_recovery,
            "statuses": self.statuses,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "zero_drift": self.zero_drift,
        }
