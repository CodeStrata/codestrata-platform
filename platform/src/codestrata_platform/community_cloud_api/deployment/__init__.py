"""Community Cloud API Lambda / container deployment adapters (Slice 7.14)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.deployment.lambda_handler import (
    get_handler,
    handler,
)
from codestrata_platform.community_cloud_api.deployment.settings import (
    DeploymentSettings,
    load_deployment_settings,
)
from codestrata_platform.community_cloud_api.deployment.wiring import (
    create_production_foundation_app,
)

__all__ = [
    "DeploymentSettings",
    "create_production_foundation_app",
    "get_handler",
    "handler",
    "load_deployment_settings",
]
