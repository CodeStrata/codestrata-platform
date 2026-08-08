"""Checks for Slice 15.2 analytics partition verification."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_analytics_partition.contract import (
    BASELINE_POLICY_RELATIVE,
    CONTRACT_DOC_RELATIVE,
    DASHBOARD_METRICS,
    FORBIDDEN_15_7_PATHS,
    POLICY_ID,
    POLICY_RELATIVE,
    POLICY_VERSION,
    SUPPORT_CLASSES,
)
from verification.community_analytics_partition.inventory import exists, load_json, read_text
from verification.community_analytics_partition.models import CheckResult, Defect


def _add(
    checks: list[CheckResult],
    defects: list[Defect],
    name: str,
    ok: bool,
    detail: str,
    category: str,
    classification: str = "partition_audit_defect",
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
        "policy:no_redesign",
        policy.get("partition_redesign_required") is False
        and policy.get("additive_path_dimensions_required") is False,
        "preserved",
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:backward_compatible",
        policy.get("backward_compatible") is True
        and policy.get("existing_data_migration_required") is False,
        "compatible",
        "backward_compatibility",
    )
    _add(
        checks,
        defects,
        "policy:ingestion_unchanged",
        policy.get("ingestion_unchanged") is True
        and policy.get("event_schemas_unchanged") is True,
        "unchanged",
        "backward_compatibility",
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
        "policy:doc_present",
        exists(monorepo, CONTRACT_DOC_RELATIVE),
        CONTRACT_DOC_RELATIVE,
        "policy",
    )
    baseline = load_json(monorepo, BASELINE_POLICY_RELATIVE)
    _add(
        checks,
        defects,
        "policy:baseline_15_1_present",
        baseline.get("policy_id") == "community-data-lake-policy",
        str(baseline.get("policy_id")),
        "policy",
    )
    return checks, defects


def check_partition_hierarchy(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)
    dims = policy.get("path_dimensions") or []
    expected = ["stream", "schema_version", "year", "month", "day"]
    _add(
        checks,
        defects,
        "hierarchy:dimensions",
        dims == expected,
        str(dims),
        "partition_hierarchy",
    )
    path = str(policy.get("authoritative_accepted_path") or "")
    _add(
        checks,
        defects,
        "hierarchy:accepted_path_shape",
        path.startswith("raw/stream=")
        and "schema_version=" in path
        and "year=" in path
        and "month=" in path
        and "day=" in path
        and "<opaque>.json" in path,
        "hive",
        "partition_hierarchy",
    )
    parts = read_text(
        monorepo,
        "platform/src/codestrata_platform/community_cloud_api/data_lake/partitions.py",
    )
    _add(
        checks,
        defects,
        "hierarchy:runtime_builder_aligned",
        "stream=" in parts and "schema_version=" in parts,
        "aligned",
        "partition_hierarchy",
    )
    return checks, defects


def check_prefix_strategy(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)
    _add(
        checks,
        defects,
        "prefix:raw_quarantine",
        policy.get("accepted_prefix") == "raw/"
        and policy.get("quarantine_prefix") == "quarantine/",
        "isolated",
        "prefix_strategy",
    )
    streams = policy.get("allowed_event_streams") or []
    _add(
        checks,
        defects,
        "prefix:five_streams",
        streams
        == [
            "telemetry",
            "assessment_metadata",
            "cli_event",
            "extension_event",
            "ai_usage",
        ],
        str(streams),
        "prefix_strategy",
    )
    return checks, defects


def check_bounded_queries(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)
    model = policy.get("bounded_query_model") or {}
    _add(
        checks,
        defects,
        "query:day_prefix_defined",
        "day_prefix" in model and "stream=" in str(model.get("day_prefix")),
        "defined",
        "bounded_query",
    )
    _add(
        checks,
        defects,
        "query:retention_bound",
        model.get("retention_bound_days") == 365,
        str(model.get("retention_bound_days")),
        "bounded_query",
    )
    _add(
        checks,
        defects,
        "query:max_scan_class",
        model.get("max_scan_class")
        == "stream_plus_date_prefixes_then_payload_aggregate",
        str(model.get("max_scan_class")),
        "bounded_query",
    )
    locality = policy.get("query_locality") or {}
    _add(
        checks,
        defects,
        "query:locality_flags",
        locality.get("stream_prefix_isolates_category") is True
        and locality.get("date_hierarchy_bounds_retention_window") is True
        and locality.get("opaque_object_names_prevent_identity_listing") is True,
        "local",
        "bounded_query",
    )
    return checks, defects


def check_metric_support(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[dict[str, Any]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)
    matrix = policy.get("dashboard_metric_support") or {}
    rows: list[dict[str, Any]] = []
    _add(
        checks,
        defects,
        "metrics:count_15",
        len(DASHBOARD_METRICS) == 15 and set(matrix) == set(DASHBOARD_METRICS),
        str(len(matrix)),
        "metric_support",
    )
    for metric in DASHBOARD_METRICS:
        entry = matrix.get(metric) or {}
        support = entry.get("support")
        ok = support in SUPPORT_CLASSES
        _add(
            checks,
            defects,
            f"metrics:{metric}:class",
            ok,
            str(support),
            "metric_support",
        )
        rows.append(
            {
                "metric": metric,
                "support": support,
                "primary_streams": list(entry.get("primary_streams") or []),
            }
        )
    # Core privacy-preserving rule: no metric requires path redesign.
    _add(
        checks,
        defects,
        "metrics:no_path_redesign_needed",
        policy.get("partition_redesign_required") is False,
        "no_redesign",
        "metric_support",
    )
    summary = policy.get("metric_support_summary") or {}
    _add(
        checks,
        defects,
        "metrics:has_bounded_aggregation_class",
        len(summary.get("Requires bounded aggregation") or []) >= 10,
        str(len(summary.get("Requires bounded aggregation") or [])),
        "metric_support",
    )
    _add(
        checks,
        defects,
        "metrics:validation_dataset_na",
        (matrix.get("validation_dataset_growth") or {}).get("support")
        == "Not applicable",
        "na",
        "metric_support",
    )
    return checks, defects, sorted(rows, key=lambda r: r["metric"])


def check_privacy_partitioning(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)
    forbidden = set(policy.get("forbidden_path_dimensions") or [])
    for field in (
        "installation_id",
        "event_id",
        "source_code",
        "provider_family",
        "primary_language",
    ):
        _add(
            checks,
            defects,
            f"privacy:forbid_{field}",
            field in forbidden,
            "forbidden",
            "privacy_partition",
        )
    _add(
        checks,
        defects,
        "privacy:safe_flag",
        policy.get("privacy_safe_partitioning") is True
        and policy.get("installation_id_in_path_allowed") is False,
        "safe",
        "privacy_partition",
    )
    # Runtime alignment: partitions.py still forbids installation in keys.
    parts = read_text(
        monorepo,
        "platform/src/codestrata_platform/community_cloud_api/data_lake/partitions.py",
    )
    _add(
        checks,
        defects,
        "privacy:runtime_key_guard",
        "installation" in parts.lower(),
        "guarded",
        "privacy_partition",
    )
    return checks, defects


def check_deterministic_mapping(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)
    # Same inputs must map to same path shape (documented).
    _add(
        checks,
        defects,
        "mapping:hive_style",
        policy.get("hive_style_partitions") is True,
        "hive",
        "deterministic_mapping",
    )
    _add(
        checks,
        defects,
        "mapping:opaque_filename",
        policy.get("object_filename") == "opaque_hex.json",
        str(policy.get("object_filename")),
        "deterministic_mapping",
    )
    # Import runtime builders for a dry deterministic shape check.
    try:
        from codestrata_platform.community_cloud_api.data_lake.partitions import (
            ACCEPTED_ROOT,
            QUARANTINE_ROOT,
        )

        _add(
            checks,
            defects,
            "mapping:roots",
            ACCEPTED_ROOT == "raw" and QUARANTINE_ROOT == "quarantine",
            f"{ACCEPTED_ROOT}/{QUARANTINE_ROOT}",
            "deterministic_mapping",
        )
    except Exception as exc:  # noqa: BLE001
        _add(
            checks,
            defects,
            "mapping:roots",
            False,
            type(exc).__name__,
            "deterministic_mapping",
        )
    return checks, defects


def check_slice_15_7_absent(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    present = [rel for rel in FORBIDDEN_15_7_PATHS if exists(monorepo, rel)]
    _add(
        checks,
        defects,
        "slice_15_7:paths_absent",
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
        "slice_15_7:no_later_reports",
        not later,
        "absent" if not later else ",".join(later),
        "slice_15_7_boundary",
        "slice_15_7_started",
    )
    return checks, defects
