"""ASGI application entry point for the Community Cloud API."""

from __future__ import annotations

import json
from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from codestrata_platform.community_cloud_api.constants import (
    API_ROOT_PREFIX,
    API_VERSION_V1,
    REQUEST_ID_HEADER,
    SUPPORTED_API_VERSIONS,
    SUPPORTED_METHODS,
)
from codestrata_platform.community_cloud_api.errors import (
    ERROR_INVALID_REQUEST_SCHEMA,
    ERROR_METHOD_NOT_ALLOWED,
    ERROR_NOT_FOUND,
    ERROR_VERSION_NOT_SUPPORTED,
)
from codestrata_platform.community_cloud_api.logging import (
    CommunityCloudLogger,
    CommunityLoggingPolicy,
    asgi_client_host,
    begin_request_logging,
    default_logging_policy,
    finish_request_logging,
)
from codestrata_platform.community_cloud_api.logging.diagnostics import (
    payload_logging_diagnostic,
    validation_logging_diagnostic,
)
from codestrata_platform.community_cloud_api.media import normalize_content_type
from codestrata_platform.community_cloud_api.models import RequestContext
from codestrata_platform.community_cloud_api.payload_limits import (
    PayloadLimitPolicy,
    build_payload_limit_error_response,
    default_payload_limit_policy,
    evaluate_payload_limits,
)
from codestrata_platform.community_cloud_api.rate_limiting import (
    CommunityRateLimitPolicy,
    RateLimitRuntime,
    default_rate_limit_policy,
    default_rate_limit_runtime,
    validate_rate_limit_policy,
)
from codestrata_platform.community_cloud_api.rate_limiting.ports import RateLimitStore
from codestrata_platform.community_cloud_api.registry import RouteRegistry
from codestrata_platform.community_cloud_api.serialization import (
    build_error_response,
    build_json_response,
)
from codestrata_platform.community_cloud_api.validation.errors import (
    build_validation_error_response,
)
from codestrata_platform.community_cloud_api.validation.validator import (
    build_safe_diagnostic,
    validate_request_body,
)


class _FoundationMiddleware(BaseHTTPMiddleware):
    """Reject unsupported HTTP methods before route dispatch."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        method = request.method.upper()
        request_id = _client_request_id(request)
        api_version = _path_api_version(request.url.path) or API_VERSION_V1

        if method not in SUPPORTED_METHODS:
            return build_error_response(
                ERROR_METHOD_NOT_ALLOWED,
                http_status=405,
                api_version=api_version,
                request_id=request_id,
                details={"method": method},
            )

        return await call_next(request)


def create_community_cloud_app(
    *,
    registry: RouteRegistry | None = None,
    payload_policy: PayloadLimitPolicy | None = None,
    logging_policy: CommunityLoggingPolicy | None = None,
    logger: CommunityCloudLogger | None = None,
    rate_limit_policy: CommunityRateLimitPolicy | None = None,
    rate_limit_store: RateLimitStore | None = None,
    rate_limit_clock_ms: Callable[[], int] | None = None,
    authentication_policy: object | None = None,
    credential_verifier: object | None = None,
    telemetry_sink: object | None = None,
    assessment_metadata_sink: object | None = None,
    cli_event_sink: object | None = None,
    extension_event_sink: object | None = None,
    ai_usage_sink: object | None = None,
    event_identity_lookup: object | None = None,
    event_identity_recorder: object | None = None,
    insights_auth_service: object | None = None,
    insights_aggregation_service: object | None = None,
    insights_extra_allowed_origins: frozenset[str] | None = None,
) -> FastAPI:
    """Create the Community Cloud API ASGI app.

    Slice 7.13 adds Community client authentication for protected ingestion
    routes. Health remains public. Default credential verifier is unavailable
    (fail-closed 503 for protected routes). No CORS, OpenAPI UI, production
    persistence, credential issuance, or log shipping.
    """

    from codestrata_platform.community_cloud_api.authentication import (
        AuthenticationRuntime,
        CommunityAuthenticationPolicy,
        UnavailableCommunityCredentialVerifier,
        default_authentication_policy,
        validate_authentication_policy,
    )
    from codestrata_platform.community_cloud_api.ai_usage.ports import (
        UnavailableAiUsageSink,
    )
    from codestrata_platform.community_cloud_api.ai_usage.service import IngestAiUsage
    from codestrata_platform.community_cloud_api.assessment_metadata.ports import (
        UnavailableAssessmentMetadataSink,
    )
    from codestrata_platform.community_cloud_api.assessment_metadata.service import (
        IngestAssessmentMetadata,
    )
    from codestrata_platform.community_cloud_api.cli_events.ports import (
        UnavailableCliEventSink,
    )
    from codestrata_platform.community_cloud_api.cli_events.service import IngestCliEvent
    from codestrata_platform.community_cloud_api.extension_events.ports import (
        UnavailableExtensionEventSink,
    )
    from codestrata_platform.community_cloud_api.extension_events.service import (
        IngestExtensionEvent,
    )
    from codestrata_platform.community_cloud_api.telemetry.ports import (
        UnavailableTelemetryEventSink,
    )
    from codestrata_platform.community_cloud_api.telemetry.service import (
        IngestTelemetryEvent,
    )

    active_payload_policy = payload_policy or default_payload_limit_policy()
    active_logging_policy = logging_policy or default_logging_policy()
    active_logger = logger or CommunityCloudLogger.create(policy=active_logging_policy)

    tel_sink = (
        telemetry_sink if telemetry_sink is not None else UnavailableTelemetryEventSink()
    )
    telemetry_service = IngestTelemetryEvent(
        sink=tel_sink,  # type: ignore[arg-type]
        lookup=event_identity_lookup,  # type: ignore[arg-type]
        recorder=event_identity_recorder,  # type: ignore[arg-type]
        logger=active_logger,
    )

    meta_sink = (
        assessment_metadata_sink
        if assessment_metadata_sink is not None
        else UnavailableAssessmentMetadataSink()
    )
    assessment_metadata_service = IngestAssessmentMetadata(
        sink=meta_sink,  # type: ignore[arg-type]
        lookup=event_identity_lookup,  # type: ignore[arg-type]
        recorder=event_identity_recorder,  # type: ignore[arg-type]
        logger=active_logger,
    )

    cli_sink = cli_event_sink if cli_event_sink is not None else UnavailableCliEventSink()
    cli_event_service = IngestCliEvent(
        sink=cli_sink,  # type: ignore[arg-type]
        lookup=event_identity_lookup,  # type: ignore[arg-type]
        recorder=event_identity_recorder,  # type: ignore[arg-type]
        logger=active_logger,
    )

    ext_sink = (
        extension_event_sink
        if extension_event_sink is not None
        else UnavailableExtensionEventSink()
    )
    extension_event_service = IngestExtensionEvent(
        sink=ext_sink,  # type: ignore[arg-type]
        lookup=event_identity_lookup,  # type: ignore[arg-type]
        recorder=event_identity_recorder,  # type: ignore[arg-type]
        logger=active_logger,
    )

    ai_sink = ai_usage_sink if ai_usage_sink is not None else UnavailableAiUsageSink()
    ai_usage_service = IngestAiUsage(
        sink=ai_sink,  # type: ignore[arg-type]
        lookup=event_identity_lookup,  # type: ignore[arg-type]
        recorder=event_identity_recorder,  # type: ignore[arg-type]
        logger=active_logger,
    )

    from codestrata_platform.community_cloud_api.insights.service import (
        InsightsAggregationService,
    )
    from codestrata_platform.community_cloud_api.insights_auth.policy import (
        default_insights_auth_policy,
    )
    from codestrata_platform.community_cloud_api.insights_auth.routes import (
        register_insights_auth_routes,
    )
    from codestrata_platform.community_cloud_api.insights_auth.service import (
        InsightsAuthService,
    )

    insights_agg = (
        insights_aggregation_service
        if isinstance(insights_aggregation_service, InsightsAggregationService)
        else InsightsAggregationService()
    )
    insights_auth = (
        insights_auth_service
        if isinstance(insights_auth_service, InsightsAuthService)
        else InsightsAuthService(
            policy=default_insights_auth_policy(),
            extra_allowed_origins=insights_extra_allowed_origins,
        )
    )

    active_registry = registry or RouteRegistry.foundation_v1(
        telemetry_service=telemetry_service,
        assessment_metadata_service=assessment_metadata_service,
        cli_event_service=cli_event_service,
        extension_event_service=extension_event_service,
        ai_usage_service=ai_usage_service,
    )
    if active_registry.get(version=API_VERSION_V1, method="POST", path="/insights/auth/login") is None:
        register_insights_auth_routes(
            active_registry,
            auth=insights_auth,
            aggregation=insights_agg,
        )

    active_rate_policy = validate_rate_limit_policy(
        rate_limit_policy or default_rate_limit_policy(),
        route_names=frozenset(item.name for item in active_registry.list_routes()),
    )
    rate_limit_runtime = default_rate_limit_runtime(
        policy=active_rate_policy,
        store=rate_limit_store,
        clock_ms=rate_limit_clock_ms,
    )

    active_auth_policy = validate_authentication_policy(
        authentication_policy  # type: ignore[arg-type]
        if isinstance(authentication_policy, CommunityAuthenticationPolicy)
        else default_authentication_policy()
    )
    active_verifier = (
        credential_verifier
        if credential_verifier is not None
        else UnavailableCommunityCredentialVerifier()
    )
    auth_runtime = AuthenticationRuntime(
        policy=active_auth_policy,
        verifier=active_verifier,  # type: ignore[arg-type]
    )

    app = FastAPI(
        title="CodeStrata Community Cloud API",
        version=API_VERSION_V1,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.community_cloud_route_registry = active_registry
    app.state.community_cloud_payload_policy = active_payload_policy
    app.state.community_cloud_logging_policy = active_logging_policy
    app.state.community_cloud_logger = active_logger
    app.state.community_cloud_rate_limit_policy = active_rate_policy
    app.state.community_cloud_rate_limit_runtime = rate_limit_runtime
    app.state.community_cloud_authentication_policy = active_auth_policy
    app.state.community_cloud_authentication_runtime = auth_runtime
    app.state.community_cloud_telemetry_service = telemetry_service
    app.state.community_cloud_assessment_metadata_service = assessment_metadata_service
    app.state.community_cloud_cli_event_service = cli_event_service
    app.state.community_cloud_extension_event_service = extension_event_service
    app.state.community_cloud_ai_usage_service = ai_usage_service
    app.state.community_insights_auth_service = insights_auth
    app.state.community_insights_aggregation_service = insights_agg
    app.add_middleware(_FoundationMiddleware)

    @app.exception_handler(RequestValidationError)
    async def _canonical_request_validation_error(
        request: Request, exc: RequestValidationError
    ) -> Response:
        _ = exc
        return build_error_response(
            ERROR_INVALID_REQUEST_SCHEMA,
            http_status=422,
            api_version=_path_api_version(request.url.path) or API_VERSION_V1,
            request_id=_client_request_id(request),
        )

    @app.api_route(
        "/{full_path:path}",
        methods=sorted(SUPPORTED_METHODS),
        include_in_schema=False,
    )
    async def _dispatch(full_path: str, request: Request) -> Response:
        return await _handle_request(
            request,
            active_registry,
            payload_policy=active_payload_policy,
            logging_policy=active_logging_policy,
            logger=active_logger,
            rate_limit_runtime=rate_limit_runtime,
            auth_runtime=auth_runtime,
        )

    return app


async def _handle_request(
    request: Request,
    registry: RouteRegistry,
    *,
    payload_policy: PayloadLimitPolicy,
    logging_policy: CommunityLoggingPolicy,
    logger: CommunityCloudLogger,
    rate_limit_runtime: RateLimitRuntime,
    auth_runtime: object,
) -> Response:
    client_request_id = _client_request_id(request)
    path = request.url.path or "/"
    method = request.method.upper()
    version = _path_api_version(path)
    content_type = normalize_content_type(request.headers.get("content-type"))
    client_host = asgi_client_host(request.scope.get("client"))

    log_ctx = begin_request_logging(
        logger=logger,
        policy=logging_policy,
        api_version=version or API_VERSION_V1,
        method=method,
        route=path,
        client_request_id=client_request_id,
        client_host=client_host,
    )

    # Client-supplied request id only — auto-generated logging ids stay off-body.
    context = RequestContext(
        api_version=version or API_VERSION_V1,
        method=method,
        path=path,
        request_id=client_request_id,
        content_type=content_type,
        accepted_json=True,
        cookie_header=request.headers.get("cookie"),
        origin_header=request.headers.get("origin"),
        referer_header=request.headers.get("referer"),
    )

    def _finish(response: Response, *, error_code: str | None = None) -> Response:
        finish_request_logging(
            logger=logger,
            context=log_ctx,
            status_code=response.status_code,
            error_code=error_code,
        )
        return response

    if version is None:
        return _finish(
            build_error_response(
                ERROR_NOT_FOUND,
                http_status=404,
                api_version=API_VERSION_V1,
                request_id=client_request_id,
            ),
            error_code=ERROR_NOT_FOUND,
        )

    if version not in SUPPORTED_API_VERSIONS:
        return _finish(
            build_error_response(
                ERROR_VERSION_NOT_SUPPORTED,
                http_status=404,
                api_version=API_VERSION_V1,
                request_id=client_request_id,
                details={"requested_version": version},
            ),
            error_code=ERROR_VERSION_NOT_SUPPORTED,
        )

    relative = _relative_path(path, version)
    spec = registry.get(version=version, method=method, path=relative)
    if spec is None:
        other_methods = sorted(
            {
                item.method
                for item in registry.list_routes()
                if item.version == version and item.path == relative
            }
        )
        if other_methods:
            return _finish(
                build_error_response(
                    ERROR_METHOD_NOT_ALLOWED,
                    http_status=405,
                    api_version=version,
                    request_id=client_request_id,
                    details={"allowed_methods": other_methods},
                ),
                error_code=ERROR_METHOD_NOT_ALLOWED,
            )
        return _finish(
            build_error_response(
                ERROR_NOT_FOUND,
                http_status=404,
                api_version=version,
                request_id=client_request_id,
            ),
            error_code=ERROR_NOT_FOUND,
        )

    log_ctx = log_ctx.with_route_name(spec.name)
    handler = registry.get_handler(spec)
    if handler is None:
        return _finish(
            build_error_response(
                ERROR_NOT_FOUND,
                http_status=404,
                api_version=version,
                request_id=client_request_id,
                details={"reason": "endpoint_not_implemented"},
            ),
            error_code=ERROR_NOT_FOUND,
        )

    # Slice 7.13: authenticate after route/method resolution, before rate limit/body.
    from codestrata_platform.community_cloud_api.authentication.middleware import (
        AuthenticationRuntime,
    )
    from codestrata_platform.community_cloud_api.authentication.responses import (
        decision_error_code as auth_decision_error_code,
    )

    assert isinstance(auth_runtime, AuthenticationRuntime)
    auth_decision, auth_response = auth_runtime.evaluate_route(
        route=spec,
        request=request,
        logger=logger,
        log_ctx=log_ctx,
        api_version=version,
        request_id=client_request_id,
    )
    if auth_response is not None:
        # Pre-auth transport throttle for failed authentication attempts.
        if auth_decision.status in {"missing", "invalid", "inactive"}:
            attempt_decision, attempt_limited = rate_limit_runtime.evaluate_route(
                route=spec,
                asgi_client_host=client_host,
                logger=logger,
                log_ctx=log_ctx,
                api_version=version,
                request_id=client_request_id,
                auth_attempt=True,
            )
            if attempt_limited is not None:
                from codestrata_platform.community_cloud_api.rate_limiting.responses import (
                    decision_error_code as rl_code,
                )

                return _finish(
                    attempt_limited,
                    error_code=rl_code(attempt_decision) if attempt_decision else None,
                )
        return _finish(
            auth_response,
            error_code=auth_decision_error_code(auth_decision),
        )

    if auth_decision.authenticated and auth_decision.principal is not None:
        context = context.with_authenticated_client(auth_decision.principal)

    # Slice 7.12/7.13: rate limit after auth; authenticated scope for ingestion.
    auth_scope_id = (
        auth_decision.principal.rate_limit_scope_id
        if auth_decision.authenticated and auth_decision.principal is not None
        else None
    )
    decision, limited_response = rate_limit_runtime.evaluate_route(
        route=spec,
        asgi_client_host=client_host,
        logger=logger,
        log_ctx=log_ctx,
        api_version=version,
        request_id=client_request_id,
        authenticated_rate_limit_scope_id=auth_scope_id,
    )
    if limited_response is not None:
        from codestrata_platform.community_cloud_api.rate_limiting.responses import (
            decision_error_code,
        )

        return _finish(
            limited_response,
            error_code=decision_error_code(decision) if decision else None,
        )

    schema = registry.get_request_schema(spec)
    body = b""
    if schema is not None:
        body = await request.body()
        result = validate_request_body(
            descriptor=schema,
            body=body,
            content_type=content_type,
            route_name=spec.name,
        )
        _ = build_safe_diagnostic(route_name=spec.name, result=result)
        _ = validation_logging_diagnostic(route_name=spec.name, result=result)
        if not result.valid:
            logger.validation_failed(
                log_ctx,
                status_code=int(result.http_status or 400),
                error_code=str(result.error_code or ERROR_INVALID_REQUEST_SCHEMA),
            )
            envelope = build_validation_error_response(
                result,
                api_version=version,
                request_id=client_request_id,
            )
            return _finish(
                build_json_response(
                    envelope,
                    status_code=int(result.http_status or 400),
                    api_version=version,
                    request_id=client_request_id,
                ),
                error_code=str(result.error_code or ERROR_INVALID_REQUEST_SCHEMA),
            )
        if result.model is not None:
            context = context.with_validated_request(result.model)
            from codestrata_platform.community_cloud_api.authentication.client_matching import (
                extract_payload_client_type,
            )

            mismatch = auth_runtime.enforce_client_payload_match(
                decision=auth_decision,
                payload_client_type=extract_payload_client_type(result.model),
                api_version=version,
                request_id=client_request_id,
                logger=logger,
                log_ctx=log_ctx,
                route_id=spec.name,
            )
            if mismatch is not None:
                return _finish(mismatch, error_code="client_not_authorized")

        parsed_for_limits = None
        if body:
            try:
                parsed_for_limits = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                parsed_for_limits = None
        limit_result, limit_diagnostic = evaluate_payload_limits(
            body=body,
            policy=payload_policy,
            parsed=parsed_for_limits,
            route_name=spec.name,
        )
        _ = limit_diagnostic
        _ = payload_logging_diagnostic(route_name=spec.name, result=limit_result)
        if not limit_result.ok:
            logger.payload_rejected(
                log_ctx,
                status_code=int(limit_result.http_status or 413),
                error_code=str(limit_result.error_code or "payload_too_large"),
            )
            return _finish(
                build_payload_limit_error_response(
                    limit_result,
                    api_version=version,
                    request_id=client_request_id,
                ),
                error_code=str(limit_result.error_code or "payload_too_large"),
            )

    response = handler(context)
    response = rate_limit_runtime.attach_allowed_headers(response, decision)
    if spec.name == "health.get" and response.status_code == 200:
        logger.health_checked(log_ctx, status_code=response.status_code)
    return _finish(response)


def _client_request_id(request: Request) -> str | None:
    raw = request.headers.get(REQUEST_ID_HEADER) or request.headers.get("X-Correlation-Id")
    if raw is None:
        return None
    text = raw.strip()
    return text or None


def _path_api_version(path: str) -> str | None:
    parts = [item for item in path.split("/") if item]
    if len(parts) < 2:
        return None
    if parts[0] != API_ROOT_PREFIX.strip("/"):
        return None
    return parts[1]


def _relative_path(path: str, version: str) -> str:
    prefix = f"{API_ROOT_PREFIX}/{version}"
    if path == prefix or path == prefix + "/":
        return "/"
    if path.startswith(prefix + "/"):
        relative = path[len(prefix) :]
        return relative if relative.startswith("/") else f"/{relative}"
    return path
