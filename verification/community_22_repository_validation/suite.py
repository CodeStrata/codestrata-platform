"""Suite manifest builder for Slice 17.13."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verification.community_22_repository_validation.catalog import CatalogRepository
from verification.community_22_repository_validation.contract import (
    MANIFEST_JSON,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SUITE_ID,
    SV1713_OUTPUT_RELATIVE,
)


def build_suite_manifest(
    *,
    repositories: tuple[CatalogRepository, ...],
    suite_execution_status: str,
    skip_execute: bool,
) -> dict[str, Any]:
    return {
        "schema": f"{SCHEMA_NAME}-manifest:1.0.0",
        "schema_version": SCHEMA_VERSION,
        "suite_id": SUITE_ID,
        "slice": "17.13",
        "repository_target": len(repositories),
        "suite_execution_status": suite_execution_status,
        "skip_execute": skip_execute,
        "repositories": [
            {
                "repository_validation_id": repo.repository_id,
                "github_repository": repo.github_repository,
                "language": repo.language_group,
                "ecosystem": repo.ecosystem,
                "qualified_revision": repo.qualified_revision_value,
            }
            for repo in repositories
        ],
    }


def write_suite_manifest(monorepo: Path, manifest: dict[str, Any]) -> Path:
    out_dir = monorepo / SV1713_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / MANIFEST_JSON
    text = json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")
    return path
