"""Assessment enums."""

from __future__ import annotations

from enum import StrEnum


class AssessmentStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
