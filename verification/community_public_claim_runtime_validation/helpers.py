"""Helpers for Slice 18.7."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from verification.community_public_claim_runtime_validation.models import (
    CheckResult,
    Defect,
)

FORBIDDEN_REPORT_PATTERNS = (
    re.compile(r"/Users/[A-Za-z0-9._-]+"),
    re.compile(r"/home/[A-Za-z0-9._-]+"),
    re.compile(r"(?<![A-Za-z0-9])AKIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"-----BEGIN (RSA |EC )?PRIVATE KEY-----"),
    re.compile(r"\b\d{12}\b"),
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(read_text(path))
    if not isinstance(payload, dict):
        raise TypeError(f"expected object JSON: {path}")
    return payload


def sanitize_detail(detail: str | object) -> str:
    safe = detail if isinstance(detail, str) else str(detail)
    safe = re.sub(r"(/Users/|/home/)[^\s\"']+", "[path-redacted]", safe)
    safe = re.sub(r"\b\d{12}\b", "[account-redacted]", safe)
    return safe


def check(check_id: str, ok: bool, detail: str, category: str) -> CheckResult:
    return CheckResult(
        check_id=check_id, ok=bool(ok), detail=sanitize_detail(detail), category=category
    )


def hard_defect(classification: str, check_id: str, expected: str, detail: str) -> Defect:
    return Defect(
        classification=classification,
        check_id=check_id,
        expected=expected,
        detail=sanitize_detail(detail),
    )


def add_check(
    checks: list[CheckResult],
    defects: list[Defect],
    check_id: str,
    ok: bool,
    detail: str,
    category: str,
    *,
    soft: bool = False,
) -> None:
    checks.append(check(check_id, ok, detail, category))
    if not ok and not soft:
        defects.append(hard_defect("DEFECT", check_id, "pass", detail))


def report_text_is_safe(text: str) -> bool:
    return not any(p.search(text) for p in FORBIDDEN_REPORT_PATTERNS)


def dict_to_canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
