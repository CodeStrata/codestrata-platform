"""Helpers for Slice 17.6."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from verification.community_cloud_runtime_security.models import CheckResult, Defect


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def add_check(
    checks: list[CheckResult],
    defects: list[Defect],
    check_id: str,
    ok: bool,
    detail: str,
    category: str,
    *,
    classification: str | None = None,
    soft: bool = False,
) -> None:
    safe_detail = detail
    if "/Users/" in safe_detail or "/home/" in safe_detail:
        safe_detail = re.sub(r"(/Users/|/home/)[^\s\"']+", "[path-redacted]", safe_detail)
    if "arn:aws:" in safe_detail:
        safe_detail = re.sub(r"arn:aws:[^\s\"']+", "[arn-redacted]", safe_detail)
    safe_detail = re.sub(r"\b\d{12}\b", "[account-redacted]", safe_detail)
    checks.append(CheckResult(check_id, bool(ok), safe_detail, category))
    if not ok and not soft:
        defects.append(Defect(classification or category, check_id, "pass", safe_detail))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def scan_tf_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    out: list[Path] = []
    for p in root.rglob("*.tf"):
        if ".terraform" in p.parts:
            continue
        out.append(p)
    return sorted(out)


def resource_addresses_from_tf(text: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for m in re.finditer(r'^\s*resource\s+"([^"]+)"\s+"([^"]+)"', text, re.M):
        found.append((m.group(1), m.group(2)))
    return found


def load_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = load_json(path)
        return data if isinstance(data, dict) else None
    except Exception:  # noqa: BLE001
        return None


def repo_has_secret_literals(text: str) -> bool:
    lowered = text.lower()
    if "test-only-insights-password" in lowered or "test-only-session-signing" in lowered:
        return False
    for pat in (
        r"password\s*=\s*['\"][^'\"]{8,}['\"]",
        r"secret\s*=\s*['\"][^'\"]{16,}['\"]",
        r"-----BEGIN (RSA |EC )?PRIVATE KEY-----",
    ):
        if re.search(pat, text, re.I):
            return True
    return False
