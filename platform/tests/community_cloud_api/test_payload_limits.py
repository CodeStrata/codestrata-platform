"""Payload size limit enforcement (Slice 7.4)."""

from __future__ import annotations

from .auth_test_support import disabled_authentication_policy

import json

import pytest
from fastapi.testclient import TestClient

from codestrata_platform.community_cloud_api import (
    COMMUNITY_CLOUD_API_SCHEMA_VERSION,
    COMMUNITY_PAYLOAD_LIMIT_POLICY_VERSION,
    PAYLOAD_LIMIT_POLICY_URN,
    PayloadLimitPolicy,
    create_community_cloud_app,
)
from codestrata_platform.community_cloud_api.errors import (
    ERROR_BODY_FORBIDDEN,
    ERROR_NOT_FOUND,
    ERROR_PAYLOAD_ARRAY_LIMIT,
    ERROR_PAYLOAD_COMPLEXITY_LIMIT,
    ERROR_PAYLOAD_OBJECT_LIMIT,
    ERROR_PAYLOAD_STRING_LIMIT,
    ERROR_PAYLOAD_TOO_DEEP,
    ERROR_PAYLOAD_TOO_LARGE,
)
from codestrata_platform.community_cloud_api.payload_limits import (
    enforce_payload_limits,
    validate_json_structure,
    validate_request_bytes,
)
from codestrata_platform.community_cloud_api.serialization import dumps_stable

from .conftest import VALID_BODY, build_validation_test_registry


def _tiny_policy(**overrides: int) -> PayloadLimitPolicy:
    base = dict(
        max_request_bytes=10_000,
        max_json_depth=8,
        max_array_length=100,
        max_object_properties=100,
        max_string_length=4_096,
        max_traversal_count=10_000,
    )
    base.update(overrides)
    return PayloadLimitPolicy(**base)


def _client(policy: PayloadLimitPolicy) -> TestClient:
    return TestClient(
        create_community_cloud_app(
            registry=build_validation_test_registry(),
            payload_policy=policy,
                authentication_policy=disabled_authentication_policy(),
    )
    )


def test_policy_version_and_defaults() -> None:
    policy = PayloadLimitPolicy.default()
    assert policy.policy_version == PAYLOAD_LIMIT_POLICY_URN == "payload-limit-policy:1.0"
    assert COMMUNITY_PAYLOAD_LIMIT_POLICY_VERSION == "1.0"
    assert COMMUNITY_CLOUD_API_SCHEMA_VERSION == "1.0"
    assert policy.to_stable_dict()["max_request_bytes"] == 65_536


def test_normal_payload_accepted() -> None:
    client = _client(_tiny_policy())
    response = client.post("/api/v1/_test/validation-envelope", json=VALID_BODY)
    assert response.status_code == 200


def test_byte_size_limit_unit_and_route() -> None:
    policy = _tiny_policy(max_request_bytes=40)
    body = json.dumps(VALID_BODY).encode()
    assert len(body) > 40
    result = validate_request_bytes(body, policy)
    assert result.error_code == ERROR_PAYLOAD_TOO_LARGE
    assert result.http_status == 413

    client = _client(policy)
    response = client.post("/api/v1/_test/validation-envelope", json=VALID_BODY)
    assert response.status_code == 413
    assert response.json()["error"]["code"] == ERROR_PAYLOAD_TOO_LARGE
    assert response.json()["meta"]["payload_limit_policy"] == PAYLOAD_LIMIT_POLICY_URN
    assert VALID_BODY["event_type"] not in response.text


def test_byte_size_boundary_accepted() -> None:
    body = json.dumps({"event_type": "e", "client_name": "c"}).encode()
    policy = _tiny_policy(max_request_bytes=len(body))
    assert enforce_payload_limits(body=body, policy=policy).ok
    over = _tiny_policy(max_request_bytes=len(body) - 1)
    assert enforce_payload_limits(body=body, policy=over).error_code == ERROR_PAYLOAD_TOO_LARGE


def test_depth_limit() -> None:
    nested = {"a": {"b": {"c": 1}}}
    policy = _tiny_policy(max_json_depth=2)
    result = validate_json_structure(nested, policy)
    assert result.error_code == ERROR_PAYLOAD_TOO_DEEP
    assert result.http_status == 413

    # Flat validated body depth is 2 (object + leaf).
    client = _client(_tiny_policy(max_json_depth=1))
    response = client.post(
        "/api/v1/_test/validation-envelope",
        json={"event_type": "e", "client_name": "c"},
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == ERROR_PAYLOAD_TOO_DEEP


def test_array_and_object_limits() -> None:
    assert (
        validate_json_structure([1, 2, 3], _tiny_policy(max_array_length=2)).error_code
        == ERROR_PAYLOAD_ARRAY_LIMIT
    )
    assert (
        validate_json_structure(
            {"a": 1, "b": 2, "c": 3}, _tiny_policy(max_object_properties=2)
        ).error_code
        == ERROR_PAYLOAD_OBJECT_LIMIT
    )

    client = _client(_tiny_policy(max_array_length=2))
    response = client.post(
        "/api/v1/_test/validation-envelope",
        json={
            "event_type": "e",
            "client_name": "c",
            "tags": ["a", "b", "c"],
        },
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == ERROR_PAYLOAD_ARRAY_LIMIT

    client = _client(_tiny_policy(max_object_properties=2))
    response = client.post(
        "/api/v1/_test/validation-envelope",
        json={
            "event_type": "e",
            "client_name": "c",
            "attributes": {"a": "1", "b": "2", "c": "3"},
        },
    )
    # Root object has more than 2 properties (event_type, client_name, attributes).
    assert response.status_code == 413
    assert response.json()["error"]["code"] == ERROR_PAYLOAD_OBJECT_LIMIT


def test_string_limit() -> None:
    assert (
        validate_json_structure({"x": "abcd"}, _tiny_policy(max_string_length=3)).error_code
        == ERROR_PAYLOAD_STRING_LIMIT
    )
    client = _client(_tiny_policy(max_string_length=5))
    response = client.post(
        "/api/v1/_test/validation-envelope",
        json={"event_type": "abcdef", "client_name": "c"},
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == ERROR_PAYLOAD_STRING_LIMIT
    assert "abcdef" not in response.text


def test_complexity_limit() -> None:
    wide = {f"k{i}": i for i in range(20)}
    result = validate_json_structure(wide, _tiny_policy(max_traversal_count=5))
    assert result.error_code == ERROR_PAYLOAD_COMPLEXITY_LIMIT


def test_determinism() -> None:
    policy = _tiny_policy(max_request_bytes=10)
    body = b'{"event_type":"e","client_name":"c"}'
    left = enforce_payload_limits(body=body, policy=policy)
    right = enforce_payload_limits(body=body, policy=policy)
    assert dumps_stable(left) == dumps_stable(right)

    client = _client(policy)
    a = client.post("/api/v1/_test/validation-envelope", content=body, headers={
        "Content-Type": "application/json",
    })
    b = client.post("/api/v1/_test/validation-envelope", content=body, headers={
        "Content-Type": "application/json",
    })
    assert a.status_code == b.status_code == 413
    assert a.content == b.content


def test_unknown_route_404_before_payload_evaluation() -> None:
    client = _client(_tiny_policy(max_request_bytes=1))
    huge = b"{" + b"a" * 1000 + b"}"
    response = client.post(
        "/api/v1/does-not-exist",
        content=huge,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == ERROR_NOT_FOUND


def test_health_regression_unchanged() -> None:
    client = TestClient(create_community_cloud_app(authentication_policy=disabled_authentication_policy()))
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["Cache-Control"] == "no-store"
    assert client.post("/api/v1/health").status_code == 405
    forbidden = client.request(
        "GET",
        "/api/v1/health",
        content=b'{"x":1}',
        headers={"Content-Type": "application/json"},
    )
    assert forbidden.status_code == 400
    assert forbidden.json()["error"]["code"] == ERROR_BODY_FORBIDDEN


def test_error_envelope_safety_no_leakage() -> None:
    client = _client(_tiny_policy(max_string_length=3))
    secret = "super-secret-value"
    response = client.post(
        "/api/v1/_test/validation-envelope",
        json={"event_type": secret, "client_name": "c"},
    )
    assert response.status_code == 413
    text = response.text
    assert secret not in text
    assert "Traceback" not in text
    assert "/Users/" not in text
    assert "offset" not in text.lower()
    body = response.json()
    assert list(body.keys()) == ["error", "meta"]
    assert body["error"]["details"] == {"limit": "max_string_length"}


def test_empty_body_skips_limits() -> None:
    assert enforce_payload_limits(body=b"", policy=_tiny_policy(max_request_bytes=1)).ok
