"""Authentication header-focused tests."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.authentication.headers import (
    parse_authorization_header,
)
from codestrata_platform.community_cloud_api.authentication.models import (
    CommunityAuthenticationPolicy,
)

from .auth_test_support import TEST_CLI_TOKEN


def test_empty_and_whitespace_tokens() -> None:
    policy = CommunityAuthenticationPolicy.default()
    assert parse_authorization_header(authorization_header="Bearer ", policy=policy).status == (
        "invalid"
    )
    assert parse_authorization_header(authorization_header="Bearer", policy=policy).status == (
        "invalid"
    )
    assert parse_authorization_header(
        authorization_header=f"  Bearer   {TEST_CLI_TOKEN}  ", policy=policy
    ).status == "ok"
