"""Assessment metadata storage-object projection tests (Slice 8.4)."""

from __future__ import annotations

import dataclasses

import pytest

from codestrata_platform.community_cloud_api.data_lake.envelopes import build_envelope
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.data_lake.stream_storage import (
    StorageProjectionResult,
)
from codestrata_platform.community_cloud_api.data_lake.streams.assessment_metadata_partitioning import (
    ALLOWED_PARTITION_PROJECTION_ERROR_CODES,
    ASSESSMENT_SCHEMA_METADATA_KEY,
    PartitionProjectionError,
    default_assessment_metadata_partition_policy,
    extract_assessment_schema_version,
    project_assessment_metadata_storage_object,
)

from ._assessment_partitioning_test_helpers import assessment_envelope
from ._envelope_test_helpers import make_envelope

DEFAULT_POLICY = default_assessment_metadata_partition_policy()


def _valid_assessment_payload(**assessment_overrides: object) -> dict[str, object]:
    envelope = assessment_envelope()
    payload = dict(envelope.payload)
    if assessment_overrides:
        assessment_block = dict(payload["assessment"])
        assessment_block.update(assessment_overrides)
        payload["assessment"] = assessment_block
    return payload


def _raw_assessment_envelope(payload: dict[str, object], **overrides: object):
    base = dict(
        event_stream="assessment_metadata",
        schema_name="community-assessment-metadata",
        schema_version="1.0",
        policy_id="community-assessment-metadata-policy:1.0",
        event_key="event:raw-assessment-key",
        safe_event_reference="evt-rawassessment01",
        accepted_at="2026-08-04T00:00:00Z",
        client_type="codestrata_cli",
        payload=payload,
    )
    base.update(overrides)
    return build_envelope(**base)


# --- extract_assessment_schema_version ---


def test_extract_assessment_schema_version_happy_path() -> None:
    envelope = assessment_envelope()
    assert extract_assessment_schema_version(envelope) == "1.2"


def test_extract_assessment_schema_version_missing_assessment_block_raises_invalid_payload() -> (
    None
):
    payload = _valid_assessment_payload()
    del payload["assessment"]
    envelope = _raw_assessment_envelope(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        extract_assessment_schema_version(envelope)
    assert excinfo.value.code == "invalid_payload"


def test_extract_assessment_schema_version_missing_field_raises_missing_assessment_schema() -> (
    None
):
    payload = _valid_assessment_payload()
    assessment_block = dict(payload["assessment"])
    del assessment_block["assessment_schema_version"]
    payload["assessment"] = assessment_block
    envelope = _raw_assessment_envelope(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        extract_assessment_schema_version(envelope)
    assert excinfo.value.code == "missing_assessment_schema"


def test_extract_assessment_schema_version_blank_string_raises_missing_assessment_schema() -> None:
    payload = _valid_assessment_payload(assessment_schema_version="   ")
    envelope = _raw_assessment_envelope(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        extract_assessment_schema_version(envelope)
    assert excinfo.value.code == "missing_assessment_schema"


# --- project_assessment_metadata_storage_object: happy path ---


def test_project_returns_storage_projection_result() -> None:
    envelope = assessment_envelope()
    result = project_assessment_metadata_storage_object(envelope)
    assert isinstance(result, StorageProjectionResult)


def test_project_object_key_is_the_generic_hive_path() -> None:
    envelope = assessment_envelope()
    result = project_assessment_metadata_storage_object(envelope)
    key = result.storage_object.object_key
    assert key.startswith(
        f"raw/stream=assessment_metadata/schema_version=1.0/"
        f"year={envelope.accepted_year}/month={envelope.accepted_month}/"
        f"day={envelope.accepted_day}/"
    )
    assert key.endswith(".json")


def test_project_attaches_assessment_schema_metadata() -> None:
    envelope = assessment_envelope()
    result = project_assessment_metadata_storage_object(envelope)
    metadata = result.storage_object.to_s3_metadata()
    assert metadata[ASSESSMENT_SCHEMA_METADATA_KEY] == "1.2"


def test_project_diagnostics_reflect_the_envelope() -> None:
    envelope = assessment_envelope()
    result = project_assessment_metadata_storage_object(envelope)
    diagnostics = result.diagnostics
    assert diagnostics.event_stream == "assessment_metadata"
    assert diagnostics.envelope_schema_version == "1.0"
    assert diagnostics.source_schema_version == "1.0"
    assert diagnostics.assessment_schema_version == "1.2"
    assert diagnostics.partition_policy_version == "1.0"
    assert diagnostics.partition_valid is True
    assert diagnostics.projection_status == "projected"


def test_project_uses_default_policies_when_none_supplied() -> None:
    envelope = assessment_envelope()
    result = project_assessment_metadata_storage_object(envelope)
    assert result.diagnostics.partition_policy_version == DEFAULT_POLICY.policy_version


# --- project_assessment_metadata_storage_object: failure paths ---


def test_project_rejects_non_assessment_stream_with_stream_mismatch() -> None:
    telemetry_envelope = make_envelope()
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_assessment_metadata_storage_object(telemetry_envelope)
    assert excinfo.value.code == "stream_mismatch"


def test_project_rejects_unsupported_envelope_schema() -> None:
    envelope = assessment_envelope()
    policy = dataclasses.replace(
        DEFAULT_POLICY, supported_envelope_schema_versions=frozenset({"9.9"})
    )
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_assessment_metadata_storage_object(envelope, partition_policy=policy)
    assert excinfo.value.code == "unsupported_envelope_schema"


def test_project_rejects_unsupported_source_schema() -> None:
    envelope = assessment_envelope()
    policy = dataclasses.replace(
        DEFAULT_POLICY, supported_source_schema_versions=frozenset({"9.9"})
    )
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_assessment_metadata_storage_object(envelope, partition_policy=policy)
    assert excinfo.value.code == "unsupported_source_schema"


def test_project_rejects_unsupported_source_policy() -> None:
    envelope = assessment_envelope()
    policy = dataclasses.replace(
        DEFAULT_POLICY, supported_source_policy_ids=frozenset({"other-policy:9.9"})
    )
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_assessment_metadata_storage_object(envelope, partition_policy=policy)
    assert excinfo.value.code == "unsupported_source_policy"


def test_project_rejects_unsupported_assessment_schema() -> None:
    envelope = assessment_envelope()
    policy = dataclasses.replace(
        DEFAULT_POLICY, supported_assessment_schema_versions=frozenset({"9.9"})
    )
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_assessment_metadata_storage_object(envelope, partition_policy=policy)
    assert excinfo.value.code == "unsupported_assessment_schema"


def test_project_rejects_missing_assessment_schema_field() -> None:
    payload = _valid_assessment_payload()
    assessment_block = dict(payload["assessment"])
    del assessment_block["assessment_schema_version"]
    payload["assessment"] = assessment_block
    envelope = _raw_assessment_envelope(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_assessment_metadata_storage_object(envelope)
    assert excinfo.value.code == "missing_assessment_schema"


def test_project_rejects_payload_that_fails_typed_revalidation() -> None:
    payload = _valid_assessment_payload()
    del payload["client"]
    envelope = _raw_assessment_envelope(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_assessment_metadata_storage_object(envelope)
    assert excinfo.value.code == "invalid_payload"


def test_project_rejects_when_data_lake_policy_disallows_the_stream() -> None:
    envelope = assessment_envelope()
    restrictive_policy = CommunityDataLakePolicy(allowed_event_streams=("telemetry",))
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_assessment_metadata_storage_object(envelope, data_lake_policy=restrictive_policy)
    assert excinfo.value.code == "storage_object_invalid"


def test_project_rejects_when_partition_key_exceeds_max_key_length() -> None:
    envelope = assessment_envelope()
    tiny_policy = dataclasses.replace(DEFAULT_POLICY, max_key_length=64)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_assessment_metadata_storage_object(envelope, partition_policy=tiny_policy)
    assert excinfo.value.code == "partition_invalid"


def test_partition_projection_error_rejects_unregistered_code() -> None:
    with pytest.raises(ValueError):
        PartitionProjectionError("not_a_real_code")


def test_partition_projection_error_to_stable_dict_never_echoes_payload() -> None:
    error = PartitionProjectionError("invalid_payload", "assessment_block_missing")
    blob = error.to_stable_dict()
    assert blob == {"code": "invalid_payload", "detail": "assessment_block_missing"}


def test_all_error_codes_are_reachable_via_the_allowlist() -> None:
    for code in ALLOWED_PARTITION_PROJECTION_ERROR_CODES:
        error = PartitionProjectionError(code)
        assert error.code == code
