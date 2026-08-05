"""Determinism guarantees for CLI event partition projection (Slice 8.6)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.streams.cli_event_partitioning import (
    default_cli_event_partition_policy,
    project_cli_event_storage_object,
)

from ._cli_event_partitioning_test_helpers import cli_event_envelope


def test_repeated_projection_of_the_same_envelope_is_byte_identical() -> None:
    envelope = cli_event_envelope(event_id="cli-evt-determinism-0001")
    first = project_cli_event_storage_object(envelope)
    second = project_cli_event_storage_object(envelope)
    assert first.storage_object.object_key == second.storage_object.object_key
    assert first.storage_object.object_id == second.storage_object.object_id
    assert first.storage_object.canonical_json_bytes == second.storage_object.canonical_json_bytes
    assert first.storage_object.content_sha256 == second.storage_object.content_sha256
    assert first.storage_object.to_s3_metadata() == second.storage_object.to_s3_metadata()


def test_repeated_projection_produces_identical_diagnostics() -> None:
    envelope = cli_event_envelope(event_id="cli-evt-determinism-0002")
    first = project_cli_event_storage_object(envelope)
    second = project_cli_event_storage_object(envelope)
    assert first.diagnostics == second.diagnostics
    assert first.diagnostics.to_stable_dict() == second.diagnostics.to_stable_dict()


def test_different_event_keys_produce_different_object_ids_and_keys() -> None:
    first = project_cli_event_storage_object(
        cli_event_envelope(event_key="event:cli-determinism-key-a")
    )
    second = project_cli_event_storage_object(
        cli_event_envelope(event_key="event:cli-determinism-key-b")
    )
    assert first.storage_object.object_id != second.storage_object.object_id
    assert first.storage_object.object_key != second.storage_object.object_key


def test_operation_alias_and_canonical_operation_produce_the_same_envelope_bytes() -> None:
    # "report.open" is a real catalog alias (see cli_events/catalog.py) for
    # the canonical operation "open" — the model validator canonicalizes
    # before any storage, so both submissions must resolve to byte-identical
    # projected content once event_id and every other field match.
    canonical = project_cli_event_storage_object(
        cli_event_envelope(
            event_key="event:cli-alias-canonical",
            event_id="cli-evt-alias-0001",
            event={
                "operation": "open",
                "lifecycle": "completed",
                "result": "succeeded",
                "duration_bucket": "under_1s",
            },
        )
    )
    aliased = project_cli_event_storage_object(
        cli_event_envelope(
            event_key="event:cli-alias-canonical",
            event_id="cli-evt-alias-0001",
            event={
                "operation": "report.open",
                "lifecycle": "completed",
                "result": "succeeded",
                "duration_bucket": "under_1s",
            },
        )
    )
    assert canonical.storage_object.canonical_json_bytes == aliased.storage_object.canonical_json_bytes
    assert canonical.storage_object.object_key == aliased.storage_object.object_key
    assert canonical.storage_object.content_sha256 == aliased.storage_object.content_sha256


def test_safe_object_reference_is_deterministically_derived_from_object_id() -> None:
    result = project_cli_event_storage_object(
        cli_event_envelope(event_key="event:cli-determinism-ref-key")
    )
    expected_fragment = result.storage_object.opaque_object_id_hex[:16]
    assert result.diagnostics.safe_object_reference == f"lake-ref:{expected_fragment}"


def test_default_policy_instances_are_value_equal_across_calls() -> None:
    first = default_cli_event_partition_policy()
    second = default_cli_event_partition_policy()
    assert first == second
    assert hash(first) == hash(second)


def test_partition_date_dimensions_track_the_envelope_acceptance_date_deterministically() -> None:
    result = project_cli_event_storage_object(
        cli_event_envelope(event_key="event:cli-determinism-date-key")
    )
    key = result.storage_object.object_key
    assert "year=2026" in key
    assert "month=08" in key
    assert "day=04" in key


def test_object_key_prefix_is_stable_across_two_different_but_same_day_events() -> None:
    first = project_cli_event_storage_object(
        cli_event_envelope(event_key="event:cli-determinism-prefix-a")
    )
    second = project_cli_event_storage_object(
        cli_event_envelope(event_key="event:cli-determinism-prefix-b")
    )
    prefix = "raw/stream=cli_event/schema_version=1.0/year=2026/month=08/day=04/"
    assert first.storage_object.object_key.startswith(prefix)
    assert second.storage_object.object_key.startswith(prefix)
