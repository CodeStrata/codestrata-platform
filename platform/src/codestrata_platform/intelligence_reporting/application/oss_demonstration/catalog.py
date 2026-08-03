"""Load the curated public OSS demonstration catalog (no network)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from codestrata_platform.domain.errors import InvalidValueError


@dataclass(frozen=True, slots=True)
class OssDemonstrationRepository:
    repository_id: str
    assessment_id: str
    assessment_run_id: str
    display_name: str
    source_reference: str
    pinned_revision: str
    report_path: str
    language: str


@dataclass(frozen=True, slots=True)
class OssDemonstrationCatalog:
    catalog_id: str
    catalog_version: str
    title: str
    report_scope: str
    selection_policy: str
    disclaimer: str
    repositories: tuple[OssDemonstrationRepository, ...]
    catalog_path: Path

    @property
    def root_directory(self) -> Path:
        return self.catalog_path.parent


def load_oss_demonstration_catalog(catalog_path: str | Path) -> OssDemonstrationCatalog:
    path = Path(catalog_path).resolve()
    if not path.is_file():
        raise InvalidValueError(
            f"OSS demonstration catalog not found: {path}",
            reason_code="oss_demo_catalog_missing",
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise InvalidValueError(
            "OSS demonstration catalog must be a JSON object",
            reason_code="oss_demo_catalog_invalid",
        )
    repos_raw = payload.get("repositories")
    if not isinstance(repos_raw, list) or not repos_raw:
        raise InvalidValueError(
            "OSS demonstration catalog requires repositories",
            reason_code="oss_demo_catalog_empty",
        )
    repositories: list[OssDemonstrationRepository] = []
    for item in repos_raw:
        if not isinstance(item, dict):
            raise InvalidValueError(
                "catalog repository entries must be objects",
                reason_code="oss_demo_catalog_invalid_entry",
            )
        repositories.append(
            OssDemonstrationRepository(
                repository_id=str(item["repository_id"]).strip(),
                assessment_id=str(item["assessment_id"]).strip(),
                assessment_run_id=str(item["assessment_run_id"]).strip(),
                display_name=str(item["display_name"]).strip(),
                source_reference=str(item["source_reference"]).strip(),
                pinned_revision=str(item["pinned_revision"]).strip(),
                report_path=str(item["report_path"]).strip(),
                language=str(item.get("language") or "").strip(),
            )
        )
    # Deterministic catalog order by repository_id.
    repositories.sort(key=lambda item: item.repository_id)
    return OssDemonstrationCatalog(
        catalog_id=str(payload.get("catalog_id") or "public-oss-demonstration").strip(),
        catalog_version=str(payload.get("catalog_version") or "1.0").strip(),
        title=str(
            payload.get("title") or "Public OSS Engineering Intelligence Demonstration"
        ).strip(),
        report_scope=str(payload.get("report_scope") or "public_oss_dataset").strip(),
        selection_policy=str(
            payload.get("selection_policy") or "explicit_validated_public_oss"
        ).strip(),
        disclaimer=str(payload.get("disclaimer") or "").strip(),
        repositories=tuple(repositories),
        catalog_path=path,
    )
