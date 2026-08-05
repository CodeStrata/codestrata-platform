"""Storage port / S3 adapter access contract (Slice 8.12)."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from codestrata_platform.community_cloud_api.data_lake.ports import (
    CommunityDataLakeStore,
    InMemoryCommunityDataLakeStore,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
PORTS_PY = (
    REPO_ROOT
    / "platform"
    / "src"
    / "codestrata_platform"
    / "community_cloud_api"
    / "data_lake"
    / "ports.py"
)
S3_STORE_PY = (
    REPO_ROOT
    / "platform"
    / "src"
    / "codestrata_platform"
    / "community_cloud_api"
    / "data_lake"
    / "infrastructure"
    / "s3_store.py"
)

_FORBIDDEN_PROTOCOL_METHODS = (
    "delete",
    "delete_object",
    "list",
    "list_objects",
    "list_bucket",
    "copy_object",
    "put_bucket",
    "get_bucket",
    "admin",
)


def _protocol_method_names() -> set[str]:
    source = PORTS_PY.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(PORTS_PY))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "CommunityDataLakeStore":
            methods: set[str] = set()
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.add(item.name)
            return methods
    raise AssertionError("CommunityDataLakeStore Protocol not found")


def test_protocol_exposes_projected_object_puts_and_convenience_helpers() -> None:
    methods = _protocol_method_names()
    assert methods == {
        "put_immutable_event",
        "put_immutable_storage_object",
        "put_immutable_quarantine_object",
        "quarantine_event",
    }


def test_protocol_does_not_expose_list_delete_or_admin() -> None:
    methods = _protocol_method_names()
    for forbidden in _FORBIDDEN_PROTOCOL_METHODS:
        assert not any(forbidden in name for name in methods), forbidden


def test_in_memory_store_may_have_test_helpers_beyond_protocol() -> None:
    """InMemory helpers are allowed; Protocol surface stays minimal."""

    assert hasattr(InMemoryCommunityDataLakeStore, "get_accepted_content")
    assert hasattr(InMemoryCommunityDataLakeStore, "accepted_object_keys")
    assert _protocol_method_names() == {
        "put_immutable_event",
        "put_immutable_storage_object",
        "put_immutable_quarantine_object",
        "quarantine_event",
    }


def test_s3_store_client_calls_limited_to_put_and_head() -> None:
    source = S3_STORE_PY.read_text(encoding="utf-8")
    client_calls = re.findall(r"self\.client\.(\w+)\(", source)
    assert client_calls, "expected self.client.* calls in s3_store.py"
    assert set(client_calls) == {"put_object", "head_object"}


def test_s3_store_does_not_reference_list_or_delete_client_methods() -> None:
    source = S3_STORE_PY.read_text(encoding="utf-8")
    for forbidden in ("list_objects", "list_objects_v2", "delete_object", "delete_objects"):
        assert f"client.{forbidden}" not in source
        assert f'self.client.{forbidden}' not in source
