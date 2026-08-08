"""Tests for Slice 15.6 community insights metrics verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.community_insights_metrics.activity import ACTIVATION_EXCLUDED
from verification.community_insights_metrics.aggregation_state import (
    CHECKPOINT_REQUIRED_FOR_FIRST_REPEAT,
)
from verification.community_insights_metrics.assessments import CANCELLED_NOT_FAILED
from verification.community_insights_metrics.catalog import all_metric_ids, catalog_entry
from verification.community_insights_metrics.cohort_suppression import (
    MINIMUM_GROUP_COUNT,
)
from verification.community_insights_metrics.completeness import ZERO_NE_UNAVAILABLE
from verification.community_insights_metrics.contract import (
    CONTRACT_RELATIVE,
    METRIC_IDS,
    POLICY_ID,
    POLICY_RELATIVE,
    REQUIRED_METRIC_FIELDS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    monorepo_root_from_here,
)
from verification.community_insights_metrics.determinism import reports_byte_identical
from verification.community_insights_metrics.ecosystems import NO_PACKAGE_NAMES
from verification.community_insights_metrics.freshness import NO_REALTIME_PROMISE
from verification.community_insights_metrics.heads import NO_FINDINGS
from verification.community_insights_metrics.installations import NOT_USERS
from verification.community_insights_metrics.inventory import load_json
from verification.community_insights_metrics.languages import SEPARATE_FROM_ECOSYSTEM
from verification.community_insights_metrics.low_cost_boundary import ATHENA_FALSE
from verification.community_insights_metrics.models_adoption import FAMILY_ONLY
from verification.community_insights_metrics.percentages import AFTER_SUPPRESSION
from verification.community_insights_metrics.privacy import NO_INSTALLATION_ID_IN_API
from verification.community_insights_metrics.providers import (
    UNAVAILABLE_EXCLUDED_FROM_SHARE,
)
from verification.community_insights_metrics.query_horizons import HORIZONS_DEFINED
from verification.community_insights_metrics.release_adoption import SPLIT_CLI_VSCODE
from verification.community_insights_metrics.reporting import write_report
from verification.community_insights_metrics.result_contract import UI_DOES_NOT_COMPUTE
from verification.community_insights_metrics.runner import build_report
from verification.community_insights_metrics.scenarios import METRICS_SCENARIOS
from verification.community_insights_metrics.time_semantics import UTC_REQUIRED
from verification.community_insights_metrics.validation_dataset import (
    EXTERNAL,
    validation_catalog_size,
    validation_has_history_snapshots,
)
from verification.community_insights_metrics.versions import (
    INSTALLATION_SHARE_NOT_EVENT_VOLUME,
)
from verification.community_insights_metrics.vscode import ASSESS_OPS_ONLY


def test_policy() -> None:
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    assert policy["policy_id"] == POLICY_ID
    assert policy["policy_version"] == "1.0"
    assert policy.get("start_slice_16_2", False) is False
    assert policy["production_data_available"] is False
    assert policy["aggregations_allowed_in_15_6"] is False
    assert policy["dashboard_ui_allowed_in_15_6"] is False
    assert policy["authentication_allowed_in_15_6"] is False
    contract = load_json(monorepo, CONTRACT_RELATIVE)
    assert contract["contract_id"] == "community-insights-metrics-contract"
    assert contract["ui_must_not_compute_metrics"] is True


def test_catalog_completeness() -> None:
    monorepo = monorepo_root_from_here()
    assert set(all_metric_ids()) == set(METRIC_IDS)
    assert len(METRIC_IDS) == 15
    for metric_id in METRIC_IDS:
        entry = catalog_entry(monorepo, metric_id)
        for field in REQUIRED_METRIC_FIELDS:
            assert field in entry, f"{metric_id} missing {field}"


def test_time_semantics() -> None:
    assert UTC_REQUIRED is True
    monorepo = monorepo_root_from_here()
    ts = load_json(monorepo, POLICY_RELATIVE)["time_semantics"]
    assert ts["storage_timezone"] == "UTC"
    assert ts["query_windows_timezone"] == "UTC"
    assert ts["dashboard_display_timezone_initial"] == "UTC"
    assert ts["hidden_timezone_conversion_forbidden"] is True


def test_installation_semantics() -> None:
    assert NOT_USERS is True
    monorepo = monorepo_root_from_here()
    entry = catalog_entry(monorepo, "total_anonymous_installations")
    assert entry["display_name"] == "Anonymous installations"
    assert "users" in entry["forbidden_interpretation"]
    assert "raw_event_count" in entry["forbidden_interpretation"]
    assert entry["numerator"] == "distinct_installation_ids"


def test_dau_mau() -> None:
    assert ACTIVATION_EXCLUDED is True
    monorepo = monorepo_root_from_here()
    dau = catalog_entry(monorepo, "daily_active_installations")
    assert "extension_activation" in dau["forbidden_interpretation"]
    mau = catalog_entry(monorepo, "monthly_active_installations")
    assert mau["time_window"] == "rolling_30_utc_days"
    assert mau["display_name"] == "30-day active installations"
    assert "calendar_mau" in mau["forbidden_interpretation"]
    activity = load_json(monorepo, POLICY_RELATIVE)["approved_activity"]
    assert "extension_activate_alone" in activity["excluded"]


def test_assessment_semantics() -> None:
    assert CANCELLED_NOT_FAILED is True
    assert CHECKPOINT_REQUIRED_FOR_FIRST_REPEAT is True
    monorepo = monorepo_root_from_here()
    first = catalog_entry(monorepo, "first_assessments")
    assert (
        "retained_history_first_not_absolute_lifetime_until_15_7_checkpoint"
        in first["known_limitations"]
    )
    repeat = catalog_entry(monorepo, "repeat_assessments")
    assert repeat["numerator"] == "repeat_assessment_events"
    failed = catalog_entry(monorepo, "failed_assessments")
    assert "cancelled_merged_into_failed" in failed["forbidden_interpretation"]
    assert "report_open_failure" in failed["forbidden_interpretation"]


def test_version_adoption() -> None:
    assert INSTALLATION_SHARE_NOT_EVENT_VOLUME is True
    monorepo = monorepo_root_from_here()
    cli = catalog_entry(monorepo, "cli_version_adoption")
    assert "event_count_as_installation_adoption" in cli["forbidden_interpretation"]
    assert cli["denominator"] == "distinct_installations_on_cli_event_in_period"


def test_head_usage() -> None:
    assert NO_FINDINGS is True
    monorepo = monorepo_root_from_here()
    heads = catalog_entry(monorepo, "assessment_head_usage")
    assert "finding_counts" in heads["forbidden_interpretation"]


def test_language_ecosystem() -> None:
    assert SEPARATE_FROM_ECOSYSTEM is True
    assert NO_PACKAGE_NAMES is True
    monorepo = monorepo_root_from_here()
    lang = catalog_entry(monorepo, "language_ecosystem_distribution")
    assert "merged_language_ecosystem_single_axis" in lang["forbidden_interpretation"]
    assert "package_names" in lang["forbidden_interpretation"]
    assert "primary_language_chart" in lang["allowed_dashboard_representation"]
    assert "package_ecosystem_chart" in lang["allowed_dashboard_representation"]


def test_provider_model_family() -> None:
    assert UNAVAILABLE_EXCLUDED_FROM_SHARE is True
    assert FAMILY_ONLY is True
    monorepo = monorepo_root_from_here()
    prov = catalog_entry(monorepo, "ai_provider_adoption")
    assert "provider_quality" in prov["forbidden_interpretation"]
    model = catalog_entry(monorepo, "ai_model_adoption")
    assert model["display_name"] == "AI model family adoption"
    assert "exact_model_adoption" in model["forbidden_interpretation"]


def test_vscode_usage() -> None:
    assert ASSESS_OPS_ONLY is True
    monorepo = monorepo_root_from_here()
    vscode = catalog_entry(monorepo, "vscode_extension_usage")
    assert "activation_as_usage" in vscode["forbidden_interpretation"]


def test_release_adoption() -> None:
    assert SPLIT_CLI_VSCODE is True
    monorepo = monorepo_root_from_here()
    release = catalog_entry(monorepo, "release_adoption")
    assert "merged_cli_vscode_single_version_axis" in release["forbidden_interpretation"]


def test_validation_dataset() -> None:
    assert EXTERNAL is True
    monorepo = monorepo_root_from_here()
    validation = catalog_entry(monorepo, "validation_dataset_growth")
    assert validation["external_internal_source"] == "external_metric_source"
    assert "fabricated_from_telemetry" in validation["forbidden_interpretation"]
    size = validation_catalog_size(monorepo)
    assert size is None or size >= 0
    if not validation_has_history_snapshots(monorepo):
        assert "no_historical_growth_without_snapshots" in validation["known_limitations"]


def test_privacy_allow_deny() -> None:
    assert NO_INSTALLATION_ID_IN_API is True
    monorepo = monorepo_root_from_here()
    privacy = load_json(monorepo, POLICY_RELATIVE)["privacy"]
    assert privacy["raw_events_api_forbidden"] is True
    assert privacy["installation_id_api_response_forbidden"] is True
    assert privacy["authentication_does_not_relax_privacy"] is True
    forbidden = set(privacy["forbidden_exposures"])
    for field in (
        "installation_id",
        "exact_model_id",
        "findings",
        "prompts",
        "ip_address",
    ):
        assert field in forbidden


def test_cohort_suppression() -> None:
    assert MINIMUM_GROUP_COUNT == 3
    monorepo = monorepo_root_from_here()
    cohort = load_json(monorepo, POLICY_RELATIVE)["cohort_suppression"]
    assert cohort["dimensional_breakdown_minimum_group_count"] == 3
    assert cohort["headline_totals_suppress_below_threshold"] is False
    assert cohort["suppressed_group_label"] == "other_suppressed"


def test_percentages() -> None:
    assert AFTER_SUPPRESSION is True
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    assert policy["cohort_suppression"]["percentage_computed_after_suppression"] is True
    assert policy["percentages"]["api_returns_count_and_denominator"] is True


def test_completeness() -> None:
    assert ZERO_NE_UNAVAILABLE is True
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    assert set(policy["completeness_states"]) == {
        "complete",
        "partial",
        "unavailable",
        "not_applicable",
    }
    assert policy["zero_versus_unavailable"]["unavailable_is_different_from_zero"] is True


def test_result_contract() -> None:
    assert UI_DOES_NOT_COMPUTE is True
    monorepo = monorepo_root_from_here()
    result = load_json(monorepo, POLICY_RELATIVE)["metric_result_contract"]
    assert "installation_ids" in result["forbidden_fields"]
    assert result["owners"]["computation"] == "aggregation_service_15_7"


def test_aggregation_state_and_horizons() -> None:
    assert CHECKPOINT_REQUIRED_FOR_FIRST_REPEAT is True
    assert HORIZONS_DEFINED is True
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    state = policy["aggregation_state_requirements_for_15_7"]
    assert state["first_seen_assessment_checkpoint"] is True
    horizons = policy["query_horizons"]
    assert "daily_active_installations" in horizons["daily"]
    assert "monthly_active_installations" in horizons["rolling_30_day"]
    assert "validation_dataset_growth" in horizons["external"]


def test_freshness_and_low_cost() -> None:
    assert NO_REALTIME_PROMISE is True
    assert ATHENA_FALSE is True
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    assert policy["freshness"]["real_time_promise_forbidden"] is True
    low = policy["low_cost_architecture"]
    assert low["athena_required"] is False
    assert low["redis_required"] is False
    assert low["rds_required"] is False


def test_scenarios() -> None:
    assert len(METRICS_SCENARIOS) == 26
    assert METRICS_SCENARIOS[0][0] == "A"
    assert METRICS_SCENARIOS[-1][0] == "Z"


def test_build_report() -> None:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert report.mau_window == "rolling_30_utc_days"
    assert report.cohort_minimum == 3
    assert report.release_posture.get("start_slice_16_2", False) is False
    assert report.release_posture["aggregations_built"] is False
    assert report.release_posture["dashboard_ui_built"] is False
    assert report.release_posture["auth_built"] is False
    assert report.release_posture["commit_created"] is False
    path = write_report(monorepo, report)
    text = Path(path).read_text(encoding="utf-8")
    assert "timestamp" not in text.lower()
    assert "/Users/" not in text
    assert report.privacy_status == "pass"


def test_determinism() -> None:
    monorepo = monorepo_root_from_here()
    a = build_report(monorepo).to_dict()
    b = build_report(monorepo).to_dict()
    assert reports_byte_identical(a, b)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
