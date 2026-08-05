"""Community Data Lake policy defaults and bounds (Slice 8.1)."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from codestrata_platform.community_cloud_api.data_lake.enums import EncryptionMode, EventStream
from codestrata_platform.community_cloud_api.data_lake.policy import (
    COMMUNITY_DATA_LAKE_POLICY_ID,
    COMMUNITY_DATA_LAKE_POLICY_URN,
    CommunityDataLakePolicy,
    default_data_lake_policy,
)


def test_default_policy_values() -> None:
    policy = CommunityDataLakePolicy.default()
    assert policy.policy_id == "community-data-lake-policy"
    assert policy.policy_version == "1.0"
    assert policy.envelope_schema_version == "1.0"
    assert policy.accepted_retention_days == 365
    assert policy.quarantine_retention_days == 90
    assert policy.incomplete_multipart_days == 7
    assert policy.noncurrent_version_expiration_days == 30
    assert policy.encryption_mode is EncryptionMode.SSE_S3
    assert policy.enable_versioning is True
    assert policy.bucket_strategy == "single_bucket_prefix_isolation"
    assert policy.accepted_prefix == "raw/"
    assert policy.quarantine_prefix == "quarantine/"
    assert policy.hive_style_partitions is True


def test_default_data_lake_policy_matches_class_default() -> None:
    assert default_data_lake_policy() == CommunityDataLakePolicy.default()


def test_policy_token() -> None:
    policy = CommunityDataLakePolicy.default()
    assert policy.policy_token == "community-data-lake-policy:1.0"
    assert policy.policy_token == COMMUNITY_DATA_LAKE_POLICY_URN
    assert policy.policy_id == COMMUNITY_DATA_LAKE_POLICY_ID


def test_allowed_event_streams_default_matches_enum() -> None:
    policy = CommunityDataLakePolicy.default()
    assert set(policy.allowed_event_streams) == {item.value for item in EventStream}
    assert policy.allowed_event_streams == tuple(sorted(policy.allowed_event_streams))


@pytest.mark.parametrize("days", [30, 90, 365, 2555])
def test_accepted_retention_days_within_bounds_accepted(days: int) -> None:
    # quarantine default is 90; keep quarantine <= accepted when lowering accepted.
    quarantine = min(90, days)
    policy = CommunityDataLakePolicy(
        accepted_retention_days=days,
        quarantine_retention_days=quarantine,
    )
    assert policy.accepted_retention_days == days


@pytest.mark.parametrize("days", [0, 29, 2556, 10_000, -1])
def test_accepted_retention_days_out_of_bounds_rejected(days: int) -> None:
    with pytest.raises(ValueError):
        CommunityDataLakePolicy(
            accepted_retention_days=days,
            quarantine_retention_days=min(90, max(days, 7)) if days > 0 else 7,
        )


@pytest.mark.parametrize("days", [7, 30, 365])
def test_quarantine_retention_days_within_bounds_accepted(days: int) -> None:
    policy = CommunityDataLakePolicy(quarantine_retention_days=days)
    assert policy.quarantine_retention_days == days


@pytest.mark.parametrize("days", [0, 6, 366, 1000, -5])
def test_quarantine_retention_days_out_of_bounds_rejected(days: int) -> None:
    with pytest.raises(ValueError):
        CommunityDataLakePolicy(quarantine_retention_days=days)


def test_quarantine_retention_greater_than_accepted_rejected() -> None:
    with pytest.raises(ValueError, match="less than or equal"):
        CommunityDataLakePolicy(
            accepted_retention_days=30,
            quarantine_retention_days=90,
        )


def test_non_positive_lifecycle_days_rejected() -> None:
    with pytest.raises(ValueError):
        CommunityDataLakePolicy(incomplete_multipart_days=0)
    with pytest.raises(ValueError):
        CommunityDataLakePolicy(noncurrent_version_expiration_days=-1)


def test_prefixes_must_end_with_slash() -> None:
    with pytest.raises(ValueError):
        CommunityDataLakePolicy(accepted_prefix="raw")
    with pytest.raises(ValueError):
        CommunityDataLakePolicy(quarantine_prefix="quarantine")


def test_prefixes_must_differ() -> None:
    with pytest.raises(ValueError):
        CommunityDataLakePolicy(accepted_prefix="shared/", quarantine_prefix="shared/")


def test_invalid_policy_id_rejected() -> None:
    with pytest.raises(ValueError):
        CommunityDataLakePolicy(policy_id="not-the-real-policy")


def test_invalid_policy_version_rejected() -> None:
    with pytest.raises(ValueError):
        CommunityDataLakePolicy(policy_version="9.9")


def test_invalid_envelope_schema_version_rejected() -> None:
    with pytest.raises(ValueError):
        CommunityDataLakePolicy(envelope_schema_version="2.0")


def test_empty_allowed_event_streams_rejected() -> None:
    with pytest.raises(ValueError):
        CommunityDataLakePolicy(allowed_event_streams=())


def test_unknown_allowed_event_stream_rejected() -> None:
    with pytest.raises(ValueError):
        CommunityDataLakePolicy(allowed_event_streams=("not_a_real_stream",))


def test_to_stable_dict_is_sorted_and_json_serializable() -> None:
    policy = CommunityDataLakePolicy.default()
    blob = policy.to_stable_dict()
    assert list(blob) == sorted(blob)
    text = json.dumps(blob, sort_keys=True)
    assert isinstance(text, str)
    assert blob["policy_token"] == "community-data-lake-policy:1.0"
    assert blob["encryption_mode"] == "sse_s3"


def test_policy_is_frozen() -> None:
    policy = CommunityDataLakePolicy.default()
    with pytest.raises(FrozenInstanceError):
        policy.accepted_retention_days = 400  # type: ignore[misc]
