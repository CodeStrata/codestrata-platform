"""Negative scenarios A–Z for Slice 17.22."""

from __future__ import annotations

from verification.community_epic17_defect_resolution.helpers import check
from verification.community_epic17_defect_resolution.models import CheckResult, Defect


def check_scenarios(*, flags: dict[str, bool]) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    scenarios = [
        ("A", "known defect silently reclassified limitation", flags.get("inventory_honest", False)),
        ("B", "dead timeout settings remain", flags.get("timeout_wired", False)),
        ("C", "provider retry infinite/unbounded", flags.get("retry_bounded", False)),
        ("D", "AI usage telemetry leaks prompts/responses", flags.get("ai_usage_safe", False)),
        ("E", "identity data deleted incorrectly", flags.get("identity_ok", False)),
        ("F", "PAT/userinfo persisted in clone remote", flags.get("git_ok", False)),
        ("G", "generated report staged for commit", flags.get("worktree_ok", False)),
        ("H", "secret included in export", flags.get("exports_ok", False)),
        ("I", "execute-api restored as public endpoint", flags.get("domains_ok", False)),
        ("J", "report bucket public", flags.get("report_storage_ok", False)),
        ("K", "report artifact appears in Data Lake", flags.get("data_lake_ok", False)),
        ("L", "query_budget regression", flags.get("insights_ok", False)),
        ("M", "assessment smoke fails", flags.get("assessment_ok", False)),
        ("N", "EIR traceability fails", flags.get("eir_ok", False)),
        ("O", "VS Code Share regresses", flags.get("vscode_ok", False)),
        ("P", "docs contradict live behavior", flags.get("docs_ok", False)),
        ("Q", "tofu drift remains", flags.get("infra_ok", False)),
        ("R", "secret scan finds credential", flags.get("security_ok", False)),
        ("S", "resolved limitation still marked current", flags.get("stale_ok", False)),
        ("T", "release carry-forward includes resolved", flags.get("carry_ok", False)),
        ("U", "full 22-repo release corpus starts", flags.get("no_full_22", False)),
        ("V", "Marketplace publish starts", flags.get("no_marketplace", False)),
        ("W", "Community Status package missing after 17.23 start", flags.get("status_17_23_present", False)),
        ("X", "release tag created", flags.get("no_tag", False)),
        ("Y", "Slice 17.24 starts", flags.get("no_17_24", False)),
        ("Z", "verifier nondeterministic", flags.get("deterministic", False)),
    ]
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    results: dict[str, bool] = {}
    for letter, title, ok in scenarios:
        results[letter] = bool(ok)
        checks.append(check(f"scenario:{letter}", bool(ok), title, "scenarios"))
    return checks, defects, results
