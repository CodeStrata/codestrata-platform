"""Checks for Slice 15.7 aggregation verification."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from codestrata_platform.community_cloud_api.insights.cache import cache_posture
from codestrata_platform.community_cloud_api.insights.checkpoint import checkpoint_posture
from codestrata_platform.community_cloud_api.insights.errors import InsightsAggregationError
from codestrata_platform.community_cloud_api.insights.models import MetricRequest
from codestrata_platform.community_cloud_api.insights.policy import (
    MINIMUM_GROUP_COUNT,
    SUPPORTED_METRICS,
)
from codestrata_platform.community_cloud_api.insights.registry import get_aggregator
from codestrata_platform.community_cloud_api.insights.service import aggregate_metric
from codestrata_platform.community_cloud_api.insights.suppression import suppress_groups
from codestrata_platform.community_cloud_api.insights.validation_dataset import (
    LocalValidationCatalogReader,
)
from codestrata_platform.community_cloud_api.insights_storage.fake_s3 import FakeInsightsS3Client
from codestrata_platform.community_cloud_api.insights_storage.reader import (
    BoundedS3Reader,
    reject_arbitrary_prefix,
)
from verification.community_insights_aggregation.contract import (
    CONTRACT_RELATIVE,
    DOC_RELATIVE,
    FORBIDDEN_15_8_PATHS,
    INSIGHTS_PACKAGE,
    POLICY_ID,
    POLICY_RELATIVE,
    POLICY_VERSION,
    STORAGE_PACKAGE,
)
from verification.community_insights_aggregation.inventory import exists, load_json, read_text
from verification.community_insights_aggregation.models import CheckResult, Defect


def _add(
    checks: list[CheckResult],
    defects: list[Defect],
    name: str,
    ok: bool,
    detail: str,
    category: str,
    classification: str = "aggregation_defect",
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
        exists(monorepo, DOC_RELATIVE),
        DOC_RELATIVE,
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:contract",
        load_json(monorepo, CONTRACT_RELATIVE).get("contract_id")
        == "community-insights-aggregation-contract",
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
        "policy:no_athena",
        policy.get("athena_required") is False
        and policy.get("glue_required") is False
        and policy.get("redis_required") is False
        and policy.get("rds_required") is False,
        "direct_s3",
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:ingestion_off",
        policy.get("production_ingestion_enabled") is False
        and policy.get("production_data_available") is False,
        "unwired",
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:checkpoint_retention",
        policy.get("checkpoint_mode") == "retention_only_with_limitation",
        str(policy.get("checkpoint_mode")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:cache_none",
        policy.get("cache_mode") == "none",
        str(policy.get("cache_mode")),
        "policy",
    )
    return checks, defects


def check_registry_runtime(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    _add(
        checks,
        defects,
        "packages:insights",
        exists(monorepo, INSIGHTS_PACKAGE),
        INSIGHTS_PACKAGE,
        "registry",
    )
    _add(
        checks,
        defects,
        "packages:storage",
        exists(monorepo, STORAGE_PACKAGE),
        STORAGE_PACKAGE,
        "registry",
    )
    _add(
        checks,
        defects,
        "registry:count_15",
        len(SUPPORTED_METRICS) == 15,
        str(len(SUPPORTED_METRICS)),
        "registry",
    )
    try:
        get_aggregator("not_a_metric")
        ok = False
    except InsightsAggregationError as exc:
        ok = exc.code == "invalid_metric"
    _add(checks, defects, "registry:fail_closed", ok, "invalid_metric", "registry")

    # Runtime smoke with fake S3
    client = FakeInsightsS3Client()
    reader = BoundedS3Reader(bucket="verify", client=client)
    result = aggregate_metric(
        MetricRequest(
            "successful_assessments", date(2026, 8, 1), date(2026, 8, 1)
        ),
        reader=reader,
    )
    _add(
        checks,
        defects,
        "runtime:zero_complete",
        result.value == 0 and result.completeness == "complete",
        str(result.completeness),
        "aggregation",
    )
    stable = result.to_stable_dict()
    text = str(stable)
    _add(
        checks,
        defects,
        "privacy:no_installation_id",
        "installation_id" not in text,
        "clean",
        "privacy",
    )
    _add(
        checks,
        defects,
        "privacy:no_s3_keys",
        "raw/stream=" not in text,
        "clean",
        "privacy",
    )

    groups, suppressed = suppress_groups(
        {"a": 1, "b": 5}, dimension="client_version", minimum=MINIMUM_GROUP_COUNT
    )
    _add(
        checks,
        defects,
        "suppression:min_3",
        suppressed and any(g.key == "other_suppressed" for g in groups),
        "other_suppressed",
        "aggregation",
    )
    _add(
        checks,
        defects,
        "suppression:no_leak_label",
        all(g.key != "a" for g in groups),
        "hidden",
        "privacy",
    )

    validation = aggregate_metric(
        MetricRequest(
            "validation_dataset_growth", date(2026, 8, 1), date(2026, 8, 1)
        ),
        validation_catalog=LocalValidationCatalogReader(monorepo),
    )
    _add(
        checks,
        defects,
        "external:catalog_size",
        validation.status == "ok" and validation.value == 22,
        str(validation.value),
        "aggregation",
    )

    try:
        reject_arbitrary_prefix("raw/")
        prefix_ok = False
    except Exception:
        prefix_ok = True
    _add(checks, defects, "reader:reject_prefix", prefix_ok, "rejected", "reader")

    cp = checkpoint_posture()
    _add(
        checks,
        defects,
        "checkpoint:retention_only",
        cp.get("checkpoint_enabled") is False and cp.get("derived_prefix") is None,
        "retention",
        "aggregation",
    )
    cache = cache_posture()
    _add(
        checks,
        defects,
        "cache:none",
        cache.get("mode") == "none",
        "none",
        "aggregation",
    )

    # No boto3 in insights domain
    insights_init = read_text(
        monorepo,
        "platform/src/codestrata_platform/community_cloud_api/insights/service.py",
    )
    _add(
        checks,
        defects,
        "privacy:no_boto_in_domain",
        "boto3" not in insights_init and "botocore" not in insights_init,
        "clean",
        "privacy",
    )
    return checks, defects


def check_boundaries(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    for name, needle in (
        ("infra:no_athena_module", "platform/src/codestrata_platform/community_cloud_api/insights_athena"),
        ("infra:no_redis", "platform/src/codestrata_platform/community_cloud_api/insights_redis"),
        ("infra:no_rds", "platform/src/codestrata_platform/community_cloud_api/insights_rds"),
    ):
        _add(
            checks,
            defects,
            name,
            not exists(monorepo, needle),
            "absent",
            "infrastructure_boundary",
        )
    present = [rel for rel in FORBIDDEN_15_8_PATHS if exists(monorepo, rel)]
    _add(
        checks,
        defects,
        "boundary:slice_15_8_paths",
        not present,
        "absent" if not present else ",".join(present),
        "slice_15_8_boundary",
        "slice_15_8_started",
    )
    _add(
        checks,
        defects,
        "boundary:dashboard_owned_by_15_10",
        exists(monorepo, "verification/community_insights_dashboard"),
        "present",
        "dashboard_boundary",
    )
    _add(
        checks,
        defects,
        "boundary:auth_deferred_to_15_9_package",
        exists(monorepo, "verification/community_insights_auth")
        or exists(
            monorepo,
            "platform/src/codestrata_platform/community_cloud_api/insights_auth",
        ),
        "present_in_15_9",
        "auth_boundary",
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
