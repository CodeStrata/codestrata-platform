"""Checks for Slice 15.6 metrics & privacy verification."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_insights_metrics.aggregation_boundary import (
    aggregation_absent,
)
from verification.community_insights_metrics.auth_boundary import auth_package_absent
from verification.community_insights_metrics.cohort_suppression import (
    MINIMUM_GROUP_COUNT,
)
from verification.community_insights_metrics.contract import (
    CONTRACT_RELATIVE,
    DOC_RELATIVE,
    FORBIDDEN_15_7_PATHS,
    METRIC_IDS,
    POLICY_ID,
    POLICY_VERSION,
    REQUIRED_METRIC_FIELDS,
)
from verification.community_insights_metrics.dashboard_boundary import dashboard_absent
from verification.community_insights_metrics.inventory import exists, load_json
from verification.community_insights_metrics.models import CheckResult, Defect
from verification.community_insights_metrics.policy import load_metrics_policy
from verification.community_insights_metrics.query_horizons import HORIZON_KEYS
from verification.community_insights_metrics.validation_dataset import (
    VALIDATION_CATALOG_RELATIVE,
    validation_has_history_snapshots,
)


def _add(
    checks: list[CheckResult],
    defects: list[Defect],
    name: str,
    ok: bool,
    detail: str,
    category: str,
    classification: str = "metrics_contract_defect",
) -> None:
    checks.append(CheckResult(name, ok, detail, category))
    if not ok:
        defects.append(Defect(classification, category, "pass", detail))


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_metrics_policy(monorepo)
    _add(checks, defects, "policy:present", bool(policy), "present", "policy")
    _add(
        checks,
        defects,
        "policy:id",
        policy.get("policy_id") == POLICY_ID,
        str(policy.get("policy_id")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:version",
        policy.get("policy_version") == POLICY_VERSION,
        str(policy.get("policy_version")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:doc",
        exists(monorepo, DOC_RELATIVE),
        DOC_RELATIVE,
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:contract",
        load_json(monorepo, CONTRACT_RELATIVE).get("contract_id")
        == "community-insights-metrics-contract",
        "present",
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:start_slice_16_3_false",
        policy.get("start_slice_16_3", False) is False,
        str(policy.get("start_slice_16_3", False)),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:no_live_data_claim",
        policy.get("production_data_available") is False
        and policy.get("production_ingestion_enabled") is False,
        "unwired",
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:utc",
        (policy.get("time_semantics") or {}).get("storage_timezone") == "UTC"
        and (policy.get("time_semantics") or {}).get("query_windows_timezone") == "UTC",
        "utc",
        "policy",
    )
    wording = policy.get("display_wording") or {}
    _add(
        checks,
        defects,
        "policy:not_users",
        wording.get("users_label_forbidden") is True
        and wording.get("installations_label") == "Anonymous installations",
        "anonymous",
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:mau_rolling_30",
        wording.get("mau_display_label") == "30-day active installations"
        and wording.get("calendar_mau_label_forbidden_for_rolling_30") is True,
        "rolling_30",
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:model_family_label",
        wording.get("ai_model_family_label") == "AI model family adoption"
        and wording.get("exact_ai_model_adoption_label_forbidden") is True,
        "family",
        "policy",
    )
    return checks, defects


def check_catalog(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[dict[str, Any]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_metrics_policy(monorepo)
    catalog = policy.get("metric_catalog") or {}
    summaries: list[dict[str, Any]] = []
    _add(
        checks,
        defects,
        "catalog:count_15",
        set(catalog) == set(METRIC_IDS),
        str(len(catalog)),
        "catalog",
    )
    for metric_id in METRIC_IDS:
        entry = catalog.get(metric_id) or {}
        missing = [f for f in REQUIRED_METRIC_FIELDS if f not in entry]
        _add(
            checks,
            defects,
            f"catalog:{metric_id}:fields",
            not missing,
            "ok" if not missing else ",".join(missing),
            "catalog",
        )
        summaries.append(
            {
                "metric_id": metric_id,
                "display_name": entry.get("display_name"),
                "time_window": entry.get("time_window"),
                "privacy_classification": entry.get("privacy_classification"),
                "external_internal_source": entry.get("external_internal_source"),
            }
        )

    # Semantic freezes
    total = catalog.get("total_anonymous_installations") or {}
    _add(
        checks,
        defects,
        "catalog:total_not_users",
        "users" in (total.get("forbidden_interpretation") or [])
        and "raw_event_count" in (total.get("forbidden_interpretation") or []),
        "frozen",
        "catalog",
    )
    dau = catalog.get("daily_active_installations") or {}
    _add(
        checks,
        defects,
        "catalog:dau_not_activation",
        "extension_activation" in (dau.get("forbidden_interpretation") or []),
        "frozen",
        "catalog",
    )
    mau = catalog.get("monthly_active_installations") or {}
    _add(
        checks,
        defects,
        "catalog:mau_rolling",
        mau.get("time_window") == "rolling_30_utc_days"
        and "calendar_mau" in (mau.get("forbidden_interpretation") or []),
        "rolling_30",
        "catalog",
    )
    first = catalog.get("first_assessments") or {}
    _add(
        checks,
        defects,
        "catalog:first_retained_history",
        "retained_history_first_not_absolute_lifetime_until_15_7_checkpoint"
        in (first.get("known_limitations") or []),
        "limited",
        "catalog",
    )
    repeat = catalog.get("repeat_assessments") or {}
    _add(
        checks,
        defects,
        "catalog:repeat_events",
        repeat.get("numerator") == "repeat_assessment_events"
        and "repeat_installation_count_as_primary"
        in (repeat.get("forbidden_interpretation") or []),
        "events",
        "catalog",
    )
    failed = catalog.get("failed_assessments") or {}
    _add(
        checks,
        defects,
        "catalog:cancelled_not_failed",
        "cancelled_merged_into_failed" in (failed.get("forbidden_interpretation") or [])
        and "report_open_failure" in (failed.get("forbidden_interpretation") or []),
        "frozen",
        "catalog",
    )
    cli = catalog.get("cli_version_adoption") or {}
    _add(
        checks,
        defects,
        "catalog:cli_not_event_volume",
        "event_count_as_installation_adoption"
        in (cli.get("forbidden_interpretation") or []),
        "share",
        "catalog",
    )
    heads = catalog.get("assessment_head_usage") or {}
    _add(
        checks,
        defects,
        "catalog:heads_no_findings",
        "finding_counts" in (heads.get("forbidden_interpretation") or []),
        "no_findings",
        "catalog",
    )
    lang = catalog.get("language_ecosystem_distribution") or {}
    _add(
        checks,
        defects,
        "catalog:language_ecosystem_separate",
        "merged_language_ecosystem_single_axis"
        in (lang.get("forbidden_interpretation") or [])
        and "package_names" in (lang.get("forbidden_interpretation") or []),
        "separate",
        "catalog",
    )
    prov = catalog.get("ai_provider_adoption") or {}
    _add(
        checks,
        defects,
        "catalog:provider_not_quality",
        "provider_quality" in (prov.get("forbidden_interpretation") or []),
        "not_quality",
        "catalog",
    )
    model = catalog.get("ai_model_adoption") or {}
    _add(
        checks,
        defects,
        "catalog:model_family_only",
        model.get("display_name") == "AI model family adoption"
        and "exact_model_adoption" in (model.get("forbidden_interpretation") or []),
        "family",
        "catalog",
    )
    vscode = catalog.get("vscode_extension_usage") or {}
    _add(
        checks,
        defects,
        "catalog:vscode_not_activation",
        "activation_as_usage" in (vscode.get("forbidden_interpretation") or []),
        "assess_ops",
        "catalog",
    )
    release = catalog.get("release_adoption") or {}
    _add(
        checks,
        defects,
        "catalog:release_split",
        "merged_cli_vscode_single_version_axis"
        in (release.get("forbidden_interpretation") or []),
        "split",
        "catalog",
    )
    validation = catalog.get("validation_dataset_growth") or {}
    _add(
        checks,
        defects,
        "catalog:validation_external",
        validation.get("external_internal_source") == "external_metric_source"
        and "fabricated_from_telemetry"
        in (validation.get("forbidden_interpretation") or []),
        "external",
        "catalog",
    )
    activity = policy.get("approved_activity") or {}
    _add(
        checks,
        defects,
        "activity:activate_excluded",
        "extension_activate_alone" in (activity.get("excluded") or []),
        "excluded",
        "catalog",
    )
    return checks, defects, summaries


def check_privacy_completeness(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_metrics_policy(monorepo)
    privacy = policy.get("privacy") or {}
    _add(
        checks,
        defects,
        "privacy:no_raw_events",
        privacy.get("raw_events_api_forbidden") is True,
        "forbidden",
        "privacy",
    )
    _add(
        checks,
        defects,
        "privacy:no_installation_id_api",
        privacy.get("installation_id_api_response_forbidden") is True,
        "forbidden",
        "privacy",
    )
    _add(
        checks,
        defects,
        "privacy:auth_does_not_relax",
        privacy.get("authentication_does_not_relax_privacy") is True,
        "strict",
        "privacy",
    )
    forbidden = set(privacy.get("forbidden_exposures") or [])
    for field in (
        "installation_id",
        "exact_model_id",
        "findings",
        "repository_name",
        "prompts",
        "ip_address",
    ):
        _add(
            checks,
            defects,
            f"privacy:forbid_{field}",
            field in forbidden,
            "forbidden",
            "privacy",
        )
    cohort = policy.get("cohort_suppression") or {}
    _add(
        checks,
        defects,
        "privacy:cohort_min_3",
        cohort.get("dimensional_breakdown_minimum_group_count") == MINIMUM_GROUP_COUNT,
        str(cohort.get("dimensional_breakdown_minimum_group_count")),
        "privacy",
    )
    _add(
        checks,
        defects,
        "privacy:pct_after_suppression",
        cohort.get("percentage_computed_after_suppression") is True,
        "after",
        "privacy",
    )
    _add(
        checks,
        defects,
        "privacy:headline_not_suppressed",
        cohort.get("headline_totals_suppress_below_threshold") is False,
        "headline_ok",
        "privacy",
    )
    completeness = set(policy.get("completeness_states") or [])
    for state in ("complete", "partial", "unavailable", "not_applicable"):
        _add(
            checks,
            defects,
            f"completeness:{state}",
            state in completeness,
            "present",
            "completeness",
        )
    zvu = policy.get("zero_versus_unavailable") or {}
    _add(
        checks,
        defects,
        "completeness:zero_ne_unavailable",
        zvu.get("unavailable_is_different_from_zero") is True
        and zvu.get("budget_exceeded_must_not_become_zero") is True,
        "distinct",
        "completeness",
    )
    result = policy.get("metric_result_contract") or {}
    _add(
        checks,
        defects,
        "result:ui_not_compute",
        load_json(monorepo, CONTRACT_RELATIVE).get("ui_must_not_compute_metrics")
        is True,
        "aggregation_owns",
        "completeness",
    )
    _add(
        checks,
        defects,
        "result:no_raw_fields",
        "raw_events" in (result.get("forbidden_fields") or [])
        and "installation_ids" in (result.get("forbidden_fields") or []),
        "clean",
        "completeness",
    )
    state = policy.get("aggregation_state_requirements_for_15_7") or {}
    _add(
        checks,
        defects,
        "state:first_seen_checkpoint",
        state.get("first_seen_assessment_checkpoint") is True,
        "required",
        "completeness",
    )
    freshness = policy.get("freshness") or {}
    _add(
        checks,
        defects,
        "freshness:no_realtime",
        freshness.get("real_time_promise_forbidden") is True,
        "near_current",
        "completeness",
    )
    low = policy.get("low_cost_architecture") or {}
    _add(
        checks,
        defects,
        "low_cost:no_athena",
        low.get("athena_required") is False
        and low.get("redis_required") is False
        and low.get("rds_required") is False,
        "direct_s3",
        "completeness",
    )
    horizons = policy.get("query_horizons") or {}
    _add(
        checks,
        defects,
        "horizons:keys",
        all(k in horizons for k in HORIZON_KEYS),
        "mapped",
        "completeness",
    )
    _add(
        checks,
        defects,
        "validation:catalog_present",
        exists(monorepo, VALIDATION_CATALOG_RELATIVE),
        VALIDATION_CATALOG_RELATIVE,
        "completeness",
    )
    has_history = validation_has_history_snapshots(monorepo)
    validation_metric = (policy.get("metric_catalog") or {}).get(
        "validation_dataset_growth"
    ) or {}
    limitations = validation_metric.get("known_limitations") or []
    honest = (
        "no_historical_growth_without_snapshots" in limitations
        if not has_history
        else True
    )
    _add(
        checks,
        defects,
        "validation:growth_limitation_honest",
        honest,
        "honest" if not has_history else "has_snapshots",
        "completeness",
    )
    return checks, defects


def check_boundaries(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    _add(
        checks,
        defects,
        "boundary:aggregation",
        aggregation_absent(monorepo),
        "absent",
        "aggregation_boundary",
    )
    _add(
        checks,
        defects,
        "boundary:dashboard",
        dashboard_absent(monorepo),
        "absent",
        "dashboard_boundary",
    )
    _add(
        checks,
        defects,
        "boundary:auth",
        auth_package_absent(monorepo),
        "absent",
        "auth_boundary",
    )
    present = [rel for rel in FORBIDDEN_15_7_PATHS if exists(monorepo, rel)]
    _add(
        checks,
        defects,
        "boundary:slice_15_8_paths",
        not present,
        "absent" if not present else ",".join(present),
        "slice_15_8_boundary",
        "slice_15_8_started",
    )
    reports = monorepo / "reports" / "verification"
    later = []
    if reports.is_dir():
        later = sorted(
            p.name
            for p in reports.iterdir()
            if p.is_dir()
            and p.name.startswith("sv15-")
            and p.name
            not in {
                "sv15-1",
                "sv15-2",
                "sv15-3",
                "sv15-4",
                "sv15-5",
                "sv15-6",
                "sv15-7",
                "sv15-8",
                "sv15-9",
                "sv15-10",
                "sv15-11",
                "sv15-12",
                "sv16-1",
            }
        )
    _add(
        checks,
        defects,
        "boundary:no_later_reports",
        not later,
        "absent" if not later else ",".join(later),
        "slice_15_8_boundary",
        "slice_15_8_started",
    )
    return checks, defects
