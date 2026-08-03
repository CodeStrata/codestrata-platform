"""AWS Lambda entry point for the Community Cloud ASGI application."""

from __future__ import annotations

from typing import Any

from codestrata_platform.community_cloud_api.deployment.wiring import (
    create_production_foundation_app,
)

_app = None
_handler = None


def get_app():
    """Lazily create the production-foundation FastAPI application."""

    global _app
    if _app is None:
        _app = create_production_foundation_app()
    return _app


def get_handler():
    """Lazily create the Mangum ASGI-to-Lambda adapter."""

    global _handler
    if _handler is None:
        from mangum import Mangum

        _handler = Mangum(get_app(), lifespan="off")
    return _handler


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler — forwards API Gateway HTTP API events to FastAPI."""

    return get_handler()(event, context)
