"""Quarantine serialization tests (Slice 8.9)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.canonical_json import CONTENT_DIGEST_PREFIX
from codestrata_platform.community_cloud_api.data_lake.quarantine_serialization import (
    QuarantineSerializationError,
    serialize_quarantine_record,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_policy import (
    CommunityDataLakeQuarantinePolicy,
)

from ._quarantine_test_helpers import make_quarantine_record


def test_serialize_quarantine_record_is_canonical_and_digested() -> None:
    record = make_quarantine_record()
    first = serialize_quarantine_record(record)
    second = serialize_quarantine_record(record)
    assert first.data == second.data
    assert first.content_sha256 == second.content_sha256
    assert first.content_sha256.startswith(CONTENT_DIGEST_PREFIX)
    assert not first.data.endswith(b"\n")


def test_serialize_rejects_oversized_record() -> None:
    tiny = CommunityDataLakeQuarantinePolicy(max_serialized_record_bytes=256)
    record = make_quarantine_record(
        limitations=tuple(f"limitation_{i:02d}_padding_xxxxxxxx" for i in range(20))
    )
    try:
        serialize_quarantine_record(record, quarantine_policy=tiny)
        raise AssertionError("expected QuarantineSerializationError")
    except (QuarantineSerializationError, ValueError):
        pass
