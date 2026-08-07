"""Extension event storage-object projection tests (Slice 8.7)."""

from __future__ import annotations

import dataclasses

import pytest

from codestrata_platform.community_cloud_api.data_lake.envelopes import build_envelope
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.data_lake.stream_storage import (
    StorageProjectionResult,
)
from codestrata_platform.community_cloud_api.data_lake.streams.extension_event_partitioning import (
    ALLOWED_PARTITION_PROJECTION_ERROR_CODES,
    CLIENT_TYPE_METADATA_KEY,
    PartitionProjectionError,
    default_extension_event_partition_policy,
    project_extension_event_storage_object,
)

from ._cli_event_partitioning_test_helpers import cli_event_envelope
from ._envelope_test_helpers import make_envelope
from ._extension_event_partitioning_test_helpers import (
    DEFAULT_EXTENSION_EVENT_CLOCK,
    extension_event_envelope,
)

DEFAULT_POLICY = default_extension_event_partition_policy()


def _raw_extension_event_envelope(payload: dict[str, object], **overrides: object):
    base = dict(
        event_stream="extension_event",
        schema_name="community-extension-event",
        schema_version="1.0",
        policy_id="community-extension-event-policy:1.0",
        event_key="event:raw-extension-event-key",
        safe_event_reference="evt-rawextevent01",
        accepted_at="2026-08-04T00:00:00Z",
        client_type="vscode_extension",
        payload=payload,
    )
    base.update(overrides)
    return build_envelope(**base)


def _valid_extension_event_payload(**overrides: object) -> dict[str, object]:
    envelope = extension_event_envelope()
    payload = dict(envelope.payload)
    payload.update(overrides)
    return payload


# --- project_extension_event_storage_object: happy path ---


def test_project_returns_storage_projection_result() -> None:
    envelope = extension_event_envelope()
    result = project_extension_event_storage_object(envelope)
    assert isinstance(result, StorageProjectionResult)


def test_project_object_key_is_the_generic_hive_path() -> None:
    envelope = extension_event_envelope()
    result = project_extension_event_storage_object(envelope)
    key = result.storage_object.object_key
    assert key.startswith(
        f"raw/stream=extension_event/schema_version=1.0/"
        f"year={envelope.accepted_year}/month={envelope.accepted_month}/"
        f"day={envelope.accepted_day}/"
    )
    assert key.endswith(".json")


def test_project_attaches_client_type_metadata_by_default() -> None:
    envelope = extension_event_envelope()
    result = project_extension_event_storage_object(envelope)
    metadata = result.storage_object.to_s3_metadata()
    assert metadata[CLIENT_TYPE_METADATA_KEY] == "vscode_extension"


def test_project_diagnostics_reflect_the_envelope() -> None:
    envelope = extension_event_envelope()
    result = project_extension_event_storage_object(envelope)
    diagnostics = result.diagnostics
    assert diagnostics.event_stream == "extension_event"
    assert diagnostics.envelope_schema_version == "1.0"
    assert diagnostics.source_schema_version == "1.0"
    assert diagnostics.client_type == "vscode_extension"
    assert diagnostics.assessment_schema_version is None
    assert diagnostics.operation_catalog_version == "1.0"
    assert diagnostics.partition_policy_version == "1.0"
    assert diagnostics.partition_valid is True
    assert diagnostics.projection_status == "projected"


def test_project_uses_default_policies_when_none_supplied() -> None:
    envelope = extension_event_envelope()
    result = project_extension_event_storage_object(envelope)
    assert result.diagnostics.partition_policy_version == DEFAULT_POLICY.policy_version


def test_active_projection_rejects_retired_cursor_extension_client_type() -> None:
    from codestrata_platform.community_cloud_api.data_lake.envelope_builders import (
        build_data_lake_envelope,
    )
    from codestrata_platform.community_cloud_api.data_lake.envelope_validation import (
        EnvelopeBuildError,
    )
    from codestrata_platform.community_cloud_api.data_lake.streams.extension_event_partitioning import (
        PartitionProjectionError,
        project_extension_event_storage_object,
    )
    from codestrata_platform.community_cloud_api.extension_events.models import (
        ExtensionEventRequest,
    )
    from codestrata_platform.community_cloud_api.historical_client_compatibility import (
        deserialize_historical_extension_event_payload,
        historical_client_type_metadata_is_valid,
    )

    from ..extension_event_helpers import valid_extension_event_body

    body = valid_extension_event_body()
    body["client"] = {
        "name": "cursor_extension",
        "version": "0.2.0",
        "editor": "cursor",
        "editor_version": "1.85.0",
        "platform": "darwin",
    }
    # Schema deserialize still works for historical records.
    request = deserialize_historical_extension_event_payload(body)
    assert isinstance(request, ExtensionEventRequest)
    assert historical_client_type_metadata_is_valid("cursor_extension")

    # Active envelope construction rejects retired clients.
    try:
        build_data_lake_envelope(
            event_stream="extension_event",
            request=request,
            event_key="event:ext-retired-cursor",
            safe_event_reference="evt-retiredcursor01",
            clock=DEFAULT_EXTENSION_EVENT_CLOCK,
        )
        raised = False
    except EnvelopeBuildError:
        raised = True
    assert raised

    # VS Code active projection still succeeds.
    result = project_extension_event_storage_object(extension_event_envelope())
    assert result.diagnostics.client_type == "vscode_extension"
    assert result.storage_object.to_s3_metadata()[CLIENT_TYPE_METADATA_KEY] == "vscode_extension"

    # Guard: PartitionProjectionError remains the active-path rejection type.
    assert issubclass(PartitionProjectionError, Exception)


def test_project_supports_operation_alias_normalizing_to_canonical() -> None:
    # "codestrata.openHtmlReport" is a catalog alias for the canonical
    # "open_report" operation — the model validator canonicalizes it before
    # storage, so submitting the alias must project successfully.
    envelope = extension_event_envelope(
        event={
            "operation": "codestrata.openHtmlReport",
            "lifecycle": "completed",
            "result": "succeeded",
            "duration_bucket": "under_1s",
        }
    )
    result = project_extension_event_storage_object(envelope)
    assert result.diagnostics.operation_catalog_version == "1.0"


# --- project_extension_event_storage_object: failure paths ---


def test_project_rejects_cli_event_stream_with_stream_mismatch() -> None:
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_extension_event_storage_object(cli_event_envelope())
    assert excinfo.value.code == "stream_mismatch"


def test_project_rejects_telemetry_stream_with_stream_mismatch() -> None:
    telemetry_envelope = make_envelope()
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_extension_event_storage_object(telemetry_envelope)
    assert excinfo.value.code == "stream_mismatch"


def test_project_rejects_unsupported_envelope_schema() -> None:
    envelope = extension_event_envelope()
    policy = dataclasses.replace(
        DEFAULT_POLICY, supported_envelope_schema_versions=frozenset({"9.9"})
    )
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_extension_event_storage_object(envelope, partition_policy=policy)
    assert excinfo.value.code == "unsupported_envelope_schema"


def test_project_rejects_unsupported_source_schema() -> None:
    envelope = extension_event_envelope()
    policy = dataclasses.replace(
        DEFAULT_POLICY, supported_source_schema_versions=frozenset({"9.9"})
    )
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_extension_event_storage_object(envelope, partition_policy=policy)
    assert excinfo.value.code == "unsupported_source_schema"


def test_project_rejects_unsupported_source_policy() -> None:
    envelope = extension_event_envelope()
    policy = dataclasses.replace(
        DEFAULT_POLICY, supported_source_policy_ids=frozenset({"other-policy:9.9"})
    )
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_extension_event_storage_object(envelope, partition_policy=policy)
    assert excinfo.value.code == "unsupported_source_policy"


def test_project_rejects_payload_that_fails_typed_revalidation() -> None:
    payload = _valid_extension_event_payload()
    del payload["client"]
    envelope = _raw_extension_event_envelope(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_extension_event_storage_object(envelope)
    assert excinfo.value.code == "invalid_payload"


def test_project_rejects_unknown_operation_as_invalid_payload() -> None:
    payload = _valid_extension_event_payload()
    event_block = dict(payload["event"])
    event_block["operation"] = "not_a_real_operation"
    payload["event"] = event_block
    envelope = _raw_extension_event_envelope(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_extension_event_storage_object(envelope)
    assert excinfo.value.code == "invalid_payload"


def test_project_rejects_workspace_path_in_context_as_invalid_payload() -> None:
    payload = _valid_extension_event_payload()
    context_block = dict(payload["context"])
    context_block["workspace_path"] = "/home/user/project"
    payload["context"] = context_block
    envelope = _raw_extension_event_envelope(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_extension_event_storage_object(envelope)
    assert excinfo.value.code == "invalid_payload"


def test_project_rejects_document_uri_as_invalid_payload() -> None:
    payload = _valid_extension_event_payload()
    context_block = dict(payload["context"])
    context_block["document_uri"] = "file:///home/user/project/main.py"
    payload["context"] = context_block
    envelope = _raw_extension_event_envelope(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_extension_event_storage_object(envelope)
    assert excinfo.value.code == "invalid_payload"


def test_project_rejects_client_editor_mismatch_as_invalid_payload() -> None:
    # vscode_extension must pair with editor=vscode; cursor editor fails model
    # validation before the projector's client_type allowlist check.
    payload = _valid_extension_event_payload()
    client_block = dict(payload["client"])
    client_block["editor"] = "cursor"
    payload["client"] = client_block
    envelope = _raw_extension_event_envelope(payload, client_type="vscode_extension")
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_extension_event_storage_object(envelope)
    assert excinfo.value.code == "invalid_payload"


def test_project_rejects_envelope_client_type_codestrata_cli() -> None:
    payload = _valid_extension_event_payload()
    envelope = _raw_extension_event_envelope(payload, client_type="codestrata_cli")
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_extension_event_storage_object(envelope)
    assert excinfo.value.code == "invalid_client_type"


def test_project_rejects_unsupported_operation_catalog() -> None:
    envelope = extension_event_envelope()
    policy = dataclasses.replace(
        DEFAULT_POLICY, supported_operation_catalog_versions=frozenset({"9.9"})
    )
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_extension_event_storage_object(envelope, partition_policy=policy)
    assert excinfo.value.code == "unsupported_operation_catalog"


def test_project_rejects_when_data_lake_policy_disallows_the_stream() -> None:
    envelope = extension_event_envelope()
    restrictive_policy = CommunityDataLakePolicy(allowed_event_streams=("assessment_metadata",))
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_extension_event_storage_object(envelope, data_lake_policy=restrictive_policy)
    assert excinfo.value.code == "storage_object_invalid"


def test_project_rejects_when_partition_key_exceeds_max_key_length() -> None:
    envelope = extension_event_envelope()
    tiny_policy = dataclasses.replace(DEFAULT_POLICY, max_key_length=64)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_extension_event_storage_object(envelope, partition_policy=tiny_policy)
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


def test_no_assessment_schema_codes_are_in_the_extension_event_allowlist() -> None:
    assert "unsupported_assessment_schema" not in ALLOWED_PARTITION_PROJECTION_ERROR_CODES
    assert "missing_assessment_schema" not in ALLOWED_PARTITION_PROJECTION_ERROR_CODES


def test_unsupported_operation_catalog_code_is_in_extension_event_allowlist() -> None:
    from codestrata_platform.community_cloud_api.data_lake.streams.telemetry_partitioning import (
        ALLOWED_PARTITION_PROJECTION_ERROR_CODES as TELEMETRY_CODES,
    )

    assert "unsupported_operation_catalog" in ALLOWED_PARTITION_PROJECTION_ERROR_CODES
    assert "unsupported_operation_catalog" not in TELEMETRY_CODES
