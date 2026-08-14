"""Slice 20.15A — overview scan reuse / bounded S3 call counts."""

from __future__ import annotations

import json
from datetime import date, timedelta

from codestrata_platform.community_cloud_api.insights.external_metrics import (
    aggregate_github_forks,
    aggregate_github_stars,
    reset_shared_github_cache_for_tests,
)
from codestrata_platform.community_cloud_api.insights.models import OverviewRequest
from codestrata_platform.community_cloud_api.insights.policy import DEFAULT_OVERVIEW_METRICS
from codestrata_platform.community_cloud_api.insights.service import (
    InsightsAggregationService,
    aggregate_dashboard_overview,
)
from codestrata_platform.community_cloud_api.insights_query.models import DateWindow
from codestrata_platform.community_cloud_api.insights_query.planner import (
    plan_metric_query,
    plan_overview_lake_query,
)
from codestrata_platform.community_cloud_api.insights_storage.fake_s3 import FakeInsightsS3Client
from codestrata_platform.community_cloud_api.insights_storage.reader import BoundedS3Reader


def _envelope(*, stream: str, payload: dict, day: str) -> bytes:
    body = {
        "acceptance": {"accepted_at": f"{day}T12:00:00Z", "partition_date": day},
        "client": {"client_type": "cli"},
        "envelope_schema_version": "1.0",
        "event_stream": stream,
        "identity": {"event_key": "event:x", "safe_event_reference": "evt-x"},
        "payload": payload,
        "source_contract": {
            "policy_id": "p",
            "schema_name": "s",
            "schema_version": "1.0",
        },
    }
    return json.dumps(body, sort_keys=True).encode("utf-8")


def _key(stream: str, schema: str, day: str, name: str) -> str:
    y, m, d = day.split("-")
    return (
        f"raw/stream={stream}/schema_version={schema}/"
        f"year={y}/month={m}/day={d}/{name}.json"
    )


def _tel(day: str, event_id: str, installation_id: str) -> bytes:
    return _envelope(
        stream="telemetry",
        day=day,
        payload={
            "schema_version": "1.0",
            "event_id": event_id,
            "installation_id": installation_id,
            "client": {"name": "codestrata_cli", "version": "0.2.0"},
            "event_type": "feature_completed",
            "properties": {
                "feature": "assess",
                "operation": "run",
                "outcome": "succeeded",
            },
            "occurred_at": f"{day}T12:00:00Z",
        },
    )


def _amd(day: str, event_id: str, installation_id: str, assessment_id: str) -> bytes:
    return _envelope(
        stream="assessment_metadata",
        day=day,
        payload={
            "schema_version": "1.1",
            "event_id": event_id,
            "installation_id": installation_id,
            "client": {"name": "cli", "version": "0.2.1"},
            "assessment": {
                "assessment_id": assessment_id,
                "assessment_status": "completed",
                "executed_heads": ["architecture"],
            },
            "repository": {"primary_language": "python"},
            "execution": {"result": "succeeded"},
            "artifacts": {},
            "finding_aggregates": [],
            "head_confidence": {},
        },
    )


def test_overview_lake_plan_is_union_not_sum_of_metric_plans() -> None:
    start = date(2026, 8, 1)
    end = date(2026, 8, 30)
    window = DateWindow(start_date=start, end_date=end)
    lake = (
        "total_assessments",
        "first_assessments",
        "repeat_assessments",
        "successful_assessments",
        "failed_assessments",
    )
    overview = plan_overview_lake_query(window=window, lake_metrics=lake)
    first = plan_metric_query(metric="first_assessments", window=window)
    total = plan_metric_query(metric="total_assessments", window=window)
    # Union equals first/repeat authority (telemetry + amd 1.0/1.1), not sum.
    assert overview.prefixes == first.prefixes
    assert set(total.prefixes).issubset(set(overview.prefixes))
    # Naive serial overview would list total prefixes then first prefixes again.
    naive = len(total.prefixes) + len(first.prefixes)
    assert len(overview.prefixes) < naive
    assert len(overview.prefixes) == 90  # 30 days × (tel + amd1.0 + amd1.1)


def test_overview_issues_one_get_per_object_not_n_scans() -> None:
    """Structural perf: overview must not re-GET the same lake object per metric."""

    day = "2026-08-10"
    client = FakeInsightsS3Client()
    # Seed enough objects across streams to exercise dual-stream path.
    for i in range(40):
        client.put_bytes(
            _key("telemetry", "1.0", day, f"t{i}"),
            _tel(day, f"t{i}", f"inst-{i % 7}"),
        )
    for i in range(25):
        client.put_bytes(
            _key("assessment_metadata", "1.1", day, f"a{i}"),
            _amd(day, f"a{i}", f"inst-{i % 7}", f"assess-{i}"),
        )
    reader = BoundedS3Reader(bucket="test-bucket", client=client)
    start = date(2026, 8, 1)
    end = date(2026, 8, 30)

    class _Port:
        def count_published_reports(self) -> int:
            return 0

        def community_sentiment_summary(self) -> dict:
            return {
                "positive_responses": 0,
                "negative_responses": 0,
                "total_responses": 0,
            }

    reset_shared_github_cache_for_tests()

    class _Meta:
        stars = 1
        forks = 2

    class _Cache:
        def get(self):
            return _Meta()

    # Inject shared cache without network.
    import codestrata_platform.community_cloud_api.insights.external_metrics as ext

    ext._SHARED_GITHUB_CACHE = _Cache()

    before_lists = sum(1 for op, _ in client.calls if op == "list_objects_v2")
    before_gets = sum(1 for op, _ in client.calls if op == "get_object")
    results = InsightsAggregationService(
        reader=reader,
        published_reports_port=_Port(),
        community_sentiment_port=_Port(),
    ).aggregate_dashboard_overview(OverviewRequest(start, end))
    lists = sum(1 for op, _ in client.calls if op == "list_objects_v2") - before_lists
    gets = sum(1 for op, _ in client.calls if op == "get_object") - before_gets

    by_id = {r.metric_id: r for r in results}
    assert set(by_id) == set(DEFAULT_OVERVIEW_METRICS)
    # 65 unique objects → exactly 65 gets (no duplicate telemetry scan).
    assert gets == 65
    # One list page per day-prefix in the unified plan (90), not 120.
    assert lists == 90
    assert by_id["total_assessments"].value == 40
    assert by_id["successful_assessments"].value == 40
    # Dual-stream first/repeat: 25 amd units + telemetry excess paired — not doubled.
    assert by_id["first_assessments"].status == "ok"
    assert by_id["repeat_assessments"].status == "ok"
    assert by_id["total_assessments"].value == by_id["successful_assessments"].value


def test_overview_semantic_equivalence_vs_per_metric_reads() -> None:
    """Same fixtures → overview batch equals independent aggregate_metric values."""

    from codestrata_platform.community_cloud_api.insights.models import MetricRequest
    from codestrata_platform.community_cloud_api.insights.service import aggregate_metric

    day = "2026-08-10"
    client = FakeInsightsS3Client()
    for i in range(12):
        client.put_bytes(
            _key("telemetry", "1.0", day, f"t{i}"),
            _tel(day, f"t{i}", f"inst-{i % 4}"),
        )
    for i in range(8):
        client.put_bytes(
            _key("assessment_metadata", "1.1", day, f"a{i}"),
            _amd(day, f"a{i}", f"inst-{i % 4}", f"assess-{i}"),
        )
    reader = BoundedS3Reader(bucket="b", client=client)
    start = end = date(2026, 8, 10)
    lake = (
        "total_assessments",
        "first_assessments",
        "repeat_assessments",
        "successful_assessments",
        "failed_assessments",
    )
    overview = {
        r.metric_id: r.value
        for r in aggregate_dashboard_overview(
            OverviewRequest(start, end, metric_ids=lake), reader=reader
        )
    }
    independent = {
        mid: aggregate_metric(MetricRequest(mid, start, end), reader=reader).value
        for mid in lake
    }
    assert overview == independent


def test_github_shared_cache_constructs_once(monkeypatch) -> None:
    reset_shared_github_cache_for_tests()
    constructs = {"n": 0}

    class CountingCache:
        def __init__(self, *args, **kwargs):
            constructs["n"] += 1
            self._meta = type("M", (), {"stars": 9, "forks": 3})()

        def get(self):
            return self._meta

    monkeypatch.setattr(
        "codestrata_platform.community_cloud_api.community_status.github_stars.GitHubMetadataCache",
        CountingCache,
    )
    assert aggregate_github_stars(date(2026, 8, 1), date(2026, 8, 10)).value == 9
    assert aggregate_github_forks(date(2026, 8, 1), date(2026, 8, 10)).value == 3
    assert constructs["n"] == 1


def test_large_window_prefix_count_stays_linear() -> None:
    """30-day overview lake plan stays O(days × streams), not O(metrics × days)."""

    start = date(2026, 1, 1)
    end = start + timedelta(days=29)
    plan = plan_overview_lake_query(
        window=DateWindow(start_date=start, end_date=end),
        lake_metrics=tuple(DEFAULT_OVERVIEW_METRICS),
    )
    assert len(plan.prefixes) == 90
