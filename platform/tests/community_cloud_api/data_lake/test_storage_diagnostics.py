"""Storage abstraction diagnostics tests (Slice 8.13)."""

from __future__ import annotations

import json

from codestrata_platform.community_cloud_api.data_lake.storage import default_storage_policy
from codestrata_platform.community_cloud_api.data_lake.storage_capabilities import (
    StorageCapabilities,
)
from codestrata_platform.community_cloud_api.data_lake.storage_configuration import (
    StorageAdapterType,
)
from codestrata_platform.community_cloud_api.data_lake.storage_diagnostics import (
    diagnostics_from_storage,
)


def test_diagnostics_from_storage_is_deterministic() -> None:
    policy = default_storage_policy()
    first = diagnostics_from_storage(
        policy=policy,
        adapter_type=StorageAdapterType.S3,
        capabilities=StorageCapabilities.for_s3(),
    )
    second = diagnostics_from_storage(
        policy=policy,
        adapter_type=StorageAdapterType.S3,
        capabilities=StorageCapabilities.for_s3(),
    )
    assert first == second
    assert first.to_stable_dict() == second.to_stable_dict()


def test_diagnostics_public_dump_has_no_bucket_key_or_arn() -> None:
    diag = diagnostics_from_storage(
        policy=default_storage_policy(),
        adapter_type=StorageAdapterType.UNAVAILABLE,
        capabilities=StorageCapabilities.for_unavailable(),
    ).to_stable_dict()
    assert "bucket" not in diag
    assert "object_key" not in diag
    assert "arn" not in diag
    assert "prefix" not in diag
    assert "endpoint" not in diag
    assert "credential" not in diag


def test_unavailable_adapter_encryption_mode_is_none() -> None:
    diag = diagnostics_from_storage(
        policy=default_storage_policy(),
        adapter_type=StorageAdapterType.UNAVAILABLE,
        capabilities=StorageCapabilities.for_unavailable(),
    )
    assert diag.encryption_mode_category == "none"
    assert diag.validation_status == "valid"


def test_in_memory_adapter_encryption_mode_is_not_applicable() -> None:
    diag = diagnostics_from_storage(
        policy=default_storage_policy(),
        adapter_type=StorageAdapterType.IN_MEMORY_TEST,
        capabilities=StorageCapabilities.for_in_memory_test(),
    )
    assert diag.encryption_mode_category == "not_applicable_test_adapter"


def test_s3_adapter_defaults_to_sse_s3_category() -> None:
    diag = diagnostics_from_storage(
        policy=default_storage_policy(),
        adapter_type=StorageAdapterType.S3,
        capabilities=StorageCapabilities.for_s3(),
    )
    assert diag.encryption_mode_category == "sse_s3"
    assert diag.accepted_write_supported is True
    assert diag.quarantine_write_supported is True
