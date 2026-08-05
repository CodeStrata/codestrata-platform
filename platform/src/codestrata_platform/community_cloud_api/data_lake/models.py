"""Thin re-export hub for Data Lake domain models (Slice 8.1 / 8.9).

Kept intentionally minimal: the envelope lives in :mod:`.envelopes`, the
storage-facing write result lives in :mod:`.ports`, and the quarantine
record lives in :mod:`.quarantine_models` (re-exported via :mod:`.ports`
for backward-compatible imports).
"""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.envelopes import DataLakeEnvelope
from codestrata_platform.community_cloud_api.data_lake.ports import (
    QuarantineRecord,
    StorageWriteResult,
)

__all__ = ["DataLakeEnvelope", "QuarantineRecord", "StorageWriteResult"]
