"""CLI event privacy endpoint tests."""

from __future__ import annotations

import pytest

from .cli_event_helpers import configured_cli_client, valid_cli_event_body


@pytest.mark.parametrize(
    "mutate",
    [
        lambda b: b.__setitem__("command", "codestrata assess --repo /tmp/x"),
        lambda b: b.__setitem__("repository_url", "https://github.com/acme/repo"),
        lambda b: b.__setitem__(
            "context",
            {**b["context"], "working_directory": "/Users/satish"},  # type: ignore[index]
        ),
        lambda b: b.__setitem__(
            "event",
            {**b["event"], "exception": "Traceback..."},  # type: ignore[index]
        ),
        lambda b: b.__setitem__(
            "context",
            {**b["context"], "provider": "openai", "token_count": 9},  # type: ignore[index]
        ),
    ],
)
def test_privacy_rejections(mutate: object) -> None:
    client, sink, _, _, _, _ = configured_cli_client()
    body = valid_cli_event_body()
    mutate(body)  # type: ignore[operator]
    response = client.post("/api/v1/cli-events", json=body)
    assert response.status_code == 422
    text = response.text
    assert "/tmp/x" not in text
    assert "github.com" not in text
    assert "/Users/satish" not in text
    assert "Traceback" not in text
    assert "openai" not in text
    assert sink.events == []
