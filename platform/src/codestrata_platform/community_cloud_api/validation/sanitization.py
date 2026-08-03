"""Safe field-path formatting and secret/path detectors (no value echo)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

_MAX_FIELD_PATH_LENGTH = 128
_SAFE_FIELD_SEGMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_INDEX_SEGMENT = re.compile(r"^\[(\d+)\]$")

_ROOT_TOKENS = frozenset(
    {
        "body",
        "__root__",
        "root",
        "model",
        "input",
        "args",
        "kwargs",
    }
)

_PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN[ A-Z0-9]*PRIVATE KEY-----",
    re.IGNORECASE,
)
_BEARER_RE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-+/=]{8,}")
_AWS_KEY_RE = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
_SIGNED_URL_RE = re.compile(
    r"(?i)([?&](X-Amz-Signature|Signature|sig)=)[A-Za-z0-9%._\-+/=]{8,}"
)
_FILE_URI_RE = re.compile(r"(?i)\bfile://")
_POSIX_HOME_TMP_RE = re.compile(
    r"(?i)(^|[\s\"'=])(/Users/|/home/|/tmp/|/var/folders/|/private/var/|~/)"
)
_WINDOWS_ABS_RE = re.compile(r"(?i)(^|[\s\"'=])([A-Za-z]:\\|\\\\)")
_MULTILINE_CODE_RE = re.compile(
    r"(?m)^(def |class |function |import |from .+ import )"
)


def format_field_path(loc: Sequence[Any]) -> str:
    """Convert a Pydantic location tuple into a stable public field path."""

    parts: list[str] = []
    for item in loc:
        if isinstance(item, int):
            parts.append(f"[{item}]")
            continue
        text = str(item).strip()
        if not text or text.lower() in _ROOT_TOKENS:
            continue
        if not _SAFE_FIELD_SEGMENT.match(text):
            parts.append("field")
            continue
        parts.append(text)

    if not parts:
        return "request"

    rendered = ""
    for part in parts:
        if _INDEX_SEGMENT.match(part):
            rendered += part
        elif not rendered:
            rendered = part
        else:
            rendered = f"{rendered}.{part}"

    if len(rendered) > _MAX_FIELD_PATH_LENGTH:
        return rendered[:_MAX_FIELD_PATH_LENGTH]
    return rendered


def sanitize_field_name(name: str) -> str:
    text = (name or "").strip()
    if not text:
        return "field"
    if not _SAFE_FIELD_SEGMENT.match(text):
        return "field"
    return text[:64]


def contains_secret_like_value(value: str) -> bool:
    """Return True when a string looks like a credential or sensitive path."""

    if not value:
        return False
    if "\x00" in value:
        return True
    if _PRIVATE_KEY_RE.search(value):
        return True
    if _BEARER_RE.search(value):
        return True
    if _AWS_KEY_RE.search(value):
        return True
    if _SIGNED_URL_RE.search(value):
        return True
    if _FILE_URI_RE.search(value):
        return True
    if _POSIX_HOME_TMP_RE.search(value):
        return True
    if _WINDOWS_ABS_RE.search(value):
        return True
    # Bare absolute POSIX path (leading slash with another segment).
    if value.startswith("/") and len(value) > 1 and not value.startswith("//"):
        return True
    if "\n" in value and _MULTILINE_CODE_RE.search(value):
        return True
    return False


def is_safe_repository_relative_path(value: str) -> bool:
    """Validate a repository-relative path candidate (no absolute / traversal)."""

    if not value or "\x00" in value:
        return False
    if len(value) > 512:
        return False
    if value.startswith("/") or value.startswith("\\"):
        return False
    if re.match(r"^[A-Za-z]:[\\/]", value):
        return False
    if value.lower().startswith("file:"):
        return False
    normalized = value.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part not in ("", ".")]
    if any(part == ".." for part in parts):
        return False
    if normalized.startswith("../") or normalized.endswith("/.."):
        return False
    if "/../" in f"/{normalized}/":
        return False
    return True


def reject_control_characters(value: str) -> bool:
    """Return True when value contains ASCII control characters."""

    return any(ord(ch) < 32 for ch in value)
