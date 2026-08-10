"""Helpers for Slice 17.16 verification."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from verification.community_report_publishing.models import CheckResult, Defect


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def exists(path: Path) -> bool:
    return path.is_file() or path.is_dir()


def sanitize_detail(detail: str) -> str:
    safe = detail
    if "/Users/" in safe or "/home/" in safe:
        safe = re.sub(r"(/Users/|/home/)[^\s\"']+", "[path-redacted]", safe)
    if "arn:aws:" in safe:
        safe = re.sub(r"arn:aws:[^\s\"']+", "[arn-redacted]", safe)
    safe = re.sub(r"\b\d{12}\b", "[account-redacted]", safe)
    safe = re.sub(
        r"[a-z0-9]{10}\.execute-api\.[a-z0-9-]+\.amazonaws\.com",
        "[execute-api-redacted]",
        safe,
        flags=re.I,
    )
    safe = re.sub(
        r"[a-z0-9.-]+\.s3\.[a-z0-9-]+\.amazonaws\.com",
        "[s3-host-redacted]",
        safe,
        flags=re.I,
    )
    if "s3://" in safe.lower():
        safe = re.sub(r"s3://[^\s\"']+", "s3://[bucket-redacted]", safe, flags=re.I)
    return safe


def add_check(
    checks: list[CheckResult],
    defects: list[Defect],
    check_id: str,
    ok: bool,
    detail: str,
    category: str,
    *,
    classification: str = "DEFECT",
    soft: bool = False,
) -> None:
    safe_detail = sanitize_detail(detail)
    checks.append(CheckResult(check_id=check_id, ok=bool(ok), detail=safe_detail, category=category))
    if not ok and not soft:
        defects.append(
            Defect(
                classification=classification,
                check_id=check_id,
                expected="pass",
                detail=safe_detail,
            )
        )
