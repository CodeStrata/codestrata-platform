"""Negative scenarios A–Z for Slice 17.10."""

from __future__ import annotations

from verification.community_cloud_production_recovery.models import CheckResult, Defect


def check_scenarios(*, flags: dict[str, bool]) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    scenarios = [
        ("A", "baseline recovery posture missing", flags.get("baseline_ok", False)),
        ("B", "lambda image rollback not ready", flags.get("lambda_image_ok", False)),
        ("C", "lambda config rollback not ready", flags.get("lambda_config_ok", False)),
        ("D", "infrastructure rollback not ready", flags.get("infra_ok", False)),
        ("E", "state recovery not ready", flags.get("state_ok", False)),
        ("F", "state lock recovery not ready", flags.get("lock_ok", False)),
        ("G", "insights rollback not ready", flags.get("insights_ok", False)),
        ("H", "docs rollback not ready", flags.get("docs_ok", False)),
        ("I", "data lake destroy allowed", flags.get("data_lake_safe", False)),
        ("J", "remote state destroy allowed", flags.get("remote_state_safe", False)),
        ("K", "destructive plan gate missing", flags.get("destructive_gate_ok", False)),
        ("L", "final zero drift not required", flags.get("zero_drift_ok", False)),
        ("M", "resource classification incomplete", flags.get("classification_ok", False)),
        ("N", "secrets values leaked in recovery surfaces", flags.get("secrets_ok", False)),
        ("O", "data preservation violated", flags.get("data_safety_ok", False)),
        ("P", "recovery matrix incomplete", flags.get("matrix_ok", False)),
        ("Q", "github IAM bootstrap missing", flags.get("github_iam_ok", False)),
        ("R", "github workflows missing destroy/replace gate", flags.get("github_workflows_ok", False)),
        ("S", "Slice 17.13 started", flags.get("slice_17_13_absent", False)),
        ("T", "commit/tag/publish occurred in slice", flags.get("no_publish", False)),
        ("U", "architecture redesign allowed", flags.get("no_redesign", False)),
        ("V", "application update unsafe", flags.get("application_ok", False)),
        ("W", "security/region/environment gates broken", flags.get("security_ok", False)),
        ("X", "prior 17.1–17.9 regression", flags.get("prior_ok", False)),
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
