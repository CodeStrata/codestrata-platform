"""Canonical validation error envelope, strict typing, and safety tests."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from codestrata_platform.community_cloud_api.errors import (
    ERROR_INVALID_REQUEST_SCHEMA,
    ERROR_MALFORMED_JSON,
)
from codestrata_platform.community_cloud_api.serialization import dumps_stable
from codestrata_platform.community_cloud_api.validation import (
    ApiRepositoryRelativePath,
    ApiSafeLabel,
    BodyPolicy,
    CommunityApiRequestModel,
    RequestSchemaDescriptor,
    validate_request_body,
)
from codestrata_platform.community_cloud_api.validation.errors import (
    FIELD_MISSING,
    FIELD_TOO_LONG,
    FIELD_UNKNOWN,
    FIELD_UNSAFE_VALUE,
    build_validation_error_response,
)
from codestrata_platform.community_cloud_api.validation.sanitization import (
    contains_secret_like_value,
    is_safe_repository_relative_path,
)

from .conftest import VALID_BODY, ValidationEnvelopeRequest


@pytest.fixture()
def client(validation_client: TestClient) -> TestClient:
    return validation_client


def _post(client: TestClient, body: object) -> object:
    return client.post("/api/v1/_test/validation-envelope", json=body)


def test_missing_required_field(client: TestClient) -> None:
    response = _post(client, {"client_name": "c"})
    assert response.status_code == 422
    details = response.json()["error"]["details"]
    assert any(item["field"] == "event_type" and item["code"] == FIELD_MISSING for item in details)


def test_wrong_type_and_unknown_field(client: TestClient) -> None:
    response = _post(
        client,
        {"event_type": "e", "client_name": "c", "count": "1", "mystery": True},
    )
    assert response.status_code == 422
    text = response.text
    assert "mystery" in text or "unknown" in text
    assert '"1"' not in text or "count" in text
    # Submitted values must not be echoed.
    assert "True" not in text
    codes = {item["code"] for item in response.json()["error"]["details"]}
    assert FIELD_UNKNOWN in codes or "invalid_type" in codes


def test_invalid_enum_and_lengths(client: TestClient) -> None:
    long_name = "x" * 65
    response = _post(
        client,
        {
            "event_type": long_name,
            "client_name": "c",
            "mode": "gamma",
        },
    )
    assert response.status_code == 422
    details = response.json()["error"]["details"]
    codes = {item["code"] for item in details}
    assert FIELD_TOO_LONG in codes or "invalid_enum" in codes or "invalid_format" in codes


def test_list_and_dict_too_large(client: TestClient) -> None:
    response = _post(
        client,
        {
            "event_type": "e",
            "client_name": "c",
            "tags": ["a", "b", "c", "d"],
            "attributes": {"a": "1", "b": "2", "c": "3", "d": "4"},
        },
    )
    assert response.status_code == 422


def test_detail_limit_and_deterministic_ordering() -> None:
    class ManyRequired(CommunityApiRequestModel):
        a: str
        b: str
        c: str
        d: str
        e: str
        f: str
        g: str
        h: str
        i: str
        j: str
        k: str
        l: str
        m: str
        n: str
        o: str
        p: str
        q: str
        r: str
        s: str
        t: str
        u: str
        v: str

    descriptor = RequestSchemaDescriptor(
        schema_id="community.test.many",
        schema_version="1.0",
        model_type=ManyRequired,
        body_policy=BodyPolicy.REQUIRED,
        max_error_details=5,
    )
    left = validate_request_body(
        descriptor=descriptor, body=b"{}", content_type="application/json"
    )
    right = validate_request_body(
        descriptor=descriptor, body=b"{}", content_type="application/json"
    )
    assert left.error_code == ERROR_INVALID_REQUEST_SCHEMA
    assert len(left.errors) == 5
    assert left.truncated_error_count > 0
    assert dumps_stable(build_validation_error_response(left, api_version="v1")) == dumps_stable(
        build_validation_error_response(right, api_version="v1")
    )
    fields = [item.field for item in left.errors]
    assert fields == sorted(fields)


def test_error_envelope_safe_and_canonical(client: TestClient) -> None:
    response = _post(client, {"event_type": "e"})
    payload = response.json()
    assert list(payload.keys()) == ["error", "meta"]
    error = payload["error"]
    assert error["code"] == ERROR_INVALID_REQUEST_SCHEMA
    assert error["message"] == "Request payload failed validation."
    assert "ValidationError" not in response.text
    assert "pydantic" not in response.text.lower()
    assert "Traceback" not in response.text
    assert "/Users/" not in response.text
    assert "codestrata_platform" not in response.text
    for item in error["details"]:
        assert set(item.keys()) == {"code", "field", "message"}
        assert item["message"].endswith(".")


def test_malformed_json_route(client: TestClient) -> None:
    response = client.post(
        "/api/v1/_test/validation-envelope",
        content=b"{",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == ERROR_MALFORMED_JSON
    assert "Expecting" not in response.text


def test_secret_like_values_rejected_without_echo(client: TestClient) -> None:
    secrets = [
        "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----",
        "Bearer supersecrettokenvalue",
        "AKIAIOSFODNN7EXAMPLE",
        "https://example.com/?X-Amz-Signature=abcdef1234567890",
        "file:///etc/passwd",
        "/Users/satish/project",
        r"C:\Users\satish\secret",
    ]
    for value in secrets:
        assert contains_secret_like_value(value)
        response = _post(
            client,
            {"event_type": "e", "client_name": "c", "label": value},
        )
        assert response.status_code == 422, value
        text = response.text
        assert value not in text
        assert "PRIVATE KEY" not in text
        assert "supersecrettokenvalue" not in text
        assert "AKIA" not in text
        details = response.json()["error"]["details"]
        assert any(item["code"] == FIELD_UNSAFE_VALUE for item in details)


def test_safe_ordinary_label_accepted(client: TestClient) -> None:
    response = _post(
        client,
        {
            "event_type": "e",
            "client_name": "c",
            "label": "ordinary-label",
        },
    )
    assert response.status_code == 200


def test_identifier_control_and_path_chars_rejected(client: TestClient) -> None:
    for bad in ("has\nnewline", "has/slash", "has space"):
        response = _post(
            client,
            {"event_type": bad, "client_name": "c"},
        )
        assert response.status_code == 422
        assert bad not in response.text


def test_repository_relative_path_helper() -> None:
    class PathModel(CommunityApiRequestModel):
        path: ApiRepositoryRelativePath

    assert is_safe_repository_relative_path("src/main.py")
    assert PathModel.model_validate({"path": "src/main.py"}).path == "src/main.py"
    for bad in ("/abs", r"C:\x", "file://x", "../secret", "a/../../b"):
        assert not is_safe_repository_relative_path(bad)
        with pytest.raises(Exception):
            PathModel.model_validate({"path": bad})


def test_no_timestamp_or_headers_in_error_body(client: TestClient) -> None:
    response = client.post(
        "/api/v1/_test/validation-envelope",
        json={"event_type": "e"},
        headers={"X-Request-Id": "rid-1", "Authorization": "Bearer abc"},
    )
    body = response.json()
    assert "timestamp" not in json.dumps(body)
    assert "Authorization" not in response.text
    assert "Bearer abc" not in response.text
    # request_id may appear from transport echo policy on error object
    assert response.headers.get("X-Request-Id") == "rid-1"


def test_unicode_safe_label_allowed() -> None:
    model = ValidationEnvelopeRequest.model_validate(
        {"event_type": "e", "client_name": "c", "label": "étiquette"}
    )
    assert model.label == "étiquette"
    # Type export remains available for future event schemas.
    assert ApiSafeLabel is not None
