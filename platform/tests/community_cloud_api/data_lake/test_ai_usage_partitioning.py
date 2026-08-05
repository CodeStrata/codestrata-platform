"""AI usage storage-object projection tests (Slice 8.8)."""

from __future__ import annotations

import dataclasses

import pytest

from codestrata_platform.community_cloud_api.data_lake.envelopes import build_envelope
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.data_lake.stream_storage import (
    StorageProjectionResult,
)
from codestrata_platform.community_cloud_api.data_lake.streams.ai_usage_partitioning import (
    ALLOWED_PARTITION_PROJECTION_ERROR_CODES,
    CLIENT_TYPE_METADATA_KEY,
    PartitionProjectionError,
    default_ai_usage_partition_policy,
    project_ai_usage_storage_object,
)

from ._ai_usage_partitioning_test_helpers import ai_usage_envelope
from ._envelope_test_helpers import make_envelope
from ._extension_event_partitioning_test_helpers import extension_event_envelope

DEFAULT_POLICY = default_ai_usage_partition_policy()


def _raw_ai_usage_envelope(payload: dict[str, object], **overrides: object):
    base = dict(
        event_stream="ai_usage",
        schema_name="community-ai-usage",
        schema_version="1.0",
        policy_id="community-ai-usage-policy:1.0",
        event_key="event:raw-ai-usage-key",
        safe_event_reference="evt-rawaiusage001",
        accepted_at="2026-08-04T00:00:00Z",
        client_type="codestrata_cli",
        payload=payload,
    )
    base.update(overrides)
    return build_envelope(**base)


def _valid_ai_usage_payload(**overrides: object) -> dict[str, object]:
    envelope = ai_usage_envelope()
    payload = dict(envelope.payload)
    payload.update(overrides)
    return payload


def _usage_block(**overrides: object) -> dict[str, object]:
    usage = dict(_valid_ai_usage_payload()["usage"])
    usage.update(overrides)
    return usage


def _context_block(**overrides: object) -> dict[str, object]:
    context = dict(_valid_ai_usage_payload()["context"])
    context.update(overrides)
    return context


# --- project_ai_usage_storage_object: happy path ---


def test_project_returns_storage_projection_result() -> None:
    envelope = ai_usage_envelope()
    result = project_ai_usage_storage_object(envelope)
    assert isinstance(result, StorageProjectionResult)


def test_project_object_key_is_the_generic_hive_path() -> None:
    envelope = ai_usage_envelope()
    result = project_ai_usage_storage_object(envelope)
    key = result.storage_object.object_key
    assert key.startswith(
        f"raw/stream=ai_usage/schema_version=1.0/"
        f"year={envelope.accepted_year}/month={envelope.accepted_month}/"
        f"day={envelope.accepted_day}/"
    )
    assert key.endswith(".json")


def test_project_attaches_client_type_metadata_by_default() -> None:
    envelope = ai_usage_envelope()
    result = project_ai_usage_storage_object(envelope)
    metadata = result.storage_object.to_s3_metadata()
    assert metadata[CLIENT_TYPE_METADATA_KEY] == "codestrata_cli"


def test_project_diagnostics_reflect_the_envelope() -> None:
    envelope = ai_usage_envelope()
    result = project_ai_usage_storage_object(envelope)
    diagnostics = result.diagnostics
    assert diagnostics.event_stream == "ai_usage"
    assert diagnostics.envelope_schema_version == "1.0"
    assert diagnostics.source_schema_version == "1.0"
    assert diagnostics.client_type == "codestrata_cli"
    assert diagnostics.assessment_schema_version is None
    assert diagnostics.operation_catalog_version is None
    assert diagnostics.capability_catalog_version == "1.0"
    assert diagnostics.provider_catalog_version == "1.0"
    assert diagnostics.model_catalog_version == "1.0"
    assert diagnostics.partition_policy_version == "1.0"
    assert diagnostics.partition_valid is True
    assert diagnostics.projection_status == "projected"


def test_project_uses_default_policies_when_none_supplied() -> None:
    envelope = ai_usage_envelope()
    result = project_ai_usage_storage_object(envelope)
    assert result.diagnostics.partition_policy_version == DEFAULT_POLICY.policy_version


def test_project_supports_vscode_extension_client_type() -> None:
    envelope = ai_usage_envelope(
        client={
            "name": "vscode_extension",
            "version": "0.2.0",
            "platform": "darwin",
        }
    )
    result = project_ai_usage_storage_object(envelope)
    assert result.diagnostics.client_type == "vscode_extension"
    assert result.storage_object.to_s3_metadata()[CLIENT_TYPE_METADATA_KEY] == "vscode_extension"


def test_project_supports_cursor_extension_client_type() -> None:
    envelope = ai_usage_envelope(
        client={
            "name": "cursor_extension",
            "version": "0.2.0",
            "platform": "darwin",
        }
    )
    result = project_ai_usage_storage_object(envelope)
    assert result.diagnostics.client_type == "cursor_extension"
    assert result.storage_object.to_s3_metadata()[CLIENT_TYPE_METADATA_KEY] == "cursor_extension"


def test_project_supports_capability_alias_modernization_advisor() -> None:
    envelope = ai_usage_envelope(usage=_usage_block(capability="modernization-advisor"))
    result = project_ai_usage_storage_object(envelope)
    assert result.diagnostics.capability_catalog_version == "1.0"


def test_project_supports_capability_alias_ai_enrichment() -> None:
    envelope = ai_usage_envelope(usage=_usage_block(capability="ai_enrichment"))
    result = project_ai_usage_storage_object(envelope)
    assert result.diagnostics.capability_catalog_version == "1.0"


def test_project_supports_provider_alias_bedrock() -> None:
    envelope = ai_usage_envelope(
        usage=_usage_block(
            provider_family="bedrock",
            model_family="amazon_nova_family",
        )
    )
    result = project_ai_usage_storage_object(envelope)
    assert result.diagnostics.provider_catalog_version == "1.0"


def test_project_supports_model_alias_gpt() -> None:
    envelope = ai_usage_envelope(usage=_usage_block(model_family="gpt"))
    result = project_ai_usage_storage_object(envelope)
    assert result.diagnostics.model_catalog_version == "1.0"


# --- project_ai_usage_storage_object: failure paths ---


def test_project_rejects_telemetry_stream_with_stream_mismatch() -> None:
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_ai_usage_storage_object(make_envelope())
    assert excinfo.value.code == "stream_mismatch"


def test_project_rejects_extension_event_stream_with_stream_mismatch() -> None:
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_ai_usage_storage_object(extension_event_envelope())
    assert excinfo.value.code == "stream_mismatch"


def test_project_rejects_unsupported_envelope_schema() -> None:
    envelope = ai_usage_envelope()
    policy = dataclasses.replace(
        DEFAULT_POLICY, supported_envelope_schema_versions=frozenset({"9.9"})
    )
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_ai_usage_storage_object(envelope, partition_policy=policy)
    assert excinfo.value.code == "unsupported_envelope_schema"


def test_project_rejects_unsupported_source_schema() -> None:
    envelope = ai_usage_envelope()
    policy = dataclasses.replace(
        DEFAULT_POLICY, supported_source_schema_versions=frozenset({"9.9"})
    )
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_ai_usage_storage_object(envelope, partition_policy=policy)
    assert excinfo.value.code == "unsupported_source_schema"


def test_project_rejects_unsupported_source_policy() -> None:
    envelope = ai_usage_envelope()
    policy = dataclasses.replace(
        DEFAULT_POLICY, supported_source_policy_ids=frozenset({"other-policy:9.9"})
    )
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_ai_usage_storage_object(envelope, partition_policy=policy)
    assert excinfo.value.code == "unsupported_source_policy"


def test_project_rejects_unsupported_capability_catalog() -> None:
    envelope = ai_usage_envelope()
    policy = dataclasses.replace(
        DEFAULT_POLICY, supported_capability_catalog_versions=frozenset({"9.9"})
    )
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_ai_usage_storage_object(envelope, partition_policy=policy)
    assert excinfo.value.code == "unsupported_capability_catalog"


def test_project_rejects_unsupported_provider_catalog() -> None:
    envelope = ai_usage_envelope()
    policy = dataclasses.replace(
        DEFAULT_POLICY, supported_provider_catalog_versions=frozenset({"9.9"})
    )
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_ai_usage_storage_object(envelope, partition_policy=policy)
    assert excinfo.value.code == "unsupported_provider_catalog"


def test_project_rejects_unsupported_model_catalog() -> None:
    envelope = ai_usage_envelope()
    policy = dataclasses.replace(
        DEFAULT_POLICY, supported_model_catalog_versions=frozenset({"9.9"})
    )
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_ai_usage_storage_object(envelope, partition_policy=policy)
    assert excinfo.value.code == "unsupported_model_catalog"


def test_project_rejects_payload_that_fails_typed_revalidation() -> None:
    payload = _valid_ai_usage_payload()
    del payload["client"]
    envelope = _raw_ai_usage_envelope(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_ai_usage_storage_object(envelope)
    assert excinfo.value.code == "invalid_payload"


def test_project_rejects_unknown_capability_as_invalid_payload() -> None:
    payload = _valid_ai_usage_payload(usage=_usage_block(capability="not_a_real_capability"))
    envelope = _raw_ai_usage_envelope(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_ai_usage_storage_object(envelope)
    assert excinfo.value.code == "invalid_payload"


def _envelope_with_poisoned_payload(payload: dict[str, object]):
    # ``prompt`` / ``response`` are forbidden envelope key names, so
    # ``build_envelope`` rejects them before the projector runs. Bypass the
    # privacy scan with ``dataclasses.replace`` so the projector's typed
    # re-check still surfaces ``invalid_payload``.
    return dataclasses.replace(ai_usage_envelope(), payload=payload)


def test_project_rejects_prompt_at_top_level_as_invalid_payload() -> None:
    payload = _valid_ai_usage_payload()
    payload["prompt"] = "Explain this repository"
    envelope = _envelope_with_poisoned_payload(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_ai_usage_storage_object(envelope)
    assert excinfo.value.code == "invalid_payload"


def test_project_rejects_prompt_in_usage_as_invalid_payload() -> None:
    payload = _valid_ai_usage_payload(usage=_usage_block(prompt="Reveal the secret plan"))
    envelope = _envelope_with_poisoned_payload(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_ai_usage_storage_object(envelope)
    assert excinfo.value.code == "invalid_payload"


def test_project_rejects_prompt_in_context_as_invalid_payload() -> None:
    payload = _valid_ai_usage_payload(context=_context_block(prompt="Reveal the secret plan"))
    envelope = _envelope_with_poisoned_payload(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_ai_usage_storage_object(envelope)
    assert excinfo.value.code == "invalid_payload"


def test_project_rejects_response_as_invalid_payload() -> None:
    payload = _valid_ai_usage_payload()
    payload["response"] = "Here is the analysis"
    envelope = _envelope_with_poisoned_payload(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_ai_usage_storage_object(envelope)
    assert excinfo.value.code == "invalid_payload"


def test_project_rejects_exact_cost_as_invalid_payload() -> None:
    payload = _valid_ai_usage_payload(usage=_usage_block(cost=0.02))
    envelope = _raw_ai_usage_envelope(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_ai_usage_storage_object(envelope)
    assert excinfo.value.code == "invalid_payload"


def test_project_rejects_raw_model_id_as_invalid_payload() -> None:
    payload = _valid_ai_usage_payload(usage=_usage_block(model_id="gpt-4o-mini"))
    envelope = _raw_ai_usage_envelope(payload)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_ai_usage_storage_object(envelope)
    assert excinfo.value.code == "invalid_payload"


def test_project_rejects_envelope_client_type_other_extension() -> None:
    payload = _valid_ai_usage_payload()
    envelope = _raw_ai_usage_envelope(payload, client_type="other_extension")
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_ai_usage_storage_object(envelope)
    assert excinfo.value.code == "invalid_client_type"


def test_project_rejects_when_data_lake_policy_disallows_the_stream() -> None:
    envelope = ai_usage_envelope()
    restrictive_policy = CommunityDataLakePolicy(allowed_event_streams=("assessment_metadata",))
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_ai_usage_storage_object(envelope, data_lake_policy=restrictive_policy)
    assert excinfo.value.code == "storage_object_invalid"


def test_project_rejects_when_partition_key_exceeds_max_key_length() -> None:
    envelope = ai_usage_envelope()
    tiny_policy = dataclasses.replace(DEFAULT_POLICY, max_key_length=64)
    with pytest.raises(PartitionProjectionError) as excinfo:
        project_ai_usage_storage_object(envelope, partition_policy=tiny_policy)
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


def test_no_assessment_or_operation_catalog_codes_are_in_the_ai_usage_allowlist() -> None:
    assert "unsupported_assessment_schema" not in ALLOWED_PARTITION_PROJECTION_ERROR_CODES
    assert "missing_assessment_schema" not in ALLOWED_PARTITION_PROJECTION_ERROR_CODES
    assert "unsupported_operation_catalog" not in ALLOWED_PARTITION_PROJECTION_ERROR_CODES


def test_ai_catalog_error_codes_are_in_the_ai_usage_allowlist() -> None:
    from codestrata_platform.community_cloud_api.data_lake.streams.extension_event_partitioning import (
        ALLOWED_PARTITION_PROJECTION_ERROR_CODES as EXTENSION_CODES,
    )

    for code in (
        "unsupported_capability_catalog",
        "unsupported_provider_catalog",
        "unsupported_model_catalog",
    ):
        assert code in ALLOWED_PARTITION_PROJECTION_ERROR_CODES
        assert code not in EXTENSION_CODES
