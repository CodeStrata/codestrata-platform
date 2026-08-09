"""Negative scenarios A–Z for Slice 17.8."""

from __future__ import annotations

from verification.community_production_sites_deployment.models import CheckResult, Defect


def check_scenarios(*, flags: dict[str, bool]) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    """Each scenario passes when the corresponding negative condition is absent."""

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    scenarios = [
        ("A", "infrastructure repo public", flags.get("infra_private", False)),
        ("B", "Insights repo public", flags.get("insights_private", False)),
        ("C", "docs GitHub repo not private (site stays public)", flags.get("docs_private", False)),
        ("D", "repository created under personal account", flags.get("org_correct", False)),
        ("E", "secret committed", flags.get("no_secrets", False)),
        ("F", "tfstate exported", flags.get("no_tfstate_export", False)),
        ("G", "backend.hcl credentials exported", flags.get("no_backend_creds", False)),
        ("H", "platform source exported to Insights", flags.get("no_platform_in_insights", False)),
        ("I", "Platform/private docs exported publicly", flags.get("public_private_boundary", False)),
        ("J", "node_modules/dist pushed unintentionally", flags.get("no_build_artifacts", False)),
        ("K", "AWS OIDC trust breaks after infrastructure repo creation", flags.get("oidc_dual_trust", False)),
        ("L", "OIDC wildcard trust added", flags.get("oidc_no_wildcard", False)),
        ("M", "Insights frontend receives AWS permission", flags.get("insights_no_aws", False)),
        ("N", "frontend contains Secrets Manager values", flags.get("no_frontend_secrets", False)),
        ("O", "docs contains production secrets", flags.get("no_docs_secrets", False)),
        ("P", "Cloudflare secret committed", flags.get("no_cloudflare_secrets", False)),
        ("Q", "Insights API route broken", flags.get("insights_api_ok", False)),
        ("R", "unauthenticated overview succeeds", flags.get("auth_required", False)),
        ("S", "dashboard leaks raw event/installation ID", flags.get("dashboard_safe", False)),
        ("T", "docs broken links", flags.get("docs_valid", False)),
        ("U", "monorepo source deleted prematurely", flags.get("monorepo_dirs_present", False)),
        ("V", "v0.2.0 tag/publish occurs", flags.get("no_v020_tag", False)),
        ("W", "Slice 17.13 starts", flags.get("slice_17_13_absent", False)),
        ("X", "repository export nondeterministic", flags.get("export_router_ok", False)),
        ("Y", "verifier nondeterministic", flags.get("determinism_ok", False)),
        ("Z", "report leaks tokens/account IDs/paths/timestamps", flags.get("report_safe", False)),
    ]
    results: dict[str, bool] = {}
    for letter, label, ok in scenarios:
        results[letter] = bool(ok)
        checks.append(
            CheckResult(
                f"scenario:{letter}",
                bool(ok),
                label if ok else f"FAIL:{label}",
                "scenarios",
            )
        )
        if not ok:
            defects.append(Defect("scenario", f"scenario:{letter}", "pass", label))
    return checks, defects, results
