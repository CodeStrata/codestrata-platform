"""Platform unit tests for Insights auth (Slice 15.9)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.insights_auth.cookies import (
    build_set_cookie,
    cookie_flags_ok,
    parse_cookie_header,
)
from codestrata_platform.community_cloud_api.insights_auth.password import (
    hash_password,
    verify_password,
)
from codestrata_platform.community_cloud_api.insights_auth.policy import (
    default_insights_auth_policy,
)
from codestrata_platform.community_cloud_api.insights_auth.secrets import (
    DEFAULT_PASSWORD_SECRET_ID,
    DEFAULT_SESSION_SECRET_ID,
    FakeSecretsPort,
    TEST_PASSWORD_PLAINTEXT,
    TEST_SESSION_SECRET,
)
from codestrata_platform.community_cloud_api.insights_auth.service import InsightsAuthService
from codestrata_platform.community_cloud_api.insights_auth.session import (
    SessionError,
    create_session_token,
    validate_session_token,
)


def _service(*, now: int = 1_700_000_000) -> InsightsAuthService:
    secrets = FakeSecretsPort(
        {
            DEFAULT_PASSWORD_SECRET_ID: hash_password(TEST_PASSWORD_PLAINTEXT),
            DEFAULT_SESSION_SECRET_ID: TEST_SESSION_SECRET,
        }
    )
    return InsightsAuthService(
        policy=default_insights_auth_policy(),
        secrets=secrets,
        now=lambda: now,
        extra_allowed_origins=frozenset({"http://localhost:5173"}),
    )


def test_scrypt_roundtrip() -> None:
    stored = hash_password(TEST_PASSWORD_PLAINTEXT)
    assert verify_password(submitted=TEST_PASSWORD_PLAINTEXT, stored_secret=stored)
    assert not verify_password(submitted="wrong", stored_secret=stored)


def test_raw_password_compare() -> None:
    assert verify_password(
        submitted=TEST_PASSWORD_PLAINTEXT,
        stored_secret=TEST_PASSWORD_PLAINTEXT,
    )


def test_session_valid_and_expired() -> None:
    token = create_session_token(
        signing_secret=TEST_SESSION_SECRET,
        ttl_seconds=10,
        now=lambda: 1000,
    )
    claims = validate_session_token(
        token, signing_secret=TEST_SESSION_SECRET, now=lambda: 1005
    )
    assert claims.authenticated is True
    try:
        validate_session_token(
            token, signing_secret=TEST_SESSION_SECRET, now=lambda: 1011
        )
        raise AssertionError("expected expire")
    except SessionError as exc:
        assert exc.code == "session_expired"


def test_session_wrong_signature() -> None:
    token = create_session_token(
        signing_secret=TEST_SESSION_SECRET,
        ttl_seconds=100,
        now=lambda: 1000,
    )
    try:
        validate_session_token(
            token, signing_secret="other-secret", now=lambda: 1001
        )
        raise AssertionError("expected invalid")
    except SessionError as exc:
        assert exc.code == "invalid_session"


def test_cookie_flags() -> None:
    policy = default_insights_auth_policy()
    cookie = build_set_cookie(policy=policy, token="abc")
    assert cookie_flags_ok(cookie, require_secure=True)
    assert "HttpOnly" in cookie
    assert "Secure" in cookie
    assert "SameSite=Strict" in cookie
    assert "Domain=" not in cookie
    assert parse_cookie_header(f"{policy.cookie_name}=abc; other=1", policy.cookie_name) == "abc"


def test_login_logout_session() -> None:
    auth = _service()
    cookie, err = auth.login(TEST_PASSWORD_PLAINTEXT)
    assert err is None
    assert cookie is not None
    assert "HttpOnly" in cookie
    token = cookie.split(";", 1)[0].split("=", 1)[1]
    header = f"{auth.policy.cookie_name}={token}"
    claims, cerr = auth.session_from_cookie_header(header)
    assert cerr is None
    assert claims is not None
    principal, perr = auth.require_authenticated(header)
    assert perr is None
    assert principal is not None
    cleared = auth.logout_cookie()
    assert "Max-Age=0" in cleared


def test_login_fails_closed_without_secrets() -> None:
    auth = InsightsAuthService(policy=default_insights_auth_policy())
    cookie, err = auth.login(TEST_PASSWORD_PLAINTEXT)
    assert cookie is None
    assert err == "auth_service_unavailable"


def test_invalid_password() -> None:
    auth = _service()
    cookie, err = auth.login("nope")
    assert cookie is None
    assert err == "invalid_credentials"
