"""Release provenance record (no personal paths or secrets)."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import RELEASE_TOOLING_VERSION
from .checksums import sha256_file

ROOT = Path(__file__).resolve().parents[2]


def _git(cmd: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            ["git", *cmd],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def build_provenance(
    *,
    artifact_dir: Path,
    artifact_files: list[Path],
    export_manifest_version: object,
    test_results: dict[str, Any],
    versions: dict[str, Any],
) -> dict[str, Any]:
    artifacts = []
    for path in artifact_files:
        if not path.is_file():
            continue
        artifacts.append(
            {
                "name": path.name,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    node_version = None
    try:
        completed = subprocess.run(
            ["node", "--version"],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode == 0:
            node_version = completed.stdout.strip()
    except OSError:
        node_version = None

    return {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace(
            "+00:00", "Z"
        ),
        "codestrata_version": (versions.get("versions") or {}).get("engine_pyproject"),
        "source_commit": _git(["rev-parse", "HEAD"]),
        "source_branch": _git(["rev-parse", "--abbrev-ref", "HEAD"]),
        "working_tree_clean": _git(["status", "--porcelain"]) == "",
        "build_environment": {
            "python_version": sys.version.split()[0],
            "node_version": node_version,
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "cpu_count": os.cpu_count(),
        },
        "build_commands": [
            "python scripts/export-public-repos.py",
            "python scripts/validate-public-exports.py --skip-install",
            "python scripts/validate_release.py",
        ],
        "export_manifest_version": export_manifest_version,
        "extraction_script_version": RELEASE_TOOLING_VERSION,
        "artifacts": artifacts,
        "sbom_references": [
            item["name"] for item in artifacts if item["name"].startswith("sbom-")
        ],
        "test_results": test_results,
        "versions": versions.get("versions") or {},
        "signing": {
            "status": "not_configured",
            "notes": "Release workflow prepared for future signing; no credentials used.",
        },
    }


def write_provenance(payload: dict[str, Any], destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination
