"""Privacy boundary tests for the S3 infrastructure adapter (Slice 8.2)."""

from __future__ import annotations

import json
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.errors import StorageErrorCategory
from codestrata_platform.community_cloud_api.data_lake.infrastructure.configuration import (
    S3DataLakeStoreConfiguration,
)
from codestrata_platform.community_cloud_api.data_lake.infrastructure.diagnostics import (
    safe_s3_storage_diagnostic,
)
from codestrata_platform.community_cloud_api.data_lake.infrastructure.s3_store import (
    CommunityDataLakeS3Store,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy

from community_cloud_api.data_lake.test_s3_store import FakeS3Client, _client_error

from ._envelope_test_helpers import make_envelope
from ._quarantine_test_helpers import make_quarantine_record

POLICY = CommunityDataLakePolicy.default()
BUCKET_NAME = "codestrata-super-secret-bucket-name"
CONFIG = S3DataLakeStoreConfiguration(bucket_name=BUCKET_NAME)


def _envelope(**overrides: object) -> object:
    base: dict[str, object] = dict(
        event_stream="assessment_metadata",
        schema_name="community-assessment-metadata",
        schema_version="1.0",
        policy_id="community-assessment-metadata-policy:1.0",
        safe_event_reference="evt-privacykeyaaaaa",
        event_key="event:privacy-adapter-key",
        client_type="codestrata_cli",
        payload={"assessment_status": "completed"},
    )
    base.update(overrides)
    return make_envelope(**base)  # type: ignore[arg-type]


def test_stored_receipt_public_dict_never_leaks_bucket_name() -> None:
    client = FakeS3Client()
    store = CommunityDataLakeS3Store(config=CONFIG, policy=POLICY, client=client)
    result = store.put_immutable_event(_envelope())
    assert result.receipt is not None
    blob = json.dumps(result.receipt.to_public_dict())
    assert BUCKET_NAME not in blob


def test_storage_write_result_stable_dict_never_leaks_bucket_name() -> None:
    client = FakeS3Client()
    store = CommunityDataLakeS3Store(config=CONFIG, policy=POLICY, client=client)
    result = store.put_immutable_event(_envelope())
    blob = json.dumps(result.to_stable_dict())
    assert BUCKET_NAME not in blob
    # object_key IS present at the StorageWriteResult level (internal), but
    # never inside the nested receipt dict.
    assert "object_key" not in result.to_stable_dict()["receipt"]


def test_access_denied_detail_never_contains_bucket_or_key() -> None:
    def behavior(_count: int, _kwargs: dict[str, Any]):
        return _client_error("AccessDenied")

    client = FakeS3Client(put_behavior=behavior)
    store = CommunityDataLakeS3Store(config=CONFIG, policy=POLICY, client=client)
    result = store.put_immutable_event(_envelope())
    assert BUCKET_NAME not in result.detail
    assert "raw/" not in result.detail


def test_metadata_never_contains_event_key_safe_reference_or_forbidden_tokens() -> None:
    client = FakeS3Client()
    store = CommunityDataLakeS3Store(config=CONFIG, policy=POLICY, client=client)
    envelope = _envelope()
    store.put_immutable_event(envelope)
    _, kwargs = client.calls[0]
    metadata_blob = json.dumps(kwargs["Metadata"])
    assert envelope.event_key not in metadata_blob
    assert envelope.safe_event_reference not in metadata_blob
    assert "event:" not in metadata_blob
    assert "evt-" not in metadata_blob


def test_safe_s3_storage_diagnostic_never_includes_bucket_or_key() -> None:
    diagnostic = safe_s3_storage_diagnostic(
        StorageWriteStatus.REJECTED,
        category=StorageErrorCategory.ACCESS_DENIED,
        event_stream="telemetry",
    )
    blob = json.dumps(diagnostic)
    assert BUCKET_NAME not in blob
    assert set(diagnostic) <= {"status", "category", "event_stream"}


def test_safe_s3_storage_diagnostic_omits_optional_fields_when_absent() -> None:
    diagnostic = safe_s3_storage_diagnostic(StorageWriteStatus.STORED)
    assert diagnostic == {"status": "stored"}


def test_quarantine_write_detail_is_bounded_and_omits_secrets() -> None:
    client = FakeS3Client()
    store = CommunityDataLakeS3Store(config=CONFIG, policy=POLICY, client=client)
    record = make_quarantine_record()
    result = store.quarantine_event(record)
    assert result.status is StorageWriteStatus.STORED
    public = result.quarantine_receipt.to_public_dict() if result.quarantine_receipt else {}
    blob = json.dumps(public)
    assert BUCKET_NAME not in blob
    assert "object_key" not in public
    assert result.object_key is not None
    assert result.object_key not in blob


def test_quarantine_rejection_detail_is_bounded_constant() -> None:
    from codestrata_platform.community_cloud_api.data_lake.quarantine_models import QuarantineRecord

    client = FakeS3Client()
    store = CommunityDataLakeS3Store(config=CONFIG, policy=POLICY, client=client)
    record = QuarantineRecord(
        quarantine_reason="not_a_real_reason",
        validation_stage="envelope_validation",
        quarantine_reference="qz-eeeeeeeeeeeeeeee",
        detected_at="2026-08-03T12:00:00Z",
        year="2026",
        month="08",
        day="03",
    )
    result = store.quarantine_event(record)
    assert result.status is StorageWriteStatus.REJECTED
    assert "should-never-appear" not in result.detail
    assert len(result.detail) <= 64
    assert client.calls == []


def test_object_key_never_appears_in_public_receipt_even_though_internal_dict_has_it() -> None:
    client = FakeS3Client()
    store = CommunityDataLakeS3Store(config=CONFIG, policy=POLICY, client=client)
    result = store.put_immutable_event(_envelope())
    assert result.receipt is not None
    public_blob = json.dumps(result.receipt.to_public_dict())
    assert result.object_key not in public_blob
    internal_blob = json.dumps(result.receipt.to_internal_dict())
    assert result.object_key in internal_blob
