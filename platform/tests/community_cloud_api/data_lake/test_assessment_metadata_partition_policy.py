"""Assessment metadata partition policy tests (Slice 8.4)."""

from __future__ import annotations

import dataclasses

import pytest

from codestrata_platform.community_cloud_api.assessment_metadata.policy import (
    ALLOWED_ASSESSMENT_SCHEMA_VERSIONS,
)
from codestrata_platform.community_cloud_api.data_lake.enums import EventStream
from codestrata_platform.community_cloud_api.data_lake.partition_policies import (
    GENERIC_REQUIRED_PATH_DIMENSIONS,
    PartitionPolicyError,
    StreamPartitionPolicy,
)
from codestrata_platform.community_cloud_api.data_lake.streams.assessment_metadata_partitioning import (
    ASSESSMENT_METADATA_PARTITION_POLICY_ID,
    ASSESSMENT_METADATA_PARTITION_POLICY_URN,
    ASSESSMENT_METADATA_PARTITION_POLICY_VERSION,
    ASSESSMENT_SCHEMA_METADATA_KEY,
    default_assessment_metadata_partition_policy,
)

_BASE_KWARGS: dict[str, object] = dict(
    policy_id="test-partition-policy",
    policy_version="1.0",
    event_stream=EventStream.TELEMETRY,
    supported_envelope_schema_versions=frozenset({"1.0"}),
    supported_source_schema_versions=frozenset({"1.0"}),
    supported_source_policy_ids=frozenset({"some-policy:1.0"}),
    s3_metadata_allowlist=frozenset({"codestrata-stream"}),
)


def _policy(**overrides: object) -> StreamPartitionPolicy:
    kwargs = dict(_BASE_KWARGS)
    kwargs.update(overrides)
    return StreamPartitionPolicy(**kwargs)  # type: ignore[arg-type]


# --- generic StreamPartitionPolicy construction/validation ---


def test_policy_token_combines_id_and_version() -> None:
    policy = _policy()
    assert policy.policy_token == "test-partition-policy:1.0"


def test_default_required_path_dimensions_is_generic_five() -> None:
    policy = _policy()
    assert policy.required_path_dimensions == GENERIC_REQUIRED_PATH_DIMENSIONS
    assert policy.required_path_dimensions == ("stream", "schema_version", "year", "month", "day")


def test_default_optional_path_dimensions_is_empty() -> None:
    assert _policy().optional_path_dimensions == ()


def test_frozensets_are_normalized_from_arbitrary_iterables() -> None:
    policy = _policy(supported_envelope_schema_versions=["1.0", "1.0"])
    assert policy.supported_envelope_schema_versions == frozenset({"1.0"})


def test_limitations_are_sorted_and_deduplicated() -> None:
    policy = _policy(limitations=("b", "a", "a"))
    assert policy.limitations == ("a", "b")


def test_to_stable_dict_is_sorted_and_bounded() -> None:
    policy = _policy()
    blob = policy.to_stable_dict()
    assert list(blob) == sorted(blob)
    assert blob["policy_token"] == policy.policy_token
    assert blob["event_stream"] == "telemetry"


def test_rejects_blank_policy_id() -> None:
    with pytest.raises(PartitionPolicyError):
        _policy(policy_id="")


def test_rejects_blank_policy_version() -> None:
    with pytest.raises(PartitionPolicyError):
        _policy(policy_version="")


def test_rejects_non_event_stream_member() -> None:
    with pytest.raises(PartitionPolicyError):
        _policy(event_stream="telemetry")  # type: ignore[arg-type]


def test_rejects_empty_supported_envelope_schema_versions() -> None:
    with pytest.raises(PartitionPolicyError):
        _policy(supported_envelope_schema_versions=frozenset())


def test_rejects_empty_supported_source_schema_versions() -> None:
    with pytest.raises(PartitionPolicyError):
        _policy(supported_source_schema_versions=frozenset())


def test_rejects_empty_supported_source_policy_ids() -> None:
    with pytest.raises(PartitionPolicyError):
        _policy(supported_source_policy_ids=frozenset())


def test_rejects_source_policy_id_missing_urn_colon() -> None:
    with pytest.raises(PartitionPolicyError):
        _policy(supported_source_policy_ids=frozenset({"not-a-urn"}))


def test_rejects_required_path_dimensions_not_matching_generic_set() -> None:
    with pytest.raises(PartitionPolicyError):
        _policy(required_path_dimensions=("stream", "schema_version", "year", "month"))


def test_rejects_required_path_dimensions_reordered() -> None:
    with pytest.raises(PartitionPolicyError):
        _policy(required_path_dimensions=("schema_version", "stream", "year", "month", "day"))


def test_rejects_nonempty_optional_path_dimensions_in_slice_8_4() -> None:
    with pytest.raises(PartitionPolicyError):
        _policy(optional_path_dimensions=("language",))


def test_rejects_max_partition_depth_smaller_than_required_dimensions() -> None:
    with pytest.raises(PartitionPolicyError):
        _policy(max_partition_depth=2)


def test_rejects_max_key_length_below_minimum_bound() -> None:
    with pytest.raises(PartitionPolicyError):
        _policy(max_key_length=10)


def test_rejects_max_key_length_above_maximum_bound() -> None:
    with pytest.raises(PartitionPolicyError):
        _policy(max_key_length=10_000)


def test_rejects_empty_s3_metadata_allowlist() -> None:
    with pytest.raises(PartitionPolicyError):
        _policy(s3_metadata_allowlist=frozenset())


def test_rejects_forbidden_partition_field_overlapping_required_dimension() -> None:
    with pytest.raises(PartitionPolicyError):
        _policy(forbidden_partition_fields=frozenset({"stream"}))


def test_dataclasses_replace_revalidates_via_post_init() -> None:
    policy = _policy()
    with pytest.raises(PartitionPolicyError):
        dataclasses.replace(policy, max_key_length=10)


# --- default_assessment_metadata_partition_policy() ---


def test_default_assessment_policy_ids_and_version() -> None:
    policy = default_assessment_metadata_partition_policy()
    assert policy.policy_id == ASSESSMENT_METADATA_PARTITION_POLICY_ID
    assert policy.policy_version == ASSESSMENT_METADATA_PARTITION_POLICY_VERSION
    assert policy.policy_version == "1.0"
    assert policy.policy_token == ASSESSMENT_METADATA_PARTITION_POLICY_URN
    assert ASSESSMENT_METADATA_PARTITION_POLICY_URN == (
        "community-assessment-metadata-partition-policy:1.0"
    )


def test_default_assessment_policy_event_stream() -> None:
    assert default_assessment_metadata_partition_policy().event_stream is (
        EventStream.ASSESSMENT_METADATA
    )


def test_default_assessment_policy_supported_versions() -> None:
    policy = default_assessment_metadata_partition_policy()
    assert policy.supported_envelope_schema_versions == frozenset({"1.0"})
    assert policy.supported_source_schema_versions == frozenset({"1.0"})
    assert policy.supported_source_policy_ids == frozenset(
        {"community-assessment-metadata-policy:1.0"}
    )


def test_default_assessment_policy_supported_assessment_schema_versions_matches_endpoint_allowlist() -> (
    None
):
    policy = default_assessment_metadata_partition_policy()
    assert policy.supported_assessment_schema_versions == frozenset(
        ALLOWED_ASSESSMENT_SCHEMA_VERSIONS
    )
    assert policy.supported_assessment_schema_versions == frozenset({"1.2"})


def test_default_assessment_policy_required_dimensions_are_generic_only() -> None:
    policy = default_assessment_metadata_partition_policy()
    assert policy.required_path_dimensions == ("stream", "schema_version", "year", "month", "day")
    assert policy.optional_path_dimensions == ()


def test_default_assessment_policy_s3_metadata_allowlist_includes_assessment_schema_key() -> None:
    policy = default_assessment_metadata_partition_policy()
    assert ASSESSMENT_SCHEMA_METADATA_KEY in policy.s3_metadata_allowlist
    assert "codestrata-stream" in policy.s3_metadata_allowlist


def test_default_assessment_policy_forbidden_fields_cover_identity_and_shape_material() -> None:
    policy = default_assessment_metadata_partition_policy()
    for field_name in (
        "event_id",
        "installation_id",
        "repository_name",
        "repository_url",
        "language",
        "primary_language",
        "repository_shape",
        "executed_heads",
        "finding_count",
        "client_type",
        "assessment_status",
        "result",
    ):
        assert field_name in policy.forbidden_partition_fields


def test_default_assessment_policy_forbidden_fields_never_overlap_required_dimensions() -> None:
    policy = default_assessment_metadata_partition_policy()
    assert not (set(policy.forbidden_partition_fields) & set(policy.required_path_dimensions))


def test_default_assessment_policy_limitations_document_the_dimension_decision() -> None:
    policy = default_assessment_metadata_partition_policy()
    blob = " ".join(policy.limitations)
    assert "no_extra_partition_dimensions" in blob
    assert "assessment_schema_in_metadata_not_path" in blob


def test_default_assessment_policy_max_partition_depth_covers_required_dimensions() -> None:
    policy = default_assessment_metadata_partition_policy()
    assert policy.max_partition_depth >= len(policy.required_path_dimensions)


def test_default_assessment_policy_is_deterministic_across_calls() -> None:
    first = default_assessment_metadata_partition_policy()
    second = default_assessment_metadata_partition_policy()
    assert first == second
    assert first.to_stable_dict() == second.to_stable_dict()
