"""Negative scenarios A–Z for Slice 17.15."""

from __future__ import annotations

from verification.report_artifact_lifecycle.models import CheckResult, Defect


def check_scenarios(*, flags: dict[str, bool]) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    """Each scenario passes when the corresponding negative condition is absent."""

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    scenarios = [
        ("A", "assessment rotation current→previous on success", flags.get("scenario_a_assessment_rotation", False)),
        ("B", "failed assessment does not promote to current", flags.get("scenario_b_failed_assessment", False)),
        ("C", "portfolio membership change preserves portfolio_id", flags.get("scenario_c_membership", False)),
        ("D", "policy start_slice_17_16 false", flags.get("start_slice_17_16_true", False)),
        ("E", "run-id-only folder model is sole authority", flags.get("human_readable_folder_authority", False)),
        ("F", "Data Lake uses report retention", flags.get("data_lake_no_retention", False)),
        ("G", "more than 2 assessment versions in policy", flags.get("max_two_assessment_versions", False)),
        ("H", "more than 2 EIR versions in policy", flags.get("max_two_eir_versions", False)),
        ("I", "repository_id not filesystem-safe", flags.get("repository_id_safe", False)),
        ("J", "portfolio_id uses run-stamped folder name", flags.get("portfolio_id_human", False)),
        ("K", "run_ids not metadata-only", flags.get("run_ids_metadata", False)),
        ("L", "rotation not atomic per policy", flags.get("rotation_atomic", False)),
        ("M", "validation artifacts use report retention", flags.get("validation_no_retention", False)),
        ("N", "failed EIR promotes to current", flags.get("failed_eir_no_promote", False)),
        ("O", "prior Epic 17 verification boundary missing", flags.get("prior_boundary_present", False)),
        ("P", "report retention policy missing", flags.get("policy_present", False)),
        ("Q", "lifecycle register missing", flags.get("register_present", False)),
        ("R", "engine lifecycle module absent (soft until wired)", flags.get("engine_lifecycle_or_soft", True)),
        ("S", "manifest lacks data lake forbidden boundary", flags.get("manifest_data_lake_boundary", False)),
        ("T", "secrets in slice paths", flags.get("no_secrets", False)),
        ("U", "legacy run-id folder aliases only (soft)", flags.get("legacy_aliases_or_soft", True)),
        ("V", "previous slot UI deferred (soft)", flags.get("previous_ui_deferred_or_soft", True)),
        ("W", "cloud report lifecycle deferred (soft)", flags.get("cloud_deferred_or_soft", True)),
        ("X", "monorepo pre-cutover (soft)", flags.get("monorepo_pre_cutover_or_soft", True)),
        ("Y", "verifier nondeterministic", flags.get("determinism_ok", False)),
        ("Z", "report leaks paths/secrets/account IDs", flags.get("report_safe", False)),
    ]
    soft_letters = frozenset({"R", "U", "V", "W", "X"})
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
