"""Canonical serialized envelope shape contract tests (Slice 8.3).

Locks in the exact top-level and nested-object shape documented in
``platform/docs/community-cloud-api/data-lake-event-envelope.md`` — a
regression here means the storage contract silently drifted.
"""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.envelopes import DataLakeEventEnvelope

from ._envelope_test_helpers import make_envelope

_TOP_LEVEL_FIELDS = frozenset(
    {
        "acceptance",
        "client",
        "envelope_schema_version",
        "event_stream",
        "identity",
        "payload",
        "source_contract",
    }
)


def test_stable_dict_has_exactly_the_documented_top_level_fields() -> None:
    envelope = make_envelope()
    assert set(envelope.to_stable_dict()) == _TOP_LEVEL_FIELDS


def test_stable_dict_top_level_keys_are_sorted() -> None:
    envelope = make_envelope()
    blob = envelope.to_stable_dict()
    assert list(blob) == sorted(blob)


def test_acceptance_block_shape() -> None:
    envelope = make_envelope(accepted_at="2026-08-04T12:34:56Z")
    assert envelope.to_stable_dict()["acceptance"] == {
        "accepted_at": "2026-08-04T12:34:56Z",
        "partition_date": "2026-08-04",
    }


def test_client_block_shape() -> None:
    envelope = make_envelope(client_type="codestrata_cli")
    assert envelope.to_stable_dict()["client"] == {"client_type": "codestrata_cli"}


def test_identity_block_shape() -> None:
    envelope = make_envelope(
        event_key="event:abcdef1234567890abcdef12", safe_event_reference="evt-aaaaaaaaaaaa"
    )
    assert envelope.to_stable_dict()["identity"] == {
        "event_key": "event:abcdef1234567890abcdef12",
        "safe_event_reference": "evt-aaaaaaaaaaaa",
    }


def test_source_contract_block_shape() -> None:
    envelope = make_envelope(
        event_stream="telemetry",
        schema_name="community-telemetry",
        schema_version="1.0",
        policy_id="community-telemetry-policy:1.0",
    )
    assert envelope.to_stable_dict()["source_contract"] == {
        "policy_id": "community-telemetry-policy:1.0",
        "schema_name": "community-telemetry",
        "schema_version": "1.0",
    }


def test_envelope_schema_version_and_event_stream_are_scalar_top_level_fields() -> None:
    envelope = make_envelope(event_stream="telemetry")
    blob = envelope.to_stable_dict()
    assert blob["envelope_schema_version"] == "1.0"
    assert blob["event_stream"] == "telemetry"


def test_payload_fingerprint_is_never_part_of_the_storage_envelope() -> None:
    envelope = make_envelope()
    assert "payload_fingerprint" not in envelope.to_stable_dict()
    assert not hasattr(envelope, "payload_fingerprint")


def test_data_lake_event_envelope_is_an_alias_for_data_lake_envelope() -> None:
    envelope = make_envelope()
    assert isinstance(envelope, DataLakeEventEnvelope)


def test_nested_block_dicts_are_sorted() -> None:
    envelope = make_envelope()
    blob = envelope.to_stable_dict()
    for nested_key in ("acceptance", "client", "identity", "source_contract"):
        nested = blob[nested_key]
        assert list(nested) == sorted(nested)
