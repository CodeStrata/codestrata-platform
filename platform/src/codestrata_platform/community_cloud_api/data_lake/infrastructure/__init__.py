"""Community Data Lake infrastructure adapters (Slice 8.2).

This subpackage is the ONLY place under
``codestrata_platform.community_cloud_api.data_lake`` allowed to import
``boto3``. It is production-capable but **unwired**: nothing in ``app.py``,
``deployment/wiring.py``, ``deployment/settings.py``, or any endpoint
service constructs or calls anything in this subpackage in this slice.

No exactly-once delivery guarantee is claimed by any adapter here. See
``platform/docs/community-cloud-api/immutable-raw-storage.md`` for the full
storage contract this subpackage implements.
"""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.infrastructure.client import (
    S3ClientPort,
    create_boto3_s3_client,
)
from codestrata_platform.community_cloud_api.data_lake.infrastructure.configuration import (
    S3ConfigurationError,
    S3DataLakeStoreConfiguration,
)
from codestrata_platform.community_cloud_api.data_lake.infrastructure.diagnostics import (
    safe_s3_storage_diagnostic,
)
from codestrata_platform.community_cloud_api.data_lake.infrastructure.error_mapping import (
    is_transient_storage_error,
    map_s3_exception,
)
from codestrata_platform.community_cloud_api.data_lake.infrastructure.s3_store import (
    CommunityDataLakeS3Store,
)
from codestrata_platform.community_cloud_api.data_lake.infrastructure.unavailable_store import (
    UnavailableCommunityDataLakeStore,
)

__all__ = [
    "CommunityDataLakeS3Store",
    "S3ClientPort",
    "S3ConfigurationError",
    "S3DataLakeStoreConfiguration",
    "UnavailableCommunityDataLakeStore",
    "create_boto3_s3_client",
    "is_transient_storage_error",
    "map_s3_exception",
    "safe_s3_storage_diagnostic",
]
