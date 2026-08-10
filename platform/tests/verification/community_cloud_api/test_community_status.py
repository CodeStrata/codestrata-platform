"""Community Status endpoint tests (Slice 17.23 / 17.25)."""

from __future__ import annotations

from starlette.testclient import TestClient

from codestrata_platform.community_cloud_api.app import create_community_cloud_app
from codestrata_platform.community_cloud_api.community_status.github_stars import (
    GITHUB_LATEST_RELEASE_API_URL,
    GITHUB_REPO_API_URL,
    GitHubMetadataCache,
    normalize_release_tag,
)
from codestrata_platform.community_cloud_api.community_status.service import (
    CommunityStatusService,
    resolve_public_engine_version,
)


def _opener_factory(repo: dict, release: dict | None):
    def opener(url: str):
        if url == GITHUB_REPO_API_URL:
            return repo
        if url == GITHUB_LATEST_RELEASE_API_URL:
            return release
        raise AssertionError(url)

    return opener


def test_normalize_release_tag() -> None:
    assert normalize_release_tag("v0.2.0") == "0.2.0"
    assert normalize_release_tag("0.2.0") == "0.2.0"
    assert normalize_release_tag("V1.0.0") == "1.0.0"


def test_resolve_public_engine_version_github_and_candidate() -> None:
    assert resolve_public_engine_version(
        release_version="0.1.0",
        candidate_version="0.2.0",
        github_lookup_ok=True,
    ) == ("0.1.0", "github_release")
    assert resolve_public_engine_version(
        release_version=None,
        candidate_version="0.2.0",
        github_lookup_ok=True,
    ) == ("0.2.0", "release_candidate")


def test_community_status_uses_github_metadata() -> None:
    cache = GitHubMetadataCache(
        opener=_opener_factory(
            {
                "full_name": "CodeStrata/codestrata-engine",
                "html_url": "https://github.com/CodeStrata/codestrata-engine",
                "stargazers_count": 42,
            },
            {"tag_name": "v0.1.0", "draft": False, "prerelease": False},
        )
    )
    service = CommunityStatusService(
        metadata_cache=cache, engine_version_provider=lambda: "0.2.0"
    )
    payload = service.build().to_stable_dict()
    assert payload["engine_version"] == "0.1.0"
    assert payload["github_stars"] == 42
    assert payload["github_repository"] == "CodeStrata/codestrata-engine"
    assert payload["github_url"] == "https://github.com/CodeStrata/codestrata-engine"
    assert "version_source" not in payload
    view = service.build_verification_view()
    assert view["version_source"] == "github_release"
    assert view["package_candidate_version"] == "0.2.0"
    assert view["package_github_release_mismatch"] is True


def test_community_status_candidate_when_no_release() -> None:
    cache = GitHubMetadataCache(
        opener=_opener_factory(
            {
                "full_name": "CodeStrata/codestrata-engine",
                "html_url": "https://github.com/CodeStrata/codestrata-engine",
                "stargazers_count": 7,
            },
            None,
        )
    )
    service = CommunityStatusService(
        metadata_cache=cache, engine_version_provider=lambda: "0.2.0"
    )
    built = service.build()
    assert built.engine_version == "0.2.0"
    assert built.version_source == "release_candidate"
    assert built.github_stars == 7


def test_community_status_failsoft() -> None:
    down = GitHubMetadataCache(opener=lambda _url: (_ for _ in ()).throw(RuntimeError("x")))
    degraded = CommunityStatusService(
        metadata_cache=down, engine_version_provider=lambda: "0.2.0"
    ).build()
    assert degraded.engine_version == "0.2.0"
    assert degraded.github_stars is None
    assert degraded.status == "degraded"
    assert degraded.github_repository == "CodeStrata/codestrata-engine"


def test_skips_draft_and_prerelease() -> None:
    cache = GitHubMetadataCache(
        opener=_opener_factory(
            {
                "full_name": "CodeStrata/codestrata-engine",
                "html_url": "https://github.com/CodeStrata/codestrata-engine",
                "stargazers_count": 1,
            },
            {"tag_name": "v0.2.0", "draft": False, "prerelease": True},
        )
    )
    built = CommunityStatusService(
        metadata_cache=cache, engine_version_provider=lambda: "0.2.0"
    ).build()
    assert built.engine_version == "0.2.0"
    assert built.version_source == "release_candidate"


def test_community_status_route_registered() -> None:
    app = create_community_cloud_app()
    client = TestClient(app)
    response = client.get(
        "/api/v1/community/status",
        headers={"Origin": "https://codestrata.ai"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["engine_version"]
    assert "github_stars" in body
    assert "version_source" not in body
    assert response.headers.get("access-control-allow-origin") == "https://codestrata.ai"
    assert "account" not in str(body).lower()
    assert "AKIA" not in str(body)
