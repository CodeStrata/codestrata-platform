"""Quarantine determinism tests (Slice 8.9)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.ports import InMemoryCommunityDataLakeStore
from codestrata_platform.community_cloud_api.data_lake.quarantine_identity import (
    build_quarantine_object_id,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_policy import (
    default_quarantine_policy,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_projection import (
    project_quarantine_storage_object,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_serialization import (
    serialize_quarantine_record,
)

from ._quarantine_test_helpers import make_quarantine_record

POLICY_TOKEN = default_quarantine_policy().policy_token


def test_projection_bytes_are_deterministic() -> None:
    record = make_quarantine_record()
    first = project_quarantine_storage_object(record).storage_object
    second = project_quarantine_storage_object(record).storage_object
    assert first.canonical_json_bytes == second.canonical_json_bytes
    assert first.content_sha256 == second.content_sha256
    assert first.object_id == second.object_id
    assert first.object_key == second.object_key


def test_in_memory_store_replay_uses_digest_equality() -> None:
    store = InMemoryCommunityDataLakeStore()
    record = make_quarantine_record()
    first = store.quarantine_event(record)
    second = store.quarantine_event(record)
    assert first.object_key == second.object_key
    assert store.get_quarantined_digest(first.object_key) == serialize_quarantine_record(
        record
    ).content_sha256


def test_identity_stable_across_builder_calls() -> None:
    a = make_quarantine_record(safe_event_reference="evt-determinism01")
    b = make_quarantine_record(safe_event_reference="evt-determinism01")
    assert build_quarantine_object_id(a, policy_token=POLICY_TOKEN) == build_quarantine_object_id(
        b, policy_token=POLICY_TOKEN
    )
