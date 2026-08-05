"""Storage adapter capability model tests (Slice 8.13)."""

from __future__ import annotations

import pytest

from codestrata_platform.community_cloud_api.data_lake.storage_capabilities import (
    FORBIDDEN_STORAGE_CAPABILITIES,
    StorageCapabilities,
    StorageCapability,
)
from codestrata_platform.community_cloud_api.data_lake.storage_validation import (
    StorageValidationError,
)


def test_s3_capabilities_set() -> None:
    caps = StorageCapabilities.for_s3()
    assert caps.supports(StorageCapability.ACCEPTED_IMMUTABLE_WRITE)
    assert caps.supports(StorageCapability.QUARANTINE_IMMUTABLE_WRITE)
    assert caps.supports(StorageCapability.CONDITIONAL_CREATE)
    assert caps.supports(StorageCapability.CHECKSUM_VALIDATION)
    assert caps.supports(StorageCapability.EXPLICIT_ENCRYPTION)
    assert caps.retry_verification_supported is True
    assert caps.is_unavailable is False


def test_in_memory_capabilities_set() -> None:
    caps = StorageCapabilities.for_in_memory_test()
    assert caps.supports(StorageCapability.ACCEPTED_IMMUTABLE_WRITE)
    assert caps.supports(StorageCapability.QUARANTINE_IMMUTABLE_WRITE)
    assert caps.supports(StorageCapability.CONDITIONAL_CREATE)
    assert caps.supports(StorageCapability.CHECKSUM_VALIDATION)
    assert not caps.supports(StorageCapability.EXPLICIT_ENCRYPTION)
    assert caps.is_unavailable is False


def test_unavailable_capabilities_set() -> None:
    caps = StorageCapabilities.for_unavailable()
    assert caps.capabilities == frozenset({StorageCapability.UNAVAILABLE})
    assert caps.is_unavailable is True
    assert caps.accepted_write_supported is False
    assert caps.quarantine_write_supported is False


def test_forbidden_capabilities_rejected() -> None:
    class FakeCapability:
        value = "list"

    with pytest.raises(StorageValidationError, match="forbidden storage capabilities"):
        StorageCapabilities(frozenset({FakeCapability()}))  # type: ignore[arg-type]


def test_valid_capability_sets_do_not_overlap_forbidden() -> None:
    for factory in (
        StorageCapabilities.for_s3,
        StorageCapabilities.for_in_memory_test,
        StorageCapabilities.for_unavailable,
    ):
        names = {cap.value for cap in factory().capabilities}
        assert names.isdisjoint(FORBIDDEN_STORAGE_CAPABILITIES)


def test_unavailable_cannot_combine_with_write_capabilities() -> None:
    with pytest.raises(StorageValidationError, match="unavailable capability cannot combine"):
        StorageCapabilities(
            frozenset(
                {
                    StorageCapability.UNAVAILABLE,
                    StorageCapability.ACCEPTED_IMMUTABLE_WRITE,
                }
            )
        )


def test_to_stable_dict_is_sorted() -> None:
    blob = StorageCapabilities.for_s3().to_stable_dict()
    assert list(blob) == sorted(blob)
    assert blob["accepted_write_supported"] is True
    assert blob["quarantine_write_supported"] is True
    assert blob["unavailable"] is False
