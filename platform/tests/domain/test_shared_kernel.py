"""Domain tests for Commercial Platform shared kernel."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.shared import (
    AuditInfo,
    CreatedAt,
    PlatformId,
    PlatformVersion,
    UpdatedAt,
)


def test_platform_id_rejects_blank_and_generates() -> None:
    with pytest.raises(InvalidValueError):
        PlatformId("  ")
    generated = PlatformId.generate(prefix="repo")
    assert generated.value.startswith("repo:")
    assert PlatformId(generated.value) == generated


def test_platform_id_equality_and_immutability() -> None:
    left = PlatformId("abc-123")
    right = PlatformId("abc-123")
    assert left == right
    assert hash(left) == hash(right)
    with pytest.raises(FrozenInstanceError):
        left.value = "mutated"  # type: ignore[misc]


def test_platform_version_validation() -> None:
    assert PlatformVersion("1.2.3").value == "1.2.3"
    with pytest.raises(InvalidValueError):
        PlatformVersion("1.2")
    with pytest.raises(InvalidValueError):
        PlatformVersion("v1.2.3")


def test_timestamps_require_timezone() -> None:
    with pytest.raises(InvalidValueError):
        CreatedAt(datetime(2026, 1, 1, 0, 0, 0))
    created = CreatedAt(datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC))
    updated = UpdatedAt.from_created(created)
    assert updated.value == created.value


def test_audit_info_touch_preserves_created() -> None:
    audit = AuditInfo.create()
    touched = audit.touch()
    assert touched.created_at == audit.created_at
    assert touched.updated_at.value >= audit.updated_at.value
