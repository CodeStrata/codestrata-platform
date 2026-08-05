"""Determinism guarantees for assessment metadata partition projection (Slice 8.4)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.streams.assessment_metadata_partitioning import (
    default_assessment_metadata_partition_policy,
    project_assessment_metadata_storage_object,
)

from ._assessment_partitioning_test_helpers import assessment_envelope


def test_repeated_projection_of_the_same_envelope_is_byte_identical() -> None:
    envelope = assessment_envelope(event_id="amd-determinism-001")
    first = project_assessment_metadata_storage_object(envelope)
    second = project_assessment_metadata_storage_object(envelope)
    assert first.storage_object.object_key == second.storage_object.object_key
    assert first.storage_object.object_id == second.storage_object.object_id
    assert first.storage_object.canonical_json_bytes == second.storage_object.canonical_json_bytes
    assert first.storage_object.content_sha256 == second.storage_object.content_sha256
    assert first.storage_object.to_s3_metadata() == second.storage_object.to_s3_metadata()


def test_repeated_projection_produces_identical_diagnostics() -> None:
    envelope = assessment_envelope(event_id="amd-determinism-002")
    first = project_assessment_metadata_storage_object(envelope)
    second = project_assessment_metadata_storage_object(envelope)
    assert first.diagnostics == second.diagnostics
    assert first.diagnostics.to_stable_dict() == second.diagnostics.to_stable_dict()


def test_different_event_keys_produce_different_object_ids_and_keys() -> None:
    first = project_assessment_metadata_storage_object(
        assessment_envelope(event_key="event:determinism-key-a")
    )
    second = project_assessment_metadata_storage_object(
        assessment_envelope(event_key="event:determinism-key-b")
    )
    assert first.storage_object.object_id != second.storage_object.object_id
    assert first.storage_object.object_key != second.storage_object.object_key


def test_safe_object_reference_is_deterministically_derived_from_object_id() -> None:
    result = project_assessment_metadata_storage_object(
        assessment_envelope(event_key="event:determinism-ref-key")
    )
    expected_fragment = result.storage_object.opaque_object_id_hex[:16]
    assert result.diagnostics.safe_object_reference == f"lake-ref:{expected_fragment}"


def test_default_policy_instances_are_value_equal_across_calls() -> None:
    first = default_assessment_metadata_partition_policy()
    second = default_assessment_metadata_partition_policy()
    assert first == second
    assert hash(first) == hash(second)


def test_partition_date_dimensions_track_the_envelope_acceptance_date_deterministically() -> None:
    result = project_assessment_metadata_storage_object(
        assessment_envelope(event_key="event:determinism-date-key")
    )
    key = result.storage_object.object_key
    assert "year=2026" in key
    assert "month=08" in key
    assert "day=04" in key


def test_object_key_prefix_is_stable_across_two_different_but_same_day_events() -> None:
    first = project_assessment_metadata_storage_object(
        assessment_envelope(event_key="event:determinism-prefix-a")
    )
    second = project_assessment_metadata_storage_object(
        assessment_envelope(event_key="event:determinism-prefix-b")
    )
    prefix = "raw/stream=assessment_metadata/schema_version=1.0/year=2026/month=08/day=04/"
    assert first.storage_object.object_key.startswith(prefix)
    assert second.storage_object.object_key.startswith(prefix)
