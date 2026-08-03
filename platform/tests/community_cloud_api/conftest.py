"""Shared fixtures for Community Cloud API validation tests (test-only routes)."""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

from typing import Annotated, Literal

import pytest
from fastapi.testclient import TestClient
from pydantic import Field

from codestrata_platform.community_cloud_api import (
    RouteRegistry,
    RouteSpec,
    create_community_cloud_app,
)
from codestrata_platform.community_cloud_api.models import RequestContext
from codestrata_platform.community_cloud_api.serialization import build_json_response
from codestrata_platform.community_cloud_api.validation import (
    ApiClientName,
    ApiEventName,
    ApiSafeLabel,
    ApiStrictBool,
    ApiStrictInt,
    BodyPolicy,
    CommunityApiRequestModel,
    RequestSchemaDescriptor,
    ValidationFieldError,
    field_error,
)
from starlette.responses import Response



class ValidationEnvelopeRequest(CommunityApiRequestModel):
    """Private test-only schema — not a production event contract."""

    event_type: ApiEventName
    client_name: ApiClientName
    count: ApiStrictInt = 1
    enabled: ApiStrictBool = True
    label: ApiSafeLabel | None = None
    tags: Annotated[list[ApiSafeLabel], Field(max_length=3)] = Field(default_factory=list)
    attributes: Annotated[dict[str, ApiSafeLabel], Field(max_length=3)] = Field(
        default_factory=dict
    )
    mode: Literal["alpha", "beta"] = "alpha"


TEST_SCHEMA = RequestSchemaDescriptor(
    schema_id="community.test.validation-envelope",
    schema_version="1.0",
    model_type=ValidationEnvelopeRequest,
    body_policy=BodyPolicy.REQUIRED,
    max_error_details=20,
)


def _semantic_reject_beta(model: CommunityApiRequestModel) -> list[ValidationFieldError]:
    assert isinstance(model, ValidationEnvelopeRequest)
    if model.mode == "beta":
        return [field_error("mode", "invalid_enum")]
    return []


TEST_SCHEMA_WITH_SEMANTIC = RequestSchemaDescriptor(
    schema_id="community.test.validation-envelope-semantic",
    schema_version="1.0",
    model_type=ValidationEnvelopeRequest,
    body_policy=BodyPolicy.REQUIRED,
    semantic_validator=_semantic_reject_beta,
)


OPTIONAL_SCHEMA = RequestSchemaDescriptor(
    schema_id="community.test.validation-optional",
    schema_version="1.0",
    model_type=ValidationEnvelopeRequest,
    body_policy=BodyPolicy.OPTIONAL,
)


def _handle_validated(context: RequestContext) -> Response:
    body = context.validated_request
    assert isinstance(body, ValidationEnvelopeRequest)
    return build_json_response(
        {"accepted": True, "event_type": body.event_type},
        status_code=200,
        api_version="v1",
        request_id=context.request_id,
    )


def _handle_optional(context: RequestContext) -> Response:
    if context.validated_request is None:
        payload = {"accepted": True, "body": None}
    else:
        assert isinstance(context.validated_request, ValidationEnvelopeRequest)
        payload = {"accepted": True, "body": "present"}
    return build_json_response(
        payload,
        status_code=200,
        api_version="v1",
        request_id=context.request_id,
    )


def build_validation_test_registry(
    *,
    with_semantic: bool = False,
    with_optional: bool = False,
) -> RouteRegistry:
    registry = RouteRegistry.foundation_v1()
    schema = TEST_SCHEMA_WITH_SEMANTIC if with_semantic else TEST_SCHEMA
    registry.register(
        RouteSpec(
            version="v1",
            method="POST",
            path="/_test/validation-envelope",
            name="test.validation_envelope",
            authentication_group="public",
        ),
        handler=_handle_validated,
        request_schema=schema,
    )
    if with_optional:
        registry.register(
            RouteSpec(
                version="v1",
                method="POST",
                path="/_test/validation-optional",
                name="test.validation_optional",
                authentication_group="public",
            ),
            handler=_handle_optional,
            request_schema=OPTIONAL_SCHEMA,
        )
    return registry


@pytest.fixture()
def validation_client() -> TestClient:
    return TestClient(
        create_community_cloud_app(
            registry=build_validation_test_registry(),
            authentication_policy=disabled_authentication_policy(),
        )
    )


@pytest.fixture()
def semantic_client() -> TestClient:
    return TestClient(
        create_community_cloud_app(
            registry=build_validation_test_registry(with_semantic=True),
            authentication_policy=disabled_authentication_policy(),
        )
    )


@pytest.fixture()
def optional_client() -> TestClient:
    return TestClient(
        create_community_cloud_app(
            registry=build_validation_test_registry(with_optional=True),
            authentication_policy=disabled_authentication_policy(),
        )
    )


VALID_BODY = {
    "event_type": "test.event",
    "client_name": "codestrata-cli",
    "count": 2,
    "enabled": True,
    "label": "ok-label",
    "tags": ["a", "b"],
    "attributes": {"k": "v"},
    "mode": "alpha",
}
