"""Determinism guarantees for extension event partition projection (Slice 8.7)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.streams.extension_event_partitioning import (
    CLIENT_TYPE_METADATA_KEY,
    default_extension_event_partition_policy,
    project_extension_event_storage_object,
)

from ._extension_event_partitioning_test_helpers import extension_event_envelope
from ._request_test_helpers import make_extension_event_request


def test_repeated_projection_of_the_same_envelope_is_byte_identical() -> None:
    envelope = extension_event_envelope(event_id="ext-evt-determinism-0001")
    first = project_extension_event_storage_object(envelope)
    second = project_extension_event_storage_object(envelope)
    assert first.storage_object.object_key == second.storage_object.object_key
    assert first.storage_object.object_id == second.storage_object.object_id
    assert first.storage_object.canonical_json_bytes == second.storage_object.canonical_json_bytes
    assert first.storage_object.content_sha256 == second.storage_object.content_sha256
    assert first.storage_object.to_s3_metadata() == second.storage_object.to_s3_metadata()


def test_repeated_projection_produces_identical_diagnostics() -> None:
    envelope = extension_event_envelope(event_id="ext-evt-determinism-0002")
    first = project_extension_event_storage_object(envelope)
    second = project_extension_event_storage_object(envelope)
    assert first.diagnostics == second.diagnostics
    assert first.diagnostics.to_stable_dict() == second.diagnostics.to_stable_dict()


def test_different_event_keys_produce_different_object_ids_and_keys() -> None:
    first = project_extension_event_storage_object(
        extension_event_envelope(event_key="event:ext-determinism-key-a")
    )
    second = project_extension_event_storage_object(
        extension_event_envelope(event_key="event:ext-determinism-key-b")
    )
    assert first.storage_object.object_id != second.storage_object.object_id
    assert first.storage_object.object_key != second.storage_object.object_key


def test_operation_alias_and_canonical_operation_produce_the_same_envelope_bytes() -> None:
    # "codestrata.openHtmlReport" is a real catalog alias for the canonical
    # operation "open_report" — the model validator canonicalizes before any
    # storage, so both submissions must resolve to byte-identical projected
    # content once event_id and every other field match.
    canonical = project_extension_event_storage_object(
        extension_event_envelope(
            event_key="event:ext-alias-canonical",
            event_id="ext-evt-alias-0001",
            event={
                "operation": "open_report",
                "lifecycle": "completed",
                "result": "succeeded",
                "duration_bucket": "under_1s",
            },
        )
    )
    aliased = project_extension_event_storage_object(
        extension_event_envelope(
            event_key="event:ext-alias-canonical",
            event_id="ext-evt-alias-0001",
            event={
                "operation": "codestrata.openHtmlReport",
                "lifecycle": "completed",
                "result": "succeeded",
                "duration_bucket": "under_1s",
            },
        )
    )
    assert canonical.storage_object.canonical_json_bytes == aliased.storage_object.canonical_json_bytes
    assert canonical.storage_object.object_key == aliased.storage_object.object_key
    assert canonical.storage_object.content_sha256 == aliased.storage_object.content_sha256


def test_vscode_and_cursor_clients_produce_different_content() -> None:
    vscode = project_extension_event_storage_object(
        extension_event_envelope(
            event_key="event:ext-client-vscode",
            event_id="ext-evt-client-0001",
        )
    )
    cursor = project_extension_event_storage_object(
        extension_event_envelope(
            event_key="event:ext-client-cursor",
            event_id="ext-evt-client-0001",
            client={
                "name": "cursor_extension",
                "version": "0.2.0",
                "editor": "cursor",
                "editor_version": "1.85.0",
                "platform": "darwin",
            },
        )
    )
    assert vscode.storage_object.canonical_json_bytes != cursor.storage_object.canonical_json_bytes
    assert vscode.storage_object.to_s3_metadata()[CLIENT_TYPE_METADATA_KEY] == "vscode_extension"
    assert cursor.storage_object.to_s3_metadata()[CLIENT_TYPE_METADATA_KEY] == "cursor_extension"


def test_safe_object_reference_is_deterministically_derived_from_object_id() -> None:
    result = project_extension_event_storage_object(
        extension_event_envelope(event_key="event:ext-determinism-ref-key")
    )
    expected_fragment = result.storage_object.opaque_object_id_hex[:16]
    assert result.diagnostics.safe_object_reference == f"lake-ref:{expected_fragment}"


def test_default_policy_instances_are_value_equal_across_calls() -> None:
    first = default_extension_event_partition_policy()
    second = default_extension_event_partition_policy()
    assert first == second
    assert hash(first) == hash(second)


def test_partition_date_dimensions_track_the_envelope_acceptance_date_deterministically() -> None:
    result = project_extension_event_storage_object(
        extension_event_envelope(event_key="event:ext-determinism-date-key")
    )
    key = result.storage_object.object_key
    assert "year=2026" in key
    assert "month=08" in key
    assert "day=04" in key


def test_object_key_prefix_is_stable_across_two_different_but_same_day_events() -> None:
    first = project_extension_event_storage_object(
        extension_event_envelope(event_key="event:ext-determinism-prefix-a")
    )
    second = project_extension_event_storage_object(
        extension_event_envelope(event_key="event:ext-determinism-prefix-b")
    )
    prefix = "raw/stream=extension_event/schema_version=1.0/year=2026/month=08/day=04/"
    assert first.storage_object.object_key.startswith(prefix)
    assert second.storage_object.object_key.startswith(prefix)


def test_request_dict_key_order_does_not_affect_projected_bytes() -> None:
    # Round-trip through make_extension_event_request so model construction
    # and dict ordering cannot quietly change the projected content.
    first_request = make_extension_event_request(event_id="ext-evt-order-0001")
    second_request = make_extension_event_request(
        **{
            "schema_version": "1.0",
            "event_id": "ext-evt-order-0001",
            "context": first_request.context.model_dump(),
            "event": first_request.event.model_dump(),
            "client": first_request.client.model_dump(),
        }
    )
    assert first_request.model_dump() == second_request.model_dump()

    from codestrata_platform.community_cloud_api.data_lake.envelope_builders import (
        build_data_lake_envelope,
    )
    from ._extension_event_partitioning_test_helpers import DEFAULT_EXTENSION_EVENT_CLOCK

    first = project_extension_event_storage_object(
        build_data_lake_envelope(
            event_stream="extension_event",
            request=first_request,
            event_key="event:ext-order-key",
            safe_event_reference="evt-extorder0001",
            clock=DEFAULT_EXTENSION_EVENT_CLOCK,
        )
    )
    second = project_extension_event_storage_object(
        build_data_lake_envelope(
            event_stream="extension_event",
            request=second_request,
            event_key="event:ext-order-key",
            safe_event_reference="evt-extorder0001",
            clock=DEFAULT_EXTENSION_EVENT_CLOCK,
        )
    )
    assert first.storage_object.canonical_json_bytes == second.storage_object.canonical_json_bytes
