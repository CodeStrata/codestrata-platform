"""End-to-end telemetry storage projection + persistence tests (Slice 8.5).

Covers: typed request -> envelope -> projection -> store, for both the
in-memory store (Slice 8.2) and a fake-S3-backed
:class:`CommunityDataLakeS3Store` (Slice 8.2 adapter, Slice 8.4
``put_immutable_storage_object`` addition), mirroring
``test_assessment_metadata_storage_projection.py``.
"""

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
from codestrata_platform.community_cloud_api.data_lake.ports import InMemoryCommunityDataLakeStore
from codestrata_platform.community_cloud_api.data_lake.streams.telemetry_partitioning import (
    CLIENT_TYPE_METADATA_KEY,
    project_telemetry_storage_object,
    store_projected_telemetry,
)

from ._telemetry_partitioning_test_helpers import telemetry_envelope

S3_POLICY = CommunityDataLakePolicy.default()
S3_CONFIG = S3DataLakeStoreConfiguration(bucket_name="codestrata-test-telemetry-lake")


class FakeS3Client:
    """Minimal S3 fake enforcing IfNoneMatch semantics (mirrors ``test_s3_store.py``)."""

    def __init__(self) -> None:
        self.objects: dict[str, dict[str, Any]] = {}
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def put_object(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("put_object", dict(kwargs)))
        assert kwargs.get("IfNoneMatch") == "*"
        key = kwargs["Key"]
        if key in self.objects:
            raise ClientError(
                {"Error": {"Code": "PreconditionFailed", "Message": "exists"}}, "PutObject"
            )
        self.objects[key] = {
            "Body": kwargs["Body"],
            "Metadata": dict(kwargs.get("Metadata", {})),
            "ContentLength": kwargs.get("ContentLength"),
            "ContentType": kwargs.get("ContentType"),
        }
        return {"ETag": '"fake-etag"'}

    def head_object(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("head_object", dict(kwargs)))
        stored = self.objects[kwargs["Key"]]
        return {"Metadata": dict(stored["Metadata"]), "ContentLength": stored["ContentLength"]}


class _StoreWithoutStorageObjectSupport:
    """A minimal store missing ``put_immutable_storage_object`` entirely."""

    def put_immutable_event(self, envelope: object) -> object:  # pragma: no cover - unused
        raise AssertionError("should never be called by store_projected_telemetry")


# --- in-memory store integration ---


def test_in_memory_store_stores_the_projected_object() -> None:
    envelope = telemetry_envelope(event_id="evt-proj-imem-0001")
    projection = project_telemetry_storage_object(envelope)
    store = InMemoryCommunityDataLakeStore()
    result = store_projected_telemetry(store, projection)
    assert result.status is StorageWriteStatus.STORED
    assert result.object_key == projection.storage_object.object_key


def test_in_memory_store_replay_is_already_exists() -> None:
    envelope = telemetry_envelope(event_id="evt-proj-imem-0002")
    projection = project_telemetry_storage_object(envelope)
    store = InMemoryCommunityDataLakeStore()
    first = store_projected_telemetry(store, projection)
    second = store_projected_telemetry(store, projection)
    assert first.status is StorageWriteStatus.STORED
    assert second.status is StorageWriteStatus.ALREADY_EXISTS


def test_in_memory_store_conflict_never_overwrites() -> None:
    # Same event_key -> same deterministic object key; different event_id ->
    # different payload/content -> a genuine conflict, never a silent
    # overwrite of the first write's bytes.
    envelope_a = telemetry_envelope(event_key="event:conflict-key", event_id="evt-proj-imem-003a")
    envelope_b = telemetry_envelope(event_key="event:conflict-key", event_id="evt-proj-imem-003b")
    projection_a = project_telemetry_storage_object(envelope_a)
    projection_b = project_telemetry_storage_object(envelope_b)
    assert projection_a.storage_object.object_key == projection_b.storage_object.object_key

    store = InMemoryCommunityDataLakeStore()
    first = store_projected_telemetry(store, projection_a)
    second = store_projected_telemetry(store, projection_b)
    assert first.status is StorageWriteStatus.STORED
    assert second.status is StorageWriteStatus.CONFLICT
    assert (
        store.get_accepted_bytes(first.object_key)
        == projection_a.storage_object.canonical_json_bytes
    )


def test_in_memory_bytes_stored_match_the_projected_canonical_bytes() -> None:
    envelope = telemetry_envelope(event_id="evt-proj-imem-0004")
    projection = project_telemetry_storage_object(envelope)
    store = InMemoryCommunityDataLakeStore()
    result = store_projected_telemetry(store, projection)
    stored_bytes = store.get_accepted_bytes(result.object_key)
    assert stored_bytes == projection.storage_object.canonical_json_bytes


def test_store_projected_telemetry_requires_put_immutable_storage_object() -> None:
    envelope = telemetry_envelope(event_id="evt-proj-imem-0005")
    projection = project_telemetry_storage_object(envelope)
    with pytest.raises(AttributeError):
        store_projected_telemetry(_StoreWithoutStorageObjectSupport(), projection)


# --- fake-S3 store integration ---


def _s3_store(client: FakeS3Client) -> CommunityDataLakeS3Store:
    return CommunityDataLakeS3Store(config=S3_CONFIG, policy=S3_POLICY, client=client)


def test_s3_store_put_immutable_storage_object_is_stored() -> None:
    envelope = telemetry_envelope(event_id="evt-proj-s3-00001")
    projection = project_telemetry_storage_object(envelope)
    client = FakeS3Client()
    store = _s3_store(client)
    result = store_projected_telemetry(store, projection)
    assert result.status is StorageWriteStatus.STORED
    assert result.object_key == projection.storage_object.object_key


def test_s3_store_put_always_sets_if_none_match_star() -> None:
    envelope = telemetry_envelope(event_id="evt-proj-s3-00002")
    projection = project_telemetry_storage_object(envelope)
    client = FakeS3Client()
    store = _s3_store(client)
    store_projected_telemetry(store, projection)
    _, kwargs = client.calls[0]
    assert kwargs["IfNoneMatch"] == "*"


def test_s3_store_object_key_starts_with_generic_accepted_path() -> None:
    envelope = telemetry_envelope(event_id="evt-proj-s3-00003")
    projection = project_telemetry_storage_object(envelope)
    client = FakeS3Client()
    store = _s3_store(client)
    result = store_projected_telemetry(store, projection)
    assert result.object_key.startswith("raw/stream=telemetry/schema_version=1.0/")


def test_s3_store_metadata_includes_client_type() -> None:
    envelope = telemetry_envelope(event_id="evt-proj-s3-00004")
    projection = project_telemetry_storage_object(envelope)
    client = FakeS3Client()
    store = _s3_store(client)
    result = store_projected_telemetry(store, projection)
    stored_metadata = client.objects[result.object_key]["Metadata"]
    assert stored_metadata[CLIENT_TYPE_METADATA_KEY] == "codestrata_cli"


def test_s3_store_metadata_excludes_event_id_and_installation_id() -> None:
    envelope = telemetry_envelope(
        event_id="evt-proj-s3-00005", installation_id="install-abcdef12"
    )
    projection = project_telemetry_storage_object(envelope)
    client = FakeS3Client()
    store = _s3_store(client)
    result = store_projected_telemetry(store, projection)
    stored_metadata = client.objects[result.object_key]["Metadata"]
    blob = " ".join(stored_metadata.values())
    assert "evt-proj-s3-00005" not in blob
    assert "install-abcdef12" not in blob
    assert "event_id" not in stored_metadata
    assert "installation_id" not in stored_metadata


def test_s3_store_replay_resolves_to_already_exists() -> None:
    envelope = telemetry_envelope(event_id="evt-proj-s3-00006")
    projection = project_telemetry_storage_object(envelope)
    client = FakeS3Client()
    store = _s3_store(client)
    first = store_projected_telemetry(store, projection)
    second = store_projected_telemetry(store, projection)
    assert first.status is StorageWriteStatus.STORED
    assert second.status is StorageWriteStatus.ALREADY_EXISTS


def test_s3_store_put_immutable_event_alone_does_not_carry_client_type() -> None:
    """Documents the durability defect ``store_projected_telemetry`` avoids.

    Calling ``put_immutable_event`` directly rebuilds the storage object from
    the envelope alone and never sees the projector's extra metadata — this
    is exactly why ``store_projected_telemetry`` requires
    ``put_immutable_storage_object`` instead of falling back to it.
    """

    envelope = telemetry_envelope(event_id="evt-proj-s3-00007")
    client = FakeS3Client()
    store = _s3_store(client)
    result = store.put_immutable_event(envelope)
    assert result.status is StorageWriteStatus.STORED
    stored_metadata = client.objects[result.object_key]["Metadata"]
    assert CLIENT_TYPE_METADATA_KEY not in stored_metadata
