"""Telemetry storage-object projection tests (Slice 8.5)."""

from __future__ import annotations

import dataclasses

import pytest

from codestrata_platform.community_cloud_api.data_lake.envelopes import build_envelope
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.data_lake.stream_storage import (
    StorageProjectionResult,
)
from codestrata_platform.community_cloud_api.data_lake.streams.telemetry_partitioning import (
    ALLOWED_PARTITION_PROJECTION_ERROR_CODES,
    CLIENT_TYPE_METADATA_KEY,
    PartitionProjectionError,
    default_telemetry_partition_policy,
    project_telemetry_storage_object,
)

from ._envelope_test_helpers import make_envelope
from ._telemetry_partitioning_test_helpers import telemetry_envelope

DEFAULT_POLICY = default_telemetry_partition_policy()


def _raw_telemetry_envelope(payload: dict[str, object], **overrides: object):
    base = dict(
        event_stream="telemetry",
        schema_name="community-telemetry",
        schema_version="1.0",
        policy_id="community-telemetry-policy:1.0",
        event_key="event:raw-telemetry-key",
        safe_event_reference="evt-rawtelemetry01",
        accepted_at="2026-08-04T00:00:00Z",
        client_type="codestrata_cli",
        payload=payload,
    )
    base.update(overrides)
    return build_envelope(**base)


def _valid_telemetry_payload(**overrides: object) -> dict[str, object]:
    envelope = telemetry_envelope()
    payload = dict(envelope.payload)
    payload.update(overrides)
    return payload


# --- project_telemetry_storage_object: happy path ---


def test_project_returns_storage_projection_result() -> None:
    envelope = telemetry_envelope()
    result = project_telemetry_storage_object(envelope)
    assert isinstance(result, StorageProjectionResult)


def test_project_object_key_is_the_generic_hive_path() -> None:
    envelope = telemetry_envelope()
    result = project_telemetry_storage_object(envelope)
    key = result.storage_object.object_key
    assert key.startswith(
        f"raw/stream=telemetry/schema_version=1.0/"
        f"year={envelope.accepted_year}/month={envelope.accepted_month}/"
        f"day={envelope.accepted_day}/"
    )
    assert key.endswith(".json")


def test_project_attaches_client_type_metadata() -> None:
    envelope = telemetry_envelope()
    result = project_telemetry_storage_object(envelope)
    metadata = result.storage_object.to_s3_metadata()
    assert metadata[CLIENT_TYPE_METADATA_KEY] == "codestrata_cli"


def test_project_diagnostics_reflect_the_envelope() -> None:
    envelope = telemetry_envelope()
    result = project_telemetry_storage_object(envelope)
    diagnostics = result.diagnostics
    assert diagnostics.event_stream == "telemetry"
    assert diagnostics.envelope_schema_version == "1.0"
    assert diagnostics.source_schema_version == "1.0"
    assert diagnostics.client_type == "codestrata_cli"
    assert diagnostics.assessment_schema_version is None
    assert diagnostics.partition_policy_version == "1.0"
    assert diagnostics.partition_valid is True
    assert diagnostics.projection_status == "projected"


def test_project_uses_default_policies_when_none_supplied() -> None:
    envelope = telemetry_envelope()
    result = project_telemetry_storage_object(envelope)
    assert result.diagnostics.partition_policy_version == DEFAULT_POLICY.policy_version


def test_project_supports_vscode_extension_client_type() -> None:
    envelope = telemetry_envelope(
        client={"name": "vscode_extension", "version": "0.2.0", "platform": "darwin"}
    )
    result = project_telemetry_storage_object(envelope)
    assert result.diagnostics.client_type == "vscode_extension"
    assert result.storage_object.to_s3_metadata()[CLIENT_TYPE_METADATA_KEY] == "vscode_extension"


def test_project_supports_other_extension_client_type() -> None:
    envelope = telemetry_envelope(
        client={"name": "other_extension", "version": "0.2.0", "platform": "linux"}
    )
    result = project_telemetry_storage_object(envelope)
    assert result.diagnostics.client_type == "other_extension"


# --- project_telemetry_storage_object: failure paths ---


def test_project_rejects_non_telemetry_stream_with_stream_mismatch() -> None:
    assessment_envelope = make_envelope(
        event_stream="assessment_metadata",
        schema_name="community-assessment-metadata",
        schema_version="1.0",
        policy_id="community-assessment-metadata-policy:1.0",
        payload={"assessment": {"assessment_schema_version": "1.2"}},
    )
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_telemetry_storage_object(assessment_envelope)
    assert excinfo.value.code == "stream_mismatch"


def test_project_rejects_unsupported_envelope_schema() -> None:
    envelope = telemetry_envelope()
    policy = dataclasses.replace(
        DEFAULT_POLICY, supported_envelope_schema_versions=frozenset({"9.9"})
    )
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_telemetry_storage_object(envelope, partition_policy=policy)
    assert excinfo.value.code == "unsupported_envelope_schema"


def test_project_rejects_unsupported_source_schema() -> None:
    envelope = telemetry_envelope()
    policy = dataclasses.replace(
        DEFAULT_POLICY, supported_source_schema_versions=frozenset({"9.9"})
    )
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_telemetry_storage_object(envelope, partition_policy=policy)
    assert excinfo.value.code == "unsupported_source_schema"


def test_project_rejects_unsupported_source_policy() -> None:
    envelope = telemetry_envelope()
    policy = dataclasses.replace(
        DEFAULT_POLICY, supported_source_policy_ids=frozenset({"other-policy:9.9"})
    )
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_telemetry_storage_object(envelope, partition_policy=policy)
    assert excinfo.value.code == "unsupported_source_policy"


def test_project_rejects_payload_that_fails_typed_revalidation() -> None:
    payload = _valid_telemetry_payload()
    del payload["client"]
    envelope = _raw_telemetry_envelope(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_telemetry_storage_object(envelope)
    assert excinfo.value.code == "invalid_payload"


def test_project_rejects_corrupted_event_type_as_invalid_payload() -> None:
    payload = _valid_telemetry_payload(event_type="not_a_real_event_type")
    envelope = _raw_telemetry_envelope(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_telemetry_storage_object(envelope)
    assert excinfo.value.code == "invalid_payload"


def test_project_rejects_missing_schema_version_as_invalid_payload() -> None:
    payload = _valid_telemetry_payload()
    del payload["schema_version"]
    envelope = _raw_telemetry_envelope(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_telemetry_storage_object(envelope)
    assert excinfo.value.code == "invalid_payload"


def test_project_rejects_envelope_client_type_not_in_vocabulary() -> None:
    payload = _valid_telemetry_payload()
    envelope = _raw_telemetry_envelope(payload, client_type="not_a_real_client")
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_telemetry_storage_object(envelope)
    assert excinfo.value.code == "invalid_client_type"


def test_project_rejects_envelope_client_type_mismatched_with_payload_client_name() -> None:
    payload = _valid_telemetry_payload()
    # The envelope declares a different (but still valid) client type than
    # the payload's own client.name — this must be rejected, not silently
    # trusted from either side.
    envelope = _raw_telemetry_envelope(payload, client_type="vscode_extension")
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_telemetry_storage_object(envelope)
    assert excinfo.value.code == "invalid_client_type"


def test_project_rejects_when_data_lake_policy_disallows_the_stream() -> None:
    envelope = telemetry_envelope()
    restrictive_policy = CommunityDataLakePolicy(allowed_event_streams=("assessment_metadata",))
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_telemetry_storage_object(envelope, data_lake_policy=restrictive_policy)
    assert excinfo.value.code == "storage_object_invalid"


def test_project_rejects_when_partition_key_exceeds_max_key_length() -> None:
    envelope = telemetry_envelope()
    tiny_policy = dataclasses.replace(DEFAULT_POLICY, max_key_length=64)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_telemetry_storage_object(envelope, partition_policy=tiny_policy)
    assert excinfo.value.code == "partition_invalid"


def test_partition_projection_error_rejects_unregistered_code() -> None:
    with pytest.raises(ValueError):
        PartitionProjectionError("not_a_real_code")


def test_partition_projection_error_to_stable_dict_never_echoes_payload() -> None:
    error = PartitionProjectionError("invalid_payload", "client_block_missing")
    blob = error.to_stable_dict()
    assert blob == {"code": "invalid_payload", "detail": "client_block_missing"}


def test_all_error_codes_are_reachable_via_the_allowlist() -> None:
    for code in ALLOWED_PARTITION_PROJECTION_ERROR_CODES:
        error = PartitionProjectionError(code)
        assert error.code == code


def test_no_assessment_schema_codes_are_in_the_telemetry_allowlist() -> None:
    assert "unsupported_assessment_schema" not in ALLOWED_PARTITION_PROJECTION_ERROR_CODES
    assert "missing_assessment_schema" not in ALLOWED_PARTITION_PROJECTION_ERROR_CODES
