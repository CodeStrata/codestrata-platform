"""Platform unit tests for Insights aggregation (Slice 15.7)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from codestrata_platform.community_cloud_api.insights.errors import InsightsAggregationError
from codestrata_platform.community_cloud_api.insights.models import (
    MetricRequest,
    OverviewRequest,
)
from codestrata_platform.community_cloud_api.insights.service import (
    InsightsAggregationService,
    aggregate_metric,
)
from codestrata_platform.community_cloud_api.insights.suppression import suppress_groups
from codestrata_platform.community_cloud_api.insights.validation_dataset import (
    LocalValidationCatalogReader,
)
from codestrata_platform.community_cloud_api.insights_query.models import DateWindow, QueryBudgets
from codestrata_platform.community_cloud_api.insights_query.planner import plan_metric_query
from codestrata_platform.community_cloud_api.insights_storage.fake_s3 import FakeInsightsS3Client
from codestrata_platform.community_cloud_api.insights_storage.reader import (
    BoundedS3Reader,
    reject_arbitrary_prefix,
)


def _envelope(
    *,
    stream: str,
    payload: dict,
    day: str = "2026-08-01",
) -> bytes:
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


def test_reject_caller_prefix() -> None:
    with pytest.raises(Exception):
        reject_arbitrary_prefix("raw/")


def test_total_and_not_event_count() -> None:
    day = "2026-08-01"
    objects = {
        _key("cli_event", day, "a"): _envelope(
            stream="cli_event",
            day=day,
            payload={
                "schema_version": "1.0",
                "event_id": "e1",
                "installation_id": "inst-1",
                "client": {"name": "cli", "version": "0.2.0"},
                "event": {"operation": "assess"},
                "context": {},
            },
        ),
        _key("cli_event", day, "b"): _envelope(
            stream="cli_event",
            day=day,
            payload={
                "schema_version": "1.0",
                "event_id": "e2",
                "installation_id": "inst-1",
                "client": {"name": "cli", "version": "0.2.0"},
                "event": {"operation": "assess"},
                "context": {},
            },
        ),
        _key("cli_event", day, "c"): _envelope(
            stream="cli_event",
            day=day,
            payload={
                "schema_version": "1.0",
                "event_id": "e3",
                "installation_id": "inst-2",
                "client": {"name": "cli", "version": "0.2.0"},
                "event": {"operation": "assess"},
                "context": {},
            },
        ),
    }
    # total uses all streams — seed assessment too for planner multi-stream
    for stream in (
        "telemetry",
        "assessment_metadata",
        "extension_event",
        "ai_usage",
    ):
        # empty prefixes ok
        pass
    reader = _reader_with(objects)
    result = aggregate_metric(
        MetricRequest("total_anonymous_installations", date(2026, 8, 1), date(2026, 8, 1)),
        reader=reader,
    )
    assert result.value == 2
    assert result.completeness in {"complete", "partial"}
    text = json.dumps(result.to_stable_dict())
    assert "inst-1" not in text
    assert "installation_id" not in text


def test_cancelled_not_failed_and_success() -> None:
    day = "2026-08-01"
    objects = {
        _key("telemetry", day, "ok"): _envelope(
            stream="telemetry",
            day=day,
            payload={
                "schema_version": "1.0",
                "event_id": "t1",
                "installation_id": "i1",
                "client": {"name": "cli", "version": "0.2.0"},
                "event_type": "feature_completed",
                "properties": {
                    "feature": "assess",
                    "operation": "run",
                    "outcome": "succeeded",
                },
                "occurred_at": f"{day}T12:00:00Z",
            },
        ),
        _key("telemetry", day, "fail"): _envelope(
            stream="telemetry",
            day=day,
            payload={
                "schema_version": "1.0",
                "event_id": "t2",
                "installation_id": "i2",
                "client": {"name": "cli", "version": "0.2.0"},
                "event_type": "operation_failed",
                "properties": {
                    "feature": "assess",
                    "operation": "run",
                    "outcome": "failed",
                },
                "occurred_at": f"{day}T12:01:00Z",
            },
        ),
        _key("assessment_metadata", day, "ok"): _envelope(
            stream="assessment_metadata",
            day=day,
            payload={
                "schema_version": "1.0",
                "event_id": "a1",
                "installation_id": "i1",
                "client": {"name": "cli", "version": "0.2.0"},
                "assessment": {
                    "assessment_status": "completed",
                    "executed_heads": ["security", "testing"],
                },
                "repository": {"primary_language": "python", "package_ecosystem": "npm"},
                "execution": {"result": "succeeded"},
                "artifacts": {},
            },
        ),
        _key("assessment_metadata", day, "fail"): _envelope(
            stream="assessment_metadata",
            day=day,
            payload={
                "schema_version": "1.0",
                "event_id": "a2",
                "installation_id": "i2",
                "client": {"name": "cli", "version": "0.2.0"},
                "assessment": {"assessment_status": "failed", "executed_heads": []},
                "repository": {"primary_language": "java"},
                "execution": {"result": "failed"},
                "artifacts": {},
            },
        ),
        _key("assessment_metadata", day, "cancel"): _envelope(
            stream="assessment_metadata",
            day=day,
            payload={
                "schema_version": "1.0",
                "event_id": "a3",
                "installation_id": "i3",
                "client": {"name": "cli", "version": "0.2.0"},
                "assessment": {"assessment_status": "cancelled", "executed_heads": []},
                "repository": {"primary_language": "go"},
                "execution": {"result": "cancelled"},
                "artifacts": {},
            },
        ),
    }
    reader = _reader_with(objects)
    ok = aggregate_metric(
        MetricRequest("successful_assessments", date(2026, 8, 1), date(2026, 8, 1)),
        reader=reader,
    )
    fail = aggregate_metric(
        MetricRequest("failed_assessments", date(2026, 8, 1), date(2026, 8, 1)),
        reader=reader,
    )
    assert ok.value == 1
    assert fail.value == 1


def test_suppression_and_provider_excludes_unavailable() -> None:
    groups, suppressed = suppress_groups(
        {"aws_bedrock": 5, "openai": 1, "openrouter": 2}, dimension="provider_family"
    )
    assert suppressed is True
    keys = {g.key for g in groups}
    assert "openai" not in keys
    assert "other_suppressed" in keys
    assert all(g.count >= 3 or g.suppressed for g in groups)

    day = "2026-08-01"
    objects = {}
    for i, family in enumerate(["aws_bedrock"] * 3 + ["unavailable"] * 2):
        objects[_key("ai_usage", day, f"p{i}")] = _envelope(
            stream="ai_usage",
            day=day,
            payload={
                "schema_version": "1.0",
                "event_id": f"u{i}",
                "installation_id": f"i{i}",
                "client": {"name": "cli", "version": "0.2.0"},
                "usage": {
                    "provider_family": family,
                    "model_family": "gpt_family",
                },
                "context": {},
            },
        )
    reader = _reader_with(objects)
    result = aggregate_metric(
        MetricRequest("ai_provider_adoption", date(2026, 8, 1), date(2026, 8, 1)),
        reader=reader,
    )
    assert result.value == 3
    assert all(g.key != "unavailable" for g in result.groups)


def test_malformed_not_zero_and_budget() -> None:
    day = "2026-08-01"
    objects = {
        _key("cli_event", day, "bad"): b"not-json",
        _key("cli_event", day, "good"): _envelope(
            stream="cli_event",
            day=day,
            payload={
                "schema_version": "1.0",
                "event_id": "e1",
                "installation_id": "inst-1",
                "client": {"name": "cli", "version": "0.2.0"},
                "event": {"operation": "assess"},
                "context": {},
            },
        ),
    }
    reader = _reader_with(objects)
    result = aggregate_metric(
        MetricRequest("cli_version_adoption", date(2026, 8, 1), date(2026, 8, 1)),
        reader=reader,
    )
    assert result.value == 1
    assert result.completeness == "partial"
    assert "malformed_objects_omitted" in result.limitations


def test_overview_isolates_failures() -> None:
    day = "2026-08-01"
    reader = _reader_with({})
    monorepo = Path(__file__).resolve().parents[4]
    svc = InsightsAggregationService(
        reader=reader,
        validation_catalog=LocalValidationCatalogReader(monorepo),
    )
    results = svc.aggregate_dashboard_overview(
        OverviewRequest(
            date(2026, 8, 1),
            date(2026, 8, 1),
            metric_ids=(
                "successful_assessments",
                "validation_dataset_growth",
                "not_a_real_metric",
            ),
        )
    )
    assert len(results) == 3
    assert results[0].status == "ok"
    assert results[0].value == 0
    assert results[1].status == "ok"
    assert results[1].value == 22
    assert results[2].status == "error"


def test_validation_external() -> None:
    monorepo = Path(__file__).resolve().parents[4]
    result = aggregate_metric(
        MetricRequest("validation_dataset_growth", date(2026, 8, 1), date(2026, 8, 1)),
        validation_catalog=LocalValidationCatalogReader(monorepo),
    )
    assert result.value == 22
    assert "validation_growth_snapshots_unavailable" in result.limitations


def test_query_budget_objects() -> None:
    day = "2026-08-01"
    objects = {
        _key("cli_event", day, f"x{i}"): _envelope(
            stream="cli_event",
            day=day,
            payload={
                "schema_version": "1.0",
                "event_id": f"e{i}",
                "installation_id": f"i{i}",
                "client": {"name": "cli", "version": "0.2.0"},
                "event": {"operation": "assess"},
                "context": {},
            },
        )
        for i in range(5)
    }
    client = FakeInsightsS3Client()
    for k, v in objects.items():
        client.put_bytes(k, v)
    reader = BoundedS3Reader(bucket="b", client=client)
    plan = plan_metric_query(
        metric="cli_version_adoption",
        window=DateWindow(date(2026, 8, 1), date(2026, 8, 1)),
        budgets=QueryBudgets(max_objects_per_query=2),
    )
    with pytest.raises(InsightsAggregationError) as exc:
        reader.read_plan(plan)
    assert exc.value.code == "query_limit_exceeded"
