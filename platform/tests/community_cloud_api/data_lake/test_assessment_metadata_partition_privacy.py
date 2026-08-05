"""Assessment metadata partition/diagnostics privacy boundary tests (Slice 8.4)."""

from __future__ import annotations

import json

from codestrata_platform.community_cloud_api.data_lake.streams.assessment_metadata_partitioning import (
    project_assessment_metadata_storage_object,
)

from ._assessment_partitioning_test_helpers import assessment_envelope

_ALLOWED_DIAGNOSTICS_KEYS = frozenset(
    {
        "assessment_schema_version",
        "envelope_schema_version",
        "event_stream",
        "limitations",
        "partition_policy_version",
        "partition_valid",
        "projection_status",
        "safe_event_reference",
        "safe_object_reference",
        "source_schema_version",
    }
)

# Values that must never appear anywhere in the object key, S3 metadata, or
# diagnostics for a default assessment metadata submission.
_SENSITIVE_VALUE_FRAGMENTS = (
    "amd-test-0001",  # event_id
    "codestrata_cli",  # client_type
    "python",  # primary_language
    "technology_inventory",  # executed_heads member
    "application",  # repository_shape
    "completed",  # assessment_status
    "succeeded",  # execution.result
)


def _result():
    return project_assessment_metadata_storage_object(assessment_envelope())


def test_object_key_carries_no_forbidden_field_values() -> None:
    key = _result().storage_object.object_key
    for fragment in _SENSITIVE_VALUE_FRAGMENTS:
        assert fragment not in key


def test_object_key_carries_only_the_generic_dimension_names() -> None:
    key = _result().storage_object.object_key
    segments = key.split("/")
    hive_segments = segments[1:-1]
    names = [segment.split("=", 1)[0] for segment in hive_segments]
    assert names == ["stream", "schema_version", "year", "month", "day"]


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


def test_diagnostics_never_contains_object_key_bucket_or_digest() -> None:
    diagnostics = _result().diagnostics.to_stable_dict()
    for forbidden_key in ("object_key", "bucket", "content_sha256", "digest", "payload"):
        assert forbidden_key not in diagnostics


def test_diagnostics_never_contains_counts_heads_or_language() -> None:
    diagnostics = _result().diagnostics.to_stable_dict()
    for forbidden_key in (
        "finding_count",
        "recommendation_count",
        "executed_heads",
        "primary_language",
        "repository_shape",
        "language",
        "heads",
        "shape",
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
