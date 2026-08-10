"""UTC time window semantics."""

from __future__ import annotations

from pathlib import Path

from verification.community_data_lake_insights.contract import METRICS_POLICY, QUERY_POLICY
from verification.community_data_lake_insights.helpers import check, load_json
from verification.community_data_lake_insights.models import CheckResult, Defect


def check_windows(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    metrics = load_json(monorepo / METRICS_POLICY)
    query = load_json(monorepo / QUERY_POLICY)

    ts = metrics.get("time_semantics") or {}
    storage_utc = ts.get("storage_timezone") == "UTC"
    query_utc = ts.get("query_windows_timezone") == "UTC"
    display_utc = ts.get("dashboard_display_timezone_initial") == "UTC"
    no_hidden = ts.get("hidden_timezone_conversion_forbidden") is True
    policy_tz = query.get("timezone") == "UTC"

    for cid, ok, detail in (
        ("windows:storage_utc", storage_utc, "storage_timezone=UTC"),
        ("windows:query_utc", query_utc, "query_windows_timezone=UTC"),
        ("windows:display_utc", display_utc, "dashboard_display_timezone_initial=UTC"),
        ("windows:no_hidden_conversion", no_hidden, "hidden_timezone_conversion_forbidden"),
        ("windows:query_policy_utc", policy_tz, "query policy timezone=UTC"),
    ):
        checks.append(check(cid, ok, detail, "windows"))
        if not ok:
            defects.append(Defect("time_semantics", cid, "UTC", detail))

    summary = {
        "storage_timezone": ts.get("storage_timezone"),
        "query_windows_timezone": ts.get("query_windows_timezone"),
        "dashboard_display_timezone_initial": ts.get("dashboard_display_timezone_initial"),
        "hidden_timezone_conversion_forbidden": no_hidden,
        "utc_semantics": all(
            (storage_utc, query_utc, display_utc, no_hidden, policy_tz)
        ),
    }
    return checks, defects, summary
