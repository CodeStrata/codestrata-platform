"""Bounded, privacy-safe error taxonomy for immutable raw storage (Slice 8.2).

``safe_code`` values are short, stable identifiers only — never exception
text, bucket/key names, or AWS request ids. See
:mod:`codestrata_platform.community_cloud_api.data_lake.diagnostics` for the
general-purpose ``sanitize_exception_message`` helper used elsewhere in this
package.
"""

from __future__ import annotations

from enum import Enum


class StorageErrorCategory(str, Enum):
    """Bounded classification of why an immutable write attempt did not succeed."""

    VALIDATION = "validation"
    PRECONDITION = "precondition"
    ACCESS_DENIED = "access_denied"
    TRANSIENT = "transient"
    TIMEOUT = "timeout"
    CHECKSUM_MISMATCH = "checksum_mismatch"
    NOT_IMPLEMENTED = "not_implemented"
    UNKNOWN = "unknown"


class DataLakeStorageError(Exception):
    """Raised for storage-boundary failures that must carry a bounded, safe code.

    ``safe_code`` must be a short, stable identifier (e.g.
    ``"storage_access_denied"``) — never raw exception text, bucket/key
    names, or AWS request ids.
    """

    def __init__(self, category: StorageErrorCategory, safe_code: str) -> None:
        super().__init__(safe_code)
        self.category = category
        self.safe_code = safe_code

    def __repr__(self) -> str:  # pragma: no cover - debugging aid only
        return f"DataLakeStorageError(category={self.category.value!r}, safe_code={self.safe_code!r})"
