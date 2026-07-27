"""Shared API DTOs: pagination and errors."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetailDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    details: dict[str, object] | None = None


class ErrorResponseDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ErrorDetailDto


class PageMetaDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int = Field(ge=1, description="1-based page number")
    size: int = Field(ge=1, le=500, description="Page size")
    total: int = Field(ge=0)
    sort: str | None = None
    next: int | None = Field(default=None, description="Next page number, if any")
    previous: int | None = Field(default=None, description="Previous page number, if any")


class PageResponseDto[T](BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[T]
    pagination: PageMetaDto
