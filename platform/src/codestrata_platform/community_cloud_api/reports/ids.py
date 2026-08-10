"""Opaque public report identifiers (Slice 17.16)."""

from __future__ import annotations

import re
import secrets

# High-entropy, non-sequential, URL-safe. No timestamps / repo names / AWS ids.
_PUBLIC_ID_RE = re.compile(r"^[A-Za-z0-9_-]{32,48}$")


def generate_public_report_id() -> str:
    """Return an opaque public report id (token_urlsafe ~32+ chars)."""

    # 24 bytes → 32 urlsafe chars (no padding).
    return secrets.token_urlsafe(24)


def validate_public_report_id(value: str) -> str:
    text = (value or "").strip()
    if not _PUBLIC_ID_RE.fullmatch(text):
        raise ValueError("invalid public report id")
    lowered = text.lower()
    for needle in (
        "github-",
        "local-",
        "assessment",
        "portfolio",
        "amazonaws",
        "s3.",
        "akia",
    ):
        if needle in lowered:
            raise ValueError("invalid public report id")
    return text


def generate_upload_id() -> str:
    return secrets.token_urlsafe(18)


__all__ = [
    "generate_public_report_id",
    "generate_upload_id",
    "validate_public_report_id",
]
