"""Deterministic secret / sensitive-content scan for release candidates.

Never logs raw secret values — only redacted evidence.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "dist",
        "build",
        ".codestrata",
        ".vscode-test",
    }
)

# Narrow allowlist for intentional synthetic fixtures (never broad suppressions).
# Documented exceptions only — do not add path-wide suppressions.
ALLOWLIST_GLOBS = (
    "**/signatures.py",  # detector pattern tables / example shapes
    "**/security_analyzer.py",  # analyzer pattern tables
    "**/test_*.py",  # pytest fixtures with synthetic credentials
    "**/tests/**/test_*.py",
    "**/docs/security/sbom-cyclonedx.json",  # sample SBOM illustration
)

ALLOWLIST_DOCUMENTATION = (
    "Synthetic AWS-style keys and private-key *markers* may appear only in "
    "allowlisted detector tables or pytest fixtures. Real credentials must "
    "never be committed. Staging exports must not include "
    ".codestrata-test-knowledge/."
)

DETECTORS: tuple[tuple[str, re.Pattern[str], str, bool], ...] = (
    (
        "private_key",
        re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
        "critical",
        True,
    ),
    (
        "aws_access_key_id",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        "critical",
        True,
    ),
    (
        "aws_secret_assignment",
        re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{20,}"),
        "critical",
        True,
    ),
    (
        "github_pat",
        re.compile(r"\bghp_[A-Za-z0-9]{20,}\b|\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
        "critical",
        True,
    ),
    (
        "slack_token",
        re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
        "critical",
        True,
    ),
    (
        "generic_api_key_assignment",
        re.compile(
            r"(?i)(?:api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*"
            r"['\"][A-Za-z0-9/+=_\-]{16,}['\"]"
        ),
        "high",
        True,
    ),
    (
        "password_assignment",
        re.compile(r"(?i)password\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
        "high",
        True,
    ),
    (
        "connection_string",
        re.compile(r"(?i)(?:postgres|mysql|mongodb|redis)://[^\s'\"]+:[^\s'\"]+@"),
        "high",
        True,
    ),
    (
        "dotenv_file",
        re.compile(r"(?i)^\.env(?:\.local|\.production)?$"),
        "critical",
        True,
    ),
    (
        "private_repo_url",
        re.compile(r"(?i)git@(?!github\.com)[A-Za-z0-9.-]+:"),
        "medium",
        False,
    ),
    (
        "internal_hostname",
        re.compile(r"(?i)\b(?:intranet|corp|internal)\.[A-Za-z0-9.-]+\b"),
        "medium",
        False,
    ),
    (
        "platform_api_leak",
        re.compile(r"(?i)platform\.codestrata\.ai|/api/openapi"),
        "high",
        True,
    ),
)


@dataclass(frozen=True)
class SecretFinding:
    file: str
    line: int | None
    detector: str
    severity: str
    redacted_evidence: str
    release_blocking: bool


def _match_allowlist(rel: str) -> bool:
    from fnmatch import fnmatch

    name = Path(rel).name
    normalized = rel.replace("\\", "/")
    candidates = (
        normalized,
        name,
        f"*/{name}",
        f"*/*/{name}",
    )
    for pat in ALLOWLIST_GLOBS:
        clean = pat.lstrip("./")
        if fnmatch(normalized, clean) or fnmatch(name, clean):
            return True
        # Support **/ prefixes without relying on recursive glob semantics.
        if clean.startswith("**/") and (
            fnmatch(normalized, clean[3:])
            or fnmatch(name, clean[3:])
            or any(fnmatch(item, clean[3:]) for item in candidates)
        ):
            return True
        if "/tests/" in f"/{normalized}/" and clean.endswith("test_*.py") and name.startswith(
            "test_"
        ):
            return True
    return False


def _redact(text: str) -> str:
    if len(text) <= 8:
        return "***"
    return text[:3] + "…" + text[-2:] + f" (len={len(text)})"


def _iter_files(base: Path) -> Iterable[Path]:
    if not base.exists():
        return []
    for dirpath, dirnames, filenames in __import__("os").walk(
        base, topdown=True, followlinks=False
    ):
        dirnames[:] = sorted(
            name for name in dirnames if name not in SKIP_DIR_NAMES
        )
        for name in sorted(filenames):
            path = Path(dirpath) / name
            if path.is_file() and not path.is_symlink():
                yield path


def scan_tree(base: Path, *, root_label: str | None = None) -> list[SecretFinding]:
    findings: list[SecretFinding] = []
    if not base.exists():
        return findings
    for path in _iter_files(base):
        try:
            rel = path.relative_to(base).as_posix()
        except ValueError:
            rel = path.name
        label = f"{root_label}/{rel}" if root_label else rel
        if path.name in {".env", ".env.local", ".env.production"} and not rel.endswith(
            ".example"
        ):
            findings.append(
                SecretFinding(
                    file=label,
                    line=None,
                    detector="dotenv_file",
                    severity="critical",
                    redacted_evidence=path.name,
                    release_blocking=True,
                )
            )
            continue
        if _match_allowlist(rel):
            continue
        try:
            raw = path.read_bytes()
        except OSError:
            continue
        if b"\0" in raw[:2048]:
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", errors="ignore")
        for line_no, line in enumerate(text.splitlines(), start=1):
            for detector, pattern, severity, blocking in DETECTORS:
                if detector == "dotenv_file":
                    continue
                match = pattern.search(line)
                if not match:
                    continue
                findings.append(
                    SecretFinding(
                        file=label,
                        line=line_no,
                        detector=detector,
                        severity=severity,
                        redacted_evidence=_redact(match.group(0)),
                        release_blocking=blocking,
                    )
                )
    return findings


def scan_export_staging(staging: Path) -> dict[str, object]:
    all_findings: list[SecretFinding] = []
    if staging.is_dir():
        for child in sorted(staging.iterdir()):
            if child.is_dir():
                all_findings.extend(scan_tree(child, root_label=child.name))
    blocking = [f for f in all_findings if f.release_blocking]
    return {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace(
            "+00:00", "Z"
        ),
        "staging": staging.name if staging.is_absolute() else str(staging),
        "finding_count": len(all_findings),
        "blocking_count": len(blocking),
        "passed": len(blocking) == 0,
        "allowlist_note": ALLOWLIST_DOCUMENTATION,
        "findings": [asdict(item) for item in all_findings],
    }


def write_secret_scan_report(payload: dict[str, object], destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination
