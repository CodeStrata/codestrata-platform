"""Negative scenarios A–Z for Slice 17.14."""

from __future__ import annotations

from verification.community_api_domain.models import CheckResult, Defect


def check_scenarios(*, flags: dict[str, bool]) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    """Each scenario passes when the corresponding negative condition is absent."""

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    scenarios = [
        ("A", "policy start_slice_17_15 true", flags.get("start_slice_17_15_false", False)),
        ("B", "public API authority modules missing", flags.get("authority_modules_ok", False)),
        ("C", "execute-api advertised as public authority in docs", flags.get("docs_no_execute_api", False)),
        ("D", "Insights browser calls api.codestrata.ai directly", flags.get("insights_same_origin", False)),
        ("E", "private Insights routes documented as Community API", flags.get("private_not_in_community_docs", False)),
        ("F", "unclassified API routes in register", flags.get("routes_classified", False)),
        ("G", "Cloudflare token or AWS key committed in slice paths", flags.get("no_secrets", False)),
        ("H", "telemetry or route schemas expanded for domain change", flags.get("schemas_unchanged", False)),
        ("I", "execute-api endpoint disabled in OpenTofu", flags.get("execute_api_retained", False)),
        ("J", "custom domain infra absent", flags.get("custom_domain_present", False)),
        ("K", "production enable_api_custom_domain false", flags.get("custom_domain_enabled", False)),
        ("L", "community-api docs page missing", flags.get("docs_page_present", False)),
        ("M", "docs nav/sidebar missing community-api link", flags.get("docs_nav_linked", False)),
        ("N", "UPSTREAM_API_BASE not api.codestrata.ai", flags.get("upstream_api_base_ok", False)),
        ("O", "domain register incomplete", flags.get("domain_register_ok", False)),
        ("P", "route register incomplete", flags.get("route_register_ok", False)),
        ("Q", "Slice 17.15 package started", flags.get("slice_17_15_absent", False)),
        ("R", "prior Epic 17 verification boundary missing", flags.get("prior_boundary_present", False)),
        ("S", "docs examples contain prohibited privacy fields", flags.get("docs_examples_safe", False)),
        ("T", "health docs example structurally invalid", flags.get("health_example_valid", False)),
        ("U", "live DNS/TLS pending (soft limitation only)", flags.get("live_ok_or_soft", True)),
        ("V", "worktree uncommitted (soft limitation only)", flags.get("worktree_clean_or_soft", True)),
        ("W", "infra zero-drift evidence absent (soft limitation only)", flags.get("zero_drift_or_soft", True)),
        ("X", "docs remote deploy evidence absent (soft limitation only)", flags.get("docs_deploy_or_soft", True)),
        ("Y", "verifier nondeterministic", flags.get("determinism_ok", False)),
        ("Z", "report leaks account IDs/ARNs/paths/execute-api", flags.get("report_safe", False)),
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
        if not ok and letter not in {"U", "V", "W", "X"}:
            defects.append(Defect("scenario", f"scenario:{letter}", "pass", label))
    return checks, defects, results
