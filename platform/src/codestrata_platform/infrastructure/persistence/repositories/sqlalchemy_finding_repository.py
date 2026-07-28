"""SqlAlchemyFindingRepository."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.intelligence.ids import FindingId
from codestrata_platform.domain.intelligence.value_objects import Finding
from codestrata_platform.infrastructure.persistence.mappers.assessment_intelligence_mapper import (
    AssessmentIntelligenceMapper,
)
from codestrata_platform.infrastructure.persistence.models.evidence_reference_record import (
    EvidenceReferenceRecord,
)
from codestrata_platform.infrastructure.persistence.models.finding_record import FindingRecord

from .sqlalchemy_assessment_intelligence_repository import (
    SqlAlchemyAssessmentIntelligenceRepository,
)


class SqlAlchemyFindingRepository:
    """Durable FindingRepository adapter with assessment-level projection."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, finding_id: FindingId) -> Finding | None:
        record = self._session.get(FindingRecord, finding_id.value)
        if record is None:
            return None
        evidence_records = self._session.scalars(
            select(EvidenceReferenceRecord)
            .where(EvidenceReferenceRecord.finding_id == record.id)
            .order_by(EvidenceReferenceRecord.id.asc())
        ).all()
        return AssessmentIntelligenceMapper.finding_to_domain(
            record,
            tuple(evidence_records),
        )

    def list_by_assessment(self, assessment_id: AssessmentId) -> tuple[Finding, ...]:
        records = self._session.scalars(
            select(FindingRecord)
            .where(FindingRecord.assessment_id == assessment_id.value)
            .order_by(FindingRecord.id.asc())
        ).all()
        findings: list[Finding] = []
        for record in records:
            evidence_records = self._session.scalars(
                select(EvidenceReferenceRecord)
                .where(EvidenceReferenceRecord.finding_id == record.id)
                .order_by(EvidenceReferenceRecord.id.asc())
            ).all()
            findings.append(
                AssessmentIntelligenceMapper.finding_to_domain(
                    record,
                    tuple(evidence_records),
                )
            )
        return tuple(findings)

    def replace_for_assessment(
        self,
        assessment_id: AssessmentId,
        findings: tuple[Finding, ...],
        *,
        intelligence_id: str | None = None,
    ) -> None:
        resolved_intelligence_id = intelligence_id or (
            SqlAlchemyAssessmentIntelligenceRepository.latest_intelligence_id_for_assessment(
                self._session,
                assessment_id,
            )
        )
        if resolved_intelligence_id is None:
            raise RuntimeError(
                f"Cannot project findings without intelligence for assessment {assessment_id.value}"
            )

        self._session.execute(
            delete(FindingRecord).where(FindingRecord.assessment_id == assessment_id.value)
        )
        for finding in findings:
            self._session.add(
                AssessmentIntelligenceMapper.finding_to_record(
                    finding,
                    intelligence_id=resolved_intelligence_id,
                )
            )
        self._session.flush()
        for finding in findings:
            for evidence in finding.evidence_references:
                self._session.add(
                    AssessmentIntelligenceMapper.evidence_to_record(
                        evidence,
                        finding_id=finding.finding_id.value,
                        assessment_id=assessment_id.value,
                    )
                )
        self._session.flush()
