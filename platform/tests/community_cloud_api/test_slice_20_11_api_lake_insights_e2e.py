"""Slice 20.11 — API → Lake → Insights chain E2E + privacy canaries."""

from __future__ import annotations

import json
from datetime import date
from typing import Any, Mapping

from codestrata_platform.community_cloud_api.assessment_metadata.models import (
    AssessmentMetadataRequest,
)
from codestrata_platform.community_cloud_api.assessment_metadata.validation import (
    validate_assessment_metadata_semantics,
)
from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.ports import InMemoryCommunityDataLakeStore
from codestrata_platform.community_cloud_api.data_lake.streams.assessment_metadata_partitioning import (
    project_assessment_metadata_storage_object,
    store_projected_assessment_metadata,
)
from codestrata_platform.community_cloud_api.insights.aggregators import (
    aggregate_failed,
    aggregate_first_assessments,
    aggregate_repeat_assessments,
    aggregate_successful,
    aggregate_total_assessments,
)
from codestrata_platform.community_cloud_api.insights.decoding import (
    decode_object_bytes,
    normalize_event,
)
from codestrata_platform.community_cloud_api.insights.external_metrics import (
    aggregate_published_reports,
)
from codestrata_platform.community_cloud_api.insights.models import (
    AggregationContext,
    ReadDiagnostics,
)

from .assessment_metadata_helpers import (
    configured_metadata_client,
    valid_assessment_metadata_body,
)
from .data_lake._assessment_partitioning_test_helpers import assessment_envelope

_AID = "aaaaaaaa-bbbb-cccc-dddd-111111111111"
_INSTALL = "11111111-1111-4111-8111-111111111111"

_CANARIES = (
    "VERY_PRIVATE_REPO_123",
    "/Users/private/AcmeSecretProject/payments/",
    "AcmeInternalSettlementEngine",
    "TEST_SECRET_DO_NOT_TRANSMIT",
    "git@github.com:private/acme-secret.git",
    "acme-internal-payments-sdk",
    "https://internal.acme.example/private",
)

_FORBIDDEN = frozenset(
    {
        "repository_name",
        "repository_url",
        "git_remote",
        "path",
        "file_path",
        "source",
        "source_code",
        "snippet",
        "evidence",
        "finding_id",
        "title",
        "description",
        "recommendation_text",
        "report_id",
        "report_url",
        "graph",
        "nodes",
        "edges",
        "dependencies",
        "packages",
        "stack_trace",
        "exception_message",
        "prompt",
        "response",
    }
)

_APPROVED_TOP = frozenset(
    {
        "schema_version",
        "event_id",
        "assessment_id",
        "installation_id",
        "client",
        "assessment",
        "repository",
        "execution",
        "artifacts",
        "finding_aggregates",
        "head_confidence",
    }
)


def _canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _all_keys(obj: object) -> list[str]:
    keys: list[str] = []
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            keys.append(str(key))
            keys.extend(_all_keys(value))
    elif isinstance(obj, list):
        for item in obj:
            keys.extend(_all_keys(item))
    return keys


def _assert_clean(obj: object) -> None:
    blob = _canonical(obj)
    for canary in _CANARIES:
        assert canary not in blob
    for key in _all_keys(obj):
        assert key not in _FORBIDDEN
        for canary in _CANARIES:
            assert canary not in key


def _valid_1_1(**overrides: object) -> dict[str, object]:
    body = valid_assessment_metadata_body(
        schema_version="1.1",
        assessment_id=_AID,
        installation_id=_INSTALL,
        finding_aggregates=[
            {
                "rule_id": "architecture.layer-dependency",
                "severity": "high",
                "category": "architecture",
                "count": 2,
            },
            {
                "rule_id": "security.debug-enabled",
                "severity": "medium",
                "category": "security",
                "count": 1,
            },
        ],
        head_confidence=[
            {"head": "security", "confidence_level": "high"},
            {"head": "architecture", "confidence_level": "moderate"},
            {"head": "dependency", "confidence_level": "limited"},
            {"head": "testing", "confidence_level": "unavailable"},
        ],
    )
    body.update(overrides)
    return body


def test_e2e_api_accepts_1_1_and_persists_to_lake() -> None:
    client, sink, _store, log_sink, _tel = configured_metadata_client()
    body = _valid_1_1(event_id="amd-e2e-20-11-api-001")
    response = client.post("/api/v1/assessment-metadata", json=body)
    assert response.status_code in {200, 202}
    assert len(sink.events) == 1
    event = sink.events[0]
    assert event.schema_version == "1.1"
    assert event.assessment_id == _AID
    # Sink event deliberately omits installation_id; lake payload retains it.

    envelope = assessment_envelope(
        event_id="amd-e2e-20-11-lake-001",
        event_key="event:e2e-20-11-001",
        schema_version="1.1",
        assessment_id=_AID,
        installation_id=_INSTALL,
        finding_aggregates=body["finding_aggregates"],
        head_confidence=body["head_confidence"],
    )
    projection = project_assessment_metadata_storage_object(envelope)
    store = InMemoryCommunityDataLakeStore()
    result = store_projected_assessment_metadata(store, projection)
    assert result.status is StorageWriteStatus.STORED
    assert "/schema_version=1.1/" in result.object_key
    raw = store.get_accepted_bytes(result.object_key)
    assert raw is not None
    lake = json.loads(raw.decode("utf-8"))
    payload = lake["payload"]
    assert set(payload.keys()) <= _APPROVED_TOP | {"schema_version"}
    _assert_clean(payload)
    assert payload["assessment_id"] == _AID
    assert payload.get("installation_id") == _INSTALL
    assert payload["finding_aggregates"][0]["count"] == 2
    assert lake["acceptance"]["accepted_at"] == "2026-08-04T00:00:00Z"
    assert "occurred_at" not in payload

    log_blob = "".join(log_sink.lines)
    for canary in _CANARIES:
        assert canary not in log_blob


def test_e2e_backend_rejects_unsafe_rule_ids_even_if_client_bypassed() -> None:
    from pydantic import ValidationError

    for bad_rule in (
        "PMD.JAVA.VeryPrivate",
        "provider:openai",
        "https://internal.acme.example/private",
        "/Users/private/AcmeSecretProject/payments/ledger.py",
        "not a valid rule",
    ):
        body = _valid_1_1(
            event_id="amd-bad-rule-001",
            finding_aggregates=[
                {
                    "rule_id": bad_rule,
                    "severity": "high",
                    "category": "security",
                    "count": 1,
                }
            ],
        )
        rejected = False
        try:
            request = AssessmentMetadataRequest.model_validate(body)
            errors = validate_assessment_metadata_semantics(request)
            rejected = bool(errors)
        except ValidationError:
            rejected = True
        assert rejected, f"expected rejection for rule_id={bad_rule!r}"


def test_e2e_1_0_compatibility_unchanged_after_1_1() -> None:
    client, sink, *_ = configured_metadata_client()
    body = valid_assessment_metadata_body(event_id="amd-e2e-10-compat-001")
    response = client.post("/api/v1/assessment-metadata", json=body)
    assert response.status_code in {200, 202}
    assert sink.events[0].schema_version == "1.0"
    assert sink.events[0].assessment_id is None

    envelope = assessment_envelope(event_id="amd-e2e-10-lake-001")
    store = InMemoryCommunityDataLakeStore()
    result = store_projected_assessment_metadata(
        store, project_assessment_metadata_storage_object(envelope)
    )
    assert result.status is StorageWriteStatus.STORED
    assert "/schema_version=1.0/" in result.object_key
    raw = store.get_accepted_bytes(result.object_key)
    assert raw is not None
    body_lake = json.loads(raw.decode("utf-8"))
    assert body_lake["payload"]["schema_version"] == "1.0"


def test_e2e_lake_roundtrip_then_insights_decode_no_raw_leak() -> None:
    envelope = assessment_envelope(
        event_id="amd-e2e-decode-001",
        event_key="event:e2e-decode-001",
        schema_version="1.1",
        assessment_id=_AID,
        installation_id=_INSTALL,
        finding_aggregates=[
            {
                "rule_id": "architecture.layer-dependency",
                "severity": "high",
                "category": "architecture",
                "count": 2,
            }
        ],
        head_confidence=[{"head": "security", "confidence_level": "high"}],
    )
    store = InMemoryCommunityDataLakeStore()
    result = store_projected_assessment_metadata(
        store, project_assessment_metadata_storage_object(envelope)
    )
    raw = store.get_accepted_bytes(result.object_key)
    assert raw is not None
    decoded = decode_object_bytes(raw)
    assert decoded is not None
    event = normalize_event(decoded)
    assert event is not None
    assert event["stream"] == "assessment_metadata"
    assert event["installation_id"] == _INSTALL  # internal calc only
    assert event["assessment_id"] == _AID
    # Insights decoder must not re-expose finding titles / graph / canaries.
    _assert_clean(event)
    assert "finding_aggregates" not in event
    assert "head_confidence" not in event
    assert "report_id" not in event


def test_e2e_insights_no_double_count_from_dual_stream() -> None:
    events = [
        {
            "stream": "telemetry",
            "event_type": "feature_completed",
            "feature": "assess",
            "outcome": "succeeded",
            "event_id": "tel-1",
            "installation_id": _INSTALL,
            "occurred_at": "2026-08-10T12:00:00Z",
            "partition_date": "2026-08-10",
        },
        {
            "stream": "assessment_metadata",
            "assessment_status": "completed",
            "execution_result": "succeeded",
            "event_id": "amd-1",
            "assessment_id": _AID,
            "installation_id": _INSTALL,
            "occurred_at": "2026-08-10T12:00:01Z",
            "partition_date": "2026-08-10",
        },
    ]
    ctx = AggregationContext(events=events, diagnostics=ReadDiagnostics())
    start, end = date(2026, 8, 10), date(2026, 8, 10)
    assert aggregate_total_assessments(ctx, start, end).value == 1
    assert aggregate_successful(ctx, start, end).value == 1
    assert aggregate_failed(ctx, start, end).value == 0
    assert aggregate_first_assessments(ctx, start, end).value == 1
    assert aggregate_repeat_assessments(ctx, start, end).value == 0

    # Second assessment same installation → first/repeat.
    events2 = events + [
        {
            "stream": "telemetry",
            "event_type": "feature_completed",
            "feature": "assess",
            "outcome": "succeeded",
            "event_id": "tel-2",
            "installation_id": _INSTALL,
            "occurred_at": "2026-08-10T13:00:00Z",
            "partition_date": "2026-08-10",
        },
        {
            "stream": "assessment_metadata",
            "assessment_status": "completed",
            "execution_result": "succeeded",
            "event_id": "amd-2",
            "assessment_id": "aaaaaaaa-bbbb-cccc-dddd-222222222222",
            "installation_id": _INSTALL,
            "occurred_at": "2026-08-10T13:00:01Z",
            "partition_date": "2026-08-10",
        },
    ]
    ctx2 = AggregationContext(events=events2, diagnostics=ReadDiagnostics())
    assert aggregate_total_assessments(ctx2, start, end).value == 2
    assert aggregate_first_assessments(ctx2, start, end).value == 1
    assert aggregate_repeat_assessments(ctx2, start, end).value == 1

    # Different installation → first semantics.
    events3 = events + [
        {
            "stream": "telemetry",
            "event_type": "feature_completed",
            "feature": "assess",
            "outcome": "succeeded",
            "event_id": "tel-b",
            "installation_id": "22222222-2222-4222-8222-222222222222",
            "occurred_at": "2026-08-10T14:00:00Z",
            "partition_date": "2026-08-10",
        },
        {
            "stream": "assessment_metadata",
            "assessment_status": "completed",
            "execution_result": "succeeded",
            "event_id": "amd-b",
            "assessment_id": "bbbbbbbb-bbbb-cccc-dddd-bbbbbbbbbbbb",
            "installation_id": "22222222-2222-4222-8222-222222222222",
            "occurred_at": "2026-08-10T14:00:01Z",
            "partition_date": "2026-08-10",
        },
    ]
    ctx3 = AggregationContext(events=events3, diagnostics=ReadDiagnostics())
    assert aggregate_first_assessments(ctx3, start, end).value == 2
    assert aggregate_repeat_assessments(ctx3, start, end).value == 0

    # Failure path: operation_failed + failed amd → Failed +1 only.
    fail_events = [
        {
            "stream": "telemetry",
            "event_type": "operation_failed",
            "feature": "assess",
            "outcome": "failed",
            "event_id": "tel-f",
            "installation_id": _INSTALL,
            "occurred_at": "2026-08-10T15:00:00Z",
            "partition_date": "2026-08-10",
        },
        {
            "stream": "assessment_metadata",
            "assessment_status": "failed",
            "execution_result": "failed",
            "event_id": "amd-f",
            "assessment_id": "aaaaaaaa-bbbb-cccc-dddd-ffffffffff01",
            "installation_id": _INSTALL,
            "occurred_at": "2026-08-10T15:00:01Z",
            "partition_date": "2026-08-10",
        },
    ]
    ctx_f = AggregationContext(events=fail_events, diagnostics=ReadDiagnostics())
    assert aggregate_failed(ctx_f, start, end).value == 1
    assert aggregate_total_assessments(ctx_f, start, end).value == 1
    assert aggregate_successful(ctx_f, start, end).value == 0

    class Port:
        def count_published_reports(self) -> int:
            return 3

    published = aggregate_published_reports(
        date(2026, 8, 1), date(2026, 8, 10), port=Port()
    )
    assert published.value == 3


def test_e2e_privacy_canary_api_reject_does_not_persist() -> None:
    client, sink, *_ = configured_metadata_client()
    body = _valid_1_1(event_id="amd-canary-reject")
    body["repository_name"] = "VERY_PRIVATE_REPO_123"
    response = client.post("/api/v1/assessment-metadata", json=body)
    assert response.status_code in {400, 422}
    assert sink.events == []
    assert "VERY_PRIVATE_REPO_123" not in response.text


def test_e2e_credential_canary_absent_from_validation_errors() -> None:
    client, sink, _store, log_sink, _tel = configured_metadata_client()
    body = _valid_1_1(event_id="amd-cred-canary")
    execution = dict(body["execution"])  # type: ignore[arg-type]
    execution["failure_category"] = "not-a-real-category"
    body["execution"] = execution
    response = client.post(
        "/api/v1/assessment-metadata",
        json=body,
        headers={
            "Authorization": "Bearer cscc_v1_SYNTHETIC_CREDENTIAL_CANARY_DO_NOT_TRANSMIT"
        },
    )
    blob = response.text + "".join(log_sink.lines)
    assert "cscc_v1_SYNTHETIC_CREDENTIAL_CANARY_DO_NOT_TRANSMIT" not in blob
    assert "AKIA_CANARY" not in blob
    _ = sink
