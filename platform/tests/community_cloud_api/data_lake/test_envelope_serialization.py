"""Envelope serialize/deserialize round-trip and fail-closed tests (Slice 8.3)."""

from __future__ import annotations

import json

import pytest

from codestrata_platform.community_cloud_api.data_lake.canonical_json import CanonicalRawJson
from codestrata_platform.community_cloud_api.data_lake.envelope_models import EnvelopeErrorCode
from codestrata_platform.community_cloud_api.data_lake.envelope_serialization import (
    deserialize_data_lake_envelope,
    serialize_data_lake_envelope,
)
from codestrata_platform.community_cloud_api.data_lake.envelope_validation import EnvelopeBuildError
from codestrata_platform.community_cloud_api.data_lake.envelopes import DataLakeEnvelope
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy

from ._envelope_test_helpers import make_envelope
from ._request_test_helpers import make_telemetry_request

_TELEMETRY_PAYLOAD = make_telemetry_request().to_stable_dict()


def _round_trippable_envelope() -> DataLakeEnvelope:
    return make_envelope(
        event_stream="telemetry",
        schema_name="community-telemetry",
        schema_version="1.0",
        policy_id="community-telemetry-policy:1.0",
        payload=_TELEMETRY_PAYLOAD,
    )


def test_serialize_returns_canonical_raw_json() -> None:
    envelope = _round_trippable_envelope()
    canonical = serialize_data_lake_envelope(envelope)
    assert isinstance(canonical, CanonicalRawJson)
    assert canonical.content_length == len(canonical.data)
    assert canonical.content_sha256.startswith("sha256:")


def test_serialize_bytes_have_no_trailing_newline() -> None:
    envelope = _round_trippable_envelope()
    canonical = serialize_data_lake_envelope(envelope)
    assert not canonical.data.endswith(b"\n")


def test_round_trip_preserves_envelope_content() -> None:
    envelope = _round_trippable_envelope()
    canonical = serialize_data_lake_envelope(envelope)
    restored = deserialize_data_lake_envelope(canonical.data)
    assert restored.to_stable_dict() == envelope.to_stable_dict()


def test_round_trip_is_deterministic_byte_for_byte() -> None:
    envelope = _round_trippable_envelope()
    first = serialize_data_lake_envelope(envelope)
    second = serialize_data_lake_envelope(_round_trippable_envelope())
    assert first.data == second.data
    assert first.content_sha256 == second.content_sha256


def test_deserialize_rejects_non_utf8_bytes() -> None:
    with pytest.raises(EnvelopeBuildError) as excinfo:
        deserialize_data_lake_envelope(b"\xff\xfe\xfd")
    assert excinfo.value.code is EnvelopeErrorCode.ENVELOPE_DESERIALIZATION_FAILED


def test_deserialize_rejects_non_json_bytes() -> None:
    with pytest.raises(EnvelopeBuildError) as excinfo:
        deserialize_data_lake_envelope(b"not json at all {")
    assert excinfo.value.code is EnvelopeErrorCode.ENVELOPE_DESERIALIZATION_FAILED


def test_deserialize_rejects_json_array_root() -> None:
    with pytest.raises(EnvelopeBuildError) as excinfo:
        deserialize_data_lake_envelope(b"[1, 2, 3]")
    assert excinfo.value.code is EnvelopeErrorCode.ENVELOPE_DESERIALIZATION_FAILED


def test_deserialize_rejects_unknown_top_level_field() -> None:
    envelope = _round_trippable_envelope()
    blob = envelope.to_stable_dict()
    blob["unexpected_field"] = "value"
    data = json.dumps(blob).encode("utf-8")
    with pytest.raises(EnvelopeBuildError) as excinfo:
        deserialize_data_lake_envelope(data)
    assert excinfo.value.code is EnvelopeErrorCode.INVALID_ENVELOPE


def test_deserialize_rejects_missing_top_level_field() -> None:
    envelope = _round_trippable_envelope()
    blob = envelope.to_stable_dict()
    del blob["client"]
    data = json.dumps(blob).encode("utf-8")
    with pytest.raises(EnvelopeBuildError) as excinfo:
        deserialize_data_lake_envelope(data)
    assert excinfo.value.code is EnvelopeErrorCode.INVALID_ENVELOPE


def test_deserialize_rejects_unknown_field_inside_source_contract() -> None:
    envelope = _round_trippable_envelope()
    blob = envelope.to_stable_dict()
    blob["source_contract"]["extra"] = "x"
    data = json.dumps(blob).encode("utf-8")
    with pytest.raises(EnvelopeBuildError) as excinfo:
        deserialize_data_lake_envelope(data)
    assert excinfo.value.code is EnvelopeErrorCode.INVALID_ENVELOPE


def test_deserialize_rejects_missing_field_inside_identity() -> None:
    envelope = _round_trippable_envelope()
    blob = envelope.to_stable_dict()
    del blob["identity"]["safe_event_reference"]
    data = json.dumps(blob).encode("utf-8")
    with pytest.raises(EnvelopeBuildError) as excinfo:
        deserialize_data_lake_envelope(data)
    assert excinfo.value.code is EnvelopeErrorCode.INVALID_ENVELOPE


def test_deserialize_rejects_unsupported_envelope_schema_version() -> None:
    envelope = _round_trippable_envelope()
    blob = envelope.to_stable_dict()
    blob["envelope_schema_version"] = "9.9"
    data = json.dumps(blob).encode("utf-8")
    with pytest.raises(EnvelopeBuildError) as excinfo:
        deserialize_data_lake_envelope(data)
    assert excinfo.value.code is EnvelopeErrorCode.UNSUPPORTED_ENVELOPE_SCHEMA


def test_deserialize_rejects_payload_that_is_not_an_object() -> None:
    envelope = _round_trippable_envelope()
    blob = envelope.to_stable_dict()
    blob["payload"] = ["not", "an", "object"]
    data = json.dumps(blob).encode("utf-8")
    with pytest.raises(EnvelopeBuildError) as excinfo:
        deserialize_data_lake_envelope(data)
    assert excinfo.value.code is EnvelopeErrorCode.INVALID_ENVELOPE


def test_deserialize_rejects_oversized_envelope_under_tight_policy() -> None:
    # The size guard runs before payload revalidation, so an oversized dummy
    # payload is sufficient here without needing a valid telemetry shape.
    envelope = make_envelope(payload={"blob": "x" * 2000})
    canonical = serialize_data_lake_envelope(envelope)
    tight_policy = CommunityDataLakePolicy(max_envelope_bytes=1024)
    with pytest.raises(EnvelopeBuildError) as excinfo:
        deserialize_data_lake_envelope(canonical.data, policy=tight_policy)
    assert excinfo.value.code is EnvelopeErrorCode.ENVELOPE_TOO_LARGE


def test_deserialize_revalidates_payload_against_source_contract_by_default() -> None:
    envelope = _round_trippable_envelope()
    blob = envelope.to_stable_dict()
    blob["payload"] = {"not": "a_valid_telemetry_payload"}
    data = json.dumps(blob).encode("utf-8")
    with pytest.raises(EnvelopeBuildError) as excinfo:
        deserialize_data_lake_envelope(data)
    assert excinfo.value.code is EnvelopeErrorCode.INVALID_SOURCE_PAYLOAD


def test_deserialize_can_skip_payload_revalidation() -> None:
    envelope = _round_trippable_envelope()
    blob = envelope.to_stable_dict()
    blob["payload"] = {"not": "a_valid_telemetry_payload"}
    data = json.dumps(blob).encode("utf-8")
    restored = deserialize_data_lake_envelope(data, revalidate_payload=False)
    assert restored.payload == {"not": "a_valid_telemetry_payload"}


def test_deserialize_rejects_unsafe_payload_via_policy_privacy_scan() -> None:
    envelope = _round_trippable_envelope()
    blob = envelope.to_stable_dict()
    blob["payload"]["password"] = "hunter2"
    data = json.dumps(blob).encode("utf-8")
    with pytest.raises(EnvelopeBuildError) as excinfo:
        deserialize_data_lake_envelope(data, revalidate_payload=False)
    assert excinfo.value.code is EnvelopeErrorCode.UNSAFE_ENVELOPE
