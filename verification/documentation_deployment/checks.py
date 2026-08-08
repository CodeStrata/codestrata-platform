"""Orchestrate all Slice 14.12 checks."""

from __future__ import annotations

from pathlib import Path

from verification.documentation_deployment.accessibility_regression import (
    check_accessibility_regression,
)
from verification.documentation_deployment.assets import check_assets
from verification.documentation_deployment.build_ownership import check_build_ownership
from verification.documentation_deployment.build_output import check_build_output
from verification.documentation_deployment.clean_ci import check_clean_ci
from verification.documentation_deployment.cloudflare_settings import check_cloudflare_settings
from verification.documentation_deployment.community_export import check_community_export
from verification.documentation_deployment.consistency_boundary import check_consistency_boundary
from verification.documentation_deployment.dependencies import check_dependencies
from verification.documentation_deployment.dry_run import check_dry_run
from verification.documentation_deployment.generated_scope import check_generated_scope
from verification.documentation_deployment.inventory import DeploymentInventory, build_inventory
from verification.documentation_deployment.models import CheckResult, Defect
from verification.documentation_deployment.mutation_boundary import check_mutation_boundary
from verification.documentation_deployment.node_runtime import check_node_runtime
from verification.documentation_deployment.non_interactive import check_non_interactive
from verification.documentation_deployment.output_alignment import check_output_alignment
from verification.documentation_deployment.package_root import check_package_root
from verification.documentation_deployment.policy import check_policy
from verification.documentation_deployment.preflight import check_preflight
from verification.documentation_deployment.scenarios import check_negative_scenarios
from verification.documentation_deployment.security import check_security
from verification.documentation_deployment.vitepress import check_vitepress
from verification.documentation_deployment.wrangler import check_wrangler
from verification.documentation_deployment.wrangler_telemetry import check_wrangler_telemetry


def check_all(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[str], DeploymentInventory]:
    inv = build_inventory(monorepo)
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    extra_limitations: list[str] = []

    def extend(result: list[CheckResult]) -> None:
        checks.extend(result)

    c, d = check_policy(inv)
    checks.extend(c)
    defects.extend(d)

    extend([CheckResult("inventory:loaded", bool(inv.policy), "ok", "inventory")])

    extend(check_package_root(inv))
    extend(check_vitepress(inv))
    extend(check_build_output(inv))
    extend(check_wrangler(inv))
    extend(check_output_alignment(inv))
    extend(check_preflight(inv))
    extend(check_build_ownership(inv))
    extend(check_non_interactive(inv))
    extend(check_mutation_boundary(inv))
    extend(check_generated_scope(inv))
    extend(check_assets(inv))
    extend(check_community_export(inv))

    dep_checks, dep_limits = check_dependencies(inv)
    extend(dep_checks)
    extra_limitations.extend(dep_limits)

    extend(check_node_runtime(inv))
    extend(check_security(inv))
    extend(check_wrangler_telemetry(inv))
    extend(check_cloudflare_settings(inv))
    extend(check_clean_ci(inv))

    dry_checks, dry_limits = check_dry_run(inv)
    extend(dry_checks)
    extra_limitations.extend(dry_limits)

    extend(check_accessibility_regression(inv))

    c, d = check_consistency_boundary(inv)
    checks.extend(c)
    defects.extend(d)

    extend(check_negative_scenarios(inv))

    return checks, defects, extra_limitations, inv
