"""DefaultAssessmentIntelligenceService — orchestrates intelligence ingestion."""

from __future__ import annotations

import hashlib

from codestrata_platform.application.commands.intelligence import (
    BeginIntelligenceIngestionCommand,
    CompleteIntelligenceIngestionCommand,
    FailIntelligenceIngestionCommand,
    ProcessAssessmentIntelligenceCommand,
    RegisterAssessmentIntelligenceCommand,
)
from codestrata_platform.application.common.diagnostics import safe_failure_summary
from codestrata_platform.application.common.errors import (
    NotFoundError,
    ValidationError,
)
from codestrata_platform.application.intelligence.parsers.contracts import (
    ParsedFinding,
    ParsedMetric,
    ParsedRecommendation,
)
from codestrata_platform.application.intelligence.parsers.orchestrator import parse_artifacts
from codestrata_platform.application.models.intelligence import (
    FindingDetails,
    FindingView,
    IntelligenceDetails,
    IntelligenceProcessingResult,
    IntelligenceRegistration,
    MetricView,
    RecommendationView,
)
from codestrata_platform.application.queries.intelligence import (
    GetAssessmentIntelligenceQuery,
    GetFindingQuery,
    GetLatestAssessmentIntelligenceQuery,
    GetRecommendationQuery,
    ListAssessmentFindingsQuery,
    ListAssessmentMetricsQuery,
    ListAssessmentRecommendationsQuery,
)
from codestrata_platform.domain.artifact import ArtifactRepository, ArtifactStatus, ArtifactStorage
from codestrata_platform.domain.assessment import AssessmentRepository
from codestrata_platform.domain.intelligence import (
    AssessmentArtifactReader,
    AssessmentIntelligence,
    AssessmentIntelligenceId,
    AssessmentIntelligenceRepository,
    CompletedArtifactContent,
    EvidenceReference,
    EvidenceReferenceId,
    Finding,
    FindingCategory,
    FindingId,
    FindingRepository,
    FindingSeverity,
    IntelligenceIngestionStatus,
    IntelligenceSchemaVersion,
    Metric,
    MetricName,
    MetricRepository,
    MetricValue,
    MetricValueKind,
    Recommendation,
    RecommendationId,
    RecommendationPriority,
    RecommendationRepository,
)
from codestrata_platform.domain.repository import RepositoryRepository

PARSER_VERSION = "1.1.0"

_CATEGORY_MAP = {item.value: item for item in FindingCategory}
_SEVERITY_MAP = {item.value: item for item in FindingSeverity}
_PRIORITY_MAP = {item.value: item for item in RecommendationPriority}
_METRIC_KIND_MAP = {item.value: item for item in MetricValueKind}


class DefaultAssessmentArtifactReader:
    """Load completed artifact metadata and content for intelligence parsing."""

    def __init__(
        self,
        *,
        artifacts: ArtifactRepository,
        storage: ArtifactStorage,
    ) -> None:
        self._artifacts = artifacts
        self._storage = storage

    def get_completed_artifacts_for_assessment(
        self,
        assessment_id,
        *,
        artifact_ids: tuple[str, ...] | None = None,
    ) -> tuple[CompletedArtifactContent, ...]:
        items = self._artifacts.list_by_assessment(assessment_id)
        if artifact_ids is not None:
            requested = set(artifact_ids)
            items = tuple(item for item in items if item.artifact_id.value in requested)
        completed: list[CompletedArtifactContent] = []
        for artifact in items:
            if artifact.status is not ArtifactStatus.COMPLETED:
                raise ValidationError(
                    f"Artifact {artifact.artifact_id.value} is not completed",
                    reason_code="artifact_not_completed",
                )
            if artifact.storage_reference is None:
                raise ValidationError(
                    f"Artifact {artifact.artifact_id.value} has no stored content",
                    reason_code="artifact_missing_content",
                )
            content = self._storage.get(artifact.storage_reference)
            completed.append(
                CompletedArtifactContent(
                    artifact_id=artifact.artifact_id.value,
                    artifact_type=artifact.artifact_type,
                    schema_version=artifact.schema_version,
                    checksum=artifact.checksum.value,
                    content=content,
                )
            )
        if not completed:
            raise ValidationError(
                "No completed artifacts available for intelligence ingestion",
                reason_code="no_completed_artifacts",
            )
        return tuple(completed)


class DefaultAssessmentIntelligenceService:
    """Application orchestration for AssessmentIntelligence lifecycle."""

    def __init__(
        self,
        *,
        intelligence: AssessmentIntelligenceRepository,
        findings: FindingRepository,
        metrics: MetricRepository,
        recommendations: RecommendationRepository,
        artifacts: ArtifactRepository,
        artifact_reader: AssessmentArtifactReader | None = None,
        storage: ArtifactStorage | None = None,
        assessments: AssessmentRepository,
        repositories: RepositoryRepository,
        parser_version: str = PARSER_VERSION,
    ) -> None:
        self._intelligence = intelligence
        self._findings = findings
        self._metrics = metrics
        self._recommendations = recommendations
        self._artifacts = artifacts
        self._artifact_reader = artifact_reader or DefaultAssessmentArtifactReader(
            artifacts=artifacts,
            storage=_require_storage(storage),
        )
        self._assessments = assessments
        self._repositories = repositories
        self._parser_version = parser_version

    def register_assessment_intelligence(
        self,
        command: RegisterAssessmentIntelligenceCommand,
    ) -> IntelligenceRegistration:
        assessment, repository = self._require_assessment_context(command.assessment_id)
        idempotency_key = self._compute_idempotency_key(
            assessment_id=command.assessment_id,
            source_artifact_ids=command.source_artifact_ids,
            parser_version=command.parser_version,
        )
        existing = self._intelligence.find_by_idempotency_key(
            assessment_id=command.assessment_id,
            idempotency_key=idempotency_key,
        )
        if (
            existing is not None
            and existing.status is IntelligenceIngestionStatus.COMPLETED
        ):
            return IntelligenceRegistration(
                intelligence_id=existing.intelligence_id,
                assessment_id=existing.assessment_id,
                revision=existing.revision,
                idempotency_key=existing.idempotency_key,
                status=existing.status,
                created=False,
            )

        revision = self._next_revision(
            assessment_id=command.assessment_id,
            idempotency_key=idempotency_key,
        )
        if revision > 1:
            self._supersede_completed_revisions(command.assessment_id)

        record = AssessmentIntelligence.create_pending(
            organization_id=repository.organization_id,
            workspace_id=assessment.workspace_id,
            repository_id=assessment.repository_id,
            assessment_id=command.assessment_id,
            engine_assessment_id=command.engine_assessment_id,
            schema_version=IntelligenceSchemaVersion("1.0"),
            parser_version=command.parser_version,
            revision=revision,
            idempotency_key=idempotency_key,
            source_artifact_ids=command.source_artifact_ids,
        )
        self._intelligence.save(record)
        return IntelligenceRegistration(
            intelligence_id=record.intelligence_id,
            assessment_id=record.assessment_id,
            revision=record.revision,
            idempotency_key=record.idempotency_key,
            status=record.status,
            created=True,
        )

    def begin_intelligence_ingestion(
        self,
        command: BeginIntelligenceIngestionCommand,
    ) -> IntelligenceDetails:
        record = self._require_intelligence(command.intelligence_id)
        record.begin_ingestion()
        self._intelligence.save(record)
        return IntelligenceDetails.from_aggregate(record)

    def complete_intelligence_ingestion(
        self,
        command: CompleteIntelligenceIngestionCommand,
    ) -> IntelligenceDetails:
        record = self._require_intelligence(command.intelligence_id)
        record.complete()
        # Persist the aggregate before relational projections so FK targets exist.
        self._intelligence.save(record)
        self._persist_projection(record)
        return IntelligenceDetails.from_aggregate(record)

    def fail_intelligence_ingestion(
        self,
        command: FailIntelligenceIngestionCommand,
    ) -> IntelligenceDetails:
        record = self._require_intelligence(command.intelligence_id)
        record.fail(reason=command.reason, diagnostics=command.diagnostics)
        self._intelligence.save(record)
        return IntelligenceDetails.from_aggregate(record)

    def process_assessment_intelligence(
        self,
        command: ProcessAssessmentIntelligenceCommand,
    ) -> IntelligenceProcessingResult:
        assessment, repository = self._require_assessment_context(command.assessment_id)
        completed_artifacts = self._artifact_reader.get_completed_artifacts_for_assessment(
            command.assessment_id,
            artifact_ids=command.artifact_ids,
        )
        source_artifact_ids = tuple(
            sorted({artifact.artifact_id for artifact in completed_artifacts})
        )
        parser_version = command.parser_version or self._parser_version
        idempotency_key = self._compute_idempotency_key_from_artifacts(
            artifacts=completed_artifacts,
            parser_version=parser_version,
        )
        existing = self._intelligence.find_by_idempotency_key(
            assessment_id=command.assessment_id,
            idempotency_key=idempotency_key,
        )
        if (
            existing is not None
            and existing.status is IntelligenceIngestionStatus.COMPLETED
        ):
            return IntelligenceProcessingResult(
                intelligence=IntelligenceDetails.from_aggregate(existing),
                created=False,
                idempotent=True,
            )

        revision = self._next_revision(
            assessment_id=command.assessment_id,
            idempotency_key=idempotency_key,
        )
        if revision > 1:
            self._supersede_completed_revisions(command.assessment_id)

        engine_assessment_id = self._resolve_engine_assessment_id(
            assessment_id=command.assessment_id,
            source_artifact_ids=source_artifact_ids,
        )
        record = AssessmentIntelligence.create_pending(
            organization_id=repository.organization_id,
            workspace_id=assessment.workspace_id,
            repository_id=assessment.repository_id,
            assessment_id=command.assessment_id,
            engine_assessment_id=engine_assessment_id,
            schema_version=IntelligenceSchemaVersion("1.0"),
            parser_version=parser_version,
            revision=revision,
            idempotency_key=idempotency_key,
            source_artifact_ids=source_artifact_ids,
        )
        record.begin_ingestion()
        try:
            parsed = parse_artifacts(
                [
                    (
                        artifact.artifact_type,
                        artifact.schema_version,
                        artifact.content,
                        artifact.artifact_id,
                    )
                    for artifact in completed_artifacts
                ]
            )
            record.schema_version = IntelligenceSchemaVersion(parsed.schema_version)
            for finding in parsed.findings:
                record.attach_finding(
                    _to_domain_finding(finding, assessment_id=command.assessment_id)
                )
            for metric in parsed.metrics:
                record.attach_metric(_to_domain_metric(metric))
            for recommendation in parsed.recommendations:
                record.attach_recommendation(
                    _to_domain_recommendation(
                        recommendation,
                        assessment_id=command.assessment_id,
                    )
                )
            if parsed.diagnostics:
                record.diagnostics = tuple(parsed.diagnostics)
            record.complete()
        except Exception as error:
            reason = safe_failure_summary(error, limit=1000)
            diagnostics = (
                (error.reason_code,)
                if hasattr(error, "reason_code") and error.reason_code
                else ()
            )
            record.fail(reason=reason, diagnostics=diagnostics)
            self._intelligence.save(record)
            raise

        # Persist the aggregate before relational projections so FK targets exist.
        self._intelligence.save(record)
        self._persist_projection(record)
        return IntelligenceProcessingResult(
            intelligence=IntelligenceDetails.from_aggregate(record),
            created=True,
            idempotent=False,
        )

    def get_assessment_intelligence(
        self,
        query: GetAssessmentIntelligenceQuery,
    ) -> IntelligenceDetails:
        return IntelligenceDetails.from_aggregate(self._require_intelligence(query.intelligence_id))

    def get_latest_assessment_intelligence(
        self,
        query: GetLatestAssessmentIntelligenceQuery,
    ) -> IntelligenceDetails:
        self._require_assessment(query.assessment_id)
        items = self._intelligence.list_by_assessment(query.assessment_id)
        if not items:
            raise NotFoundError(
                f"Intelligence not found for assessment {query.assessment_id.value}",
                reason_code="intelligence_not_found",
            )
        preferred = sorted(
            items,
            key=lambda item: (
                0 if item.status is IntelligenceIngestionStatus.COMPLETED else 1,
                -item.revision,
            ),
        )[0]
        return IntelligenceDetails.from_aggregate(preferred)

    def list_assessment_findings(
        self,
        query: ListAssessmentFindingsQuery,
    ) -> tuple[FindingView, ...]:
        self._require_assessment(query.assessment_id)
        findings = self._findings.list_by_assessment(query.assessment_id)
        if query.severity is not None:
            findings = tuple(item for item in findings if item.severity is query.severity)
        return tuple(FindingView.from_domain(item) for item in findings)

    def list_assessment_metrics(
        self,
        query: ListAssessmentMetricsQuery,
    ) -> tuple[MetricView, ...]:
        self._require_assessment(query.assessment_id)
        items = self._metrics.list_by_assessment(query.assessment_id)
        return tuple(MetricView.from_domain(item) for item in items)

    def list_assessment_recommendations(
        self,
        query: ListAssessmentRecommendationsQuery,
    ) -> tuple[RecommendationView, ...]:
        self._require_assessment(query.assessment_id)
        items = self._recommendations.list_by_assessment(query.assessment_id)
        return tuple(RecommendationView.from_domain(item) for item in items)

    def get_finding(self, query: GetFindingQuery) -> FindingDetails:
        finding = self._findings.get(query.finding_id)
        if finding is None or finding.assessment_id != query.assessment_id:
            raise NotFoundError(
                f"Finding not found: {query.finding_id.value}",
                reason_code="finding_not_found",
            )
        return FindingDetails.from_domain(finding)

    def get_recommendation(self, query: GetRecommendationQuery) -> RecommendationView:
        recommendation = self._recommendations.get(query.recommendation_id)
        if recommendation is None or recommendation.assessment_id != query.assessment_id:
            raise NotFoundError(
                f"Recommendation not found: {query.recommendation_id.value}",
                reason_code="recommendation_not_found",
            )
        return RecommendationView.from_domain(recommendation)

    def _compute_idempotency_key(
        self,
        *,
        assessment_id,
        source_artifact_ids: tuple[str, ...],
        parser_version: str,
    ) -> str:
        artifacts = self._artifacts.list_by_assessment(assessment_id)
        selected = {
            artifact.artifact_id.value: artifact
            for artifact in artifacts
            if artifact.artifact_id.value in set(source_artifact_ids)
        }
        if len(selected) != len(set(source_artifact_ids)):
            missing = sorted(set(source_artifact_ids) - set(selected))
            raise NotFoundError(
                f"Artifact(s) not found: {', '.join(missing)}",
                reason_code="artifact_not_found",
            )
        completed = [
            CompletedArtifactContent(
                artifact_id=artifact.artifact_id.value,
                artifact_type=artifact.artifact_type,
                schema_version=artifact.schema_version,
                checksum=artifact.checksum.value,
                content=b"",
            )
            for artifact in selected.values()
        ]
        return self._compute_idempotency_key_from_artifacts(
            artifacts=completed,
            parser_version=parser_version,
        )

    @staticmethod
    def _compute_idempotency_key_from_artifacts(
        *,
        artifacts: tuple[CompletedArtifactContent, ...] | list[CompletedArtifactContent],
        parser_version: str,
    ) -> str:
        parts = sorted(f"{artifact.artifact_id}:{artifact.checksum}" for artifact in artifacts)
        payload = "|".join(parts) + f"|parser:{parser_version}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _next_revision(self, *, assessment_id, idempotency_key: str) -> int:
        existing = self._intelligence.find_by_idempotency_key(
            assessment_id=assessment_id,
            idempotency_key=idempotency_key,
        )
        if existing is not None:
            return existing.revision
        return self._intelligence.latest_revision_for_assessment(assessment_id) + 1

    def _supersede_completed_revisions(self, assessment_id) -> None:
        for record in self._intelligence.list_by_assessment(assessment_id):
            if record.status is IntelligenceIngestionStatus.COMPLETED:
                record.supersede()
                self._intelligence.save(record)

    def _persist_projection(self, record: AssessmentIntelligence) -> None:
        assessment_id = record.assessment_id
        intelligence_id = record.intelligence_id.value
        self._replace_findings(assessment_id, record.findings, intelligence_id=intelligence_id)
        self._replace_metrics(assessment_id, record.metrics, intelligence_id=intelligence_id)
        self._replace_recommendations(
            assessment_id,
            record.recommendations,
            intelligence_id=intelligence_id,
        )

    def _replace_findings(
        self,
        assessment_id,
        findings: tuple[Finding, ...],
        *,
        intelligence_id: str,
    ) -> None:
        if hasattr(self._findings, "replace_for_assessment"):
            self._findings.replace_for_assessment(
                assessment_id,
                findings,
                intelligence_id=intelligence_id,
            )
            return
        for finding in findings:
            if hasattr(self._findings, "save"):
                self._findings.save(finding)

    def _replace_metrics(
        self,
        assessment_id,
        metrics: tuple[Metric, ...],
        *,
        intelligence_id: str,
    ) -> None:
        if hasattr(self._metrics, "replace_for_assessment"):
            self._metrics.replace_for_assessment(
                assessment_id,
                metrics,
                intelligence_id=intelligence_id,
            )
            return
        for metric in metrics:
            if hasattr(self._metrics, "save"):
                self._metrics.save(metric)

    def _replace_recommendations(
        self,
        assessment_id,
        recommendations: tuple[Recommendation, ...],
        *,
        intelligence_id: str,
    ) -> None:
        if hasattr(self._recommendations, "replace_for_assessment"):
            self._recommendations.replace_for_assessment(
                assessment_id,
                recommendations,
                intelligence_id=intelligence_id,
            )
            return
        for recommendation in recommendations:
            if hasattr(self._recommendations, "save"):
                self._recommendations.save(recommendation)

    def _require_assessment_context(self, assessment_id):
        assessment = self._assessments.get(assessment_id)
        if assessment is None:
            raise NotFoundError(
                f"Assessment not found: {assessment_id.value}",
                reason_code="assessment_not_found",
            )
        repository = self._repositories.get(assessment.repository_id)
        if repository is None:
            raise NotFoundError(
                f"Repository not found: {assessment.repository_id.value}",
                reason_code="repository_not_found",
            )
        return assessment, repository

    def _require_assessment(self, assessment_id):
        assessment = self._assessments.get(assessment_id)
        if assessment is None:
            raise NotFoundError(
                f"Assessment not found: {assessment_id.value}",
                reason_code="assessment_not_found",
            )
        return assessment

    def _require_intelligence(
        self,
        intelligence_id: AssessmentIntelligenceId,
    ) -> AssessmentIntelligence:
        record = self._intelligence.get(intelligence_id)
        if record is None:
            raise NotFoundError(
                f"Assessment intelligence not found: {intelligence_id.value}",
                reason_code="intelligence_not_found",
            )
        return record

    def _resolve_engine_assessment_id(
        self,
        *,
        assessment_id,
        source_artifact_ids: tuple[str, ...],
    ) -> str:
        for artifact in self._artifacts.list_by_assessment(assessment_id):
            if artifact.artifact_id.value in source_artifact_ids:
                return artifact.engine_assessment_id
        return "unknown"


def _require_storage(storage: ArtifactStorage | None) -> ArtifactStorage:
    if storage is None:
        raise ValidationError(
            "Artifact storage is required when artifact_reader is not provided",
            reason_code="missing_storage",
        )
    return storage


def _to_domain_finding(parsed: ParsedFinding, *, assessment_id) -> Finding:
    evidence = tuple(
        EvidenceReference(
            evidence_id=(
                EvidenceReferenceId(item.evidence_id)
                if item.evidence_id
                else EvidenceReferenceId.generate()
            ),
            path_reference=item.path_reference,
            line_start=item.line_start,
            line_end=item.line_end,
            symbol=item.symbol,
            component=item.component,
            evidence_type=item.evidence_type,
            checksum=item.checksum,
            redacted_excerpt=item.redacted_excerpt,
            source_artifact_id=item.source_artifact_id,
        )
        for item in parsed.evidence_references
    )
    return Finding(
        finding_id=FindingId(parsed.finding_id),
        assessment_id=assessment_id,
        category=_map_category(parsed.category),
        rule_id=parsed.rule_id,
        title=parsed.title,
        summary=parsed.summary,
        severity=_map_severity(parsed.severity),
        confidence=parsed.confidence,
        production_scope=parsed.production_scope,
        affected_component=parsed.affected_component,
        affected_path_reference=parsed.affected_path_reference,
        evidence_references=evidence,
        remediation_reference=parsed.remediation_reference,
        metadata=parsed.metadata,
    )


def _to_domain_metric(parsed: ParsedMetric) -> Metric:
    kind = _METRIC_KIND_MAP.get(parsed.kind.lower())
    if kind is None:
        raise ValidationError(
            f"Unsupported metric kind: {parsed.kind}",
            reason_code="invalid_metric_kind",
        )
    return Metric(
        name=MetricName(parsed.name),
        value=MetricValue(kind=kind, value=parsed.value),
        unit=parsed.unit,
        metadata=parsed.metadata,
    )


def _to_domain_recommendation(
    parsed: ParsedRecommendation,
    *,
    assessment_id,
) -> Recommendation:
    return Recommendation(
        recommendation_id=RecommendationId(parsed.recommendation_id),
        assessment_id=assessment_id,
        category=_map_category(parsed.category),
        title=parsed.title,
        rationale=parsed.rationale,
        priority=_map_priority(parsed.priority),
        related_finding_ids=parsed.related_finding_ids,
        dependencies=parsed.dependencies,
        effort=parsed.effort,
        impact=parsed.impact,
        roadmap_horizon=parsed.roadmap_horizon,
        metadata=parsed.metadata,
    )


def _map_category(raw: str) -> FindingCategory:
    mapped = _CATEGORY_MAP.get(raw.lower())
    if mapped is None:
        raise ValidationError(
            f"Unsupported finding category: {raw}",
            reason_code="invalid_category",
        )
    return mapped


def _map_severity(raw: str) -> FindingSeverity:
    mapped = _SEVERITY_MAP.get(raw.lower())
    if mapped is None:
        raise ValidationError(
            f"Unsupported finding severity: {raw}",
            reason_code="invalid_severity",
        )
    return mapped


def _map_priority(raw: str) -> RecommendationPriority:
    mapped = _PRIORITY_MAP.get(raw.lower())
    if mapped is None:
        raise ValidationError(
            f"Unsupported recommendation priority: {raw}",
            reason_code="invalid_priority",
        )
    return mapped
