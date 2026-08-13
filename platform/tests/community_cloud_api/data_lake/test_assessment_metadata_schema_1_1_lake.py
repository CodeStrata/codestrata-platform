"""Slice 20.7 — assessment_metadata Data Lake 1.0/1.1 coexistence + canary."""

from __future__ import annotations

import json

from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.ports import InMemoryCommunityDataLakeStore
from codestrata_platform.community_cloud_api.data_lake.streams.assessment_metadata_partitioning import (
    project_assessment_metadata_storage_object,
    store_projected_assessment_metadata,
)

from ._assessment_partitioning_test_helpers import assessment_envelope

_AID = "aaaaaaaa-bbbb-cccc-dddd-111111111111"
_CANARIES = (
    "VERY_PRIVATE_REPO_123",
    "/Users/private/AcmeSecretProject/payments/",
    "AcmeInternalSettlementEngine",
    "TEST_SECRET_DO_NOT_TRANSMIT",
    "git@github.com:private/acme-secret.git",
    "acme-internal-payments-sdk",
    "https://internal.acme.example/private",
)


def test_l1_l4_l5_1_0_persistence_unchanged() -> None:
    envelope = assessment_envelope(event_id="amd-lake-10-001")
    assert envelope.source_schema_version == "1.0"
    assert envelope.acceptance.accepted_at == "2026-08-04T00:00:00Z"
    assert envelope.acceptance.partition_date == "2026-08-04"
    projection = project_assessment_metadata_storage_object(envelope)
    store = InMemoryCommunityDataLakeStore()
    result = store_projected_assessment_metadata(store, projection)
    assert result.status is StorageWriteStatus.STORED
    assert result.object_key.startswith(
        "raw/stream=assessment_metadata/schema_version=1.0/"
    )
    assert "/day=04/" in result.object_key
    raw = store.get_accepted_bytes(result.object_key)
    assert raw is not None
    body = json.loads(raw.decode("utf-8"))
    assert body["payload"]["schema_version"] == "1.0"
    assert body["payload"].get("assessment_id") in (None, "")


def test_l2_l6_l7_l8_l9_1_1_persistence_retains_fields() -> None:
    envelope = assessment_envelope(
        event_id="amd-lake-11-001",
        schema_version="1.1",
        assessment_id=_AID,
        finding_aggregates=[
            {
                "rule_id": "architecture.layer-dependency",
                "severity": "high",
                "category": "architecture",
                "count": 2,
            }
        ],
        head_confidence=[{"head": "security", "confidence_level": "high"}],
        execution={
            "duration_bucket": "10s_to_30s",
            "result": "failed",
            "ai_used": False,
            "offline_mode": True,
            "client_version": "0.2.1",
            "platform": "darwin",
            "failure_category": "timeout",
        },
    )
    assert envelope.source_schema_version == "1.1"
    projection = project_assessment_metadata_storage_object(envelope)
    store = InMemoryCommunityDataLakeStore()
    result = store_projected_assessment_metadata(store, projection)
    assert result.status is StorageWriteStatus.STORED
    assert result.object_key.startswith(
        "raw/stream=assessment_metadata/schema_version=1.1/"
    )
    assert envelope.acceptance.partition_date == "2026-08-04"
    raw = store.get_accepted_bytes(result.object_key)
    assert raw is not None
    body = json.loads(raw.decode("utf-8"))
    payload = body["payload"]
    assert payload["schema_version"] == "1.1"
    assert payload["assessment_id"] == _AID
    assert payload["finding_aggregates"][0]["rule_id"] == "architecture.layer-dependency"
    assert payload["head_confidence"][0]["confidence_level"] == "high"
    assert payload["execution"]["failure_category"] == "timeout"
    assert body["acceptance"]["accepted_at"] == "2026-08-04T00:00:00Z"
    assert "occurred_at" not in payload


def test_l3_coexistence_1_0_and_1_1_same_store() -> None:
    store = InMemoryCommunityDataLakeStore()
    e0 = assessment_envelope(event_id="amd-coexist-10", event_key="event:coexist-10")
    e1 = assessment_envelope(
        event_id="amd-coexist-11",
        event_key="event:coexist-11",
        schema_version="1.1",
        assessment_id=_AID,
    )
    p0 = project_assessment_metadata_storage_object(e0)
    p1 = project_assessment_metadata_storage_object(e1)
    r0 = store_projected_assessment_metadata(store, p0)
    r1 = store_projected_assessment_metadata(store, p1)
    assert r0.status is StorageWriteStatus.STORED
    assert r1.status is StorageWriteStatus.STORED
    assert "/schema_version=1.0/" in r0.object_key
    assert "/schema_version=1.1/" in r1.object_key
    assert r0.object_key != r1.object_key


def test_l10_forbidden_values_absent_from_persisted_1_1() -> None:
    envelope = assessment_envelope(
        event_id="amd-lake-canary-001",
        schema_version="1.1",
        assessment_id=_AID,
        finding_aggregates=[
            {
                "rule_id": "architecture.layer-dependency",
                "severity": "high",
                "category": "architecture",
                "count": 1,
            }
        ],
    )
    projection = project_assessment_metadata_storage_object(envelope)
    store = InMemoryCommunityDataLakeStore()
    result = store_projected_assessment_metadata(store, projection)
    raw = store.get_accepted_bytes(result.object_key)
    assert raw is not None
    text = raw.decode("utf-8")
    for token in _CANARIES:
        assert token not in text
        assert token not in result.object_key
