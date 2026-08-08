"""Models for Slice 16.10."""

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
class RepositoryCleanupCompletionReport:
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
    slice_completion_matrix: list[dict[str, Any]]
    policy_registry: list[dict[str, str]]
    contract_registry: list[dict[str, str]]
    version_registry: dict[str, str]
    owner_review_final_register: list[dict[str, Any]]
    technical_debt_handoff: list[dict[str, Any]]
    repository_structure: list[dict[str, str]]
    public_repository_quality: dict[str, Any]
    export_summary: dict[str, Any]
    epic17_readiness: dict[str, Any]
    release_posture: dict[str, Any]
    statuses: dict[str, str]
    scenario_results: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "checks": self.checks,
            "contract_registry": self.contract_registry,
            "defects": self.defects,
            "epic": self.epic,
            "epic17_readiness": self.epic17_readiness,
            "export_summary": self.export_summary,
            "failed_checks": self.failed_checks,
            "limitations": self.limitations,
            "owner_review_final_register": self.owner_review_final_register,
            "package_id": self.package_id,
            "package_version": self.package_version,
            "policy": self.policy,
            "policy_registry": self.policy_registry,
            "public_repository_quality": self.public_repository_quality,
            "release_posture": self.release_posture,
            "repository_structure": self.repository_structure,
            "scenario_results": self.scenario_results,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "slice": self.slice,
            "slice_completion_matrix": self.slice_completion_matrix,
            "statuses": self.statuses,
            "technical_debt_handoff": self.technical_debt_handoff,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "version_registry": self.version_registry,
        }
