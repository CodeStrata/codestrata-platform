"""Negative scenarios A–Z for Slice 17.9."""

from __future__ import annotations

from verification.community_cloud_incremental_deployment.models import CheckResult, Defect


def check_scenarios(*, flags: dict[str, bool]) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    scenarios = [
        ("A", "baseline drift present", flags.get("baseline_clean", False)),
        ("B", "unrelated resources in incremental plan", flags.get("only_expected", False)),
        ("C", "destroy in incremental plan", flags.get("no_destroy", False)),
        ("D", "replace in incremental plan", flags.get("no_replace", False)),
        ("E", "architecture redesign in change", flags.get("no_redesign", False)),
        ("F", "ingestion modified", flags.get("no_ingestion_change", False)),
        ("G", "post-apply drift remains", flags.get("post_apply_clean", False)),
        ("H", "rollback fails / leaves drift", flags.get("final_clean", False)),
        ("I", "tfvars not restored", flags.get("tfvars_restored", False)),
        ("J", "apply on pull_request", flags.get("apply_not_on_pr", False)),
        ("K", "missing OIDC on workflows", flags.get("workflow_oidc", False)),
        ("L", "missing production environment protection", flags.get("env_production", False)),
        ("M", "OIDC org wildcard trust", flags.get("no_wildcard", False)),
        ("N", "AdministratorAccess on GitHub role", flags.get("no_admin", False)),
        ("O", "missing destroy/replace apply gate", flags.get("destroy_gate", False)),
        ("P", "missing post-apply drift check in apply workflow", flags.get("post_drift_gate", False)),
        ("Q", "prior 17.1–17.8 report regression", flags.get("prior_reports_ok", False)),
        ("R", "prior policy invariants broken", flags.get("prior_invariants_ok", False)),
        ("S", "Slice 17.13 started", flags.get("slice_17_13_absent", False)),
        ("T", "commit/tag/publish occurred in slice", flags.get("no_publish", False)),
        ("U", "new AWS services created", flags.get("no_new_services", False)),
        ("V", "Cloudflare redesigned", flags.get("no_cloudflare_redesign", False)),
        ("W", "telemetry touched", flags.get("no_telemetry", False)),
        ("X", "evidence missing", flags.get("evidence_present", False)),
        ("Y", "verifier nondeterministic", flags.get("determinism_ok", False)),
        ("Z", "report leaks secrets/paths/account IDs", flags.get("report_safe", False)),
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
