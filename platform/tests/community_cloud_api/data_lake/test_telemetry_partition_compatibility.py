"""Version/schema compatibility guarantees for Slice 8.5 (telemetry partitioning)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.constants import (
    COMMUNITY_DATA_LAKE_ENVELOPE_SCHEMA_VERSION,
    COMMUNITY_DATA_LAKE_POLICY_VERSION,
    COMMUNITY_TELEMETRY_POLICY_VERSION,
)
from codestrata_platform.community_cloud_api.constants import (
    COMMUNITY_TELEMETRY_SCHEMA_VERSION as CONSTANTS_TELEMETRY_SCHEMA_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.partition_policies import (
    GENERIC_REQUIRED_PATH_DIMENSIONS,
)
from codestrata_platform.community_cloud_api.data_lake.streams.assessment_metadata_partitioning import (
    ASSESSMENT_METADATA_PARTITION_POLICY_ID,
    ASSESSMENT_METADATA_PARTITION_POLICY_URN,
)
from codestrata_platform.community_cloud_api.data_lake.streams.telemetry_partitioning import (
    TELEMETRY_PARTITION_POLICY_ID,
    TELEMETRY_PARTITION_POLICY_URN,
    TELEMETRY_PARTITION_POLICY_VERSION,
    default_telemetry_partition_policy,
)
from codestrata_platform.community_cloud_api.telemetry.policy import (
    COMMUNITY_TELEMETRY_POLICY_URN,
    COMMUNITY_TELEMETRY_SCHEMA_VERSION,
)


def test_data_lake_envelope_and_policy_versions_remain_pinned_at_1_0() -> None:
    assert COMMUNITY_DATA_LAKE_POLICY_VERSION == "1.0"
    assert COMMUNITY_DATA_LAKE_ENVELOPE_SCHEMA_VERSION == "1.0"


def test_telemetry_endpoint_schema_and_policy_remain_pinned_at_1_0() -> None:
    assert COMMUNITY_TELEMETRY_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_TELEMETRY_POLICY_VERSION == "1.0"
    assert CONSTANTS_TELEMETRY_SCHEMA_VERSION == "1.0"


def test_new_partition_policy_is_versioned_1_0() -> None:
    assert TELEMETRY_PARTITION_POLICY_VERSION == "1.0"
    assert TELEMETRY_PARTITION_POLICY_URN == f"{TELEMETRY_PARTITION_POLICY_ID}:1.0"
    assert default_telemetry_partition_policy().policy_version == "1.0"


def test_partition_policy_has_no_assessment_schema_concept() -> None:
    """Telemetry carries no nested "assessment schema" — unlike Slice 8.4's stream."""

    policy = default_telemetry_partition_policy()
    assert policy.supported_assessment_schema_versions == frozenset()


def test_partition_policy_source_policy_id_matches_endpoint_policy_urn() -> None:
    policy = default_telemetry_partition_policy()
    assert COMMUNITY_TELEMETRY_POLICY_URN in policy.supported_source_policy_ids
    assert policy.supported_source_policy_ids == frozenset({"community-telemetry-policy:1.0"})


def test_partition_policy_source_schema_version_matches_endpoint_schema_version() -> None:
    policy = default_telemetry_partition_policy()
    assert COMMUNITY_TELEMETRY_SCHEMA_VERSION in policy.supported_source_schema_versions


def test_generic_required_path_dimensions_are_unchanged_five_field_hive_shape() -> None:
    assert GENERIC_REQUIRED_PATH_DIMENSIONS == (
        "stream",
        "schema_version",
        "year",
        "month",
        "day",
    )


def test_default_partition_policy_required_dimensions_match_the_generic_constant() -> None:
    policy = default_telemetry_partition_policy()
    assert policy.required_path_dimensions == GENERIC_REQUIRED_PATH_DIMENSIONS


def test_default_partition_policy_has_no_optional_path_dimensions() -> None:
    """No extra partition dimension exists for this stream (Slice 8.5 decision)."""

    assert default_telemetry_partition_policy().optional_path_dimensions == ()


def test_telemetry_and_assessment_metadata_partition_policies_are_distinct() -> None:
    assert TELEMETRY_PARTITION_POLICY_ID != ASSESSMENT_METADATA_PARTITION_POLICY_ID
    assert TELEMETRY_PARTITION_POLICY_URN != ASSESSMENT_METADATA_PARTITION_POLICY_URN
