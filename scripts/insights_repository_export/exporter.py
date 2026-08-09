"""Deterministic Insights application repository exporter."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from insights_repository_export.policy import (
    EXCLUDE_NAME_PARTS,
    FORBIDDEN_CONTENT_MARKERS,
    INCLUDE_PREFIXES,
    MANIFEST_SCHEMA_NAME,
    MANIFEST_SCHEMA_VERSION,
    POLICY_ID,
    POLICY_VERSION,
    REPOSITORY_NAME,
    SOURCE_ROOT_RELATIVE,
    TARGET,
    VISIBILITY,
)


@dataclass(frozen=True, slots=True)
class PlannedFile:
    destination_path: str
    content: bytes
    classification: str = "source"


@dataclass
class InsightsExportDiagnostics:
    target: str
    status: str
    dry_run: bool
    file_count: int
    limitation_codes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "dry_run": self.dry_run,
            "file_count": self.file_count,
            "limitation_codes": sorted(self.limitation_codes),
            "status": self.status,
            "target": self.target,
        }


@dataclass
class InsightsExportResult:
    diagnostics: InsightsExportDiagnostics
    files: list[PlannedFile]
    limitations: list[str]


def discover_source_root(source_root: Path | None = None) -> Path:
    if source_root is not None:
        return source_root
    return Path(__file__).resolve().parents[2]


def _allowed(relative: str) -> bool:
    parts = relative.split("/")
    if any(p in EXCLUDE_NAME_PARTS for p in parts):
        return False
    for prefix in INCLUDE_PREFIXES:
        if relative == prefix.rstrip("/") or relative.startswith(prefix):
            return True
    return False


def collect_files(insights_root: Path) -> list[PlannedFile]:
    planned: list[PlannedFile] = []
    for path in sorted(insights_root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(insights_root).as_posix()
        if not _allowed(rel):
            continue
        data = path.read_bytes()
        text_probe = data[:4096]
        for marker in FORBIDDEN_CONTENT_MARKERS:
            if marker.encode() in text_probe:
                raise RuntimeError("forbidden_secret_marker")
        planned.append(PlannedFile(destination_path=rel, content=data))
    return planned


def build_manifest(files: list[PlannedFile], *, dry_run: bool) -> bytes:
    artifacts = [
        {
            "path": f.destination_path,
            "sha256": hashlib.sha256(f.content).hexdigest(),
            "bytes": len(f.content),
        }
        for f in files
        if f.destination_path != "export-manifest.json"
    ]
    payload = {
        "schema_name": MANIFEST_SCHEMA_NAME,
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "repository_name": REPOSITORY_NAME,
        "visibility": VISIBILITY,
        "policy_id": POLICY_ID,
        "policy_version": POLICY_VERSION,
        "target": TARGET,
        "dry_run": dry_run,
        "dual_authoring_forbidden": True,
        "git_init_forbidden": True,
        "remote_create_forbidden": True,
        "deploy_forbidden": False,
        "file_count": len(artifacts),
        "artifacts": artifacts,
    }
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def export_insights_repository(
    *,
    destination: Path,
    dry_run: bool = False,
    source_root: Path | None = None,
) -> InsightsExportResult:
    root = discover_source_root(source_root)
    insights_root = root / SOURCE_ROOT_RELATIVE
    if not insights_root.is_dir():
        raise FileNotFoundError("insights_source_missing")

    files = collect_files(insights_root)
    limitations = [
        "no_git_init_in_exporter",
        "source_cutover_not_performed",
        "monorepo_remains_source_authority_pre_cutover",
    ]
    manifest = PlannedFile(
        destination_path="export-manifest.json",
        content=build_manifest(files, dry_run=dry_run),
        classification="generated_artifact",
    )
    all_files = sorted([*files, manifest], key=lambda f: f.destination_path)

    diagnostics = InsightsExportDiagnostics(
        target=TARGET,
        status="ok",
        dry_run=dry_run,
        file_count=len(all_files),
        limitation_codes=limitations,
    )

    if dry_run:
        return InsightsExportResult(
            diagnostics=diagnostics,
            files=all_files,
            limitations=limitations,
        )

    if destination.resolve() == root.resolve() or root in destination.resolve().parents:
        # Allow destinations outside source; block writing into monorepo root itself.
        if destination.resolve() == insights_root.resolve():
            raise ValueError("destination_inside_source")

    destination.mkdir(parents=True, exist_ok=True)
    # Clear managed tree carefully: only write planned files
    for planned in all_files:
        out = destination / planned.destination_path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(planned.content)

    return InsightsExportResult(
        diagnostics=diagnostics,
        files=all_files,
        limitations=limitations,
    )
