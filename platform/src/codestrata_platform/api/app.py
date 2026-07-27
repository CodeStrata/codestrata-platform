"""FastAPI application factory for the Commercial Platform REST API."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from codestrata_platform.api.configuration.dependencies import (
    install_artifact_storage,
    install_memory_stores,
)
from codestrata_platform.api.configuration.settings import ApiSettings
from codestrata_platform.api.controllers import build_api_router
from codestrata_platform.api.exception import register_exception_handlers


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
        description=(
            "REST transport for CodeStrata Commercial Platform capabilities. "
            "Exposes Application Services only; no Domain or persistence leakage."
        ),
        lifespan=lifespan,
        openapi_tags=[
            {"name": "Organizations", "description": "Organization lifecycle"},
            {"name": "Workspaces", "description": "Workspace lifecycle"},
            {"name": "Repositories", "description": "Repository Registry"},
            {"name": "Assessments", "description": "Assessment records"},
            {
                "name": "Ingestion",
                "description": "Engine → Platform assessment ingestion contract",
            },
            {
                "name": "Ingestion Artifacts",
                "description": "Opt-in assessment artifact ingestion",
            },
        ],
    )
    register_exception_handlers(app)
    app.include_router(build_api_router())

    @app.get("/health", tags=["Health"], summary="Health check")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": resolved.version}

    return app
