"""Authentication evaluation helpers for Community Cloud dispatch."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.authentication.decisions import (
    DECISION_AUTHENTICATED,
    DECISION_DISABLED,
    DECISION_INACTIVE,
    DECISION_INVALID,
    DECISION_MISSING,
    DECISION_SCOPE_MISMATCH,
    DECISION_UNAVAILABLE,
    AuthenticationDecision,
)
from codestrata_platform.community_cloud_api.authentication.diagnostics import (
    AuthenticationDiagnostics,
)
from codestrata_platform.community_cloud_api.authentication.headers import (
    HEADER_AUTHORIZATION,
    parse_authorization_header,
)
from codestrata_platform.community_cloud_api.authentication.models import (
    AUTH_GROUP_PUBLIC,
    ROUTE_GROUP_INGESTION,
    AuthenticatedCommunityClient,
    CommunityAuthenticationPolicy,
)
from codestrata_platform.community_cloud_api.authentication.ports import (
    CommunityCredentialVerifier,
    UnavailableCommunityCredentialVerifier,
)
from codestrata_platform.community_cloud_api.authentication.responses import (
    build_authentication_error_response,
    build_client_not_authorized_response,
    decision_error_code,
)
from codestrata_platform.community_cloud_api.authentication.verifier import (
    build_safe_client_reference,
)
from codestrata_platform.community_cloud_api.logging.context import LoggingContext
from codestrata_platform.community_cloud_api.logging.logger import CommunityCloudLogger
from codestrata_platform.community_cloud_api.registry import RouteSpec
from starlette.requests import Request
from starlette.responses import Response


class AuthenticationRuntime:
    """Bundled auth policy/verifier used by application dispatch."""

    def __init__(
        self,
        *,
        policy: CommunityAuthenticationPolicy,
        verifier: CommunityCredentialVerifier,
    ) -> None:
        self.policy = policy
        self.verifier = verifier
        self.last_diagnostics: AuthenticationDiagnostics | None = None

    def evaluate_route(
        self,
        *,
        route: RouteSpec,
        request: Request,
        logger: CommunityCloudLogger,
        log_ctx: LoggingContext,
        api_version: str,
        request_id: str | None,
    ) -> tuple[AuthenticationDecision, Response | None]:
        auth_group = getattr(route, "authentication_group", AUTH_GROUP_PUBLIC)
        if not self.policy.enabled:
            decision = AuthenticationDecision(
                status=DECISION_DISABLED,
                authenticated=False,
                principal=None,
                safe_client_reference=None,
                reason="authentication_disabled",
                policy_id=self.policy.policy_id,
                verifier_status="disabled",
                limitations=("authentication_disabled",),
            )
            self._record(route.name, decision, rate_limit_scope_status="disabled")
            return decision, None

        if auth_group == AUTH_GROUP_PUBLIC or self.policy.is_public_route(route.name):
            decision = AuthenticationDecision(
                status=DECISION_DISABLED,
                authenticated=False,
                principal=None,
                safe_client_reference=None,
                reason="public_route",
                policy_id=self.policy.policy_id,
                verifier_status="skipped",
                limitations=("public_route_unauthenticated",),
            )
            self._record(route.name, decision, rate_limit_scope_status="public")
            return decision, None

        if isinstance(self.verifier, UnavailableCommunityCredentialVerifier):
            decision = AuthenticationDecision(
                status=DECISION_UNAVAILABLE,
                authenticated=False,
                principal=None,
                safe_client_reference=None,
                reason="verifier_unavailable",
                policy_id=self.policy.policy_id,
                verifier_status="unavailable",
                limitations=("credential_verifier_unavailable",),
            )
            self._record(route.name, decision, rate_limit_scope_status="none")
            logger.authentication_unavailable(
                log_ctx, status_code=503, decision=decision, policy=self.policy
            )
            return decision, build_authentication_error_response(
                decision,
                api_version=api_version,
                request_id=request_id,
                policy=self.policy,
            )

        headers = _authorization_values(request)
        parsed = parse_authorization_header(
            authorization_header=None,
            authorization_headers=headers,
            policy=self.policy,
        )
        if parsed.status == "missing":
            decision = AuthenticationDecision(
                status=DECISION_MISSING,
                authenticated=False,
                principal=None,
                safe_client_reference=None,
                reason=parsed.reason or "missing_authorization",
                policy_id=self.policy.policy_id,
                verifier_status="not_called",
            )
            self._record(route.name, decision, rate_limit_scope_status="none")
            logger.authentication_failed(
                log_ctx, status_code=401, decision=decision, policy=self.policy
            )
            return decision, build_authentication_error_response(
                decision,
                api_version=api_version,
                request_id=request_id,
                policy=self.policy,
            )
        if parsed.status != "ok" or parsed.credential is None:
            decision = AuthenticationDecision(
                status=DECISION_INVALID,
                authenticated=False,
                principal=None,
                safe_client_reference=None,
                reason=parsed.reason or "invalid_authorization",
                policy_id=self.policy.policy_id,
                verifier_status="not_called",
            )
            self._record(route.name, decision, rate_limit_scope_status="none")
            logger.authentication_failed(
                log_ctx, status_code=401, decision=decision, policy=self.policy
            )
            response = build_authentication_error_response(
                decision,
                api_version=api_version,
                request_id=request_id,
                policy=self.policy,
            )
            return decision, response

        credential = parsed.credential
        try:
            result = self.verifier.verify(credential)
        except Exception:  # noqa: BLE001
            credential.release()
            decision = AuthenticationDecision(
                status=DECISION_UNAVAILABLE,
                authenticated=False,
                principal=None,
                safe_client_reference=None,
                reason="verifier_exception",
                policy_id=self.policy.policy_id,
                verifier_status="exception",
            )
            self._record(route.name, decision, rate_limit_scope_status="none")
            logger.authentication_unavailable(
                log_ctx, status_code=503, decision=decision, policy=self.policy
            )
            return decision, build_authentication_error_response(
                decision,
                api_version=api_version,
                request_id=request_id,
                policy=self.policy,
            )
        finally:
            credential.release()

        if result.status == "unavailable":
            decision = AuthenticationDecision(
                status=DECISION_UNAVAILABLE,
                authenticated=False,
                principal=None,
                safe_client_reference=None,
                reason="verifier_unavailable",
                policy_id=self.policy.policy_id,
                verifier_status="unavailable",
                limitations=result.limitations,
            )
            self._record(route.name, decision, rate_limit_scope_status="none")
            logger.authentication_unavailable(
                log_ctx, status_code=503, decision=decision, policy=self.policy
            )
            return decision, build_authentication_error_response(
                decision,
                api_version=api_version,
                request_id=request_id,
                policy=self.policy,
            )

        if result.status in {"unknown", "inactive", "revoked"} or result.record is None:
            # Enumeration-resistant public classification.
            internal = (
                DECISION_INACTIVE
                if result.status in {"inactive", "revoked"}
                else DECISION_INVALID
            )
            decision = AuthenticationDecision(
                status=internal,
                authenticated=False,
                principal=None,
                safe_client_reference=None,
                reason=f"credential_{result.status}",
                policy_id=self.policy.policy_id,
                verifier_status=result.status,
            )
            self._record(route.name, decision, rate_limit_scope_status="none")
            logger.authentication_failed(
                log_ctx, status_code=401, decision=decision, policy=self.policy
            )
            # Public response always generic invalid credential.
            public = AuthenticationDecision(
                status=DECISION_INVALID,
                authenticated=False,
                principal=None,
                safe_client_reference=None,
                reason="invalid_client_credential",
                policy_id=self.policy.policy_id,
                verifier_status=result.status,
            )
            return public, build_authentication_error_response(
                public,
                api_version=api_version,
                request_id=request_id,
                policy=self.policy,
            )

        record = result.record
        if ROUTE_GROUP_INGESTION not in record.allowed_route_groups:
            decision = AuthenticationDecision(
                status=DECISION_SCOPE_MISMATCH,
                authenticated=False,
                principal=None,
                safe_client_reference=None,
                reason="route_group_denied",
                policy_id=self.policy.policy_id,
                verifier_status="active",
            )
            self._record(route.name, decision, rate_limit_scope_status="denied")
            logger.authorization_denied(
                log_ctx, status_code=403, decision=decision, policy=self.policy
            )
            return decision, build_authentication_error_response(
                decision,
                api_version=api_version,
                request_id=request_id,
                policy=self.policy,
            )

        principal = AuthenticatedCommunityClient(
            client_id=record.client_id,
            client_type=record.client_type,
            credential_id=record.credential_id,
            credential_version=record.credential_version,
            status=record.status,
            rate_limit_scope_id=record.rate_limit_scope_id,
            allowed_route_groups=record.allowed_route_groups,
        )
        safe_ref = build_safe_client_reference(
            client_id=record.client_id, policy=self.policy
        )
        decision = AuthenticationDecision(
            status=DECISION_AUTHENTICATED,
            authenticated=True,
            principal=principal,
            safe_client_reference=safe_ref,
            reason="authenticated",
            policy_id=self.policy.policy_id,
            verifier_status="active",
        )
        self._record(
            route.name,
            decision,
            rate_limit_scope_status="authenticated",
        )
        logger.authentication_succeeded(
            log_ctx, status_code=None, decision=decision, policy=self.policy
        )
        return decision, None

    def enforce_client_payload_match(
        self,
        *,
        decision: AuthenticationDecision,
        payload_client_type: str | None,
        api_version: str,
        request_id: str | None,
        logger: CommunityCloudLogger,
        log_ctx: LoggingContext,
        route_id: str,
    ) -> Response | None:
        if not self.policy.enabled or not self.policy.enforce_client_payload_match:
            return None
        if not decision.authenticated or decision.principal is None:
            return None
        if payload_client_type is None:
            return None
        if payload_client_type == decision.principal.client_type:
            return None
        denied = AuthenticationDecision(
            status=DECISION_SCOPE_MISMATCH,
            authenticated=False,
            principal=None,
            safe_client_reference=None,
            reason="client_type_mismatch",
            policy_id=self.policy.policy_id,
            verifier_status="active",
        )
        self._record(route_id, denied, rate_limit_scope_status="mismatch")
        logger.authorization_denied(
            log_ctx, status_code=403, decision=denied, policy=self.policy
        )
        return build_client_not_authorized_response(
            api_version=api_version, request_id=request_id
        )

    def _record(
        self,
        route_id: str,
        decision: AuthenticationDecision,
        *,
        rate_limit_scope_status: str,
    ) -> None:
        self.last_diagnostics = AuthenticationDiagnostics(
            route_id=route_id,
            decision_status=decision.status,
            verifier_status=decision.verifier_status,
            safe_client_reference=decision.safe_client_reference,
            client_type=(
                decision.principal.client_type if decision.principal is not None else None
            ),
            authentication_policy_id=decision.policy_id,
            rate_limit_scope_status=rate_limit_scope_status,
            limitations=decision.limitations,
        )


def _authorization_values(request: Request) -> list[str]:
    # Starlette may collapse duplicates; getlist when available.
    headers = request.headers
    if hasattr(headers, "getlist"):
        values = headers.getlist(HEADER_AUTHORIZATION)  # type: ignore[attr-defined]
        if values:
            return list(values)
    raw = headers.get(HEADER_AUTHORIZATION)
    return [raw] if raw is not None else []


__all__ = [
    "AuthenticationRuntime",
    "decision_error_code",
]
