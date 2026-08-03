"""Request validation models, descriptors, and results."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict

from codestrata_platform.community_cloud_api.constants import (
    COMMUNITY_REQUEST_VALIDATION_POLICY_VERSION,
)

TModel = TypeVar("TModel", bound="CommunityApiRequestModel")


class BodyPolicy(str, Enum):
    """Explicit request-body presence policy (not inferred from HTTP method)."""

    FORBIDDEN = "forbidden"
    REQUIRED = "required"
    OPTIONAL = "optional"


class UnknownFieldPolicy(str, Enum):
    """Unknown JSON field handling. Default is reject."""

    REJECT = "reject"


class CommunityApiRequestModel(BaseModel):
    """Base model for Community Cloud JSON request bodies.

    Frozen, strict, and fail-closed on unknown fields. Not an Engine contract.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        arbitrary_types_allowed=False,
        validate_assignment=False,
        populate_by_name=True,
        ser_json_timedelta="iso8601",
    )

    def to_stable_dict(self) -> dict[str, Any]:
        data = self.model_dump(by_alias=True, mode="json")
        return {str(key): data[key] for key in sorted(data, key=str)}


SemanticValidator = Callable[[CommunityApiRequestModel], Sequence["ValidationFieldError"]]


@dataclass(frozen=True, slots=True)
class ValidationFieldError:
    """Safe field-level validation detail — never includes submitted values."""

    field: str
    code: str
    message: str

    def __post_init__(self) -> None:
        field = (self.field or "").strip()
        code = (self.code or "").strip()
        message = " ".join((self.message or "").split())
        if not field:
            raise ValueError("field path is required")
        if not code:
            raise ValueError("field error code is required")
        if not message:
            raise ValueError("field error message is required")
        object.__setattr__(self, "field", field)
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "message", message)

    def to_stable_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "field": self.field,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class RequestSchemaDescriptor:
    """Stable identity and policy for a route request schema."""

    schema_id: str
    schema_version: str
    model_type: type[CommunityApiRequestModel] | None
    body_policy: BodyPolicy
    unknown_field_policy: UnknownFieldPolicy = UnknownFieldPolicy.REJECT
    validation_policy_version: str = COMMUNITY_REQUEST_VALIDATION_POLICY_VERSION
    max_error_details: int = 20
    semantic_validator: SemanticValidator | None = None

    def __post_init__(self) -> None:
        schema_id = (self.schema_id or "").strip()
        schema_version = (self.schema_version or "").strip()
        if not schema_id:
            raise ValueError("schema_id is required")
        if not schema_version:
            raise ValueError("schema_version is required")
        if not isinstance(self.body_policy, BodyPolicy):
            raise ValueError("body_policy must be a BodyPolicy")
        if not isinstance(self.unknown_field_policy, UnknownFieldPolicy):
            raise ValueError("unknown_field_policy must be an UnknownFieldPolicy")
        if self.max_error_details < 1 or self.max_error_details > 100:
            raise ValueError("max_error_details must be between 1 and 100")
        if self.body_policy != BodyPolicy.FORBIDDEN and self.model_type is None:
            raise ValueError("model_type is required unless body_policy is forbidden")
        if self.model_type is not None and not issubclass(
            self.model_type, CommunityApiRequestModel
        ):
            raise ValueError("model_type must subclass CommunityApiRequestModel")
        if self.unknown_field_policy is not UnknownFieldPolicy.REJECT:
            raise ValueError("only reject unknown-field policy is supported in policy 1.0")
        object.__setattr__(self, "schema_id", schema_id)
        object.__setattr__(self, "schema_version", schema_version)

    def identity_key(self) -> tuple[str, str]:
        return (self.schema_id, self.schema_version)

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "body_policy": self.body_policy.value,
            "max_error_details": self.max_error_details,
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "unknown_field_policy": self.unknown_field_policy.value,
            "validation_policy_version": self.validation_policy_version,
        }


@dataclass(frozen=True, slots=True)
class RequestValidationResult:
    """Internal validation outcome — never partial on success."""

    valid: bool
    model: CommunityApiRequestModel | None
    errors: tuple[ValidationFieldError, ...]
    schema_id: str
    schema_version: str
    error_code: str | None = None
    http_status: int | None = None
    truncated_error_count: int = 0

    @classmethod
    def ok(
        cls,
        model: CommunityApiRequestModel | None,
        *,
        schema_id: str,
        schema_version: str,
    ) -> RequestValidationResult:
        return cls(
            valid=True,
            model=model,
            errors=(),
            schema_id=schema_id,
            schema_version=schema_version,
        )

    @classmethod
    def fail(
        cls,
        *,
        error_code: str,
        http_status: int,
        schema_id: str,
        schema_version: str,
        errors: Sequence[ValidationFieldError] = (),
        truncated_error_count: int = 0,
    ) -> RequestValidationResult:
        return cls(
            valid=False,
            model=None,
            errors=tuple(errors),
            schema_id=schema_id,
            schema_version=schema_version,
            error_code=error_code,
            http_status=http_status,
            truncated_error_count=int(truncated_error_count),
        )


@dataclass(frozen=True, slots=True)
class SafeValidationDiagnostic:
    """Internal diagnostic for future structured logging — no raw values."""

    route_name: str
    error_code: str
    field_names: tuple[str, ...]
    error_count: int
    schema_id: str

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "error_count": self.error_count,
            "field_names": list(self.field_names),
            "route_name": self.route_name,
            "schema_id": self.schema_id,
        }


# Marker used by health / no-body routes.
NO_BODY_SCHEMA = RequestSchemaDescriptor(
    schema_id="community.foundation.no-body",
    schema_version="1.0",
    model_type=None,
    body_policy=BodyPolicy.FORBIDDEN,
)
