"""Safe S3 storage diagnostics (Slice 8.2 infrastructure).

Never includes bucket names, object keys, AWS request ids, or raw AWS
exception messages — bounded status/category/stream fields only.
"""

from __future__ import annotations

from typing import Any

from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.errors import StorageErrorCategory


def safe_s3_storage_diagnostic(
    status: StorageWriteStatus,
    category: StorageErrorCategory | None = None,
    event_stream: str | None = None,
) -> dict[str, Any]:
    """Bounded, stable diagnostic dict for one S3 write attempt outcome."""

    payload: dict[str, Any] = {"status": status.value}
    if category is not None:
        payload["category"] = category.value
    if event_stream is not None:
        payload["event_stream"] = event_stream
    return {key: payload[key] for key in sorted(payload)}
