"""Request correlation middleware for operator diagnostics."""

from __future__ import annotations

import re
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

REQUEST_ID_HEADER = "X-Request-Id"
CORRELATION_ID_HEADER = "X-Correlation-Id"
_SAFE_ID = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")
_CallNext = Callable[[Request], Awaitable[Response]]


def _normalize_id(value: str | None) -> str | None:
    if value is None:
        return None
    compact = value.strip()
    if not compact or not _SAFE_ID.fullmatch(compact):
        return None
    return compact


def resolve_request_id(request: Request) -> str:
    existing = getattr(request.state, "request_id", None)
    if isinstance(existing, str) and existing:
        return existing
    return "unknown"


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """Accept or mint request/correlation IDs and echo them on the response."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: _CallNext) -> Response:
        request_id = _normalize_id(request.headers.get(REQUEST_ID_HEADER)) or str(uuid.uuid4())
        correlation_id = (
            _normalize_id(request.headers.get(CORRELATION_ID_HEADER)) or request_id
        )
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response
