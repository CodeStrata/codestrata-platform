"""Shared-secret API access gate (not a full identity platform).

Development may run without a key. Production fails closed unless an API key is
configured. When a key is configured, every non-health/readiness request must
present it. OpenAPI docs are public only outside production.
"""

from __future__ import annotations

import hmac
import os
from collections.abc import Awaitable, Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

from codestrata_platform.api.dto.common import ErrorDetailDto, ErrorResponseDto

PLATFORM_ENV_VAR = "CODESTRATA_PLATFORM_ENV"
PLATFORM_API_KEY_ENV = "CODESTRATA_PLATFORM_API_KEY"
_PRODUCTION_ENVS = frozenset({"production", "prod"})
_PUBLIC_PATHS = frozenset({"/health", "/ready"})
_DOCS_PATHS = frozenset(
    {
        "/docs",
        "/openapi.json",
        "/redoc",
        "/api/docs",
        "/api/openapi.yaml",
        "/api/openapi.json",
    }
)
_CallNext = Callable[[Request], Awaitable[Response]]


def _is_docs_path(path: str) -> bool:
    if path in _DOCS_PATHS:
        return True
    return path.startswith("/api/docs/")


def resolve_platform_env() -> str:
    return os.environ.get(PLATFORM_ENV_VAR, "development").strip().lower() or "development"


def resolve_platform_api_key() -> str | None:
    key = os.environ.get(PLATFORM_API_KEY_ENV, "").strip()
    return key or None


def assert_production_auth_configuration() -> None:
    """Fail closed when production would otherwise run without authentication."""

    if resolve_platform_env() not in _PRODUCTION_ENVS:
        return
    if resolve_platform_api_key() is None:
        raise RuntimeError(
            f"CodeStrata Platform production requires {PLATFORM_API_KEY_ENV}. "
            f"Set {PLATFORM_ENV_VAR}=development for local use, or configure a "
            "shared API key before starting the API."
        )


def _unauthorized(message: str) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content=ErrorResponseDto(
            error=ErrorDetailDto(code="unauthorized", message=message)
        ).model_dump(mode="json"),
    )


class PlatformApiKeyMiddleware(BaseHTTPMiddleware):
    """Require Authorization: Bearer <api-key> when an API key is configured."""

    def __init__(self, app: ASGIApp, *, api_key: str | None = None) -> None:
        super().__init__(app)
        self._api_key = api_key if api_key is not None else resolve_platform_api_key()

    async def dispatch(self, request: Request, call_next: _CallNext) -> Response:
        if self._api_key is None:
            return await call_next(request)
        path = request.url.path
        if path in _PUBLIC_PATHS:
            return await call_next(request)
        # Keep OpenAPI browsable in non-production; require the key in production.
        if _is_docs_path(path) and resolve_platform_env() not in _PRODUCTION_ENVS:
            return await call_next(request)
        authorization = request.headers.get("authorization", "")
        scheme, _, credential = authorization.partition(" ")
        if scheme.lower() != "bearer" or not credential.strip():
            return _unauthorized(
                "Missing or invalid Authorization header. "
                f"Send Authorization: Bearer <key> using {PLATFORM_API_KEY_ENV}. "
                "This is the CodeStrata Platform API key, not an AI provider credential."
            )
        if not hmac.compare_digest(credential.strip(), self._api_key):
            return _unauthorized(
                "Invalid CodeStrata Platform API key. "
                f"Verify {PLATFORM_API_KEY_ENV}. "
                "Do not use AI provider tokens (Bedrock/OpenAI/etc.) here."
            )
        return await call_next(request)
