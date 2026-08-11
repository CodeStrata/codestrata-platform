"""Slice 19.1 — telemetry → Insights assessment metrics + external adapters."""

from __future__ import annotations

import json
from datetime import date

from codestrata_platform.community_cloud_api.insights.external_metrics import (
    aggregate_community_sentiment,
    aggregate_github_forks,
    aggregate_github_stars,
    aggregate_published_reports,
    count_published_from_registry,
)
from codestrata_platform.community_cloud_api.insights.models import MetricRequest
from codestrata_platform.community_cloud_api.insights.policy import DEFAULT_OVERVIEW_METRICS
from codestrata_platform.community_cloud_api.insights.service import aggregate_metric
from codestrata_platform.community_cloud_api.insights_storage.fake_s3 import FakeInsightsS3Client
from codestrata_platform.community_cloud_api.insights_storage.reader import BoundedS3Reader


def _envelope(*, stream: str, payload: dict, day: str = "2026-08-10") -> bytes:
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


def _key(stream: str, day: str, name: str) -> str:
    y, m, d = day.split("-")
    return (
        f"raw/stream={stream}/schema_version=1.0/"
        f"year={y}/month={m}/day={d}/{name}.json"
    )


def _reader_with(objects: dict[str, bytes]) -> BoundedS3Reader:
    client = FakeInsightsS3Client()
    for k, v in objects.items():
        client.put_bytes(k, v)
    return BoundedS3Reader(bucket="test-bucket", client=client)


def _telemetry_assess(
    *,
    event_id: str,
    installation_id: str | None,
    event_type: str,
    day: str = "2026-08-10",
    hour: str = "12:00:00",
) -> bytes:
    payload: dict = {
        "schema_version": "1.0",
        "event_id": event_id,
        "client": {"name": "codestrata_cli", "version": "0.2.0"},
        "event_type": event_type,
        "properties": {"feature": "assess", "operation": "run", "outcome": "succeeded"},
        "occurred_at": f"{day}T{hour}Z",
    }
    if installation_id is not None:
        payload["installation_id"] = installation_id
    if event_type == "operation_failed":
        payload["properties"]["outcome"] = "failed"
    return _envelope(stream="telemetry", payload=payload, day=day)


def test_default_overview_is_nine_v02_metrics() -> None:
    assert len(DEFAULT_OVERVIEW_METRICS) == 9
    assert DEFAULT_OVERVIEW_METRICS == (
        "github_stars",
        "github_forks",
        "community_sentiment",
        "total_assessments",
        "first_assessments",
        "repeat_assessments",
        "successful_assessments",
        "failed_assessments",
        "published_reports",
    )


def test_telemetry_assess_increments_total_and_success() -> None:
    day = "2026-08-10"
    objects = {
        _key("telemetry", day, "ok1"): _telemetry_assess(
            event_id="e1", installation_id="inst-a", event_type="feature_completed"
        ),
        _key("assessment_metadata", day, "pad"): _envelope(
            stream="assessment_metadata",
            day=day,
            payload={
                "schema_version": "1.0",
                "event_id": "pad",
                "client": {"name": "cli", "version": "0.2.0"},
                "assessment": {"assessment_status": "cancelled", "executed_heads": []},
                "repository": {"primary_language": "python"},
                "execution": {"result": "cancelled"},
                "artifacts": {},
            },
        ),
    }
    reader = _reader_with(objects)
    total = aggregate_metric(
        MetricRequest("total_assessments", date(2026, 8, 10), date(2026, 8, 10)),
        reader=reader,
    )
    ok = aggregate_metric(
        MetricRequest("successful_assessments", date(2026, 8, 10), date(2026, 8, 10)),
        reader=reader,
    )
    fail = aggregate_metric(
        MetricRequest("failed_assessments", date(2026, 8, 10), date(2026, 8, 10)),
        reader=reader,
    )
    assert total.value == 1
    assert ok.value == 1
    assert fail.value == 0
    assert (ok.value or 0) + (fail.value or 0) == total.value


def test_first_and_repeat_use_installation_identity_not_repo() -> None:
    day = "2026-08-10"
    objects = {
        _key("telemetry", day, "a1"): _telemetry_assess(
            event_id="a1",
            installation_id="inst-same",
            event_type="feature_completed",
            hour="10:00:00",
        ),
        _key("telemetry", day, "a2"): _telemetry_assess(
            event_id="a2",
            installation_id="inst-same",
            event_type="feature_completed",
            hour="11:00:00",
        ),
        _key("telemetry", day, "b1"): _telemetry_assess(
            event_id="b1",
            installation_id="inst-other",
            event_type="feature_completed",
            hour="12:00:00",
        ),
        _key("assessment_metadata", day, "pad"): _envelope(
            stream="assessment_metadata",
            day=day,
            payload={
                "schema_version": "1.0",
                "event_id": "pad",
                "client": {"name": "cli", "version": "0.2.0"},
                "assessment": {"assessment_status": "cancelled", "executed_heads": []},
                "repository": {"primary_language": "python"},
                "execution": {"result": "cancelled"},
                "artifacts": {},
            },
        ),
    }
    reader = _reader_with(objects)
    first = aggregate_metric(
        MetricRequest("first_assessments", date(2026, 8, 10), date(2026, 8, 10)),
        reader=reader,
    )
    repeat = aggregate_metric(
        MetricRequest("repeat_assessments", date(2026, 8, 10), date(2026, 8, 10)),
        reader=reader,
    )
    total = aggregate_metric(
        MetricRequest("total_assessments", date(2026, 8, 10), date(2026, 8, 10)),
        reader=reader,
    )
    assert first.value == 2  # two distinct installation ids
    assert repeat.value == 1  # second event for inst-same
    assert total.value == 3


def test_failed_telemetry_operation_counts() -> None:
    day = "2026-08-10"
    objects = {
        _key("telemetry", day, "f1"): _telemetry_assess(
            event_id="f1", installation_id="inst-a", event_type="operation_failed"
        ),
        _key("assessment_metadata", day, "pad"): _envelope(
            stream="assessment_metadata",
            day=day,
            payload={
                "schema_version": "1.0",
                "event_id": "pad",
                "client": {"name": "cli", "version": "0.2.0"},
                "assessment": {"assessment_status": "cancelled", "executed_heads": []},
                "repository": {"primary_language": "python"},
                "execution": {"result": "cancelled"},
                "artifacts": {},
            },
        ),
    }
    reader = _reader_with(objects)
    fail = aggregate_metric(
        MetricRequest("failed_assessments", date(2026, 8, 10), date(2026, 8, 10)),
        reader=reader,
    )
    total = aggregate_metric(
        MetricRequest("total_assessments", date(2026, 8, 10), date(2026, 8, 10)),
        reader=reader,
    )
    assert fail.value == 1
    assert total.value == 1


def test_community_sentiment_unavailable_not_fabricated() -> None:
    result = aggregate_community_sentiment(date(2026, 8, 1), date(2026, 8, 10))
    assert result.metric_id == "community_sentiment"
    assert result.value is None
    assert result.completeness == "unavailable"
    assert "community_sentiment_not_yet_collected" in result.limitations


def test_published_reports_port_and_registry_count() -> None:
    class Port:
        def count_published_reports(self) -> int:
            return 2

    result = aggregate_published_reports(
        date(2026, 8, 1), date(2026, 8, 10), port=Port()
    )
    assert result.value == 2
    assert result.status == "ok"

    missing = aggregate_published_reports(
        date(2026, 8, 1), date(2026, 8, 10), port=None
    )
    assert missing.value is None
    assert missing.completeness == "unavailable"

    registry = {
        "assessments": [
            {"current_status": "published", "previous_status": None},
            {"current_status": "published", "previous_status": "published"},
        ],
        "engineering_intelligence": [],
    }
    assert count_published_from_registry(registry) == 3


def test_github_metrics_fail_gracefully_without_network(monkeypatch) -> None:
    class BoomCache:
        def get(self):
            raise RuntimeError("network")

    monkeypatch.setattr(
        "codestrata_platform.community_cloud_api.community_status.github_stars.GitHubMetadataCache",
        BoomCache,
    )
    stars = aggregate_github_stars(date(2026, 8, 1), date(2026, 8, 10))
    forks = aggregate_github_forks(date(2026, 8, 1), date(2026, 8, 10))
    assert stars.value is None
    assert forks.value is None
    assert "source_unavailable" in stars.limitations
    assert "source_unavailable" in forks.limitations
