"""Release surface inventory — classify distributable vs internal assets."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parents[2]

# Authoritative classifications for top-level monorepo surfaces.
SURFACE_CLASSIFICATIONS: dict[str, dict[str, str]] = {
    "engine/": {
        "classification": "public_release",
        "notes": "Community Engine package and CLI source",
    },
    "docs/": {
        "classification": "public_release",
        "notes": "Public documentation site (codestrata-docs)",
    },
    "examples/": {
        "classification": "public_release",
        "notes": "Public showcase manifests and expected results",
    },
    "cursor-plugin/": {
        "classification": "public_release",
        "notes": "Cursor extension Community client",
    },
    "vscode-plugin/": {
        "classification": "public_release",
        "notes": "VS Code extension Community client",
    },
    "platform/": {
        "classification": "commercial_platform_only",
        "notes": "Must never enter Community export",
    },
    "governance/": {
        "classification": "internal_only",
        "notes": "Engineering governance; not a public product tree",
    },
    "knowledge/": {
        "classification": "internal_only",
        "notes": "Engineering knowledge corpus; not Community source",
    },
    "test-fixtures/": {
        "classification": "test_only",
        "notes": "Sample apps; sample-js may be exported via extra_includes",
    },
    ".codestrata-test-knowledge/": {
        "classification": "test_only",
        "notes": "Synthetic secrets for tests; never publish",
    },
    ".codestrata-examples/": {
        "classification": "development_only",
        "notes": "Local dogfood clones; never publish",
    },
    ".export-staging/": {
        "classification": "generated",
        "notes": "Export staging only",
    },
    "reports/": {
        "classification": "generated",
        "notes": "Local assessment outputs; never publish",
    },
    "scripts/": {
        "classification": "development_only",
        "notes": "Monorepo maintainer scripts; not shipped in Engine wheel",
    },
    "public-export-manifest.yaml": {
        "classification": "development_only",
        "notes": "Authoritative Community release manifest (monorepo)",
    },
    ".env": {
        "classification": "secret_sensitive",
        "notes": "Forbidden in release",
    },
    ".env.example": {
        "classification": "public_release",
        "notes": "Placeholder names only; no secrets",
    },
}


def load_export_manifest(root: Path = ROOT) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required")
    path = root / "public-export-manifest.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("invalid public-export-manifest.yaml")
    return data


def build_surface_inventory(root: Path = ROOT) -> dict[str, Any]:
    manifest = load_export_manifest(root)
    exports = []
    for item in manifest.get("exports") or []:
        exports.append(
            {
                "name": item.get("name"),
                "source_root": item.get("source_root"),
                "public_repository": item.get("public_repository"),
                "classification": "public_release",
                "include": list(item.get("include") or []),
                "exclude": list(item.get("exclude") or []),
                "required_files": list(
                    (item.get("validation") or {}).get("require_files") or []
                ),
                "forbid_globs": list(
                    (item.get("validation") or {}).get("forbid_globs") or []
                ),
            }
        )
    defaults = manifest.get("defaults") or {}
    return {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace(
            "+00:00", "Z"
        ),
        "manifest_version": manifest.get("version"),
        "staging_directory": manifest.get("staging_directory"),
        "source_of_truth": manifest.get("source_of_truth"),
        "surfaces": SURFACE_CLASSIFICATIONS,
        "exports": exports,
        "default_exclude_globs": list(defaults.get("exclude_globs") or []),
        "forbid_path_substrings": list(defaults.get("forbid_path_substrings") or []),
        "documentation_boundary": defaults.get("documentation_boundary") or {},
        "classifications_legend": [
            "public_release",
            "internal_only",
            "generated",
            "test_only",
            "development_only",
            "secret_sensitive",
            "customer_specific",
            "commercial_platform_only",
        ],
    }


def write_surface_inventory(destination: Path, root: Path = ROOT) -> Path:
    payload = build_surface_inventory(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination
