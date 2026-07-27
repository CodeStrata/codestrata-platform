"""Concrete AssessmentService — assessment record use cases."""

from __future__ import annotations

from codestrata_platform.application.commands.assessment import (
    CompleteAssessmentCommand,
    FailAssessmentCommand,
    RegisterAssessmentCommand,
    StartAssessmentCommand,
)
from codestrata_platform.application.common.errors import NotFoundError, ValidationError
from codestrata_platform.application.common.pagination import PageResult
from codestrata_platform.application.models.assessment import AssessmentSummary
from codestrata_platform.application.queries.assessment import AssessmentQuery
from codestrata_platform.domain.assessment import Assessment, AssessmentId, AssessmentRepository
from codestrata_platform.domain.assessment.value_objects import AssessmentMetadata
from codestrata_platform.domain.repository import RepositoryRepository, RepositoryStatus
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace import WorkspaceRepository, WorkspaceStatus


class DefaultAssessmentService:
    """Orchestrates Assessment aggregate operations via domain ports."""

    def __init__(
        self,
        *,
        assessments: AssessmentRepository,
        repositories: RepositoryRepository,
        workspaces: WorkspaceRepository,
    ) -> None:
        self._assessments = assessments
        self._repositories = repositories
        self._workspaces = workspaces

    def create_assessment(self, command: RegisterAssessmentCommand) -> AssessmentSummary:
        repository = self._repositories.get(command.repository_id)
        if repository is None:
            raise NotFoundError(
                f"Repository not found: {command.repository_id.value}",
                reason_code="repository_not_found",
            )
        if repository.status is RepositoryStatus.ARCHIVED:
            raise ValidationError(
                "Cannot register an assessment against an archived repository",
                reason_code="repository_archived",
            )
        if repository.workspace_id != command.workspace_id:
            raise ValidationError(
                "Assessment workspace does not match the repository workspace",
                reason_code="assessment_workspace_mismatch",
            )

        workspace = self._workspaces.get(command.workspace_id)
        if workspace is None:
            raise NotFoundError(
                f"Workspace not found: {command.workspace_id.value}",
                reason_code="workspace_not_found",
            )
        if workspace.status is not WorkspaceStatus.ACTIVE:
            raise ValidationError(
                "Cannot register an assessment under an inactive workspace",
                reason_code="workspace_inactive",
            )

        assessment = Assessment.create(
            repository_id=command.repository_id,
            workspace_id=command.workspace_id,
            engine_version=command.engine_version,
            assessment_version=command.assessment_version,
            metadata=(
                AssessmentMetadata(dict(command.metadata))
                if command.metadata is not None
                else None
            ),
        )
        self._assessments.save(assessment)
        return AssessmentSummary.from_aggregate(assessment)

    def start_assessment(self, command: StartAssessmentCommand) -> AssessmentSummary:
        assessment = self._require_assessment(command.assessment_id)
        assessment.start()
        self._assessments.save(assessment)
        return AssessmentSummary.from_aggregate(assessment)

    def complete_assessment(self, command: CompleteAssessmentCommand) -> AssessmentSummary:
        assessment = self._require_assessment(command.assessment_id)
        assessment.complete(
            generated_reports=command.generated_reports,
            references=command.references,
        )
        self._assessments.save(assessment)
        return AssessmentSummary.from_aggregate(assessment)

    def fail_assessment(self, command: FailAssessmentCommand) -> AssessmentSummary:
        assessment = self._require_assessment(command.assessment_id)
        assessment.fail(reason=command.reason)
        self._assessments.save(assessment)
        return AssessmentSummary.from_aggregate(assessment)

    def get_assessment(self, assessment_id: AssessmentId) -> AssessmentSummary:
        assessment = self._require_assessment(assessment_id)
        return AssessmentSummary.from_aggregate(assessment)

    def list_assessments(self, query: AssessmentQuery) -> PageResult[AssessmentSummary]:
        if query.repository_id is not None:
            candidates = self._assessments.list_by_repository(query.repository_id)
        elif query.workspace_id is not None:
            candidates = self._assessments.list_by_workspace(query.workspace_id)
        else:
            raise ValidationError(
                "AssessmentQuery requires repository_id or workspace_id",
                reason_code="assessment_query_scope_required",
            )

        filtered: list[Assessment] = []
        for assessment in candidates:
            if query.repository_id is not None and assessment.repository_id != query.repository_id:
                continue
            if query.workspace_id is not None and assessment.workspace_id != query.workspace_id:
                continue
            if query.status is not None and assessment.status is not query.status:
                continue
            filtered.append(assessment)

        total = len(filtered)
        page = query.page
        window = filtered[page.offset : page.offset + page.limit]
        items = tuple(AssessmentSummary.from_aggregate(item) for item in window)
        return PageResult(items=items, total=total, offset=page.offset, limit=page.limit)

    def list_assessment_history(
        self,
        repository_id: RepositoryId,
    ) -> tuple[AssessmentSummary, ...]:
        items = self._assessments.list_by_repository(repository_id)
        return tuple(AssessmentSummary.from_aggregate(item) for item in items)

    def _require_assessment(self, assessment_id: AssessmentId) -> Assessment:
        assessment = self._assessments.get(assessment_id)
        if assessment is None:
            raise NotFoundError(
                f"Assessment not found: {assessment_id.value}",
                reason_code="assessment_not_found",
            )
        return assessment
