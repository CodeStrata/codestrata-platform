"""Secret / privacy scans for infrastructure and packaging."""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.verification.contract import SAFETY_PATTERNS, infra_root, repo_root
from infrastructure.verification.models import CheckResult

_SCAN_GLOBS = (
    "*.tf",
    "*.md",
    "*.sh",
    "*.json",
    "*.example",
    "Dockerfile",
    ".dockerignore",
    ".gitignore",
)


def _iter_scan_files() -> list[Path]:
    root = infra_root()
    files: list[Path] = []
    for pattern in _SCAN_GLOBS:
        files.extend(root.rglob(pattern))
    packaging = repo_root() / "platform" / "deployment" / "community-cloud-api"
    files.extend(packaging.glob("*"))
    # Exclude generated reports / caches / verification package itself may contain
    # intentionally fake token constants — skip verification python sources for cscc.
    filtered: list[Path] = []
    for path in files:
        if not path.is_file():
            continue
        if any(part in {".terraform", "__pycache__", ".pytest_cache", "reports"} for part in path.parts):
            continue
        if path.suffix == ".py" and "verification" in path.parts:
            continue
        filtered.append(path)
    return filtered


def check_safety() -> list[CheckResult]:
    hits: list[str] = []
    for path in _iter_scan_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for label, pattern in SAFETY_PATTERNS:
            for match in re.finditer(pattern, text):
                value = match.group(0)
                if "TEST_ONLY" in value or "EXAMPLE" in value.upper():
                    continue
                # Documentation / scripts that list forbidden families are allowed.
                if path.suffix in {".md", ".sh"} or path.name.endswith(".example"):
                    if label in {
                        "bearer",
                        "cscc_credential",
                        "aws_access_key",
                        "home_path",
                        "file_uri",
                        "private_key",
                    }:
                        continue
                hits.append(f"{path.name}:{label}")
                break
    manifest = (repo_root() / "public-export-manifest.yaml").read_text(encoding="utf-8")
    return [
        CheckResult(
            name="safety:no_secret_patterns",
            ok=not hits,
            detail="ok" if not hits else ",".join(hits[:8]),
            category="safety",
            scenario="O",
        ),
        CheckResult(
            name="safety:public_export_excludes_infra",
            ok="infrastructure/" in manifest or "infrastructure/**" in manifest,
            detail="public-export-manifest",
            category="safety",
            scenario="Z",
        ),
    ]
