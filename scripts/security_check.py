#!/usr/bin/env python3
"""Static security checks for the codestrata-platform monorepo / engine tree.

Checks (fail on first category with findings unless --warn-only):
  - committed secret-like patterns
  - shell=True subprocess usage
  - unsafe YAML loaders
  - pickle / marshal / eval / exec of untrusted input patterns
  - archive extractall usage
  - engine imports of platform/

Does not push or publish anything.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE_SRC = ROOT / "engine" / "src"

SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    ".export-staging",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".codestrata",
    "reports",
}

SECRET_PATTERNS = [
    re.compile(r"(?i)BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY"),
    re.compile(r"(?i)aws_secret_access_key\s*=\s*['\"]?[A-Za-z0-9/+=]{20,}"),
    re.compile(r"(?i)github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?i)xox[baprs]-[A-Za-z0-9-]{10,}"),
]

# Detector fixtures intentionally contain signature strings.
SECRET_ALLOW_GLOBS = (
    "**/signatures.py",
    "**/test_*.py",
    "**/tests/**",
    "**/security_analyzer.py",
)

UNSAFE_PATTERNS = {
    "subprocess_shell": re.compile(
        r"subprocess\.(?:run|Popen|call|check_call|check_output)\([^\n]*shell\s*=\s*True"
    ),
    "yaml_unsafe": re.compile(r"yaml\.(?:load|full_load|unsafe_load)\("),
    "pickle": re.compile(r"\bpickle\.(?:loads?|Unpickler)\b"),
    "marshal": re.compile(r"\bmarshal\.loads?\b"),
    "eval_exec": re.compile(r"\b(?:eval|exec)\s*\("),
    "extractall": re.compile(r"\.(?:extractall|unpack_archive)\s*\("),
    "platform_import": re.compile(
        r"^\s*(?:from|import)\s+platform\.",
        re.MULTILINE,
    ),
}


@dataclass
class Finding:
    category: str
    path: str
    detail: str


def _iter_files(base: Path) -> list[Path]:
    files: list[Path] = []
    if not base.exists():
        return files
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.suffix.lower() not in {".py", ".toml", ".yml", ".yaml", ".md", ".env", ".txt"}:
            continue
        files.append(path)
    return sorted(files)


def _allowed_secret_path(rel: str) -> bool:
    from fnmatch import fnmatch

    return any(fnmatch(rel, pat) for pat in SECRET_ALLOW_GLOBS)


def scan(roots: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for root in roots:
        for path in _iter_files(root):
            rel = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            if path.suffix == ".py" or path.name.endswith(".py"):
                rel_posix = rel.replace("\\", "/")
                in_tests = "/tests/" in rel_posix or rel_posix.startswith("tests/")
                for category, pattern in UNSAFE_PATTERNS.items():
                    if category == "platform_import" and "engine/src" not in rel_posix:
                        continue
                    # Test fixtures intentionally mention unsafe APIs / payloads.
                    if in_tests and category in {
                        "eval_exec",
                        "yaml_unsafe",
                        "pickle",
                        "marshal",
                        "extractall",
                    }:
                        continue
                    if category == "eval_exec" and "scripts/" in rel_posix:
                        if "engine/src" not in rel_posix:
                            continue
                    if pattern.search(text):
                        findings.append(Finding(category, rel, pattern.pattern))

            if not _allowed_secret_path(rel.replace("\\", "/")):
                for pattern in SECRET_PATTERNS:
                    if pattern.search(text):
                        findings.append(Finding("secret_like", rel, pattern.pattern))
                        break
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Print findings but exit 0.",
    )
    parser.add_argument(
        "--engine-only",
        action="store_true",
        help="Scan engine/src and engine/tests only.",
    )
    args = parser.parse_args(argv)

    roots = (
        [ROOT / "engine" / "src", ROOT / "engine" / "tests"]
        if args.engine_only
        else [
            ROOT / "engine",
            ROOT / "platform" / "src",
            ROOT / "platform" / "tests",
            ROOT / "scripts",
            ROOT / "examples",
            ROOT / "tests",
        ]
    )
    findings = scan(roots)
    if not findings:
        print("security_check: OK (no findings)")
        return 0

    print(f"security_check: {len(findings)} finding(s)")
    for item in findings[:100]:
        print(f"  [{item.category}] {item.path}: {item.detail}")
    if len(findings) > 100:
        print(f"  … {len(findings) - 100} more")
    return 0 if args.warn_only else 1


if __name__ == "__main__":
    raise SystemExit(main())
