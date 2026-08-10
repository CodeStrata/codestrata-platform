"""Security preflight and output classification for Slice 17.13."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from verification.community_22_repository_validation.helpers import add_check
from verification.community_22_repository_validation.models import CheckResult, Defect

_FORBIDDEN_FIELD_NAMES = frozenset(
    {
        "aws_account_id",
        "s3_uri",
        "absolute_path",
        "clone_url_with_credentials",
        "pat",
        "password",
        "secret",
        "token",
    }
)
_SECRET_PATTERNS = (
    re.compile(r"ghp_[A-Za-z0-9]+"),
    re.compile(r"github_pat_[A-Za-z0-9_]+"),
    re.compile(r"password\s*="),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]+"),
    re.compile(r"arn:aws:[^\s\"']+"),
    re.compile(r"s3://[^\s\"']+"),
    re.compile(r"/Users/[^\s\"']+"),
    re.compile(r"/home/[^\s\"']+"),
)


def classify_text(text: str) -> list[str]:
    """Return safe classification labels for suspicious content (no secret echo)."""

    labels: list[str] = []
    if any(p.search(text) for p in _SECRET_PATTERNS):
        labels.append("forbidden_secret_or_path_pattern")
    return labels


def validate_public_clone_url(url: str) -> tuple[bool, str]:
    parsed = urlparse(url.strip())
    if parsed.scheme != "https":
        return False, "only https clone URLs are allowed"
    if parsed.username or parsed.password:
        return False, "credentials in clone URL are forbidden"
    if "@" in url.split("://", 1)[-1].split("/", 1)[0]:
        return False, "credentials in clone URL are forbidden"
    return True, "ok"


def register_entry_is_safe(entry: dict[str, Any]) -> tuple[bool, str]:
    keys = {str(k).lower() for k in entry.keys()}
    forbidden = keys & _FORBIDDEN_FIELD_NAMES
    if forbidden:
        return False, f"forbidden register fields: {sorted(forbidden)}"
    blob = str(sorted(entry.items()))
    if classify_text(blob):
        return False, "register entry contains forbidden patterns"
    return True, "ok"


def check_security_preflight(
    *,
    clone_urls: list[str],
    register_entries: list[dict[str, Any]],
    report_text: str,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    for idx, url in enumerate(clone_urls):
        ok, detail = validate_public_clone_url(url)
        add_check(
            checks,
            defects,
            f"security:clone_url:{idx}",
            ok,
            detail,
            "security",
            CheckResult=CheckResult,
            Defect=Defect,
        )

    for idx, entry in enumerate(register_entries):
        ok, detail = register_entry_is_safe(entry)
        add_check(
            checks,
            defects,
            f"security:register_entry:{idx}",
            ok,
            detail,
            "security",
            CheckResult=CheckResult,
            Defect=Defect,
        )

    labels = classify_text(report_text)
    add_check(
        checks,
        defects,
        "security:report_text_safe",
        not labels,
        "ok" if not labels else labels[0],
        "security",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    return checks, defects
