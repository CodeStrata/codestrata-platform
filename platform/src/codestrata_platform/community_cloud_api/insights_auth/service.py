"""Insights auth service — password login and session lifecycle."""

from __future__ import annotations

from typing import Callable

from codestrata_platform.community_cloud_api.insights_auth.cookies import (
    build_set_cookie,
    parse_cookie_header,
)
from codestrata_platform.community_cloud_api.insights_auth.csrf import origin_allowed
from codestrata_platform.community_cloud_api.insights_auth.errors import (
    ERROR_AUTH_SERVICE_UNAVAILABLE,
    ERROR_AUTHENTICATION_REQUIRED,
    ERROR_INVALID_CREDENTIALS,
    ERROR_INVALID_ORIGIN,
    ERROR_INVALID_SESSION,
    ERROR_SESSION_EXPIRED,
)
from codestrata_platform.community_cloud_api.insights_auth.models import (
    InsightsPrincipal,
    SessionClaims,
)
from codestrata_platform.community_cloud_api.insights_auth.password import verify_password
from codestrata_platform.community_cloud_api.insights_auth.policy import InsightsAuthPolicy
from codestrata_platform.community_cloud_api.insights_auth.secrets import (
    SecretsPort,
    UnavailableSecretsPort,
)
from codestrata_platform.community_cloud_api.insights_auth.session import (
    SessionError,
    create_session_token,
    validate_session_token,
)


class InsightsAuthService:
    """Server-side auth authority. Aggregation must not call this for metrics."""

    def __init__(
        self,
        *,
        policy: InsightsAuthPolicy,
        secrets: SecretsPort | None = None,
        now: Callable[[], int] | None = None,
        extra_allowed_origins: frozenset[str] | None = None,
    ) -> None:
        self.policy = policy
        self._secrets = secrets if secrets is not None else UnavailableSecretsPort()
        self._now = now
        self._extra_origins = extra_allowed_origins

    def check_origin(self, *, origin: str | None, referer: str | None) -> str | None:
        if origin_allowed(
            origin=origin,
            referer=referer,
            policy=self.policy,
            extra_allowed_origins=self._extra_origins,
        ):
            return None
        return ERROR_INVALID_ORIGIN

    def login(self, password: str) -> tuple[str | None, str | None]:
        """Return (set_cookie_value, error_code)."""

        if self.policy.session_signing_reuses_dashboard_password:
            return None, ERROR_AUTH_SERVICE_UNAVAILABLE

        stored = self._secrets.get_secret_value(self.policy.password_secret_id)
        if stored is None:
            return None, ERROR_AUTH_SERVICE_UNAVAILABLE
        try:
            ok = verify_password(submitted=password, stored_secret=stored)
        finally:
            # Best-effort: drop local reference promptly.
            stored = ""
            del stored

        if not ok:
            return None, ERROR_INVALID_CREDENTIALS

        signing = self._secrets.get_secret_value(self.policy.session_secret_id)
        if not signing:
            return None, ERROR_AUTH_SERVICE_UNAVAILABLE
        if signing == password:
            return None, ERROR_AUTH_SERVICE_UNAVAILABLE

        token = create_session_token(
            signing_secret=signing,
            ttl_seconds=self.policy.session_ttl_seconds,
            now=self._now,
        )
        cookie = build_set_cookie(policy=self.policy, token=token)
        return cookie, None

    def logout_cookie(self) -> str:
        return build_set_cookie(policy=self.policy, token="", clear=True)

    def session_from_cookie_header(
        self, cookie_header: str | None
    ) -> tuple[SessionClaims | None, str | None]:
        token = parse_cookie_header(cookie_header, self.policy.cookie_name)
        if not token:
            return None, ERROR_AUTHENTICATION_REQUIRED
        signing = self._secrets.get_secret_value(self.policy.session_secret_id)
        if not signing:
            return None, ERROR_AUTH_SERVICE_UNAVAILABLE
        try:
            claims = validate_session_token(
                token,
                signing_secret=signing,
                now=self._now,
            )
            return claims, None
        except SessionError as exc:
            return None, exc.code

    def require_authenticated(
        self, cookie_header: str | None
    ) -> tuple[InsightsPrincipal | None, str | None]:
        claims, err = self.session_from_cookie_header(cookie_header)
        if claims is None:
            return None, err or ERROR_AUTHENTICATION_REQUIRED
        if err in {ERROR_SESSION_EXPIRED, ERROR_INVALID_SESSION}:
            return None, err
        return InsightsPrincipal(), None
