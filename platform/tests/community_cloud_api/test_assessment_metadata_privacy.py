"""Assessment metadata privacy endpoint tests."""

from __future__ import annotations

import pytest

from .assessment_metadata_helpers import (
    configured_metadata_client,
    valid_assessment_metadata_body,
)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda b: b.__setitem__("repository_name", "acme-app"),
        lambda b: b.__setitem__("email", "a@b.com"),
        lambda b: b.__setitem__(
            "repository",
            {**b["repository"], "primary_language": "/Users/satish/code"},  # type: ignore[index]
        ),
        lambda b: b.__setitem__(
            "assessment",
            {**b["assessment"], "findings": [{"id": "F1"}]},  # type: ignore[index]
        ),
        lambda b: b.__setitem__(
            "execution",
            {**b["execution"], "exception": "boom"},  # type: ignore[index]
        ),
        lambda b: b.__setitem__(
            "execution",
            {**b["execution"], "model": "gpt-x", "token_count": 12},  # type: ignore[index]
        ),
    ],
)
def test_privacy_rejections(mutate: object) -> None:
    client, sink, _, _, _ = configured_metadata_client()
    body = valid_assessment_metadata_body()
    mutate(body)  # type: ignore[operator]
    response = client.post("/api/v1/assessment-metadata", json=body)
    assert response.status_code == 422
    text = response.text
    assert "acme-app" not in text
    assert "a@b.com" not in text
    assert "/Users/satish" not in text
    assert "gpt-x" not in text
    assert sink.events == []
