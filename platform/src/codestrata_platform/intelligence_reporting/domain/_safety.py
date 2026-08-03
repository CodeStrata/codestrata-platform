"""Safety helpers — reject paths, secrets, and oversized free text in domain values."""

from __future__ import annotations

import re
from collections.abc import Sequence

from codestrata_platform.domain.errors import InvalidValueError

_ABS_PATH_RE = re.compile(
    r"(^|[\s\"'=])(/Users/|/home/|/var/folders/|[A-Za-z]:\\|/tmp/|/private/)"
)
_SECRET_RE = re.compile(
    r"(AKIA[0-9A-Z]{16}|BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY|"
    r"-----BEGIN|"
    r"(password|secret|api[_-]?key)\s*[:=]\s*\S+)",
    re.IGNORECASE,
)
_MAX_STATEMENT = 2000
_MAX_TITLE = 256


def require_nonblank(value: str, *, label: str) -> str:
    text = str(value).strip()
    if not text:
        raise InvalidValueError(
            f"{label} must be non-blank",
            reason_code=f"empty_{label}",
        )
    return text


def reject_unsafe_text(value: str, *, label: str) -> str:
    text = require_nonblank(value, label=label)
    if _ABS_PATH_RE.search(text):
        raise InvalidValueError(
            f"{label} must not contain absolute filesystem paths",
            reason_code="absolute_path_forbidden",
        )
    if _SECRET_RE.search(text):
        raise InvalidValueError(
            f"{label} must not contain secret-like content",
            reason_code="secret_like_content_forbidden",
        )
    return text


def bound_title(value: str) -> str:
    text = reject_unsafe_text(value, label="title")
    if len(text) > _MAX_TITLE:
        raise InvalidValueError(
            "title exceeds maximum length",
            reason_code="title_too_long",
        )
    return text


def bound_statement(value: str) -> str:
    text = reject_unsafe_text(value, label="statement")
    if len(text) > _MAX_STATEMENT:
        raise InvalidValueError(
            "statement exceeds maximum length",
            reason_code="statement_too_long",
        )
    return text


def unique_sorted_ids(values: Sequence[str], *, label: str) -> tuple[str, ...]:
    cleaned = [require_nonblank(str(item), label=label) for item in values]
    unique = tuple(sorted(set(cleaned)))
    if len(unique) != len(cleaned):
        raise InvalidValueError(
            f"{label} must be unique",
            reason_code=f"duplicate_{label}",
        )
    for item in unique:
        reject_unsafe_text(item, label=label)
    return unique


def optional_sorted_ids(values: Sequence[str], *, label: str) -> tuple[str, ...]:
    cleaned = [str(item).strip() for item in values if str(item).strip()]
    unique = tuple(sorted(set(cleaned)))
    if len(unique) != len(cleaned):
        raise InvalidValueError(
            f"{label} must be unique",
            reason_code=f"duplicate_{label}",
        )
    for item in unique:
        reject_unsafe_text(item, label=label)
    return unique
