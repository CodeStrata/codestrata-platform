"""Safe logging diagnostics derived from validation/payload outcomes."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.logging.models import LoggingDiagnostic
from codestrata_platform.community_cloud_api.payload_limits.models import (
    PayloadLimitResult,
)
from codestrata_platform.community_cloud_api.validation.models import (
    RequestValidationResult,
)


def validation_logging_diagnostic(
    *,
    route_name: str,
    result: RequestValidationResult,
) -> LoggingDiagnostic | None:
    if result.valid or not result.error_code:
        return None
    return LoggingDiagnostic(
        event_type="validation_failed",
        error_code=result.error_code,
        route_name=route_name,
    )


def payload_logging_diagnostic(
    *,
    route_name: str,
    result: PayloadLimitResult,
) -> LoggingDiagnostic | None:
    if result.ok or not result.error_code:
        return None
    return LoggingDiagnostic(
        event_type="payload_rejected",
        error_code=result.error_code,
        route_name=route_name,
    )
