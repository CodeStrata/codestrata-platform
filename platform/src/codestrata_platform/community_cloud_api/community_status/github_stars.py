"""Bounded in-process GitHub metadata cache (repo + latest published release).

No browser tokens. No GitHub PAT required for public low-volume lookup.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

from codestrata_platform.community_cloud_api.community_status.models import (
    GITHUB_OWNER,
    GITHUB_REPO,
    GITHUB_REPOSITORY,
    GITHUB_URL,
)

DEFAULT_METADATA_TTL_SECONDS = 300.0
# Backward-compatible alias used by prior status wiring.
DEFAULT_STARS_TTL_SECONDS = DEFAULT_METADATA_TTL_SECONDS

GITHUB_REPO_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
GITHUB_LATEST_RELEASE_API_URL = (
    f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
)
USER_AGENT = "codestrata-community-status/1.0"

VERSION_SOURCE_GITHUB_RELEASE = "github_release"
VERSION_SOURCE_RELEASE_CANDIDATE = "release_candidate"
VERSION_SOURCE_UNAVAILABLE = "unavailable"

Clock = Callable[[], float]
Opener = Callable[[str], dict[str, Any] | None]


@dataclass(frozen=True, slots=True)
class CachedGitHubMetadata:
    """Cached public GitHub fields for Community Status."""

    stars: int | None
    github_repository: str
    github_url: str
    release_version: str | None
    fetched_at: float
    source: str  # live | cache | unavailable
    release_lookup_ok: bool


# Backward-compatible name used by existing imports/tests.
CachedStars = CachedGitHubMetadata


def normalize_release_tag(tag: str) -> str:
    """Normalize a GitHub release tag to a bare semver-like string.

    ``v0.2.0`` / ``V0.2.0`` → ``0.2.0``. Does not invent versions.
    """

    text = (tag or "").strip()
    if text.lower().startswith("v") and len(text) > 1 and text[1].isdigit():
        return text[1:]
    return text


def resolve_candidate_engine_version() -> str:
    """Runtime/package candidate version (internal consistency / fallback only)."""

    try:
        from codestrata import __version__ as engine_version
    except Exception:  # noqa: BLE001
        return "0.0.0-unavailable"
    return str(engine_version)


class GitHubMetadataCache:
    """Process-local TTL cache for public repo metadata + latest published release.

    Fail-soft: transport/parse failures return last-known values when present.
    Never raises to callers for transport failures.
    """

    def __init__(
        self,
        *,
        ttl_seconds: float = DEFAULT_METADATA_TTL_SECONDS,
        clock: Clock | None = None,
        opener: Opener | None = None,
    ) -> None:
        self._ttl = max(30.0, float(ttl_seconds))
        self._clock = clock or time.time
        self._opener = opener or _default_fetch
        self._cached: CachedGitHubMetadata | None = None

    @property
    def ttl_seconds(self) -> float:
        return self._ttl

    def get(self) -> CachedGitHubMetadata:
        now = float(self._clock())
        if self._cached is not None and (now - self._cached.fetched_at) < self._ttl:
            return CachedGitHubMetadata(
                stars=self._cached.stars,
                github_repository=self._cached.github_repository,
                github_url=self._cached.github_url,
                release_version=self._cached.release_version,
                fetched_at=self._cached.fetched_at,
                source="cache",
                release_lookup_ok=self._cached.release_lookup_ok,
            )

        try:
            repo = self._opener(GITHUB_REPO_API_URL)
            if not isinstance(repo, dict):
                raise ValueError("invalid repo payload")
            stars = repo.get("stargazers_count")
            if not isinstance(stars, int) or stars < 0:
                raise ValueError("invalid stargazers_count")
            full_name = str(repo.get("full_name") or "").strip() or GITHUB_REPOSITORY
            html_url = str(repo.get("html_url") or "").strip() or GITHUB_URL

            release_version: str | None = None
            release_lookup_ok = True
            release = self._opener(GITHUB_LATEST_RELEASE_API_URL)
            if release is None:
                # 404 / no published release — candidate fallback path.
                release_lookup_ok = True
                release_version = None
            elif not isinstance(release, dict):
                raise ValueError("invalid release payload")
            else:
                if bool(release.get("draft")) or bool(release.get("prerelease")):
                    # releases/latest should not return these; treat as absent.
                    release_version = None
                else:
                    tag = str(release.get("tag_name") or "").strip()
                    release_version = normalize_release_tag(tag) if tag else None

            self._cached = CachedGitHubMetadata(
                stars=stars,
                github_repository=full_name,
                github_url=html_url,
                release_version=release_version,
                fetched_at=now,
                source="live",
                release_lookup_ok=release_lookup_ok,
            )
            return self._cached
        except Exception:  # noqa: BLE001 — fail-soft
            if self._cached is not None:
                return CachedGitHubMetadata(
                    stars=self._cached.stars,
                    github_repository=self._cached.github_repository,
                    github_url=self._cached.github_url,
                    release_version=self._cached.release_version,
                    fetched_at=self._cached.fetched_at,
                    source="cache",
                    release_lookup_ok=self._cached.release_lookup_ok,
                )
            return CachedGitHubMetadata(
                stars=None,
                github_repository=GITHUB_REPOSITORY,
                github_url=GITHUB_URL,
                release_version=None,
                fetched_at=now,
                source="unavailable",
                release_lookup_ok=False,
            )


# Backward-compatible alias.
GitHubStarsCache = GitHubMetadataCache


def _default_fetch(url: str) -> dict[str, Any] | None:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=4.0) as response:  # noqa: S310
            raw = response.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise TypeError("expected object")
    return data


__all__ = [
    "CachedGitHubMetadata",
    "CachedStars",
    "DEFAULT_METADATA_TTL_SECONDS",
    "DEFAULT_STARS_TTL_SECONDS",
    "GITHUB_LATEST_RELEASE_API_URL",
    "GITHUB_REPO_API_URL",
    "GitHubMetadataCache",
    "GitHubStarsCache",
    "VERSION_SOURCE_GITHUB_RELEASE",
    "VERSION_SOURCE_RELEASE_CANDIDATE",
    "VERSION_SOURCE_UNAVAILABLE",
    "normalize_release_tag",
    "resolve_candidate_engine_version",
]
