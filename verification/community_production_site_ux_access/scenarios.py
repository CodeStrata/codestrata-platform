"""Negative scenarios A–N for Slice 17.11."""

from __future__ import annotations

from verification.community_production_site_ux_access.models import CheckResult, Defect


def check_scenarios(*, flags: dict[str, bool]) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    """Each scenario passes when the corresponding negative condition is absent."""

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    scenarios = [
        ("A", "docs fixed header still overlaps hero", flags.get("header_overlap_fixed", False)),
        ("B", "docs logo/Main Site navigation ambiguous", flags.get("logo_main_site_clear", False)),
        ("C", "codestrata-docs GitHub repo public", flags.get("docs_repo_private", False)),
        ("D", "docs.codestrata.ai site private", flags.get("docs_site_public", False)),
        ("E", "password or verifier leaked in report", flags.get("report_no_secrets", False)),
        ("F", "Slice 17.12 started", flags.get("slice_17_13_absent", False)),
        ("G", "Insights favicon not approved mark", flags.get("insights_favicon_ok", False)),
        ("H", "Docs favicon not approved mark", flags.get("docs_favicon_ok", False)),
        ("I", "inner docs footer not minimal/legal-only", flags.get("inner_footer_minimal", False)),
        ("J", "Insights auth root cause not encoded", flags.get("auth_root_cause_encoded", False)),
        ("K", "password rotation performed unnecessarily", flags.get("rotation_not_required", False)),
        ("L", "Insights login UX regressed", flags.get("insights_login_ok", False)),
        ("M", "production sites posture degraded", flags.get("production_sites_ok", False)),
        ("N", "verifier nondeterministic or report unsafe", flags.get("determinism_ok", False)),
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
