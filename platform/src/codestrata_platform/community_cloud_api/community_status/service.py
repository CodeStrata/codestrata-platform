"""Community Status service — GitHub public metadata + candidate version fallback."""

from __future__ import annotations

import time
from typing import Callable

from codestrata_platform.community_cloud_api.community_status.github_stars import (
    DEFAULT_METADATA_TTL_SECONDS,
    DEFAULT_STARS_TTL_SECONDS,
    GitHubMetadataCache,
    GitHubStarsCache,
    VERSION_SOURCE_GITHUB_RELEASE,
    VERSION_SOURCE_RELEASE_CANDIDATE,
    VERSION_SOURCE_UNAVAILABLE,
    resolve_candidate_engine_version,
)
from codestrata_platform.community_cloud_api.community_status.models import (
    CommunityStatusResponse,
    GITHUB_REPOSITORY,
    GITHUB_URL,
)

Clock = Callable[[], float]


def resolve_engine_version() -> str:
    """Candidate/runtime Engine package version (internal consistency check).

    Not the public Community Status source of truth after Slice 17.25 — use
    GitHub published release when available.
    """

    return resolve_candidate_engine_version()


def resolve_public_engine_version(
    *,
    release_version: str | None,
    candidate_version: str,
    github_lookup_ok: bool,
) -> tuple[str, str]:
    """Return ``(engine_version, version_source)``.

    Public ``engine_version`` uses the latest published GitHub Release tag when
    one exists (normalized, never fabricated). When no published release exists
    (or GitHub release lookup failed with no cache), fall back to the runtime
    package candidate.

    Package/candidate is an internal consistency check only — when it differs
    from the published release, the public body still reflects GitHub and
    verifiers classify the mismatch for Release Readiness.
    """

    candidate = (candidate_version or "").strip() or "0.0.0-unavailable"
    published = (release_version or "").strip() or None
    if published:
        return published, VERSION_SOURCE_GITHUB_RELEASE
    _ = github_lookup_ok
    return candidate, VERSION_SOURCE_RELEASE_CANDIDATE


class CommunityStatusService:
    def __init__(
        self,
        *,
        stars_cache: GitHubStarsCache | GitHubMetadataCache | None = None,
        metadata_cache: GitHubMetadataCache | None = None,
        clock: Clock | None = None,
        engine_version_provider: Callable[[], str] | None = None,
    ) -> None:
        cache = metadata_cache or stars_cache
        self._metadata = cache or GitHubMetadataCache(
            ttl_seconds=DEFAULT_METADATA_TTL_SECONDS
        )
        self._clock = clock or time.time
        self._candidate_version = engine_version_provider or resolve_candidate_engine_version

    @property
    def cache_control_max_age(self) -> int:
        return int(self._metadata.ttl_seconds)

    def build(self) -> CommunityStatusResponse:
        candidate = self._candidate_version()
        cached = self._metadata.get()
        now = float(self._clock())
        age: int | None = None
        if cached.fetched_at:
            age = int(max(0.0, now - cached.fetched_at))

        github_lookup_ok = cached.source != "unavailable"
        engine_version, version_source = resolve_public_engine_version(
            release_version=cached.release_version,
            candidate_version=candidate,
            github_lookup_ok=github_lookup_ok or cached.release_version is not None,
        )

        status = "ok"
        if cached.stars is None:
            status = "degraded"

        source = cached.source
        if cached.stars is None and cached.source == "unavailable":
            source = "unavailable"

        return CommunityStatusResponse(
            engine_version=engine_version,
            github_stars=cached.stars,
            github_repository=cached.github_repository or GITHUB_REPOSITORY,
            github_url=cached.github_url or GITHUB_URL,
            status=status,  # type: ignore[arg-type]
            github_stars_source=source,
            cache_age_seconds=age,
            version_source=version_source,
            package_candidate_version=candidate,
            github_latest_release_version=cached.release_version,
        )

    def build_verification_view(self) -> dict[str, object]:
        """Internal classification for verifiers (not the public HTTP body)."""

        response = self.build()
        return {
            "engine_version": response.engine_version,
            "version_source": response.version_source,
            "package_candidate_version": response.package_candidate_version,
            "github_latest_release_version": response.github_latest_release_version,
            "github_stars": response.github_stars,
            "github_repository": response.github_repository,
            "github_url": response.github_url,
            "status": response.status,
            "package_matches_public": (
                response.package_candidate_version == response.engine_version
            ),
            "awaiting_matching_github_release": (
                response.version_source == VERSION_SOURCE_RELEASE_CANDIDATE
                or (
                    response.github_latest_release_version is not None
                    and response.github_latest_release_version
                    != response.package_candidate_version
                )
            ),
            "package_github_release_mismatch": (
                response.github_latest_release_version is not None
                and response.package_candidate_version
                != response.github_latest_release_version
            ),
        }


__all__ = [
    "CommunityStatusService",
    "DEFAULT_STARS_TTL_SECONDS",
    "VERSION_SOURCE_GITHUB_RELEASE",
    "VERSION_SOURCE_RELEASE_CANDIDATE",
    "VERSION_SOURCE_UNAVAILABLE",
    "resolve_engine_version",
    "resolve_public_engine_version",
]
