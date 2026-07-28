"""FastAPI application factory for the CodeStrata Platform REST API."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from codestrata_platform.api.configuration.dependencies import (
    install_artifact_storage,
    install_memory_stores,
)
from codestrata_platform.api.configuration.settings import ApiSettings
from codestrata_platform.api.contracts import API_MAJOR_VERSION, API_VERSION_HEADER, VERSION_POLICY
from codestrata_platform.api.controllers import build_api_router
from codestrata_platform.api.correlation import RequestCorrelationMiddleware
from codestrata_platform.api.dto.common import HealthResponseDto, ReadyResponseDto
from codestrata_platform.api.exception import register_exception_handlers
from codestrata_platform.api.security import (
    PLATFORM_API_KEY_ENV,
    PlatformApiKeyMiddleware,
    assert_production_auth_configuration,
    resolve_platform_api_key,
    resolve_platform_env,
)

# platform/src/codestrata_platform/api/app.py → platform/api/openapi
_OPENAPI_ROOT = Path(__file__).resolve().parents[3] / "api" / "openapi"
_SWAGGER_ROOT = _OPENAPI_ROOT / "swagger"

_OPENAPI_DESCRIPTION = """\
CodeStrata Platform REST API (`/api/v1`).

## Product boundary

**CodeStrata Platform** is the multi-user product surface: organizations, workspaces,
repository registry, Engineering Assessment records, Engineering Snapshot,
Engineering Knowledge Graph, Repository Retrieval and Answering, Portfolio
Intelligence, Executive Intelligence, and Strategic Roadmap.

**CodeStrata Engine** (Community) runs local assessments and optional AI enrichment
without this API. Local MCP tools expose Engine knowledge; Platform MCP extensions
are separate. Do not confuse Platform API credentials with optional AI provider
credentials used by the Engine.

## Authentication

When `{api_key_env}` is set, send `Authorization: Bearer <api-key>` on every
request except `/health` and `/ready`. Development may omit the key; production
requires it. This shared secret is **not** an AI provider token.

## Errors

Failures use a stable envelope:
`{{"error": {{"code", "message", "details?", "correlation_id?"}}}}`.
Validation failures return HTTP 422 with bounded field errors. Missing or invalid
API credentials return HTTP 401. Correlation ids are also echoed in
`X-Correlation-Id` / `X-Request-Id` headers.

## Feature flags

Some capabilities are gated by environment flags (default off), including
answering, portfolio retrieval/answering, executive intelligence/presentation,
strategic roadmap, and retrieval indexing. Disabled features return clear
application errors rather than silent empty success.

## Versioning

{version_policy}

Responses include header `{version_header}: {api_major}`.
OpenAPI `info.version` is `{api_major}`.

Visual branding follows `governance/assets/DESIGN-SYSTEM.md`.
""".format(
    api_key_env=PLATFORM_API_KEY_ENV,
    version_policy=VERSION_POLICY,
    version_header=API_VERSION_HEADER,
    api_major=API_MAJOR_VERSION,
)

_OPENAPI_TAGS: list[dict[str, str]] = [
    {
        "name": "Organizations",
        "description": "Organization lifecycle for multi-user Platform tenancy.",
    },
    {
        "name": "Workspaces",
        "description": "Workspace lifecycle within an organization.",
    },
    {
        "name": "Repositories",
        "description": "Repository Registry — tracked engineering repositories.",
    },
    {
        "name": "Assessments",
        "description": "Engineering Assessment records registered on the Platform.",
    },
    {
        "name": "Assessment Intelligence",
        "description": "Findings, metrics, and recommendations for an assessment.",
    },
    {
        "name": "Ingestion",
        "description": "Engine → Platform registration of repositories and assessments.",
    },
    {
        "name": "Ingestion Artifacts",
        "description": "Opt-in upload of assessment artifacts (reports, bundles).",
    },
    {
        "name": "Ingestion Intelligence",
        "description": "Ingest and process assessment intelligence payloads.",
    },
    {
        "name": "Engineering Intelligence",
        "description": "Engineering Snapshot build and query for Platform consumers.",
    },
    {
        "name": "Knowledge Graphs",
        "description": "Engineering Knowledge Graph lifecycle and graph reads.",
    },
    {
        "name": "Knowledge Graph Intelligence",
        "description": "Impact, traceability, coverage, and risk views over a graph.",
    },
    {
        "name": "Retrieval",
        "description": "Repository Retrieval indexes, search, and context.",
    },
    {
        "name": "Answering",
        "description": "Grounded Repository Answering over retrieval indexes.",
    },
    {
        "name": "Portfolio",
        "description": "Portfolio Intelligence — portfolios and portfolio snapshots.",
    },
    {
        "name": "Portfolio Retrieval",
        "description": "Portfolio-scoped retrieval indexes.",
    },
    {
        "name": "Portfolio Answering",
        "description": "Grounded answering across a portfolio.",
    },
    {
        "name": "Executive Intelligence",
        "description": "Executive Intelligence build and query for a portfolio.",
    },
    {
        "name": "Executive Presentation",
        "description": "On-read Executive Intelligence presentation views.",
    },
    {
        "name": "Strategic Portfolio Roadmap",
        "description": "On-read Strategic Roadmap views (Platform; not Engine roadmap).",
    },
    {
        "name": "Health",
        "description": "Liveness and readiness probes (no API key required).",
    },
]


def _internal_api_docs_enabled() -> bool:
    """Swagger is internal-only; never expose in production environments."""

    if resolve_platform_env() in {"production", "prod"}:
        return False
    flag = os.environ.get("CODESTRATA_PLATFORM_INTERNAL_API_DOCS", "1").strip().lower()
    return flag in {"1", "true", "yes", "on"}


def _mount_internal_api_docs(app: FastAPI) -> None:
    """Serve canonical OpenAPI + branded Swagger under /api/* (local/dev only)."""

    if not _internal_api_docs_enabled():
        return
    openapi_yaml = _OPENAPI_ROOT / "openapi.yaml"
    openapi_json = _OPENAPI_ROOT / "openapi.json"
    if not openapi_yaml.is_file() or not openapi_json.is_file():
        return

    @app.get("/api/openapi.yaml", include_in_schema=False)
    def serve_openapi_yaml() -> FileResponse:
        return FileResponse(
            openapi_yaml,
            media_type="application/yaml",
            filename="openapi.yaml",
        )

    @app.get("/api/openapi.json", include_in_schema=False)
    def serve_openapi_json() -> FileResponse:
        return FileResponse(
            openapi_json,
            media_type="application/json",
            filename="openapi.json",
        )

    @app.get("/api/docs", include_in_schema=False)
    def swagger_index() -> FileResponse:
        return FileResponse(_SWAGGER_ROOT / "index.html")

    if _SWAGGER_ROOT.is_dir():
        app.mount(
            "/api/docs/static",
            StaticFiles(directory=_SWAGGER_ROOT),
            name="platform-api-docs-static",
        )

    @app.get("/docs", include_in_schema=False)
    def redirect_legacy_docs() -> RedirectResponse:
        return RedirectResponse(url="/api/docs", status_code=307)


def create_app(
    *,
    settings: ApiSettings | None = None,
    use_memory: bool = False,
    database_url: str | None = None,
    artifact_storage_root: Path | None = None,
) -> FastAPI:
    """Create the Platform REST application.

    Controllers are thin adapters over Application Services.
    """

    assert_production_auth_configuration()
    resolved = settings or ApiSettings.from_env(use_memory=use_memory, database_url=database_url)
    if use_memory:
        resolved = ApiSettings(
            database_url=resolved.database_url,
            use_memory=True,
            artifact_storage_root=artifact_storage_root or resolved.artifact_storage_root,
            max_artifact_bytes=resolved.max_artifact_bytes,
            title=resolved.title,
            version=resolved.version,
        )
    elif artifact_storage_root is not None:
        resolved = ApiSettings(
            database_url=resolved.database_url,
            use_memory=resolved.use_memory,
            artifact_storage_root=artifact_storage_root,
            max_artifact_bytes=resolved.max_artifact_bytes,
            title=resolved.title,
            version=resolved.version,
        )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.max_artifact_bytes = resolved.max_artifact_bytes
        if resolved.use_memory:
            install_memory_stores(app.state)
            install_artifact_storage(app.state, use_memory=True)
        else:
            from codestrata_platform.infrastructure.persistence import (
                create_engine_from_url,
                create_platform_schema,
                create_session_factory,
            )

            engine = create_engine_from_url(resolved.database_url)
            create_platform_schema(engine)
            app.state.use_memory = False
            app.state.engine = engine
            app.state.session_factory = create_session_factory(engine)
            root = resolved.artifact_storage_root
            if root is None:
                # Ephemeral filesystem root beside the process; tests should pass an explicit root.
                root = Path.cwd() / ".codestrata-platform-artifacts"
            install_artifact_storage(app.state, root=root, use_memory=False)
        yield
        engine = getattr(app.state, "engine", None)
        if engine is not None:
            engine.dispose()

    app = FastAPI(
        title=resolved.title,
        version=resolved.version,
        description=_OPENAPI_DESCRIPTION,
        lifespan=lifespan,
        openapi_tags=_OPENAPI_TAGS,
    )
    register_exception_handlers(app)
    app.add_middleware(
        PlatformApiKeyMiddleware,
        api_key=resolve_platform_api_key(),
    )
    app.add_middleware(RequestCorrelationMiddleware)
    app.include_router(build_api_router())

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema is not None:
            return app.openapi_schema
        schema = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=app.description,
            routes=app.routes,
            tags=app.openapi_tags,
        )
        components = schema.setdefault("components", {})
        schemes = components.setdefault("securitySchemes", {})
        schemes["PlatformApiKey"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "API key",
            "description": (
                f"CodeStrata Platform shared API key from `{PLATFORM_API_KEY_ENV}`. "
                "Send as `Authorization: Bearer <api-key>`. "
                "This is not an AI provider credential (Bedrock/OpenAI/etc.)."
            ),
        }
        # Document expected auth without changing runtime middleware behavior.
        schema["security"] = [{"PlatformApiKey": []}]
        schema["servers"] = [
            {
                "url": "/",
                "description": "CodeStrata Platform API (relative to deployment host)",
            }
        ]
        schemas = components.setdefault("schemas", {})
        schemas.setdefault(
            "ErrorDetailDto",
            {
                "type": "object",
                "description": "Stable Platform API error detail",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Machine-readable error code",
                        "examples": ["unauthorized", "not_found", "validation_error"],
                    },
                    "message": {
                        "type": "string",
                        "description": "Human-readable, sanitized guidance",
                    },
                    "details": {
                        "type": "object",
                        "additionalProperties": True,
                        "nullable": True,
                        "description": "Optional structured detail",
                    },
                },
                "required": ["code", "message"],
            },
        )
        schemas.setdefault(
            "ErrorResponseDto",
            {
                "type": "object",
                "description": "Standard Platform API error envelope",
                "properties": {
                    "error": {"$ref": "#/components/schemas/ErrorDetailDto"},
                },
                "required": ["error"],
                "example": {
                    "error": {
                        "code": "unauthorized",
                        "message": (
                            "Missing or invalid Authorization header. "
                            f"Send Authorization: Bearer <key> using {PLATFORM_API_KEY_ENV}."
                        ),
                        "details": None,
                    }
                },
            },
        )
        # Golden-path request examples for SDK generation (additive documentation).
        org_post = schema["paths"].get("/api/v1/organizations", {}).get("post")
        if isinstance(org_post, dict):
            content = (
                (org_post.get("requestBody") or {})
                .get("content", {})
                .get("application/json")
            )
            if isinstance(content, dict):
                content["examples"] = {
                    "createOrganization": {
                        "summary": "Create an organization",
                        "value": {"name": "Acme Engineering"},
                    }
                }
            org_post.setdefault("responses", {}).setdefault(
                "401",
                {
                    "description": "Missing or invalid Platform API key",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ErrorResponseDto"}
                        }
                    },
                },
            )
        answers_post = schema["paths"].get("/api/v1/answers", {}).get("post")
        if isinstance(answers_post, dict):
            content = (
                (answers_post.get("requestBody") or {})
                .get("content", {})
                .get("application/json")
            )
            if isinstance(content, dict):
                content["examples"] = {
                    "askRepositoryQuestion": {
                        "summary": "Ask a grounded repository question",
                        "value": {
                            "question": "What are the highest severity findings?",
                            "organization_id": "org_example",
                            "workspace_id": "ws_example",
                            "repository_id": "repo_example",
                            "include_diagnostics": False,
                            "use_cache": True,
                        },
                    }
                }
        schema["x-codestrata-public-contract"] = {
            "api_major": "v1",
            "compatibility_policy": (
                "governance/playbooks/PUBLIC_CONTRACT_COMPATIBILITY.md"
            ),
            "error_envelope": "ErrorResponseDto",
        }
        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore[method-assign]

    @app.get(
        "/health",
        tags=["Health"],
        summary="Liveness probe",
        description="Returns process liveness. No Platform API key required.",
        response_model=HealthResponseDto,
        responses={200: {"description": "Service is alive"}},
    )
    def health() -> HealthResponseDto:
        return HealthResponseDto(status="ok", version=resolved.version)

    @app.get(
        "/ready",
        tags=["Health"],
        summary="Readiness probe",
        description=(
            "Returns readiness including persistence connectivity. "
            "No Platform API key required. HTTP 503 when not ready."
        ),
        response_model=ReadyResponseDto,
        responses={
            200: {"description": "Service is ready"},
            503: {"description": "Service is not ready"},
        },
    )
    def ready():
        from fastapi.responses import JSONResponse

        from codestrata.security.database_url import sanitize_exception_message

        checks: dict[str, str] = {"application": "ok"}
        if resolved.use_memory:
            checks["persistence"] = "memory"
            return ReadyResponseDto(
                status="ready", version=resolved.version, checks=checks
            )

        engine = getattr(app.state, "engine", None)
        if engine is None:
            return JSONResponse(
                status_code=503,
                content=ReadyResponseDto(
                    status="not_ready",
                    version=resolved.version,
                    checks={"application": "ok", "persistence": "unavailable"},
                ).model_dump(mode="json"),
            )
        try:
            from sqlalchemy import text

            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            checks["persistence"] = "ok"
        except Exception as exc:  # noqa: BLE001 - readiness must never leak DSN details
            return JSONResponse(
                status_code=503,
                content=ReadyResponseDto(
                    status="not_ready",
                    version=resolved.version,
                    checks={
                        "application": "ok",
                        "persistence": "error",
                        "detail": sanitize_exception_message(str(exc))[:200],
                    },
                ).model_dump(mode="json"),
            )
        return ReadyResponseDto(status="ready", version=resolved.version, checks=checks)

    _mount_internal_api_docs(app)
    return app
