"""Negative scenarios A–Z for Slice 17.23."""

from __future__ import annotations

from verification.community_status_report_registry.helpers import check, hard_defect
from verification.community_status_report_registry.models import CheckResult, Defect


def check_scenarios(*, flags: dict[str, bool]) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    """Each scenario passes when the corresponding negative condition is absent."""

    scenarios = [
        ("A", "policy missing required status/registry flags", flags.get("policy_ok", False)),
        ("B", "community status module absent", flags.get("status_module", False)),
        ("C", "community status route not registered", flags.get("status_route", False)),
        ("D", "live status schema invalid when HTTP 200", flags.get("live_schema_ok", False)),
        ("E", "live engine_version mismatches codestrata.__version__", flags.get("live_version_ok", False)),
        ("F", "live status body leaks AWS IDs or secrets", flags.get("live_no_secrets", False)),
        ("G", "GitHub stars cache module absent", flags.get("github_cache", False)),
        ("H", "browser embeds GitHub token (ghp_/token)", flags.get("website_no_token", False)),
        ("I", "public-report-urls manifest not schema 1.1", flags.get("manifest_schema", False)),
        ("J", "manifest missing current/previous assessment fields", flags.get("manifest_fields", False)),
        ("K", "17.21 flask assessment URL not retained", flags.get("flask_retained", False)),
        ("L", "engine public_report_url_manifest auto-upsert absent", flags.get("auto_upsert", False)),
        ("M", "Insights PublishedReportsPage absent", flags.get("insights_page", False)),
        ("N", "AppShell missing published-reports nav", flags.get("insights_nav", False)),
        ("O", "published-reports route missing in App", flags.get("insights_route", False)),
        ("P", "Insights API path /insights/api/published-reports absent", flags.get("insights_api", False)),
        ("Q", "community-api docs omit community/status", flags.get("docs_status", False)),
        ("R", "report rendering leaves reports.codestrata.ai", flags.get("reports_domain", False)),
        ("S", "start_slice_17_23 false in policy", flags.get("start_17_23", False)),
        ("T", "start_slice_17_24 true in policy", flags.get("no_17_24_flag", False)),
        ("U", "Slice 17.24 verification package present", flags.get("no_17_24_pkg", False)),
        ("V", "marketplace publish started", flags.get("no_marketplace", False)),
        ("W", "full 22-repo release corpus started", flags.get("no_full_22", False)),
        ("X", "status live unreachable (soft deploy pending)", flags.get("live_ok_or_soft", True)),
        ("Y", "Slice 17.24 starts", flags.get("no_17_24", False)),
        ("Z", "verifier nondeterministic or report leaks paths/secrets", flags.get("deterministic", False)),
    ]
    soft_letters = frozenset({"X"})
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    results: dict[str, bool] = {}
    for letter, label, ok in scenarios:
        results[letter] = bool(ok)
        checks.append(check(f"scenario:{letter}", bool(ok), label, "scenarios"))
        if not ok and letter not in soft_letters:
            defects.append(hard_defect("scenario", f"scenario:{letter}", "pass", label))
    return checks, defects, results
