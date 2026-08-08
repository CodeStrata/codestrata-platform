"""Insights repository export policy (Slice 15.8)."""

from __future__ import annotations

REPOSITORY_NAME = "codestrata-insights"
POLICY_ID = "codestrata-insights-application-policy"
POLICY_VERSION = "1.0"
MANIFEST_SCHEMA_NAME = "insights-repository-export-manifest"
MANIFEST_SCHEMA_VERSION = "1.0.0"
TARGET = "insights"
VISIBILITY = "private"

SOURCE_ROOT_RELATIVE = "insights"

# Paths relative to insights/ to include (prefix match after root).
INCLUDE_PREFIXES: tuple[str, ...] = (
    "package.json",
    "package-lock.json",
    "tsconfig.json",
    "tsconfig.node.json",
    "vite.config.ts",
    "vitest.config.ts",
    "index.html",
    "README.md",
    "LICENSE",
    "SECURITY.md",
    ".gitignore",
    "src/",
    "public/",
    "tests/",
    "docs/",
    "policies/",
)

EXCLUDE_NAME_PARTS: frozenset[str] = frozenset(
    {
        "node_modules",
        "dist",
        ".git",
        ".DS_Store",
        "__pycache__",
        ".vite",
        "coverage",
    }
)

FORBIDDEN_CONTENT_MARKERS: frozenset[str] = frozenset(
    {
        "AWS_SECRET",
        "SECRET_KEY",
        "sk-live",
    }
)
