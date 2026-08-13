"""Slice 20.7 — Insights authorities: no double-count + old-client continuity."""

from __future__ import annotations

from datetime import date

from codestrata_platform.community_cloud_api.insights.aggregators import (
    aggregate_failed,
    aggregate_first_assessments,
    aggregate_repeat_assessments,
    aggregate_successful,
    aggregate_total_assessments,
)
from codestrata_platform.community_cloud_api.insights.external_metrics import (
    aggregate_published_reports,
)
from codestrata_platform.community_cloud_api.insights.models import (
    AggregationContext,
    ReadDiagnostics,
)
from codestrata_platform.community_cloud_api.insights_query.policy import METRIC_STREAMS


def _ctx(events: list[dict]) -> AggregationContext:
    return AggregationContext(events=events, diagnostics=ReadDiagnostics())


def _tel(
    *,
    event_id: str,
    installation_id: str,
    event_type: str = "feature_completed",
    hour: str = "12:00:00",
) -> dict:
    return {
        "stream": "telemetry",
        "event_type": event_type,
        "feature": "assess",
        "outcome": "failed" if event_type == "operation_failed" else "succeeded",
        "event_id": event_id,
        "installation_id": installation_id,
        "occurred_at": f"2026-08-10T{hour}Z",
        "partition_date": "2026-08-10",
    }


def _amd(
    *,
    event_id: str,
    installation_id: str,
    assessment_id: str,
    hour: str = "12:00:01",
    status: str = "completed",
    result: str = "succeeded",
) -> dict:
    return {
        "stream": "assessment_metadata",
        "assessment_status": status,
        "execution_result": result,
        "event_id": event_id,
        "assessment_id": assessment_id,
        "installation_id": installation_id,
        "occurred_at": f"2026-08-10T{hour}Z",
        "partition_date": "2026-08-10",
    }


def test_metric_stream_authorities_are_explicit() -> None:
    assert METRIC_STREAMS["total_assessments"] == ("telemetry",)
    assert METRIC_STREAMS["successful_assessments"] == ("telemetry",)
    assert METRIC_STREAMS["failed_assessments"] == ("telemetry",)
    assert METRIC_STREAMS["first_assessments"] == ("telemetry", "assessment_metadata")
    assert METRIC_STREAMS["repeat_assessments"] == ("telemetry", "assessment_metadata")


def test_i1_old_client_lifecycle_only_first_repeat( ) -> None:
    """I1/I7/I8: backend upgrade before amd emission — telemetry-only still works."""

    events = [
        _tel(event_id="t1", installation_id="inst-a", hour="10:00:00"),
        _tel(event_id="t2", installation_id="inst-a", hour="11:00:00"),
        _tel(event_id="t3", installation_id="inst-b", hour="12:00:00"),
    ]
    ctx = _ctx(events)
    start, end = date(2026, 8, 10), date(2026, 8, 10)
    assert aggregate_total_assessments(ctx, start, end).value == 3
    assert aggregate_successful(ctx, start, end).value == 3
    assert aggregate_first_assessments(ctx, start, end).value == 2
    assert aggregate_repeat_assessments(ctx, start, end).value == 1


def test_i2_new_client_telemetry_plus_amd_no_double_count() -> None:
    """I2 / no-double-count: one assess emitting both streams counts once for totals."""

    events = [
        _tel(event_id="tel-1", installation_id="inst-a"),
        _amd(
            event_id="amd-1",
            installation_id="inst-a",
            assessment_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        ),
    ]
    ctx = _ctx(events)
    start, end = date(2026, 8, 10), date(2026, 8, 10)
    assert aggregate_total_assessments(ctx, start, end).value == 1
    assert aggregate_successful(ctx, start, end).value == 1
    assert aggregate_failed(ctx, start, end).value == 0
    assert aggregate_first_assessments(ctx, start, end).value == 1
    assert aggregate_repeat_assessments(ctx, start, end).value == 0


def test_i3_two_assessments_same_installation() -> None:
    events = [
        _tel(event_id="tel-1", installation_id="inst-a", hour="10:00:00"),
        _amd(
            event_id="amd-1",
            installation_id="inst-a",
            assessment_id="aaaaaaaa-bbbb-cccc-dddd-111111111111",
            hour="10:00:01",
        ),
        _tel(event_id="tel-2", installation_id="inst-a", hour="11:00:00"),
        _amd(
            event_id="amd-2",
            installation_id="inst-a",
            assessment_id="aaaaaaaa-bbbb-cccc-dddd-222222222222",
            hour="11:00:01",
        ),
    ]
    ctx = _ctx(events)
    start, end = date(2026, 8, 10), date(2026, 8, 10)
    assert aggregate_total_assessments(ctx, start, end).value == 2
    assert aggregate_first_assessments(ctx, start, end).value == 1
    assert aggregate_repeat_assessments(ctx, start, end).value == 1


def test_i4_two_installations() -> None:
    events = [
        _tel(event_id="tel-a", installation_id="inst-a"),
        _amd(
            event_id="amd-a",
            installation_id="inst-a",
            assessment_id="aaaaaaaa-bbbb-cccc-dddd-aaaaaaaaaaaa",
        ),
        _tel(event_id="tel-b", installation_id="inst-b"),
        _amd(
            event_id="amd-b",
            installation_id="inst-b",
            assessment_id="bbbbbbbb-bbbb-cccc-dddd-bbbbbbbbbbbb",
        ),
    ]
    ctx = _ctx(events)
    start, end = date(2026, 8, 10), date(2026, 8, 10)
    assert aggregate_first_assessments(ctx, start, end).value == 2
    assert aggregate_repeat_assessments(ctx, start, end).value == 0


def test_i5_failure_lifecycle_plus_failed_amd() -> None:
    events = [
        _tel(
            event_id="tel-f",
            installation_id="inst-a",
            event_type="operation_failed",
        ),
        _amd(
            event_id="amd-f",
            installation_id="inst-a",
            assessment_id="aaaaaaaa-bbbb-cccc-dddd-ffffffffff01",
            status="failed",
            result="failed",
        ),
    ]
    ctx = _ctx(events)
    start, end = date(2026, 8, 10), date(2026, 8, 10)
    assert aggregate_failed(ctx, start, end).value == 1
    assert aggregate_total_assessments(ctx, start, end).value == 1
    assert aggregate_successful(ctx, start, end).value == 0
    assert aggregate_first_assessments(ctx, start, end).value == 1
    assert aggregate_repeat_assessments(ctx, start, end).value == 0


def test_i6_published_reports_independent() -> None:
    class Port:
        def count_published_reports(self) -> int:
            return 7

    result = aggregate_published_reports(
        date(2026, 8, 1), date(2026, 8, 10), port=Port()
    )
    assert result.value == 7
    # Dual-stream assessment events must not affect published reports.
    events = [
        _tel(event_id="tel-1", installation_id="inst-a"),
        _amd(
            event_id="amd-1",
            installation_id="inst-a",
            assessment_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        ),
    ]
    ctx = _ctx(events)
    start, end = date(2026, 8, 10), date(2026, 8, 10)
    assert aggregate_total_assessments(ctx, start, end).value == 1
    assert result.value == 7


def test_amd_duplicate_assessment_id_does_not_inflate_repeat() -> None:
    events = [
        _tel(event_id="tel-1", installation_id="inst-a"),
        _amd(
            event_id="amd-1",
            installation_id="inst-a",
            assessment_id="aaaaaaaa-bbbb-cccc-dddd-111111111111",
            hour="12:00:01",
        ),
        _amd(
            event_id="amd-1-dup",
            installation_id="inst-a",
            assessment_id="aaaaaaaa-bbbb-cccc-dddd-111111111111",
            hour="12:00:02",
        ),
        _tel(event_id="tel-2", installation_id="inst-a", hour="13:00:00"),
        _amd(
            event_id="amd-2",
            installation_id="inst-a",
            assessment_id="aaaaaaaa-bbbb-cccc-dddd-222222222222",
            hour="13:00:01",
        ),
    ]
    ctx = _ctx(events)
    start, end = date(2026, 8, 10), date(2026, 8, 10)
    assert aggregate_first_assessments(ctx, start, end).value == 1
    assert aggregate_repeat_assessments(ctx, start, end).value == 1
