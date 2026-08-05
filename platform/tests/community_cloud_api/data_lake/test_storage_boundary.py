"""Storage-contract-specific boundary tests for Slice 8.2 (distinct from ``test_boundary.py``).

``test_boundary.py`` covers the general Community Data Lake package/wiring
boundary (Slice 8.1) plus the boto3-confinement boundary (Slice 8.2). This
module covers boundary properties specific to the immutable raw storage
contract itself: no forbidden adapter methods, no exactly-once claims in any
docstring/limitation text, versions pinned at 1.0, and production wiring
still untouched by the new infrastructure subpackage.
"""

from __future__ import annotations

import ast
from pathlib import Path

from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.errors import (
    DataLakeStorageError,
    StorageErrorCategory,
)
from codestrata_platform.community_cloud_api.data_lake.infrastructure.s3_store import (
    CommunityDataLakeS3Store,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.data_lake.receipts import DEFAULT_RECEIPT_LIMITATIONS
from codestrata_platform.community_cloud_api.constants import (
    COMMUNITY_DATA_LAKE_ENVELOPE_SCHEMA_VERSION,
    COMMUNITY_DATA_LAKE_POLICY_VERSION,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
PLATFORM_SRC = REPO_ROOT / "platform" / "src" / "codestrata_platform"
COMMUNITY_CLOUD_API_PKG = PLATFORM_SRC / "community_cloud_api"
DATA_LAKE_PKG = COMMUNITY_CLOUD_API_PKG / "data_lake"
INFRASTRUCTURE_PKG = DATA_LAKE_PKG / "infrastructure"

_FORBIDDEN_ADAPTER_METHODS = ("delete_object", "delete", "update", "list_objects", "list", "copy_object")


def test_versions_pinned_at_1_0_for_slice_8_2() -> None:
    assert COMMUNITY_DATA_LAKE_POLICY_VERSION == "1.0"
    assert COMMUNITY_DATA_LAKE_ENVELOPE_SCHEMA_VERSION == "1.0"
    assert CommunityDataLakePolicy.default().policy_version == "1.0"
    assert CommunityDataLakePolicy.default().envelope_schema_version == "1.0"


def test_s3_store_exposes_only_the_two_protocol_methods_and_no_others() -> None:
    for forbidden in _FORBIDDEN_ADAPTER_METHODS:
        assert not hasattr(CommunityDataLakeS3Store, forbidden), f"unexpected method: {forbidden}"
    assert hasattr(CommunityDataLakeS3Store, "put_immutable_event")
    assert hasattr(CommunityDataLakeS3Store, "quarantine_event")


def test_default_receipt_limitations_disclose_no_exactly_once_guarantee() -> None:
    blob = " ".join(DEFAULT_RECEIPT_LIMITATIONS).lower()
    assert "no_exactly_once" in blob


def test_no_source_file_under_data_lake_claims_exactly_once_delivery() -> None:
    """No module may claim exactly-once delivery in code, comments, or docstrings."""

    offenders = []
    for path in DATA_LAKE_PKG.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        if "guarantees exactly-once" in text or "guarantees exactly once" in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))
        if "exactly-once delivery is provided" in text or "exactly once delivery is provided" in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == []


def test_no_source_file_returns_http_202() -> None:
    """This slice defines no HTTP contract at all — no 202 Accepted status anywhere."""

    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path in DATA_LAKE_PKG.rglob("*.py")
        if "202 accepted" in path.read_text(encoding="utf-8").lower()
        or "status_code=202" in path.read_text(encoding="utf-8")
        or "http_status=202" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_storage_error_category_has_expected_members() -> None:
    expected = {
        "validation",
        "precondition",
        "access_denied",
        "transient",
        "timeout",
        "checksum_mismatch",
        "not_implemented",
        "unknown",
    }
    assert {member.value for member in StorageErrorCategory} == expected


def test_data_lake_storage_error_carries_category_and_safe_code() -> None:
    error = DataLakeStorageError(StorageErrorCategory.ACCESS_DENIED, "storage_access_denied")
    assert error.category is StorageErrorCategory.ACCESS_DENIED
    assert error.safe_code == "storage_access_denied"
    assert str(error) == "storage_access_denied"


def test_infrastructure_package_not_referenced_by_production_wiring_files() -> None:
    targets = (
        COMMUNITY_CLOUD_API_PKG / "app.py",
        COMMUNITY_CLOUD_API_PKG / "registry.py",
        COMMUNITY_CLOUD_API_PKG / "deployment" / "wiring.py",
        COMMUNITY_CLOUD_API_PKG / "deployment" / "settings.py",
    )
    offenders = []
    for target in targets:
        text = target.read_text(encoding="utf-8")
        if "data_lake" in text or "boto3" in text or "S3Store" in text:
            offenders.append(str(target.relative_to(REPO_ROOT)))
    assert offenders == []


def test_data_lake_top_level_init_does_not_import_infrastructure() -> None:
    init_path = DATA_LAKE_PKG / "__init__.py"
    text = init_path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(init_path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "infrastructure" not in node.module, f"unexpected eager import: {node.module}"


def test_s3_store_module_has_no_sleep_based_retry_delay() -> None:
    """Unit tests must run instantly — no real sleep-based backoff in this slice."""

    text = (INFRASTRUCTURE_PKG / "s3_store.py").read_text(encoding="utf-8")
    assert "time.sleep(" not in text
