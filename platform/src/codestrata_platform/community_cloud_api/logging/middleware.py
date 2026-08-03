"""Request-lifecycle logging helpers for Community Cloud dispatch.

Not a global ASGI middleware that inspects bodies or forwarding headers.
Logging is invoked explicitly from the application dispatch path.
"""

from __future__ import annotations

from codestrata_platform.community_cloud_api.logging.context import (
    LoggingContext,
    create_logging_context,
)
from codestrata_platform.community_cloud_api.logging.logger import CommunityCloudLogger
from codestrata_platform.community_cloud_api.logging.models import CommunityLoggingPolicy


def begin_request_logging(
    *,
    logger: CommunityCloudLogger,
    policy: CommunityLoggingPolicy,
    api_version: str,
    method: str,
    route: str,
    client_request_id: str | None,
    client_host: str | None,
) -> LoggingContext:
    """Create logging context and emit request_received (fail-safe)."""

    context = create_logging_context(
        policy=policy,
        api_version=api_version,
        method=method,
        route=route,
        client_request_id=client_request_id,
        clock_ms=logger.clock_ms,
        request_id_factory=logger.request_id_factory,
        client_host=client_host,
    )
    logger.request_received(context)
    return context


def finish_request_logging(
    *,
    logger: CommunityCloudLogger,
    context: LoggingContext,
    status_code: int,
    error_code: str | None = None,
) -> None:
    """Emit terminal completion/failure event with duration."""

    try:
        duration = max(0, int(logger.clock_ms()) - int(context.started_ms))
    except Exception:  # noqa: BLE001
        duration = 0
    if 200 <= int(status_code) < 400:
        logger.request_completed(
            context, status_code=status_code, duration_ms=duration
        )
    else:
        logger.request_failed(
            context,
            status_code=status_code,
            duration_ms=duration,
            error_code=error_code,
        )


def asgi_client_host(scope_client: tuple[str, int] | None) -> str | None:
    """Return ASGI client host only — never parse X-Forwarded-For."""

    if scope_client is None:
        return None
    host = scope_client[0]
    return host if isinstance(host, str) and host.strip() else None
