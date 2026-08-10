"""Community Status models — public safe payload only (Slice 17.23 / 17.25)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

SCHEMA_ID = "community-status"
SCHEMA_VERSION = "1.0"

GITHUB_OWNER = "CodeStrata"
GITHUB_REPO = "codestrata-engine"
GITHUB_REPOSITORY = f"{GITHUB_OWNER}/{GITHUB_REPO}"
GITHUB_URL = f"https://github.com/{GITHUB_REPOSITORY}"

StatusLiteral = Literal["ok", "degraded"]


@dataclass(frozen=True, slots=True)
class CommunityStatusResponse:
    """Public Community Status payload — no AWS/internal identifiers.

    ``version_source`` and ``package_candidate_version`` are verification-only
    fields and are omitted from the public HTTP body.
    """

    engine_version: str
    github_stars: int | None
    github_repository: str = GITHUB_REPOSITORY
    github_url: str = GITHUB_URL
    status: StatusLiteral = "ok"
    schema_id: str = SCHEMA_ID
    schema_version: str = SCHEMA_VERSION
    github_stars_source: str = "live"
    cache_age_seconds: int | None = None
    version_source: str = "release_candidate"
    package_candidate_version: str | None = None
    github_latest_release_version: str | None = None

    def to_stable_dict(self) -> dict[str, Any]:
        # Public wire contract — website-facing fields only (+ schema/cache diagnostics).
        payload: dict[str, Any] = {
            "cache_age_seconds": self.cache_age_seconds,
            "engine_version": self.engine_version,
            "github_repository": self.github_repository,
            "github_stars": self.github_stars,
            "github_stars_source": self.github_stars_source,
            "github_url": self.github_url,
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "status": self.status,
        }
        return payload
