"""Negative scenarios A–Z for Slice 17.7 (user-specified)."""

from __future__ import annotations

from verification.community_cloud_production_ingestion.models import CheckResult, Defect


def check_scenarios(*, flags: dict[str, bool]) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    """Each scenario passes when the corresponding negative condition is absent."""

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    scenarios = [
        ("A", "writer remains unattached after activation", flags.get("writer_attached_after_activation", False)),
        ("B", "ingestion true before writer ready", flags.get("ingestion_after_writer_ready", False)),
        ("C", "writer has DeleteObject allow", flags.get("writer_no_delete", False)),
        ("D", "writer writes state bucket", flags.get("writer_no_state_bucket", False)),
        ("E", "auth bypass", flags.get("auth_fail_closed", False)),
        ("F", "telemetry-disabled client forced to send", flags.get("consent_respected", False)),
        ("G", "repo name enters payload", flags.get("privacy_no_repo_name", False)),
        ("H", "repo path enters payload", flags.get("privacy_no_repo_path", False)),
        ("I", "findings/evidence enter payload", flags.get("privacy_no_findings", False)),
        ("J", "prompt/response enters AI usage", flags.get("privacy_no_prompt_response", False)),
        ("K", "exact model_id enters payload", flags.get("privacy_no_exact_model_id", False)),
        ("L", "machine ID enters extension event", flags.get("privacy_no_machine_id", False)),
        ("M", "package name enters assessment metadata", flags.get("privacy_no_package_name", False)),
        ("N", "identity enters S3 path", flags.get("privacy_no_identity_in_path", False)),
        ("O", "invalid event accepted raw", flags.get("invalid_quarantined_not_raw", False)),
        ("P", "quarantine reason leaks sensitive value", flags.get("quarantine_reason_safe", False)),
        ("Q", "Data Lake bucket becomes public", flags.get("data_lake_private", False)),
        ("R", "report artifact appears in Data Lake", flags.get("no_report_in_lake", False)),
        ("S", "ingestion failure breaks assessment", flags.get("failure_isolated", False)),
        ("T", "unbounded retry", flags.get("bounded_retry", False)),
        ("U", "raw boto error exposed", flags.get("safe_error_taxonomy", False)),
        ("V", "unrelated AWS service introduced", flags.get("no_unexpected_services", False)),
        ("W", "Slice 17.8 starts", flags.get("slice_17_8_absent", False)),
        ("X", "zero-drift fails", flags.get("zero_drift_ok", False)),
        ("Y", "verifier nondeterministic", flags.get("determinism_ok", False)),
        ("Z", "report leaks object keys/IDs/account/path/secret/test poison", flags.get("report_safe", False)),
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
