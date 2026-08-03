"""Central versioned route registry for the Community Cloud API."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from codestrata_platform.community_cloud_api.constants import (
    API_PREFIX_V1,
    API_ROOT_PREFIX,
    API_VERSION_V1,
    SUPPORTED_API_VERSIONS,
    SUPPORTED_METHODS,
)
from codestrata_platform.community_cloud_api.models import ApiDiagnostics

if TYPE_CHECKING:
    from codestrata_platform.community_cloud_api.models import RequestContext
    from codestrata_platform.community_cloud_api.validation.models import (
        RequestSchemaDescriptor,
    )
    from starlette.responses import Response

    RouteHandler = Callable[[RequestContext], Response]
else:
    RouteHandler = Callable[..., object]
    RequestSchemaDescriptor = object  # type: ignore[misc,assignment]


@dataclass(frozen=True, slots=True)
class RouteSpec:
    """Declarative route registration entry."""

    version: str
    method: str
    path: str
    name: str
    # Additive metadata — excluded from identity_key().
    rate_limit_group: str = "ingestion"
    authentication_group: str = "community_ingestion"

    def __post_init__(self) -> None:
        from codestrata_platform.community_cloud_api.authentication.models import (
            VALID_AUTH_GROUPS,
        )
        from codestrata_platform.community_cloud_api.rate_limiting.models import (
            VALID_RATE_LIMIT_GROUPS,
        )

        version = (self.version or "").strip()
        method = (self.method or "").strip().upper()
        path = (self.path or "").strip()
        name = (self.name or "").strip()
        group = (self.rate_limit_group or "").strip()
        auth_group = (self.authentication_group or "").strip()
        if version not in SUPPORTED_API_VERSIONS:
            raise ValueError(f"unsupported API version: {version}")
        if method not in SUPPORTED_METHODS:
            raise ValueError(f"unsupported HTTP method: {method}")
        if not path.startswith("/"):
            raise ValueError("route path must start with '/'")
        if not name:
            raise ValueError("route name is required")
        if "{" in path or "}" in path:
            raise ValueError("parameterized paths are not registered yet")
        if group not in VALID_RATE_LIMIT_GROUPS:
            raise ValueError(f"invalid rate_limit_group: {group}")
        if auth_group not in VALID_AUTH_GROUPS:
            raise ValueError(f"invalid authentication_group: {auth_group}")
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "method", method)
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "rate_limit_group", group)
        object.__setattr__(self, "authentication_group", auth_group)

    @property
    def absolute_path(self) -> str:
        return f"{API_ROOT_PREFIX}/{self.version}{self.path}"

    def identity_key(self) -> tuple[str, str, str]:
        return (self.version, self.method, self.path)


class RouteRegistry:
    """Central registry — the only place route declarations are stored."""

    def __init__(self) -> None:
        self._routes: dict[tuple[str, str, str], RouteSpec] = {}
        self._handlers: dict[tuple[str, str, str], RouteHandler] = {}
        self._request_schemas: dict[tuple[str, str, str], RequestSchemaDescriptor] = {}
        self._schema_ids: set[tuple[str, str]] = set()

    def register(
        self,
        spec: RouteSpec,
        *,
        handler: RouteHandler | None = None,
        request_schema: RequestSchemaDescriptor | None = None,
    ) -> None:
        key = spec.identity_key()
        if key in self._routes:
            raise ValueError(f"duplicate route registration: {key}")
        for existing in self._routes.values():
            if existing.version == spec.version and existing.name == spec.name:
                raise ValueError(f"duplicate route name for {spec.version}: {spec.name}")
        if request_schema is not None:
            schema_key = request_schema.identity_key()
            # Same schema_id/version may be reused across routes; reject only when
            # an identical schema_id is rebound with a conflicting version string
            # already tracked under a different descriptor identity for this registry
            # instance. Duplicate route+schema is fine; duplicate schema_id with
            # different version in one registry is rejected for determinism.
            for existing_id, existing_version in self._schema_ids:
                if existing_id == schema_key[0] and existing_version != schema_key[1]:
                    raise ValueError(
                        f"conflicting schema version for {schema_key[0]}: "
                        f"{existing_version} vs {schema_key[1]}"
                    )
            self._schema_ids.add(schema_key)
        self._routes[key] = spec
        if handler is not None:
            self._handlers[key] = handler
        if request_schema is not None:
            self._request_schemas[key] = request_schema

    def bind_request_schema(
        self,
        spec: RouteSpec,
        descriptor: RequestSchemaDescriptor,
    ) -> None:
        key = spec.identity_key()
        if key not in self._routes:
            raise ValueError(f"route is not registered: {key}")
        if key in self._request_schemas:
            raise ValueError(f"duplicate request schema for route: {key}")
        schema_key = descriptor.identity_key()
        for existing_id, existing_version in self._schema_ids:
            if existing_id == schema_key[0] and existing_version != schema_key[1]:
                raise ValueError(
                    f"conflicting schema version for {schema_key[0]}: "
                    f"{existing_version} vs {schema_key[1]}"
                )
        self._schema_ids.add(schema_key)
        self._request_schemas[key] = descriptor

    def get(self, *, version: str, method: str, path: str) -> RouteSpec | None:
        return self._routes.get((version, method.upper(), path))

    def get_handler(self, spec: RouteSpec) -> RouteHandler | None:
        return self._handlers.get(spec.identity_key())

    def get_request_schema(self, spec: RouteSpec) -> RequestSchemaDescriptor | None:
        return self._request_schemas.get(spec.identity_key())

    def list_routes(self) -> tuple[RouteSpec, ...]:
        return tuple(
            sorted(
                self._routes.values(),
                key=lambda item: (item.version, item.method, item.path, item.name),
            )
        )

    def list_request_schemas(self) -> tuple[RequestSchemaDescriptor, ...]:
        return tuple(
            sorted(
                self._request_schemas.values(),
                key=lambda item: (item.schema_id, item.schema_version),
            )
        )

    def list_versions(self) -> tuple[str, ...]:
        return SUPPORTED_API_VERSIONS

    def prefix_for_version(self, version: str) -> str:
        if version not in SUPPORTED_API_VERSIONS:
            raise ValueError(f"unsupported API version: {version}")
        return f"{API_ROOT_PREFIX}/{version}"

    def diagnostics(self) -> ApiDiagnostics:
        return ApiDiagnostics(
            registered_route_count=len(self._routes),
            supported_version_count=len(SUPPORTED_API_VERSIONS),
            api_version=API_VERSION_V1,
        )

    @classmethod
    def foundation_v1(
        cls,
        *,
        telemetry_service: object | None = None,
        assessment_metadata_service: object | None = None,
        cli_event_service: object | None = None,
        extension_event_service: object | None = None,
        ai_usage_service: object | None = None,
    ) -> RouteRegistry:
        """v1 registry: health, telemetry, metadata, cli, extension, ai-usage."""

        from codestrata_platform.community_cloud_api.ai_usage.routes import (
            register_ai_usage_routes,
        )
        from codestrata_platform.community_cloud_api.ai_usage.service import IngestAiUsage
        from codestrata_platform.community_cloud_api.assessment_metadata.routes import (
            register_assessment_metadata_routes,
        )
        from codestrata_platform.community_cloud_api.assessment_metadata.service import (
            IngestAssessmentMetadata,
        )
        from codestrata_platform.community_cloud_api.cli_events.routes import (
            register_cli_event_routes,
        )
        from codestrata_platform.community_cloud_api.cli_events.service import (
            IngestCliEvent,
        )
        from codestrata_platform.community_cloud_api.extension_events.routes import (
            register_extension_event_routes,
        )
        from codestrata_platform.community_cloud_api.extension_events.service import (
            IngestExtensionEvent,
        )
        from codestrata_platform.community_cloud_api.health.routes import (
            register_health_routes,
        )
        from codestrata_platform.community_cloud_api.telemetry.routes import (
            register_telemetry_routes,
        )
        from codestrata_platform.community_cloud_api.telemetry.service import (
            IngestTelemetryEvent,
        )

        registry = cls()
        assert registry.prefix_for_version(API_VERSION_V1) == API_PREFIX_V1
        register_health_routes(registry)
        tel_service = telemetry_service if isinstance(
            telemetry_service, IngestTelemetryEvent
        ) else IngestTelemetryEvent()
        register_telemetry_routes(registry, service=tel_service)
        meta_service = assessment_metadata_service if isinstance(
            assessment_metadata_service, IngestAssessmentMetadata
        ) else IngestAssessmentMetadata()
        register_assessment_metadata_routes(registry, service=meta_service)
        cli_service = cli_event_service if isinstance(
            cli_event_service, IngestCliEvent
        ) else IngestCliEvent()
        register_cli_event_routes(registry, service=cli_service)
        ext_service = extension_event_service if isinstance(
            extension_event_service, IngestExtensionEvent
        ) else IngestExtensionEvent()
        register_extension_event_routes(registry, service=ext_service)
        ai_service = ai_usage_service if isinstance(
            ai_usage_service, IngestAiUsage
        ) else IngestAiUsage()
        register_ai_usage_routes(registry, service=ai_service)
        return registry
