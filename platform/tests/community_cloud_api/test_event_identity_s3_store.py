"""Unit tests for S3-backed event identity store (Slice 17.7)."""

from __future__ import annotations

from typing import Any

import pytest

try:
    from botocore.exceptions import ClientError
except ImportError:  # pragma: no cover

    class ClientError(Exception):  # type: ignore[no-redef]
        def __init__(self, error_response: dict[str, Any], operation_name: str) -> None:
            super().__init__(operation_name)
            self.response = error_response


from codestrata_platform.community_cloud_api.event_identity.models import StoredEventIdentity
from codestrata_platform.community_cloud_api.event_identity.s3_store import (
    EventIdentityStoreError,
    S3EventIdentityStore,
)


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": "synthetic"}}, "GetObject")


class FakeS3Client:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def get_object(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("get_object", dict(kwargs)))
        key = kwargs["Key"]
        if key not in self.objects:
            raise _client_error("NoSuchKey")
        return {"Body": _BytesBody(self.objects[key])}

    def put_object(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("put_object", dict(kwargs)))
        assert kwargs.get("IfNoneMatch") == "*"
        key = kwargs["Key"]
        if key in self.objects:
            raise _client_error("PreconditionFailed")
        body = kwargs["Body"]
        self.objects[key] = body if isinstance(body, bytes) else bytes(body)
        return {"ETag": '"fake"'}


class _BytesBody:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self) -> bytes:
        return self._data


def _identity(**overrides: str) -> StoredEventIdentity:
    base = {
        "event_key": "event:abcdef123456789012345678",
        "payload_fingerprint": "fp:" + ("b" * 64),
        "event_type": "application_started",
        "client_type": "codestrata_cli",
        "identity_policy_version": "1.0",
    }
    base.update(overrides)
    return StoredEventIdentity(**base)  # type: ignore[arg-type]


def test_s3_identity_get_missing_returns_none() -> None:
    client = FakeS3Client()
    store = S3EventIdentityStore(bucket_name="codestrata-test-lake", client=client)
    assert store.get("event:missingkey000000000000") is None


def test_s3_identity_record_and_get() -> None:
    client = FakeS3Client()
    store = S3EventIdentityStore(bucket_name="codestrata-test-lake", client=client)
    identity = _identity()
    store.record(identity)
    loaded = store.get(identity.event_key)
    assert loaded == identity
    assert any(key.startswith("identity/") for key in client.objects)


def test_s3_identity_conflict_on_fingerprint_mismatch() -> None:
    client = FakeS3Client()
    store = S3EventIdentityStore(bucket_name="codestrata-test-lake", client=client)
    store.record(_identity())
    with pytest.raises(EventIdentityStoreError, match="conflicting_event_identity"):
        store.record(_identity(payload_fingerprint="fp:" + ("c" * 64)))


def test_s3_identity_exact_retry_is_idempotent() -> None:
    client = FakeS3Client()
    store = S3EventIdentityStore(bucket_name="codestrata-test-lake", client=client)
    identity = _identity()
    store.record(identity)
    store.record(identity)
    put_calls = [c for c in client.calls if c[0] == "put_object"]
    assert len(put_calls) == 1
