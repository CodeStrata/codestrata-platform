"""Fail-closed envelope validation guard-helper tests (Slice 8.3)."""

from __future__ import annotations

import pytest

from codestrata_platform.community_cloud_api.data_lake.envelope_models import EnvelopeErrorCode
from codestrata_platform.community_cloud_api.data_lake.envelope_validation import (
    EnvelopeBuildError,
    require_allowed_client_type,
    require_bounded_size,
    require_matching_request_model,
    require_supported_envelope_schema_version,
    require_supported_source_policy,
    require_supported_source_schema_version,
    revalidate_payload_against_source_contract,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.telemetry.models import TelemetryIngestionRequest

from ._envelope_test_helpers import make_envelope
from ._request_test_helpers import make_telemetry_request


def test_require_supported_envelope_schema_version_passes_for_match() -> None:
    policy = CommunityDataLakePolicy.default()
    require_supported_envelope_schema_version(policy.envelope_schema_version, policy)


def test_require_supported_envelope_schema_version_rejects_mismatch() -> None:
    policy = CommunityDataLakePolicy.default()
    with pytest.raises(EnvelopeBuildError) as excinfo:
        require_supported_envelope_schema_version("9.9", policy)
    assert excinfo.value.code is EnvelopeErrorCode.UNSUPPORTED_ENVELOPE_SCHEMA


def test_require_supported_source_schema_version_passes_for_match() -> None:
    require_supported_source_schema_version("1.0", "1.0")


def test_require_supported_source_schema_version_rejects_mismatch() -> None:
    with pytest.raises(EnvelopeBuildError) as excinfo:
        require_supported_source_schema_version("2.0", "1.0")
    assert excinfo.value.code is EnvelopeErrorCode.UNSUPPORTED_SOURCE_SCHEMA


def test_require_supported_source_policy_passes_for_match() -> None:
    require_supported_source_policy("community-telemetry-policy:1.0", "community-telemetry-policy:1.0")


def test_require_supported_source_policy_rejects_mismatch() -> None:
    with pytest.raises(EnvelopeBuildError) as excinfo:
        require_supported_source_policy("community-telemetry-policy:2.0", "community-telemetry-policy:1.0")
    assert excinfo.value.code is EnvelopeErrorCode.UNSUPPORTED_SOURCE_POLICY


def test_require_matching_request_model_passes_for_instance() -> None:
    require_matching_request_model(make_telemetry_request(), TelemetryIngestionRequest)


def test_require_matching_request_model_rejects_non_instance() -> None:
    with pytest.raises(EnvelopeBuildError) as excinfo:
        require_matching_request_model(object(), TelemetryIngestionRequest)
    assert excinfo.value.code is EnvelopeErrorCode.STREAM_CONTRACT_MISMATCH


def test_require_allowed_client_type_passes_for_allowed() -> None:
    require_allowed_client_type("codestrata_cli", frozenset({"codestrata_cli"}))


def test_require_allowed_client_type_rejects_disallowed() -> None:
    with pytest.raises(EnvelopeBuildError) as excinfo:
        require_allowed_client_type("mystery_client", frozenset({"codestrata_cli"}))
    assert excinfo.value.code is EnvelopeErrorCode.STREAM_CONTRACT_MISMATCH
    assert excinfo.value.detail == "client_type_not_allowed"


def test_require_bounded_size_passes_within_bound() -> None:
    policy = CommunityDataLakePolicy.default()
    require_bounded_size(100, policy)


def test_require_bounded_size_rejects_over_bound() -> None:
    policy = CommunityDataLakePolicy(max_envelope_bytes=1024)
    with pytest.raises(EnvelopeBuildError) as excinfo:
        require_bounded_size(2000, policy)
    assert excinfo.value.code is EnvelopeErrorCode.ENVELOPE_TOO_LARGE


def test_revalidate_payload_against_source_contract_passes_for_untampered_envelope() -> None:
    envelope = make_envelope(
        event_stream="telemetry",
        schema_name="community-telemetry",
        schema_version="1.0",
        policy_id="community-telemetry-policy:1.0",
        payload=make_telemetry_request().to_stable_dict(),
    )
    revalidate_payload_against_source_contract(envelope)


def test_revalidate_payload_against_source_contract_rejects_unknown_stream() -> None:
    envelope = make_envelope(event_stream="telemetry")
    object.__setattr__(envelope, "event_stream", "not_a_real_stream")
    with pytest.raises(EnvelopeBuildError) as excinfo:
        revalidate_payload_against_source_contract(envelope)
    assert excinfo.value.code is EnvelopeErrorCode.INVALID_ENVELOPE


def test_revalidate_payload_against_source_contract_rejects_schema_name_mismatch() -> None:
    envelope = make_envelope(
        event_stream="telemetry",
        schema_name="not-the-registered-schema-name",
        payload=make_telemetry_request().to_stable_dict(),
    )
    with pytest.raises(EnvelopeBuildError) as excinfo:
        revalidate_payload_against_source_contract(envelope)
    assert excinfo.value.code is EnvelopeErrorCode.UNSUPPORTED_SOURCE_SCHEMA


def test_revalidate_payload_against_source_contract_rejects_source_schema_version_mismatch() -> None:
    envelope = make_envelope(
        event_stream="telemetry",
        schema_version="9.9",
        payload=make_telemetry_request().to_stable_dict(),
    )
    with pytest.raises(EnvelopeBuildError) as excinfo:
        revalidate_payload_against_source_contract(envelope)
    assert excinfo.value.code is EnvelopeErrorCode.UNSUPPORTED_SOURCE_SCHEMA


def test_revalidate_payload_against_source_contract_rejects_source_policy_mismatch() -> None:
    envelope = make_envelope(
        event_stream="telemetry",
        policy_id="community-telemetry-policy:9.9",
        payload=make_telemetry_request().to_stable_dict(),
    )
    with pytest.raises(EnvelopeBuildError) as excinfo:
        revalidate_payload_against_source_contract(envelope)
    assert excinfo.value.code is EnvelopeErrorCode.UNSUPPORTED_SOURCE_POLICY


def test_revalidate_payload_against_source_contract_rejects_payload_that_fails_model_validation() -> None:
    envelope = make_envelope(
        event_stream="telemetry",
        payload={"not": "a_valid_telemetry_payload"},
    )
    with pytest.raises(EnvelopeBuildError) as excinfo:
        revalidate_payload_against_source_contract(envelope)
    assert excinfo.value.code is EnvelopeErrorCode.INVALID_SOURCE_PAYLOAD
