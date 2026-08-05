"""CLI event partition policy tests (Slice 8.6).

Generic ``StreamPartitionPolicy`` construction/validation is already covered
by ``test_assessment_metadata_partition_policy.py`` — this module covers
only ``default_cli_event_partition_policy()``'s concrete shape.
"""

from __future__ import annotations

from codestrata_platform.community_cloud_api.cli_events.catalog import (
    CLI_OPERATION_CATALOG_VERSION,
)
from codestrata_platform.community_cloud_api.cli_events.policy import (
    COMMUNITY_CLI_EVENT_POLICY_URN,
)
from codestrata_platform.community_cloud_api.data_lake.enums import EventStream
from codestrata_platform.community_cloud_api.data_lake.objects import BASE_S3_METADATA_KEYS
from codestrata_platform.community_cloud_api.data_lake.streams.cli_event_partitioning import (
    CLI_EVENT_PARTITION_POLICY_ID,
    CLI_EVENT_PARTITION_POLICY_URN,
    CLI_EVENT_PARTITION_POLICY_VERSION,
    default_cli_event_partition_policy,
)


def test_default_cli_event_policy_ids_and_version() -> None:
    policy = default_cli_event_partition_policy()
    assert policy.policy_id == CLI_EVENT_PARTITION_POLICY_ID
    assert policy.policy_version == CLI_EVENT_PARTITION_POLICY_VERSION
    assert policy.policy_version == "1.0"
    assert policy.policy_token == CLI_EVENT_PARTITION_POLICY_URN
    assert CLI_EVENT_PARTITION_POLICY_URN == "community-cli-event-partition-policy:1.0"


def test_default_cli_event_policy_event_stream() -> None:
    assert default_cli_event_partition_policy().event_stream is EventStream.CLI_EVENT


def test_default_cli_event_policy_supported_versions() -> None:
    policy = default_cli_event_partition_policy()
    assert policy.supported_envelope_schema_versions == frozenset({"1.0"})
    assert policy.supported_source_schema_versions == frozenset({"1.0"})
    assert policy.supported_source_policy_ids == frozenset({COMMUNITY_CLI_EVENT_POLICY_URN})
    assert policy.supported_source_policy_ids == frozenset({"community-cli-event-policy:1.0"})


def test_default_cli_event_policy_has_no_assessment_schema_versions() -> None:
    policy = default_cli_event_partition_policy()
    assert policy.supported_assessment_schema_versions == frozenset()


def test_default_cli_event_policy_supported_operation_catalog_versions() -> None:
    policy = default_cli_event_partition_policy()
    assert policy.supported_operation_catalog_versions == frozenset({CLI_OPERATION_CATALOG_VERSION})
    assert policy.supported_operation_catalog_versions == frozenset({"1.0"})


def test_default_cli_event_policy_required_dimensions_are_generic_only() -> None:
    policy = default_cli_event_partition_policy()
    assert policy.required_path_dimensions == ("stream", "schema_version", "year", "month", "day")
    assert policy.optional_path_dimensions == ()


def test_default_cli_event_policy_s3_metadata_allowlist_is_exactly_the_five_base_keys() -> None:
    policy = default_cli_event_partition_policy()
    assert policy.s3_metadata_allowlist == frozenset(BASE_S3_METADATA_KEYS)
    assert len(policy.s3_metadata_allowlist) == 5


def test_default_cli_event_policy_s3_metadata_allowlist_excludes_stream_specific_keys() -> None:
    policy = default_cli_event_partition_policy()
    assert "codestrata-client-type" not in policy.s3_metadata_allowlist
    assert "codestrata-assessment-schema" not in policy.s3_metadata_allowlist


def test_default_cli_event_policy_forbidden_fields_cover_private_payload_material() -> None:
    policy = default_cli_event_partition_policy()
    for field_name in (
        "event_id",
        "installation_id",
        "request_id",
        "operation",
        "lifecycle",
        "result",
        "failure_category",
        "duration_bucket",
        "invocation_source",
        "command",
        "command_line",
        "argv",
        "cwd",
        "repository_name",
        "repository_url",
        "path",
        "file",
        "source",
        "client_type",
        "client_version",
        "platform",
    ):
        assert field_name in policy.forbidden_partition_fields


def test_default_cli_event_policy_forbidden_fields_never_overlap_required_dimensions() -> None:
    policy = default_cli_event_partition_policy()
    assert not (set(policy.forbidden_partition_fields) & set(policy.required_path_dimensions))


def test_default_cli_event_policy_limitations_document_the_dimension_decision() -> None:
    policy = default_cli_event_partition_policy()
    blob = " ".join(policy.limitations)
    assert "no_extra_partition_dimensions" in blob
    assert "no_cli_specific_s3_metadata" in blob
    assert "operation_remains_private_payload" in blob
    assert "lifecycle_result_remain_private_payload" in blob


def test_default_cli_event_policy_max_partition_depth_covers_required_dimensions() -> None:
    policy = default_cli_event_partition_policy()
    assert policy.max_partition_depth >= len(policy.required_path_dimensions)


def test_default_cli_event_policy_is_deterministic_across_calls() -> None:
    first = default_cli_event_partition_policy()
    second = default_cli_event_partition_policy()
    assert first == second
    assert first.to_stable_dict() == second.to_stable_dict()


def test_default_cli_event_policy_to_stable_dict_includes_operation_catalog_versions() -> None:
    policy = default_cli_event_partition_policy()
    blob = policy.to_stable_dict()
    assert blob["supported_operation_catalog_versions"] == ["1.0"]
