"""Helpers for Slice 17.21."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from verification.community_vscode_clean_install.models import CheckResult, Defect

FORBIDDEN_REPORT_PATTERNS = (
    re.compile(r"cscc_v1_"),
    re.compile(r"(?<![A-Za-z0-9])sk-(?:proj-|or-v1-)?[A-Za-z0-9]{16,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]{8,}"),
    re.compile(r"(?<![A-Za-z0-9])AKIA[0-9A-Z]{16}"),
    re.compile(r"(?<![A-Za-z0-9])ASIA[0-9A-Z]{16}"),
    re.compile(r"OPENAI_API_KEY\s*[:=]\s*\S+"),
    re.compile(r"OPENROUTER_API_KEY\s*[:=]\s*\S+"),
    re.compile(r"aws_secret_access_key\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"/Users/[A-Za-z0-9._-]+"),
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(read_text(path))
    if not isinstance(payload, dict):
        raise TypeError(f"expected object JSON: {path}")
    return payload


def contains(path: Path, needle: str) -> bool:
    return needle in read_text(path)


def check(check_id: str, ok: bool, detail: str, category: str) -> CheckResult:
    return CheckResult(check_id=check_id, ok=bool(ok), detail=detail, category=category)


def hard_defect(classification: str, check_id: str, expected: str, detail: str) -> Defect:
    return Defect(
        classification=classification,
        check_id=check_id,
        expected=expected,
        detail=detail,
    )


def report_text_is_safe(text: str) -> bool:
    return not any(p.search(text) for p in FORBIDDEN_REPORT_PATTERNS)


def find_vsix(plugin_dir: Path) -> Path | None:
    matches = sorted(plugin_dir.glob("codestrata-vscode-*.vsix"))
    return matches[-1] if matches else None
