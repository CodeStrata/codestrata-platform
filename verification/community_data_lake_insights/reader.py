"""Insights BoundedS3Reader / production data lake wiring."""

from __future__ import annotations

from pathlib import Path

from verification.community_data_lake_insights.contract import (
    AGG_REGISTER,
    DATA_LAKE_BUCKET,
    DEPLOYMENT_WIRING_PY,
    INSIGHTS_MODELS_PY,
    QUERY_POLICY,
    READER_PY,
    REPORT_BUCKET,
)
from verification.community_data_lake_insights.helpers import check, contains, load_json, read_text
from verification.community_data_lake_insights.models import CheckResult, Defect


def check_reader(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    reader_present = (monorepo / READER_PY).is_file() and contains(
        monorepo / READER_PY, "class BoundedS3Reader"
    )
    checks.append(
        check("reader:bounded_s3_reader_present", reader_present, READER_PY, "reader")
    )
    if not reader_present:
        defects.append(
            Defect(
                "missing_reader",
                "reader:bounded_s3_reader_present",
                "BoundedS3Reader",
                "absent",
            )
        )

    models_text = read_text(monorepo / INSIGHTS_MODELS_PY)
    models_budget = "max_list_requests_per_query: int = 2000" in models_text or (
        "max_list_requests_per_query" in models_text and "2000" in models_text
    )
    checks.append(
        check(
            "reader:models_max_list_2000",
            models_budget,
            "max_list_requests_per_query=2000",
            "reader",
        )
    )
    if not models_budget:
        defects.append(
            Defect(
                "list_budget_models",
                "reader:models_max_list_2000",
                "2000",
                "mismatch",
            )
        )

    policy = load_json(monorepo / QUERY_POLICY)
    budgets = policy.get("budgets") or {}
    policy_budget = budgets.get("max_list_requests_per_query") == 2000
    checks.append(
        check(
            "reader:policy_max_list_2000",
            policy_budget,
            str(budgets.get("max_list_requests_per_query")),
            "reader",
        )
    )

    agg = load_json(monorepo / AGG_REGISTER)
    agg_reader = agg.get("reader") == "BoundedS3Reader"
    agg_budget = agg.get("max_list_requests_per_query") == 2000
    checks.append(
        check("reader:agg_register_bounded", agg_reader, str(agg.get("reader")), "reader")
    )
    checks.append(
        check(
            "reader:agg_register_budget_2000",
            agg_budget,
            str(agg.get("max_list_requests_per_query")),
            "reader",
        )
    )

    wiring = read_text(monorepo / DEPLOYMENT_WIRING_PY)
    uses_bounded = "BoundedS3Reader" in wiring
    # Must wire Insights to data lake bucket variable, not report artifacts bucket
    uses_data_lake = "BoundedS3Reader(bucket=bucket_name" in wiring or (
        "BoundedS3Reader" in wiring and "bucket_name" in wiring
    )
    confuses_report = (
        "BoundedS3Reader" in wiring
        and "report_artifacts_bucket" in wiring
        and wiring.find("BoundedS3Reader")
        < wiring.find("report_artifacts_bucket") + 200
        and "report_artifacts_bucket" in wiring[
            max(0, wiring.find("BoundedS3Reader") - 50) : wiring.find("BoundedS3Reader")
            + 400
        ]
    )
    # Safer: Insights builder must not pass report_artifacts_bucket to BoundedS3Reader
    insights_block = ""
    if "_build_insights_aggregation_service" in wiring:
        start = wiring.find("def _build_insights_aggregation_service")
        end = wiring.find("\ndef _build_", start + 1)
        insights_block = wiring[start : end if end != -1 else start + 800]
    insights_uses_report = "report_artifacts" in insights_block
    lake_not_report = uses_bounded and uses_data_lake and not insights_uses_report
    checks.append(
        check(
            "reader:insights_uses_data_lake_not_report",
            lake_not_report,
            f"data_lake={DATA_LAKE_BUCKET} report={REPORT_BUCKET}",
            "reader",
        )
    )
    if not lake_not_report:
        defects.append(
            Defect(
                "insights_wrong_bucket",
                "reader:insights_uses_data_lake_not_report",
                "data lake bucket",
                "report bucket or unwired",
            )
        )

    summary = {
        "bounded_s3_reader": reader_present,
        "max_list_requests_per_query": 2000 if models_budget and policy_budget else None,
        "insights_reads_production_data_lake": lake_not_report,
        "uses_test_only_reader_in_prod_wiring": False,
        "_confuses_report_noise": confuses_report,
    }
    return checks, defects, summary
