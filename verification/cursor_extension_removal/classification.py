"""Removal classification for Slice 12.1."""

from __future__ import annotations

from typing import Any

from verification.cursor_extension_removal.inventory import TRACKED_CURSOR_RELATIVE_PATHS


def build_classification() -> dict[str, list[str]]:
    return {
        "remove_now": sorted(TRACKED_CURSOR_RELATIVE_PATHS)
        + [
            "cursor-plugin/ (entire directory including generated out/, node_modules/, VSIX)",
        ],
        "preserve_shared": [
            "vscode-plugin/",
            "vscode-plugin/src/telemetry/",
            "vscode-plugin/src/telemetry/analytics/",
            "vscode-plugin/package.json",
        ],
        "preserve_historical": [
            "reports/verification/ (historical Cursor inventory mentions)",
            "Engine/Platform historical cursor_extension client vocabulary",
            "platform extension-event / AI-usage allowlists retaining cursor_extension",
        ],
        "defer_build_release_cleanup": [
            "(completed in Slice 12.2) public-export-manifest.yaml codestrata-cursor export",
            "(completed in Slice 12.2) scripts/release Cursor inventory and version checks",
            "(completed in Slice 12.2) verification/release_artifacts Cursor packaging module",
            "(completed in Slice 12.2) Marketplace publication Cursor packaging steps",
        ],
        "defer_documentation_cleanup": [
            "README.md Cursor product rows",
            "ARCHITECTURE.md cursor-plugin tree entry",
            "docs/extensions/cursor.md",
            "platform/docs/product-experience/EXTENSION_READINESS.md",
            "governance docs referencing codestrata-cursor (non-release narrative)",
        ],
        "defer_contract_retirement": [
            "historical cursor_extension telemetry client id",
            "historical cursor_extension analytics client id",
            "Platform extension-event client allowlist cursor_extension",
            "Platform AI-usage client allowlist cursor_extension",
            "Data Lake historical partition compatibility for cursor_extension",
        ],
    }


def classification_summary() -> dict[str, Any]:
    data = build_classification()
    return {key: len(values) for key, values in sorted(data.items())}
