"""Prohibited path / filename detection for Infrastructure export."""

from __future__ import annotations

import fnmatch
import re
from pathlib import PurePosixPath

# Directory name segments that are always excluded (generated / local).
EXCLUDE_DIR_NAMES = frozenset(
    {
        ".git",
        ".terraform",
        ".tofu",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
        ".venv",
        "venv",
        ".eggs",
        "dist",
        "build",
        "htmlcov",
        ".idea",
        ".vscode",
        "reports",
    }
)

# Filename / path patterns that fail closed if discovered under allowlisted trees
# (tracked or accidental secrets/state). Exception: clearly synthetic *.example.
FAIL_CLOSED_PATTERNS = (
    "*.tfstate",
    "*.tfstate.*",
    "*.tfplan",
    "*.plan",
    "crash.log",
    "crash.*.log",
    "override.tf",
    "override.tf.json",
    "*_override.tf",
    "*_override.tf.json",
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "credentials",
    "credentials.json",
    "aws-credentials",
    "local.auto.tfvars",
    "*.auto.tfvars",
    "*.auto.tfvars.json",
    "terraform.tfvars",
    "tofu.tfvars",
    "secrets.tfvars",
    "*.secrets.tfvars",
    "*.vsix",
    "*.whl",
    "*.tar.gz",
    "*.egg",
    "*.egg-info",
    ".DS_Store",
    "*.swp",
    "*~",
    "*.pyc",
    ".coverage",
    "coverage.xml",
)

# Safe example exceptions for fail-closed patterns (basename match).
SAFE_EXAMPLE_NAMES = frozenset(
    {
        "backend.tf.example",
        "terraform.tfvars.example",
        ".env.example",
    }
)

# Product trees that must never appear in export sources relative to monorepo.
FORBIDDEN_MONOREPO_PREFIXES = (
    "engine/",
    "platform/",
    "vscode-plugin/",
    "cursor-plugin/",
    "docs/",
    "examples/",
    "community/",
)


def _match(name: str, pattern: str) -> bool:
    return fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(name.lower(), pattern.lower())


def path_has_excluded_dir(rel_posix: str) -> bool:
    parts = PurePosixPath(rel_posix).parts
    return any(part in EXCLUDE_DIR_NAMES for part in parts)


def is_safe_example(name: str) -> bool:
    if name in SAFE_EXAMPLE_NAMES:
        return True
    return name.endswith(".example") and not name.endswith(".tfvars")


def is_fail_closed_name(name: str) -> bool:
    if is_safe_example(name):
        return False
    # Allow .env.example explicitly
    if name == ".env.example":
        return False
    for pattern in FAIL_CLOSED_PATTERNS:
        if pattern.startswith(".env") and name.startswith(".env") and name != ".env.example":
            return True
        if _match(name, pattern):
            # *.tfvars.example is safe
            if name.endswith(".tfvars.example"):
                return False
            return True
    return False


def is_real_tfvars(name: str) -> bool:
    if name.endswith(".example"):
        return False
    if name in {"terraform.tfvars", "tofu.tfvars", "secrets.tfvars", "local.auto.tfvars"}:
        return True
    if name.endswith(".auto.tfvars") or name.endswith(".auto.tfvars.json"):
        return True
    if name.endswith(".tfvars") and not name.endswith(".tfvars.example"):
        return True
    return False


_LOCK_NAME = ".terraform.lock.hcl"


def is_provider_lock(name: str) -> bool:
    return name == _LOCK_NAME


def excluded_category_for(rel_posix: str) -> str | None:
    """Return a safe exclusion category, or None if not an expected exclusion."""

    if path_has_excluded_dir(rel_posix):
        parts = PurePosixPath(rel_posix).parts
        for part in parts:
            if part in {
                ".terraform",
                ".tofu",
            }:
                return "provider_plugin_cache"
            if part in {
                "__pycache__",
                ".pytest_cache",
                ".mypy_cache",
                ".ruff_cache",
                "node_modules",
                ".venv",
                "venv",
            }:
                return "generated_caches"
            if part == "reports":
                return "generated_reports"
            if part == ".git":
                return "git_metadata"
    name = PurePosixPath(rel_posix).name
    if name.endswith((".pyc", ".pyo")) or name == ".DS_Store":
        return "generated_caches"
    if name in {".coverage", "coverage.xml"} or name.startswith(".coverage."):
        return "generated_caches"
    return None


_ABS_PATH_HINT = re.compile(r"(?<![\w.-])(/Users/|/home/|file://)")


def content_looks_like_secret_blob(data: bytes) -> bool:
    """Heuristic for fail-closed content (not a substitute for Slice 12.7 scan)."""

    if b"-----BEGIN" in data and b"PRIVATE KEY" in data:
        text = data.decode("utf-8", errors="ignore")
        # Allow documented detection patterns / test fixtures marked EXAMPLE/TEST_ONLY.
        if "TEST_ONLY" in text or "EXAMPLE" in text.upper() or "SAFETY_PATTERNS" in text:
            return False
        return True
    text = data.decode("utf-8", errors="ignore")
    # Regex pattern definitions that mention AKIA[...] are not live keys.
    if "SAFETY_PATTERNS" in text or "aws_access_key" in text and r"AKIA[0-9A-Z]{16}" in text:
        return False
    match = re.search(r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])", text)
    if match:
        if "TEST_ONLY" in text or "EXAMPLE" in text.upper() or "pattern" in text.lower():
            return False
        return True
    return False
