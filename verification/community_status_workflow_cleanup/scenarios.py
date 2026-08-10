"""Negative scenarios A–Z for Slice 17.25."""

from __future__ import annotations

from verification.community_status_workflow_cleanup.helpers import check, hard_defect
from verification.community_status_workflow_cleanup.models import CheckResult, Defect


def check_scenarios(*, flags: dict[str, bool]) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    """Each scenario passes when the corresponding negative condition is absent."""

    scenarios = [
        ("A", "GitHub authority policy missing or invalid", flags.get("policy_ok", False)),
        ("B", "workflow authority register missing or invalid", flags.get("workflow_register_ok", False)),
        ("C", "status register schema 1.1 absent", flags.get("status_register_ok", False)),
        ("D", "GitHubMetadataCache module absent", flags.get("github_cache", False)),
        ("E", "normalize_release_tag absent", flags.get("normalize_release_tag", False)),
        ("F", "resolve_public_engine_version absent", flags.get("resolve_public_engine_version", False)),
        ("G", "version_source exposed on public to_stable_dict", flags.get("public_no_version_source", False)),
        ("H", "fabricated hardcoded github stars in service", flags.get("no_fabricated_stars", False)),
        ("I", "community-api docs omit GitHub release authority", flags.get("docs_github_release", False)),
        ("J", "website site.js missing status API binding", flags.get("website_status_binding", False)),
        ("K", "root workflow inventory drift from register", flags.get("workflow_inventory", False)),
        ("L", "export workflows missing repository guards", flags.get("export_guards", False)),
        ("M", "absent root deploy workflows present", flags.get("no_root_deploy", False)),
        ("N", "ci.yml contains deploy steps", flags.get("ci_no_deploy", False)),
        ("O", "workflows embed GH PAT or static AWS keys", flags.get("workflow_secrets_clean", False)),
        ("P", "live status body leaks AWS IDs or secrets", flags.get("live_no_secrets", False)),
        ("Q", "live status schema invalid when HTTP 200", flags.get("live_schema_ok", False)),
        ("R", "prior slice 17.24 package absent", flags.get("prior_17_24", False)),
        ("S", "start_slice_17_25 false in policy", flags.get("start_17_25", False)),
        ("T", "start_slice_17_26 true in policy", flags.get("no_17_26_flag", False)),
        ("U", "Slice 17.26 verification package present", flags.get("no_17_26_pkg", False)),
        ("V", "marketplace publish started", flags.get("no_marketplace", False)),
        ("W", "browser embeds GitHub token", flags.get("website_no_token", False)),
        ("X", "status live unreachable (soft deploy pending)", flags.get("live_ok_or_soft", True)),
        ("Y", "Slice 17.26 starts", flags.get("no_17_26", False)),
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
