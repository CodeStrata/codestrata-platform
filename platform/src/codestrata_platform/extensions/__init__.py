"""Platform extension entry points for the Community Engine."""

from __future__ import annotations

from codestrata_platform.extensions.cli import (
    register_ai_cli,
    register_enterprise_cli,
    register_repository_cli,
)
from codestrata_platform.extensions.mcp import register_platform_mcp

__all__ = [
    "register_ai_cli",
    "register_enterprise_cli",
    "register_platform_mcp",
    "register_repository_cli",
]
