"""Slice 8.4 boundary tests: wiring isolation + low-level partition-vs-policy checks."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from codestrata_platform.community_cloud_api.data_lake.stream_partitions import (
    StreamPartitionError,
    assert_partition_bounds,
    assert_partition_dimensions_allowed,
    assert_partition_key_matches_policy,
    assert_s3_metadata_matches_policy,
    parse_hive_dimensions,
)
from codestrata_platform.community_cloud_api.data_lake.streams.assessment_metadata_partitioning import (
    default_assessment_metadata_partition_policy,
)

from ._assessment_partitioning_test_helpers import assessment_envelope

REPO_ROOT = Path(__file__).resolve().parents[4]
PLATFORM_SRC = REPO_ROOT / "platform" / "src" / "codestrata_platform"
COMMUNITY_CLOUD_API_PKG = PLATFORM_SRC / "community_cloud_api"
DATA_LAKE_PKG = COMMUNITY_CLOUD_API_PKG / "data_lake"
INFRASTRUCTURE_PKG = DATA_LAKE_PKG / "infrastructure"

POLICY = default_assessment_metadata_partition_policy()


def _envelope():
    return assessment_envelope(event_key="event:boundary-key")


def _valid_key(envelope) -> str:
    return (
        f"raw/stream=assessment_metadata/schema_version=1.0/"
        f"year={envelope.accepted_year}/month={envelope.accepted_month}/"
        f"day={envelope.accepted_day}/000000000000000000000000.json"
    )


# --- wiring isolation ---


def test_new_slice_8_4_modules_exist_under_data_lake_only() -> None:
    assert (DATA_LAKE_PKG / "partition_policies.py").is_file()
    assert (DATA_LAKE_PKG / "stream_partitions.py").is_file()
    assert (DATA_LAKE_PKG / "partition_diagnostics.py").is_file()
    assert (DATA_LAKE_PKG / "stream_storage.py").is_file()
    assert (DATA_LAKE_PKG / "streams" / "assessment_metadata_partitioning.py").is_file()


def test_new_slice_8_4_domain_modules_have_no_boto3_import() -> None:
    modules = (
        DATA_LAKE_PKG / "partition_policies.py",
        DATA_LAKE_PKG / "stream_partitions.py",
        DATA_LAKE_PKG / "partition_diagnostics.py",
        DATA_LAKE_PKG / "stream_storage.py",
        DATA_LAKE_PKG / "streams" / "assessment_metadata_partitioning.py",
    )
    for path in modules:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "boto3" not in node.module, f"{path}: {node.module}"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "boto3" not in alias.name, f"{path}: {alias.name}"


def test_production_wiring_files_have_no_reference_to_new_slice_8_4_symbols() -> None:
    targets = (
        COMMUNITY_CLOUD_API_PKG / "app.py",
        COMMUNITY_CLOUD_API_PKG / "registry.py",
        COMMUNITY_CLOUD_API_PKG / "deployment" / "wiring.py",
        COMMUNITY_CLOUD_API_PKG / "deployment" / "settings.py",
    )
    forbidden_tokens = (
        "assessment_metadata_partitioning",
        "StreamPartitionPolicy",
        "project_assessment_metadata_storage_object",
        "PartitionProjectionDiagnostics",
    )
    offenders: list[str] = []
    for target in targets:
        text = target.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            if token in text:
                offenders.append(f"{target.relative_to(REPO_ROOT)}:{token}")
    assert offenders == []


def test_s3_store_still_exposes_no_forbidden_adapter_methods() -> None:
    from codestrata_platform.community_cloud_api.data_lake.infrastructure.s3_store import (
        CommunityDataLakeS3Store,
    )

    for forbidden in ("delete_object", "delete", "update", "list_objects", "list", "copy_object"):
        assert not hasattr(CommunityDataLakeS3Store, forbidden)
    assert hasattr(CommunityDataLakeS3Store, "put_immutable_event")
    assert hasattr(CommunityDataLakeS3Store, "put_immutable_storage_object")
    assert hasattr(CommunityDataLakeS3Store, "quarantine_event")


# --- parse_hive_dimensions ---


def test_parse_hive_dimensions_happy_path() -> None:
    dims = parse_hive_dimensions(
        "raw/stream=assessment_metadata/schema_version=1.0/year=2026/month=08/day=04/x.json"
    )
    assert dims == {
        "stream": "assessment_metadata",
        "schema_version": "1.0",
        "year": "2026",
        "month": "08",
        "day": "04",
    }


def test_parse_hive_dimensions_rejects_too_few_segments() -> None:
    with pytest.raises(StreamPartitionError):
        parse_hive_dimensions("raw/x.json")


def test_parse_hive_dimensions_rejects_segment_without_equals() -> None:
    with pytest.raises(StreamPartitionError):
        parse_hive_dimensions("raw/stream=assessment_metadata/notakeyvalue/x.json")


def test_parse_hive_dimensions_rejects_blank_key() -> None:
    with pytest.raises(StreamPartitionError):
        parse_hive_dimensions("raw/=value/x.json")


def test_parse_hive_dimensions_rejects_blank_value() -> None:
    with pytest.raises(StreamPartitionError):
        parse_hive_dimensions("raw/stream=/x.json")


def test_parse_hive_dimensions_rejects_duplicate_dimension_name() -> None:
    with pytest.raises(StreamPartitionError):
        parse_hive_dimensions("raw/stream=a/stream=b/x.json")


# --- assert_partition_bounds ---


def test_assert_partition_bounds_passes_for_generic_key() -> None:
    envelope = _envelope()
    assert_partition_bounds(_valid_key(envelope), POLICY)


def test_assert_partition_bounds_rejects_key_over_max_length() -> None:
    import dataclasses

    tiny_policy = dataclasses.replace(POLICY, max_key_length=64)
    envelope = _envelope()
    with pytest.raises(StreamPartitionError):
        assert_partition_bounds(_valid_key(envelope), tiny_policy)


def test_assert_partition_bounds_rejects_too_many_dimensions() -> None:
    import dataclasses

    # A policy's own max_partition_depth can never be built below
    # len(required_path_dimensions) == 5 (StreamPartitionPolicy.validate()
    # enforces that), so to exercise the "too many dimensions" branch we
    # keep max_partition_depth at its minimum valid value (5) and instead
    # hand-craft a six-dimension key.
    shallow_policy = dataclasses.replace(POLICY, max_partition_depth=5)
    envelope = _envelope()
    six_dimension_key = (
        f"raw/stream=assessment_metadata/schema_version=1.0/year={envelope.accepted_year}/"
        f"month={envelope.accepted_month}/day={envelope.accepted_day}/extra=1/x.json"
    )
    with pytest.raises(StreamPartitionError):
        assert_partition_bounds(six_dimension_key, shallow_policy)


# --- assert_partition_dimensions_allowed ---


def test_assert_partition_dimensions_allowed_rejects_unlisted_extra_dimension() -> None:
    key = (
        "raw/stream=assessment_metadata/schema_version=1.0/year=2026/month=08/day=04/"
        "language=python/x.json"
    )
    with pytest.raises(StreamPartitionError):
        assert_partition_dimensions_allowed(key, POLICY)


def test_assert_partition_dimensions_allowed_rejects_forbidden_dimension() -> None:
    import dataclasses

    policy = dataclasses.replace(
        POLICY,
        optional_path_dimensions=(),
        forbidden_partition_fields=frozenset({"extra"}),
    )
    key = (
        "raw/stream=assessment_metadata/schema_version=1.0/year=2026/month=08/day=04/"
        "extra=1/x.json"
    )
    # "extra" is neither required nor optional, so this is rejected as
    # unlisted before the forbidden-field check is ever reached — proving
    # both layers of defense independently reject it.
    with pytest.raises(StreamPartitionError):
        assert_partition_dimensions_allowed(key, policy)


def test_assert_partition_dimensions_allowed_rejects_missing_required_dimension() -> None:
    key = "raw/stream=assessment_metadata/schema_version=1.0/year=2026/month=08/x.json"
    with pytest.raises(StreamPartitionError):
        assert_partition_dimensions_allowed(key, POLICY)


# --- assert_partition_key_matches_policy ---


def test_assert_partition_key_matches_policy_happy_path() -> None:
    envelope = _envelope()
    key = _valid_key(envelope)
    dims = assert_partition_key_matches_policy(key, POLICY, envelope)
    assert dims["stream"] == "assessment_metadata"


def test_assert_partition_key_matches_policy_rejects_quarantine_prefix() -> None:
    envelope = _envelope()
    key = (
        f"quarantine/reason=unsafe_payload/year={envelope.accepted_year}/"
        f"month={envelope.accepted_month}/day={envelope.accepted_day}/x.json"
    )
    with pytest.raises(StreamPartitionError):
        assert_partition_key_matches_policy(key, POLICY, envelope)


def test_assert_partition_key_matches_policy_rejects_stream_mismatch() -> None:
    envelope = _envelope()
    key = (
        f"raw/stream=telemetry/schema_version=1.0/year={envelope.accepted_year}/"
        f"month={envelope.accepted_month}/day={envelope.accepted_day}/x.json"
    )
    with pytest.raises(StreamPartitionError):
        assert_partition_key_matches_policy(key, POLICY, envelope)


def test_assert_partition_key_matches_policy_rejects_schema_version_mismatch() -> None:
    envelope = _envelope()
    key = (
        f"raw/stream=assessment_metadata/schema_version=9.9/year={envelope.accepted_year}/"
        f"month={envelope.accepted_month}/day={envelope.accepted_day}/x.json"
    )
    with pytest.raises(StreamPartitionError):
        assert_partition_key_matches_policy(key, POLICY, envelope)


def test_assert_partition_key_matches_policy_rejects_date_mismatch() -> None:
    envelope = _envelope()
    key = "raw/stream=assessment_metadata/schema_version=1.0/year=2020/month=01/day=01/x.json"
    with pytest.raises(StreamPartitionError):
        assert_partition_key_matches_policy(key, POLICY, envelope)


def test_assert_partition_key_matches_policy_rejects_malformed_date_component() -> None:
    envelope = _envelope()
    key = "raw/stream=assessment_metadata/schema_version=1.0/year=abcd/month=08/day=04/x.json"
    with pytest.raises(StreamPartitionError):
        assert_partition_key_matches_policy(key, POLICY, envelope)


def test_assert_partition_key_matches_policy_rejects_extra_dimension_beyond_generic_set() -> None:
    envelope = _envelope()
    key = (
        f"raw/stream=assessment_metadata/schema_version=1.0/year={envelope.accepted_year}/"
        f"month={envelope.accepted_month}/day={envelope.accepted_day}/"
        f"client_type=codestrata_cli/x.json"
    )
    with pytest.raises(StreamPartitionError):
        assert_partition_key_matches_policy(key, POLICY, envelope)


def test_assert_partition_key_matches_policy_rejects_identity_material_in_key() -> None:
    envelope = _envelope()
    key = (
        f"raw/stream=assessment_metadata/schema_version=1.0/year={envelope.accepted_year}/"
        f"month={envelope.accepted_month}/day={envelope.accepted_day}/installation-abc/x.json"
    )
    with pytest.raises(StreamPartitionError):
        assert_partition_key_matches_policy(key, POLICY, envelope)


# --- assert_s3_metadata_matches_policy ---


def test_assert_s3_metadata_matches_policy_accepts_allowlisted_keys() -> None:
    assert_s3_metadata_matches_policy(
        {"codestrata-stream": "assessment_metadata", "codestrata-assessment-schema": "1.2"},
        POLICY,
    )


def test_assert_s3_metadata_matches_policy_rejects_unlisted_key() -> None:
    with pytest.raises(StreamPartitionError):
        assert_s3_metadata_matches_policy({"codestrata-not-allowlisted": "x"}, POLICY)
