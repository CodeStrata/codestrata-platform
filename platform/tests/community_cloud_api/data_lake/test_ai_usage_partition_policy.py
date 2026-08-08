"""AI usage partition policy tests (Slice 8.8).

Generic ``StreamPartitionPolicy`` construction/validation is already covered
by ``test_assessment_metadata_partition_policy.py`` — this module covers
only ``default_ai_usage_partition_policy()``'s concrete shape.
"""

from __future__ import annotations

from codestrata_platform.community_cloud_api.ai_usage.catalog import (
    AI_CAPABILITY_CATALOG_VERSION,
    AI_MODEL_FAMILY_CATALOG_VERSION,
    AI_PROVIDER_FAMILY_CATALOG_VERSION,
)
from codestrata_platform.community_cloud_api.ai_usage.policy import (
    COMMUNITY_AI_USAGE_POLICY_URN,
)
from codestrata_platform.community_cloud_api.data_lake.enums import EventStream
from codestrata_platform.community_cloud_api.data_lake.objects import ALLOWED_S3_METADATA_KEYS
from codestrata_platform.community_cloud_api.data_lake.streams.ai_usage_partitioning import (
    AI_USAGE_PARTITION_POLICY_ID,
    AI_USAGE_PARTITION_POLICY_URN,
    AI_USAGE_PARTITION_POLICY_VERSION,
    default_ai_usage_partition_policy,
)


def test_default_ai_usage_policy_ids_and_version() -> None:
    policy = default_ai_usage_partition_policy()
    assert policy.policy_id == AI_USAGE_PARTITION_POLICY_ID
    assert policy.policy_version == AI_USAGE_PARTITION_POLICY_VERSION
    assert policy.policy_version == "1.0"
    assert policy.policy_token == AI_USAGE_PARTITION_POLICY_URN
    assert AI_USAGE_PARTITION_POLICY_URN == ("community-ai-usage-partition-policy:1.0")


def test_default_ai_usage_policy_event_stream() -> None:
    assert default_ai_usage_partition_policy().event_stream is EventStream.AI_USAGE


def test_default_ai_usage_policy_supported_versions() -> None:
    policy = default_ai_usage_partition_policy()
    assert policy.supported_envelope_schema_versions == frozenset({"1.0"})
    assert policy.supported_source_schema_versions == frozenset({"1.0"})
    assert policy.supported_source_policy_ids == frozenset({COMMUNITY_AI_USAGE_POLICY_URN})
    assert policy.supported_source_policy_ids == frozenset({"community-ai-usage-policy:1.0"})


def test_default_ai_usage_policy_has_no_assessment_schema_versions() -> None:
    policy = default_ai_usage_partition_policy()
    assert policy.supported_assessment_schema_versions == frozenset()


def test_default_ai_usage_policy_has_empty_operation_catalog_versions() -> None:
    policy = default_ai_usage_partition_policy()
    assert policy.supported_operation_catalog_versions == frozenset()


def test_default_ai_usage_policy_supported_capability_catalog_versions() -> None:
    policy = default_ai_usage_partition_policy()
    assert policy.supported_capability_catalog_versions == frozenset(
        {AI_CAPABILITY_CATALOG_VERSION}
    )
    assert policy.supported_capability_catalog_versions == frozenset({"1.0"})


def test_default_ai_usage_policy_supported_provider_catalog_versions() -> None:
    policy = default_ai_usage_partition_policy()
    assert policy.supported_provider_catalog_versions == frozenset(
        {AI_PROVIDER_FAMILY_CATALOG_VERSION}
    )
    assert policy.supported_provider_catalog_versions == frozenset({"1.0"})


def test_default_ai_usage_policy_supported_model_catalog_versions() -> None:
    policy = default_ai_usage_partition_policy()
    assert policy.supported_model_catalog_versions == frozenset({AI_MODEL_FAMILY_CATALOG_VERSION})
    assert policy.supported_model_catalog_versions == frozenset({"1.0"})


def test_default_ai_usage_policy_required_dimensions_are_generic_only() -> None:
    policy = default_ai_usage_partition_policy()
    assert policy.required_path_dimensions == ("stream", "schema_version", "year", "month", "day")
    assert policy.optional_path_dimensions == ()


def test_default_ai_usage_policy_s3_metadata_allowlist_includes_client_type() -> None:
    policy = default_ai_usage_partition_policy()
    assert policy.s3_metadata_allowlist == frozenset(ALLOWED_S3_METADATA_KEYS)
    assert "codestrata-client-type" in policy.s3_metadata_allowlist


def test_default_ai_usage_policy_forbidden_fields_cover_private_payload_material() -> None:
    policy = default_ai_usage_partition_policy()
    for field_name in (
        "event_id",
        "installation_id",
        "request_id",
        "capability",
        "provider_family",
        "model_family",
        "model",
        "model_id",
        "prompt",
        "response",
        "cost",
        "token",
        "api_key",
        "outcome",
        "client_type",
        "client_version",
        "platform",
        "tool_usage",
        "rag_usage",
        "graph_usage",
        "repository",
        "path",
        "file",
        "source",
    ):
        assert field_name in policy.forbidden_partition_fields


def test_default_ai_usage_policy_forbidden_fields_never_overlap_required_dimensions() -> None:
    policy = default_ai_usage_partition_policy()
    assert not (set(policy.forbidden_partition_fields) & set(policy.required_path_dimensions))


def test_default_ai_usage_policy_limitations_document_the_dimension_decision() -> None:
    policy = default_ai_usage_partition_policy()
    blob = " ".join(policy.limitations)
    assert "no_extra_partition_dimensions" in blob
    assert "client_type_in_metadata_not_path" in blob
    assert "capability_provider_model_remain_private_payload" in blob
    assert "openrouter_provider_family_supported" in blob


def test_default_ai_usage_policy_max_partition_depth_covers_required_dimensions() -> None:
    policy = default_ai_usage_partition_policy()
    assert policy.max_partition_depth >= len(policy.required_path_dimensions)


def test_default_ai_usage_policy_is_deterministic_across_calls() -> None:
    first = default_ai_usage_partition_policy()
    second = default_ai_usage_partition_policy()
    assert first == second
    assert first.to_stable_dict() == second.to_stable_dict()


def test_default_ai_usage_policy_to_stable_dict_includes_catalog_versions() -> None:
    policy = default_ai_usage_partition_policy()
    blob = policy.to_stable_dict()
    assert blob["supported_capability_catalog_versions"] == ["1.0"]
    assert blob["supported_provider_catalog_versions"] == ["1.0"]
    assert blob["supported_model_catalog_versions"] == ["1.0"]
    assert blob["supported_operation_catalog_versions"] == []
