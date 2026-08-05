"""Fail-closed classification of existing-object conflicts (Slice 8.2).

Fail-closed by design: an existing object with a missing or malformed
digest is always treated as a :class:`~...enums.StorageWriteStatus.CONFLICT`,
never as ``ALREADY_EXISTS``. This intentionally forfeits idempotent-replay
convenience in the (rare, anomalous) case where an existing object's digest
cannot be read or parsed, in favor of never silently accepting a write next
to material we cannot prove is identical.
"""

from __future__ import annotations

import re

from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus

_CONTENT_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def is_valid_content_digest(value: str) -> bool:
    """Return ``True`` only for a well-formed ``sha256:`` + 64 lowercase hex digest."""

    return bool(value) and bool(_CONTENT_DIGEST_RE.match(value))


def classify_existing_object(
    *,
    requested_digest: str,
    stored_digest: str | None,
) -> StorageWriteStatus:
    """Classify a write against an object that already exists at the same key.

    - ``stored_digest`` missing or malformed -> ``CONFLICT`` (fail-closed;
      never ``ALREADY_EXISTS``).
    - ``requested_digest`` malformed -> ``CONFLICT``.
    - Digests match (case-insensitive) -> ``ALREADY_EXISTS``.
    - Digests differ -> ``CONFLICT``.
    """

    if stored_digest is None or not is_valid_content_digest(stored_digest):
        return StorageWriteStatus.CONFLICT
    if not is_valid_content_digest(requested_digest):
        return StorageWriteStatus.CONFLICT
    if stored_digest.lower() == requested_digest.lower():
        return StorageWriteStatus.ALREADY_EXISTS
    return StorageWriteStatus.CONFLICT
