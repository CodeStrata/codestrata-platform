"""Tests for Slice 15.3 event coverage verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.community_insights_event_coverage.ai_models import (
    model_privacy_decision,
)
from verification.community_insights_event_coverage.contract import (
    DASHBOARD_METRICS,
    POLICY_ID,
    POLICY_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    monorepo_root_from_here,
)
from verification.community_insights_event_coverage.coverage_matrix import (
    build_metric_matrix,
)
from verification.community_insights_event_coverage.determinism import (
    reports_byte_identical,
)
from verification.community_insights_event_coverage.inventory import load_json
from verification.community_insights_event_coverage.reporting import write_report
from verification.community_insights_event_coverage.runner import build_report
from verification.community_insights_event_coverage.scenarios import COVERAGE_SCENARIOS
from verification.community_insights_event_coverage.validation_dataset import (
    validation_dataset_source,
)
from verification.community_insights_event_coverage.vscode import vscode_rules


def test_policy() -> None:
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    assert policy["policy_id"] == POLICY_ID
    assert policy["policy_version"] == "1.0"
    assert policy.get("start_slice_16_2", False) is False
    assert policy["schema_activation_allowed_in_15_3"] is False
    assert policy["model_adoption_decision"] == "C_normalized_model_family_allowed"
    assert set(policy["metric_coverage"]) == set(DASHBOARD_METRICS)


def test_scenarios_a_to_z() -> None:
    assert len(COVERAGE_SCENARIOS) == 26
    assert COVERAGE_SCENARIOS[0][0] == "A"
    assert COVERAGE_SCENARIOS[-1][0] == "Z"


def test_identity_not_event_count() -> None:
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    assert (
        "raw_event_count_without_installation_id"
        in policy["activity_definition"]["do_not_count"]
    )
    assert policy["installation_identity"]["platform_optional"] is True


def test_dau_not_every_event() -> None:
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    assert "extension_activate_alone_as_usage" in policy["activity_definition"][
        "do_not_count"
    ]


def test_first_assessment_derived() -> None:
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    assert policy["metric_coverage"]["first_assessments"]["derive_not_flag"] is True
    assert policy["metric_coverage"]["repeat_assessments"]["derive_not_flag"] is True


def test_success_not_open_report() -> None:
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    assert "open_report" in policy["assessment_success_failure"]["not_authoritative"]


def test_cli_version_not_path() -> None:
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    assert (
        policy["metric_coverage"]["cli_version_adoption"]["executable_path_forbidden"]
        is True
    )


def test_heads_no_findings() -> None:
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    assert (
        policy["metric_coverage"]["assessment_head_usage"]["findings_forbidden"]
        is True
    )


def test_language_no_paths_packages() -> None:
    monorepo = monorepo_root_from_here()
    forbidden = set(policy_forbidden(monorepo))
    assert "file_path" in forbidden
    assert "package_name" in forbidden


def policy_forbidden(monorepo: Path) -> list[str]:
    return list(
        load_json(monorepo, POLICY_RELATIVE).get("privacy_forbidden_dashboard_fields")
        or []
    )


def test_ai_provider_no_credentials() -> None:
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    assert policy["ai_provider_vocab"]["credentials_forbidden"] is True
    assert policy["ai_provider_vocab"]["openrouter_present"] is True


def test_ai_model_privacy_outcome_c() -> None:
    decision = model_privacy_decision()
    assert decision["outcome"] == "C"
    assert decision["exact_model_id_permitted"] is False
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    assert (
        policy["metric_coverage"]["ai_model_adoption"]["exact_model_id_forbidden"]
        is True
    )


def test_vscode_activate_not_usage() -> None:
    rules = vscode_rules()
    assert rules["activate_alone_counts_as_usage"] is False
    assert "assess" in rules["usage_operations"]


def test_validation_external() -> None:
    monorepo = monorepo_root_from_here()
    src = validation_dataset_source(monorepo)
    assert src["present"] is True
    assert src["force_into_telemetry"] is False
    assert src["schema_name"] == "codestrata-repository-catalog"


def test_metric_matrix() -> None:
    monorepo = monorepo_root_from_here()
    rows = build_metric_matrix(monorepo)
    assert len(rows) == 15
    by_id = {r["metric"]: r for r in rows}
    assert by_id["validation_dataset_growth"]["external_metric_source"] is True
    assert by_id["ai_model_adoption"]["status"] == "supported_as_model_family_only"


def test_change_register_implemented() -> None:
    monorepo = monorepo_root_from_here()
    policy = load_json(monorepo, POLICY_RELATIVE)
    for row in policy["change_register"]:
        assert row["activated_in_runtime"] is True
        assert row["status"] == "implemented_in_15_4"


def test_build_report() -> None:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert report.release_posture.get("start_slice_16_2", False) is False
    assert report.release_posture["schema_activated"] is False
    assert len(report.metric_matrix) == 15
    path = write_report(monorepo, report)
    text = Path(path).read_text(encoding="utf-8")
    assert "timestamp" not in text.lower()
    assert "/Users/" not in text


def test_determinism() -> None:
    monorepo = monorepo_root_from_here()
    a = build_report(monorepo).to_dict()
    b = build_report(monorepo).to_dict()
    assert reports_byte_identical(a, b)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
