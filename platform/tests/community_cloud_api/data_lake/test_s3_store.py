"""S3 adapter (Slice 8.2) behavior tests using a fake S3 client — no network, no boto3 client construction."""

from __future__ import annotations

from typing import Any

import pytest

try:
    from botocore.exceptions import ClientError

    _HAS_BOTOCORE = True
except ImportError:  # pragma: no cover - botocore is a project dependency
    _HAS_BOTOCORE = False

    class ClientError(Exception):  # type: ignore[no-redef]
        def __init__(self, error_response: dict[str, Any], operation_name: str) -> None:
            super().__init__(operation_name)
            self.response = error_response


from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.infrastructure.configuration import (
    S3DataLakeStoreConfiguration,
)
from codestrata_platform.community_cloud_api.data_lake.infrastructure.s3_store import (
    CommunityDataLakeS3Store,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy

from ._envelope_test_helpers import make_envelope
from ._quarantine_test_helpers import make_quarantine_record

POLICY = CommunityDataLakePolicy.default()
CONFIG = S3DataLakeStoreConfiguration(bucket_name="codestrata-test-lake-bucket")


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": "synthetic test error"}}, "PutObject")


class FakeS3Client:
    """Records every call and enforces IfNoneMatch semantics like real S3."""

    def __init__(self, *, put_behavior: Any = None) -> None:
        self.objects: dict[str, dict[str, Any]] = {}
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self._put_behavior = put_behavior
        self._put_call_count = 0

    def put_object(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("put_object", dict(kwargs)))
        self._put_call_count += 1
        if self._put_behavior is not None:
            outcome = self._put_behavior(self._put_call_count, kwargs)
            if outcome is not None:
                raise outcome

        assert kwargs.get("IfNoneMatch") == "*", "PutObject must always set IfNoneMatch='*'"
        key = kwargs["Key"]
        if key in self.objects:
            raise _client_error("PreconditionFailed")
        self.objects[key] = {
            "Body": kwargs["Body"],
            "Metadata": dict(kwargs.get("Metadata", {})),
            "ContentLength": kwargs.get("ContentLength"),
            "ContentType": kwargs.get("ContentType"),
        }
        return {"ETag": '"fake-etag"'}

    def head_object(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("head_object", dict(kwargs)))
        key = kwargs["Key"]
        if key not in self.objects:
            raise _client_error("404")
        stored = self.objects[key]
        return {"Metadata": dict(stored["Metadata"]), "ContentLength": stored["ContentLength"]}

    def put_object_call_count(self) -> int:
        return sum(1 for name, _ in self.calls if name == "put_object")

    def head_object_call_count(self) -> int:
        return sum(1 for name, _ in self.calls if name == "head_object")


def _envelope(**overrides: object) -> object:
    base: dict[str, object] = dict(
        safe_event_reference="evt-s3storekeyaaaa",
        event_key="event:s3-store-key",
    )
    base.update(overrides)
    return make_envelope(**base)  # type: ignore[arg-type]


def _store(client: FakeS3Client, *, config: S3DataLakeStoreConfiguration = CONFIG) -> CommunityDataLakeS3Store:
    return CommunityDataLakeS3Store(config=config, policy=POLICY, client=client)


# --- happy path ---


def test_put_immutable_event_new_key_is_stored() -> None:
    client = FakeS3Client()
    store = _store(client)
    result = store.put_immutable_event(_envelope())
    assert result.status is StorageWriteStatus.STORED
    assert result.receipt is not None
    assert client.put_object_call_count() == 1
    assert client.head_object_call_count() == 0


def test_put_object_always_sets_if_none_match_star() -> None:
    client = FakeS3Client()
    store = _store(client)
    store.put_immutable_event(_envelope())
    _, kwargs = client.calls[0]
    assert kwargs["IfNoneMatch"] == "*"


def test_put_object_sets_content_type_length_and_encryption() -> None:
    client = FakeS3Client()
    store = _store(client)
    store.put_immutable_event(_envelope())
    _, kwargs = client.calls[0]
    assert kwargs["ContentType"] == "application/json"
    assert kwargs["ContentLength"] == len(kwargs["Body"])
    assert kwargs["ServerSideEncryption"] == "AES256"


def test_put_object_includes_checksum_when_required() -> None:
    client = FakeS3Client()
    store = _store(client)
    store.put_immutable_event(_envelope())
    _, kwargs = client.calls[0]
    assert "ChecksumSHA256" in kwargs


def test_put_object_omits_checksum_when_not_required() -> None:
    client = FakeS3Client()
    config = S3DataLakeStoreConfiguration(bucket_name="codestrata-test-lake-bucket", checksum_required=False)
    store = _store(client, config=config)
    store.put_immutable_event(_envelope())
    _, kwargs = client.calls[0]
    assert "ChecksumSHA256" not in kwargs


# --- already exists / conflict via precondition ---


def test_replay_same_content_resolves_to_already_exists_via_precondition() -> None:
    client = FakeS3Client()
    store = _store(client)
    envelope = _envelope()
    first = store.put_immutable_event(envelope)
    second = store.put_immutable_event(envelope)
    assert first.status is StorageWriteStatus.STORED
    assert second.status is StorageWriteStatus.ALREADY_EXISTS
    assert second.receipt is not None
    assert client.put_object_call_count() == 2
    assert client.head_object_call_count() == 1


def test_conflicting_content_resolves_to_conflict_via_precondition() -> None:
    client = FakeS3Client()
    store = _store(client)
    first = store.put_immutable_event(_envelope(payload={"duration_bucket": "1s_to_5s"}))
    second = store.put_immutable_event(_envelope(payload={"duration_bucket": "over_10m"}))
    assert first.status is StorageWriteStatus.STORED
    assert second.status is StorageWriteStatus.CONFLICT
    assert second.receipt is None


def test_conflict_never_overwrites_original_object() -> None:
    client = FakeS3Client()
    store = _store(client)
    first = store.put_immutable_event(_envelope(payload={"duration_bucket": "1s_to_5s"}))
    original_body = client.objects[first.object_key]["Body"]
    store.put_immutable_event(_envelope(payload={"duration_bucket": "over_10m"}))
    assert client.objects[first.object_key]["Body"] == original_body
    # Never a second successful PutObject write to the same key.
    put_calls_for_key = [
        kwargs for name, kwargs in client.calls if name == "put_object" and kwargs["Key"] == first.object_key
    ]
    assert len(put_calls_for_key) == 2  # one STORED attempt + one that raised PreconditionFailed


def test_missing_digest_metadata_on_existing_object_fails_closed_to_conflict() -> None:
    client = FakeS3Client()
    store = _store(client)
    envelope = _envelope()
    first = store.put_immutable_event(envelope)
    # Simulate an existing object with no/garbled digest metadata.
    client.objects[first.object_key]["Metadata"] = {}
    second = store.put_immutable_event(envelope)
    assert second.status is StorageWriteStatus.CONFLICT


def test_head_object_called_exactly_once_on_precondition_failed() -> None:
    client = FakeS3Client()
    store = _store(client)
    envelope = _envelope()
    store.put_immutable_event(envelope)
    store.put_immutable_event(envelope)
    assert client.head_object_call_count() == 1


# --- access denied ---


def test_access_denied_is_rejected_without_retry() -> None:
    def behavior(call_count: int, _kwargs: dict[str, Any]) -> Exception | None:
        return _client_error("AccessDenied")

    client = FakeS3Client(put_behavior=behavior)
    store = _store(client)
    result = store.put_immutable_event(_envelope())
    assert result.status is StorageWriteStatus.REJECTED
    assert result.detail == "storage_access_denied"
    assert client.put_object_call_count() == 1


# --- transient / timeout retries ---


def test_transient_error_retries_then_succeeds() -> None:
    def behavior(call_count: int, _kwargs: dict[str, Any]) -> Exception | None:
        if call_count < 3:
            return _client_error("SlowDown")
        return None

    client = FakeS3Client(put_behavior=behavior)
    store = _store(client, config=S3DataLakeStoreConfiguration(bucket_name="codestrata-test-lake-bucket", max_attempts=5))
    result = store.put_immutable_event(_envelope())
    assert result.status is StorageWriteStatus.STORED
    assert client.put_object_call_count() == 3


def test_transient_error_exhausts_retries_and_returns_unavailable() -> None:
    def behavior(_call_count: int, _kwargs: dict[str, Any]) -> Exception | None:
        return _client_error("ServiceUnavailable")

    client = FakeS3Client(put_behavior=behavior)
    config = S3DataLakeStoreConfiguration(bucket_name="codestrata-test-lake-bucket", max_attempts=3)
    store = _store(client, config=config)
    result = store.put_immutable_event(_envelope())
    assert result.status is StorageWriteStatus.UNAVAILABLE
    assert client.put_object_call_count() == 3


def test_timeout_like_exception_returns_unavailable() -> None:
    class ConnectTimeoutError(Exception):
        pass

    def behavior(_call_count: int, _kwargs: dict[str, Any]) -> Exception | None:
        return ConnectTimeoutError("synthetic timeout, no bucket/key detail")

    client = FakeS3Client(put_behavior=behavior)
    config = S3DataLakeStoreConfiguration(bucket_name="codestrata-test-lake-bucket", max_attempts=2)
    store = _store(client, config=config)
    result = store.put_immutable_event(_envelope())
    assert result.status is StorageWriteStatus.UNAVAILABLE
    assert result.detail == "storage_timeout"
    assert client.put_object_call_count() == 2


# --- build failure before any S3 call ---


def test_invalid_envelope_is_rejected_before_any_s3_call() -> None:
    client = FakeS3Client()
    store = _store(client)
    bad_envelope = make_envelope(
        safe_event_reference="evt-badenvelopeaaaa",
        event_key="event:bad-envelope",
    )
    object.__setattr__(bad_envelope, "envelope_schema_version", "9.9")
    result = store.put_immutable_event(bad_envelope)
    assert result.status is StorageWriteStatus.REJECTED
    assert client.calls == []


# --- quarantine ---


def test_quarantine_event_stores_object_with_if_none_match() -> None:
    client = FakeS3Client()
    store = _store(client)
    record = make_quarantine_record()
    result = store.quarantine_event(record)
    assert result.status is StorageWriteStatus.STORED
    assert result.object_key is not None
    assert result.object_key.startswith("quarantine/reason=unsafe_payload/")
    assert client.put_object_call_count() == 1
    put_kwargs = client.calls[0][1]
    assert put_kwargs["IfNoneMatch"] == "*"
    assert put_kwargs["Key"] == result.object_key
    metadata = put_kwargs["Metadata"]
    assert set(metadata) == {
        "codestrata-content-sha256",
        "codestrata-object-id",
        "codestrata-quarantine-reason",
        "codestrata-quarantine-schema",
    }
    assert "codestrata-stream" not in metadata
    assert result.quarantine_receipt is not None


def test_quarantine_event_identical_replay_is_already_exists() -> None:
    client = FakeS3Client()
    store = _store(client)
    record = make_quarantine_record()
    first = store.quarantine_event(record)
    second = store.quarantine_event(record)
    assert first.status is StorageWriteStatus.STORED
    assert second.status is StorageWriteStatus.ALREADY_EXISTS
    assert first.object_key == second.object_key
    assert client.put_object_call_count() == 2
    assert client.head_object_call_count() == 1


def test_quarantine_event_rejects_invalid_record_with_no_s3_calls() -> None:
    from codestrata_platform.community_cloud_api.data_lake.quarantine_models import QuarantineRecord

    client = FakeS3Client()
    store = _store(client)
    record = QuarantineRecord(
        quarantine_reason="not_a_real_reason",
        validation_stage="envelope_validation",
        quarantine_reference="qz-dddddddddddddddd",
        detected_at="2026-08-03T12:00:00Z",
        year="2026",
        month="08",
        day="03",
    )
    result = store.quarantine_event(record)
    assert result.status is StorageWriteStatus.REJECTED
    assert client.calls == []


# --- no forbidden methods ---


def test_s3_store_has_no_delete_update_or_list_methods() -> None:
    for forbidden in ("delete_object", "delete", "update", "list_objects", "list"):
        assert not hasattr(CommunityDataLakeS3Store, forbidden)
