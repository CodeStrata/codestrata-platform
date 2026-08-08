"""Destination ownership — target manifests must not authorize cross-target use."""

from __future__ import annotations

import json
from pathlib import Path

from repository_export_router.errors import TargetConfigurationInvalid
from repository_export_router.targets import ExportTarget


def detect_destination_owner(destination: Path) -> ExportTarget | None:
    """Return owning target if a known managed marker is present, else None."""

    if not destination.exists() or not destination.is_dir():
        return None

    # Infrastructure: single-repo export-manifest.json
    infra_manifest = destination / "export-manifest.json"
    if infra_manifest.is_file():
        try:
            data = json.loads(infra_manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = None
        if isinstance(data, dict):
            if data.get("schema_name") == "infrastructure-repository-export-manifest":
                return ExportTarget.INFRASTRUCTURE
            if data.get("schema_name") == "insights-repository-export-manifest":
                return ExportTarget.INSIGHTS

    # Community: staging root contains per-repo .codestrata-export-snapshot.json
    # or nested export dirs with snapshots
    snapshot = destination / ".codestrata-export-snapshot.json"
    if snapshot.is_file():
        return ExportTarget.COMMUNITY
    if destination.is_dir():
        for child in destination.iterdir():
            if child.is_dir() and (child / ".codestrata-export-snapshot.json").is_file():
                return ExportTarget.COMMUNITY
            # Community staging often has named repo dirs; prefer snapshot marker
    return None


def assert_destination_compatible(*, target: ExportTarget, destination: Path) -> None:
    owner = detect_destination_owner(destination)
    if owner is None:
        return
    if owner != target:
        raise TargetConfigurationInvalid(
            "destination_ownership_mismatch",
            category="target_configuration_invalid",
        )
