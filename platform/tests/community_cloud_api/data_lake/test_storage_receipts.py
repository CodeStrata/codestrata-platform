"""Privacy-safe storage receipt tests (Slice 8.2)."""

from __future__ import annotations

import json
from dataclasses import replace

from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.immutable_write import (
    build_immutable_raw_storage_object,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.data_lake.receipts import (
    STORED_OBJECT_REFERENCE_PREFIX,
    build_receipt_from_object,
)

from ._envelope_test_helpers import make_envelope

POLICY = CommunityDataLakePolicy.default()

_FORBIDDEN_PUBLIC_KEYS = frozenset(
    {"object_key", "bucket", "etag", "version_id", "region", "account", "account_id"}
)


def _envelope(**overrides: object) -> object:
    base: dict[str, object] = dict(
        event_stream="ai_usage",
        schema_name="community-ai-usage",
        schema_version="1.0",
        policy_id="community-ai-usage-policy:1.0",
        safe_event_reference="evt-receiptkeyaaaa",
        event_key="event:receipts-key",
        payload={"canonical_capability": "chat"},
    )
    base.update(overrides)
    return make_envelope(**base)  # type: ignore[arg-type]


def _storage_object():
    return build_immutable_raw_storage_object(_envelope(), POLICY)


def test_build_receipt_from_object_populates_all_identity_fields() -> None:
    obj = _storage_object()
    receipt = build_receipt_from_object(StorageWriteStatus.STORED, obj)
    assert receipt.status is StorageWriteStatus.STORED
    assert receipt.object_id == obj.object_id
    assert receipt.safe_event_reference == obj.safe_event_reference
    assert receipt.event_stream == obj.event_stream
    assert receipt.content_sha256 == obj.content_sha256
    assert receipt.content_length == obj.content_length
    assert receipt.envelope_schema_version == obj.envelope_schema_version
    assert receipt.source_schema_version == obj.source_schema_version
    assert receipt.storage_policy_token == obj.storage_policy_token
    assert receipt.object_key == obj.object_key


def test_stored_object_reference_is_opaque_and_prefixed() -> None:
    obj = _storage_object()
    receipt = build_receipt_from_object(StorageWriteStatus.STORED, obj)
    assert receipt.stored_object_reference.startswith(STORED_OBJECT_REFERENCE_PREFIX)
    fragment = receipt.stored_object_reference.removeprefix(STORED_OBJECT_REFERENCE_PREFIX)
    assert fragment == obj.opaque_object_id_hex[:16]


def test_to_public_dict_never_includes_internal_fields() -> None:
    obj = _storage_object()
    receipt = build_receipt_from_object(StorageWriteStatus.STORED, obj)
    public = receipt.to_public_dict()
    assert set(public) & _FORBIDDEN_PUBLIC_KEYS == set()
    blob = json.dumps(public)
    assert obj.object_key not in blob


def test_to_public_dict_is_json_serializable_and_sorted() -> None:
    obj = _storage_object()
    receipt = build_receipt_from_object(StorageWriteStatus.ALREADY_EXISTS, obj)
    public = receipt.to_public_dict()
    json.dumps(public)  # must not raise
    assert list(public) == sorted(public)


def test_to_internal_dict_includes_object_key_when_present() -> None:
    obj = _storage_object()
    receipt = build_receipt_from_object(StorageWriteStatus.STORED, obj)
    internal = receipt.to_internal_dict()
    assert internal["object_key"] == obj.object_key
    # Internal dict is a strict superset of the public dict.
    public = receipt.to_public_dict()
    for key, value in public.items():
        assert internal[key] == value


def test_to_internal_dict_omits_object_key_when_absent() -> None:
    obj = _storage_object()
    receipt = build_receipt_from_object(StorageWriteStatus.STORED, obj)
    receipt_no_key = replace(receipt, object_key=None)
    internal = receipt_no_key.to_internal_dict()
    assert "object_key" not in internal


def test_limitations_never_claims_exactly_once_delivery() -> None:
    obj = _storage_object()
    receipt = build_receipt_from_object(StorageWriteStatus.STORED, obj)
    blob = " ".join(receipt.limitations).lower()
    assert "exactly_once" in blob or "exactly-once" in blob
    assert "guarantees_exactly_once" not in blob


def test_limitations_are_sorted_and_deduplicated() -> None:
    obj = _storage_object()
    receipt = build_receipt_from_object(
        StorageWriteStatus.STORED,
        obj,
        limitations=("b_item", "a_item", "a_item"),
    )
    assert receipt.limitations == ("a_item", "b_item")


def test_status_value_reflected_in_public_dict() -> None:
    obj = _storage_object()
    for status in (StorageWriteStatus.STORED, StorageWriteStatus.ALREADY_EXISTS, StorageWriteStatus.CONFLICT):
        receipt = build_receipt_from_object(status, obj)
        assert receipt.to_public_dict()["status"] == status.value
