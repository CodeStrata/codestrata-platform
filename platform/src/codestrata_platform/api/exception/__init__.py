"""Global exception mapping for the Platform REST API."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from codestrata.security.database_url import sanitize_exception_message
from codestrata_platform.api.correlation import resolve_request_id
from codestrata_platform.api.dto.common import ErrorDetailDto, ErrorResponseDto
from codestrata_platform.application.common.diagnostics import classify_exception
from codestrata_platform.application.common.errors import (
    ApplicationError,
    ConflictError,
    NotFoundError,
    PayloadTooLargeError,
    ValidationError,
)
from codestrata_platform.domain.errors import (
    DomainError,
    InvalidStateTransitionError,
    InvalidValueError,
)

logger = logging.getLogger(__name__)

_MAX_VALIDATION_ERRORS = 40


def _safe_message(exc: BaseException | str) -> str:
    return sanitize_exception_message(str(exc))


def _error_body(*, code: str, message: str, details: dict[str, object] | None = None) -> dict:
    return ErrorResponseDto(
        error=ErrorDetailDto(code=code, message=_safe_message(message), details=details)
    ).model_dump(mode="json")


def _bounded_validation_details(errors: list[dict]) -> dict[str, object]:
    bounded: list[dict[str, object]] = []
    for item in errors[:_MAX_VALIDATION_ERRORS]:
        entry: dict[str, object] = {}
        for key, value in item.items():
            if key == "input":
                continue
            if key == "ctx" and isinstance(value, dict):
                continue
            if key == "msg":
                entry[key] = _safe_message(value)
            else:
                entry[key] = value
        bounded.append(entry)
    payload: dict[str, object] = {"errors": bounded}
    if len(errors) > _MAX_VALIDATION_ERRORS:
        payload["truncated"] = True
        payload["total"] = len(errors)
    return payload


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content=_error_body(
                code=exc.reason_code or "not_found",
                message=str(exc),
            ),
        )

    @app.exception_handler(ConflictError)
    async def conflict_handler(_request: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content=_error_body(
                code=exc.reason_code or "conflict",
                message=str(exc),
            ),
        )

    @app.exception_handler(ValidationError)
    async def validation_handler(_request: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_error_body(
                code=exc.reason_code or "validation_error",
                message=str(exc),
            ),
        )

    @app.exception_handler(PayloadTooLargeError)
    async def payload_too_large_handler(
        _request: Request,
        exc: PayloadTooLargeError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=413,
            content=_error_body(
                code=exc.reason_code or "payload_too_large",
                message=str(exc),
            ),
        )

    @app.exception_handler(InvalidValueError)
    async def invalid_value_handler(_request: Request, exc: InvalidValueError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=_error_body(
                code=exc.reason_code or "invalid_value",
                message=str(exc),
            ),
        )

    @app.exception_handler(InvalidStateTransitionError)
    async def invalid_state_handler(
        _request: Request,
        exc: InvalidStateTransitionError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content=_error_body(
                code=exc.reason_code or "invalid_state_transition",
                message=str(exc),
            ),
        )

    @app.exception_handler(DomainError)
    async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=_error_body(
                code=exc.reason_code or "domain_error",
                message=str(exc),
            ),
        )

    @app.exception_handler(ApplicationError)
    async def application_error_handler(
        _request: Request,
        exc: ApplicationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=_error_body(
                code=exc.reason_code or "application_error",
                message=str(exc),
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_error_body(
                code="request_validation_error",
                message="Request validation failed",
                details=_bounded_validation_details(list(exc.errors())),
            ),
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(_request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=_error_body(code="value_error", message=str(exc)),
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        import traceback

        request_id = resolve_request_id(request)
        correlation_id = getattr(request.state, "correlation_id", request_id)
        safe_trace = sanitize_exception_message(
            "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        )
        logger.error(
            "Unhandled API exception category=%s request_id=%s "
            "correlation_id=%s path=%s\n%s",
            classify_exception(exc),
            request_id,
            correlation_id,
            request.url.path,
            safe_trace,
        )
        return JSONResponse(
            status_code=500,
            content=_error_body(
                code="internal_server_error",
                message="An unexpected error occurred",
            ),
            headers={
                "X-Request-Id": request_id,
                "X-Correlation-Id": str(correlation_id),
            },
        )
