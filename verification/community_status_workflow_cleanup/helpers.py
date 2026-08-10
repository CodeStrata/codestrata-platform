"""Helpers for Slice 17.25 verification."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from verification.community_status_workflow_cleanup.models import CheckResult, Defect

FORBIDDEN_REPORT_PATTERNS = (
    re.compile(r"/Users/[A-Za-z0-9._-]+"),
    re.compile(r"/home/[A-Za-z0-9._-]+"),
    re.compile(r"(?<![A-Za-z0-9])AKIA[0-9A-Z]{16}"),
    re.compile(r"(?<![A-Za-z0-9])ASIA[0-9A-Z]{16}"),
    re.compile(r"aws_secret_access_key\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"-----BEGIN (RSA |EC )?PRIVATE KEY-----"),
    re.compile(r"arn:aws:[^\s\"']+"),
)

AWS_OR_SECRET_IN_BODY = (
    re.compile(r"(?<![A-Za-z0-9])AKIA[0-9A-Z]{16}"),
    re.compile(r"(?<![A-Za-z0-9])ASIA[0-9A-Z]{16}"),
    re.compile(r"arn:aws:", re.IGNORECASE),
    re.compile(r"execute-api\.[a-z0-9-]+\.amazonaws\.com", re.IGNORECASE),
    re.compile(r"s3://", re.IGNORECASE),
    re.compile(r"aws_secret_access_key", re.IGNORECASE),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_", re.IGNORECASE),
)

WORKFLOW_SECRET_PATTERNS = (
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AWS_SECRET_ACCESS_KEY\s*:\s*['\"][^'\"]{8,}['\"]", re.IGNORECASE),
    re.compile(r"AWS_ACCESS_KEY_ID\s*:\s*['\"]?(AKIA|ASIA)[0-9A-Z]{12,}['\"]?", re.IGNORECASE),
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(read_text(path))
    if not isinstance(payload, dict):
        raise TypeError(f"expected object JSON: {path}")
    return payload


def contains(path: Path, needle: str) -> bool:
    return needle in read_text(path)


def sanitize_detail(detail: str) -> str:
    safe = detail
    if "/Users/" in safe or "/home/" in safe:
        safe = re.sub(r"(/Users/|/home/)[^\s\"']+", "[path-redacted]", safe)
    if "arn:aws:" in safe:
        safe = re.sub(r"arn:aws:[^\s\"']+", "[arn-redacted]", safe)
    safe = re.sub(r"\b\d{12}\b", "[account-redacted]", safe)
    return safe


def check(check_id: str, ok: bool, detail: str, category: str) -> CheckResult:
    return CheckResult(
        check_id=check_id,
        ok=bool(ok),
        detail=sanitize_detail(detail),
        category=category,
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
    classification: str = "DEFECT",
    soft: bool = False,
) -> None:
    checks.append(check(check_id, ok, detail, category))
    if not ok and not soft:
        defects.append(hard_defect(classification, check_id, "pass", detail))


def report_text_is_safe(text: str) -> bool:
    return not any(p.search(text) for p in FORBIDDEN_REPORT_PATTERNS)


def body_has_aws_or_secrets(text: str) -> bool:
    return any(p.search(text) for p in AWS_OR_SECRET_IN_BODY)


def workflow_has_embedded_secrets(text: str) -> bool:
    return any(p.search(text) for p in WORKFLOW_SECRET_PATTERNS)


def dict_to_canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def read_engine_version(monorepo: Path) -> str | None:
    init_path = monorepo / "engine/src/codestrata/__init__.py"
    text = read_text(init_path)
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', text, re.M)
    return match.group(1) if match else None
