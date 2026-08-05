"""Unit tests for access validation helpers (Slice 8.12)."""

from __future__ import annotations

import pytest

from codestrata_platform.community_cloud_api.data_lake.access_policy import (
    WRITER_ALLOWED_ACTIONS,
    WRITER_FORBIDDEN_ACTIONS,
)
from codestrata_platform.community_cloud_api.data_lake.access_validation import (
    AccessValidationError,
    validate_access_action_sets,
)


def test_validate_access_action_sets_accepts_default_sets() -> None:
    validate_access_action_sets(
        allowed=WRITER_ALLOWED_ACTIONS,
        forbidden=WRITER_FORBIDDEN_ACTIONS,
    )


def test_validate_access_action_sets_rejects_s3_wildcard_in_allowed() -> None:
    allowed = frozenset({"s3:PutObject", "s3:GetObject", "s3:*"})
    with pytest.raises(AccessValidationError, match="s3:\\*"):
        validate_access_action_sets(allowed=allowed, forbidden=WRITER_FORBIDDEN_ACTIONS)


def test_validate_access_action_sets_rejects_delete_in_allowed() -> None:
    allowed = frozenset({"s3:PutObject", "s3:GetObject", "s3:DeleteObject"})
    with pytest.raises(AccessValidationError, match="delete"):
        validate_access_action_sets(allowed=allowed, forbidden=WRITER_FORBIDDEN_ACTIONS)

    allowed_version = frozenset({"s3:PutObject", "s3:GetObject", "s3:DeleteObjectVersion"})
    with pytest.raises(AccessValidationError, match="delete"):
        validate_access_action_sets(allowed=allowed_version, forbidden=WRITER_FORBIDDEN_ACTIONS)


def test_validate_access_action_sets_rejects_kms_in_allowed() -> None:
    allowed = frozenset({"s3:PutObject", "s3:GetObject", "kms:Decrypt"})
    with pytest.raises(AccessValidationError, match="KMS"):
        validate_access_action_sets(allowed=allowed, forbidden=WRITER_FORBIDDEN_ACTIONS)


def test_validate_access_action_sets_rejects_missing_forbidden_entries() -> None:
    forbidden = WRITER_FORBIDDEN_ACTIONS - {"s3:*", "kms:*"}
    with pytest.raises(AccessValidationError, match="missing required entries"):
        validate_access_action_sets(allowed=WRITER_ALLOWED_ACTIONS, forbidden=forbidden)


def test_validate_access_action_sets_rejects_overlap() -> None:
    forbidden = WRITER_FORBIDDEN_ACTIONS | {"s3:PutObject"}
    with pytest.raises(AccessValidationError, match="overlap"):
        validate_access_action_sets(allowed=WRITER_ALLOWED_ACTIONS, forbidden=forbidden)


def test_validate_access_action_sets_rejects_empty_allowed() -> None:
    with pytest.raises(AccessValidationError, match="must not be empty"):
        validate_access_action_sets(allowed=frozenset(), forbidden=WRITER_FORBIDDEN_ACTIONS)


def test_validate_access_action_sets_rejects_missing_required_allowed() -> None:
    with pytest.raises(AccessValidationError, match="s3:PutObject and s3:GetObject"):
        validate_access_action_sets(
            allowed=frozenset({"s3:PutObject"}),
            forbidden=WRITER_FORBIDDEN_ACTIONS,
        )
