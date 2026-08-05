"""Bounded validation helpers for Community Data Lake access control (Slice 8.12)."""

from __future__ import annotations

from collections.abc import Iterable


class AccessValidationError(ValueError):
    """Raised when access-policy values fail structural validation."""


_REQUIRED_ALLOWED: frozenset[str] = frozenset({"s3:PutObject", "s3:GetObject"})
_FORBIDDEN_MUST_INCLUDE: frozenset[str] = frozenset(
    {
        "s3:*",
        "s3:ListAllMyBuckets",
        "s3:DeleteObject",
        "s3:DeleteObjectVersion",
        "kms:*",
    }
)


def validate_access_action_sets(
    *,
    allowed: Iterable[str],
    forbidden: Iterable[str],
) -> None:
    """Fail closed if allowed/forbidden sets violate least-privilege invariants."""

    allowed_set = frozenset(allowed)
    forbidden_set = frozenset(forbidden)

    if not allowed_set:
        raise AccessValidationError("writer_allowed_actions must not be empty")
    if not _REQUIRED_ALLOWED.issubset(allowed_set):
        raise AccessValidationError(
            "writer_allowed_actions must include s3:PutObject and s3:GetObject"
        )
    if "s3:*" in allowed_set:
        raise AccessValidationError("writer_allowed_actions must not include s3:*")
    if "s3:ListAllMyBuckets" in allowed_set:
        raise AccessValidationError("writer_allowed_actions must not include ListAllMyBuckets")
    if "s3:DeleteObject" in allowed_set or "s3:DeleteObjectVersion" in allowed_set:
        raise AccessValidationError("writer_allowed_actions must not include delete actions")
    if any(action.startswith("kms:") for action in allowed_set):
        raise AccessValidationError("writer_allowed_actions must not include KMS actions")

    missing_forbidden = _FORBIDDEN_MUST_INCLUDE - forbidden_set
    if missing_forbidden:
        raise AccessValidationError(
            f"writer_forbidden_actions missing required entries: {sorted(missing_forbidden)}"
        )

    overlap = allowed_set & forbidden_set
    if overlap:
        raise AccessValidationError(
            f"writer_allowed_actions and writer_forbidden_actions overlap: {sorted(overlap)}"
        )


__all__ = ["AccessValidationError", "validate_access_action_sets"]
