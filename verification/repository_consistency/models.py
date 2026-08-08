"""Models for Slice 16.8."""

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
class RepositoryConsistencyReport:
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
    domain_verdicts: dict[str, str]
    top_level_map: list[dict[str, str]]
    authority_registry: dict[str, str]
    policy_registry_summary: list[dict[str, str]]
    contract_registry_summary: list[dict[str, str]]
    version_registry: dict[str, str]
    build_authority_summary: list[dict[str, str]]
    visibility_matrix: list[dict[str, str]]
    cross_repo_contract_matrix: list[dict[str, str]]
    owner_review_register: list[dict[str, Any]]
    historical_exceptions: list[str]
    unresolved_findings: list[str]
    release_blocking_findings: list[str]
    release_posture: dict[str, Any]
    statuses: dict[str, str]
    scenario_results: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority_registry": self.authority_registry,
            "build_authority_summary": self.build_authority_summary,
            "checks": self.checks,
            "contract_registry_summary": self.contract_registry_summary,
            "cross_repo_contract_matrix": self.cross_repo_contract_matrix,
            "defects": self.defects,
            "domain_verdicts": self.domain_verdicts,
            "epic": self.epic,
            "failed_checks": self.failed_checks,
            "historical_exceptions": self.historical_exceptions,
            "limitations": self.limitations,
            "owner_review_register": self.owner_review_register,
            "package_id": self.package_id,
            "package_version": self.package_version,
            "policy": self.policy,
            "policy_registry_summary": self.policy_registry_summary,
            "release_blocking_findings": self.release_blocking_findings,
            "release_posture": self.release_posture,
            "scenario_results": self.scenario_results,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "slice": self.slice,
            "statuses": self.statuses,
            "top_level_map": self.top_level_map,
            "total_checks": self.total_checks,
            "unresolved_findings": self.unresolved_findings,
            "verdict": self.verdict,
            "version_registry": self.version_registry,
            "visibility_matrix": self.visibility_matrix,
        }
