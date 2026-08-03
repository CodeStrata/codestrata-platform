"""Telemetry privacy endpoint tests — rejected values never echoed."""

from __future__ import annotations

import pytest

from .telemetry_helpers import configured_client, valid_telemetry_body


@pytest.mark.parametrize(
    "body",
    [
        valid_telemetry_body(properties={"feature": "alice@example.com"}),
        valid_telemetry_body(properties={"operation": "/Users/satish/code"}),
        valid_telemetry_body(properties={"feature": "C:\\repo\\src"}),
        valid_telemetry_body(properties={"feature": "file://tmp/x"}),
        {
            **valid_telemetry_body(),
            "email": "alice@example.com",
        },
        {
            **valid_telemetry_body(),
            "username": "alice",
        },
        {
            **valid_telemetry_body(),
            "repository_url": "https://github.com/acme/repo",
        },
        valid_telemetry_body(properties={"feature": "-----BEGIN PRIVATE KEY-----\nabc"}),
    ],
)
def test_privacy_rejections_do_not_echo_values(body: dict[str, object]) -> None:
    client, sink, _, _ = configured_client()
    response = client.post("/api/v1/telemetry", json=body)
    assert response.status_code == 422
    text = response.text
    assert "alice@example.com" not in text
    assert "/Users/satish" not in text
    assert "PRIVATE KEY" not in text
    assert "github.com" not in text
    assert sink.events == []
