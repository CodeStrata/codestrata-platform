"""boto3 client factory tests (Slice 8.2 infrastructure — only module allowed to import boto3)."""

from __future__ import annotations

import ast
from pathlib import Path

from codestrata_platform.community_cloud_api.data_lake.infrastructure.client import (
    S3ClientPort,
    create_boto3_s3_client,
)
from codestrata_platform.community_cloud_api.data_lake.infrastructure.configuration import (
    S3DataLakeStoreConfiguration,
)


def test_create_boto3_s3_client_builds_a_client_with_required_methods() -> None:
    config = S3DataLakeStoreConfiguration(bucket_name="valid-bucket-name")
    client = create_boto3_s3_client(config)
    assert hasattr(client, "put_object")
    assert hasattr(client, "head_object")


def test_create_boto3_s3_client_respects_allowed_endpoint_override() -> None:
    config = S3DataLakeStoreConfiguration(
        bucket_name="valid-bucket-name",
        endpoint_url="http://localhost:9000",
        allow_endpoint_override=True,
    )
    client = create_boto3_s3_client(config)
    assert client.meta.endpoint_url.rstrip("/") == "http://localhost:9000"


def test_s3_client_port_protocol_is_satisfied_by_a_minimal_duck_type() -> None:
    class Minimal:
        def put_object(self, **kwargs: object) -> None:
            return None

        def head_object(self, **kwargs: object) -> None:
            return None

    minimal: S3ClientPort = Minimal()
    assert hasattr(minimal, "put_object")
    assert hasattr(minimal, "head_object")


def test_client_module_imports_boto3_lazily_inside_function_only() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    client_path = (
        repo_root
        / "platform"
        / "src"
        / "codestrata_platform"
        / "community_cloud_api"
        / "data_lake"
        / "infrastructure"
        / "client.py"
    )
    text = client_path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(client_path))
    module_level_imports = [
        node
        for node in ast.iter_child_nodes(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        and any(getattr(alias, "name", "") == "boto3" or node.__dict__.get("module") == "boto3" for alias in node.names)
    ]
    assert module_level_imports == []
