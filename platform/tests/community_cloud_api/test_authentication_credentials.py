"""Credential format and header parsing tests."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.authentication.credentials import (
    CommunityClientCredential,
    constant_time_equal,
    parse_credential_token,
)
from codestrata_platform.community_cloud_api.authentication.headers import (
    parse_authorization_header,
)
from codestrata_platform.community_cloud_api.authentication.models import (
    CommunityAuthenticationPolicy,
)
from codestrata_platform.community_cloud_api.authentication.verifier import (
    InMemoryCommunityCredentialVerifier,
)

from .auth_test_support import TEST_CLI_TOKEN


def test_valid_and_invalid_credential_formats() -> None:
    policy = CommunityAuthenticationPolicy.default()
    assert parse_credential_token(TEST_CLI_TOKEN, policy=policy) is not None
    assert parse_credential_token("cscc_v2_TEST_ONLY_XXXX", policy=policy) is None
    assert parse_credential_token("cscc_v1_short", policy=policy) is None
    assert parse_credential_token("cscc_v1_TEST ONLY SPACES", policy=policy) is None
    assert parse_credential_token("cscc_v1_TEST/path", policy=policy) is None
    assert parse_credential_token("cscc_v1_TEST\nline", policy=policy) is None
    assert parse_credential_token("-----BEGIN PRIVATE KEY-----", policy=policy) is None
    cred = parse_credential_token(TEST_CLI_TOKEN, policy=policy)
    assert cred is not None
    assert "TEST_ONLY" not in repr(cred)
    assert "TEST_ONLY" not in str(cred)


def test_authorization_header_parsing() -> None:
    policy = CommunityAuthenticationPolicy.default()
    ok = parse_authorization_header(
        authorization_header=f"Bearer {TEST_CLI_TOKEN}", policy=policy
    )
    assert ok.status == "ok"
    assert ok.credential is not None
    assert parse_authorization_header(
        authorization_header=f"bearer {TEST_CLI_TOKEN}", policy=policy
    ).status == "ok"
    assert parse_authorization_header(authorization_header=None, policy=policy).status == (
        "missing"
    )
    assert parse_authorization_header(
        authorization_header=f"Basic {TEST_CLI_TOKEN}", policy=policy
    ).status == "invalid"
    assert parse_authorization_header(
        authorization_headers=[f"Bearer {TEST_CLI_TOKEN}", f"Bearer {TEST_CLI_TOKEN}"],
        policy=policy,
    ).status == "invalid"
    assert parse_authorization_header(
        authorization_header=f"Bearer {TEST_CLI_TOKEN}, Bearer x", policy=policy
    ).status == "invalid"


def test_verifier_active_unknown_inactive_and_constant_time() -> None:
    policy = CommunityAuthenticationPolicy.default()
    verifier = InMemoryCommunityCredentialVerifier(policy=policy)
    verifier.register(
        TEST_CLI_TOKEN,
        client_id="c1",
        client_type="codestrata_cli",
        rate_limit_scope_id="scope-1",
        credential_id="cred-1",
    )
    cred = parse_credential_token(TEST_CLI_TOKEN, policy=policy)
    assert cred is not None
    assert verifier.verify(cred).status == "active"
    bad = parse_credential_token("cscc_v1_TEST_ONLY_UNKNOWN_TOKEN_ZZ", policy=policy)
    assert bad is not None
    assert verifier.verify(bad).status == "unknown"
    assert verifier.has_plaintext() is False
    assert constant_time_equal("abc", "abc") is True
    assert constant_time_equal("abc", "abd") is False
    _ = CommunityClientCredential
