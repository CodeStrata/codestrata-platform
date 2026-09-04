"""Versioned, technology-neutral evidence and assessment contracts."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from codestrata.domain.evidence.framework.identifiers import evidence_identity

SCHEMA_VERSION: Literal["1.0"] = "1.0"


class FrozenModel(BaseModel):
    """Strict immutable contract base."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class StrictModel(BaseModel):
    """Strict mutable authoring contract base."""

    model_config = ConfigDict(extra="forbid")


class CoverageState(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNKNOWN = "unknown"
    FAILED = "failed"
    NOT_APPLICABLE = "not_applicable"


class ActivityStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ClaimOutcome(StrEnum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    CONTRADICTED = "contradicted"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    NOT_ASSESSED = "not_assessed"
    NOT_APPLICABLE = "not_applicable"


class CostClass(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ExternalAccess(StrEnum):
    NONE = "none"
    OPTIONAL = "optional"
    REQUIRED = "required"


class CollectorMaturity(StrEnum):
    SUPPORTED = "supported"
    PARTIAL = "partial"
    EXPERIMENTAL = "experimental"


class EvidenceFamily(StrEnum):
    REPOSITORY = "repository"
    LANGUAGE = "language"
    ARCHITECTURE = "architecture"
    CODE_HEALTH = "code_health"
    DEPENDENCIES = "dependencies"
    TESTING = "testing"
    SECURITY = "security"
    DELIVERY = "delivery"
    RUNTIME = "runtime"
    DECLARED = "declared"
    IMPORTED = "imported"


class RepositorySubject(StrictModel):
    repository_id: str
    path: str
    revision: str = "working-tree"

    @field_validator("repository_id", "path", "revision")
    @classmethod
    def required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


class Scope(StrictModel):
    include: tuple[str, ...] = ("**/*",)
    exclude: tuple[str, ...] = (
        ".git/**",
        ".codestrata-artifacts/**",
        "node_modules/**",
        "dist/**",
        "build/**",
        ".venv/**",
    )


class SensitivityPolicy(StrictModel):
    store_source_snippets: bool = False
    redact_secrets: bool = True
    raw_artifacts: Literal["referenced", "copied"] = "copied"


class EvidenceActivity(StrictModel):
    activity_id: str
    collector_id: str
    enabled: bool = True
    configuration: dict[str, Any] = Field(default_factory=dict)

    @field_validator("activity_id", "collector_id")
    @classmethod
    def required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


class EvidenceImport(StrictModel):
    import_id: str
    format: Literal["sarif-2.1"] = "sarif-2.1"
    path: str

    @field_validator("import_id", "path")
    @classmethod
    def required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


class ManualAttestation(StrictModel):
    attestation_id: str
    statement: str
    source: str
    confidence_basis: str = "Declared by user; not independently verified."

    @field_validator("attestation_id", "statement", "source", "confidence_basis")
    @classmethod
    def required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


class ReportView(StrictModel):
    format: Literal["html", "json", "jsonl", "sarif"]
    audience: str = "engineering"


class ExecutionLimits(StrictModel):
    max_files: int = Field(default=5000, ge=1, le=100_000)
    max_file_bytes: int = Field(default=1_000_000, ge=1024, le=20_000_000)
    activity_timeout_seconds: int = Field(default=300, ge=1, le=3600)
    max_evidence_records: int = Field(default=20_000, ge=1, le=1_000_000)
    external_access: Literal["deny", "allow"] = "deny"


class EvidencePlan(StrictModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    plan_id: str
    goal: str
    questions: tuple[str, ...] = ()
    audience: tuple[str, ...] = ("engineering",)
    subject: RepositorySubject
    scope: Scope = Field(default_factory=Scope)
    sensitivity: SensitivityPolicy = Field(default_factory=SensitivityPolicy)
    packs: tuple[str, ...] = ("repository-baseline",)
    activities: tuple[EvidenceActivity, ...]
    imports: tuple[EvidenceImport, ...] = ()
    attestations: tuple[ManualAttestation, ...] = ()
    assessment_profile: str = "repository-evidence-baseline@1.0"
    reports: tuple[ReportView, ...] = (
        ReportView(format="html"),
        ReportView(format="json"),
        ReportView(format="jsonl"),
        ReportView(format="sarif"),
    )
    limits: ExecutionLimits = Field(default_factory=ExecutionLimits)

    @field_validator("plan_id", "goal", "assessment_profile")
    @classmethod
    def required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned

    @model_validator(mode="after")
    def unique_activity_ids(self) -> EvidencePlan:
        ids = [activity.activity_id for activity in self.activities]
        if len(ids) != len(set(ids)):
            raise ValueError("activities must have unique activity_id values")
        import_ids = [item.import_id for item in self.imports]
        if len(import_ids) != len(set(import_ids)):
            raise ValueError("imports must have unique import_id values")
        attestation_ids = [item.attestation_id for item in self.attestations]
        if len(attestation_ids) != len(set(attestation_ids)):
            raise ValueError("attestations must have unique attestation_id values")
        claim_ids = (
            [f"evidence.{activity.activity_id}" for activity in self.activities]
            + [f"evidence.import.{item.import_id}" for item in self.imports]
            + [f"evidence.attestation.{item.attestation_id}" for item in self.attestations]
        )
        if len(claim_ids) != len(set(claim_ids)):
            raise ValueError("activity, import, and attestation IDs create colliding claims")
        return self


class EvidenceLocation(FrozenModel):
    path: str
    start_line: int | None = Field(default=None, ge=1)
    start_column: int | None = Field(default=None, ge=1)
    end_line: int | None = Field(default=None, ge=1)
    end_column: int | None = Field(default=None, ge=1)


class Coverage(FrozenModel):
    state: CoverageState
    population: str
    planned: int | None = Field(default=None, ge=0)
    examined: int | None = Field(default=None, ge=0)
    successful: bool
    supports_absence_conclusion: bool = False
    limitations: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_absence_basis(self) -> Coverage:
        if self.supports_absence_conclusion:
            if self.state is not CoverageState.COMPLETE or not self.successful:
                raise ValueError("absence conclusions require complete, successful coverage")
            if self.planned is None or self.examined is None:
                raise ValueError("absence conclusions require planned and examined counts")
            if self.examined < self.planned:
                raise ValueError("examined count must cover the planned population")
        return self


class RawArtifactReference(FrozenModel):
    sha256: str
    media_type: str
    relative_path: str
    storage_mode: Literal["copied", "repository_referenced"] = "copied"


class EvidenceEnvelope(FrozenModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    evidence_id: str
    kind: str
    run_id: str
    activity_id: str
    collector_id: str
    collector_version: str
    repository_id: str
    revision: str
    method: str
    production_mode: Literal["observed", "derived", "declared", "imported"]
    collected_at: datetime
    locations: tuple[EvidenceLocation, ...] = ()
    raw_references: tuple[RawArtifactReference, ...] = ()
    parent_evidence_ids: tuple[str, ...] = ()
    coverage: Coverage
    confidence_basis: str | None = None
    sensitivity: Literal["public", "internal", "sensitive"] = "internal"
    redactions: tuple[str, ...] = ()
    payload: dict[str, Any]
    payload_sha256: str

    @model_validator(mode="after")
    def validate_negative_observation(self) -> EvidenceEnvelope:
        if self.payload.get("assertion") == "absent":
            if not self.coverage.supports_absence_conclusion:
                raise ValueError("negative observations require a successful searched population")
        return self

    @classmethod
    def create(
        cls,
        *,
        kind: str,
        run_id: str,
        activity_id: str,
        collector_id: str,
        collector_version: str,
        repository_id: str,
        revision: str,
        method: str,
        production_mode: Literal["observed", "derived", "declared", "imported"],
        coverage: Coverage,
        payload: dict[str, Any],
        locations: tuple[EvidenceLocation, ...] = (),
        raw_references: tuple[RawArtifactReference, ...] = (),
        parent_evidence_ids: tuple[str, ...] = (),
        confidence_basis: str | None = None,
        sensitivity: Literal["public", "internal", "sensitive"] = "internal",
        redactions: tuple[str, ...] = (),
        collected_at: datetime | None = None,
    ) -> EvidenceEnvelope:
        location_payload = [item.model_dump(mode="json") for item in locations]
        evidence_id, payload_sha256 = evidence_identity(
            repository_id=repository_id,
            revision=revision,
            collector_id=collector_id,
            collector_version=collector_version,
            kind=kind,
            payload=payload,
            locations=location_payload,
        )
        return cls(
            evidence_id=evidence_id,
            kind=kind,
            run_id=run_id,
            activity_id=activity_id,
            collector_id=collector_id,
            collector_version=collector_version,
            repository_id=repository_id,
            revision=revision,
            method=method,
            production_mode=production_mode,
            collected_at=collected_at or datetime.now(UTC),
            locations=locations,
            raw_references=raw_references,
            parent_evidence_ids=parent_evidence_ids,
            coverage=coverage,
            confidence_basis=confidence_basis,
            sensitivity=sensitivity,
            redactions=redactions,
            payload=payload,
            payload_sha256=payload_sha256,
        )


class CollectorManifest(FrozenModel):
    collector_id: str
    version: str
    label: str
    description: str
    publisher: str = "CodeStrata"
    supported_subjects: tuple[str, ...] = ("repository",)
    output_kinds: tuple[str, ...]
    permission_requirements: tuple[str, ...] = ("read_repository",)
    cost_class: CostClass = CostClass.LOW
    deterministic: bool = True
    runs_code: bool = False
    side_effects: bool = False
    external_access: ExternalAccess = ExternalAccess.NONE
    coverage_semantics: str
    limitations: tuple[str, ...] = ()
    configuration_schema: dict[str, Any] = Field(default_factory=dict)
    license: str | None = None
    homepage: str | None = None
    family: EvidenceFamily = EvidenceFamily.REPOSITORY
    languages: tuple[str, ...] = ()
    capability_ids: tuple[str, ...] = ()
    maturity: CollectorMaturity = CollectorMaturity.SUPPORTED
    recommendation_weight: int = Field(default=50, ge=0, le=100)


class EvidencePackActivity(FrozenModel):
    activity_id: str
    collector_id: str
    configuration: dict[str, Any] = Field(default_factory=dict)
    required: bool = True
    when_applicable: bool = True


class EvidencePackManifest(FrozenModel):
    pack_id: str
    version: str
    title: str
    description: str
    goal: str
    families: tuple[EvidenceFamily, ...]
    activities: tuple[EvidencePackActivity, ...]
    includes: tuple[str, ...] = ()
    recommended_languages: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    @property
    def key(self) -> str:
        return f"{self.pack_id}@{self.version}"


class EvidencePackRecommendation(FrozenModel):
    pack: EvidencePackManifest
    status: Literal["recommended", "available", "unavailable"]
    reason: str


class EvidenceCatalog(FrozenModel):
    detected_languages: tuple[str, ...]
    collectors: tuple[CollectorManifest, ...]
    packs: tuple[EvidencePackRecommendation, ...]


class CollectorPreview(FrozenModel):
    activity_id: str
    collector_id: str
    status: Literal["applicable", "inapplicable", "unavailable", "blocked"]
    reason: str
    manifest: CollectorManifest


class PlanPreview(FrozenModel):
    plan_id: str
    collectors: tuple[CollectorPreview, ...]
    reads: tuple[str, ...]
    executes: tuple[str, ...]
    leaves_machine: tuple[str, ...]
    blind_spots: tuple[str, ...]


class ActivityRecord(FrozenModel):
    activity_id: str
    collector_id: str
    status: ActivityStatus
    evidence_count: int = Field(default=0, ge=0)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    message: str = ""


class ExecutionEvent(FrozenModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    run_id: str
    sequence: int = Field(ge=0)
    activity_id: str
    status: ActivityStatus
    message: str
    occurred_at: datetime


class RunRecord(FrozenModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    run_id: str
    plan_id: str
    status: RunStatus
    repository_id: str
    revision: str
    started_at: datetime
    finished_at: datetime | None = None
    activities: tuple[ActivityRecord, ...] = ()
    errors: tuple[str, ...] = ()


class ClaimDefinition(FrozenModel):
    claim_id: str
    statement: str
    activity_id: str
    accepted_evidence_kinds: tuple[str, ...]
    minimum_evidence: int = Field(default=1, ge=0)
    require_complete_coverage: bool = False
    limitation: str | None = None


class AssessmentProfile(FrozenModel):
    profile_id: str
    version: str
    title: str
    goal: str
    questions: tuple[str, ...]
    claims: tuple[ClaimDefinition, ...]


class AssessmentProfileManifest(FrozenModel):
    profile_id: str
    version: str
    title: str
    description: str
    supported_outcomes: tuple[ClaimOutcome, ...]
    limitations: tuple[str, ...] = ()


class ClaimResult(FrozenModel):
    claim_id: str
    statement: str
    outcome: ClaimOutcome
    rationale: str
    evidence_ids: tuple[str, ...] = ()
    missing_requirements: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


class Finding(FrozenModel):
    finding_id: str
    claim_id: str
    title: str
    summary: str
    level: Literal["note", "warning", "error"] = "warning"
    evidence_ids: tuple[str, ...] = ()
    locations: tuple[EvidenceLocation, ...] = ()


class Action(FrozenModel):
    action_id: str
    finding_id: str
    title: str
    rationale: str
    verification: str
    priority: Literal["now", "next", "later"] = "next"


class Risk(FrozenModel):
    risk_id: str
    finding_id: str
    statement: str
    likelihood: Literal["unknown", "low", "medium", "high"] = "unknown"
    impact: Literal["unknown", "low", "medium", "high"] = "unknown"


class TraceabilityEdge(FrozenModel):
    source_id: str
    relationship: Literal[
        "supports",
        "contradicts",
        "produces_finding",
        "creates_risk",
        "addressed_by",
    ]
    target_id: str


class AssessmentResult(FrozenModel):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    assessment_id: str
    plan_id: str
    run_id: str
    profile_id: str
    profile_version: str
    repository_id: str
    revision: str
    generated_at: datetime
    claims: tuple[ClaimResult, ...]
    findings: tuple[Finding, ...] = ()
    risks: tuple[Risk, ...] = ()
    actions: tuple[Action, ...] = ()
    traceability: tuple[TraceabilityEdge, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    baseline_run_id: str | None = None

    @model_validator(mode="after")
    def validate_traceability(self) -> AssessmentResult:
        claim_ids = {item.claim_id for item in self.claims}
        finding_ids = {item.finding_id for item in self.findings}
        risk_ids = {item.risk_id for item in self.risks}
        action_ids = {item.action_id for item in self.actions}
        evidence_ids = set(self.evidence_ids)
        if len(claim_ids) != len(self.claims):
            raise ValueError("assessment claims must have unique IDs")
        if len(finding_ids) != len(self.findings):
            raise ValueError("assessment findings must have unique IDs")
        if len(risk_ids) != len(self.risks) or len(action_ids) != len(self.actions):
            raise ValueError("assessment risks and actions must have unique IDs")
        for finding in self.findings:
            if finding.claim_id not in claim_ids:
                raise ValueError(f"finding references unknown claim {finding.claim_id!r}")
            if not set(finding.evidence_ids) <= evidence_ids:
                raise ValueError(f"finding {finding.finding_id!r} references unknown evidence")
        if any(item.finding_id not in finding_ids for item in self.risks):
            raise ValueError("risk references an unknown finding")
        if any(item.finding_id not in finding_ids for item in self.actions):
            raise ValueError("action references an unknown finding")
        all_ids = claim_ids | finding_ids | risk_ids | action_ids | evidence_ids
        if any(
            edge.source_id not in all_ids or edge.target_id not in all_ids
            for edge in self.traceability
        ):
            raise ValueError("traceability edge references an unknown contract ID")
        return self
