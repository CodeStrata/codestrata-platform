"""Negative scenarios A–Z for Slice 17.16."""

from __future__ import annotations

from verification.community_report_publishing.models import CheckResult, Defect


def check_scenarios(*, flags: dict[str, bool]) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    """Each scenario passes when the corresponding negative condition is absent."""

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    scenarios = [
        ("A", "policy start_slice_17_17 false", flags.get("start_slice_17_17_true", False)),
        ("B", "report artifacts stored in Data Lake bucket/prefixes", flags.get("data_lake_separation", False)),
        ("C", "report artifact store not private (missing BPA)", flags.get("private_bpa", False)),
        ("D", "raw S3 URLs returned as public share links", flags.get("no_raw_s3_public", False)),
        ("E", "automatic publish after assessment enabled", flags.get("no_auto_publish_assess", False)),
        ("F", "telemetry opt-in auto-publishes reports", flags.get("telemetry_no_auto_publish", False)),
        ("G", "publishing policy missing required flags", flags.get("policy_flags_ok", False)),
        ("H", "publishing register missing or incomplete", flags.get("publishing_register_ok", False)),
        ("I", "storage register missing or incomplete", flags.get("storage_register_ok", False)),
        ("J", "verification contract missing", flags.get("contract_present", False)),
        ("K", "community-report-artifacts infra module absent", flags.get("infra_module_present", False)),
        ("L", "report bucket name collides with data-lake bucket", flags.get("bucket_names_distinct", False)),
        ("M", "opaque public id module absent", flags.get("opaque_ids_present", False)),
        ("N", "publication sanitizer absent", flags.get("sanitizer_present", False)),
        ("O", "cloud rotation exceeds two versions", flags.get("rotation_max_two", False)),
        ("P", "report API routes incomplete", flags.get("routes_complete", False)),
        ("Q", "engine CLI explicit publish command absent", flags.get("engine_cli_publish", False)),
        ("R", "assess path wires cloud report publish", flags.get("assess_no_cloud_publish", False)),
        ("S", "community-api docs omit report endpoints", flags.get("docs_report_endpoints", False)),
        ("T", "reports.codestrata.ai delivery worker absent or thick", flags.get("delivery_worker_thin", False)),
        ("U", "Data Lake module prefixes include report html/json", flags.get("data_lake_no_report_prefixes", False)),
        ("V", "publish failure deletes local artifacts", flags.get("failure_isolation_ok", False)),
        ("W", "Slice 17.18 verification package started", flags.get("slice_17_18_absent", False)),
        ("X", "live reports TLS/domain pending (soft limitation only)", flags.get("live_ok_or_soft", True)),
        ("Y", "worktree uncommitted or zero-drift evidence absent (soft)", flags.get("operational_or_soft", True)),
        ("Z", "verifier nondeterministic or report leaks secrets/paths/S3", flags.get("determinism_and_safe", False)),
    ]
    soft_letters = frozenset({"X", "Y"})
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
        if not ok and letter not in soft_letters:
            defects.append(Defect("scenario", f"scenario:{letter}", "pass", label))
    return checks, defects, results
