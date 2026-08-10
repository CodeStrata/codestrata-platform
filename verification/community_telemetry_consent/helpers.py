"""Shared helpers for Slice 17.17 verification."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from verification.community_telemetry_consent.models import CheckResult, Defect

FORBIDDEN_REPORT_PATTERNS = (
    re.compile(r"/Users/[A-Za-z0-9._-]+"),
    re.compile(r"cscc_v1_[A-Za-z0-9]+"),
    re.compile(r"arn:aws:[a-z0-9-]+:"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIDAU[A-Z0-9]+"),
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
