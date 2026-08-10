"""Publication sanitizer — reject secret/path leaks before cloud promote."""

from __future__ import annotations

import re
from dataclasses import dataclass

_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*\S+"),
    re.compile(r"cscc_v1_[A-Za-z0-9_-]{16,}"),
    re.compile(r"(?i)authorization:\s*bearer\s+\S+"),
    re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"),
    re.compile(r"(?i)(api[_-]?key|token|secret)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
)

_PATH_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)/(Users|home)/[^\s\"']+"),
    re.compile(r"(?i)[A-Z]:\\\\Users\\\\[^\s\"']+"),
    re.compile(r"(?i)file:///"),
)

_AWS_ACCOUNT_RE = re.compile(r"\barn:aws:[a-z0-9-]+:[a-z0-9-]*:\d{12}:")
_GIT_USERINFO_RE = re.compile(r"https?://[^/\s\"']+:[^/\s\"']+@")


@dataclass(frozen=True, slots=True)
class SanitizeResult:
    ok: bool
    reason_code: str | None = None

    def to_stable_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {"ok": self.ok}
        if self.reason_code is not None:
            payload["reason_code"] = self.reason_code
        return payload


def sanitize_report_bytes(*, name: str, content: bytes) -> SanitizeResult:
    """Reject accidental secret / absolute-path / AWS-id leakage.

    Does not rewrite legitimate assessment findings.
    """

    _ = name
    try:
        text = content.decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return SanitizeResult(ok=False, reason_code="undecodable_content")

    for pattern in _SECRET_PATTERNS:
        if pattern.search(text):
            return SanitizeResult(ok=False, reason_code="secret_pattern_detected")
    for pattern in _PATH_PATTERNS:
        if pattern.search(text):
            return SanitizeResult(ok=False, reason_code="absolute_path_detected")
    if _AWS_ACCOUNT_RE.search(text):
        return SanitizeResult(ok=False, reason_code="aws_account_detected")
    if _GIT_USERINFO_RE.search(text):
        return SanitizeResult(ok=False, reason_code="git_userinfo_detected")
    return SanitizeResult(ok=True)


__all__ = ["SanitizeResult", "sanitize_report_bytes"]
