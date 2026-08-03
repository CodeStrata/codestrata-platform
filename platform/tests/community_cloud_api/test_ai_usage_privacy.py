"""AI usage privacy endpoint tests."""

from __future__ import annotations

import pytest

from .ai_usage_helpers import configured_ai_usage_client, valid_ai_usage_body


@pytest.mark.parametrize(
    "mutate",
    [
        lambda b: b.__setitem__("prompt", "Explain this repository"),
        lambda b: b.__setitem__("response", "Here is the analysis"),
        lambda b: b.__setitem__("repository_url", "https://github.com/acme/repo"),
        lambda b: b.__setitem__(
            "usage",
            {**b["usage"], "model_id": "gpt-4o-mini"},  # type: ignore[index]
        ),
        lambda b: b.__setitem__(
            "usage",
            {**b["usage"], "cost": 0.02},  # type: ignore[index]
        ),
        lambda b: b.__setitem__(
            "context",
            {**b["context"], "tool_args": {"path": "/tmp/x"}},  # type: ignore[index]
        ),
    ],
)
def test_privacy_rejections(mutate: object) -> None:
    client, sink, *_ = configured_ai_usage_client()
    body = valid_ai_usage_body()
    mutate(body)  # type: ignore[operator]
    response = client.post("/api/v1/ai-usage", json=body)
    assert response.status_code == 422
    text = response.text
    assert "Explain this repository" not in text
    assert "Here is the analysis" not in text
    assert "github.com" not in text
    assert "gpt-4o-mini" not in text
    assert "/tmp/x" not in text
    assert sink.events == []
