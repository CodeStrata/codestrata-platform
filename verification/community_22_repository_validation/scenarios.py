"""Negative scenarios A–Z for Slice 17.13."""

from __future__ import annotations

from verification.community_22_repository_validation.models import CheckResult, Defect


def check_scenarios(*, flags: dict[str, bool]) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    scenarios = [
        ("A", "catalog count is exactly 22", flags.get("catalog_count_22", False)),
        ("B", "cherry-picking forbidden", flags.get("no_cherry_picking", False)),
        ("C", "qualified commit pins present", flags.get("qualified_commits", False)),
        ("D", "assessments under artifact root", flags.get("assessments_under_root", False)),
        ("E", "assessment head artifacts enabled", flags.get("head_artifacts_enabled", False)),
        ("F", "data lake report storage disabled", flags.get("data_lake_storage_disabled", False)),
        ("G", "Slice 17.14 not started", flags.get("slice_17_14_absent", False)),
        ("H", "report text safe from secrets", flags.get("report_text_safe", False)),
        ("I", "manifest has no absolute paths", flags.get("manifest_no_absolute_paths", False)),
        ("J", "suite output under sv17-13", flags.get("suite_path_sv17_13", False)),
        ("K", "individual assessment reports enabled", flags.get("individual_reports_enabled", False)),
        ("L", "portfolio EIR count is 1", flags.get("portfolio_eir_count_1", False)),
        ("M", "telemetry validation enabled", flags.get("telemetry_validation_enabled", False)),
        ("N", "insights validation enabled", flags.get("insights_validation_enabled", False)),
        ("O", "clone URLs are credential-free", flags.get("clone_urls_safe", False)),
        ("P", "global git insteadOf isolated", flags.get("git_config_isolated", False)),
        ("Q", "assessment PASS not invented pre-execution", flags.get("no_invented_pass", False)),
        ("R", "repository register safe fields only", flags.get("register_safe_fields", False)),
        ("S", "no AWS account in outputs", flags.get("no_aws_accounts", False)),
        ("T", "no S3 URIs in outputs", flags.get("no_s3_uris", False)),
        ("U", "catalog sorted deterministically", flags.get("catalog_deterministic", False)),
        ("V", "policy schema matches contract", flags.get("policy_schema_match", False)),
        ("W", "start_slice_17_13 is true", flags.get("start_slice_17_13", False)),
        ("X", "artifact root is .codestrata-artifacts", flags.get("artifact_root_correct", False)),
        ("Y", "release boundary requires no commit", flags.get("release_boundary_open", False)),
        ("Z", "full suite not falsely marked complete", flags.get("suite_not_false_complete", False)),
    ]
    checks: list[CheckResult] = []
    defects: list[Defect] = []
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
