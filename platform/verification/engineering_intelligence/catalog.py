"""Resolve SV.6 repositories exclusively from the permanent catalog."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from verification.engineering_intelligence.contract import (
    CATALOG_RELATIVE_PATH,
    PREFERRED_FIVE_LANGUAGE_SUBSET,
    SUBSET_LANGUAGE_GROUPS,
)

_FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
_FLOATING = frozenset(
    {"main", "master", "head", "default", "latest", "origin/main", "origin/master"}
)


@dataclass(frozen=True, slots=True)
class QualifiedRevision:
    revision_type: str
    value: str
    source_tag: str | None = None


@dataclass(frozen=True, slots=True)
class CatalogRepository:
    repository_id: str
    project_name: str
    github_repository: str
    github_url: str
    language_group: str
    candidate_category: str
    license: str
    qualified_revision: QualifiedRevision
    enabled_for_engineering_intelligence: bool


@dataclass(frozen=True, slots=True)
class PermanentCatalog:
    catalog_id: str
    schema_name: str
    schema_version: str
    relative_path: str
    repositories: tuple[CatalogRepository, ...]


def monorepo_root_from_here() -> Path:
    # platform/verification/engineering_intelligence/catalog.py → monorepo
    return Path(__file__).resolve().parents[3]


def resolve_catalog_path(repo_root: Path | None = None) -> Path:
    root = (repo_root or monorepo_root_from_here()).resolve()
    candidates = [
        root / CATALOG_RELATIVE_PATH,
        root / "validation" / "repository-catalog" / "catalog.json",
        root.parent / CATALOG_RELATIVE_PATH,
    ]
    for path in candidates:
        if path.is_file():
            return path.resolve()
    raise FileNotFoundError(f"permanent catalog not found; expected {CATALOG_RELATIVE_PATH}")


def _parse_revision(raw: Any) -> QualifiedRevision | None:
    if not isinstance(raw, dict):
        return None
    rtype = str(raw.get("type") or "").strip().lower()
    value = str(raw.get("value") or "").strip()
    source_tag = raw.get("source_tag")
    source = str(source_tag).strip() if isinstance(source_tag, str) and source_tag.strip() else None
    if rtype != "commit" or not value:
        return None
    if value.lower() in _FLOATING:
        return None
    if not _FULL_SHA.match(value.lower()):
        return None
    return QualifiedRevision("commit", value.lower(), source)


def load_permanent_catalog(repo_root: Path | None = None) -> PermanentCatalog:
    path = resolve_catalog_path(repo_root)
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_name") != "codestrata-repository-catalog":
        raise ValueError(f"unexpected catalog schema_name: {data.get('schema_name')!r}")
    repos: list[CatalogRepository] = []
    for item in data.get("repositories") or []:
        if not isinstance(item, dict):
            continue
        rev = _parse_revision(item.get("qualified_revision"))
        if rev is None:
            continue
        enabled = item.get("enabled_for") or {}
        repos.append(
            CatalogRepository(
                repository_id=str(item.get("id") or ""),
                project_name=str(item.get("project_name") or ""),
                github_repository=str(item.get("github_repository") or ""),
                github_url=str(item.get("github_url") or ""),
                language_group=str(item.get("language_group") or ""),
                candidate_category=str(item.get("candidate_category") or ""),
                license=str(item.get("license") or ""),
                qualified_revision=rev,
                enabled_for_engineering_intelligence=bool(
                    enabled.get("engineering_intelligence", True)
                ),
            )
        )
    return PermanentCatalog(
        catalog_id=str(data.get("catalog_id") or ""),
        schema_name=str(data.get("schema_name") or ""),
        schema_version=str(data.get("schema_version") or ""),
        relative_path=CATALOG_RELATIVE_PATH,
        repositories=tuple(repos),
    )


def qualified_by_id(catalog: PermanentCatalog) -> dict[str, CatalogRepository]:
    return {item.repository_id: item for item in catalog.repositories}


def resolve_subset(
    catalog: PermanentCatalog,
    *,
    repository_ids: tuple[str, ...] | None = None,
) -> tuple[CatalogRepository, ...]:
    """Resolve requested catalog IDs; default to preferred five-language subset."""

    wanted = repository_ids or PREFERRED_FIVE_LANGUAGE_SUBSET
    by_id = qualified_by_id(catalog)
    resolved: list[CatalogRepository] = []
    missing: list[str] = []
    for rid in wanted:
        entry = by_id.get(rid)
        if entry is None:
            missing.append(rid)
            continue
        if not entry.enabled_for_engineering_intelligence:
            missing.append(f"{rid}:disabled")
            continue
        resolved.append(entry)
    if missing:
        raise ValueError(
            "subset requires fully qualified pinned catalog commits; missing/unqualified: "
            + ", ".join(missing)
        )
    # Stable order follows requested IDs (deterministic).
    return tuple(resolved)


def assert_five_language_coverage(entries: tuple[CatalogRepository, ...]) -> None:
    groups = {item.language_group for item in entries}
    expected = set(SUBSET_LANGUAGE_GROUPS.values())
    if not expected.issubset(groups) and len(entries) >= 5:
        # Prefer exact preferred mapping when using default subset.
        mapped = {SUBSET_LANGUAGE_GROUPS.get(e.repository_id) for e in entries}
        if expected - mapped:
            raise ValueError(
                f"five-language coverage incomplete: have={sorted(groups)} "
                f"expected={sorted(expected)}"
            )
