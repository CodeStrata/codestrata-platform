"""Models for Slice 14.12 documentation deployment verification."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Verdict = Literal["PASS", "PASS_WITH_LIMITATIONS", "FAIL"]


@dataclass(slots=True)
class CheckResult:
    name: str
    ok: bool
    detail: str
    category: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "detail": self.detail,
            "name": self.name,
            "ok": self.ok,
        }


@dataclass(slots=True)
class Defect:
    classification: str
    summary: str

    def to_dict(self) -> dict[str, str]:
        return {"classification": self.classification, "summary": self.summary}


@dataclass(slots=True)
class DocumentationDeploymentReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    policy_status: str = "not_executed"
    inventory_status: str = "not_executed"
    package_root_status: str = "not_executed"
    vitepress_status: str = "not_executed"
    build_output_status: str = "not_executed"
    wrangler_status: str = "not_executed"
    output_alignment_status: str = "not_executed"
    preflight_status: str = "not_executed"
    build_ownership_status: str = "not_executed"
    non_interactive_status: str = "not_executed"
    mutation_boundary_status: str = "not_executed"
    generated_scope_status: str = "not_executed"
    assets_status: str = "not_executed"
    community_export_status: str = "not_executed"
    dependencies_status: str = "not_executed"
    node_runtime_status: str = "not_executed"
    security_status: str = "not_executed"
    wrangler_telemetry_status: str = "not_executed"
    cloudflare_settings_status: str = "not_executed"
    clean_ci_status: str = "not_executed"
    dry_run_status: str = "not_executed"
    accessibility_regression_status: str = "not_executed"
    consistency_boundary_status: str = "not_executed"
    determinism_status: str = "not_executed"
    scenarios_status: str = "not_executed"
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0
    release_posture: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "accessibility_regression_status": self.accessibility_regression_status,
            "assets_status": self.assets_status,
            "blockers": sorted(self.blockers),
            "build_output_status": self.build_output_status,
            "build_ownership_status": self.build_ownership_status,
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "clean_ci_status": self.clean_ci_status,
            "cloudflare_settings_status": self.cloudflare_settings_status,
            "community_export_status": self.community_export_status,
            "consistency_boundary_status": self.consistency_boundary_status,
            "defects": [d.to_dict() for d in self.defects],
            "dependencies_status": self.dependencies_status,
            "determinism_status": self.determinism_status,
            "dry_run_status": self.dry_run_status,
            "failed_checks": self.failed_checks,
            "generated_scope_status": self.generated_scope_status,
            "inventory_status": self.inventory_status,
            "limitations": sorted(self.limitations),
            "mutation_boundary_status": self.mutation_boundary_status,
            "node_runtime_status": self.node_runtime_status,
            "non_interactive_status": self.non_interactive_status,
            "output_alignment_status": self.output_alignment_status,
            "package_root_status": self.package_root_status,
            "policy_status": self.policy_status,
            "preflight_status": self.preflight_status,
            "release_posture": dict(sorted(self.release_posture.items())),
            "scenarios_status": self.scenarios_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "security_status": self.security_status,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "vitepress_status": self.vitepress_status,
            "wrangler_status": self.wrangler_status,
            "wrangler_telemetry_status": self.wrangler_telemetry_status,
        }
