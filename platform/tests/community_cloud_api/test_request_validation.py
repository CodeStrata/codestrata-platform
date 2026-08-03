"""Request model, schema descriptor, body policy, and route integration tests."""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

import json

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from codestrata_platform.community_cloud_api import (
    COMMUNITY_REQUEST_VALIDATION_POLICY_VERSION,
    RouteRegistry,
    RouteSpec,
    create_community_cloud_app,
)
from codestrata_platform.community_cloud_api.errors import (
    ERROR_BODY_FORBIDDEN,
    ERROR_BODY_REQUIRED,
    ERROR_INVALID_REQUEST_SCHEMA,
    ERROR_MALFORMED_JSON,
    ERROR_UNSUPPORTED_JSON_SHAPE,
    ERROR_UNSUPPORTED_MEDIA_TYPE,
)
from codestrata_platform.community_cloud_api.serialization import dumps_stable
from codestrata_platform.community_cloud_api.validation import (
    ApiStrictInt,
    BodyPolicy,
    CommunityApiRequestModel,
    RequestSchemaDescriptor,
    UnknownFieldPolicy,
    validate_request_body,
)
from codestrata_platform.community_cloud_api.validation.models import NO_BODY_SCHEMA

from .conftest import (
    VALID_BODY,
    ValidationEnvelopeRequest,
    build_validation_test_registry,
)


def test_base_model_rejects_unknown_fields_and_is_frozen() -> None:
    model = ValidationEnvelopeRequest.model_validate(
        {"event_type": "e", "client_name": "c"}
    )
    with pytest.raises(ValidationError):
        ValidationEnvelopeRequest.model_validate(
            {"event_type": "e", "client_name": "c", "extra": 1}
        )
    with pytest.raises(ValidationError):
        model.event_type = "other"  # type: ignore[misc]


def test_base_model_strict_types_and_deterministic_serialization() -> None:
    with pytest.raises(ValidationError):
        ValidationEnvelopeRequest.model_validate(
            {"event_type": "e", "client_name": "c", "count": "1"}
        )
    with pytest.raises(ValidationError):
        ValidationEnvelopeRequest.model_validate(
            {"event_type": "e", "client_name": "c", "enabled": "true"}
        )
    with pytest.raises(ValidationError):
        ValidationEnvelopeRequest.model_validate(
            {"event_type": "e", "client_name": "c", "count": 1.5}
        )
    left = ValidationEnvelopeRequest.model_validate(
        {"event_type": "e", "client_name": "c", "count": 1}
    )
    right = ValidationEnvelopeRequest.model_validate(
        {"event_type": "e", "client_name": "c", "count": 1}
    )
    assert dumps_stable(left) == dumps_stable(right)
    assert list(left.to_stable_dict().keys()) == sorted(left.to_stable_dict().keys())


def test_schema_descriptor_identity_and_policy() -> None:
    descriptor = RequestSchemaDescriptor(
        schema_id="community.test.validation-envelope",
        schema_version="1.0",
        model_type=ValidationEnvelopeRequest,
        body_policy=BodyPolicy.REQUIRED,
    )
    assert descriptor.identity_key() == (
        "community.test.validation-envelope",
        "1.0",
    )
    assert descriptor.validation_policy_version == COMMUNITY_REQUEST_VALIDATION_POLICY_VERSION
    assert descriptor.unknown_field_policy is UnknownFieldPolicy.REJECT
    assert descriptor.to_stable_dict()["body_policy"] == "required"


def test_schema_descriptor_rejects_unsupported_model() -> None:
    class NotApiModel(CommunityApiRequestModel):
        pass

    class Plain:
        pass

    with pytest.raises(ValueError, match="subclass CommunityApiRequestModel"):
        RequestSchemaDescriptor(
            schema_id="x",
            schema_version="1.0",
            model_type=Plain,  # type: ignore[arg-type]
            body_policy=BodyPolicy.REQUIRED,
        )
    _ = NotApiModel  # valid subclass path covered by ValidationEnvelopeRequest


def test_duplicate_request_schema_binding_rejected() -> None:
    registry = RouteRegistry.foundation_v1()
    spec = RouteSpec(version="v1", method="GET", path="/health", name="health.get")
    with pytest.raises(ValueError, match="duplicate request schema"):
        registry.bind_request_schema(spec, NO_BODY_SCHEMA)


def test_conflicting_schema_version_rejected() -> None:
    registry = RouteRegistry()
    first = RequestSchemaDescriptor(
        schema_id="community.test.same",
        schema_version="1.0",
        model_type=ValidationEnvelopeRequest,
        body_policy=BodyPolicy.REQUIRED,
    )
    second = RequestSchemaDescriptor(
        schema_id="community.test.same",
        schema_version="2.0",
        model_type=ValidationEnvelopeRequest,
        body_policy=BodyPolicy.REQUIRED,
    )
    registry.register(
        RouteSpec(version="v1", method="POST", path="/a", name="a"),
        request_schema=first,
    )
    with pytest.raises(ValueError, match="conflicting schema version"):
        registry.register(
            RouteSpec(version="v1", method="POST", path="/b", name="b"),
            request_schema=second,
        )


def test_body_policy_forbidden() -> None:
    result = validate_request_body(
        descriptor=NO_BODY_SCHEMA,
        body=b'{"x":1}',
        content_type="application/json",
    )
    assert not result.valid
    assert result.error_code == ERROR_BODY_FORBIDDEN
    assert result.http_status == 400


def test_body_policy_required_and_optional() -> None:
    required = RequestSchemaDescriptor(
        schema_id="community.test.req",
        schema_version="1.0",
        model_type=ValidationEnvelopeRequest,
        body_policy=BodyPolicy.REQUIRED,
    )
    optional = RequestSchemaDescriptor(
        schema_id="community.test.opt",
        schema_version="1.0",
        model_type=ValidationEnvelopeRequest,
        body_policy=BodyPolicy.OPTIONAL,
    )
    missing = validate_request_body(
        descriptor=required, body=b"", content_type="application/json"
    )
    assert missing.error_code == ERROR_BODY_REQUIRED
    absent = validate_request_body(
        descriptor=optional, body=b"", content_type="application/json"
    )
    assert absent.valid and absent.model is None
    present = validate_request_body(
        descriptor=optional,
        body=json.dumps(VALID_BODY).encode(),
        content_type="application/json",
    )
    assert present.valid and present.model is not None


def test_unsupported_json_shapes() -> None:
    descriptor = RequestSchemaDescriptor(
        schema_id="community.test.shape",
        schema_version="1.0",
        model_type=ValidationEnvelopeRequest,
        body_policy=BodyPolicy.REQUIRED,
    )
    for payload in (b"null", b"[]", b'"x"', b"1", b"true"):
        result = validate_request_body(
            descriptor=descriptor,
            body=payload,
            content_type="application/json",
        )
        assert result.error_code == ERROR_UNSUPPORTED_JSON_SHAPE
        assert result.http_status == 400


def test_malformed_json() -> None:
    descriptor = RequestSchemaDescriptor(
        schema_id="community.test.malformed",
        schema_version="1.0",
        model_type=ValidationEnvelopeRequest,
        body_policy=BodyPolicy.REQUIRED,
    )
    for payload in (b"{", b'{"a":', b"\xff\xff"):
        result = validate_request_body(
            descriptor=descriptor,
            body=payload,
            content_type="application/json",
        )
        assert result.error_code == ERROR_MALFORMED_JSON
        assert result.http_status == 400
        assert "JSONDecode" not in json.dumps(
            result.errors[0].to_stable_dict() if result.errors else {}
        )


def test_route_integration_valid_and_invalid(validation_client: TestClient) -> None:
    ok = validation_client.post(
        "/api/v1/_test/validation-envelope",
        json=VALID_BODY,
    )
    assert ok.status_code == 200
    assert ok.json() == {"accepted": True, "event_type": "test.event"}

    bad = validation_client.post(
        "/api/v1/_test/validation-envelope",
        json={"client_name": "c"},
    )
    assert bad.status_code == 422
    assert bad.json()["error"]["code"] == ERROR_INVALID_REQUEST_SCHEMA
    assert bad.json()["error"]["details"]


def test_invalid_request_never_reaches_handler() -> None:
    hits = {"count": 0}

    def counting_handler(context):  # noqa: ANN001
        hits["count"] += 1
        from codestrata_platform.community_cloud_api.serialization import (
            build_json_response,
        )

        return build_json_response(
            {"ok": True}, status_code=200, api_version="v1"
        )

    registry = RouteRegistry.foundation_v1()
    registry.register(
        RouteSpec(
            version="v1",
            method="POST",
            path="/_test/count",
            name="test.count",
        ),
        handler=counting_handler,
        request_schema=RequestSchemaDescriptor(
            schema_id="community.test.count",
            schema_version="1.0",
            model_type=ValidationEnvelopeRequest,
            body_policy=BodyPolicy.REQUIRED,
        ),
    )
    client = TestClient(create_community_cloud_app(registry=registry,
        authentication_policy=disabled_authentication_policy(),
    ))
    assert client.post("/api/v1/_test/count", json={}).status_code == 422
    assert hits["count"] == 0
    assert (
        client.post("/api/v1/_test/count", json=VALID_BODY).status_code == 200
    )
    assert hits["count"] == 1


def test_semantic_validator_extension(semantic_client: TestClient) -> None:
    body = dict(VALID_BODY)
    body["mode"] = "beta"
    response = semantic_client.post("/api/v1/_test/validation-envelope", json=body)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == ERROR_INVALID_REQUEST_SCHEMA
    details = response.json()["error"]["details"]
    assert any(item["field"] == "mode" for item in details)


def test_optional_route_absent_and_present(optional_client: TestClient) -> None:
    absent = optional_client.post("/api/v1/_test/validation-optional")
    assert absent.status_code == 200
    assert absent.json()["body"] is None
    present = optional_client.post(
        "/api/v1/_test/validation-optional",
        json=VALID_BODY,
    )
    assert present.status_code == 200
    assert present.json()["body"] == "present"


def test_media_type_on_schema_route(validation_client: TestClient) -> None:
    ok = validation_client.post(
        "/api/v1/_test/validation-envelope",
        content=json.dumps(VALID_BODY).encode(),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    assert ok.status_code == 200
    plain = validation_client.post(
        "/api/v1/_test/validation-envelope",
        content=json.dumps(VALID_BODY).encode(),
        headers={"Content-Type": "text/plain"},
    )
    assert plain.status_code == 415
    assert plain.json()["error"]["code"] == ERROR_UNSUPPORTED_MEDIA_TYPE
    form = validation_client.post(
        "/api/v1/_test/validation-envelope",
        content=b"a=1",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert form.status_code == 415


def test_health_unaffected_by_validation_foundation() -> None:
    client = TestClient(create_community_cloud_app(authentication_policy=disabled_authentication_policy()))
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["Cache-Control"] == "no-store"
    assert client.post("/api/v1/health").status_code == 405
    # Non-empty body on GET health is forbidden by schema policy.
    forbidden = client.request(
        "GET",
        "/api/v1/health",
        content=b'{"x":1}',
        headers={"Content-Type": "application/json"},
    )
    assert forbidden.status_code == 400
    assert forbidden.json()["error"]["code"] == ERROR_BODY_FORBIDDEN


def test_route_without_body_schema_behaves_as_before() -> None:
    registry = RouteRegistry()
    from codestrata_platform.community_cloud_api.health.handler import handle_health
    from codestrata_platform.community_cloud_api.validation.models import NO_BODY_SCHEMA

    registry.register(
        RouteSpec(version="v1", method="GET", path="/health", name="health.get"),
        handler=handle_health,
        request_schema=NO_BODY_SCHEMA,
    )

    def bare(context):  # noqa: ANN001
        from codestrata_platform.community_cloud_api.serialization import (
            build_json_response,
        )

        assert context.validated_request is None
        return build_json_response({"ok": True}, status_code=200, api_version="v1")

    registry.register(
        RouteSpec(version="v1", method="GET", path="/bare", name="bare.get"),
        handler=bare,
    )
    client = TestClient(create_community_cloud_app(registry=registry,
        authentication_policy=disabled_authentication_policy(),
    ))
    assert client.get("/api/v1/bare").status_code == 200


def test_strict_int_primitive() -> None:
    class M(CommunityApiRequestModel):
        n: ApiStrictInt

    with pytest.raises(ValidationError):
        M.model_validate({"n": "1"})
    assert M.model_validate({"n": 1}).n == 1


def test_foundation_registry_lists_health_schema() -> None:
    registry = build_validation_test_registry()
    schemas = registry.list_request_schemas()
    ids = sorted(item.schema_id for item in schemas)
    assert "community.foundation.no-body" in ids
    assert "community.test.validation-envelope" in ids
