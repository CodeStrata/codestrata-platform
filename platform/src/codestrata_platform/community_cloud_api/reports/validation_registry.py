"""Private Community validation report registry (temporary internal tooling).

Stores verified/pending publish records under the private report-artifacts
bucket prefix ``metadata/validation/entries/``.

Not a permanent Community product surface. Designed to be removed or replaced
by commercial portfolio/report management without changing opaque public URLs
(``https://reports.codestrata.ai/r/<id>``).
"""

from __future__ import annotations

from typing import Any

VALIDATION_ENTRY_SCHEMA = "community-validation-report-entry:1.0"
VALIDATION_ENTRIES_PREFIX = "metadata/validation/entries/"
VALIDATION_PURPOSE = "temporary_community_validation"

VERIFICATION_PENDING = "published_pending_verification"
VERIFICATION_VERIFIED = "verified"
VERIFICATION_FAILED = "verification_failed"
VALID_VERIFICATION_STATUSES = frozenset(
    {VERIFICATION_PENDING, VERIFICATION_VERIFIED, VERIFICATION_FAILED}
)

DEFAULT_LIST_LIMIT = 50
MAX_LIST_LIMIT = 200


def validation_entry_key(public_id: str) -> str:
    return f"{VALIDATION_ENTRIES_PREFIX}{public_id}.json"


def build_validation_entry(
    *,
    public_id: str,
    public_url: str,
    report_type: str,
    logical_identity_key: str,
    logical_identity_type: str,
    published_at: str,
    verification_status: str = VERIFICATION_PENDING,
    verified_http_status: int | None = None,
    verified_at: str | None = None,
) -> dict[str, Any]:
    status = verification_status if verification_status in VALID_VERIFICATION_STATUSES else VERIFICATION_PENDING
    return {
        "schema": VALIDATION_ENTRY_SCHEMA,
        "temporary": True,
        "purpose": VALIDATION_PURPOSE,
        "public_report_id": public_id,
        "public_url": public_url,
        "report_type": report_type,
        "logical_identity_key": logical_identity_key,
        "logical_identity_type": logical_identity_type,
        "published_at": published_at,
        "verification_status": status,
        "verified_http_status": verified_http_status,
        "verified_at": verified_at,
        # Display alias for Insights table (repository or portfolio id).
        "display_identity": logical_identity_key,
    }


def sanitize_list_limit(raw: object) -> int:
    try:
        value = int(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return DEFAULT_LIST_LIMIT
    if value < 1:
        return DEFAULT_LIST_LIMIT
    return min(value, MAX_LIST_LIMIT)


__all__ = [
    "DEFAULT_LIST_LIMIT",
    "MAX_LIST_LIMIT",
    "VALIDATION_ENTRIES_PREFIX",
    "VALIDATION_ENTRY_SCHEMA",
    "VALIDATION_PURPOSE",
    "VERIFICATION_FAILED",
    "VERIFICATION_PENDING",
    "VERIFICATION_VERIFIED",
    "VALID_VERIFICATION_STATUSES",
    "build_validation_entry",
    "sanitize_list_limit",
    "validation_entry_key",
]
