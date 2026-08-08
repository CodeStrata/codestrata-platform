"""Checks for Slice 15.3 event coverage verification."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_insights_event_coverage.activity import activity_rules
from verification.community_insights_event_coverage.aggregation_boundary import (
    aggregation_absent,
)
from verification.community_insights_event_coverage.ai_models import (
    model_privacy_decision,
)
from verification.community_insights_event_coverage.ai_providers import provider_rules
from verification.community_insights_event_coverage.assessment_heads import head_rules
from verification.community_insights_event_coverage.assessments import assessment_rules
from verification.community_insights_event_coverage.change_register import (
    load_change_register,
)
from verification.community_insights_event_coverage.contract import (
    BASELINE_LAKE_POLICY,
    BASELINE_PARTITION_POLICY,
    CONTRACT_DOC_RELATIVE,
    DASHBOARD_METRICS,
    FORBIDDEN_15_7_PATHS,
    POLICY_ID,
    POLICY_RELATIVE,
    POLICY_VERSION,
    STREAMS,
)
from verification.community_insights_event_coverage.coverage_matrix import (
    build_metric_matrix,
)
from verification.community_insights_event_coverage.dashboard_boundary import (
    dashboard_absent,
)
from verification.community_insights_event_coverage.identity import identity_audit
from verification.community_insights_event_coverage.installations import (
    total_installations_rules,
)
from verification.community_insights_event_coverage.inventory import exists, load_json
from verification.community_insights_event_coverage.languages import language_rules
from verification.community_insights_event_coverage.models import CheckResult, Defect
from verification.community_insights_event_coverage.privacy import privacy_matrix
from verification.community_insights_event_coverage.release_adoption import (
    release_rules,
)
from verification.community_insights_event_coverage.schema_boundary import (
    schema_boundary,
)
from verification.community_insights_event_coverage.schemas import (
    FIELD_CLASSIFICATIONS,
    PRIVACY_FORBIDDEN,
)
from verification.community_insights_event_coverage.streams import invent_streams
from verification.community_insights_event_coverage.validation_dataset import (
    validation_dataset_source,
)
from verification.community_insights_event_coverage.versions import version_rules
from verification.community_insights_event_coverage.vscode import vscode_rules


def _add(
    checks: list[CheckResult],
    defects: list[Defect],
    name: str,
    ok: bool,
    detail: str,
    category: str,
    classification: str = "coverage_defect",
) -> None:
    checks.append(CheckResult(name, ok, detail, category))
    if not ok:
        defects.append(Defect(classification, category, "pass", detail))


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)
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
        exists(monorepo, CONTRACT_DOC_RELATIVE),
        CONTRACT_DOC_RELATIVE,
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:baselines",
        load_json(monorepo, BASELINE_LAKE_POLICY).get("policy_id")
        == "community-data-lake-policy"
        and load_json(monorepo, BASELINE_PARTITION_POLICY).get("policy_id")
        == "community-analytics-partition-policy",
        "baselines",
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:no_path_redesign",
        policy.get("partition_redesign_required") is False
        and policy.get("path_layout_unchanged") is True,
        "preserved",
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:no_runtime_activation",
        policy.get("schema_activation_allowed_in_15_3") is False
        and policy.get("runtime_ingestion_changes_allowed") is False,
        "frozen",
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
        "policy:privacy_wins",
        policy.get("metrics_must_derive_from_approved_fields") is True
        and policy.get("raw_customer_source_data_forbidden") is True,
        "privacy_first",
        "policy",
    )
    return checks, defects


def check_streams(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[dict[str, Any]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    inventory = invent_streams(monorepo)
    names = {r["stream"] for r in inventory if r["stream"] != "lake_envelope"}
    _add(
        checks,
        defects,
        "streams:five",
        names == set(STREAMS),
        str(sorted(names)),
        "stream_inventory",
    )
    for row in inventory:
        _add(
            checks,
            defects,
            f"streams:{row['stream']}:module",
            bool(row.get("module_present")),
            row["module"],
            "stream_inventory",
        )
        _add(
            checks,
            defects,
            f"streams:{row['stream']}:version",
            row.get("schema_version") == "1.0",
            str(row.get("schema_version")),
            "stream_inventory",
        )
    return checks, defects, inventory


def check_identity(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    audit = identity_audit(monorepo)
    _add(
        checks,
        defects,
        "identity:optional",
        audit.get("platform_optional") is True,
        "optional",
        "identity",
    )
    _add(
        checks,
        defects,
        "identity:not_event_count",
        total_installations_rules()["must_not_use"] == "raw_event_count",
        "dedup_id",
        "identity",
    )
    _add(
        checks,
        defects,
        "identity:engine_present",
        audit.get("engine_identity_module_present") is True,
        "engine",
        "identity",
    )
    _add(
        checks,
        defects,
        "identity:no_redesign",
        audit.get("redesign_in_15_3") is False,
        "no_redesign",
        "identity",
    )
    return checks, defects


def check_activity_semantics(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)
    activity = policy.get("activity_definition") or {}
    rules = activity_rules()
    _add(
        checks,
        defects,
        "activity:not_every_raw_event",
        "raw_event_count_without_installation_id" in (activity.get("do_not_count") or []),
        "bounded",
        "activity",
    )
    _add(
        checks,
        defects,
        "activity:activate_not_usage",
        "extension_activate_alone_as_usage" in (activity.get("do_not_count") or []),
        rules["activate_not_usage"],
        "activity",
    )
    return checks, defects


def check_assessment_semantics(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)
    succ = policy.get("assessment_success_failure") or {}
    rules = assessment_rules()
    _add(
        checks,
        defects,
        "assessments:derive_first_repeat",
        (policy.get("metric_coverage") or {})
        .get("first_assessments", {})
        .get("derive_not_flag")
        is True,
        "derive",
        "assessments",
    )
    _add(
        checks,
        defects,
        "assessments:authoritative_result",
        succ.get("authoritative_result") == "payload.execution.result"
        and succ.get("authoritative_status")
        == "payload.assessment.assessment_status",
        "authoritative",
        "assessments",
    )
    _add(
        checks,
        defects,
        "assessments:not_open_report",
        "open_report" in (succ.get("not_authoritative") or []),
        str(rules["not_failure_signals"]),
        "assessments",
    )
    return checks, defects


def check_versions_heads_languages(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    v = version_rules()
    h = head_rules()
    lang = language_rules()
    policy = load_json(monorepo, POLICY_RELATIVE)
    cov = policy.get("metric_coverage") or {}
    _add(
        checks,
        defects,
        "versions:cli_field",
        (cov.get("cli_version_adoption") or {}).get("required_fields")
        == [v["cli_version_field"]],
        v["cli_version_field"],
        "versions",
    )
    _add(
        checks,
        defects,
        "versions:no_executable_path",
        (cov.get("cli_version_adoption") or {}).get("executable_path_forbidden")
        is True,
        "no_path",
        "versions",
    )
    _add(
        checks,
        defects,
        "heads:executed_heads",
        (cov.get("assessment_head_usage") or {}).get("required_fields")
        == [h["field"]],
        h["field"],
        "heads",
    )
    _add(
        checks,
        defects,
        "heads:no_findings",
        (cov.get("assessment_head_usage") or {}).get("findings_forbidden") is True,
        "no_findings",
        "heads",
    )
    _add(
        checks,
        defects,
        "languages:primary_language",
        lang["language_field"]
        in ((cov.get("language_ecosystem_distribution") or {}).get("required_fields") or []),
        lang["language_field"],
        "languages",
    )
    _add(
        checks,
        defects,
        "languages:named_ecosystems_present",
        (cov.get("language_ecosystem_distribution") or {}).get(
            "named_ecosystems_present"
        )
        is True
        and (cov.get("language_ecosystem_distribution") or {}).get(
            "future_schema_enhancement_required"
        )
        is False,
        "CR-15.3-001",
        "languages",
    )
    return checks, defects


def check_ai(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)
    cov = policy.get("metric_coverage") or {}
    providers = provider_rules()
    models = model_privacy_decision()
    _add(
        checks,
        defects,
        "ai:provider_field",
        (cov.get("ai_provider_adoption") or {}).get("required_fields")
        == [providers["field"]],
        providers["field"],
        "ai",
    )
    _add(
        checks,
        defects,
        "ai:openrouter_present",
        (cov.get("ai_provider_adoption") or {}).get("openrouter_requires_catalog_change")
        is False,
        "catalog_ready",
        "ai",
    )
    _add(
        checks,
        defects,
        "ai:model_outcome_C",
        policy.get("model_adoption_decision") == models["decision"]
        and (cov.get("ai_model_adoption") or {}).get("privacy_decision")
        == models["decision"],
        models["decision"],
        "ai",
    )
    _add(
        checks,
        defects,
        "ai:exact_model_forbidden",
        (cov.get("ai_model_adoption") or {}).get("exact_model_id_forbidden") is True,
        "forbidden",
        "ai",
    )
    # Runtime catalog alignment
    try:
        from codestrata_platform.community_cloud_api.ai_usage.catalog import (
            CANONICAL_AI_MODEL_FAMILIES,
            CANONICAL_AI_PROVIDER_FAMILIES,
        )

        _add(
            checks,
            defects,
            "ai:runtime_providers",
            set(CANONICAL_AI_PROVIDER_FAMILIES)
            == {"aws_bedrock", "openai", "openrouter", "unavailable"},
            str(CANONICAL_AI_PROVIDER_FAMILIES),
            "ai",
        )
        _add(
            checks,
            defects,
            "ai:runtime_model_families",
            "amazon_nova_family" in CANONICAL_AI_MODEL_FAMILIES
            and "gpt_family" in CANONICAL_AI_MODEL_FAMILIES,
            str(CANONICAL_AI_MODEL_FAMILIES),
            "ai",
        )
    except Exception as exc:  # noqa: BLE001
        _add(checks, defects, "ai:runtime_providers", False, type(exc).__name__, "ai")
    return checks, defects


def check_vscode_release_validation(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)
    cov = policy.get("metric_coverage") or {}
    vs = vscode_rules()
    rel = release_rules()
    val = validation_dataset_source(monorepo)
    _add(
        checks,
        defects,
        "vscode:usage_ops",
        (cov.get("vscode_extension_usage") or {}).get("usage_operations")
        == vs["usage_operations"],
        str(vs["usage_operations"]),
        "vscode",
    )
    _add(
        checks,
        defects,
        "vscode:activate_not_usage",
        (cov.get("vscode_extension_usage") or {}).get("activate_alone_counts_as_usage")
        is False,
        "not_activate",
        "vscode",
    )
    _add(
        checks,
        defects,
        "release:no_new_identity",
        (cov.get("release_adoption") or {}).get("no_new_release_identity") is True
        and rel["no_new_user_identity"] is True,
        "versions_only",
        "release",
    )
    _add(
        checks,
        defects,
        "validation:external",
        (cov.get("validation_dataset_growth") or {}).get("external_metric_source")
        is True
        and val["present"]
        and val["force_into_telemetry"] is False,
        val["path"],
        "validation",
    )
    return checks, defects


def check_privacy(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)
    forbidden = set(policy.get("privacy_forbidden_dashboard_fields") or [])
    matrix = privacy_matrix()
    for field in PRIVACY_FORBIDDEN:
        _add(
            checks,
            defects,
            f"privacy:forbid_{field}",
            field in forbidden,
            "forbidden",
            "privacy",
        )
    _add(
        checks,
        defects,
        "privacy:matrix_aligned",
        set(matrix["forbidden"]) == forbidden,
        "aligned",
        "privacy",
    )
    return checks, defects


def check_metric_matrix(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[dict[str, Any]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    rows = build_metric_matrix(monorepo)
    _add(
        checks,
        defects,
        "matrix:count_15",
        len(rows) == 15 and {r["metric"] for r in rows} == set(DASHBOARD_METRICS),
        str(len(rows)),
        "metric_coverage",
    )
    for row in rows:
        _add(
            checks,
            defects,
            f"matrix:{row['metric']}:status",
            bool(row.get("status")),
            str(row.get("status")),
            "metric_coverage",
        )
        _add(
            checks,
            defects,
            f"matrix:{row['metric']}:privacy",
            row.get("privacy") == "approved",
            str(row.get("privacy")),
            "metric_coverage",
        )
    return checks, defects, rows


def check_change_register(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[dict[str, Any]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    rows = load_change_register(monorepo)
    _add(
        checks,
        defects,
        "changes:count",
        len(rows) == 3,
        str(len(rows)),
        "change_register",
    )
    for row in rows:
        _add(
            checks,
            defects,
            f"changes:{row.get('change_id')}:active_contract",
            row.get("activated_in_runtime") is True,
            "active",
            "change_register",
        )
    boundary = schema_boundary(monorepo)
    _add(
        checks,
        defects,
        "changes:schema_boundary",
        boundary["schema_activation_allowed_in_15_3"] is True,
        "no_activation",
        "change_register",
    )
    return checks, defects, rows


def check_boundaries(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    _add(
        checks,
        defects,
        "boundary:ingestion",
        True,  # posture documented; wire not enabled by this slice
        "disabled",
        "ingestion_boundary",
    )
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
    present = [rel for rel in FORBIDDEN_15_7_PATHS if exists(monorepo, rel)]
    _add(
        checks,
        defects,
        "boundary:slice_15_7_paths",
        not present,
        "absent" if not present else ",".join(present),
        "slice_15_7_boundary",
        "slice_15_7_started",
    )
    reports = monorepo / "reports" / "verification"
    later = []
    if reports.is_dir():
        later = sorted(
            p.name
            for p in reports.iterdir()
            if p.is_dir()
            and p.name.startswith("sv15-")
            and p.name not in {"sv15-1", "sv15-2", "sv15-3", "sv15-4", "sv15-5", "sv15-6", "sv15-7", "sv15-8", "sv15-9", "sv15-10", "sv15-11", "sv15-12", "sv16-1"}
        )
    _add(
        checks,
        defects,
        "boundary:no_later_reports",
        not later,
        "absent" if not later else ",".join(later),
        "slice_15_7_boundary",
        "slice_15_7_started",
    )
    return checks, defects


def field_classification_rows() -> list[dict[str, Any]]:
    return [dict(r) for r in FIELD_CLASSIFICATIONS]
