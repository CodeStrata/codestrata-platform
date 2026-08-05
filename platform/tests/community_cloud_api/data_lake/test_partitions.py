"""Hive-style Data Lake object key construction tests (Slice 8.1)."""

from __future__ import annotations

import pytest

from codestrata_platform.community_cloud_api.data_lake.identifiers import build_lake_object_id
from codestrata_platform.community_cloud_api.data_lake.partitions import (
    PartitionKeyError,
    assert_key_excludes_identity_material,
    build_accepted_object_key,
    build_quarantine_object_key,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy

from ._envelope_test_helpers import make_envelope

POLICY_TOKEN = CommunityDataLakePolicy.default().policy_token


def _envelope(**overrides: object) -> object:
    return make_envelope(**overrides)  # type: ignore[arg-type]


def test_build_accepted_object_key_hive_style_format() -> None:
    envelope = _envelope()
    lake_object_id = build_lake_object_id(
        POLICY_TOKEN, envelope.event_stream, envelope.source_schema_version, envelope.event_key
    )
    key = build_accepted_object_key(envelope, lake_object_id, hive_style=True)
    hex_part = lake_object_id.split(":", 1)[1]
    assert key == (
        f"raw/stream=telemetry/schema_version=1.0/year=2026/month=08/day=03/{hex_part}.json"
    )


def test_build_accepted_object_key_non_hive_style_format() -> None:
    envelope = _envelope()
    lake_object_id = build_lake_object_id(
        POLICY_TOKEN, envelope.event_stream, envelope.source_schema_version, envelope.event_key
    )
    key = build_accepted_object_key(envelope, lake_object_id, hive_style=False)
    hex_part = lake_object_id.split(":", 1)[1]
    assert key == f"raw/telemetry/1.0/2026/08/03/{hex_part}.json"


def test_build_accepted_object_key_is_deterministic_for_identical_envelope() -> None:
    envelope = _envelope()
    lake_object_id = build_lake_object_id(
        POLICY_TOKEN, envelope.event_stream, envelope.source_schema_version, envelope.event_key
    )
    first = build_accepted_object_key(envelope, lake_object_id)
    second = build_accepted_object_key(envelope, lake_object_id)
    assert first == second


def test_build_quarantine_object_key_hive_style_format() -> None:
    lake_object_id = build_lake_object_id(POLICY_TOKEN, "telemetry", "1.0", "event:quarantined")
    key = build_quarantine_object_key(
        "invalid_envelope", "2026", "08", "03", lake_object_id, hive_style=True
    )
    hex_part = lake_object_id.split(":", 1)[1]
    assert key == (
        f"quarantine/reason=invalid_envelope/year=2026/month=08/day=03/{hex_part}.json"
    )


def test_build_quarantine_object_key_non_hive_style_format() -> None:
    lake_object_id = build_lake_object_id(POLICY_TOKEN, "telemetry", "1.0", "event:quarantined")
    key = build_quarantine_object_key(
        "unsafe_payload", "2026", "08", "03", lake_object_id, hive_style=False
    )
    hex_part = lake_object_id.split(":", 1)[1]
    assert key == f"quarantine/unsafe_payload/2026/08/03/{hex_part}.json"


def test_build_quarantine_object_key_rejects_unknown_reason() -> None:
    lake_object_id = build_lake_object_id(POLICY_TOKEN, "telemetry", "1.0", "event:quarantined")
    with pytest.raises(ValueError):
        build_quarantine_object_key("not_a_real_reason", "2026", "08", "03", lake_object_id)


def test_build_accepted_object_key_revalidates_stream_even_if_envelope_is_tampered() -> None:
    envelope = _envelope()
    lake_object_id = build_lake_object_id(
        POLICY_TOKEN, envelope.event_stream, envelope.source_schema_version, envelope.event_key
    )
    object.__setattr__(envelope, "event_stream", "not_a_real_stream")
    with pytest.raises(ValueError):
        build_accepted_object_key(envelope, lake_object_id)


@pytest.mark.parametrize(
    "key",
    [
        "raw/stream=telemetry/schema_version=1.0/year=2026/month=08/day=03//Users/alice/x.json",
        "raw/stream=telemetry/.../event:abc123.json",
        "raw/stream=telemetry/installation-1234.json",
        "raw/stream=telemetry/request_id=abc123.json",
        "raw/stream=telemetry/ip_address=127.0.0.1.json",
        "raw/../etc/passwd",
        "raw/stream=telemetry/evt-aaaaaaaaaaaa.json",
    ],
)
def test_assert_key_excludes_identity_material_rejects_unsafe_keys(key: str) -> None:
    with pytest.raises(PartitionKeyError):
        assert_key_excludes_identity_material(key)


def test_assert_key_excludes_identity_material_accepts_safe_key() -> None:
    assert_key_excludes_identity_material(
        "raw/stream=telemetry/schema_version=1.0/year=2026/month=08/day=03/abc123.json"
    )


def test_assert_key_excludes_identity_material_rejects_empty_key() -> None:
    with pytest.raises(PartitionKeyError):
        assert_key_excludes_identity_material("")


def test_assert_key_excludes_identity_material_rejects_null_byte() -> None:
    with pytest.raises(PartitionKeyError):
        assert_key_excludes_identity_material("raw/stream=telemetry/\x00abc.json")
