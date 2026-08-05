"""Safe Community Data Lake storage diagnostics — never echoes payload or secrets."""

from __future__ import annotations

from typing import Any

from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus

_MAX_EXCEPTION_TYPE_NAME_LENGTH = 64


def safe_storage_diagnostic(
    status: StorageWriteStatus,
    reason_code: str | None = None,
) -> dict[str, Any]:
    """Bounded, stable diagnostic dict — status and an optional reason code only."""

    payload: dict[str, Any] = {"status": status.value}
    if reason_code:
        payload["reason_code"] = reason_code
    return {key: payload[key] for key in sorted(payload)}


def sanitize_exception_message(exc: BaseException) -> str:
    """Return a bounded, content-free diagnostic: the exception type name only.

    Never includes ``str(exc)`` — exception messages may echo payload
    fragments, file paths, or other sensitive material raised by validation.
    """

    name = type(exc).__name__
    return name[:_MAX_EXCEPTION_TYPE_NAME_LENGTH]
