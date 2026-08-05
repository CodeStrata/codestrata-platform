"""Version/schema compatibility guarantees for Slice 8.7 (extension event partitioning)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.constants import (
    COMMUNITY_DATA_LAKE_ENVELOPE_SCHEMA_VERSION,
    COMMUNITY_DATA_LAKE_POLICY_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.objects import (
    ALLOWED_S3_METADATA_KEYS,
    BASE_S3_METADATA_KEYS,
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
    default_cli_event_partition_policy,
)
from codestrata_platform.community_cloud_api.data_lake.streams.extension_event_partitioning import (
    EXTENSION_EVENT_PARTITION_POLICY_ID,
    EXTENSION_EVENT_PARTITION_POLICY_URN,
    EXTENSION_EVENT_PARTITION_POLICY_VERSION,
    default_extension_event_partition_policy,
)
from codestrata_platform.community_cloud_api.data_lake.streams.telemetry_partitioning import (
    TELEMETRY_PARTITION_POLICY_ID,
    TELEMETRY_PARTITION_POLICY_URN,
)
from codestrata_platform.community_cloud_api.extension_events.catalog import (
    EXTENSION_OPERATION_CATALOG_VERSION,
)
from codestrata_platform.community_cloud_api.extension_events.policy import (
    COMMUNITY_EXTENSION_EVENT_POLICY_URN,
)


def test_data_lake_envelope_and_policy_versions_remain_pinned_at_1_0() -> None:
    assert COMMUNITY_DATA_LAKE_POLICY_VERSION == "1.0"
    assert COMMUNITY_DATA_LAKE_ENVELOPE_SCHEMA_VERSION == "1.0"


def test_extension_event_endpoint_schema_and_policy_remain_pinned_at_1_0() -> None:
    assert COMMUNITY_EXTENSION_EVENT_POLICY_URN == "community-extension-event-policy:1.0"
    assert EXTENSION_OPERATION_CATALOG_VERSION == "1.0"


def test_new_partition_policy_is_versioned_1_0() -> None:
    assert EXTENSION_EVENT_PARTITION_POLICY_VERSION == "1.0"
    assert EXTENSION_EVENT_PARTITION_POLICY_URN == f"{EXTENSION_EVENT_PARTITION_POLICY_ID}:1.0"
    assert default_extension_event_partition_policy().policy_version == "1.0"


def test_partition_policy_has_no_assessment_schema_concept() -> None:
    """Extension events carry no nested "assessment schema" — unlike Slice 8.4."""

    policy = default_extension_event_partition_policy()
    assert policy.supported_assessment_schema_versions == frozenset()


def test_partition_policy_has_the_operation_catalog_concept() -> None:
    """Extension events reuse ``supported_operation_catalog_versions`` like CLI."""

    policy = default_extension_event_partition_policy()
    assert policy.supported_operation_catalog_versions == frozenset(
        {EXTENSION_OPERATION_CATALOG_VERSION}
    )


def test_partition_policy_source_policy_id_matches_endpoint_policy_urn() -> None:
    policy = default_extension_event_partition_policy()
    assert COMMUNITY_EXTENSION_EVENT_POLICY_URN in policy.supported_source_policy_ids
    assert policy.supported_source_policy_ids == frozenset(
        {"community-extension-event-policy:1.0"}
    )


def test_generic_required_path_dimensions_are_unchanged_five_field_hive_shape() -> None:
    assert GENERIC_REQUIRED_PATH_DIMENSIONS == (
        "stream",
        "schema_version",
        "year",
        "month",
        "day",
    )


def test_default_partition_policy_required_dimensions_match_the_generic_constant() -> None:
    policy = default_extension_event_partition_policy()
    assert policy.required_path_dimensions == GENERIC_REQUIRED_PATH_DIMENSIONS


def test_default_partition_policy_has_no_optional_path_dimensions() -> None:
    """No extra partition dimension exists for this stream (Slice 8.7 decision)."""

    assert default_extension_event_partition_policy().optional_path_dimensions == ()


def test_extension_event_and_prior_partition_policies_are_all_distinct() -> None:
    ids = {
        EXTENSION_EVENT_PARTITION_POLICY_ID,
        CLI_EVENT_PARTITION_POLICY_ID,
        ASSESSMENT_METADATA_PARTITION_POLICY_ID,
        TELEMETRY_PARTITION_POLICY_ID,
    }
    urns = {
        EXTENSION_EVENT_PARTITION_POLICY_URN,
        CLI_EVENT_PARTITION_POLICY_URN,
        ASSESSMENT_METADATA_PARTITION_POLICY_URN,
        TELEMETRY_PARTITION_POLICY_URN,
    }
    assert len(ids) == 4
    assert len(urns) == 4


def test_cli_partition_policy_still_excludes_client_type_from_allowlist() -> None:
    cli_policy = default_cli_event_partition_policy()
    assert cli_policy.s3_metadata_allowlist == frozenset(BASE_S3_METADATA_KEYS)
    assert "codestrata-client-type" not in cli_policy.s3_metadata_allowlist


def test_extension_partition_policy_includes_client_type_in_allowlist() -> None:
    policy = default_extension_event_partition_policy()
    assert policy.s3_metadata_allowlist == frozenset(ALLOWED_S3_METADATA_KEYS)
    assert "codestrata-client-type" in policy.s3_metadata_allowlist
