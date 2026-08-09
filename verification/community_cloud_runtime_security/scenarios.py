"""Negative scenarios A–Z for Slice 17.6 (user-specified)."""

from __future__ import annotations

from verification.community_cloud_runtime_security.models import CheckResult, Defect


def check_scenarios(*, flags: dict[str, bool]) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    """Each scenario passes when the corresponding negative condition is absent."""

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    scenarios = [
        ("A", "dashboard password in Git", flags.get("no_password_in_git", False)),
        ("B", "session secret in Git", flags.get("no_session_in_git", False)),
        ("C", "secret value in OpenTofu state", flags.get("no_secret_in_tf_state", False)),
        ("D", "secret value in Lambda environment", flags.get("no_secret_in_lambda_env", False)),
        ("E", "Lambda gets secretsmanager:* on *", flags.get("no_sm_star", False)),
        ("F", "Lambda gets s3:* on *", flags.get("no_s3_star", False)),
        ("G", "Insights reader can write", flags.get("reader_no_write", False)),
        ("H", "reader can read quarantine unexpectedly", flags.get("reader_no_quarantine", False)),
        ("I", "writer can delete accepted objects", flags.get("writer_deny_delete", False)),
        ("J", "writer accesses state bucket", flags.get("writer_no_state_bucket", False)),
        ("K", "production ingestion enabled", flags.get("ingestion_off", False)),
        ("L", "real event created during 17.6", flags.get("no_new_events", False)),
        ("M", "browser/frontend gets AWS secret permission", flags.get("frontend_no_sm", False)),
        ("N", "Bedrock permission added early", flags.get("no_bedrock", False)),
        ("O", "OpenAI/OpenRouter keys configured early", flags.get("no_provider_keys", False)),
        ("P", "DynamoDB/Athena/Glue/RDS/Redis introduced", flags.get("no_unexpected_services", False)),
        ("Q", "auth becomes fail-open", flags.get("auth_fail_closed", False)),
        ("R", "unauthenticated Insights overview works", flags.get("overview_auth_required", False)),
        ("S", "GitHub apply role becomes admin", flags.get("github_not_admin", False)),
        ("T", "operator grants itself broad admin", flags.get("operator_not_admin", False)),
        ("U", "secrets leaked to report/log", flags.get("report_safe", False)),
        ("V", "unbounded IAM retry", flags.get("bounded_iam_retry", False)),
        ("W", "Slice 17.8 starts", flags.get("slice_17_8_absent", False)),
        ("X", "runtime policy ownership ambiguous", flags.get("policy_ownership_clear", False)),
        ("Y", "verifier nondeterministic", flags.get("determinism_ok", False)),
        ("Z", "report leaks secret/account/path/timestamp/event contents", flags.get("report_safe", False)),
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
