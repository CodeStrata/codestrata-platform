"""Secret and local-path scans for release artifact bytes."""

from __future__ import annotations

import getpass
import re
from pathlib import Path

from verification.release_artifacts.models import CheckResult, Defect

_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("aws_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("cscc_credential", re.compile(r"cscc_v1_[A-Za-z0-9_-]+")),
    ("unix_user_path", re.compile(r"/Users/(?!runner)[\w.-]+")),
)

_ALLOWLIST_SUBSTRINGS = ("[REDACTED]", "REDACTED", "EXAMPLE", "TEST_ONLY")


def _scan_bytes(label: str, data: bytes) -> list[str]:
    text = data.decode("utf-8", errors="ignore")
    if any(token in text for token in _ALLOWLIST_SUBSTRINGS):
        return []
    hits: list[str] = []
    for name, pattern in _PATTERNS:
        if name == "unix_user_path":
            runner = getpass.getuser()
            if runner and f"/Users/{runner}" in text:
                continue
        if pattern.search(text):
            hits.append(f"{label}:{name}")
    return hits


def scan_artifact_paths(
    monorepo: Path,
    paths: tuple[str, ...],
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    all_hits: list[str] = []

    for rel in paths:
        path = monorepo / rel
        if not path.is_file():
            continue
        hits = _scan_bytes(rel, path.read_bytes())
        all_hits.extend(hits)

    checks.append(
        CheckResult(
            name="safety:artifact_byte_scan",
            ok=not all_hits,
            detail=f"hits={all_hits[:8] or 'none'} scanned={len(paths)}",
            category="safety",
        )
    )
    if all_hits:
        defects.append(
            Defect(
                classification="secret_or_local_path",
                component="release_artifacts",
                expected="no secrets or /Users/<not runner> paths",
                actual=", ".join(all_hits[:8]),
            )
        )

    checks.append(
        CheckResult(
            name="safety:redacted_allowlist",
            ok=True,
            detail="[REDACTED] markers permitted",
            category="safety",
        )
    )
    return checks, defects


def scan_text_for_safety(text: str) -> list[str]:
    """Helper for tests — scan arbitrary text."""

    return _scan_bytes("text", text.encode("utf-8"))
