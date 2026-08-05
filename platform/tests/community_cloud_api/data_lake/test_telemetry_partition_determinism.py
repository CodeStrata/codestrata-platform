"""Determinism guarantees for telemetry partition projection (Slice 8.5)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.streams.telemetry_partitioning import (
    default_telemetry_partition_policy,
    project_telemetry_storage_object,
)

from ._telemetry_partitioning_test_helpers import telemetry_envelope


def test_repeated_projection_of_the_same_envelope_is_byte_identical() -> None:
    envelope = telemetry_envelope(event_id="evt-determinism-0001")
    first = project_telemetry_storage_object(envelope)
    second = project_telemetry_storage_object(envelope)
    assert first.storage_object.object_key == second.storage_object.object_key
    assert first.storage_object.object_id == second.storage_object.object_id
    assert first.storage_object.canonical_json_bytes == second.storage_object.canonical_json_bytes
    assert first.storage_object.content_sha256 == second.storage_object.content_sha256
    assert first.storage_object.to_s3_metadata() == second.storage_object.to_s3_metadata()


def test_repeated_projection_produces_identical_diagnostics() -> None:
    envelope = telemetry_envelope(event_id="evt-determinism-0002")
    first = project_telemetry_storage_object(envelope)
    second = project_telemetry_storage_object(envelope)
    assert first.diagnostics == second.diagnostics
    assert first.diagnostics.to_stable_dict() == second.diagnostics.to_stable_dict()


def test_different_event_keys_produce_different_object_ids_and_keys() -> None:
    first = project_telemetry_storage_object(
        telemetry_envelope(event_key="event:determinism-key-a")
    )
    second = project_telemetry_storage_object(
        telemetry_envelope(event_key="event:determinism-key-b")
    )
    assert first.storage_object.object_id != second.storage_object.object_id
    assert first.storage_object.object_key != second.storage_object.object_key


def test_safe_object_reference_is_deterministically_derived_from_object_id() -> None:
    result = project_telemetry_storage_object(
        telemetry_envelope(event_key="event:determinism-ref-key")
    )
    expected_fragment = result.storage_object.opaque_object_id_hex[:16]
    assert result.diagnostics.safe_object_reference == f"lake-ref:{expected_fragment}"


def test_default_policy_instances_are_value_equal_across_calls() -> None:
    first = default_telemetry_partition_policy()
    second = default_telemetry_partition_policy()
    assert first == second
    assert hash(first) == hash(second)


def test_partition_date_dimensions_track_the_envelope_acceptance_date_deterministically() -> None:
    result = project_telemetry_storage_object(
        telemetry_envelope(event_key="event:determinism-date-key")
    )
    key = result.storage_object.object_key
    assert "year=2026" in key
    assert "month=08" in key
    assert "day=04" in key


def test_object_key_prefix_is_stable_across_two_different_but_same_day_events() -> None:
    first = project_telemetry_storage_object(
        telemetry_envelope(event_key="event:determinism-prefix-a")
    )
    second = project_telemetry_storage_object(
        telemetry_envelope(event_key="event:determinism-prefix-b")
    )
    prefix = "raw/stream=telemetry/schema_version=1.0/year=2026/month=08/day=04/"
    assert first.storage_object.object_key.startswith(prefix)
    assert second.storage_object.object_key.startswith(prefix)


def test_occurred_at_in_payload_does_not_affect_partition_date() -> None:
    # occurred_at is client-submitted content; only the server-assigned
    # acceptance date (via the fixed clock) may ever drive the partition.
    result = project_telemetry_storage_object(
        telemetry_envelope(
            event_key="event:determinism-occurred-at-key",
            occurred_at="2020-01-01T00:00:00Z",
        )
    )
    key = result.storage_object.object_key
    assert "year=2026" in key
    assert "month=08" in key
    assert "day=04" in key
    assert "year=2020" not in key
