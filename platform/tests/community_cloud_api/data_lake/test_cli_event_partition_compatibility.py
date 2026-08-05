"""Version/schema compatibility guarantees for Slice 8.6 (CLI event partitioning)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.cli_events.catalog import (
    CLI_OPERATION_CATALOG_VERSION,
)
from codestrata_platform.community_cloud_api.cli_events.policy import (
    COMMUNITY_CLI_EVENT_POLICY_URN,
)
from codestrata_platform.community_cloud_api.constants import (
    COMMUNITY_DATA_LAKE_ENVELOPE_SCHEMA_VERSION,
    COMMUNITY_DATA_LAKE_POLICY_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.partition_policies import (
    GENERIC_REQUIRED_PATH_DIMENSIONS,
)
from codestrata_platform.community_cloud_api.data_lake.streams.assessment_metadata_partitioning import (
    ASSESSMENT_METADATA_PARTITION_POLICY_ID,
    ASSESSMENT_METADATA_PARTITION_POLICY_URN,
)
from codestrata_platform.community_cloud_api.data_lake.streams.cli_event_partitioning import (
    CLI_EVENT_PARTITION_POLICY_ID,
    CLI_EVENT_PARTITION_POLICY_URN,
    CLI_EVENT_PARTITION_POLICY_VERSION,
    default_cli_event_partition_policy,
)
from codestrata_platform.community_cloud_api.data_lake.streams.telemetry_partitioning import (
    TELEMETRY_PARTITION_POLICY_ID,
    TELEMETRY_PARTITION_POLICY_URN,
)


def test_data_lake_envelope_and_policy_versions_remain_pinned_at_1_0() -> None:
    assert COMMUNITY_DATA_LAKE_POLICY_VERSION == "1.0"
    assert COMMUNITY_DATA_LAKE_ENVELOPE_SCHEMA_VERSION == "1.0"


def test_cli_event_endpoint_schema_and_policy_remain_pinned_at_1_0() -> None:
    assert COMMUNITY_CLI_EVENT_POLICY_URN == "community-cli-event-policy:1.0"
    assert CLI_OPERATION_CATALOG_VERSION == "1.0"


def test_new_partition_policy_is_versioned_1_0() -> None:
    assert CLI_EVENT_PARTITION_POLICY_VERSION == "1.0"
    assert CLI_EVENT_PARTITION_POLICY_URN == f"{CLI_EVENT_PARTITION_POLICY_ID}:1.0"
    assert default_cli_event_partition_policy().policy_version == "1.0"


def test_partition_policy_has_no_assessment_schema_concept() -> None:
    """CLI events carry no nested "assessment schema" — unlike Slice 8.4's stream."""

    policy = default_cli_event_partition_policy()
    assert policy.supported_assessment_schema_versions == frozenset()


def test_partition_policy_has_the_operation_catalog_concept() -> None:
    """CLI events are the first stream to use ``supported_operation_catalog_versions``."""

    policy = default_cli_event_partition_policy()
    assert policy.supported_operation_catalog_versions == frozenset({CLI_OPERATION_CATALOG_VERSION})


def test_partition_policy_source_policy_id_matches_endpoint_policy_urn() -> None:
    policy = default_cli_event_partition_policy()
    assert COMMUNITY_CLI_EVENT_POLICY_URN in policy.supported_source_policy_ids
    assert policy.supported_source_policy_ids == frozenset({"community-cli-event-policy:1.0"})


def test_generic_required_path_dimensions_are_unchanged_five_field_hive_shape() -> None:
    assert GENERIC_REQUIRED_PATH_DIMENSIONS == (
        "stream",
        "schema_version",
        "year",
        "month",
        "day",
    )


def test_default_partition_policy_required_dimensions_match_the_generic_constant() -> None:
    policy = default_cli_event_partition_policy()
    assert policy.required_path_dimensions == GENERIC_REQUIRED_PATH_DIMENSIONS


def test_default_partition_policy_has_no_optional_path_dimensions() -> None:
    """No extra partition dimension exists for this stream (Slice 8.6 decision)."""

    assert default_cli_event_partition_policy().optional_path_dimensions == ()


def test_cli_event_and_other_partition_policies_are_all_distinct() -> None:
    ids = {
        CLI_EVENT_PARTITION_POLICY_ID,
        ASSESSMENT_METADATA_PARTITION_POLICY_ID,
        TELEMETRY_PARTITION_POLICY_ID,
    }
    urns = {
        CLI_EVENT_PARTITION_POLICY_URN,
        ASSESSMENT_METADATA_PARTITION_POLICY_URN,
        TELEMETRY_PARTITION_POLICY_URN,
    }
    assert len(ids) == 3
    assert len(urns) == 3
