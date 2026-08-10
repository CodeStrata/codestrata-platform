"""Load exactly 22 release_validation catalog repositories."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from verification.community_22_repository_validation.contract import (
    CATALOG_RELATIVE,
    REPOSITORY_TARGET,
)
from verification.community_22_repository_validation.helpers import read_json

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True, slots=True)
class CatalogRepository:
    repository_id: str
    project_name: str
    github_repository: str
    github_url: str
    language_group: str | None
    ecosystem: str | None
    qualified_revision_type: str
    qualified_revision_value: str
    qualified_revision_source_tag: str | None
    requires_submodules: bool
    requires_git_lfs: bool
    enabled_for: dict[str, bool]
    raw: dict[str, Any]


class CatalogSelectionError(ValueError):
    """Raised when catalog selection violates Slice 17.13 rules."""


def _revision_is_qualified_commit(rev: Any) -> bool:
    if not isinstance(rev, dict):
        return False
    if rev.get("type") != "commit":
        return False
    value = str(rev.get("value") or "").strip().lower()
    return bool(_SHA_RE.match(value))


def load_catalog_document(monorepo: Path) -> dict[str, Any]:
    path = monorepo / CATALOG_RELATIVE
    if not path.is_file():
        raise FileNotFoundError(CATALOG_RELATIVE)
    return read_json(path)


def load_release_validation_repositories(
    monorepo: Path,
    *,
    repository_ids: tuple[str, ...] | None = None,
) -> tuple[CatalogRepository, ...]:
    """Return all release_validation-enabled catalog entries sorted by id.

    Rejects cherry-picking: if *repository_ids* is provided it must match the
    full release_validation set exactly.
    """

    data = load_catalog_document(monorepo)
    entries: list[CatalogRepository] = []
    for item in data.get("repositories") or []:
        if not isinstance(item, dict):
            continue
        enabled = item.get("enabled_for") or {}
        if not enabled.get("release_validation"):
            continue
        rev = item.get("qualified_revision")
        if not _revision_is_qualified_commit(rev):
            raise CatalogSelectionError(
                f"release_validation entry missing qualified commit pin: {item.get('id')!r}"
            )
        entries.append(
            CatalogRepository(
                repository_id=str(item["id"]),
                project_name=str(item.get("project_name") or item["id"]),
                github_repository=str(item.get("github_repository") or ""),
                github_url=str(item.get("github_url") or ""),
                language_group=item.get("language_group"),
                ecosystem=item.get("dependency_ecosystem"),
                qualified_revision_type=str(rev["type"]),
                qualified_revision_value=str(rev["value"]).lower(),
                qualified_revision_source_tag=(
                    str(rev["source_tag"]).strip()
                    if isinstance(rev.get("source_tag"), str) and rev.get("source_tag")
                    else None
                ),
                requires_submodules=bool(item.get("requires_submodules")),
                requires_git_lfs=bool(item.get("requires_git_lfs")),
                enabled_for={k: bool(v) for k, v in enabled.items()},
                raw=item,
            )
        )
    entries.sort(key=lambda e: e.repository_id)

    if len(entries) != REPOSITORY_TARGET:
        raise CatalogSelectionError(
            f"expected {REPOSITORY_TARGET} release_validation repositories, found {len(entries)}"
        )

    target = data.get("release_validation_target")
    if target != REPOSITORY_TARGET:
        raise CatalogSelectionError(
            f"catalog release_validation_target {target!r} != {REPOSITORY_TARGET}"
        )

    if repository_ids is not None:
        expected = tuple(e.repository_id for e in entries)
        if tuple(sorted(repository_ids)) != expected:
            raise CatalogSelectionError(
                "cherry-picking forbidden: repository_ids must match full release_validation set"
            )

    return tuple(entries)


def catalog_summary(repositories: tuple[CatalogRepository, ...]) -> dict[str, Any]:
    return {
        "count": len(repositories),
        "repository_ids": [r.repository_id for r in repositories],
        "sorted_by": "repository_id",
    }
