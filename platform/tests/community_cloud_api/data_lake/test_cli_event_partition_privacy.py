"""CLI event partition/diagnostics privacy boundary tests (Slice 8.6)."""

from __future__ import annotations

import json

from codestrata_platform.community_cloud_api.data_lake.streams.cli_event_partitioning import (
    project_cli_event_storage_object,
)

from ._cli_event_partitioning_test_helpers import cli_event_envelope

_ALLOWED_DIAGNOSTICS_KEYS = frozenset(
    {
        "envelope_schema_version",
        "event_stream",
        "limitations",
        "operation_catalog_version",
        "partition_policy_version",
        "partition_valid",
        "projection_status",
        "safe_event_reference",
        "safe_object_reference",
        "source_schema_version",
    }
)

# Values that must never appear anywhere in the object key or diagnostics
# for a default CLI event submission.
_SENSITIVE_VALUE_FRAGMENTS = (
    "cli-evt-0001",  # event_id
    "assess",  # operation
    "completed",  # lifecycle
    "succeeded",  # result
)


def _result(**overrides: object):
    return project_cli_event_storage_object(cli_event_envelope(**overrides))


def test_object_key_carries_no_forbidden_field_values() -> None:
    key = _result().storage_object.object_key
    for fragment in _SENSITIVE_VALUE_FRAGMENTS:
        assert fragment not in key
    assert "codestrata_cli" not in key


def test_object_key_carries_only_the_generic_dimension_names() -> None:
    key = _result().storage_object.object_key
    segments = key.split("/")
    hive_segments = segments[1:-1]
    names = [segment.split("=", 1)[0] for segment in hive_segments]
    assert names == ["stream", "schema_version", "year", "month", "day"]


def test_s3_metadata_has_only_the_five_base_keys() -> None:
    metadata = _result().storage_object.to_s3_metadata()
    base_keys = {
        "codestrata-content-sha256",
        "codestrata-envelope-schema",
        "codestrata-source-schema",
        "codestrata-stream",
        "codestrata-object-id",
    }
    assert set(metadata) == base_keys


def test_s3_metadata_has_no_client_type_key() -> None:
    metadata = _result().storage_object.to_s3_metadata()
    assert "codestrata-client-type" not in metadata


def test_s3_metadata_has_no_operation_or_lifecycle_key() -> None:
    metadata = _result().storage_object.to_s3_metadata()
    for forbidden_key in (
        "codestrata-cli-operation",
        "codestrata-operation",
        "codestrata-cli-lifecycle",
        "codestrata-lifecycle",
        "codestrata-cli-result",
        "codestrata-result",
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


def test_diagnostics_never_contains_forbidden_field_values() -> None:
    diagnostics = _result().diagnostics.to_stable_dict()
    blob = json.dumps(diagnostics).lower()
    for fragment in _SENSITIVE_VALUE_FRAGMENTS:
        assert fragment.lower() not in blob


def test_diagnostics_never_contains_event_id_or_installation_id_keys() -> None:
    diagnostics = _result().diagnostics.to_stable_dict()
    assert "event_id" not in diagnostics
    assert "installation_id" not in diagnostics


def test_diagnostics_never_contains_operation_lifecycle_or_result() -> None:
    diagnostics = _result().diagnostics.to_stable_dict()
    assert "operation" not in diagnostics
    assert "lifecycle" not in diagnostics
    assert "result" not in diagnostics
    assert "failure_category" not in diagnostics


def test_diagnostics_never_contains_client_type() -> None:
    diagnostics = _result().diagnostics.to_stable_dict()
    assert "client_type" not in diagnostics


def test_diagnostics_never_contains_object_key_bucket_or_digest() -> None:
    diagnostics = _result().diagnostics.to_stable_dict()
    for forbidden_key in ("object_key", "bucket", "content_sha256", "digest", "payload"):
        assert forbidden_key not in diagnostics


def test_diagnostics_never_contains_duration_bucket_or_invocation_source() -> None:
    diagnostics = _result().diagnostics.to_stable_dict()
    for forbidden_key in ("duration_bucket", "invocation_source", "terminal_environment"):
        assert forbidden_key not in diagnostics


def test_diagnostics_operation_catalog_version_is_the_only_new_field() -> None:
    diagnostics = _result().diagnostics.to_stable_dict()
    assert diagnostics["operation_catalog_version"] == "1.0"
    assert "assessment_schema_version" not in diagnostics


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
