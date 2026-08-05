"""S3 client port and lazy boto3 client factory (Slice 8.2 infrastructure).

This module is the ONLY place under
``codestrata_platform.community_cloud_api.data_lake`` allowed to import
``boto3`` — every domain module (``data_lake/*.py`` at the package root)
remains boto3-free. ``boto3`` is imported lazily inside
:func:`create_boto3_s3_client`'s body, so simply importing this module never
requires ``boto3`` to be installed unless the factory is actually called.

IMPORTANT: no production wiring path (``app.py``, ``deployment/wiring.py``,
or any endpoint service) calls :func:`create_boto3_s3_client` in this slice.
The adapter is production-capable but intentionally unwired.
"""

from __future__ import annotations

from typing import Any, Protocol

from codestrata_platform.community_cloud_api.data_lake.infrastructure.configuration import (
    S3DataLakeStoreConfiguration,
)


class S3ClientPort(Protocol):
    """Minimal boto3 S3 client surface used by :class:`.s3_store.CommunityDataLakeS3Store`."""

    def put_object(self, **kwargs: Any) -> Any: ...

    def head_object(self, **kwargs: Any) -> Any: ...


def create_boto3_s3_client(config: S3DataLakeStoreConfiguration) -> Any:
    """Build a real boto3 S3 client from validated configuration.

    Not called by any production wiring path in this slice. Callers that do
    invoke this factory (e.g. a future Slice 8.3 wiring change, or an
    integration test opting in explicitly) must have ``boto3`` installed.
    """

    import boto3
    from botocore.config import Config as BotoConfig

    config.validate()
    boto_config = BotoConfig(
        connect_timeout=config.connect_timeout_seconds,
        read_timeout=config.read_timeout_seconds,
        retries={"max_attempts": config.max_attempts, "mode": "standard"},
    )
    client_kwargs: dict[str, Any] = {"config": boto_config}
    if config.endpoint_url is not None and config.allow_endpoint_override:
        client_kwargs["endpoint_url"] = config.endpoint_url
    return boto3.client("s3", **client_kwargs)
