"""AssessmentService contract."""

from __future__ import annotations

from typing import Protocol

from codestrata_platform.application.commands.assessment import (
    CompleteAssessmentCommand,
    FailAssessmentCommand,
    RegisterAssessmentCommand,
    StartAssessmentCommand,
)
from codestrata_platform.application.common.pagination import PageResult
from codestrata_platform.application.models.assessment import AssessmentSummary
from codestrata_platform.application.queries.assessment import AssessmentQuery
from codestrata_platform.domain.assessment import AssessmentId
from codestrata_platform.domain.repository.ids import RepositoryId


class AssessmentService(Protocol):
    """Application contract for Platform assessment records.

    Does not run the Community Engine. Records outcomes after Engine completion.
    """

    def create_assessment(self, command: RegisterAssessmentCommand) -> AssessmentSummary:
        """Create a pending assessment record."""

    def start_assessment(self, command: StartAssessmentCommand) -> AssessmentSummary:
        """Mark an assessment as running."""

    def complete_assessment(self, command: CompleteAssessmentCommand) -> AssessmentSummary:
        """Mark an assessment as succeeded with report pointers."""

    def fail_assessment(self, command: FailAssessmentCommand) -> AssessmentSummary:
        """Mark an assessment as failed."""

    def get_assessment(self, assessment_id: AssessmentId) -> AssessmentSummary:
        """Return an assessment or raise when missing."""

    def list_assessments(self, query: AssessmentQuery) -> PageResult[AssessmentSummary]:
        """List assessments matching the query."""

    def list_assessment_history(
        self,
        repository_id: RepositoryId,
    ) -> tuple[AssessmentSummary, ...]:
        """Return assessment history for a repository."""
