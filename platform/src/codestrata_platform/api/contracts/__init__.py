"""Platform API contract constants (versioning metadata)."""

from __future__ import annotations

# URL major version — breaking changes require a new major path (e.g. /api/v2).
API_MAJOR_VERSION = "v1"
API_VERSION_HEADER = "X-CodeStrata-API-Version"

# Public contract policy (documented; additive within major).
VERSION_POLICY = (
    "Platform REST contracts are versioned by URL major (`/api/v1`). "
    "Additive, backward-compatible fields may appear within a major. "
    "Breaking changes require a new major path and updated clients."
)

__all__ = [
    "API_MAJOR_VERSION",
    "API_VERSION_HEADER",
    "VERSION_POLICY",
]
