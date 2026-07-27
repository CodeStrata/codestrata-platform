"""Assessment aggregate for Platform-owned assessment records."""

from __future__ import annotations

from codestrata_platform.domain.assessment.aggregate import Assessment
from codestrata_platform.domain.assessment.enums import AssessmentStatus
from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.assessment.ports import AssessmentRepository
from codestrata_platform.domain.assessment.value_objects import (
    AssessmentReference,
    AssessmentVersion,
    GeneratedReport,
)

__all__ = [
    "Assessment",
    "AssessmentId",
    "AssessmentReference",
    "AssessmentRepository",
    "AssessmentStatus",
    "AssessmentVersion",
    "GeneratedReport",
]
