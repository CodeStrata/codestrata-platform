"""Extension event privacy endpoint tests."""

from __future__ import annotations

import pytest

from .extension_event_helpers import (
    configured_extension_client,
    valid_extension_event_body,
)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda b: b.__setitem__("workspace_uri", "file:///Users/satish/repo"),
        lambda b: b.__setitem__("repository_url", "https://github.com/acme/repo"),
        lambda b: b.__setitem__(
            "context",
            {**b["context"], "selected_text": "secret code"},  # type: ignore[index]
        ),
        lambda b: b.__setitem__(
            "event",
            {**b["event"], "exception": "Traceback..."},  # type: ignore[index]
        ),
        lambda b: b.__setitem__(
            "context",
            {**b["context"], "provider": "openai", "token_count": 9},  # type: ignore[index]
        ),
        lambda b: b.__setitem__("command_id", "codestrata.assess"),
    ],
)
def test_privacy_rejections(mutate: object) -> None:
    client, sink, _, _, _, _, _ = configured_extension_client()
    body = valid_extension_event_body()
    mutate(body)  # type: ignore[operator]
    response = client.post("/api/v1/extension-events", json=body)
    assert response.status_code == 422
    text = response.text
    assert "/Users/satish" not in text
    assert "github.com" not in text
    assert "secret code" not in text
    assert "Traceback" not in text
    assert "openai" not in text
    assert sink.events == []
