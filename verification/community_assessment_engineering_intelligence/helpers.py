"""Shared helpers for Slice 17.19 verification."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from verification.community_assessment_engineering_intelligence.models import (
    CheckResult,
    Defect,
)

FORBIDDEN_REPORT_PATTERNS = (
    re.compile(r"cscc_v1_"),
    re.compile(r"Bearer "),
    re.compile(r"arn:aws:"),
    re.compile(r"AKIA"),
    re.compile(r"execute-api\."),
    re.compile(r"raw/stream="),
    re.compile(r"SecretString"),
    re.compile(r"dashboard[-_ ]?password", re.IGNORECASE),
    re.compile(r"/Users/[A-Za-z0-9._-]+"),
)

FORBIDDEN_ARTIFACT_PATTERNS = FORBIDDEN_REPORT_PATTERNS + (
    # Credential assignment not followed by redaction marker.
    re.compile(r"password\s*[:=]\s*(?!\[REDACTED\])(?!\*+)(?!redacted)\S+", re.IGNORECASE),
    re.compile(r"api[_-]?key\s*[:=]\s*(?!\[REDACTED\])(?!\*+)(?!redacted)\S+", re.IGNORECASE),
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(read_text(path))
    if not isinstance(payload, dict):
        raise TypeError(f"expected object JSON: {path}")
    return payload


def load_json_any(path: Path) -> Any:
    return json.loads(read_text(path))


def contains(path: Path, needle: str) -> bool:
    return needle in read_text(path)


def check(
    check_id: str,
    ok: bool,
    detail: str,
    category: str,
) -> CheckResult:
    return CheckResult(check_id=check_id, ok=bool(ok), detail=detail, category=category)


def hard_defect(
    classification: str,
    check_id: str,
    expected: str,
    detail: str,
) -> Defect:
    return Defect(
        classification=classification,
        check_id=check_id,
        expected=expected,
        detail=detail,
    )


def report_text_is_safe(text: str) -> bool:
    return not any(p.search(text) for p in FORBIDDEN_REPORT_PATTERNS)


def artifact_text_is_safe(text: str) -> bool:
    return not any(p.search(text) for p in FORBIDDEN_ARTIFACT_PATTERNS)


def github_artifact_folder(github_repository: str) -> str:
    """Map catalog ``owner/repo`` → ``github-<owner>-<repo>`` (dots preserved)."""

    owner, _, repo = github_repository.partition("/")
    owner_s = owner.strip().lower()
    repo_s = repo.strip().lower()
    return f"github-{owner_s}-{repo_s}"
