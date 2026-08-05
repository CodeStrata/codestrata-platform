"""CLI event storage-object projection tests (Slice 8.6)."""

from __future__ import annotations

import dataclasses

import pytest

from codestrata_platform.community_cloud_api.cli_events.enums import CLI_CLIENT_NAME
from codestrata_platform.community_cloud_api.data_lake.envelopes import build_envelope
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.data_lake.stream_storage import (
    StorageProjectionResult,
)
from codestrata_platform.community_cloud_api.data_lake.streams.cli_event_partitioning import (
    ALLOWED_PARTITION_PROJECTION_ERROR_CODES,
    PartitionProjectionError,
    default_cli_event_partition_policy,
    project_cli_event_storage_object,
)

from ._cli_event_partitioning_test_helpers import cli_event_envelope
from ._envelope_test_helpers import make_envelope

DEFAULT_POLICY = default_cli_event_partition_policy()


def _raw_cli_event_envelope(payload: dict[str, object], **overrides: object):
    base = dict(
        event_stream="cli_event",
        schema_name="community-cli-event",
        schema_version="1.0",
        policy_id="community-cli-event-policy:1.0",
        event_key="event:raw-cli-event-key",
        safe_event_reference="evt-rawclievent01",
        accepted_at="2026-08-04T00:00:00Z",
        client_type=CLI_CLIENT_NAME,
        payload=payload,
    )
    base.update(overrides)
    return build_envelope(**base)


def _valid_cli_event_payload(**overrides: object) -> dict[str, object]:
    envelope = cli_event_envelope()
    payload = dict(envelope.payload)
    payload.update(overrides)
    return payload


# --- project_cli_event_storage_object: happy path ---


def test_project_returns_storage_projection_result() -> None:
    envelope = cli_event_envelope()
    result = project_cli_event_storage_object(envelope)
    assert isinstance(result, StorageProjectionResult)


def test_project_object_key_is_the_generic_hive_path() -> None:
    envelope = cli_event_envelope()
    result = project_cli_event_storage_object(envelope)
    key = result.storage_object.object_key
    assert key.startswith(
        f"raw/stream=cli_event/schema_version=1.0/"
        f"year={envelope.accepted_year}/month={envelope.accepted_month}/"
        f"day={envelope.accepted_day}/"
    )
    assert key.endswith(".json")


def test_project_s3_metadata_has_no_extra_keys() -> None:
    envelope = cli_event_envelope()
    result = project_cli_event_storage_object(envelope)
    metadata = result.storage_object.to_s3_metadata()
    assert set(metadata) == {
        "codestrata-content-sha256",
        "codestrata-envelope-schema",
        "codestrata-source-schema",
        "codestrata-stream",
        "codestrata-object-id",
    }


def test_project_diagnostics_reflect_the_envelope() -> None:
    envelope = cli_event_envelope()
    result = project_cli_event_storage_object(envelope)
    diagnostics = result.diagnostics
    assert diagnostics.event_stream == "cli_event"
    assert diagnostics.envelope_schema_version == "1.0"
    assert diagnostics.source_schema_version == "1.0"
    assert diagnostics.client_type is None
    assert diagnostics.assessment_schema_version is None
    assert diagnostics.operation_catalog_version == "1.0"
    assert diagnostics.partition_policy_version == "1.0"
    assert diagnostics.partition_valid is True
    assert diagnostics.projection_status == "projected"


def test_project_uses_default_policies_when_none_supplied() -> None:
    envelope = cli_event_envelope()
    result = project_cli_event_storage_object(envelope)
    assert result.diagnostics.partition_policy_version == DEFAULT_POLICY.policy_version


def test_project_supports_operation_alias_normalizing_to_canonical() -> None:
    # "report.open" is a catalog alias for the canonical "open" operation —
    # the model validator canonicalizes it before storage, so submitting the
    # alias must project identically to submitting the canonical value.
    envelope = cli_event_envelope(event={
        "operation": "report.open",
        "lifecycle": "completed",
        "result": "succeeded",
        "duration_bucket": "under_1s",
    })
    result = project_cli_event_storage_object(envelope)
    assert result.diagnostics.operation_catalog_version == "1.0"


# --- project_cli_event_storage_object: failure paths ---


def test_project_rejects_non_cli_event_stream_with_stream_mismatch() -> None:
    telemetry_envelope = make_envelope()
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_cli_event_storage_object(telemetry_envelope)
    assert excinfo.value.code == "stream_mismatch"


def test_project_rejects_assessment_metadata_stream_with_stream_mismatch() -> None:
    assessment_envelope = make_envelope(
        event_stream="assessment_metadata",
        schema_name="community-assessment-metadata",
        schema_version="1.0",
        policy_id="community-assessment-metadata-policy:1.0",
        payload={"assessment": {"assessment_schema_version": "1.2"}},
    )
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_cli_event_storage_object(assessment_envelope)
    assert excinfo.value.code == "stream_mismatch"


def test_project_rejects_unsupported_envelope_schema() -> None:
    envelope = cli_event_envelope()
    policy = dataclasses.replace(
        DEFAULT_POLICY, supported_envelope_schema_versions=frozenset({"9.9"})
    )
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_cli_event_storage_object(envelope, partition_policy=policy)
    assert excinfo.value.code == "unsupported_envelope_schema"


def test_project_rejects_unsupported_source_schema() -> None:
    envelope = cli_event_envelope()
    policy = dataclasses.replace(
        DEFAULT_POLICY, supported_source_schema_versions=frozenset({"9.9"})
    )
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_cli_event_storage_object(envelope, partition_policy=policy)
    assert excinfo.value.code == "unsupported_source_schema"


def test_project_rejects_unsupported_source_policy() -> None:
    envelope = cli_event_envelope()
    policy = dataclasses.replace(
        DEFAULT_POLICY, supported_source_policy_ids=frozenset({"other-policy:9.9"})
    )
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_cli_event_storage_object(envelope, partition_policy=policy)
    assert excinfo.value.code == "unsupported_source_policy"


def test_project_rejects_payload_that_fails_typed_revalidation() -> None:
    payload = _valid_cli_event_payload()
    del payload["client"]
    envelope = _raw_cli_event_envelope(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_cli_event_storage_object(envelope)
    assert excinfo.value.code == "invalid_payload"


def test_project_rejects_corrupted_operation_as_invalid_payload() -> None:
    payload = _valid_cli_event_payload()
    event_block = dict(payload["event"])
    event_block["operation"] = "not_a_real_operation"
    payload["event"] = event_block
    envelope = _raw_cli_event_envelope(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_cli_event_storage_object(envelope)
    assert excinfo.value.code == "invalid_payload"


def test_project_rejects_command_field_as_invalid_payload() -> None:
    payload = _valid_cli_event_payload()
    context_block = dict(payload["context"])
    context_block["command"] = "codestrata assess ."
    payload["context"] = context_block
    envelope = _raw_cli_event_envelope(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_cli_event_storage_object(envelope)
    assert excinfo.value.code == "invalid_payload"


def test_project_rejects_argv_field_as_invalid_payload() -> None:
    payload = _valid_cli_event_payload()
    context_block = dict(payload["context"])
    context_block["argv"] = ["codestrata", "assess", "."]
    payload["context"] = context_block
    envelope = _raw_cli_event_envelope(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_cli_event_storage_object(envelope)
    assert excinfo.value.code == "invalid_payload"


def test_project_rejects_cwd_field_as_invalid_payload() -> None:
    payload = _valid_cli_event_payload()
    context_block = dict(payload["context"])
    context_block["cwd"] = "/home/user/project"
    payload["context"] = context_block
    envelope = _raw_cli_event_envelope(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_cli_event_storage_object(envelope)
    assert excinfo.value.code == "invalid_payload"


def test_project_rejects_missing_schema_version_as_invalid_payload() -> None:
    payload = _valid_cli_event_payload()
    del payload["schema_version"]
    envelope = _raw_cli_event_envelope(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_cli_event_storage_object(envelope)
    assert excinfo.value.code == "invalid_payload"


def test_project_rejects_envelope_client_type_not_codestrata_cli() -> None:
    payload = _valid_cli_event_payload()
    envelope = _raw_cli_event_envelope(payload, client_type="vscode_extension")
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_cli_event_storage_object(envelope)
    assert excinfo.value.code == "invalid_client_type"


def test_project_rejects_unsupported_operation_catalog() -> None:
    envelope = cli_event_envelope()
    policy = dataclasses.replace(
        DEFAULT_POLICY, supported_operation_catalog_versions=frozenset({"9.9"})
    )
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_cli_event_storage_object(envelope, partition_policy=policy)
    assert excinfo.value.code == "unsupported_operation_catalog"


def test_project_rejects_when_data_lake_policy_disallows_the_stream() -> None:
    envelope = cli_event_envelope()
    restrictive_policy = CommunityDataLakePolicy(allowed_event_streams=("assessment_metadata",))
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_cli_event_storage_object(envelope, data_lake_policy=restrictive_policy)
    assert excinfo.value.code == "storage_object_invalid"


def test_project_rejects_when_partition_key_exceeds_max_key_length() -> None:
    envelope = cli_event_envelope()
    tiny_policy = dataclasses.replace(DEFAULT_POLICY, max_key_length=64)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_cli_event_storage_object(envelope, partition_policy=tiny_policy)
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


def test_no_assessment_schema_codes_are_in_the_cli_event_allowlist() -> None:
    assert "unsupported_assessment_schema" not in ALLOWED_PARTITION_PROJECTION_ERROR_CODES
    assert "missing_assessment_schema" not in ALLOWED_PARTITION_PROJECTION_ERROR_CODES


def test_unsupported_operation_catalog_code_is_only_in_cli_event_allowlist() -> None:
    from codestrata_platform.community_cloud_api.data_lake.streams.telemetry_partitioning import (
        ALLOWED_PARTITION_PROJECTION_ERROR_CODES as TELEMETRY_CODES,
    )

    assert "unsupported_operation_catalog" in ALLOWED_PARTITION_PROJECTION_ERROR_CODES
    assert "unsupported_operation_catalog" not in TELEMETRY_CODES
