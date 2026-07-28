"""Global exception mapping for the Platform REST API."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from codestrata_platform.api.dto.common import ErrorDetailDto, ErrorResponseDto
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


def _error_body(*, code: str, message: str, details: dict[str, object] | None = None) -> dict:
    return ErrorResponseDto(
        error=ErrorDetailDto(code=code, message=message, details=details)
    ).model_dump(mode="json")


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
                details={"errors": exc.errors()},
            ),
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(_request: Request, exc: ValueError) -> JSONResponse:
        from codestrata.security.redaction import redact_secrets

        return JSONResponse(
            status_code=400,
            content=_error_body(code="value_error", message=redact_secrets(str(exc))),
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(_request: Request, _exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=_error_body(
                code="internal_server_error",
                message="An unexpected error occurred",
            ),
        )
