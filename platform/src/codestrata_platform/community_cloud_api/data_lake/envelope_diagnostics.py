"""Safe Slice 8.3 envelope error diagnostics — never echoes payload or secrets.

Mirrors the shape of :mod:`.diagnostics` (Slice 8.1/8.2) but scoped to the
new :class:`~.envelope_validation.EnvelopeBuildError` taxonomy.
"""

from __future__ import annotations

from typing import Any

from codestrata_platform.community_cloud_api.data_lake.envelope_models import EnvelopeErrorCode
from codestrata_platform.community_cloud_api.data_lake.envelope_validation import EnvelopeBuildError

_MAX_DETAIL_LENGTH = 64


def safe_envelope_error_diagnostic(error: EnvelopeBuildError) -> dict[str, Any]:
    """Bounded, stable diagnostic dict — error code and a short detail token only."""

    payload: dict[str, Any] = {"code": error.code.value}
    if error.detail:
        payload["detail"] = str(error.detail)[:_MAX_DETAIL_LENGTH]
    return {key: payload[key] for key in sorted(payload)}


def safe_error_code_for_exception(exc: BaseException) -> EnvelopeErrorCode:
    """Map any exception to a bounded :class:`EnvelopeErrorCode`, defaulting fail-closed."""

    if isinstance(exc, EnvelopeBuildError):
        return exc.code
    return EnvelopeErrorCode.INVALID_ENVELOPE
