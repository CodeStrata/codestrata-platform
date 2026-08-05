"""AI usage partition/diagnostics privacy boundary tests (Slice 8.8)."""

from __future__ import annotations

import json

from codestrata_platform.community_cloud_api.data_lake.streams.ai_usage_partitioning import (
    project_ai_usage_storage_object,
)

from ._ai_usage_partitioning_test_helpers import ai_usage_envelope

_ALLOWED_DIAGNOSTICS_KEYS = frozenset(
    {
        "capability_catalog_version",
        "client_type",
        "envelope_schema_version",
        "event_stream",
        "limitations",
        "model_catalog_version",
        "partition_policy_version",
        "partition_valid",
        "projection_status",
        "provider_catalog_version",
        "safe_event_reference",
        "safe_object_reference",
        "source_schema_version",
    }
)

# Values that must never appear anywhere in the object key or diagnostics
# for a default AI usage submission. ``codestrata_cli`` is deliberately
# excluded here — it IS an approved S3-metadata / diagnostics value
# (Option B). Catalog version ``1.0`` is likewise fine. Do not assert
# those absent from metadata/diagnostics.
_SENSITIVE_VALUE_FRAGMENTS = (
    "ai-usage-0001",  # event_id
    "modernization_advisor",  # capability
    "openai",  # provider_family
    "gpt_family",  # model_family
)


def _result(**overrides: object):
    return project_ai_usage_storage_object(ai_usage_envelope(**overrides))


def test_object_key_carries_no_forbidden_field_values() -> None:
    key = _result().storage_object.object_key
    for fragment in _SENSITIVE_VALUE_FRAGMENTS:
        assert fragment not in key
    assert "codestrata_cli" not in key
    assert "vscode_extension" not in key
    assert "cursor_extension" not in key


def test_object_key_carries_only_the_generic_dimension_names() -> None:
    key = _result().storage_object.object_key
    segments = key.split("/")
    hive_segments = segments[1:-1]
    names = [segment.split("=", 1)[0] for segment in hive_segments]
    assert names == ["stream", "schema_version", "year", "month", "day"]


def test_s3_metadata_has_client_type_only_as_extra() -> None:
    metadata = _result().storage_object.to_s3_metadata()
    base_keys = {
        "codestrata-content-sha256",
        "codestrata-envelope-schema",
        "codestrata-source-schema",
        "codestrata-stream",
        "codestrata-object-id",
    }
    assert set(metadata) == base_keys | {"codestrata-client-type"}
    assert metadata["codestrata-client-type"] == "codestrata_cli"


def test_s3_metadata_has_no_capability_provider_model_or_identity_keys() -> None:
    metadata = _result().storage_object.to_s3_metadata()
    for forbidden_key in (
        "codestrata-capability",
        "codestrata-provider-family",
        "codestrata-model-family",
        "codestrata-outcome",
        "codestrata-installation-id",
        "codestrata-event-id",
        "installation_id",
        "event_id",
        "capability",
        "provider_family",
        "model_family",
        "outcome",
    ):
        assert forbidden_key not in metadata


def test_s3_metadata_has_no_forbidden_field_values() -> None:
    metadata = _result().storage_object.to_s3_metadata()
    blob = " ".join(metadata.values()).lower()
    for fragment in _SENSITIVE_VALUE_FRAGMENTS:
        assert fragment.lower() not in blob


def test_s3_metadata_has_no_event_key_or_safe_reference() -> None:
    metadata = _result().storage_object.to_s3_metadata()
    blob = " ".join(metadata.values())
    assert "event:" not in blob
    assert "evt-" not in blob


def test_s3_metadata_excludes_installation_id_and_event_id() -> None:
    metadata = _result(installation_id="install-abcdef12").storage_object.to_s3_metadata()
    assert "installation_id" not in metadata
    assert "event_id" not in metadata
    blob = " ".join(metadata.values())
    assert "install-abcdef12" not in blob


def test_diagnostics_only_exposes_allowlisted_keys() -> None:
    diagnostics = _result().diagnostics.to_stable_dict()
    assert set(diagnostics) <= _ALLOWED_DIAGNOSTICS_KEYS


def test_diagnostics_includes_client_type_and_three_catalog_versions() -> None:
    diagnostics = _result().diagnostics.to_stable_dict()
    assert diagnostics["client_type"] == "codestrata_cli"
    assert diagnostics["capability_catalog_version"] == "1.0"
    assert diagnostics["provider_catalog_version"] == "1.0"
    assert diagnostics["model_catalog_version"] == "1.0"
    assert "operation_catalog_version" not in diagnostics
    assert "assessment_schema_version" not in diagnostics
    assert "capability" not in diagnostics
    assert "provider_family" not in diagnostics


def test_diagnostics_never_contains_forbidden_field_values() -> None:
    diagnostics = _result().diagnostics.to_stable_dict()
    blob = json.dumps(diagnostics).lower()
    for fragment in _SENSITIVE_VALUE_FRAGMENTS:
        assert fragment.lower() not in blob


def test_diagnostics_never_contains_event_id_or_installation_id_keys() -> None:
    diagnostics = _result().diagnostics.to_stable_dict()
    assert "event_id" not in diagnostics
    assert "installation_id" not in diagnostics


def test_diagnostics_never_contains_capability_provider_model_or_outcome() -> None:
    diagnostics = _result().diagnostics.to_stable_dict()
    assert "capability" not in diagnostics
    assert "provider_family" not in diagnostics
    assert "model_family" not in diagnostics
    assert "outcome" not in diagnostics
    assert "failure_category" not in diagnostics


def test_diagnostics_never_contains_object_key_bucket_or_digest() -> None:
    diagnostics = _result().diagnostics.to_stable_dict()
    for forbidden_key in ("object_key", "bucket", "content_sha256", "digest", "payload"):
        assert forbidden_key not in diagnostics


def test_diagnostics_never_contains_prompt_response_or_cost_fields() -> None:
    diagnostics = _result().diagnostics.to_stable_dict()
    for forbidden_key in (
        "prompt",
        "response",
        "cost",
        "model_id",
        "api_key",
        "token_count",
    ):
        assert forbidden_key not in diagnostics


def test_diagnostics_safe_event_reference_is_opaque() -> None:
    diagnostics = _result().diagnostics
    assert diagnostics.safe_event_reference.startswith("evt-")
    assert "event:" not in diagnostics.safe_event_reference


def test_diagnostics_safe_object_reference_is_opaque() -> None:
    diagnostics = _result().diagnostics
    assert diagnostics.safe_object_reference.startswith("lake-ref:")
    assert "lake-object:" not in diagnostics.safe_object_reference


def test_storage_projection_result_to_stable_dict_excludes_object_key_and_bytes() -> None:
    blob = _result().to_stable_dict()
    assert "object_key" not in blob
    assert "canonical_json_bytes" not in blob
    assert set(blob) == {"diagnostics"}
