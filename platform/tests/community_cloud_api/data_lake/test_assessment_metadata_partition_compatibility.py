"""Version/schema compatibility guarantees for Slice 8.4 (assessment metadata partitioning)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.assessment_metadata.policy import (
    ALLOWED_ASSESSMENT_SCHEMA_VERSIONS,
    COMMUNITY_ASSESSMENT_METADATA_POLICY_URN,
    COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION,
)
from codestrata_platform.community_cloud_api.constants import (
    COMMUNITY_ASSESSMENT_METADATA_POLICY_VERSION,
    COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION as CONSTANTS_ASSESSMENT_SCHEMA_VERSION,
    COMMUNITY_DATA_LAKE_ENVELOPE_SCHEMA_VERSION,
    COMMUNITY_DATA_LAKE_POLICY_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.partition_policies import (
    GENERIC_REQUIRED_PATH_DIMENSIONS,
)
from codestrata_platform.community_cloud_api.data_lake.streams.assessment_metadata_partitioning import (
    ASSESSMENT_METADATA_PARTITION_POLICY_ID,
    ASSESSMENT_METADATA_PARTITION_POLICY_URN,
    ASSESSMENT_METADATA_PARTITION_POLICY_VERSION,
    default_assessment_metadata_partition_policy,
)


def test_data_lake_envelope_and_policy_versions_remain_pinned_at_1_0() -> None:
    assert COMMUNITY_DATA_LAKE_POLICY_VERSION == "1.0"
    assert COMMUNITY_DATA_LAKE_ENVELOPE_SCHEMA_VERSION == "1.0"


def test_assessment_metadata_endpoint_schema_and_policy_remain_pinned_at_1_0() -> None:
    assert COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_ASSESSMENT_METADATA_POLICY_VERSION == "1.0"
    assert CONSTANTS_ASSESSMENT_SCHEMA_VERSION == "1.0"


def test_assessment_report_schema_allowlist_remains_1_2_only() -> None:
    assert ALLOWED_ASSESSMENT_SCHEMA_VERSIONS == ("1.2",)


def test_new_partition_policy_is_versioned_1_0() -> None:
    assert ASSESSMENT_METADATA_PARTITION_POLICY_VERSION == "1.0"
    assert ASSESSMENT_METADATA_PARTITION_POLICY_URN == f"{ASSESSMENT_METADATA_PARTITION_POLICY_ID}:1.0"
    assert default_assessment_metadata_partition_policy().policy_version == "1.0"


def test_partition_policy_assessment_schema_set_stays_in_sync_with_endpoint_policy() -> None:
    """If the endpoint's allowlist ever changes, this partition policy must move with it.

    This test intentionally couples the two: a future slice that widens
    ``ALLOWED_ASSESSMENT_SCHEMA_VERSIONS`` without updating the partition
    policy's ``supported_assessment_schema_versions`` will fail here first.
    """

    policy = default_assessment_metadata_partition_policy()
    assert policy.supported_assessment_schema_versions == frozenset(
        ALLOWED_ASSESSMENT_SCHEMA_VERSIONS
    )


def test_partition_policy_source_policy_id_matches_endpoint_policy_urn() -> None:
    policy = default_assessment_metadata_partition_policy()
    assert COMMUNITY_ASSESSMENT_METADATA_POLICY_URN in policy.supported_source_policy_ids


def test_partition_policy_source_schema_version_matches_endpoint_schema_version() -> None:
    policy = default_assessment_metadata_partition_policy()
    assert COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION in policy.supported_source_schema_versions


def test_generic_required_path_dimensions_are_unchanged_five_field_hive_shape() -> None:
    assert GENERIC_REQUIRED_PATH_DIMENSIONS == (
        "stream",
        "schema_version",
        "year",
        "month",
        "day",
    )


def test_default_partition_policy_required_dimensions_match_the_generic_constant() -> None:
    policy = default_assessment_metadata_partition_policy()
    assert policy.required_path_dimensions == GENERIC_REQUIRED_PATH_DIMENSIONS


def test_default_partition_policy_has_no_optional_path_dimensions() -> None:
    """No extra partition dimension exists yet for this stream (Slice 8.4 decision)."""

    assert default_assessment_metadata_partition_policy().optional_path_dimensions == ()
