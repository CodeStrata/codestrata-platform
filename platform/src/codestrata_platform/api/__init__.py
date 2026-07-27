"""Commercial Platform REST API transport layer.

Thin FastAPI adapters over Application Services. No business logic.
"""

from __future__ import annotations

from codestrata_platform.api.app import create_app

__all__ = ["create_app"]
