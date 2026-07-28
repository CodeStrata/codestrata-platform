"""Shared API DTOs: pagination and errors."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetailDto(BaseModel):
    """Stable error payload for CodeStrata Platform REST responses."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(description="Machine-readable error code (stable for clients)")
    message: str = Field(description="Human-readable guidance; safe for operators")
    details: dict[str, object] | None = Field(
        default=None,
        description="Optional structured detail (for example bounded validation errors)",
    )


class ErrorResponseDto(BaseModel):
    """Standard Platform API error envelope."""

    model_config = ConfigDict(extra="forbid")

    error: ErrorDetailDto = Field(description="Error detail")


class PageMetaDto(BaseModel):
    """Pagination metadata for list endpoints."""

    model_config = ConfigDict(extra="forbid")

    page: int = Field(ge=1, description="1-based page number")
    size: int = Field(ge=1, le=500, description="Page size")
    total: int = Field(ge=0, description="Total matching items")
    sort: str | None = Field(default=None, description="Applied sort key, if any")
    next: int | None = Field(default=None, description="Next page number, if any")
    previous: int | None = Field(default=None, description="Previous page number, if any")


class PageResponseDto[T](BaseModel):
    """Paginated list response."""

    model_config = ConfigDict(extra="forbid")

    items: list[T] = Field(description="Page items")
    pagination: PageMetaDto = Field(description="Pagination metadata")
